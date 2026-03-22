"""
Tests for utils.data_loader module.

27 tests covering: basic loading, normalization, type conversions,
derived columns, referential integrity, nullability by stage, and enrichment/JOINs.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Path setup — allow imports from the solution root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.data_loader import get_active_deals, get_reference_date, load_data  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def data_dir():
    """Return the absolute path to the data/ directory."""
    return os.path.join(os.path.dirname(__file__), "..", "data")


@pytest.fixture(scope="module")
def data(data_dir):
    """Load all data once per test module via load_data()."""
    return load_data(data_dir)


# ===================================================================
# 11.1 Basic loading (5 tests)
# ===================================================================
class TestBasicLoading:
    """Verify that load_data returns properly shaped DataFrames."""

    def test_load_data_returns_dict_with_expected_keys(self, data):
        """load_data() must return a dict with keys: pipeline, accounts, products, sales_teams."""
        assert isinstance(data, dict)
        expected_keys = {"pipeline", "accounts", "products", "sales_teams"}
        assert set(data.keys()) == expected_keys

    def test_load_accounts_returns_dataframe_with_expected_columns(self, data):
        """accounts DataFrame must contain the 7 original CSV columns."""
        expected_cols = {
            "account",
            "sector",
            "year_established",
            "revenue",
            "employees",
            "office_location",
            "subsidiary_of",
        }
        assert expected_cols.issubset(set(data["accounts"].columns))

    def test_load_products_returns_exactly_7_products(self, data):
        """products DataFrame must have exactly 7 records."""
        assert len(data["products"]) == 7

    def test_load_sales_teams_returns_at_least_30_agents(self, data):
        """sales_teams DataFrame must have at least 30 records."""
        assert len(data["sales_teams"]) >= 30

    def test_load_pipeline_returns_at_least_8000_records(self, data):
        """pipeline DataFrame must have at least 8000 records."""
        assert len(data["pipeline"]) >= 8000


# ===================================================================
# 11.2 Normalization (3 tests)
# ===================================================================
class TestNormalization:
    """Verify that known data quality issues are corrected during load."""

    def test_product_gtxpro_normalized_to_gtx_pro(self, data):
        """In pipeline, raw 'GTXPro' entries must be normalized to 'GTX Pro'."""
        pipeline = data["pipeline"]
        assert "GTXPro" not in pipeline["product"].values, (
            "'GTXPro' should have been normalized to 'GTX Pro'"
        )

    def test_sector_technolgy_normalized_to_technology(self, data):
        """In accounts, the misspelling 'technolgy' must be corrected to 'technology'."""
        accounts = data["accounts"]
        assert "technolgy" not in accounts["sector"].values, (
            "'technolgy' should have been normalized to 'technology'"
        )

    def test_all_pipeline_products_exist_in_products_table(self, data):
        """After normalization, every product name in pipeline must exist in the products table."""
        pipeline_products = set(data["pipeline"]["product"].dropna().unique())
        products_table = set(data["products"]["product"].unique())
        missing = pipeline_products - products_table
        assert len(missing) == 0, f"Products in pipeline not found in products table: {missing}"


# ===================================================================
# 11.3 Type conversions (3 tests)
# ===================================================================
class TestTypeConversions:
    """Verify that date and numeric columns have the correct dtypes."""

    def test_engage_date_is_datetime_type(self, data):
        """engage_date column must be datetime64."""
        assert pd.api.types.is_datetime64_any_dtype(data["pipeline"]["engage_date"])

    def test_close_date_is_datetime_type(self, data):
        """close_date column must be datetime64."""
        assert pd.api.types.is_datetime64_any_dtype(data["pipeline"]["close_date"])

    def test_close_value_is_numeric_type(self, data):
        """close_value column must be a numeric type (int or float)."""
        assert pd.api.types.is_numeric_dtype(data["pipeline"]["close_value"])


# ===================================================================
# 11.4 Derived columns (4 tests)
# ===================================================================
class TestDerivedColumns:
    """Verify computed columns added during data loading."""

    def test_is_active_true_for_prospecting_and_engaging(self, data):
        """is_active must be True for Prospecting/Engaging and False for Won/Lost."""
        pipeline = data["pipeline"]
        active_stages = {"Prospecting", "Engaging"}
        closed_stages = {"Won", "Lost"}

        for stage in active_stages:
            subset = pipeline[pipeline["deal_stage"] == stage]
            if len(subset) > 0:
                assert subset["is_active"].all(), (
                    f"is_active should be True for all {stage} deals"
                )

        for stage in closed_stages:
            subset = pipeline[pipeline["deal_stage"] == stage]
            if len(subset) > 0:
                assert not subset["is_active"].any(), (
                    f"is_active should be False for all {stage} deals"
                )

    def test_days_in_stage_nan_for_prospecting(self, data):
        """days_in_stage must be NaN for all Prospecting deals (no engage_date)."""
        prospecting = data["pipeline"][data["pipeline"]["deal_stage"] == "Prospecting"]
        assert prospecting["days_in_stage"].isna().all(), (
            "days_in_stage should be NaN for all Prospecting deals"
        )

    def test_days_in_stage_positive_for_engaging(self, data):
        """days_in_stage must be positive (>0) for all Engaging deals."""
        engaging = data["pipeline"][data["pipeline"]["deal_stage"] == "Engaging"]
        valid = engaging["days_in_stage"].dropna()
        assert len(valid) > 0, "Expected at least some Engaging deals with days_in_stage"
        assert (valid > 0).all(), "days_in_stage should be positive for Engaging deals"

    def test_reference_date_is_2017_12_31(self, data):
        """get_reference_date() must return pd.Timestamp('2017-12-31')."""
        ref = get_reference_date()
        assert ref == pd.Timestamp("2017-12-31"), (
            f"Reference date should be 2017-12-31, got {ref}"
        )


# ===================================================================
# 11.5 Referential integrity (3 tests)
# ===================================================================
class TestReferentialIntegrity:
    """Verify foreign-key relationships between tables."""

    def test_all_pipeline_agents_exist_in_sales_teams(self, data):
        """Every sales_agent in pipeline must exist in sales_teams."""
        pipeline_agents = set(data["pipeline"]["sales_agent"].dropna().unique())
        team_agents = set(data["sales_teams"]["sales_agent"].unique())
        missing = pipeline_agents - team_agents
        assert len(missing) == 0, f"Agents in pipeline not in sales_teams: {missing}"

    def test_all_non_null_accounts_exist_in_accounts_table(self, data):
        """All non-null account values in pipeline must exist in accounts table."""
        pipeline_accounts = set(data["pipeline"]["account"].dropna().unique())
        accounts_table = set(data["accounts"]["account"].unique())
        missing = pipeline_accounts - accounts_table
        assert len(missing) == 0, f"Accounts in pipeline not in accounts table: {missing}"

    def test_opportunity_id_is_unique(self, data):
        """opportunity_id must be unique across the entire pipeline."""
        pipeline = data["pipeline"]
        assert pipeline["opportunity_id"].is_unique, (
            "opportunity_id contains duplicates"
        )


# ===================================================================
# 11.6 Nullability by stage (5 tests)
# ===================================================================
class TestNullabilityByStage:
    """Verify expected null/filled patterns per deal stage."""

    def test_prospecting_has_no_engage_date(self, data):
        """Prospecting deals must have 100% null engage_date."""
        prospecting = data["pipeline"][data["pipeline"]["deal_stage"] == "Prospecting"]
        assert prospecting["engage_date"].isna().all(), (
            "Prospecting deals should have no engage_date"
        )

    def test_prospecting_has_no_close_date(self, data):
        """Prospecting deals must have 100% null close_date."""
        prospecting = data["pipeline"][data["pipeline"]["deal_stage"] == "Prospecting"]
        assert prospecting["close_date"].isna().all(), (
            "Prospecting deals should have no close_date"
        )

    def test_engaging_has_engage_date(self, data):
        """Engaging deals must have 100% filled (non-null) engage_date."""
        engaging = data["pipeline"][data["pipeline"]["deal_stage"] == "Engaging"]
        assert engaging["engage_date"].notna().all(), (
            "Engaging deals should all have engage_date filled"
        )

    def test_won_has_positive_close_value(self, data):
        """Won deals must have close_value > 0."""
        won = data["pipeline"][data["pipeline"]["deal_stage"] == "Won"]
        assert (won["close_value"] > 0).all(), (
            "Won deals should all have close_value > 0"
        )

    def test_lost_has_zero_close_value(self, data):
        """Lost deals must have close_value == 0."""
        lost = data["pipeline"][data["pipeline"]["deal_stage"] == "Lost"]
        assert (lost["close_value"] == 0).all(), (
            "Lost deals should all have close_value == 0"
        )


# ===================================================================
# 11.7 Enrichment / JOINs (4 tests)
# ===================================================================
class TestEnrichmentJoins:
    """Verify that pipeline is enriched with columns from related tables."""

    def test_pipeline_has_sales_price_after_merge(self, data):
        """Pipeline must have a sales_price column from merge with products."""
        assert "sales_price" in data["pipeline"].columns, (
            "Pipeline should contain 'sales_price' after merge with products"
        )

    def test_pipeline_has_manager_after_merge(self, data):
        """Pipeline must have a manager column from merge with sales_teams."""
        assert "manager" in data["pipeline"].columns, (
            "Pipeline should contain 'manager' after merge with sales_teams"
        )

    def test_pipeline_has_sector_after_merge(self, data):
        """Pipeline must have a sector column from merge with accounts.
        Rows where account is null may have NaN sector — that is acceptable."""
        assert "sector" in data["pipeline"].columns, (
            "Pipeline should contain 'sector' after merge with accounts"
        )

    def test_get_active_deals_returns_only_active(self, data):
        """get_active_deals() must return only Prospecting and Engaging deals."""
        active = get_active_deals(data)
        stages_present = set(active["deal_stage"].unique())
        allowed = {"Prospecting", "Engaging"}
        assert stages_present.issubset(allowed), (
            f"get_active_deals should only contain Prospecting/Engaging, got {stages_present}"
        )
        assert len(active) > 0, "get_active_deals should return at least 1 deal"
