"""
Tests for the Next Best Action (NBA) module.

20 tests covering: individual rules, priority resolution, zombie deals,
edge cases, and real data validation.

TDD Red Phase: these tests define expected behavior BEFORE implementation.
All tests should FAIL initially and pass after scoring/nba.py is built.
"""

import os
import sys

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Path setup — allow imports from the solution root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoring.nba import (  # noqa: E402
    NBAContext,
    NBAResult,
    RegraAplicavel,
    calcular_nba,
    calcular_nba_batch,
    resolver_nba,
)
from scoring.engine import ScoringEngine  # noqa: E402
from utils.data_loader import get_active_deals, load_data  # noqa: E402


# ---------------------------------------------------------------------------
# Constants used in tests (must match the spec)
# ---------------------------------------------------------------------------
REFERENCIA_ENGAGING = 88
REFERENCIA_PROSPECTING = 30
REFERENCE_DATE = pd.Timestamp("2017-12-31")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_contexto(
    percentil_75_valor: float = 5000.0,
    referencia_prospecting: int = REFERENCIA_PROSPECTING,
    referencia_engaging: int = REFERENCIA_ENGAGING,
    top_sellers_por_setor: dict | None = None,
) -> NBAContext:
    """Build an NBAContext with sensible defaults for unit tests."""
    if top_sellers_por_setor is None:
        top_sellers_por_setor = {"technology": "Top Seller"}
    return NBAContext(
        top_sellers_por_setor=top_sellers_por_setor,
        percentil_75_valor=percentil_75_valor,
        referencia_prospecting=referencia_prospecting,
        referencia_engaging=referencia_engaging,
    )


def _make_deal(
    deal_stage: str = "Engaging",
    dias_no_stage: int | None = 50,
    valor_deal: float = 550.0,
    seller_sector_winrate: float = 0.6,
    team_sector_winrate: float = 0.6,
    deals_vendedor_no_setor: int = 10,
    losses_conta: int = 0,
    setor_conta: str | None = "technology",
    is_zombie: bool = False,
    score_final: float = 60.0,
    account: str | None = "TestCo",
    product: str = "GTX Basic",
    opportunity_id: str = "OPP-TEST-001",
    sales_agent: str = "Agent A",
) -> dict:
    """Build a deal_data dict with sensible defaults for unit tests.

    Override any parameter to test specific conditions.
    """
    return {
        "opportunity_id": opportunity_id,
        "sales_agent": sales_agent,
        "product": product,
        "account": account,
        "deal_stage": deal_stage,
        "dias_no_stage": dias_no_stage,
        "valor_deal": valor_deal,
        "seller_sector_winrate": seller_sector_winrate,
        "team_sector_winrate": team_sector_winrate,
        "deals_vendedor_no_setor": deals_vendedor_no_setor,
        "losses_conta": losses_conta,
        "setor_conta": setor_conta,
        "is_zombie": is_zombie,
        "score_final": score_final,
    }


def _make_pipeline_df() -> pd.DataFrame:
    """Build a minimal pipeline DataFrame for calcular_nba calls."""
    return pd.DataFrame(
        {
            "opportunity_id": ["OPP-1", "OPP-2"],
            "deal_stage": ["Won", "Lost"],
            "sales_agent": ["Agent A", "Agent B"],
            "account": ["TestCo", "TestCo"],
            "product": ["GTX Basic", "GTX Basic"],
            "sector": ["technology", "technology"],
        }
    )


def _find_rule_by_id(result: NBAResult, rule_id: str) -> bool:
    """Check if a rule ID appears as principal or secondary in the result."""
    if result.acao_principal.id == rule_id:
        return True
    return any(r.id == rule_id for r in result.acoes_secundarias)


# ---------------------------------------------------------------------------
# Fixtures for real data tests
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def data_dir():
    """Return the absolute path to the data/ directory."""
    return os.path.join(os.path.dirname(__file__), "..", "data")


@pytest.fixture(scope="module")
def real_data(data_dir):
    """Load all data once per test module via load_data()."""
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


@pytest.fixture(scope="module")
def nba_results(scored_pipeline, real_data):
    """Compute NBA for all scored deals."""
    return calcular_nba_batch(scored_pipeline, real_data["pipeline"])


# ===================================================================
# 12.1 Testes de regras individuais (9 tests)
# ===================================================================
class TestNBARules:
    """Verificar disparo individual de cada regra NBA."""

    def test_nba01_deal_parado_fires_when_ratio_above_1(self):
        """NBA-01 dispara quando 1.0 < ratio <= 1.5 (ex: 95 dias Engaging, ref=88)."""
        deal = _make_deal(
            deal_stage="Engaging",
            dias_no_stage=95,  # ratio = 95/88 = ~1.08 (within 1.0-1.5)
        )
        contexto = _make_contexto()
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        assert _find_rule_by_id(result, "NBA-01"), (
            f"NBA-01 (Deal Parado) should fire for 95 days Engaging (ratio ~1.08). "
            f"Got principal: {result.acao_principal.id}"
        )

    def test_nba01_does_not_fire_below_reference(self):
        """NBA-01 NAO dispara quando ratio <= 1.0."""
        deal = _make_deal(
            deal_stage="Engaging",
            dias_no_stage=80,  # ratio = 80/88 = ~0.91 (below 1.0)
        )
        contexto = _make_contexto()
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        assert not _find_rule_by_id(result, "NBA-01"), (
            f"NBA-01 should NOT fire for 80 days Engaging (ratio ~0.91). "
            f"Got principal: {result.acao_principal.id}"
        )

    def test_nba02_deal_em_risco_fires_when_ratio_above_1_5(self):
        """NBA-02 dispara quando 1.5 < ratio <= 2.0 (ex: 140 dias Engaging)."""
        deal = _make_deal(
            deal_stage="Engaging",
            dias_no_stage=140,  # ratio = 140/88 = ~1.59 (within 1.5-2.0)
        )
        contexto = _make_contexto()
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        assert _find_rule_by_id(result, "NBA-02"), (
            f"NBA-02 (Deal em Risco) should fire for 140 days Engaging (ratio ~1.59). "
            f"Got principal: {result.acao_principal.id}"
        )

    def test_nba04_seller_fit_fires_when_wr_below_80pct_team(self):
        """NBA-04 dispara quando seller_wr < team_wr * 0.8 e deals >= 5."""
        deal = _make_deal(
            seller_sector_winrate=0.35,   # 35%
            team_sector_winrate=0.63,     # 63% -> 0.63 * 0.8 = 0.504 > 0.35
            deals_vendedor_no_setor=28,   # >= 5
            dias_no_stage=50,             # healthy, so no time rules dominate
        )
        contexto = _make_contexto()
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        assert _find_rule_by_id(result, "NBA-04"), (
            f"NBA-04 (Seller Fit Baixo) should fire for WR 35% vs team 63% with 28 deals. "
            f"Got principal: {result.acao_principal.id}, "
            f"secundarias: {[r.id for r in result.acoes_secundarias]}"
        )

    def test_nba04_does_not_fire_with_few_deals(self):
        """NBA-04 NAO dispara quando vendedor tem < 5 deals no setor."""
        deal = _make_deal(
            seller_sector_winrate=0.20,   # 20% — very low
            team_sector_winrate=0.63,     # 63% — significantly higher
            deals_vendedor_no_setor=3,    # < 5 threshold
        )
        contexto = _make_contexto()
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        assert not _find_rule_by_id(result, "NBA-04"), (
            f"NBA-04 should NOT fire when seller has only 3 deals in sector. "
            f"Got principal: {result.acao_principal.id}"
        )

    def test_nba05_conta_problematica_fires_with_2_losses(self):
        """NBA-05 dispara quando conta tem >= 2 losses."""
        deal = _make_deal(
            losses_conta=2,
            dias_no_stage=50,  # healthy, so time rules don't trigger
        )
        contexto = _make_contexto()
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        assert _find_rule_by_id(result, "NBA-05"), (
            f"NBA-05 (Conta Problematica) should fire for account with 2 losses. "
            f"Got principal: {result.acao_principal.id}, "
            f"secundarias: {[r.id for r in result.acoes_secundarias]}"
        )

    def test_nba05_does_not_fire_with_1_loss(self):
        """NBA-05 NAO dispara com apenas 1 loss."""
        deal = _make_deal(
            losses_conta=1,
        )
        contexto = _make_contexto()
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        assert not _find_rule_by_id(result, "NBA-05"), (
            f"NBA-05 should NOT fire with only 1 loss. "
            f"Got principal: {result.acao_principal.id}"
        )

    def test_nba06_prioridade_maxima_fires_for_healthy_high_value(self):
        """NBA-06 dispara: Engaging + valor >= P75 + dias <= 88."""
        deal = _make_deal(
            deal_stage="Engaging",
            dias_no_stage=50,       # <= 88 (healthy)
            valor_deal=26768.0,     # GTK 500 — above P75
        )
        contexto = _make_contexto(percentil_75_valor=5000.0)  # 26768 >= 5000
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        assert _find_rule_by_id(result, "NBA-06"), (
            f"NBA-06 (Prioridade Maxima) should fire for Engaging deal with "
            f"high value ($26768) and 50 days (healthy). "
            f"Got principal: {result.acao_principal.id}"
        )

    def test_nba06b_prospecting_alto_valor(self):
        """NBA-06B dispara: Prospecting + valor >= P75."""
        deal = _make_deal(
            deal_stage="Prospecting",
            dias_no_stage=None,     # Prospecting has no temporal data
            valor_deal=26768.0,     # GTK 500 — above P75
            is_zombie=False,
        )
        contexto = _make_contexto(percentil_75_valor=5000.0)  # 26768 >= 5000
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        assert _find_rule_by_id(result, "NBA-06B"), (
            f"NBA-06B (Prospecting Alto Valor) should fire for Prospecting deal "
            f"with high value ($26768). Got principal: {result.acao_principal.id}"
        )


# ===================================================================
# 12.2 Testes de resolucao de prioridades (3 tests)
# ===================================================================
class TestNBAPriority:
    """Verificar resolucao de conflitos quando multiplas regras se aplicam."""

    def test_highest_priority_rule_wins(self):
        """Quando multiplas regras se aplicam, a de menor prioridade numerica e a principal."""
        regras = [
            RegraAplicavel(
                id="NBA-01",
                nome="Deal Parado",
                prioridade=3,
                mensagem="Deal parado ha 95 dias.",
                tipo="alerta",
            ),
            RegraAplicavel(
                id="NBA-04",
                nome="Seller Fit Baixo",
                prioridade=4,
                mensagem="Historico abaixo da media.",
                tipo="orientacao",
            ),
            RegraAplicavel(
                id="NBA-02",
                nome="Deal em Risco",
                prioridade=2,
                mensagem="Deal em risco.",
                tipo="risco",
            ),
        ]

        result = resolver_nba(regras)

        assert result.acao_principal.id == "NBA-02", (
            f"Acao principal deveria ser NBA-02 (prioridade 2, a mais alta), "
            f"mas foi {result.acao_principal.id}"
        )

    def test_nba05_overrides_nba06(self):
        """NBA-05 (Conta Problematica) prevalece sobre NBA-06 (Prioridade Maxima)."""
        regras = [
            RegraAplicavel(
                id="NBA-06",
                nome="Prioridade Maxima",
                prioridade=1,
                mensagem="Deal saudavel e de alto valor.",
                tipo="oportunidade",
            ),
            RegraAplicavel(
                id="NBA-05",
                nome="Conta Problematica",
                prioridade=2,
                mensagem="Esta conta ja teve 5 deals perdidos.",
                tipo="risco",
            ),
        ]

        result = resolver_nba(regras)

        assert result.acao_principal.id == "NBA-05", (
            f"NBA-05 (Conta Problematica) deve prevalecer sobre NBA-06 "
            f"(Prioridade Maxima) por excecao de risco. "
            f"Got principal: {result.acao_principal.id}"
        )

    def test_secondary_actions_limited_to_2(self):
        """Acoes secundarias sao limitadas a no maximo 2."""
        regras = [
            RegraAplicavel(
                id="NBA-02",
                nome="Deal em Risco",
                prioridade=2,
                mensagem="Deal em risco.",
                tipo="risco",
            ),
            RegraAplicavel(
                id="NBA-05",
                nome="Conta Problematica",
                prioridade=2,
                mensagem="Conta problematica.",
                tipo="risco",
            ),
            RegraAplicavel(
                id="NBA-01",
                nome="Deal Parado",
                prioridade=3,
                mensagem="Deal parado.",
                tipo="alerta",
            ),
            RegraAplicavel(
                id="NBA-04",
                nome="Seller Fit Baixo",
                prioridade=4,
                mensagem="Fit baixo.",
                tipo="orientacao",
            ),
        ]

        result = resolver_nba(regras)

        assert len(result.acoes_secundarias) <= 2, (
            f"Acoes secundarias devem ser no maximo 2, "
            f"mas foram {len(result.acoes_secundarias)}: "
            f"{[r.id for r in result.acoes_secundarias]}"
        )


# ===================================================================
# 12.3 Testes de deals zumbi (2 tests)
# ===================================================================
class TestNBAZombie:
    """Verificar tratamento especial de deals zumbi na NBA."""

    def test_zombie_deal_receives_nba_zb(self):
        """Deal com ratio > 2.0 recebe NBA-ZB (nao NBA-01 ou NBA-02)."""
        deal = _make_deal(
            deal_stage="Engaging",
            dias_no_stage=200,  # ratio = 200/88 = ~2.27 (zombie)
            is_zombie=True,
        )
        contexto = _make_contexto()
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        assert _find_rule_by_id(result, "NBA-ZB"), (
            f"Zombie deal (200 days, ratio ~2.27) should receive NBA-ZB. "
            f"Got principal: {result.acao_principal.id}"
        )
        assert not _find_rule_by_id(result, "NBA-01"), (
            "Zombie deal should NOT receive NBA-01 (Deal Parado)"
        )
        assert not _find_rule_by_id(result, "NBA-02"), (
            "Zombie deal should NOT receive NBA-02 (Deal em Risco)"
        )

    def test_zombie_nba_includes_days_and_ratio(self):
        """Mensagem do zumbi inclui dias no stage e ratio."""
        deal = _make_deal(
            deal_stage="Engaging",
            dias_no_stage=200,  # ratio = 200/88 = ~2.27
            is_zombie=True,
        )
        contexto = _make_contexto()
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        # Find the NBA-ZB rule (could be principal or secondary)
        zb_rule = None
        if result.acao_principal.id == "NBA-ZB":
            zb_rule = result.acao_principal
        else:
            for r in result.acoes_secundarias:
                if r.id == "NBA-ZB":
                    zb_rule = r
                    break

        assert zb_rule is not None, (
            f"NBA-ZB rule not found in result. "
            f"Principal: {result.acao_principal.id}"
        )

        # Message should contain the number of days
        assert "200" in zb_rule.mensagem, (
            f"Zombie message should include '200' (days in stage). "
            f"Got: {zb_rule.mensagem}"
        )

        # Message should contain the ratio (2.27 or similar representation)
        assert "2." in zb_rule.mensagem or "2,2" in zb_rule.mensagem, (
            f"Zombie message should include the ratio (~2.27). "
            f"Got: {zb_rule.mensagem}"
        )


# ===================================================================
# 12.4 Testes de edge cases (4 tests)
# ===================================================================
class TestNBAEdgeCases:
    """Verificar tratamento de casos limite."""

    def test_deal_without_any_rule_gets_fallback(self):
        """Deal sem nenhuma regra aplicavel recebe mensagem fallback neutra."""
        deal = _make_deal(
            deal_stage="Engaging",
            dias_no_stage=50,             # healthy (ratio ~0.57)
            valor_deal=100.0,             # low value, below P75
            seller_sector_winrate=0.6,    # same as team
            team_sector_winrate=0.6,
            deals_vendedor_no_setor=10,
            losses_conta=0,               # no losses
            is_zombie=False,
        )
        contexto = _make_contexto(percentil_75_valor=5000.0)
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        # Should get a fallback with priority 5
        assert result.acao_principal.prioridade == 5, (
            f"Fallback should have priority 5 (minimal), "
            f"got {result.acao_principal.prioridade} ({result.acao_principal.id})"
        )
        assert len(result.acoes_secundarias) == 0, (
            f"Fallback should have no secondary actions, "
            f"got {len(result.acoes_secundarias)}"
        )

    def test_prospecting_without_temporal_data_skips_time_rules(self):
        """Deals Prospecting nao recebem NBA-01, NBA-02, NBA-ZB."""
        deal = _make_deal(
            deal_stage="Prospecting",
            dias_no_stage=None,           # No temporal data for Prospecting
            valor_deal=100.0,             # low value
            losses_conta=0,
            is_zombie=False,
        )
        contexto = _make_contexto(percentil_75_valor=5000.0)
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        time_based_rules = {"NBA-01", "NBA-02", "NBA-ZB"}
        all_rule_ids = {result.acao_principal.id}
        all_rule_ids.update(r.id for r in result.acoes_secundarias)

        overlap = all_rule_ids & time_based_rules
        assert len(overlap) == 0, (
            f"Prospecting deals should NOT receive time-based rules, "
            f"but got: {overlap}. All rules: {all_rule_ids}"
        )

    def test_deal_with_null_account_skips_nba05(self):
        """Deal sem conta nao dispara NBA-05."""
        deal = _make_deal(
            account=None,
            setor_conta=None,
            losses_conta=0,               # No account => no losses
            dias_no_stage=50,
        )
        contexto = _make_contexto()
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        assert not _find_rule_by_id(result, "NBA-05"), (
            f"NBA-05 should NOT fire for a deal without an account. "
            f"Got principal: {result.acao_principal.id}"
        )

    def test_nba_result_has_acao_principal(self):
        """NBAResult sempre tem acao_principal (nunca None)."""
        deal = _make_deal()
        contexto = _make_contexto()
        pipeline_df = _make_pipeline_df()

        result = calcular_nba(deal, contexto, pipeline_df)

        assert isinstance(result, NBAResult), (
            f"calcular_nba should return NBAResult, got {type(result).__name__}"
        )
        assert result.acao_principal is not None, (
            "NBAResult.acao_principal should never be None"
        )
        assert isinstance(result.acao_principal, RegraAplicavel), (
            f"acao_principal should be RegraAplicavel, "
            f"got {type(result.acao_principal).__name__}"
        )
        assert isinstance(result.acoes_secundarias, list), (
            f"acoes_secundarias should be a list, "
            f"got {type(result.acoes_secundarias).__name__}"
        )


# ===================================================================
# 12.5 Testes com dados reais (2 tests)
# ===================================================================
class TestNBARealData:
    """Validacao com dados reais do dataset Kaggle."""

    def test_hottechi_deals_receive_nba05(
        self, real_data, scored_pipeline, nba_results
    ):
        """Deals na conta Hottechi (82 losses) recebem NBA-05."""
        # Find active deals for Hottechi
        hottechi_deals = scored_pipeline[
            scored_pipeline["account"] == "Hottechi"
        ]

        assert len(hottechi_deals) > 0, (
            "Should have active deals for Hottechi in scored pipeline"
        )

        # Verify each Hottechi deal receives NBA-05
        for _, deal_row in hottechi_deals.iterrows():
            opp_id = deal_row["opportunity_id"]
            assert opp_id in nba_results, (
                f"NBA result should exist for Hottechi deal {opp_id}"
            )
            nba = nba_results[opp_id]
            assert _find_rule_by_id(nba, "NBA-05"), (
                f"Hottechi deal {opp_id} should receive NBA-05 (Conta Problematica) "
                f"given 82 historical losses. "
                f"Got principal: {nba.acao_principal.id}, "
                f"secundarias: {[r.id for r in nba.acoes_secundarias]}"
            )

    def test_gtk500_engaging_healthy_receives_nba06(
        self, real_data, scored_pipeline, nba_results
    ):
        """Deal GTK 500 em Engaging ha 50 dias recebe NBA-06 (Prioridade Maxima).

        Se nenhum deal real atende exatamente esse criterio, sintetizamos um
        usando os dados reais como contexto.
        """
        # Look for a GTK 500 deal in Engaging with days <= 88
        gtk500_engaging = scored_pipeline[
            (scored_pipeline["product"] == "GTK 500")
            & (scored_pipeline["deal_stage"] == "Engaging")
        ]

        if len(gtk500_engaging) > 0:
            # Filter to healthy ones (days <= 88)
            if "days_in_stage" in gtk500_engaging.columns:
                healthy = gtk500_engaging[
                    gtk500_engaging["days_in_stage"] <= REFERENCIA_ENGAGING
                ]
            else:
                healthy = pd.DataFrame()

            if len(healthy) > 0:
                # Use a real deal
                opp_id = healthy.iloc[0]["opportunity_id"]
                assert opp_id in nba_results, (
                    f"NBA result should exist for GTK 500 deal {opp_id}"
                )
                nba = nba_results[opp_id]
                assert _find_rule_by_id(nba, "NBA-06"), (
                    f"Healthy GTK 500 Engaging deal {opp_id} should receive NBA-06. "
                    f"Got principal: {nba.acao_principal.id}"
                )
                return

        # No real healthy GTK 500 Engaging deal found — synthesize one
        deal = _make_deal(
            deal_stage="Engaging",
            dias_no_stage=50,
            valor_deal=26768.0,     # GTK 500 price
            product="GTK 500",
            losses_conta=0,
            is_zombie=False,
        )

        # Build context from real data
        products_df = real_data["products"]
        p75_valor = products_df["sales_price"].quantile(0.75)
        contexto = _make_contexto(percentil_75_valor=p75_valor)
        pipeline_df = real_data["pipeline"]

        result = calcular_nba(deal, contexto, pipeline_df)

        assert _find_rule_by_id(result, "NBA-06"), (
            f"GTK 500 Engaging deal with 50 days should receive NBA-06 "
            f"(Prioridade Maxima). GTK 500 price ($26768) >= P75 ({p75_valor}). "
            f"Got principal: {result.acao_principal.id}"
        )
