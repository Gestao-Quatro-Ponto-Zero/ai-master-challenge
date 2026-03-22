"""
Testes TDD para components/metrics.py — camada de calculo pura.

Testa apenas funcoes puras (sem Streamlit):
- count_active_deals: contagem de deals ativos (Prospecting + Engaging)
- calculate_pipeline_total: soma de estimated_value dos deals ativos
- count_zombies: contagem de deals zumbi
- calculate_win_rate: taxa de conversao Won/(Won+Lost)
- calculate_score_distribution: distribuicao por faixa de score
- calculate_pipeline_health: saude do pipeline (saudaveis vs zumbis)
"""

import numpy as np
import pandas as pd
import pytest

from components.metrics import (
    calculate_pipeline_health,
    calculate_pipeline_total,
    calculate_score_distribution,
    calculate_win_rate,
    count_active_deals,
    count_zombies,
)
from utils.formatters import format_currency


# ---------------------------------------------------------------------------
# Fixtures — DataFrames sinteticos que replicam a estrutura real
# ---------------------------------------------------------------------------


def _make_deal(
    deal_stage: str,
    score: float = 50.0,
    is_zombie: bool = False,
    sales_price: float = 1000.0,
    close_value: float = np.nan,
    estimated_value: float | None = None,
    opportunity_id: str = "OPP-001",
    sales_agent: str = "Agent A",
    manager: str = "Manager X",
    regional_office: str = "Central",
    product: str = "GTX Basic",
) -> dict:
    """Helper para criar um deal como dict (vira row do DataFrame)."""
    if estimated_value is None:
        estimated_value = close_value if not np.isnan(close_value) else sales_price
    return {
        "opportunity_id": opportunity_id,
        "deal_stage": deal_stage,
        "score": score,
        "is_zombie": is_zombie,
        "sales_price": sales_price,
        "close_value": close_value,
        "estimated_value": estimated_value,
        "sales_agent": sales_agent,
        "manager": manager,
        "regional_office": regional_office,
        "product": product,
    }


@pytest.fixture
def df_mixed() -> pd.DataFrame:
    """DataFrame com mix de stages: 3 Engaging, 2 Prospecting, 5 Won, 3 Lost."""
    deals = [
        # Active — Engaging (3)
        _make_deal("Engaging", score=85, sales_price=5000, close_value=np.nan,
                    estimated_value=5000, opportunity_id="E1"),
        _make_deal("Engaging", score=42, sales_price=3000, close_value=np.nan,
                    estimated_value=3000, opportunity_id="E2", is_zombie=True),
        _make_deal("Engaging", score=70, sales_price=2000, close_value=np.nan,
                    estimated_value=2000, opportunity_id="E3"),
        # Active — Prospecting (2)
        _make_deal("Prospecting", score=30, sales_price=1500,
                    estimated_value=1500, opportunity_id="P1"),
        _make_deal("Prospecting", score=25, sales_price=2500,
                    estimated_value=2500, opportunity_id="P2"),
        # Won (5)
        _make_deal("Won", close_value=10000, estimated_value=10000,
                    opportunity_id="W1"),
        _make_deal("Won", close_value=8000, estimated_value=8000,
                    opportunity_id="W2"),
        _make_deal("Won", close_value=5000, estimated_value=5000,
                    opportunity_id="W3"),
        _make_deal("Won", close_value=12000, estimated_value=12000,
                    opportunity_id="W4"),
        _make_deal("Won", close_value=7000, estimated_value=7000,
                    opportunity_id="W5"),
        # Lost (3)
        _make_deal("Lost", close_value=0, estimated_value=0,
                    opportunity_id="L1"),
        _make_deal("Lost", close_value=0, estimated_value=0,
                    opportunity_id="L2"),
        _make_deal("Lost", close_value=0, estimated_value=0,
                    opportunity_id="L3"),
    ]
    return pd.DataFrame(deals)


@pytest.fixture
def df_empty() -> pd.DataFrame:
    """DataFrame vazio com colunas corretas."""
    return pd.DataFrame(columns=[
        "opportunity_id", "deal_stage", "score", "is_zombie",
        "sales_price", "close_value", "estimated_value",
        "sales_agent", "manager", "regional_office", "product",
    ])


@pytest.fixture
def df_single() -> pd.DataFrame:
    """DataFrame com apenas 1 deal ativo."""
    return pd.DataFrame([
        _make_deal("Engaging", score=72, sales_price=4000,
                    estimated_value=4000, is_zombie=False,
                    opportunity_id="SOLO-1"),
    ])


# ===========================================================================
# KPI Calculation Tests
# ===========================================================================


class TestCountActiveDeals:
    def test_count_active_deals_only_prospecting_and_engaging(self, df_mixed):
        """count_active_deals returns count of only Prospecting + Engaging deals."""
        # 3 Engaging + 2 Prospecting = 5
        assert count_active_deals(df_mixed) == 5

    def test_count_active_deals_ignores_won_and_lost(self, df_mixed):
        """Won and Lost deals are not counted as active."""
        total_rows = len(df_mixed)
        active = count_active_deals(df_mixed)
        # 5 Won + 3 Lost = 8 excluded
        assert active == total_rows - 8


class TestCalculatePipelineTotal:
    def test_pipeline_total_uses_estimated_value(self, df_mixed):
        """calculate_pipeline_total sums estimated_value for active deals."""
        # Active deals estimated_value: 5000 + 3000 + 2000 + 1500 + 2500 = 14000
        assert calculate_pipeline_total(df_mixed) == 14000.0


class TestCountZombies:
    def test_zombie_count_matches_is_zombie_flag(self, df_mixed):
        """count_zombies returns len(df[df['is_zombie'] == True])."""
        # Only E2 is zombie
        assert count_zombies(df_mixed) == 1


class TestCalculateWinRate:
    def test_win_rate_calculated_from_won_and_lost(self, df_mixed):
        """calculate_win_rate = Won / (Won + Lost). 5 Won + 3 Lost -> 0.625"""
        result = calculate_win_rate(df_mixed)
        assert result == pytest.approx(5 / 8)  # 0.625

    def test_win_rate_returns_none_when_no_closed_deals(self):
        """calculate_win_rate returns None when no Won/Lost deals."""
        df_only_active = pd.DataFrame([
            _make_deal("Prospecting", opportunity_id="P1"),
            _make_deal("Engaging", opportunity_id="E1"),
        ])
        assert calculate_win_rate(df_only_active) is None


# ===========================================================================
# Currency Format Tests (import from utils.formatters)
# ===========================================================================


class TestFormatCurrencyIntegration:
    def test_format_currency_millions(self):
        """1_200_000 -> '$1.2M'"""
        assert format_currency(1_200_000) == "$1.2M"

    def test_format_currency_thousands(self):
        """45_000 -> '$45K'"""
        assert format_currency(45_000) == "$45K"

    def test_format_currency_small(self):
        """55 -> '$55'"""
        assert format_currency(55) == "$55"


# ===========================================================================
# Score Distribution Tests
# ===========================================================================


class TestScoreDistribution:
    def test_score_distribution_has_4_faixas(self, df_mixed):
        """calculate_score_distribution returns exactly 4 bands."""
        dist = calculate_score_distribution(df_mixed)
        assert len(dist) == 4

    def test_score_distribution_counts_sum_to_total(self, df_mixed):
        """Sum of all band counts equals total active deals."""
        dist = calculate_score_distribution(df_mixed)
        total = sum(band["count"] for band in dist)
        active = count_active_deals(df_mixed)
        assert total == active

    def test_score_80_falls_in_alta_prioridade(self):
        """A deal with score 80 is counted in 'Alta (80-100)' band."""
        df = pd.DataFrame([
            _make_deal("Engaging", score=80, opportunity_id="HIGH-1"),
        ])
        dist = calculate_score_distribution(df)
        alta = next(b for b in dist if "Alta" in b["name"])
        assert alta["count"] == 1

    def test_score_39_falls_in_critico(self):
        """A deal with score 39 is counted in 'Critico (0-39)' band."""
        df = pd.DataFrame([
            _make_deal("Prospecting", score=39, opportunity_id="CRIT-1"),
        ])
        dist = calculate_score_distribution(df)
        critico = next(b for b in dist if "Critico" in b["name"])
        assert critico["count"] == 1

    def test_float_scores_at_boundaries_are_not_lost(self):
        """Scores like 39.7, 59.3, 79.5 must fall into a band (no gaps)."""
        df = pd.DataFrame([
            _make_deal("Engaging", score=39.7, opportunity_id="B1"),
            _make_deal("Engaging", score=59.3, opportunity_id="B2"),
            _make_deal("Engaging", score=79.5, opportunity_id="B3"),
        ])
        dist = calculate_score_distribution(df)
        total = sum(b["count"] for b in dist)
        assert total == 3, f"Expected 3 deals distributed, got {total}"


# ===========================================================================
# Pipeline Health Tests
# ===========================================================================


class TestPipelineHealth:
    def test_pipeline_health_sums_to_total_deals(self, df_mixed):
        """healthy + zombies = total active deals."""
        health = calculate_pipeline_health(df_mixed)
        assert health["healthy"] + health["zombies"] == health["total"]

    def test_pipeline_health_zero_zombies(self):
        """When no zombies, healthy count = total count."""
        df = pd.DataFrame([
            _make_deal("Engaging", is_zombie=False, opportunity_id="H1"),
            _make_deal("Prospecting", is_zombie=False, opportunity_id="H2"),
        ])
        health = calculate_pipeline_health(df)
        assert health["zombies"] == 0
        assert health["healthy"] == health["total"]
        assert health["total"] == 2


# ===========================================================================
# Edge Case Tests
# ===========================================================================


class TestEdgeCases:
    def test_metrics_handle_empty_dataframe(self, df_empty):
        """Empty DataFrame returns zeros for all metrics, no errors."""
        assert count_active_deals(df_empty) == 0
        assert calculate_pipeline_total(df_empty) == 0.0
        assert count_zombies(df_empty) == 0
        assert calculate_win_rate(df_empty) is None

        dist = calculate_score_distribution(df_empty)
        assert len(dist) == 4
        assert all(b["count"] == 0 for b in dist)

        health = calculate_pipeline_health(df_empty)
        assert health == {"healthy": 0, "zombies": 0, "total": 0}

    def test_metrics_handle_single_deal(self, df_single):
        """Single-deal DataFrame computes all metrics correctly."""
        assert count_active_deals(df_single) == 1
        assert calculate_pipeline_total(df_single) == 4000.0
        assert count_zombies(df_single) == 0
        assert calculate_win_rate(df_single) is None

        dist = calculate_score_distribution(df_single)
        total = sum(b["count"] for b in dist)
        assert total == 1

        health = calculate_pipeline_health(df_single)
        assert health == {"healthy": 1, "zombies": 0, "total": 1}
