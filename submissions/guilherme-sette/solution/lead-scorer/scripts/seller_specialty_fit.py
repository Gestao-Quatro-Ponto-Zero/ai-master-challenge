#!/usr/bin/env python3
"""Estimate seller specialization fit and match open deals to specialists.

The analysis is intentionally heuristic and explainable. It uses only closed
opportunities for historical fit and only open opportunities for deal matching.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

PRIOR_WEIGHT = 25
MIN_CANDIDATE_CLOSED = 100
SEGMENT_MIN_N = {
    "product": 12,
    "ticket_band": 20,
    "sector": 12,
    "revenue_band": 20,
    "employee_band": 20,
    "account": 8,
}
DIMENSION_WEIGHTS = {
    "product": 0.30,
    "ticket_band": 0.20,
    "sector": 0.20,
    "revenue_band": 0.10,
    "employee_band": 0.10,
    "account": 0.10,
}


@dataclass(frozen=True)
class FitKey:
    seller_id: str
    dimension: str
    segment_value: str


def ticket_band(price: object) -> str:
    if pd.isna(price):
        return "unknown_ticket"
    price = float(price)
    if price < 1_000:
        return "low_ticket_under_1k"
    if price < 4_000:
        return "mid_ticket_1k_to_4k"
    if price < 10_000:
        return "high_ticket_4k_to_10k"
    return "strategic_ticket_10k_plus"


def fmt_pct(value: object) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def fmt_money(value: object) -> str:
    if pd.isna(value):
        return "n/a"
    return f"US$ {float(value):,.0f}"


def md_table(df: pd.DataFrame, columns: list[str]) -> str:
    out = df[columns].copy()
    for col in out.columns:
        if col.endswith("_rate") or col.endswith("_pct") or "uplift" in col or "confidence" in col:
            out[col] = out[col].map(fmt_pct)
        elif col in {"estimated_deal_value", "open_value", "won_revenue_total"}:
            out[col] = out[col].map(fmt_money)
        elif col.endswith("_score"):
            out[col] = out[col].map(lambda x: "n/a" if pd.isna(x) else f"{float(x):.1f}")
        elif col.endswith("_days"):
            out[col] = out[col].map(lambda x: "n/a" if pd.isna(x) else f"{float(x):.0f}")
    out = out.fillna("n/a").astype(str)
    header = "| " + " | ".join(out.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(out.columns)) + " |"
    body = ["| " + " | ".join(row) + " |" for row in out.to_numpy()]
    return "\n".join([header, separator, *body])


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    enriched = pd.read_csv(PROCESSED_DIR / "opportunities_enriched.csv")
    open_pipeline = pd.read_csv(PROCESSED_DIR / "open_pipeline_for_scoring.csv")
    seller_xray = pd.read_csv(PROCESSED_DIR / "seller_xray.csv")
    for df in (enriched, open_pipeline):
        df["ticket_band"] = df["sales_price"].map(ticket_band)
    return enriched, open_pipeline, seller_xray


def seller_summary(closed: pd.DataFrame) -> pd.DataFrame:
    summary = closed.groupby(["sales_agent_id", "sales_agent", "manager", "regional_office"]).agg(
        seller_closed=("opportunity_id", "size"),
        seller_won=("is_won", "sum"),
    ).reset_index()
    global_wr = float(closed["is_won"].mean())
    summary["seller_win_rate"] = summary["seller_won"] / summary["seller_closed"]
    summary["seller_smoothed_win_rate"] = (
        summary["seller_won"] + PRIOR_WEIGHT * global_wr
    ) / (summary["seller_closed"] + PRIOR_WEIGHT)
    return summary


def build_fit_table(closed: pd.DataFrame) -> pd.DataFrame:
    global_wr = float(closed["is_won"].mean())
    sellers = seller_summary(closed)
    rows: list[dict[str, object]] = []

    dimensions = ["product", "ticket_band", "sector", "revenue_band", "employee_band", "account"]
    for dimension in dimensions:
        data = closed[closed[dimension].notna()].copy()
        segment_base = data.groupby(dimension).agg(
            segment_closed=("opportunity_id", "size"),
            segment_won=("is_won", "sum"),
        ).reset_index()
        segment_base["segment_win_rate"] = segment_base["segment_won"] / segment_base["segment_closed"]
        grouped = data.groupby(["sales_agent_id", dimension]).agg(
            seller_segment_closed=("opportunity_id", "size"),
            seller_segment_won=("is_won", "sum"),
            seller_segment_revenue=("close_value", "sum"),
            seller_segment_median_value=("close_value", "median"),
        ).reset_index()
        grouped = grouped.merge(
            sellers[
                [
                    "sales_agent_id",
                    "sales_agent",
                    "manager",
                    "regional_office",
                    "seller_closed",
                    "seller_win_rate",
                    "seller_smoothed_win_rate",
                ]
            ],
            on="sales_agent_id",
            how="left",
        ).merge(
            segment_base[[dimension, "segment_closed", "segment_win_rate"]],
            on=dimension,
            how="left",
        )
        min_n = SEGMENT_MIN_N[dimension]
        for _, row in grouped.iterrows():
            n = int(row["seller_segment_closed"])
            confidence = min(1.0, (n / max(min_n * 2, 1)) ** 0.5)
            smoothed = (
                row["seller_segment_won"] + PRIOR_WEIGHT * row["segment_win_rate"]
            ) / (row["seller_segment_closed"] + PRIOR_WEIGHT)
            uplift_vs_segment = float(smoothed - row["segment_win_rate"])
            uplift_vs_seller = float(smoothed - row["seller_smoothed_win_rate"])
            specialty_score = max(0.0, (0.65 * uplift_vs_segment + 0.35 * uplift_vs_seller)) * confidence
            if n < min_n:
                fit_strength = "insufficient_sample"
            elif specialty_score >= 0.035 and uplift_vs_segment > 0:
                fit_strength = "strong_fit"
            elif specialty_score >= 0.015 and uplift_vs_segment > 0:
                fit_strength = "possible_fit"
            elif uplift_vs_segment < -0.02:
                fit_strength = "weak_fit"
            else:
                fit_strength = "neutral"
            rows.append(
                {
                    "sales_agent_id": row["sales_agent_id"],
                    "sales_agent": row["sales_agent"],
                    "manager": row["manager"],
                    "regional_office": row["regional_office"],
                    "dimension": dimension,
                    "segment_value": row[dimension],
                    "seller_segment_closed": n,
                    "seller_segment_won": int(row["seller_segment_won"]),
                    "seller_segment_win_rate": row["seller_segment_won"] / row["seller_segment_closed"],
                    "seller_segment_smoothed_win_rate": smoothed,
                    "segment_win_rate": row["segment_win_rate"],
                    "seller_win_rate": row["seller_win_rate"],
                    "uplift_vs_segment": uplift_vs_segment,
                    "uplift_vs_seller": uplift_vs_seller,
                    "confidence_weight": confidence,
                    "specialty_score": specialty_score * 100,
                    "fit_strength": fit_strength,
                    "seller_segment_revenue": row["seller_segment_revenue"],
                    "seller_segment_median_value": row["seller_segment_median_value"],
                    "global_win_rate": global_wr,
                }
            )
    return pd.DataFrame(rows)


def fit_lookup(fit: pd.DataFrame) -> dict[FitKey, dict[str, object]]:
    lookup: dict[FitKey, dict[str, object]] = {}
    for _, row in fit.iterrows():
        key = FitKey(
            seller_id=str(row["sales_agent_id"]),
            dimension=str(row["dimension"]),
            segment_value=str(row["segment_value"]),
        )
        lookup[key] = row.to_dict()
    return lookup


def explain_match(contributions: list[tuple[str, dict[str, object], float]]) -> str:
    good = [
        f"{dimension}={fit_row['segment_value']} ({fit_row['fit_strength']}, n={int(fit_row['seller_segment_closed'])})"
        for dimension, fit_row, contribution in contributions
        if contribution > 0
        and fit_row["fit_strength"] in {"strong_fit", "possible_fit", "neutral"}
        and int(fit_row["seller_segment_closed"]) >= SEGMENT_MIN_N[dimension]
    ]
    if not good:
        return "Sem fit historico forte; recomendacao baseada em fallback de performance geral."
    return "; ".join(good[:3])


def score_candidate(
    deal: pd.Series,
    seller: pd.Series,
    fit_by_key: dict[FitKey, dict[str, object]],
) -> tuple[float, float, str, list[str]]:
    score = float(seller["seller_smoothed_win_rate"]) * 100
    usable_weight = 0.0
    contributions: list[tuple[str, dict[str, object], float]] = []
    fit_strengths: list[str] = []

    for dimension, weight in DIMENSION_WEIGHTS.items():
        value = deal.get(dimension)
        if pd.isna(value):
            continue
        key = FitKey(str(seller["sales_agent_id"]), dimension, str(value))
        fit_row = fit_by_key.get(key)
        if not fit_row:
            continue
        n = int(fit_row["seller_segment_closed"])
        if n < SEGMENT_MIN_N[dimension]:
            continue
        usable_weight += weight * float(fit_row["confidence_weight"])
        uplift = float(fit_row["uplift_vs_segment"])
        score += weight * float(fit_row["confidence_weight"]) * uplift * 100
        contributions.append((dimension, fit_row, uplift))
        fit_strengths.append(str(fit_row["fit_strength"]))

    confidence = min(1.0, usable_weight / sum(DIMENSION_WEIGHTS.values()))
    if "strong_fit" in fit_strengths:
        match_band = "specialist_match"
    elif "possible_fit" in fit_strengths:
        match_band = "possible_specialist"
    elif confidence >= 0.35:
        match_band = "generalist_match"
    else:
        match_band = "low_confidence"
    return score, confidence, match_band, [explain_match(contributions)]


def recommend_open_deals(
    open_pipeline: pd.DataFrame,
    fit: pd.DataFrame,
    sellers: pd.DataFrame,
) -> pd.DataFrame:
    candidate_sellers = sellers[sellers["seller_closed"] >= MIN_CANDIDATE_CLOSED].copy()
    fit_by_key = fit_lookup(fit)
    rows: list[dict[str, object]] = []

    for _, deal in open_pipeline.iterrows():
        candidate_rows: list[dict[str, object]] = []
        for _, seller in candidate_sellers.iterrows():
            score, confidence, match_band, reasons = score_candidate(deal, seller, fit_by_key)
            candidate_rows.append(
                {
                    "recommended_sales_agent_id": seller["sales_agent_id"],
                    "recommended_sales_agent": seller["sales_agent"],
                    "recommended_manager": seller["manager"],
                    "recommended_region": seller["regional_office"],
                    "match_score": score,
                    "match_confidence": confidence,
                    "match_band": match_band,
                    "match_reason": reasons[0],
                }
            )
        ranked = sorted(candidate_rows, key=lambda row: (row["match_score"], row["match_confidence"]), reverse=True)
        top = ranked[0]
        current = next(
            (row for row in ranked if row["recommended_sales_agent_id"] == deal["sales_agent_id"]),
            None,
        )
        current_rank = (
            next(i + 1 for i, row in enumerate(ranked) if row["recommended_sales_agent_id"] == deal["sales_agent_id"])
            if current
            else np.nan
        )
        rows.append(
            {
                "opportunity_id": deal["opportunity_id"],
                "deal_stage": deal["deal_stage"],
                "current_sales_agent_id": deal["sales_agent_id"],
                "current_sales_agent": deal["sales_agent"],
                "current_manager": deal["manager"],
                "current_region": deal["regional_office"],
                "product": deal["product"],
                "ticket_band": deal["ticket_band"],
                "estimated_deal_value": deal["estimated_deal_value"],
                "account": deal.get("account"),
                "sector": deal.get("sector"),
                "revenue_band": deal.get("revenue_band"),
                "employee_band": deal.get("employee_band"),
                "days_open_as_of_snapshot": deal.get("days_open_as_of_snapshot"),
                "account_known": deal.get("account_known"),
                **top,
                "current_match_score": current["match_score"] if current else np.nan,
                "current_match_confidence": current["match_confidence"] if current else np.nan,
                "current_match_band": current["match_band"] if current else "not_candidate",
                "current_specialist_rank": current_rank,
                "recommended_differs_from_current": top["recommended_sales_agent_id"] != deal["sales_agent_id"],
            }
        )
    return pd.DataFrame(rows)


def seller_best_deals(recommendations: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for seller, group in recommendations.groupby("current_sales_agent"):
        current_fit = group.copy()
        current_fit["seller_deal_score"] = current_fit["current_match_score"].fillna(0)
        current_fit["priority_score"] = (
            current_fit["seller_deal_score"]
            + np.log1p(current_fit["estimated_deal_value"].fillna(0)) * 2
            + current_fit["days_open_as_of_snapshot"].fillna(0).clip(upper=180) / 30
        )
        rows.append(current_fit.sort_values("priority_score", ascending=False).head(top_n))
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    cols = [
        "current_sales_agent",
        "opportunity_id",
        "deal_stage",
        "product",
        "ticket_band",
        "estimated_deal_value",
        "account",
        "sector",
        "days_open_as_of_snapshot",
        "current_match_score",
        "current_match_confidence",
        "current_match_band",
        "current_specialist_rank",
        "recommended_sales_agent",
        "recommended_differs_from_current",
        "priority_score",
    ]
    return out[cols]


def summarize_top_specialties(fit: pd.DataFrame) -> pd.DataFrame:
    eligible = fit[
        fit["fit_strength"].isin(["strong_fit", "possible_fit"])
        & (fit["seller_segment_closed"] >= fit["dimension"].map(SEGMENT_MIN_N))
    ].copy()
    return eligible.sort_values(
        ["specialty_score", "seller_segment_closed"], ascending=[False, False]
    ).head(30)


def write_report(
    fit: pd.DataFrame,
    recommendations: pd.DataFrame,
    seller_deals: pd.DataFrame,
    sellers: pd.DataFrame,
    seller_xray: pd.DataFrame,
) -> None:
    top_fit = summarize_top_specialties(fit).head(12)
    candidate_reassignments = recommendations[
        (recommendations["recommended_differs_from_current"])
        & (recommendations["match_confidence"] >= 0.45)
    ].sort_values(["estimated_deal_value", "match_score"], ascending=[False, False]).head(15)
    best_current = seller_deals.sort_values("priority_score", ascending=False).head(15)
    excluded = seller_xray[seller_xray["closed_opportunities"] < MIN_CANDIDATE_CLOSED].copy()

    lines = [
        "# Seller Specialty Fit",
        "",
        "Generated from standardized CSVs in `data/processed`.",
        "",
        "## Method",
        "",
        "- Historical fit uses only closed opportunities.",
        "- Open deal matching uses product, ticket band, sector, revenue band, employee band, and account when available.",
        "- Seller-segment win rates are smoothed against the segment baseline to reduce overfitting.",
        f"- Sellers need at least {MIN_CANDIDATE_CLOSED} closed opportunities to be considered specialist candidates.",
        "- Results are associative, not causal.",
        "",
        "## Strongest Apparent Specialties",
        "",
        md_table(
            top_fit,
            [
                "sales_agent",
                "dimension",
                "segment_value",
                "seller_segment_closed",
                "seller_segment_win_rate",
                "segment_win_rate",
                "uplift_vs_segment",
                "specialty_score",
                "fit_strength",
            ],
        ),
        "",
        "## High-Value Open Deals Where Suggested Specialist Differs",
        "",
        md_table(
            candidate_reassignments,
            [
                "opportunity_id",
                "deal_stage",
                "product",
                "ticket_band",
                "estimated_deal_value",
                "current_sales_agent",
                "recommended_sales_agent",
                "match_score",
                "match_confidence",
                "match_band",
                "match_reason",
            ],
        ),
        "",
        "## Best Current Deals Inside Seller Specialty",
        "",
        md_table(
            best_current,
            [
                "current_sales_agent",
                "opportunity_id",
                "deal_stage",
                "product",
                "ticket_band",
                "estimated_deal_value",
                "current_match_score",
                "current_match_confidence",
                "current_match_band",
                "recommended_sales_agent",
            ],
        ),
        "",
        "## Sellers Excluded From Specialist Candidate Pool",
        "",
        md_table(
            excluded,
            [
                "sales_agent",
                "manager",
                "regional_office",
                "closed_opportunities",
                "win_rate",
                "history_maturity",
            ],
        ),
        "",
        "## Output Files",
        "",
        "- `data/processed/seller_segment_fit.csv`",
        "- `data/processed/open_deal_specialist_recommendations.csv`",
        "- `data/processed/seller_best_fit_deals.csv`",
        "",
    ]
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "seller_specialty_fit.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    enriched, open_pipeline, seller_xray = load_data()
    closed = enriched[enriched["is_closed"]].copy()
    sellers = seller_summary(closed)

    fit = build_fit_table(closed)
    recommendations = recommend_open_deals(open_pipeline, fit, sellers)
    best_deals = seller_best_deals(recommendations)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    fit.to_csv(PROCESSED_DIR / "seller_segment_fit.csv", index=False)
    recommendations.to_csv(PROCESSED_DIR / "open_deal_specialist_recommendations.csv", index=False)
    best_deals.to_csv(PROCESSED_DIR / "seller_best_fit_deals.csv", index=False)
    write_report(fit, recommendations, best_deals, sellers, seller_xray)

    print(f"Wrote {PROCESSED_DIR / 'seller_segment_fit.csv'} rows={len(fit)}")
    print(f"Wrote {PROCESSED_DIR / 'open_deal_specialist_recommendations.csv'} rows={len(recommendations)}")
    print(f"Wrote {PROCESSED_DIR / 'seller_best_fit_deals.csv'} rows={len(best_deals)}")
    print(f"Wrote {REPORTS_DIR / 'seller_specialty_fit.md'}")


if __name__ == "__main__":
    main()
