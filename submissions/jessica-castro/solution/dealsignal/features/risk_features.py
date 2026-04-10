"""Risk / stagnation features — capture deal health signals."""
from __future__ import annotations
import numpy as np
import pandas as pd


def compute_risk_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add risk and stagnation flags to df."""
    df = df.copy()

    days = df.get("days_since_engage", pd.Series(0, index=df.index))

    p75 = days.quantile(0.75)
    p90 = days.quantile(0.90)

    df["is_stale_flag"]    = (days >= p75).astype(int)
    df["is_very_old_deal"] = (days >= p90).astype(int)

    open_mask = (
        df["target"].isna()
        if "target" in df.columns
        else pd.Series(True, index=df.index)
    )
    pipeline_avg_days = days[open_mask].mean() if open_mask.any() else days.mean()
    df["deal_age_vs_pipeline_avg"] = days - pipeline_avg_days

    if "seller_pipeline_load" in df.columns:
        p75_load = df["seller_pipeline_load"].quantile(0.75)
        df["seller_overloaded_flag"] = (df["seller_pipeline_load"] >= p75_load).astype(int)
    else:
        df["seller_overloaded_flag"] = 0

    if "product_rank_percentile" in df.columns:
        df["low_product_performance_flag"] = (df["product_rank_percentile"] < 0.33).astype(int)
    else:
        df["low_product_performance_flag"] = 0

    return df
