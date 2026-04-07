"""Deal Health Engine — rule-based score for current pipeline health.

Answers: 'Is this deal healthy TODAY?' independently of historical win probability.
"""
from __future__ import annotations
import pandas as pd

from config.constants import HEALTH_BINS, HEALTH_LABELS


def compute_deal_health(df: pd.DataFrame) -> pd.DataFrame:
    """Compute deal_health_score (0-100) and deal_health_status for each deal."""
    df = df.copy()
    scores = pd.DataFrame(index=df.index)

    age_pct = df.get("deal_age_percentile", pd.Series(0.5, index=df.index)).fillna(0.5)
    scores["age_score"] = 1.0 - age_pct

    stale      = df.get("is_stale_flag",    pd.Series(0, index=df.index)).fillna(0)
    very_old   = df.get("is_very_old_deal", pd.Series(0, index=df.index)).fillna(0)
    scores["stale_score"] = (1.0 - stale * 0.3 - very_old * 0.2).clip(0.0, 1.0)

    overloaded = df.get("seller_overloaded_flag", pd.Series(0, index=df.index)).fillna(0)
    scores["load_score"] = (1.0 - overloaded * 0.2).clip(0.0, 1.0)

    prod_pct = df.get("product_rank_percentile", pd.Series(0.5, index=df.index)).fillna(0.5)
    scores["product_score"] = prod_pct

    weights = {"age_score": 0.40, "stale_score": 0.30, "load_score": 0.15, "product_score": 0.15}
    health_raw = sum(scores[k] * w for k, w in weights.items())

    df["deal_health_score"]  = (health_raw * 100).round(1)
    df["deal_health_status"] = pd.cut(
        df["deal_health_score"],
        bins=HEALTH_BINS,
        labels=HEALTH_LABELS,
    ).astype(str)

    return df
