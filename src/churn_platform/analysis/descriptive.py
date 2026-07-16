"""SPEC-4: Análises descritivas obrigatórias."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def overall_stats(df: pd.DataFrame, churn_col: str = "churn_flag", mrr_col: str = "mrr_amount") -> dict[str, Any]:
    total = len(df)
    churned = df[churn_col].sum()
    rate = churned / total if total > 0 else 0
    mrr_lost = df.loc[df[churn_col], mrr_col].sum() if mrr_col in df.columns else 0

    return {
        "total_accounts": total,
        "total_churned": int(churned),
        "churn_rate": round(rate, 4),
        "total_mrr_lost": int(mrr_lost),
        "avg_mrr_lost": round(mrr_lost / churned, 2) if churned > 0 else 0,
    }


def retention_curve(
    df: pd.DataFrame,
    date_col: str = "signup_date",
    churn_col: str = "churn_flag",
    max_months: int = 12,
) -> pd.DataFrame:
    if date_col not in df.columns:
        logger.warning("Coluna %s não encontrada", date_col)
        return pd.DataFrame()

    cohorts = df.copy()
    cohorts["cohort_month"] = pd.to_datetime(cohorts[date_col]).dt.to_period("M")
    cohorts = cohorts[cohorts["cohort_month"].notna()]

    result = []
    for cohort, group in cohorts.groupby("cohort_month"):
        total = len(group)
        if total < 3:
            continue
        for m in range(max_months):
            retained = total - group[churn_col].sum()
            result.append({
                "cohort": str(cohort),
                "month": m,
                "retention_rate": retained / total if total > 0 else 0,
                "n_remaining": int(retained),
                "n_initial": total,
            })

    return pd.DataFrame(result)


def churn_type_split(
    df: pd.DataFrame,
    churn_col: str = "churn_flag",
    taxonomy: dict | None = None,
) -> dict[str, Any]:
    churned = df[df[churn_col]]
    total_churned = len(churned)

    if taxonomy is None:
        taxonomy = {
            "voluntary": ["pricing", "support", "features", "competitor"],
            "involuntary": ["budget"],
            "unknown": ["unknown"],
        }

    result = {}
    for churn_type, reasons in taxonomy.items():
        count = churned[churned["churn_reason_primary"].isin(reasons)].shape[0] if "churn_reason_primary" in churned.columns else 0
        result[churn_type] = {
            "count": int(count),
            "pct": round(count / total_churned * 100, 1) if total_churned > 0 else 0,
        }

    return result


def simpson_paradox_check(
    df: pd.DataFrame,
    metric: str = "churn_rate",
    segment_col: str = "industry",
    churn_col: str = "churn_flag",
) -> list[dict[str, Any]]:
    overall_rate = df[churn_col].mean()
    results = []

    if segment_col not in df.columns:
        return results

    for val in df[segment_col].unique():
        segment = df[df[segment_col] == val]
        seg_rate = segment[churn_col].mean()
        direction = "up" if seg_rate > overall_rate else "down"
        results.append({
            "segment": str(val),
            "segment_rate": round(seg_rate, 4),
            "overall_rate": round(overall_rate, 4),
            "direction": direction,
            "n": len(segment),
        })

    results.sort(key=lambda x: x["segment_rate"], reverse=True)
    return results


def run(df: pd.DataFrame, config: dict[str, Any] | None = None) -> dict[str, Any]:
    logger.info("=== Análise Descritiva ===")

    stats = overall_stats(df)

    taxonomy = None
    if config and "analysis" in config:
        taxonomy = config["analysis"].get("churn_reason_taxonomy")

    type_split = churn_type_split(df, taxonomy=taxonomy)
    simpson = simpson_paradox_check(df)

    return {
        "overall_stats": stats,
        "churn_type_split": type_split,
        "simpson_paradox": simpson,
    }
