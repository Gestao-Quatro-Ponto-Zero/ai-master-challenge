"""Product-domain features — computed from historical (Won/Lost) data only."""
from __future__ import annotations
import numpy as np
import pandas as pd


def compute_product_features(df: pd.DataFrame, train_df: pd.DataFrame) -> pd.DataFrame:
    """Add product-domain features to df."""
    won = train_df[train_df["target"] == 1].copy()

    agg = (
        train_df.groupby("product")
        .agg(
            product_win_rate       =("target",          "mean"),
            product_deal_count     =("target",          "count"),
            product_avg_deal_value =("effective_value",  "mean"),
        )
        .reset_index()
    )

    if "close_date" in won.columns and "engage_date" in won.columns:
        won = won.copy()
        won["sales_cycle"] = (
            pd.to_datetime(won["close_date"]) - pd.to_datetime(won["engage_date"])
        ).dt.days.clip(lower=0)
        cycle = won.groupby("product")["sales_cycle"].mean().rename("product_avg_sales_cycle")
        agg = agg.merge(cycle, on="product", how="left")
    else:
        agg["product_avg_sales_cycle"] = np.nan

    agg["product_rank_percentile"] = agg["product_win_rate"].rank(pct=True)

    for col in ["product_win_rate", "product_avg_deal_value", "product_avg_sales_cycle", "product_rank_percentile"]:
        if col in agg.columns:
            agg[col] = agg[col].fillna(agg[col].median())

    overlap = [c for c in agg.columns if c != "product" and c in df.columns]
    df = df.drop(columns=overlap, errors="ignore")
    return df.merge(agg, on="product", how="left")
