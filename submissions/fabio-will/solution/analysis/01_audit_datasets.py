"""Audit both datasets before any analysis.

Question for Dataset 1: can it support an operational diagnosis (time lost, what drives CSAT)?
Question for Dataset 2: is it clean enough to train and evaluate a ticket router?
Outputs: outputs/audit.json
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from common import load_it_tickets, load_tickets, write_json, TICKETS_CSV


def pct(n: int | float, d: int | float) -> float:
    return round(100.0 * n / d, 2) if d else 0.0


def uniformity_p(series: pd.Series) -> float:
    """Chi-square goodness-of-fit against a uniform distribution over observed categories."""
    counts = series.value_counts().values
    return float(stats.chisquare(counts).pvalue)


COMBO_COLS = ["Ticket Channel", "Ticket Priority", "Ticket Type"]
PERMUTATIONS = 2000


def worst_cell_test(frame: pd.DataFrame, value: str, worst: str, seed: int = 42) -> dict:
    """Answers "which channel x priority x type combination is worst?" and whether that is more than chance.

    Max-statistic permutation test: shuffle the values across tickets, keep the cells, and count how often
    the worst cell of a random shuffle is at least as extreme as the observed worst cell. This corrects for
    picking the worst of 80 cells, which is what a dashboard of "slowest combination" silently does.
    """
    rng = np.random.default_rng(seed)
    cells = frame.groupby(COMBO_COLS, observed=True)[value]
    stat = cells.median() if worst == "max" else cells.mean()
    observed = float(stat.max() if worst == "max" else stat.min())
    codes = frame.groupby(COMBO_COLS, observed=True).ngroup().to_numpy()
    values = frame[value].to_numpy()
    n_cells = int(codes.max()) + 1
    hits = 0
    for _ in range(PERMUTATIONS):
        shuffled = rng.permutation(values)
        if worst == "max":
            extreme = max(np.median(shuffled[codes == k]) for k in range(n_cells))
            hits += extreme >= observed
        else:
            extreme = min(shuffled[codes == k].mean() for k in range(n_cells))
            hits += extreme <= observed
    ranked = stat.sort_values(ascending=(worst != "max")).head(5)
    sizes = cells.size()
    return {
        "cells": n_cells,
        "tickets": int(len(frame)),
        "overall": round(float(np.median(values) if worst == "max" else values.mean()), 2),
        "worst": [
            {"channel": k[0], "priority": k[1], "type": k[2], "value": round(float(v), 2), "n": int(sizes[k])}
            for k, v in ranked.items()
        ],
        "permutation_p": round((hits + 1) / (PERMUTATIONS + 1), 4),
        "by_dimension": {
            col: {
                "kruskal_p": round(float(stats.kruskal(*[g[value].values for _, g in frame.groupby(col)]).pvalue), 4),
                "by_group": {
                    k: round(float(v), 2)
                    for k, v in (frame.groupby(col)[value].median() if worst == "max" else frame.groupby(col)[value].mean()).items()
                },
            }
            for col in COMBO_COLS
        },
    }


def audit_dataset1() -> dict:
    df = load_tickets()
    raw_lines = sum(1 for _ in open(TICKETS_CSV, encoding="utf-8"))
    n = len(df)

    closed = df[df["Ticket Status"] == "Closed"].copy()
    frt = pd.to_datetime(df["First Response Time"], errors="coerce")
    ttr = pd.to_datetime(df["Time to Resolution"], errors="coerce")
    both = frt.notna() & ttr.notna()
    delta_h = (ttr[both] - frt[both]).dt.total_seconds() / 3600
    purchase = pd.to_datetime(df["Date of Purchase"], errors="coerce")

    stamps = pd.concat([frt.dropna(), ttr.dropna()])
    span_h = (stamps.max() - stamps.min()).total_seconds() / 3600

    # CSAT only exists on closed tickets: does anything move it?
    c = closed.assign(
        csat=pd.to_numeric(closed["Customer Satisfaction Rating"], errors="coerce"),
        delta_h=(pd.to_datetime(closed["Time to Resolution"]) - pd.to_datetime(closed["First Response Time"])).dt.total_seconds() / 3600,
    ).dropna(subset=["csat"])
    csat_drivers = {}
    for col in ["Ticket Priority", "Ticket Channel", "Ticket Type", "Product Purchased", "Customer Gender"]:
        groups = [g["csat"].values for _, g in c.groupby(col)]
        csat_drivers[col] = {
            "kruskal_p": round(float(stats.kruskal(*groups).pvalue), 4),
            "mean_by_group": {k: round(float(v), 3) for k, v in c.groupby(col)["csat"].mean().items()},
        }
    rho, rho_p = stats.spearmanr(c["delta_h"].abs(), c["csat"])
    # Most favourable reading of the stamps: treat the gap as a duration whatever its sign.
    c["hours"] = c["delta_h"].abs()
    bottleneck = worst_cell_test(c, "hours", worst="max")
    satisfaction = worst_cell_test(c, "csat", worst="min")
    age_rho, age_p = stats.spearmanr(c["Customer Age"], c["csat"])

    desc = df["Ticket Description"].fillna("")
    resolution = closed["Resolution"].fillna("")
    # How often a resolution reuses a word that appears in its own ticket description
    overlap = []
    for d_txt, r_txt in zip(closed["Ticket Description"].fillna(""), resolution):
        dw = set(re.findall(r"[a-z]{4,}", d_txt.lower()))
        rw = set(re.findall(r"[a-z]{4,}", r_txt.lower()))
        overlap.append(len(dw & rw) / len(rw) if rw else 0)

    return {
        "records": n,
        "raw_csv_lines": raw_lines,
        "status": df["Ticket Status"].value_counts().to_dict(),
        "missing_pct": {k: pct(v, n) for k, v in df.isna().sum().items() if v},
        "first_response_present": int(frt.notna().sum()),
        "resolution_time_present": int(ttr.notna().sum()),
        "timestamps": {
            "min": str(stamps.min()),
            "max": str(stamps.max()),
            "span_hours": round(span_h, 1),
            "resolution_before_first_response": int((delta_h < 0).sum()),
            "resolution_before_first_response_pct": pct((delta_h < 0).sum(), len(delta_h)),
            "delta_hours_median": round(float(delta_h.median()), 2),
            "purchase_date_range": [str(purchase.min().date()), str(purchase.max().date())],
        },
        "uniformity_p": {col: round(uniformity_p(df[col]), 4) for col in ["Ticket Type", "Ticket Channel", "Ticket Priority", "Ticket Subject", "Product Purchased"]},
        "distribution": {col: df[col].value_counts().to_dict() for col in ["Ticket Type", "Ticket Channel", "Ticket Priority"]},
        "csat": {
            "present": int(len(c)),
            "distribution": {str(int(k)): int(v) for k, v in c["csat"].value_counts().sort_index().items()},
            "uniformity_p": round(float(stats.chisquare(c["csat"].value_counts().values).pvalue), 4),
            "spearman_abs_delta_hours": [round(float(rho), 4), round(float(rho_p), 4)],
            "spearman_age": [round(float(age_rho), 4), round(float(age_p), 4)],
            "drivers": csat_drivers,
        },
        "director_questions": {
            "where_flow_stalls": bottleneck,
            "what_moves_csat": satisfaction,
            "open_or_pending_pct": pct(int((df["Ticket Status"] != "Closed").sum()), n),
        },
        "text": {
            "placeholder_product_purchased_pct": pct(desc.str.contains(r"\{product_purchased\}").sum(), n),
            "unique_descriptions_pct": pct(desc.nunique(), n),
            "resolution_unique_pct": pct(resolution.nunique(), len(resolution)),
            "resolution_word_overlap_with_description_mean_pct": round(100 * float(np.mean(overlap)), 2),
            "resolution_examples": resolution.head(3).tolist(),
            "email_domains_top": df["Customer Email"].str.split("@").str[1].value_counts().head(3).to_dict(),
        },
    }


def audit_dataset2() -> dict:
    df = load_it_tickets()
    n = len(df)
    tokens = df["Document"].str.split()
    dup_mask = df.duplicated("Document", keep=False)
    conflicting = df[dup_mask].groupby("Document")["Topic_group"].nunique()
    stopwords = {"the", "and", "is", "to", "of", "a", "in", "for"}
    stopword_rate = float(np.mean([any(t in stopwords for t in toks) for toks in tokens]))
    return {
        "records": n,
        "classes": df["Topic_group"].value_counts().to_dict(),
        "class_share_pct": {k: pct(v, n) for k, v in df["Topic_group"].value_counts().items()},
        "tokens_per_ticket": {
            "median": int(tokens.str.len().median()),
            "p10": int(tokens.str.len().quantile(0.10)),
            "p90": int(tokens.str.len().quantile(0.90)),
        },
        "empty_or_short_lt3_tokens": int((tokens.str.len() < 3).sum()),
        "exact_duplicate_rows": int(df.duplicated("Document").sum()),
        "duplicate_texts_with_conflicting_labels": int((conflicting > 1).sum()),
        "share_with_common_stopwords_pct": round(100 * stopword_rate, 2),
        "lowercase_only": bool((df["Document"] == df["Document"].str.lower()).all()),
        "examples": df.groupby("Topic_group").head(1)[["Topic_group", "Document"]].to_dict("records"),
    }


if __name__ == "__main__":
    result = {"dataset1": audit_dataset1(), "dataset2": audit_dataset2()}
    path = write_json("audit.json", result)
    d1, d2 = result["dataset1"], result["dataset2"]
    print(f"Dataset 1: {d1['records']} records ({d1['raw_csv_lines']} CSV lines)")
    print(f"  timestamps span {d1['timestamps']['span_hours']}h; resolution before first response: {d1['timestamps']['resolution_before_first_response_pct']}%")
    print(f"  CSAT uniformity p={d1['csat']['uniformity_p']}; |delta| vs CSAT rho={d1['csat']['spearman_abs_delta_hours']}")
    print(f"  CSAT drivers p-values: { {k: v['kruskal_p'] for k, v in d1['csat']['drivers'].items()} }")
    dq = d1["director_questions"]
    for key in ("where_flow_stalls", "what_moves_csat"):
        w = dq[key]["worst"][0]
        print(f"  {key}: worst of {dq[key]['cells']} cells = {w} vs overall {dq[key]['overall']}; permutation p={dq[key]['permutation_p']}")
    print(f"  placeholder in description: {d1['text']['placeholder_product_purchased_pct']}%; resolution/description word overlap: {d1['text']['resolution_word_overlap_with_description_mean_pct']}%")
    print(f"Dataset 2: {d2['records']} records; duplicates {d2['exact_duplicate_rows']}; conflicting labels {d2['duplicate_texts_with_conflicting_labels']}")
    print(f"  tokens median {d2['tokens_per_ticket']['median']} (p10 {d2['tokens_per_ticket']['p10']}, p90 {d2['tokens_per_ticket']['p90']}); stopwords present {d2['share_with_common_stopwords_pct']}%")
    print("→", path.relative_to(Path(__file__).resolve().parent))
