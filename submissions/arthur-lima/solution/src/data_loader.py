"""
Data Loader, Schema Sanitizer & Point-in-Time Feature Store.

Fixes critical dataset anomalies discovered during empirical audit:
1. Product foreign key mismatch ('GTXPro' in sales_pipeline vs 'GTX Pro' in products.csv).
2. Typo in accounts.csv sector ('technolgy' -> 'technology').
3. Missing account names in 1,425 open deals (1,088 Engaging + 337 Prospecting).
4. Anti-leakage deal value estimation via historical median close_value by (product, regional_office).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SNAPSHOT_DATE = pd.Timestamp("2017-12-31")


def normalize_product_name(series: pd.Series) -> pd.Series:
    """Fixes the foreign-key bug where 'GTXPro' in sales_pipeline lacks a space."""
    return (
        series.astype(str)
        .str.strip()
        .replace(
            {
                "GTXPro": "GTX Pro",
                "GTXPlusBasic": "GTX Plus Basic",
                "GTXPlusPro": "GTX Plus Pro",
            }
        )
    )


def load_raw_tables(data_dir: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    """Loads the 4 official CRM CSV tables with strict schema normalization."""
    base = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR

    pipeline = pd.read_csv(base / "sales_pipeline.csv")
    accounts = pd.read_csv(base / "accounts.csv")
    products = pd.read_csv(base / "products.csv")
    teams = pd.read_csv(base / "sales_teams.csv")

    # 1. Fix product key mismatch ('GTXPro' -> 'GTX Pro')
    pipeline["product_raw"] = pipeline["product"]
    pipeline["product"] = normalize_product_name(pipeline["product"])
    products["product"] = normalize_product_name(products["product"])

    # 2. Fix sector typo in accounts.csv ('technolgy' -> 'technology')
    accounts["sector"] = (
        accounts["sector"]
        .astype(str)
        .str.strip()
        .replace({"technolgy": "technology"})
    )

    # 3. Parse dates safely
    pipeline["engage_date"] = pd.to_datetime(pipeline["engage_date"], errors="coerce")
    pipeline["close_date"] = pd.to_datetime(pipeline["close_date"], errors="coerce")

    return {
        "pipeline": pipeline,
        "accounts": accounts,
        "products": products,
        "teams": teams,
    }


def compute_value_estimation_table(
    closed_won_df: pd.DataFrame, products_df: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Computes historical median & mean Won close_value per (product, regional_office)
    and evaluates Mean Absolute Error (MAE) vs catalog sales_price.
    Strictly uses Won deals in the training window to prevent target leakage.
    """
    won = closed_won_df[closed_won_df["deal_stage"] == "Won"].copy()
    catalog_map = products_df.set_index("product")["sales_price"].to_dict()

    if len(won) == 0:
        est_df = pd.DataFrame(columns=["product", "regional_office", "median_won_value"])
        return est_df, {
            "mae_median_estimator": 0.0,
            "mae_catalog_price": 0.0,
            "avg_price_realization_delta_pct": 0.0,
        }

    prod_reg = (
        won.groupby(["product", "regional_office"], as_index=False)["close_value"]
        .agg(median_won_value="median", mean_won_value="mean", won_count="count")
    )
    prod_global = won.groupby("product")["close_value"].median().to_dict()

    # Evaluate MAE on historical Won deals
    merged_eval = won.merge(prod_reg, on=["product", "regional_office"], how="left")
    merged_eval["catalog_price"] = merged_eval["product"].map(catalog_map)
    merged_eval["est_value"] = (
        merged_eval["median_won_value"]
        .fillna(merged_eval["product"].map(prod_global))
        .fillna(merged_eval["catalog_price"])
    )

    mae_median = float(
        np.mean(np.abs(merged_eval["close_value"] - merged_eval["est_value"]))
    )
    mae_catalog = float(
        np.mean(np.abs(merged_eval["close_value"] - merged_eval["catalog_price"]))
    )
    avg_discount_pct = float(
        np.mean(
            (merged_eval["close_value"] - merged_eval["catalog_price"])
            / merged_eval["catalog_price"]
        )
        * 100.0
    )

    metrics = {
        "mae_median_estimator": round(mae_median, 2),
        "mae_catalog_price": round(mae_catalog, 2),
        "avg_price_realization_delta_pct": round(avg_discount_pct, 2),
    }
    return prod_reg, metrics


def build_enriched_pipeline(
    data_dir: Optional[Path] = None,
    as_of_date: pd.Timestamp = SNAPSHOT_DATE,
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """
    Joins the 4 CRM tables, audits data quality anomalies, and constructs
    point-in-time features as of `as_of_date` with zero future data leakage.
    """
    tables = load_raw_tables(data_dir)
    pipeline = tables["pipeline"]
    accounts = tables["accounts"]
    products = tables["products"]
    teams = tables["teams"]

    # Count how many rows had the 'GTXPro' anomaly before normalization
    gtxpro_fixed_count = int((pipeline["product_raw"] == "GTXPro").sum())

    # Relational joins
    df = (
        pipeline.merge(teams, on="sales_agent", how="left")
        .merge(products, on="product", how="left")
        .merge(accounts, on="account", how="left")
    )

    # Account completeness flags (critical discovery: 68.5% of Engaging lack account!)
    df["has_account"] = df["account"].notnull() & (
        df["account"].astype(str).str.strip() != ""
    )
    df["account_display"] = np.where(
        df["has_account"], df["account"], "⚠️ Conta Não Vinculada (CRM Gap)"
    )
    df["sector_display"] = np.where(
        df["has_account"], df["sector"].fillna("unknown"), "unlinked_account"
    )
    df["is_enterprise_account"] = (df["revenue"].fillna(0) >= 2000.0) | (
        df["employees"].fillna(0) >= 5000
    )
    df["has_parent_company"] = df["subsidiary_of"].notnull() & (
        df["subsidiary_of"].astype(str).str.strip() != ""
    )

    # Filter historical closed deals strictly up to as_of_date for value estimation
    closed_before_as_of = df[
        df["deal_stage"].isin(["Won", "Lost"])
        & (df["close_date"].notnull())
        & (df["close_date"] <= as_of_date)
    ].copy()

    prod_reg_est, val_metrics = compute_value_estimation_table(
        closed_before_as_of, products
    )
    prod_global_median = (
        closed_before_as_of[closed_before_as_of["deal_stage"] == "Won"]
        .groupby("product")["close_value"]
        .median()
        .to_dict()
    )

    df = df.merge(
        prod_reg_est[["product", "regional_office", "median_won_value"]],
        on=["product", "regional_office"],
        how="left",
    )

    # Expected deal value if won (never uses actual close_value of open deals!)
    df["expected_won_value"] = (
        df["median_won_value"]
        .fillna(df["product"].map(prod_global_median))
        .fillna(df["sales_price"])
        .astype(float)
    )

    # Cycle / Aging days calculation anchored strictly at as_of_date (Point-in-Time)
    df["as_of_date"] = as_of_date
    already_closed_at_as_of = (
        df["deal_stage"].isin(["Won", "Lost"])
        & df["close_date"].notnull()
        & (df["close_date"] <= as_of_date)
    )
    df["cycle_days"] = np.where(
        already_closed_at_as_of,
        (df["close_date"] - df["engage_date"]).dt.days,
        (as_of_date - df["engage_date"]).dt.days,
    )

    audit_summary = {
        "total_rows": int(len(df)),
        "won_count": int((df["deal_stage"] == "Won").sum()),
        "lost_count": int((df["deal_stage"] == "Lost").sum()),
        "engaging_count": int((df["deal_stage"] == "Engaging").sum()),
        "prospecting_count": int((df["deal_stage"] == "Prospecting").sum()),
        "gtxpro_foreign_key_fixed": gtxpro_fixed_count,
        "missing_account_engaging": int(
            ((df["deal_stage"] == "Engaging") & (~df["has_account"])).sum()
        ),
        "missing_account_prospecting": int(
            ((df["deal_stage"] == "Prospecting") & (~df["has_account"])).sum()
        ),
        "missing_engage_date_prospecting": int(
            ((df["deal_stage"] == "Prospecting") & (df["engage_date"].isnull())).sum()
        ),
        "snapshot_date": str(as_of_date.date()),
        **val_metrics,
    }

    return df, audit_summary
