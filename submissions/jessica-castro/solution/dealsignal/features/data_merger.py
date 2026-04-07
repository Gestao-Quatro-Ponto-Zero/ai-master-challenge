"""
DealSignal — Raw data merge layer.

Responsible for joining the four source CSVs (pipeline, accounts, products, teams)
with the enriched accounts table and computing the base numeric columns required
by all downstream feature modules.

This layer has no knowledge of the model or feature engineering logic; it only
produces a clean, wide DataFrame ready for the feature computation step.
"""

import pandas as pd

from features.feature_columns import STAGE_INDEX, normalize_product_names
from utils.logger import get_logger

logger = get_logger(__name__)


def merge_raw_data(
    pipeline_df: pd.DataFrame,
    accounts_df: pd.DataFrame,
    products_df: pd.DataFrame,
    teams_df: pd.DataFrame,
    enriched_df: pd.DataFrame,
    dataset_end: pd.Timestamp,
) -> pd.DataFrame:
    """
    Joins all source DataFrames and computes base numeric columns.

    Parameters
    ----------
    pipeline_df : raw sales_pipeline rows
    accounts_df : account master (unused directly; enriched_df supersedes it)
    products_df : product catalogue with sales_price
    teams_df    : sales team hierarchy (agent → manager → office)
    enriched_df : accounts enriched with BrasilAPI + BuiltWith + Similarweb data
    dataset_end : reference date derived from the latest close_date in pipeline_df;
                  used for company_age computation to ensure reproducibility

    Returns
    -------
    pd.DataFrame with all source columns merged plus derived base columns:
        snapshot_date, days_since_engage, stage_index, pipeline_velocity,
        effective_value, close_value, deal_value_percentile,
        office, manager, revenue, employees, revenue_per_employee,
        company_age, company_age_score, digital_maturity_index,
        digital_presence_score, tech_stack_count
    """
    df = normalize_product_names(pipeline_df.copy())

    # ── Schema normalisation ──────────────────────────────────────────────────
    # Support datasets that use 'final_status' instead of 'deal_stage'
    if "deal_stage" not in df.columns and "final_status" in df.columns:
        df["deal_stage"] = df["final_status"]

    # ── Date-based vs numeric-time schema ────────────────────────────────────
    has_dates = "engage_date" in df.columns and "close_date" in df.columns

    if has_dates:
        df["engage_date"] = pd.to_datetime(df["engage_date"], errors="coerce")
        df["close_date"]  = pd.to_datetime(df["close_date"],  errors="coerce")
        # Drop rows with no engagement date or no account
        df = df.dropna(subset=["engage_date"])
        df = df[df["account"].notna() & (df["account"] != "")]
        df["snapshot_date"]     = df["close_date"].fillna(dataset_end)
        df["days_since_engage"] = (df["snapshot_date"] - df["engage_date"]).dt.days.clip(lower=0)
    else:
        # Numeric schema: engagement_time is already the number of days engaged
        df = df[df["account"].notna() & (df["account"] != "")]
        df["engage_date"]       = pd.NaT
        df["close_date"]        = pd.NaT
        df["snapshot_date"]     = pd.NaT
        df["days_since_engage"] = pd.to_numeric(
            df.get("engagement_time", 0), errors="coerce"
        ).fillna(0).clip(lower=0)

    df["stage_index"]       = df["deal_stage"].map(STAGE_INDEX).fillna(2)
    df["pipeline_velocity"] = df["days_since_engage"] / df["stage_index"].replace(0, 1)

    # ── Product join — provides sales_price (skip if already in pipeline) ─────
    products_clean = products_df.copy()
    products_clean.columns = products_clean.columns.str.strip()
    if "sales_price" not in df.columns:
        df = df.merge(products_clean[["product", "sales_price"]], on="product", how="left")
    else:
        # pipeline already carries sales_price; enrich only if product catalog has new info
        price_map = products_clean.set_index("product")["sales_price"].to_dict()
        df["sales_price"] = df["sales_price"].combine_first(
            df["product"].map(price_map)
        )

    # close_value is preserved for expected_revenue output ONLY — never used as a feature.
    # Using close_value as a feature leaks the target: Lost deals have close_value=0,
    # Won deals have close_value>0, so the model would trivially predict from it.
    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce")

    # effective_value = list price (known at engagement time) — no leakage
    df["effective_value"]     = pd.to_numeric(df["sales_price"], errors="coerce").fillna(0)
    df["deal_value_percentile"] = df["effective_value"].rank(pct=True)

    # ── Teams join — provides manager and office ──────────────────────────────
    teams_clean = teams_df.rename(columns={"regional_office": "office"})
    df = df.merge(
        teams_clean[["sales_agent", "manager", "office"]],
        on="sales_agent",
        how="left",
    )

    # ── Enriched accounts join ────────────────────────────────────────────────
    df = df.merge(
        enriched_df[[
            "account", "revenue", "employees", "year_established",
            "digital_maturity_index", "digital_presence_score", "tech_stack_count",
        ]],
        on="account",
        how="left",
    )

    # ── Account strength base columns ─────────────────────────────────────────
    df["revenue"]             = pd.to_numeric(df["revenue"],   errors="coerce").fillna(0)
    df["employees"]           = pd.to_numeric(df["employees"], errors="coerce").fillna(1)
    df["revenue_per_employee"] = df["revenue"] / df["employees"].replace(0, 1)

    reference_year = int(dataset_end.year) if (dataset_end is not None and pd.notna(dataset_end)) else pd.Timestamp.now().year
    df["year_established"] = pd.to_numeric(df["year_established"], errors="coerce")
    df["company_age"]      = (reference_year - df["year_established"]).clip(lower=0).fillna(0)

    ca_min = df["company_age"].min()
    ca_max = df["company_age"].max()
    if ca_max > ca_min:
        df["company_age_score"] = (df["company_age"] - ca_min) / (ca_max - ca_min)
    else:
        df["company_age_score"] = 0.5

    # ── Enrichment numeric coercion + median fill ─────────────────────────────
    for col in ["digital_maturity_index", "digital_presence_score", "tech_stack_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    logger.info(
        "merge_raw_data: %d rows after filtering. dataset_end=%s",
        len(df),
        str(dataset_end)[:10],
    )
    return df
