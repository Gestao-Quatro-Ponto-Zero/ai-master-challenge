"""
Tests for the Scoring Engine.

38 tests covering: stage score, value score, velocity score, seller fit,
account health, and engine integration with real data.

TDD Red Phase: these tests define expected behavior BEFORE implementation.
All tests should FAIL initially and pass after the scoring engine is built.
"""

import math
import os
import sys

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Path setup — allow imports from the solution root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoring.constants import (
    DECAY_TABLE,
    FIT_MULTIPLIER_MAX,
    FIT_MULTIPLIER_MIN,
    STAGE_SCORES,
    VALUE_MAX_REFERENCE,
    WEIGHTS,
)
from scoring.velocity import calculate_days_in_stage, calculate_velocity_score
from scoring.seller_fit import build_seller_fit_stats, calculate_seller_fit_score
from scoring.account_health import (
    build_account_health_stats,
    calculate_account_health_score,
)
from scoring.engine import ScoringEngine
from utils.data_loader import get_active_deals, load_data


# ===================================================================
# 15.1 Stage Score (4 tests)
# ===================================================================
class TestStageScore:
    """Verify STAGE_SCORES lookup returns correct values for each stage."""

    def test_stage_score_prospecting_returns_15(self):
        """Prospecting deve retornar score 15."""
        assert STAGE_SCORES.get("Prospecting", 0) == 15

    def test_stage_score_engaging_returns_90(self):
        """Engaging deve retornar score 90."""
        assert STAGE_SCORES.get("Engaging", 0) == 90

    def test_stage_score_won_returns_0(self):
        """Won nao e deal ativo, retorna 0."""
        assert STAGE_SCORES.get("Won", 0) == 0

    def test_stage_score_unknown_returns_0(self):
        """Stage desconhecido retorna 0."""
        assert STAGE_SCORES.get("XyzUnknown", 0) == 0


# ===================================================================
# 15.2 Value Score (6 tests)
# ===================================================================
class TestValueScore:
    """Verify log-scaled value score calculation.

    Formula: score = log(1 + effective_value) / log(1 + max_value) * 100
    max_value = VALUE_MAX_REFERENCE (26768, GTK 500)
    """

    @staticmethod
    def _expected_value_score(effective_value: float, max_value: float) -> float:
        """Compute the expected value score using the spec formula."""
        if max_value <= 0:
            return 0.0
        return min(math.log(1 + effective_value) / math.log(1 + max_value) * 100, 100.0)

    def test_value_score_gtk500_near_100(self, scoring_engine, scored_pipeline):
        """GTK 500 ($26768) deve ter value_score proximo de 100."""
        gtk500_deals = scored_pipeline[scored_pipeline["product"] == "GTK 500"]
        if len(gtk500_deals) > 0:
            score = gtk500_deals.iloc[0]["score_value"]
            expected = self._expected_value_score(26768, VALUE_MAX_REFERENCE)
            assert score == pytest.approx(expected, abs=2), (
                f"GTK 500 value score should be ~{expected}, got {score}"
            )

    def test_value_score_mg_special_around_39(self, scoring_engine, scored_pipeline):
        """MG Special ($55) deve ter value_score em torno de 39.5."""
        mg_deals = scored_pipeline[scored_pipeline["product"] == "MG Special"]
        if len(mg_deals) > 0:
            score = mg_deals.iloc[0]["score_value"]
            expected = self._expected_value_score(55, VALUE_MAX_REFERENCE)
            assert score == pytest.approx(expected, abs=3), (
                f"MG Special value score should be ~{expected}, got {score}"
            )

    def test_value_score_uses_product_price_when_close_value_null(
        self, scoring_engine, scored_pipeline
    ):
        """Quando close_value e null (deals ativos), usa sales_price do produto."""
        # All active deals have null close_value, so score_value should use product price
        prospecting = scored_pipeline[scored_pipeline["deal_stage"] == "Prospecting"]
        if len(prospecting) > 0:
            row = prospecting.iloc[0]
            # score_value should be > 0 (product_price used as proxy)
            assert row["score_value"] > 0, (
                "Value score should be > 0 when close_value is null (using product price)"
            )

    def test_value_score_zero_when_max_value_zero(self, scoring_engine):
        """Se max_value = 0, retorna 0 (sem divisao por zero)."""
        result = self._expected_value_score(1000, 0)
        assert result == 0.0, (
            "Value score should be 0 when max_value is 0"
        )

    def test_value_score_always_between_0_and_100(self, scored_pipeline):
        """value_score deve estar sempre entre 0 e 100."""
        assert (scored_pipeline["score_value"] >= 0).all(), (
            "All value scores should be >= 0"
        )
        assert (scored_pipeline["score_value"] <= 100).all(), (
            "All value scores should be <= 100"
        )

    def test_value_score_gtx_basic_around_62(self, scoring_engine, scored_pipeline):
        """GTX Basic ($550) deve ter value_score em torno de 61.9."""
        gtx_deals = scored_pipeline[scored_pipeline["product"] == "GTX Basic"]
        if len(gtx_deals) > 0:
            score = gtx_deals.iloc[0]["score_value"]
            expected = self._expected_value_score(550, VALUE_MAX_REFERENCE)
            assert score == pytest.approx(expected, abs=3), (
                f"GTX Basic value score should be ~{expected}, got {score}"
            )


# ===================================================================
# 15.3 Velocity Score (7 tests)
# ===================================================================
class TestVelocityScore:
    """Verify velocity decay calculations for different time-in-stage scenarios."""

    def test_velocity_score_healthy_deal(self):
        """Deal com 44 dias em Engaging (ratio 0.5) -> score=100, label='saudavel'."""
        score, label, meta = calculate_velocity_score("Engaging", 44)
        assert score == 100.0, f"Expected score 100 for 44 days Engaging, got {score}"
        assert label == "saudavel", f"Expected label 'saudavel', got '{label}'"

    def test_velocity_score_at_reference(self):
        """Deal com 88 dias em Engaging (ratio 1.0) -> score=100, label='saudavel'."""
        score, label, meta = calculate_velocity_score("Engaging", 88)
        assert score == 100.0, f"Expected score 100 at reference (88 days), got {score}"
        assert label == "saudavel", f"Expected label 'saudavel', got '{label}'"

    def test_velocity_score_attention(self):
        """Deal com 95 dias (ratio ~1.08) -> score=80, label='atencao'."""
        score, label, meta = calculate_velocity_score("Engaging", 95)
        assert score == pytest.approx(80.0, abs=1), (
            f"Expected score ~80 for 95 days Engaging, got {score}"
        )
        assert label == "atencao", f"Expected label 'atencao', got '{label}'"

    def test_velocity_score_alert(self):
        """Deal com 150 dias (ratio ~1.70) -> score=55, label='alerta'."""
        score, label, meta = calculate_velocity_score("Engaging", 150)
        assert score == pytest.approx(55.0, abs=1), (
            f"Expected score ~55 for 150 days Engaging, got {score}"
        )
        assert label == "alerta", f"Expected label 'alerta', got '{label}'"

    def test_velocity_score_zombie(self):
        """Deal com 300 dias (ratio ~3.41) -> score=10, label='quase_morto'."""
        score, label, meta = calculate_velocity_score("Engaging", 300)
        assert score == pytest.approx(10.0, abs=1), (
            f"Expected score ~10 for 300 days Engaging, got {score}"
        )
        assert label == "quase_morto", f"Expected label 'quase_morto', got '{label}'"

    def test_velocity_score_prospecting_returns_neutral(self):
        """Deal em Prospecting (sem engage_date) retorna score neutro (50)."""
        score, label, meta = calculate_velocity_score("Prospecting", None)
        assert score == 50.0, (
            f"Expected neutral score 50 for Prospecting, got {score}"
        )

    def test_velocity_decay_is_monotonically_decreasing(self):
        """Score de velocidade deve diminuir conforme ratio aumenta."""
        score_44, _, _ = calculate_velocity_score("Engaging", 44)
        score_95, _, _ = calculate_velocity_score("Engaging", 95)
        score_120, _, _ = calculate_velocity_score("Engaging", 120)
        score_200, _, _ = calculate_velocity_score("Engaging", 200)

        assert score_44 >= score_95, (
            f"Score at 44d ({score_44}) should be >= score at 95d ({score_95})"
        )
        assert score_95 >= score_120, (
            f"Score at 95d ({score_95}) should be >= score at 120d ({score_120})"
        )
        assert score_120 >= score_200, (
            f"Score at 120d ({score_120}) should be >= score at 200d ({score_200})"
        )


# ===================================================================
# 15.4 Seller Fit (7 tests)
# ===================================================================
class TestSellerFit:
    """Verify seller-deal fit score using synthetic and real data."""

    @staticmethod
    def _make_fit_stats(
        seller_agent: str,
        sector: str,
        seller_wins: int,
        seller_total: int,
        team_wins: int,
        team_total: int,
    ) -> dict:
        """Build a minimal fit_stats dict for unit tests."""
        seller_sector = pd.DataFrame(
            {
                "sales_agent": [seller_agent],
                "sector": [sector],
                "wins": [seller_wins],
                "total": [seller_total],
                "winrate": [seller_wins / seller_total if seller_total > 0 else 0.0],
            }
        )
        team_sector = pd.DataFrame(
            {
                "sector": [sector],
                "wins": [team_wins],
                "total": [team_total],
                "winrate": [team_wins / team_total if team_total > 0 else 0.0],
            }
        )
        return {"seller_sector": seller_sector, "team_sector": team_sector}

    def test_seller_fit_neutral_when_few_deals(self):
        """Vendedor com < 5 deals no setor retorna 50 (neutro)."""
        stats = self._make_fit_stats("Agent A", "tech", 2, 3, 60, 100)
        score, meta = calculate_seller_fit_score("Agent A", "tech", stats)
        assert score == 50.0, (
            f"Expected neutral score 50 for seller with 3 deals, got {score}"
        )

    def test_seller_fit_neutral_when_no_sector(self):
        """Deal sem setor (account_sector=None) retorna 50 (neutro)."""
        stats = self._make_fit_stats("Agent A", "tech", 5, 10, 60, 100)
        score, meta = calculate_seller_fit_score("Agent A", None, stats)
        assert score == 50.0, (
            f"Expected neutral score 50 for null sector, got {score}"
        )

    def test_seller_fit_high_when_above_team_average(self):
        """Vendedor com WR acima da media do time retorna score > 50."""
        # seller_wr = 8/10 = 0.8, team_wr = 60/100 = 0.6
        # multiplier = 0.8 / 0.6 = 1.333
        # clamped = 1.333 (in [0.3, 2.0])
        # score = (1.333 - 0.3) / (2.0 - 0.3) * 100 = 60.8
        stats = self._make_fit_stats("Agent A", "tech", 8, 10, 60, 100)
        score, meta = calculate_seller_fit_score("Agent A", "tech", stats)
        assert score > 50.0, (
            f"Expected score > 50 for seller above team avg, got {score}"
        )

    def test_seller_fit_low_when_below_team_average(self):
        """Vendedor com WR abaixo da media retorna score < 50."""
        # seller_wr = 3/10 = 0.3, team_wr = 60/100 = 0.6
        # multiplier = 0.3 / 0.6 = 0.5
        # clamped = 0.5 (in [0.3, 2.0])
        # score = (0.5 - 0.3) / (2.0 - 0.3) * 100 = 11.8
        stats = self._make_fit_stats("Agent A", "tech", 3, 10, 60, 100)
        score, meta = calculate_seller_fit_score("Agent A", "tech", stats)
        assert score < 50.0, (
            f"Expected score < 50 for seller below team avg, got {score}"
        )

    def test_seller_fit_clamped_at_100(self):
        """Multiplicador > 2.0 deve ser clamped, score maximo = 100."""
        # seller_wr = 9/10 = 0.9, team_wr = 30/100 = 0.3
        # multiplier = 0.9 / 0.3 = 3.0 -> clamped to 2.0
        # score = (2.0 - 0.3) / (2.0 - 0.3) * 100 = 100.0
        stats = self._make_fit_stats("Agent A", "tech", 9, 10, 30, 100)
        score, meta = calculate_seller_fit_score("Agent A", "tech", stats)
        assert score == pytest.approx(100.0, abs=0.1), (
            f"Expected clamped score 100 for multiplier > 2.0, got {score}"
        )

    def test_seller_fit_clamped_at_0(self):
        """Multiplicador < 0.3 deve ser clamped, score minimo = 0."""
        # seller_wr = 1/10 = 0.1, team_wr = 90/100 = 0.9
        # multiplier = 0.1 / 0.9 = 0.111 -> clamped to 0.3
        # score = (0.3 - 0.3) / (2.0 - 0.3) * 100 = 0.0
        stats = self._make_fit_stats("Agent A", "tech", 1, 10, 90, 100)
        score, meta = calculate_seller_fit_score("Agent A", "tech", stats)
        assert score == pytest.approx(0.0, abs=0.1), (
            f"Expected clamped score 0 for multiplier < 0.3, got {score}"
        )

    def test_build_seller_fit_stats_uses_only_closed_deals(self):
        """Stats devem ser calculadas apenas com deals Won e Lost."""
        pipeline_df = pd.DataFrame(
            {
                "deal_stage": ["Won", "Lost", "Prospecting", "Engaging", "Won"],
                "sales_agent": ["A", "A", "A", "A", "A"],
                "account": ["Co1", "Co1", "Co2", "Co2", "Co1"],
            }
        )
        accounts_df = pd.DataFrame(
            {
                "account": ["Co1", "Co2"],
                "sector": ["tech", "finance"],
            }
        )
        stats = build_seller_fit_stats(pipeline_df, accounts_df)
        seller_sector = stats["seller_sector"]

        # Only Won/Lost should be counted: 2 Won + 1 Lost in "tech" (Co1)
        tech_row = seller_sector[
            (seller_sector["sales_agent"] == "A")
            & (seller_sector["sector"] == "tech")
        ]
        assert len(tech_row) == 1, "Should have stats for agent A in tech"
        assert int(tech_row.iloc[0]["total"]) == 3, (
            "Total should be 3 (2 Won + 1 Lost for Co1/tech), "
            f"got {int(tech_row.iloc[0]['total'])}"
        )

        # Prospecting and Engaging deals for Co2/finance should NOT appear
        finance_row = seller_sector[
            (seller_sector["sales_agent"] == "A")
            & (seller_sector["sector"] == "finance")
        ]
        assert len(finance_row) == 0, (
            "Prospecting/Engaging deals should not be included in fit stats"
        )


# ===================================================================
# 15.5 Account Health (5 tests)
# ===================================================================
class TestAccountHealth:
    """Verify account health score using synthetic account_stats DataFrames."""

    @staticmethod
    def _make_account_stats(
        account: str,
        wins: int,
        losses: int,
        recent_losses: int,
    ) -> pd.DataFrame:
        """Build a minimal account_stats DataFrame for unit tests."""
        total = wins + losses
        winrate = wins / total if total > 0 else 0.0
        return pd.DataFrame(
            {
                "account": [account],
                "wins": [wins],
                "losses": [losses],
                "total": [total],
                "winrate": [winrate],
                "recent_losses": [recent_losses],
            }
        )

    def test_account_health_neutral_when_few_deals(self):
        """Conta com < 3 deals fechados retorna 50 (neutro)."""
        stats = self._make_account_stats("TestCo", 1, 1, 0)
        score, meta = calculate_account_health_score("TestCo", stats)
        assert score == 50.0, (
            f"Expected neutral score 50 for account with 2 deals, got {score}"
        )

    def test_account_health_high_winrate(self):
        """Conta com 80% WR e 0 losses recentes -> score=100 (topo do range)."""
        stats = self._make_account_stats("GoodCo", 8, 2, 0)
        score, meta = calculate_account_health_score("GoodCo", stats)
        assert score == pytest.approx(100.0, abs=0.5), (
            f"Expected score ~100 for 80% WR with 0 recent losses, got {score}"
        )

    def test_account_health_low_with_recent_losses(self):
        """Conta com WR baixo + losses recentes -> score=0."""
        # WR = 40% (abaixo do WR_MIN=50%), base = 0
        # penalty = min(3*5, 15) = 15 -> score = max(0, 0-15) = 0
        stats = self._make_account_stats("BadCo", 4, 6, 3)
        score, meta = calculate_account_health_score("BadCo", stats)
        assert score == pytest.approx(0.0, abs=0.5), (
            f"Expected score ~0 for 40% WR with 3 recent losses, got {score}"
        )

    def test_account_health_penalty_capped(self):
        """Penalizacao por losses recentes e capped."""
        # WR = 50% (WR_MIN), base = 25
        # penalty = min(5*5, 15) = 15 -> score = 25 - 15 = 10
        stats = self._make_account_stats("CapCo", 5, 5, 5)
        score, meta = calculate_account_health_score("CapCo", stats)
        assert score == pytest.approx(10.0, abs=0.5), (
            f"Expected score ~10 for 50% WR with 5 recent losses (penalty capped), got {score}"
        )

    def test_account_health_score_never_negative(self):
        """Score nunca fica abaixo de 0."""
        # WR = 0%, recent_losses = 4, penalty = min(4*10, 30) = 30
        # score = max(0, 0 - 30) = 0
        stats = self._make_account_stats("ZeroCo", 0, 10, 4)
        score, meta = calculate_account_health_score("ZeroCo", stats)
        assert score >= 0.0, (
            f"Account health score should never be negative, got {score}"
        )
        assert score == 0.0, (
            f"Expected score 0 for 0% WR with losses penalty, got {score}"
        )


# ===================================================================
# Shared fixtures for engine integration tests
# ===================================================================
@pytest.fixture(scope="module")
def real_data():
    """Load all data from CSVs once per test module."""
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    )
    return load_data(data_dir)


@pytest.fixture(scope="module")
def scoring_engine(real_data):
    """Create a ScoringEngine from real data."""
    return ScoringEngine(
        pipeline_df=real_data["pipeline"],
        accounts_df=real_data["accounts"],
        products_df=real_data["products"],
        sales_teams_df=real_data["sales_teams"],
    )


@pytest.fixture(scope="module")
def scored_pipeline(scoring_engine):
    """Score all active deals using the engine."""
    return scoring_engine.score_pipeline()


# ===================================================================
# 15.6 Engine Integration (9 tests)
# ===================================================================
class TestEngineIntegration:
    """Integration tests using real CSV data and the full ScoringEngine."""

    def test_score_pipeline_returns_all_active_deals(
        self, real_data, scored_pipeline
    ):
        """score_pipeline() retorna um score para cada deal ativo."""
        active = get_active_deals(real_data)
        expected_count = len(active)
        actual_count = len(scored_pipeline)
        assert actual_count == expected_count, (
            f"Expected {expected_count} scored deals (all active), got {actual_count}"
        )

    def test_score_final_between_0_and_100(self, scored_pipeline):
        """Todos os scores finais estao entre 0 e 100."""
        assert (scored_pipeline["score_final"] >= 0).all(), (
            "All final scores should be >= 0"
        )
        assert (scored_pipeline["score_final"] <= 100).all(), (
            "All final scores should be <= 100"
        )

    def test_score_final_no_nan(self, scored_pipeline):
        """Nenhum NaN no score final."""
        nan_count = scored_pipeline["score_final"].isna().sum()
        assert nan_count == 0, (
            f"score_final should have no NaN values, found {nan_count}"
        )

    def test_won_and_lost_excluded_from_scoring(self, scored_pipeline):
        """Deals Won e Lost nao aparecem no resultado."""
        stages = set(scored_pipeline["deal_stage"].unique())
        forbidden = {"Won", "Lost"}
        overlap = stages & forbidden
        assert len(overlap) == 0, (
            f"Won/Lost deals should not appear in scored output, found: {overlap}"
        )

    def test_weighted_components_sum_to_final(self, scored_pipeline):
        """Soma dos componentes ponderados = score final (tolerancia 0.5)."""
        sample = scored_pipeline.head(100)
        for _, row in sample.iterrows():
            weighted_sum = (
                row["score_stage"] * WEIGHTS["stage"]
                + row["score_value"] * WEIGHTS["expected_value"]
                + row["score_velocity"] * WEIGHTS["velocity"]
                + row["score_seller_fit"] * WEIGHTS["seller_fit"]
                + row["score_account_health"] * WEIGHTS["account_health"]
            )
            assert row["score_final"] == pytest.approx(weighted_sum, abs=0.5), (
                f"score_final ({row['score_final']}) should be approx "
                f"sum of weighted components ({weighted_sum})"
            )

    def test_engaging_mean_score_higher_than_prospecting(self, scored_pipeline):
        """Score medio de Engaging > score medio de Prospecting."""
        engaging_mean = scored_pipeline[
            scored_pipeline["deal_stage"] == "Engaging"
        ]["score_final"].mean()
        prospecting_mean = scored_pipeline[
            scored_pipeline["deal_stage"] == "Prospecting"
        ]["score_final"].mean()
        assert engaging_mean > prospecting_mean, (
            f"Engaging mean ({engaging_mean:.1f}) should be higher than "
            f"Prospecting mean ({prospecting_mean:.1f})"
        )

    def test_zombie_flag_set_when_ratio_above_2(self, scored_pipeline):
        """is_zombie = True quando velocity_ratio >= 2.0."""
        has_ratio = scored_pipeline[scored_pipeline["velocity_ratio"].notna()]
        zombies = has_ratio[has_ratio["velocity_ratio"] >= 2.0]
        if len(zombies) > 0:
            assert zombies["is_zombie"].all(), (
                "All deals with velocity_ratio >= 2.0 should have is_zombie=True"
            )

        non_zombies = has_ratio[has_ratio["velocity_ratio"] < 2.0]
        if len(non_zombies) > 0:
            assert not non_zombies["is_zombie"].any(), (
                "Deals with velocity_ratio < 2.0 should have is_zombie=False"
            )

    def test_critical_zombie_requires_zombie_and_high_value(self, scored_pipeline):
        """is_critical_zombie requer is_zombie AND valor > P75."""
        critical = scored_pipeline[scored_pipeline["is_critical_zombie"] == True]  # noqa: E712
        if len(critical) > 0:
            # Every critical zombie must also be a zombie
            assert critical["is_zombie"].all(), (
                "All critical zombies must also be zombies"
            )

    def test_score_breakdown_has_all_components(self, scored_pipeline):
        """score_breakdown contem stage, expected_value, velocity, seller_fit, account_health."""
        assert "score_breakdown" in scored_pipeline.columns, (
            "scored pipeline should have a 'score_breakdown' column"
        )
        expected_keys = {"stage", "expected_value", "velocity", "seller_fit", "account_health"}
        # Check first non-null breakdown
        sample = scored_pipeline["score_breakdown"].dropna()
        assert len(sample) > 0, "At least one deal should have a score_breakdown"
        breakdown = sample.iloc[0]
        if isinstance(breakdown, dict):
            component_keys = set(breakdown.get("components", {}).keys())
        else:
            component_keys = set()
        assert expected_keys.issubset(component_keys), (
            f"score_breakdown.components should contain {expected_keys}, "
            f"got {component_keys}"
        )
