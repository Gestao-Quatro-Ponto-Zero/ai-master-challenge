"""Deal-domain features."""
from __future__ import annotations
import numpy as np
import pandas as pd

STAGE_INDEX = {"Prospecting": 1, "Engaging": 2, "Won": 3, "Lost": 3}


def compute_deal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add deal-domain features to df.

    NOTE: pipeline_velocity is intentionally NOT computed here.
    In this dataset every open deal is in 'Engaging' (stage_index=2), so
    pipeline_velocity = days_since_engage / 2 — perfectly collinear.
    """
    df = df.copy()

    df["engage_date"] = pd.to_datetime(df["engage_date"], errors="coerce")
    df["close_date"]  = pd.to_datetime(df["close_date"],  errors="coerce")

    # Only recompute from dates when date columns are actually populated.
    # When the dataset uses a numeric schema (engagement_time), data_merger already
    # set days_since_engage from engagement_time — preserve it.
    has_dates = df["engage_date"].notna().any() and df["close_date"].notna().any()
    if has_dates:
        dataset_end = df["close_date"].max()
        snapshot    = df["close_date"].fillna(dataset_end)
        df["days_since_engage"] = (snapshot - df["engage_date"]).dt.days.clip(lower=0)

    df["stage_index"] = df["deal_stage"].map(STAGE_INDEX).fillna(2)
    days = df["days_since_engage"].fillna(0)
    df["log_days_since_engage"] = np.log1p(days)
    df["deal_age_percentile"]   = days.rank(pct=True)

    eff = df.get("effective_value", pd.Series(0.0, index=df.index))
    df["log_deal_value"]        = np.log1p(eff)
    df["deal_value_percentile"] = eff.rank(pct=True)

    return df
