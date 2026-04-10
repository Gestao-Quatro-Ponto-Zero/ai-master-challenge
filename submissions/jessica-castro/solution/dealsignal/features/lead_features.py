"""
DealSignal — Lead & engagement feature engineering.

Computes features from previously unused pipeline columns:
lead_source, lead_origin, contact_role, lead_quality, lead_tag,
activity_count, page_views_per_visit, last_activity_type.

All target-encoded features use Bayesian smoothing (m=30) to avoid
overfitting on small groups:
    smoothed_rate = (n * group_rate + m * global_rate) / (n + m)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

SMOOTHING_PRIOR = 30  # Bayesian smoothing strength


def _target_encode(
    df: pd.DataFrame,
    train_df: pd.DataFrame,
    col: str,
    target_col: str = "target",
    output_col: str | None = None,
    m: int = SMOOTHING_PRIOR,
) -> pd.Series:
    """Target-encode a categorical column using Bayesian smoothing on train_df only."""
    output_col = output_col or f"{col}_wr"
    global_rate = train_df[target_col].mean()

    stats = train_df.groupby(col)[target_col].agg(["mean", "count"])
    stats["smoothed"] = (stats["count"] * stats["mean"] + m * global_rate) / (
        stats["count"] + m
    )
    mapping = stats["smoothed"].to_dict()
    return df[col].map(mapping).fillna(global_rate)


# ── Ordinal mapping for lead_quality ────────────────────────────────────────
LEAD_QUALITY_MAP = {
    "Low in Relevance": 0,
    "Not Sure": 1,
    "Might be": 2,
}

# ── Positive last activity types (signals engagement) ───────────────────────
POSITIVE_ACTIVITIES = {"Email Opened", "SMS Sent", "Email Link Clicked"}


def compute_lead_features(df: pd.DataFrame, train_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute lead and engagement features from unused pipeline columns.

    Parameters
    ----------
    df : Full DataFrame (train + score rows) with raw pipeline columns.
    train_df : Training subset (Won/Lost only) for target-encoding.

    Returns
    -------
    df with new columns added.
    """
    df = df.copy()

    global_rate = train_df["target"].mean() if "target" in train_df.columns else 0.5

    # ── Target-encoded categorical features ─────────────────────────────────
    for col in ["lead_source", "lead_origin", "contact_role", "last_activity_type"]:
        if col in df.columns:
            # Fill missing before encoding
            df[col] = df[col].fillna("Unknown")
            if col in train_df.columns:
                train_df = train_df.copy()
                train_df[col] = train_df[col].fillna("Unknown")
            df[f"{col}_wr"] = _target_encode(df, train_df, col)
        else:
            df[f"{col}_wr"] = global_rate

    # ── Lead quality (ordinal) ──────────────────────────────────────────────
    if "lead_quality" in df.columns:
        df["lead_quality_score"] = (
            df["lead_quality"].map(LEAD_QUALITY_MAP).fillna(1.0)  # default=Not Sure
        )
    else:
        df["lead_quality_score"] = 1.0

    # ── Numeric engagement features ─────────────────────────────────────────
    if "activity_count" in df.columns:
        df["activity_count"] = pd.to_numeric(df["activity_count"], errors="coerce").fillna(0)
    else:
        df["activity_count"] = 0.0

    if "page_views_per_visit" in df.columns:
        df["page_views_per_visit"] = pd.to_numeric(
            df["page_views_per_visit"], errors="coerce"
        ).fillna(0)
    else:
        df["page_views_per_visit"] = 0.0

    # ── Derived flags ───────────────────────────────────────────────────────
    df["has_activity"] = (df["activity_count"] > 0).astype(int)

    if "last_activity_type" in df.columns:
        df["last_activity_is_positive"] = (
            df["last_activity_type"].isin(POSITIVE_ACTIVITIES).astype(int)
        )
    else:
        df["last_activity_is_positive"] = 0

    # ── Lead tag target-encoded ─────────────────────────────────────────────
    if "lead_tag" in df.columns:
        df["lead_tag"] = df["lead_tag"].fillna("Unknown")
        if "lead_tag" in train_df.columns:
            train_df = train_df.copy()
            train_df["lead_tag"] = train_df["lead_tag"].fillna("Unknown")
        df["lead_tag_wr"] = _target_encode(df, train_df, "lead_tag")
    else:
        df["lead_tag_wr"] = global_rate

    logger.info("Lead features computed: 10 new columns added.")
    return df
