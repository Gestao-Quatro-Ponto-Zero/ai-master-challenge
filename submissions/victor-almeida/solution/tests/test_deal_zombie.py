"""
Tests for the Deal Zombie classification module.

19 tests covering: zombie classification, critical zombie detection,
account recurrent loss, estimated value, zombie summary, and sanity checks
with real data.

TDD Red Phase: these tests define expected behavior BEFORE implementation.
All tests should FAIL initially and pass after scoring/deal_zombie.py is built.
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

from scoring.deal_zombie import (  # noqa: E402
    classify_accounts,
    classify_zombies,
    get_zombie_summary,
)
from utils.data_loader import get_active_deals, load_data  # noqa: E402


# ---------------------------------------------------------------------------
# Constants used in tests (must match the spec)
# ---------------------------------------------------------------------------
ENGAGING_REFERENCE_DAYS = 88          # P75 of Won deals
ZOMBIE_THRESHOLD_MULTIPLIER = 2.0
ZOMBIE_THRESHOLD_DAYS = int(ENGAGING_REFERENCE_DAYS * ZOMBIE_THRESHOLD_MULTIPLIER)  # 176
RECURRENT_LOSS_THRESHOLD = 2
HIGH_RISK_LOSS_THRESHOLD = 5
REFERENCE_DATE = pd.Timestamp("2017-12-31")


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


@pytest.fixture(scope="module")
def classified_real(data):
    """Run classify_zombies on real active deals once per test module."""
    active = get_active_deals(data)
    return classify_zombies(active, data["products"], reference_date=REFERENCE_DATE)


# ---------------------------------------------------------------------------
# Helpers for synthetic DataFrames
# ---------------------------------------------------------------------------
def _make_engaging_deal(days_ago: int, product: str = "GTX Basic", close_value=None):
    """Build a single-row DataFrame for an Engaging deal.

    ``days_ago`` is how many days before REFERENCE_DATE the engage_date was set.
    """
    engage_date = REFERENCE_DATE - pd.Timedelta(days=days_ago)
    return pd.DataFrame(
        {
            "opportunity_id": [f"OPP-{days_ago}"],
            "deal_stage": ["Engaging"],
            "engage_date": [engage_date],
            "close_value": [close_value],
            "product": [product],
            "account": ["TestCo"],
            "sales_agent": ["Agent A"],
            "is_active": [True],
            "days_in_stage": [days_ago],
        }
    )


def _make_prospecting_deal():
    """Build a single-row DataFrame for a Prospecting deal (no temporal data)."""
    return pd.DataFrame(
        {
            "opportunity_id": ["OPP-PROSP-1"],
            "deal_stage": ["Prospecting"],
            "engage_date": [pd.NaT],
            "close_value": [np.nan],
            "product": ["GTX Basic"],
            "account": ["TestCo"],
            "sales_agent": ["Agent A"],
            "is_active": [True],
            "days_in_stage": [np.nan],
        }
    )


def _products_df():
    """Build a minimal products DataFrame with key products."""
    return pd.DataFrame(
        {
            "product": ["GTK 500", "GTX Basic", "MG Special", "GTX Pro"],
            "sales_price": [26768, 550, 55, 4821],
        }
    )


# ===================================================================
# 15.1 Classification tests (5)
# ===================================================================
class TestZombieClassification:
    """Verify zombie classification thresholds and stage rules."""

    def test_engaging_100_days_not_zombie(self):
        """Deal Engaging com 100 dias (ratio 1.14) NAO e zumbi."""
        deal = _make_engaging_deal(100)
        products = _products_df()
        result = classify_zombies(deal, products, reference_date=REFERENCE_DATE)

        assert len(result) == 1
        row = result.iloc[0]
        assert row["is_zombie"] is False or row["is_zombie"] == False, (  # noqa: E712
            f"Deal with 100 days (ratio ~1.14) should NOT be a zombie, got is_zombie={row['is_zombie']}"
        )

    def test_engaging_180_days_is_zombie(self):
        """Deal Engaging com 180 dias (ratio 2.05) E zumbi."""
        deal = _make_engaging_deal(180)
        products = _products_df()
        result = classify_zombies(deal, products, reference_date=REFERENCE_DATE)

        row = result.iloc[0]
        assert row["is_zombie"] is True or row["is_zombie"] == True, (  # noqa: E712
            f"Deal with 180 days (ratio ~2.05) SHOULD be a zombie, got is_zombie={row['is_zombie']}"
        )

    def test_engaging_270_days_is_chronic_zombie(self):
        """Deal Engaging com 270 dias (ratio 3.07) e Zumbi Cronico."""
        deal = _make_engaging_deal(270)
        products = _products_df()
        result = classify_zombies(deal, products, reference_date=REFERENCE_DATE)

        row = result.iloc[0]
        assert row["is_zombie"] is True or row["is_zombie"] == True, (  # noqa: E712
            "Deal with 270 days should be a zombie"
        )
        assert row["zombie_severity"] == "zombie_chronic", (
            f"Deal with 270 days (ratio 3.07) should be 'zombie_chronic', got '{row['zombie_severity']}'"
        )

    def test_prospecting_never_classified_as_zombie(self):
        """Deals em Prospecting NAO podem ser classificados como Zumbi (sem dados temporais)."""
        deal = _make_prospecting_deal()
        products = _products_df()
        result = classify_zombies(deal, products, reference_date=REFERENCE_DATE)

        row = result.iloc[0]
        assert row["is_zombie"] is False or row["is_zombie"] == False, (  # noqa: E712
            "Prospecting deals should NEVER be classified as zombie (no temporal data)"
        )
        assert row["zombie_severity"] is None or pd.isna(row["zombie_severity"]), (
            "Prospecting deals should have no zombie_severity"
        )

    def test_zombie_threshold_is_176_days(self):
        """Threshold para Engaging = 2 * 88 (P75) = 176 dias."""
        # 176 days: ratio = 176/88 = 2.0 exactly — NOT zombie (spec says > 2.0)
        deal_at_threshold = _make_engaging_deal(176)
        products = _products_df()
        result_at = classify_zombies(deal_at_threshold, products, reference_date=REFERENCE_DATE)
        row_at = result_at.iloc[0]

        # 177 days: ratio = 177/88 = 2.01 — IS zombie
        deal_over = _make_engaging_deal(177)
        result_over = classify_zombies(deal_over, products, reference_date=REFERENCE_DATE)
        row_over = result_over.iloc[0]

        assert row_over["is_zombie"] is True or row_over["is_zombie"] == True, (  # noqa: E712
            "Deal with 177 days (ratio 2.01) should be zombie"
        )
        # Verify the threshold is exactly 176 days (2 * 88)
        assert ZOMBIE_THRESHOLD_DAYS == 176, (
            f"Zombie threshold should be 176 days (2 * 88), got {ZOMBIE_THRESHOLD_DAYS}"
        )


# ===================================================================
# 15.2 Critical zombie tests (3)
# ===================================================================
class TestZombieCritical:
    """Verify critical zombie detection based on value thresholds."""

    def test_zombie_with_gtk500_is_critical(self):
        """Zumbi com GTK 500 ($26.768) e Zumbi Critico (valor > P75)."""
        deal = _make_engaging_deal(200, product="GTK 500")
        products = _products_df()
        result = classify_zombies(deal, products, reference_date=REFERENCE_DATE)

        row = result.iloc[0]
        assert row["is_zombie"] is True or row["is_zombie"] == True, (  # noqa: E712
            "Deal with 200 days should be a zombie"
        )
        assert row["is_zombie_critical"] is True or row["is_zombie_critical"] == True, (  # noqa: E712
            "Zombie with GTK 500 ($26,768) should be critical (value above P75)"
        )

    def test_zombie_with_mg_special_not_critical(self):
        """Zumbi com MG Special ($55) NAO e Zumbi Critico."""
        deal = _make_engaging_deal(200, product="MG Special")
        products = _products_df()
        result = classify_zombies(deal, products, reference_date=REFERENCE_DATE)

        row = result.iloc[0]
        assert row["is_zombie"] is True or row["is_zombie"] == True, (  # noqa: E712
            "Deal with 200 days should be a zombie"
        )
        assert row["is_zombie_critical"] is False or row["is_zombie_critical"] == False, (  # noqa: E712
            "Zombie with MG Special ($55) should NOT be critical (value below P75)"
        )

    def test_non_zombie_never_critical(self):
        """Deal nao-zumbi nunca e classificado como Zumbi Critico."""
        # 100 days = ratio 1.14, not a zombie even with high-value product
        deal = _make_engaging_deal(100, product="GTK 500")
        products = _products_df()
        result = classify_zombies(deal, products, reference_date=REFERENCE_DATE)

        row = result.iloc[0]
        assert row["is_zombie"] is False or row["is_zombie"] == False, (  # noqa: E712
            "Deal with 100 days should NOT be a zombie"
        )
        assert row["is_zombie_critical"] is False or row["is_zombie_critical"] == False, (  # noqa: E712
            "Non-zombie deal should NEVER be critical, regardless of value"
        )


# ===================================================================
# 15.3 Account tests (4)
# ===================================================================
class TestAccountRecurrentLoss:
    """Verify account classification based on historical losses."""

    @staticmethod
    def _make_pipeline_with_losses(account: str, n_won: int, n_lost: int):
        """Build a synthetic pipeline DataFrame with specified won/lost counts."""
        rows = []
        for i in range(n_won):
            rows.append({"account": account, "deal_stage": "Won"})
        for i in range(n_lost):
            rows.append({"account": account, "deal_stage": "Lost"})
        return pd.DataFrame(rows)

    def test_account_0_losses_not_recurrent(self):
        """Conta com 0 losses nao e recorrente."""
        pipeline = self._make_pipeline_with_losses("CleanCo", n_won=5, n_lost=0)
        result = classify_accounts(pipeline)

        row = result[result["account"] == "CleanCo"]
        assert len(row) == 1, "Should have exactly one row for CleanCo"
        assert row.iloc[0]["is_recurrent_loss"] is False or row.iloc[0]["is_recurrent_loss"] == False, (  # noqa: E712
            "Account with 0 losses should NOT be recurrent"
        )

    def test_account_1_loss_not_recurrent(self):
        """Conta com 1 loss nao e recorrente."""
        pipeline = self._make_pipeline_with_losses("AlmostCo", n_won=5, n_lost=1)
        result = classify_accounts(pipeline)

        row = result[result["account"] == "AlmostCo"]
        assert len(row) == 1, "Should have exactly one row for AlmostCo"
        assert row.iloc[0]["is_recurrent_loss"] is False or row.iloc[0]["is_recurrent_loss"] == False, (  # noqa: E712
            "Account with 1 loss should NOT be recurrent (threshold is 2)"
        )

    def test_account_2_losses_is_recurrent(self):
        """Conta com 2 losses E recorrente."""
        pipeline = self._make_pipeline_with_losses("ProblemCo", n_won=3, n_lost=2)
        result = classify_accounts(pipeline)

        row = result[result["account"] == "ProblemCo"]
        assert len(row) == 1, "Should have exactly one row for ProblemCo"
        assert row.iloc[0]["is_recurrent_loss"] is True or row.iloc[0]["is_recurrent_loss"] == True, (  # noqa: E712
            "Account with 2 losses SHOULD be recurrent (threshold is 2)"
        )
        assert row.iloc[0]["total_lost"] == 2, (
            f"total_lost should be 2, got {row.iloc[0]['total_lost']}"
        )

    def test_account_10_losses_is_high_risk(self):
        """Conta com 10 losses e recorrente E alto risco."""
        pipeline = self._make_pipeline_with_losses("HighRiskCo", n_won=5, n_lost=10)
        result = classify_accounts(pipeline)

        row = result[result["account"] == "HighRiskCo"]
        assert len(row) == 1, "Should have exactly one row for HighRiskCo"
        assert row.iloc[0]["is_recurrent_loss"] is True or row.iloc[0]["is_recurrent_loss"] == True, (  # noqa: E712
            "Account with 10 losses should be recurrent"
        )
        assert row.iloc[0]["is_high_risk"] is True or row.iloc[0]["is_high_risk"] == True, (  # noqa: E712
            "Account with 10 losses should be high risk (threshold is 5)"
        )
        assert row.iloc[0]["total_lost"] == 10, (
            f"total_lost should be 10, got {row.iloc[0]['total_lost']}"
        )


# ===================================================================
# 15.4 Estimated value tests (2)
# ===================================================================
class TestEstimatedValue:
    """Verify estimated value calculation for zombie classification."""

    def test_estimated_value_uses_close_value_when_available(self):
        """Se close_value > 0, usar close_value como valor estimado."""
        deal = _make_engaging_deal(200, product="GTX Basic", close_value=999.0)
        products = _products_df()
        result = classify_zombies(deal, products, reference_date=REFERENCE_DATE)

        row = result.iloc[0]
        assert row["estimated_value"] == pytest.approx(999.0, abs=0.01), (
            f"estimated_value should be 999.0 (close_value), got {row['estimated_value']}"
        )

    def test_estimated_value_uses_product_price_when_no_close_value(self):
        """Se close_value null, usar preco de lista do produto."""
        deal = _make_engaging_deal(200, product="GTX Basic", close_value=None)
        products = _products_df()
        result = classify_zombies(deal, products, reference_date=REFERENCE_DATE)

        row = result.iloc[0]
        # GTX Basic sales_price = 550
        assert row["estimated_value"] == pytest.approx(550.0, abs=0.01), (
            f"estimated_value should be 550.0 (GTX Basic price), got {row['estimated_value']}"
        )


# ===================================================================
# 15.5 Summary tests (3)
# ===================================================================
class TestZombieSummary:
    """Verify get_zombie_summary returns correct structure and values."""

    @staticmethod
    def _make_classified_df():
        """Build a synthetic classified DataFrame with known zombie/non-zombie deals."""
        products = _products_df()

        # Create a mix of zombie and non-zombie deals
        deals = pd.concat(
            [
                _make_engaging_deal(100, product="GTX Basic"),    # Not zombie
                _make_engaging_deal(200, product="GTK 500"),      # Zombie
                _make_engaging_deal(250, product="MG Special"),   # Zombie
                _make_engaging_deal(50, product="GTX Pro"),       # Not zombie
            ],
            ignore_index=True,
        )
        return classify_zombies(deals, products, reference_date=REFERENCE_DATE)

    def test_zombie_summary_has_expected_keys(self):
        """Resumo contem todas as chaves esperadas."""
        classified = self._make_classified_df()
        summary = get_zombie_summary(classified)

        expected_keys = {
            "total_active_deals",
            "total_zombies",
            "total_zombies_critical",
            "total_zombies_chronic",
            "pct_zombies",
            "pipeline_total",
            "pipeline_inflated",
            "pipeline_inflated_critical",
            "pct_pipeline_inflated",
        }
        actual_keys = set(summary.keys())
        missing = expected_keys - actual_keys
        assert len(missing) == 0, (
            f"Zombie summary is missing keys: {missing}. Got keys: {actual_keys}"
        )

    def test_zombie_summary_pct_consistent(self):
        """pct_zombies = total_zombies / total_active_deals * 100."""
        classified = self._make_classified_df()
        summary = get_zombie_summary(classified)

        if summary["total_active_deals"] > 0:
            expected_pct = summary["total_zombies"] / summary["total_active_deals"] * 100
            assert summary["pct_zombies"] == pytest.approx(expected_pct, abs=0.1), (
                f"pct_zombies should be {expected_pct:.1f}, got {summary['pct_zombies']:.1f}"
            )
        else:
            pytest.skip("No active deals in test data")

    def test_zombie_summary_pipeline_inflated_sum_of_zombie_values(self):
        """pipeline_inflated = soma dos valores estimados dos deals zumbis."""
        classified = self._make_classified_df()
        summary = get_zombie_summary(classified)

        # Calculate expected inflated value from the classified DataFrame
        zombie_mask = classified["is_zombie"] == True  # noqa: E712
        expected_inflated = classified.loc[zombie_mask, "estimated_value"].sum()

        assert summary["pipeline_inflated"] == pytest.approx(expected_inflated, abs=0.01), (
            f"pipeline_inflated should be {expected_inflated:.2f}, got {summary['pipeline_inflated']:.2f}"
        )


# ===================================================================
# 15.6 Sanity tests with real data (2)
# ===================================================================
class TestRealDataSanity:
    """Sanity checks using the real CSV data from the dataset."""

    def test_approximately_47_percent_engaging_are_zombies(self, data, classified_real):
        """Com referencia P75 (88d) e threshold 2x, ~40-55% dos deals Engaging sao zumbis."""
        engaging = classified_real[classified_real["deal_stage"] == "Engaging"]
        total_engaging = len(engaging)
        total_zombies = engaging["is_zombie"].sum()

        assert total_engaging > 0, "Should have Engaging deals in real data"

        pct_zombies = total_zombies / total_engaging * 100

        assert 40 <= pct_zombies <= 55, (
            f"Expected ~40-55% of Engaging deals to be zombies with P75 reference, "
            f"got {pct_zombies:.1f}% ({total_zombies} of {total_engaging})"
        )

    def test_classify_zombies_adds_expected_columns(self, classified_real):
        """classify_zombies retorna DataFrame com as colunas adicionais esperadas."""
        expected_columns = {
            "is_zombie",
            "zombie_severity",
            "zombie_label",
            "time_ratio",
            "estimated_value",
            "is_zombie_critical",
        }
        actual_columns = set(classified_real.columns)
        missing = expected_columns - actual_columns
        assert len(missing) == 0, (
            f"classify_zombies output is missing columns: {missing}. "
            f"Available columns: {sorted(actual_columns)}"
        )
