from typing import Tuple

import numpy as np
import pandas as pd

from utils.logger import get_logger
from features.deal_features import compute_deal_features
from features.seller_features import compute_seller_features
from features.product_features import compute_product_features
from features.account_features import compute_account_features
from features.risk_features import compute_risk_features

logger = get_logger(__name__)

PRODUCT_NAME_MAP = {"GTXPro": "GTX Pro"}

STAGE_INDEX = {
    "Prospecting": 1,
    "Engaging": 2,
    "Won": 3,
    "Lost": 3,
}

FEATURE_COLS = [
    "days_since_engage",
    "pipeline_velocity",
    "effective_value",
    "deal_value_percentile",
    "agent_win_rate",
    "agent_avg_deal_value",
    "product_win_rate",
    "product_avg_deal_value",
    "revenue",
    "employees",
    "revenue_per_employee",
    "company_age",
    "company_age_score",
    "digital_maturity_index",
    "digital_presence_score",
    "tech_stack_count",
]

FEATURE_COLS_V2: list[str] = [
    "seller_win_rate",
    "seller_rank_percentile",
    "seller_close_speed",
    "seller_product_experience",
    "seller_pipeline_load",
    "log_days_since_engage",  # deal_age_percentile excluded (collinear)
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


def normalize_product_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["product"] = df["product"].replace(PRODUCT_NAME_MAP)
    return df


def _compute_agent_stats(train_df: pd.DataFrame) -> pd.DataFrame:
    def _agg(g):
        return pd.Series(
            {
                "agent_win_rate": (g["target"] == 1).mean(),
                "agent_avg_deal_value": g.loc[g["target"] == 1, "effective_value"].mean()
                if (g["target"] == 1).any()
                else 0.0,
            }
        )
    stats = (
        train_df.groupby("sales_agent")[["target", "effective_value"]]
        .apply(_agg)
        .reset_index()
    )
    return stats


def _compute_product_stats(train_df: pd.DataFrame) -> pd.DataFrame:
    def _agg(g):
        return pd.Series(
            {
                "product_win_rate": (g["target"] == 1).mean(),
                "product_avg_deal_value": g.loc[g["target"] == 1, "effective_value"].mean()
                if (g["target"] == 1).any()
                else 0.0,
            }
        )
    stats = (
        train_df.groupby("product")[["target", "effective_value"]]
        .apply(_agg)
        .reset_index()
    )
    return stats


def build_features(
    pipeline_df: pd.DataFrame,
    accounts_df: pd.DataFrame,
    products_df: pd.DataFrame,
    teams_df: pd.DataFrame,
    enriched_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.Series]:
    df = normalize_product_names(pipeline_df.copy())

    # Parse dates
    df["engage_date"] = pd.to_datetime(df["engage_date"], errors="coerce")
    df["close_date"] = pd.to_datetime(df["close_date"], errors="coerce")

    # Drop rows with no account or no engage_date
    df = df.dropna(subset=["engage_date"])
    df = df[df["account"].notna() & (df["account"] != "")]

    # Snapshot date per deal
    dataset_end = df["close_date"].max()
    df["snapshot_date"] = df["close_date"].fillna(dataset_end)
    df["days_since_engage"] = (df["snapshot_date"] - df["engage_date"]).dt.days.clip(lower=0)

    # Stage index
    df["stage_index"] = df["deal_stage"].map(STAGE_INDEX).fillna(2)

    # Pipeline velocity
    df["pipeline_velocity"] = df["days_since_engage"] / df["stage_index"].replace(0, 1)

    # Join products for sales_price
    products_df = products_df.copy()
    products_df.columns = products_df.columns.str.strip()
    df = df.merge(products_df[["product", "sales_price"]], on="product", how="left")

    # close_value preserved for expected_revenue output ONLY — never used as a feature.
    # Using close_value as a feature leaks the target: Lost deals have close_value=0,
    # Won deals have close_value>0, so the model would trivially predict from it.
    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce")

    # effective_value = sales_price (list price) for ALL deals — no leakage
    df["effective_value"] = pd.to_numeric(df["sales_price"], errors="coerce").fillna(0)

    # Deal value percentile (based on list price, consistent for train and score)
    df["deal_value_percentile"] = df["effective_value"].rank(pct=True)

    # Join teams
    teams_df = teams_df.rename(columns={"regional_office": "office"})
    df = df.merge(
        teams_df[["sales_agent", "manager", "office"]],
        on="sales_agent",
        how="left",
    )

    # Join accounts
    accounts_enriched = enriched_df.copy()
    df = df.merge(
        accounts_enriched[[
            "account", "revenue", "employees", "year_established",
            "digital_maturity_index", "digital_presence_score", "tech_stack_count",
        ]],
        on="account",
        how="left",
    )

    # Account strength features
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0)
    df["employees"] = pd.to_numeric(df["employees"], errors="coerce").fillna(1)
    df["revenue_per_employee"] = df["revenue"] / df["employees"].replace(0, 1)

    reference_year = int(dataset_end.year) if pd.notna(dataset_end) else 2017
    df["year_established"] = pd.to_numeric(df["year_established"], errors="coerce")
    df["company_age"] = (reference_year - df["year_established"]).clip(lower=0).fillna(0)

    ca_min = df["company_age"].min()
    ca_max = df["company_age"].max()
    if ca_max > ca_min:
        df["company_age_score"] = (df["company_age"] - ca_min) / (ca_max - ca_min)
    else:
        df["company_age_score"] = 0.5

    # Enrichment features — fill missing with medians
    for col in ["digital_maturity_index", "digital_presence_score", "tech_stack_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    # Target: 1 = Won, 0 = Lost (NaN for open deals)
    df["target"] = df["deal_stage"].map({"Won": 1, "Lost": 0})

    # Compute seller/product stats on TRAINING rows only (leakage-safe)
    train_mask = df["target"].notna()
    train_df = df[train_mask].copy()

    agent_stats = _compute_agent_stats(train_df)
    product_stats = _compute_product_stats(train_df)

    pop_agent_win_rate = train_df["target"].mean()
    pop_agent_avg = train_df.loc[train_df["target"] == 1, "effective_value"].mean()
    pop_product_win_rate = pop_agent_win_rate
    pop_product_avg = pop_agent_avg

    df = df.merge(agent_stats, on="sales_agent", how="left")
    df["agent_win_rate"] = df["agent_win_rate"].fillna(pop_agent_win_rate)
    df["agent_avg_deal_value"] = df["agent_avg_deal_value"].fillna(pop_agent_avg)

    df = df.merge(product_stats, on="product", how="left")
    df["product_win_rate"] = df["product_win_rate"].fillna(pop_product_win_rate)
    df["product_avg_deal_value"] = df["product_avg_deal_value"].fillna(pop_product_avg)

    # Final fill for any remaining NaNs in feature cols
    for col in FEATURE_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median() if df[col].notna().any() else 0)

    # ── V2 feature modules ───────────────────────────────────────────────────
    df = compute_deal_features(df)
    df = compute_seller_features(df, df[train_mask].copy())
    df = compute_product_features(df, df[train_mask].copy())
    df = compute_account_features(df)
    df = compute_risk_features(df)

    logger.info(
        "Feature matrix: %d rows, %d feature cols. Train=%d, Score=%d",
        len(df),
        len(FEATURE_COLS),
        train_mask.sum(),
        (~train_mask).sum(),
    )

    target = df["target"]
    return df, target
