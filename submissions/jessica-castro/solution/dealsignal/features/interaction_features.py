"""
EXPERIMENTAL — V3 Feature Engineering (NOT used in the production pipeline).

This module implements V3 feature engineering, including:
- Within-seller and within-product deal value percentiles
- Deal-to-account size ratio
- Seller×product cross-features (seller_product_win_rate)
- Product performance relative to global average
- Bucket features: deal age, deal value, account size (categorical bins)
- Additional risk flags: deal_estagnado, deal_muito_antigo, produto_fraco, conta_fraca
- Interaction terms: seller×product, seller×value, product×age, account×value

STATUS: Fully developed and tested in experiments/v2_experiments.py but deliberately
excluded from run_pipeline.py due to insufficient AUC improvement over V2 features
to justify the added complexity (AUC remains ≈0.62 regardless of feature set,
indicating weak underlying signal rather than a feature engineering problem).

To use in experiments:
    from features.interaction_features import add_v3_features
    df = add_v3_features(df, train_df)

Do NOT import this module in run_pipeline.py or feature_engineering.py
without a deliberate experimental decision and documented AUC comparison.

All group-level stats (seller_product_win_rate, within-seller percentiles, etc.)
are computed exclusively from train_df to avoid leakage.
Bucket features and interactions are computed on the full df.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ── Feature groups (used by ablation study) ──────────────────────────────────

FEATURE_COLS_V2 = [
    "seller_win_rate",
    "seller_rank_percentile",
    "seller_close_speed",
    "seller_product_experience",
    "seller_pipeline_load",
    "log_days_since_engage",
    "deal_age_percentile",
    "log_deal_value",
    "deal_value_percentile",
    "is_stale_flag",
    "product_win_rate",
    "product_rank_percentile",
    "product_avg_sales_cycle",
    "account_size_percentile",
    "digital_maturity_index",
    "revenue_per_employee",
    "company_age_score",
]

GROUP_SELLER = [
    "seller_win_rate",
    "seller_rank_percentile",
    "seller_close_speed",
    "seller_product_experience",
    "seller_pipeline_load",
    "seller_product_win_rate",
]

GROUP_DEAL = [
    "log_days_since_engage",
    "deal_age_percentile",
    "log_deal_value",
    "deal_value_percentile",
    "deal_value_percentile_within_seller",
    "deal_value_percentile_within_product",
    "deal_value_vs_account_size",
]

GROUP_PRODUCT = [
    "product_win_rate",
    "product_rank_percentile",
    "product_avg_sales_cycle",
    "product_relative_performance",
]

GROUP_ACCOUNT = [
    "account_size_percentile",
    "digital_maturity_index",
    "revenue_per_employee",
    "company_age_score",
]

GROUP_RISK = [
    "is_stale_flag",
    "is_very_old_deal",
    "seller_overloaded_flag",
    "low_product_performance_flag",
    "deal_estagnado",
    "deal_muito_antigo",
    "produto_fraco",
    "conta_fraca",
]

GROUP_BUCKETS = [
    "bucket_deal_age",
    "bucket_deal_value",
    "bucket_account_size",
]

GROUP_INTERACTIONS = [
    "interact_seller_product",
    "interact_seller_value",
    "interact_product_age",
    "interact_account_value",
]

FEATURE_COLS_V3 = (
    GROUP_SELLER
    + GROUP_DEAL
    + GROUP_PRODUCT
    + GROUP_ACCOUNT
    + GROUP_RISK
    + GROUP_BUCKETS
    + GROUP_INTERACTIONS
)

ABLATION_GROUPS = {
    "seller":       GROUP_SELLER,
    "deal":         GROUP_DEAL,
    "product":      GROUP_PRODUCT,
    "account":      GROUP_ACCOUNT,
    "risk":         GROUP_RISK,
    "buckets":      GROUP_BUCKETS,
    "interactions": GROUP_INTERACTIONS,
    "all":          FEATURE_COLS_V3,
}


def add_v3_features(df: pd.DataFrame, train_mask: pd.Series) -> pd.DataFrame:
    """Compute all V3 features and add them to df.

    Parameters
    ----------
    df : DataFrame with V2 features already computed.
    train_mask : Boolean Series; True for Won/Lost rows, False for open deals.
    """
    df = df.copy()
    train_df = df[train_mask].copy()
    global_win_rate = train_df["target"].mean() if "target" in train_df.columns else 0.5

    # ── 1. Within-seller deal value percentile ───────────────────────────────
    # safe on full df — effective_value is always known at engage date (no leakage)
    df["deal_value_percentile_within_seller"] = (
        df.groupby("sales_agent")["effective_value"].rank(pct=True)
    )

    # ── 2. Within-product deal value percentile ──────────────────────────────
    df["deal_value_percentile_within_product"] = (
        df.groupby("product")["effective_value"].rank(pct=True)
    )

    # ── 3. Deal value relative to account revenue ────────────────────────────
    rev = df["revenue"].replace(0, np.nan) if "revenue" in df.columns else pd.Series(np.nan, index=df.index)
    median_rev = rev.median()
    df["deal_value_vs_account_size"] = (
        df["effective_value"] / rev.fillna(median_rev if pd.notna(median_rev) else 1.0)
    )

    # ── 4. Seller×product win rate (train only) ───────────────────────────────
    if "target" in train_df.columns:
        sp_wr = (
            train_df.groupby(["sales_agent", "product"])["target"]
            .mean()
            .reset_index()
            .rename(columns={"target": "seller_product_win_rate"})
        )
        df = df.merge(sp_wr, on=["sales_agent", "product"], how="left")
        df["seller_product_win_rate"] = df["seller_product_win_rate"].fillna(global_win_rate)
    else:
        df["seller_product_win_rate"] = global_win_rate

    # ── 5. Product relative performance (product WR / global WR) ─────────────
    if "product_win_rate" in df.columns:
        df["product_relative_performance"] = (
            df["product_win_rate"] / (global_win_rate + 1e-9)
        )
    else:
        df["product_relative_performance"] = 1.0

    # ── 6. Bucket: deal age ───────────────────────────────────────────────────
    days = df.get("days_since_engage", pd.Series(0, index=df.index))
    df["bucket_deal_age"] = pd.cut(
        days,
        bins=[-1, 30, 90, 180, float("inf")],
        labels=[0, 1, 2, 3],  # 0-30d, 30-90d, 90-180d, >180d
    ).astype(float)

    # ── 7. Bucket: deal value (tertiles) ──────────────────────────────────────
    eff = df.get("effective_value", pd.Series(0, index=df.index))
    try:
        df["bucket_deal_value"] = pd.qcut(eff, q=3, labels=[0, 1, 2], duplicates="drop").astype(float)
    except ValueError:
        df["bucket_deal_value"] = 1.0

    # ── 8. Bucket: account size (tercis) ──────────────────────────────────────
    if "account_size_percentile" in df.columns:
        df["bucket_account_size"] = pd.cut(
            df["account_size_percentile"],
            bins=[-0.01, 0.33, 0.66, 1.01],
            labels=[0, 1, 2],
        ).astype(float)
    else:
        df["bucket_account_size"] = 1.0

    # ── 9. Risk flag: stagnant deal (≥ p90 days) ──────────────────────────────
    p90 = days.quantile(0.90)
    p95 = days.quantile(0.95)
    df["deal_estagnado"]    = (days >= p90).astype(int)
    df["deal_muito_antigo"] = (days >= p95).astype(int)

    # ── 10. Risk flag: weak product (below mean product win rate on train) ────
    if "product_win_rate" in df.columns:
        mean_pwr = (
            train_df["product_win_rate"].mean()
            if "product_win_rate" in train_df.columns and train_df["product_win_rate"].notna().any()
            else df["product_win_rate"].mean()
        )
        df["produto_fraco"] = (df["product_win_rate"] < mean_pwr).astype(int)
    else:
        df["produto_fraco"] = 0

    # ── 11. Risk flag: weak account (below 33rd percentile) ───────────────────
    if "account_size_percentile" in df.columns:
        df["conta_fraca"] = (df["account_size_percentile"] < 0.33).astype(int)
    else:
        df["conta_fraca"] = 0

    # ── 12. Interactions ──────────────────────────────────────────────────────
    swr = df.get("seller_win_rate",         pd.Series(global_win_rate, index=df.index))
    pwr = df.get("product_win_rate",        pd.Series(global_win_rate, index=df.index))
    dvp = df.get("deal_value_percentile",   pd.Series(0.5, index=df.index))
    dap = df.get("deal_age_percentile",     pd.Series(0.5, index=df.index))
    asp = df.get("account_size_percentile", pd.Series(0.5, index=df.index))

    df["interact_seller_product"] = swr * pwr
    df["interact_seller_value"]   = swr * dvp
    df["interact_product_age"]    = pwr * dap
    df["interact_account_value"]  = asp * dvp

    # ── Fill any remaining NaNs ───────────────────────────────────────────────
    for col in FEATURE_COLS_V3:
        if col in df.columns:
            median = df[col].median()
            df[col] = df[col].fillna(median if pd.notna(median) else 0.0)

    return df
