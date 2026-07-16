"""SPEC-4: Segmentação de churn por dimensões."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def churn_rate_by(
    df: pd.DataFrame,
    group_col: str,
    churn_col: str = "churn_flag",
    min_samples: int = 3,
) -> pd.DataFrame:
    grp = df.groupby(group_col)[churn_col].agg(["mean", "sum", "count"]).reset_index()
    grp.columns = [group_col, "churn_rate", "churned", "total"]
    grp = grp[grp["total"] >= min_samples].sort_values("churn_rate", ascending=False)
    grp["pct_of_total_churn"] = grp["churned"] / grp["churned"].sum()
    return grp


def segment_summary(
    df: pd.DataFrame,
    churn_col: str = "churn_flag",
    mrr_col: str = "mrr_amount",
) -> list[dict[str, Any]]:
    segments = ["industry", "plan_tier", "country", "referral_source", "billing_frequency"]
    results = []

    for seg in segments:
        if seg not in df.columns:
            continue
        rates = churn_rate_by(df, seg, churn_col)
        mrr_impact = df.groupby(seg).apply(
            lambda g: {
                "total_mrr": g[mrr_col].sum(),
                "mrr_lost": g.loc[g[churn_col], mrr_col].sum(),
                "avg_mrr_lost": g.loc[g[churn_col], mrr_col].mean(),
            },
            include_groups=False,
        ).reset_index() if seg in df.columns else pd.DataFrame()

        results.append({
            "segment": seg,
            "config": df[seg].dtype.name if seg in df.columns else "N/A",
            "churn_rates": rates.to_dict("records"),
            "mrr_impact": mrr_impact.to_dict("records") if not mrr_impact.empty else [],
        })
        logger.info(
            "  %s: %s segmentos, maior taxa = %.1f%%",
            seg, len(rates),
            rates["churn_rate"].max() * 100 if not rates.empty else 0,
        )

    return results


def run(df: pd.DataFrame, config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    logger.info("=== Segmentação ===")
    return segment_summary(df)
