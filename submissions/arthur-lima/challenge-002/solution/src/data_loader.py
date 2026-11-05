"""Data loading and Forensic Statistical Audit for Challenge 002 (Support Redesign).

Implements H1: empirical verification of Dataset 1 (`customer_support_tickets.csv`)
before drawing operational bottleneck conclusions, plus deterministic loading of
Dataset 2 (`all_tickets_processed_improved_v3.csv`).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from scipy import stats


DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FALLBACK_DATA_DIR = (
    Path(__file__).resolve().parents[4] / "challenges" / "process-002-support" / "data"
)


def resolve_data_file(filename: str, data_dir: Path | None = None) -> Path:
    """Resolves dataset path inside `solution/data/` with fallback to challenge folder."""
    candidates = []
    if data_dir is not None:
        candidates.append(Path(data_dir) / filename)
    candidates.append(DEFAULT_DATA_DIR / filename)
    candidates.append(FALLBACK_DATA_DIR / filename)
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(
        f"Arquivo de dados '{filename}' não encontrado em {candidates}."
    )


def load_support_datasets(
    data_dir: Path | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Loads Dataset 1 (consumer support metrics) and Dataset 2 (IT service tickets)."""
    d1_path = resolve_data_file("customer_support_tickets.csv", data_dir)
    d2_path = resolve_data_file("all_tickets_processed_improved_v3.csv", data_dir)
    df_d1 = pd.read_csv(d1_path)
    df_d2 = pd.read_csv(d2_path)
    return df_d1, df_d2


# H1 — Auditoria forense e testes de hipótese/permutação sobre o Dataset 1.
# Combina evidências determinísticas de corrupção de template/timestamps (100% de
# `{product_purchased}` literal e 49,3% de durações negativas) com testes ANOVA,
# Kruskal-Wallis e Permutação Monte Carlo que não detectam diferenças significativas
# entre canais, prioridades, tipos ou assuntos (p > 0.27).
def audit_dataset1_forensics(
    df_d1: pd.DataFrame, n_permutations: int = 300, random_state: int = 42
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Enriches Dataset 1 with parsed timestamps and runs forensic statistical checks:
    - Uninterpolated `{product_purchased}` placeholder rate
    - Backlog ratio (`Open` + `Pending Customer Response`)
    - Priority distribution across the 4 levels (`High` + `Critical` share)
    - Negative resolution intervals (`Time to Resolution < First Response Time`)
    - One-way ANOVA, Kruskal-Wallis, and Permutation Test p-values across dimensions
    """
    df = df_d1.copy()
    frt = pd.to_datetime(df["First Response Time"], errors="coerce")
    ttr = pd.to_datetime(df["Time to Resolution"], errors="coerce")

    df["frt_ts"] = frt
    df["ttr_ts"] = ttr
    df["resolution_delta_hours"] = (ttr - frt).dt.total_seconds() / 3600.0
    df["has_literal_placeholder"] = (
        df["Ticket Description"]
        .fillna("")
        .str.contains("{product_purchased}", regex=False)
    )
    df["is_backlog"] = df["Ticket Status"].isin(
        ["Open", "Pending Customer Response"]
    )
    df["is_high_or_critical"] = df["Ticket Priority"].isin(["High", "Critical"])

    closed = df[df["Ticket Status"] == "Closed"].copy()
    valid_delta = closed["resolution_delta_hours"].dropna()
    neg_count = int((valid_delta < 0).sum())
    closed_count = int(len(closed))

    # ANOVA and Kruskal-Wallis tests across operational dimensions
    dimension_tests: Dict[str, Dict[str, float]] = {}
    rng = np.random.default_rng(random_state)

    for col in ["Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject"]:
        csat_groups = [
            g["Customer Satisfaction Rating"].dropna().to_numpy(dtype=float)
            for _, g in closed.groupby(col)
        ]
        delta_groups = [
            g["resolution_delta_hours"].dropna().to_numpy(dtype=float)
            for _, g in closed.groupby(col)
        ]
        f_csat, p_csat = stats.f_oneway(*csat_groups)
        kw_csat, p_kw_csat = stats.kruskal(*csat_groups)
        f_delta, p_delta = stats.f_oneway(*delta_groups)
        kw_delta, p_kw_delta = stats.kruskal(*delta_groups)

        # Permutation check on between-group spread (max - min group mean CSAT)
        all_csat = closed["Customer Satisfaction Rating"].dropna().to_numpy(dtype=float)
        labels = closed.loc[
            closed["Customer Satisfaction Rating"].notnull(), col
        ].to_numpy(dtype=str)
        obs_means = pd.Series(all_csat).groupby(labels).mean()
        obs_spread = float(obs_means.max() - obs_means.min())

        exceed_count = 0
        for _ in range(n_permutations):
            perm_labels = rng.permutation(labels)
            perm_means = pd.Series(all_csat).groupby(perm_labels).mean()
            if float(perm_means.max() - perm_means.min()) >= obs_spread:
                exceed_count += 1
        perm_p = float((exceed_count + 1) / (n_permutations + 1))

        dimension_tests[col] = {
            "csat_anova_f": float(f_csat),
            "csat_anova_p": float(p_csat),
            "csat_kruskal_p": float(p_kw_csat),
            "csat_obs_spread": obs_spread,
            "csat_perm_p": perm_p,
            "delta_anova_f": float(f_delta),
            "delta_anova_p": float(p_delta),
            "delta_kruskal_p": float(p_kw_delta),
        }

    csat_clean = closed["Customer Satisfaction Rating"].dropna().to_numpy(dtype=float)
    delta_clean = closed.loc[
        closed["Customer Satisfaction Rating"].notnull(), "resolution_delta_hours"
    ].to_numpy(dtype=float)
    r_val, p_corr = stats.pearsonr(csat_clean, delta_clean)

    status_counts = df["Ticket Status"].value_counts().to_dict()
    priority_counts = df["Ticket Priority"].value_counts().to_dict()
    channel_counts = df["Ticket Channel"].value_counts().to_dict()
    type_counts = df["Ticket Type"].value_counts().to_dict()
    csat_counts = (
        closed["Customer Satisfaction Rating"]
        .value_counts()
        .sort_index()
        .to_dict()
    )

    audit: Dict[str, Any] = {
        "total_tickets": int(len(df)),
        "closed_tickets": closed_count,
        "open_tickets": int(status_counts.get("Open", 0)),
        "pending_customer_tickets": int(
            status_counts.get("Pending Customer Response", 0)
        ),
        "backlog_tickets": int(df["is_backlog"].sum()),
        "backlog_share_pct": float(df["is_backlog"].mean() * 100.0),
        "high_critical_tickets": int(df["is_high_or_critical"].sum()),
        "high_critical_share_pct": float(df["is_high_or_critical"].mean() * 100.0),
        "literal_placeholder_count": int(df["has_literal_placeholder"].sum()),
        "literal_placeholder_pct": float(
            df["has_literal_placeholder"].mean() * 100.0
        ),
        "negative_ttr_count": neg_count,
        "negative_ttr_pct": float((neg_count / max(closed_count, 1)) * 100.0),
        "mean_delta_hours": float(valid_delta.mean()),
        "median_delta_hours": float(valid_delta.median()),
        "csat_mean": float(csat_clean.mean()),
        "csat_std": float(csat_clean.std(ddof=1)),
        "csat_delta_corr_r": float(r_val),
        "csat_delta_corr_p": float(p_corr),
        "status_counts": {str(k): int(v) for k, v in status_counts.items()},
        "priority_counts": {str(k): int(v) for k, v in priority_counts.items()},
        "channel_counts": {str(k): int(v) for k, v in channel_counts.items()},
        "type_counts": {str(k): int(v) for k, v in type_counts.items()},
        "csat_distribution": {int(k): int(v) for k, v in csat_counts.items()},
        "dimension_tests": dimension_tests,
    }
    return df, audit


def build_dimension_summary_table(
    df_d1_enriched: pd.DataFrame, column: str
) -> pd.DataFrame:
    """Builds a cross-tab summary with 95% confidence intervals for a Dataset 1 dimension."""
    rows = []
    for val, grp in df_d1_enriched.groupby(column):
        closed_grp = grp[grp["Ticket Status"] == "Closed"]
        deltas = closed_grp["resolution_delta_hours"].dropna()
        csats = closed_grp["Customer Satisfaction Rating"].dropna()

        csat_mean = float(csats.mean()) if len(csats) else np.nan
        csat_ci = (
            1.96 * float(csats.std(ddof=1)) / np.sqrt(len(csats))
            if len(csats) > 1
            else np.nan
        )
        delta_mean = float(deltas.mean()) if len(deltas) else np.nan
        delta_ci = (
            1.96 * float(deltas.std(ddof=1)) / np.sqrt(len(deltas))
            if len(deltas) > 1
            else np.nan
        )

        rows.append(
            {
                "Dimensão": column,
                "Valor": str(val),
                "Total Tickets": int(len(grp)),
                "% Backlog (Open+Pending)": round(float(grp["is_backlog"].mean() * 100.0), 1),
                "Fechados": int(len(closed_grp)),
                "CSAT Médio": round(csat_mean, 3) if pd.notnull(csat_mean) else np.nan,
                "CSAT IC 95% (±)": round(csat_ci, 3) if pd.notnull(csat_ci) else np.nan,
                "Δ Tempo Médio (h)": round(delta_mean, 2) if pd.notnull(delta_mean) else np.nan,
                "Δ Tempo IC 95% (±h)": round(delta_ci, 2) if pd.notnull(delta_ci) else np.nan,
                "% Δ Tempo Negativo (TTR < FRT)": round(
                    float((deltas < 0).mean() * 100.0), 1
                )
                if len(deltas)
                else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("Total Tickets", ascending=False).reset_index(drop=True)
