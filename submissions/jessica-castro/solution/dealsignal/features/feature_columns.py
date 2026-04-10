"""
DealSignal — Feature column definitions and product normalisation.

Single source of truth for:
- The V1 and V2 feature column lists consumed by the model pipeline
- The stage index mapping used during data preparation
- The product name normalisation map and helper
"""

import pandas as pd

# ── Product name normalisation ────────────────────────────────────────────────
PRODUCT_NAME_MAP: dict[str, str] = {"GTXPro": "GTX Pro"}

# ── Deal stage ordinal mapping ────────────────────────────────────────────────
STAGE_INDEX: dict[str, int] = {
    "Prospecting": 1,
    "Engaging":    2,
    "Won":         3,
    "Lost":        3,
}

# ── V1 feature columns (backward-compatible, kept for experiments) ────────────
FEATURE_COLS: list[str] = [
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

# ── V2 feature columns (production — excludes collinear pipeline_velocity) ────
FEATURE_COLS_V2: list[str] = [
    "seller_win_rate",
    "seller_rank_percentile",
    "seller_close_speed",
    "seller_product_experience",
    "seller_pipeline_load",
    "log_days_since_engage",   # deal_age_percentile excluded (collinear with log_days_since_engage)
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


# ── V4 feature columns (V2 + lead/engagement + geo features) ─────────────
FEATURE_COLS_V4_LEAD: list[str] = [
    "lead_source_wr",
    "lead_origin_wr",
    "contact_role_wr",
    "last_activity_type_wr",
    "lead_quality_score",
    "activity_count",
    "page_views_per_visit",
    "has_activity",
    "last_activity_is_positive",
    "lead_tag_wr",
]

FEATURE_COLS_V4_GEO: list[str] = [
    "country_wr",
    "is_india",
]

FEATURE_COLS_V4: list[str] = FEATURE_COLS_V2 + FEATURE_COLS_V4_LEAD + FEATURE_COLS_V4_GEO


def normalize_product_names(df: pd.DataFrame) -> pd.DataFrame:
    """Applies PRODUCT_NAME_MAP to the 'product' column (returns a copy)."""
    df = df.copy()
    df["product"] = df["product"].replace(PRODUCT_NAME_MAP)
    return df
