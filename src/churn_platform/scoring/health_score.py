"""SPEC-5: Health Score (0-100) com 4 pilares e 5 tiers."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

TIERS = [
    (0, 40, "Critical"),
    (41, 60, "At Risk"),
    (61, 75, "Neutral"),
    (76, 90, "Healthy"),
    (91, 100, "Champion"),
]


def compute_pillar_scores(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    # Usage pillar (0-100)
    usage_level = result["total_usage_count"] / result["total_usage_count"].max() * 100 if "total_usage_count" in result.columns else 50
    feature_adoption = result["unique_features"] / result["unique_features"].max() * 100 if "unique_features" in result.columns else 50
    error_rate_inv = 100 - ((result["total_error_count"] / result["total_usage_count"].replace(0, 1)) * 100) if "total_error_count" in result.columns else 50

    result["pillar_usage"] = (
        usage_level * 0.30
        + feature_adoption * 0.35
        + error_rate_inv * 0.35
    ).clip(0, 100)

    # Support pillar (0-100)
    if "avg_satisfaction" in result.columns:
        satisfaction_score = (result["avg_satisfaction"].fillna(3) / 5) * 100
    else:
        satisfaction_score = pd.Series(50, index=result.index)
    has_escalation = (result["escalation_count"] > 0).astype(int) * (-30) + 100 if "escalation_count" in result.columns else pd.Series(70, index=result.index)
    low_tickets = 100 - (result["total_tickets"].fillna(0) / result["total_tickets"].max() * 50) if "total_tickets" in result.columns else pd.Series(70, index=result.index)

    result["pillar_support"] = (
        satisfaction_score * 0.40
        + has_escalation * 0.40
        + low_tickets * 0.20
    ).clip(0, 100)

    # Engagement pillar (0-100)
    usage_days_score = result["usage_days"] / result["usage_days"].max() * 100 if "usage_days" in result.columns else pd.Series(50, index=result.index)
    if "beta_feature_used" in result.columns:
        col = result["beta_feature_used"].where(result["beta_feature_used"].notna(), False)
        beta_score = col.astype(int) * 100
    else:
        beta_score = pd.Series(0, index=result.index)

    result["pillar_engagement"] = (
        usage_days_score * 0.60
        + beta_score * 0.40
    ).clip(0, 100)

    # Financial pillar (0-100)
    downgrade_penalty = result["downgrade_flag"].fillna(False).astype(int) * (-30) + 100 if "downgrade_flag" in result.columns else pd.Series(90, index=result.index)
    monthly_penalty = ((result["billing_frequency"] == "monthly").fillna(False).astype(int) * (-15) + 100) if "billing_frequency" in result.columns else pd.Series(90, index=result.index)

    result["pillar_financial"] = (
        downgrade_penalty * 0.50
        + monthly_penalty * 0.50
    ).clip(0, 100)

    return result


def compute_health_score(
    df: pd.DataFrame,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    if weights is None:
        weights = {"usage": 0.35, "support": 0.25, "engagement": 0.20, "financial": 0.20}

    result = compute_pillar_scores(df)
    result["health_score"] = (
        result["pillar_usage"] * weights["usage"]
        + result["pillar_support"] * weights["support"]
        + result["pillar_engagement"] * weights["engagement"]
        + result["pillar_financial"] * weights["financial"]
    ).clip(0, 100)

    def assign_tier(score: float) -> str:
        for lo, hi, label in TIERS:
            if lo <= score <= hi:
                return label
        return "Unknown"

    result["health_tier"] = result["health_score"].apply(assign_tier)

    n = len(result)
    logger.info("Health Score distribution:")
    for lo, hi, label in TIERS:
        count = ((result["health_score"] >= lo) & (result["health_score"] <= hi)).sum()
        pct = count / n * 100
        bar = "█" * int(pct / 5)
        logger.info("  %-12s (%2d-%3d): %3d (%5.1f%%) %s", label, lo, hi, count, pct, bar)

    return result


def run(df: pd.DataFrame, config: dict[str, Any] | None = None) -> pd.DataFrame:
    logger.info("=== Health Score ===")
    weights = None
    if config and "scoring" in config:
        pillars = config["scoring"]["health_score"]["pillars"]
        weights = {k: v["weight"] for k, v in pillars.items()}
    return compute_health_score(df, weights)
