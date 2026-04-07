"""Seller-domain features — computed from historical (Won/Lost) data only."""
from __future__ import annotations
import numpy as np
import pandas as pd


def compute_seller_features(df: pd.DataFrame, train_df: pd.DataFrame) -> pd.DataFrame:
    """Add seller-domain features to df.

    All stats derived exclusively from train_df (Won/Lost deals) to avoid leakage.
    seller_pipeline_load is the only feature derived from the full df (open deals).
    """
    won = train_df[train_df["target"] == 1].copy()

    agg = (
        train_df.groupby("sales_agent")
        .agg(
            seller_win_rate       =("target",          "mean"),
            seller_deal_count     =("target",          "count"),
            seller_avg_deal_value =("effective_value",  "mean"),
        )
        .reset_index()
    )

    if "close_date" in won.columns and "engage_date" in won.columns:
        won = won.copy()
        won["close_speed"] = (
            pd.to_datetime(won["close_date"]) - pd.to_datetime(won["engage_date"])
        ).dt.days.clip(lower=0)
        speed = won.groupby("sales_agent")["close_speed"].mean().rename("seller_close_speed")
        agg = agg.merge(speed, on="sales_agent", how="left")
    else:
        agg["seller_close_speed"] = np.nan

    agg["seller_rank_percentile"] = agg["seller_win_rate"].rank(pct=True)

    open_mask = df["target"].isna() if "target" in df.columns else pd.Series(True, index=df.index)
    load = (
        df[open_mask]
        .groupby("sales_agent")
        .size()
        .rename("seller_pipeline_load")
    )
    agg = agg.merge(load, on="sales_agent", how="left")
    agg["seller_pipeline_load"] = agg["seller_pipeline_load"].fillna(0)

    df = df.merge(agg, on="sales_agent", how="left")

    prod_exp = (
        train_df.groupby(["sales_agent", "product"])
        .size()
        .reset_index(name="seller_product_experience")
    )
    df = df.merge(prod_exp, on=["sales_agent", "product"], how="left")
    df["seller_product_experience"] = df["seller_product_experience"].fillna(0)

    for col in ["seller_win_rate", "seller_close_speed", "seller_avg_deal_value", "seller_rank_percentile"]:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    return df
