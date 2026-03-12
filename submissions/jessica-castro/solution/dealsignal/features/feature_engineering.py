"""
DealSignal — Feature engineering orchestrator.

Coordinates the full feature-building pipeline:
  1. merge_raw_data()   — joins CSVs, computes base numeric columns
  2. Target column      — maps Won/Lost → 1/0
  3. V1 agent/product stats (leakage-safe, training rows only)
  4. V2 feature modules — deal, seller, product, account, risk
"""

from typing import Tuple

import pandas as pd

from features.data_merger import merge_raw_data
from features.feature_columns import FEATURE_COLS, FEATURE_COLS_V2
from features.deal_features import compute_deal_features
from features.seller_features import compute_seller_features
from features.product_features import compute_product_features
from features.account_features import compute_account_features
from features.risk_features import compute_risk_features
from utils.logger import get_logger

logger = get_logger(__name__)


def _compute_agent_stats(train_df: pd.DataFrame) -> pd.DataFrame:
    """Computes V1 agent win-rate and avg deal value from training rows only."""
    def _agg(g):
        return pd.Series({
            "agent_win_rate": (g["target"] == 1).mean(),
            "agent_avg_deal_value": (
                g.loc[g["target"] == 1, "effective_value"].mean()
                if (g["target"] == 1).any() else 0.0
            ),
        })
    return (
        train_df.groupby("sales_agent")[["target", "effective_value"]]
        .apply(_agg)
        .reset_index()
    )


def _compute_product_stats(train_df: pd.DataFrame) -> pd.DataFrame:
    """Computes V1 product win-rate and avg deal value from training rows only."""
    def _agg(g):
        return pd.Series({
            "product_win_rate": (g["target"] == 1).mean(),
            "product_avg_deal_value": (
                g.loc[g["target"] == 1, "effective_value"].mean()
                if (g["target"] == 1).any() else 0.0
            ),
        })
    return (
        train_df.groupby("product")[["target", "effective_value"]]
        .apply(_agg)
        .reset_index()
    )


def build_features(
    pipeline_df: pd.DataFrame,
    accounts_df: pd.DataFrame,
    products_df: pd.DataFrame,
    teams_df: pd.DataFrame,
    enriched_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Builds the full feature matrix from raw source DataFrames.

    Returns
    -------
    df     : DataFrame with all feature columns (train + score rows)
    target : Series with 1/Won, 0/Lost, NaN/open for each row
    """
    # Derive reference date before merging (used for company_age reproducibility)
    raw_dates = pd.to_datetime(pipeline_df["close_date"], errors="coerce")
    dataset_end = raw_dates.max()

    df = merge_raw_data(pipeline_df, accounts_df, products_df, teams_df, enriched_df, dataset_end)

    # ── Target ────────────────────────────────────────────────────────────────
    df["target"] = df["deal_stage"].map({"Won": 1, "Lost": 0})

    # ── V1 agent/product stats (leakage-safe — training rows only) ────────────
    train_mask = df["target"].notna()
    train_df   = df[train_mask].copy()

    agent_stats   = _compute_agent_stats(train_df)
    product_stats = _compute_product_stats(train_df)

    pop_win_rate = train_df["target"].mean()
    pop_avg_val  = train_df.loc[train_df["target"] == 1, "effective_value"].mean()

    df = df.merge(agent_stats, on="sales_agent", how="left")
    df["agent_win_rate"]       = df["agent_win_rate"].fillna(pop_win_rate)
    df["agent_avg_deal_value"] = df["agent_avg_deal_value"].fillna(pop_avg_val)

    df = df.merge(product_stats, on="product", how="left")
    df["product_win_rate"]       = df["product_win_rate"].fillna(pop_win_rate)
    df["product_avg_deal_value"] = df["product_avg_deal_value"].fillna(pop_avg_val)

    # Final fill for any remaining NaNs in V1 feature cols
    for col in FEATURE_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median() if df[col].notna().any() else 0)

    # ── V2 feature modules ────────────────────────────────────────────────────
    # Re-derive train_mask after merge (index may have shifted)
    train_mask = df["target"].notna()
    df = compute_deal_features(df)
    df = compute_seller_features(df, df[train_mask].copy())
    df = compute_product_features(df, df[train_mask].copy())
    df = compute_account_features(df, reference_date=dataset_end)
    df = compute_risk_features(df)

    logger.info(
        "Feature matrix: %d rows, %d V2 feature cols. Train=%d, Score=%d",
        len(df),
        len(FEATURE_COLS_V2),
        train_mask.sum(),
        (~train_mask).sum(),
    )

    target = df["target"]
    return df, target
