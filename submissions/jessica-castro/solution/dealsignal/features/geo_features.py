"""
DealSignal — Geographic feature engineering.

Computes features from the 'country' column in the sales pipeline,
using target-encoding with Bayesian smoothing.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

SMOOTHING_PRIOR = 30


def compute_geo_features(df: pd.DataFrame, train_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute geographic features.

    Parameters
    ----------
    df : Full DataFrame (train + score rows).
    train_df : Training subset (Won/Lost only) for target-encoding.

    Returns
    -------
    df with new columns: country_wr, is_india.
    """
    df = df.copy()

    global_rate = train_df["target"].mean() if "target" in train_df.columns else 0.5

    # ── Country target-encoded ──────────────────────────────────────────────
    if "country" in df.columns:
        df["country"] = df["country"].fillna("Unknown")
        train_copy = train_df.copy()
        if "country" in train_copy.columns:
            train_copy["country"] = train_copy["country"].fillna("Unknown")

        stats = train_copy.groupby("country")["target"].agg(["mean", "count"])
        m = SMOOTHING_PRIOR
        stats["smoothed"] = (stats["count"] * stats["mean"] + m * global_rate) / (
            stats["count"] + m
        )
        mapping = stats["smoothed"].to_dict()
        df["country_wr"] = df["country"].map(mapping).fillna(global_rate)

        # ── Binary flag for dominant country ────────────────────────────────
        df["is_india"] = (df["country"] == "India").astype(int)
    else:
        df["country_wr"] = global_rate
        df["is_india"] = 0

    logger.info("Geo features computed: 2 new columns added.")
    return df
