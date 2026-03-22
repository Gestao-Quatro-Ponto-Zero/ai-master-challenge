"""
Modulo Next Best Action (NBA).

Transforma o score numerico de cada deal em uma instrucao ativa e especifica
para o vendedor. Em vez de exibir apenas "Score 72", o sistema diz o que fazer.

Referencia: specs/next_best_action.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from scoring.constants import (
    SELLER_FIT_MIN_DEALS,
    STAGE_REFERENCE_DAYS,
    ZOMBIE_THRESHOLD,
)
from scoring.seller_fit import build_seller_fit_stats


# ---------------------------------------------------------------------------
# Constantes do NBA
# ---------------------------------------------------------------------------

REFERENCIA_ENGAGING = STAGE_REFERENCE_DAYS.get("Engaging") or 88
REFERENCIA_PROSPECTING = 30

RATIO_PARADO = 1.0
RATIO_RISCO = 1.5
RATIO_ZUMBI = ZOMBIE_THRESHOLD  # 2.0

PERCENTIL_VALOR = 0.75
RATIO_FIT_BAIXO = 0.8
THRESHOLD_LOSSES_CONTA = 2


# ---------------------------------------------------------------------------
# Task 4.1 — Data structures
# ---------------------------------------------------------------------------


@dataclass
class NBAContext:
    """Contexto pre-calculado, compartilhado entre todos os deals."""

    top_sellers_por_setor: dict[str, str]  # {sector: seller_name}
    percentil_75_valor: float
    referencia_prospecting: int  # ~30 days
    referencia_engaging: int  # 88 days


@dataclass
class RegraAplicavel:
    """Uma regra NBA que se aplica a um deal especifico."""

    id: str  # 'NBA-01', ..., 'NBA-ZB'
    nome: str
    prioridade: int  # 1 (critical) to 5 (minimal)
    mensagem: str
    tipo: str  # 'alerta' | 'risco' | 'oportunidade' | 'orientacao'


@dataclass
class NBAResult:
    """Resultado final da NBA para um deal."""

    acao_principal: RegraAplicavel
    acoes_secundarias: list[RegraAplicavel] = field(default_factory=list)  # max 2

    @property
    def tem_acao(self) -> bool:
        return self.acao_principal is not None

    @property
    def cor_indicador(self) -> str:
        """Cor para UI baseada no tipo da acao principal."""
        cores = {
            "alerta": "amarelo",
            "risco": "vermelho",
            "oportunidade": "verde",
            "orientacao": "azul",
        }
        if self.acao_principal is None:
            return "cinza"
        return cores.get(self.acao_principal.tipo, "cinza")


# ---------------------------------------------------------------------------
# Task 4.2 — Individual rules
# ---------------------------------------------------------------------------


def _regra_nba_zb(deal: dict, contexto: NBAContext) -> Optional[RegraAplicavel]:
    """NBA-ZB: Deal Zumbi (ratio > 2.0). Prioridade 1, tipo risco.

    Apenas Engaging (Prospecting nao tem dados temporais).
    """
    dias = deal.get("dias_no_stage")
    if dias is None:
        return None

    if deal.get("deal_stage") != "Engaging":
        return None

    if not deal.get("is_zombie", False):
        return None

    ref = contexto.referencia_engaging
    ratio = dias / ref if ref > 0 else 0

    if ratio <= RATIO_ZUMBI:
        return None

    mensagem = (
        f"Deal classificado como zumbi — parado ha {dias} dias "
        f"({ratio:.1f}x a referencia). "
        f"Considerar descarte ou requalificacao total com novo approach."
    )

    return RegraAplicavel(
        id="NBA-ZB",
        nome="Zumbi",
        prioridade=1,
        mensagem=mensagem,
        tipo="risco",
    )


def _regra_nba_06(deal: dict, contexto: NBAContext) -> Optional[RegraAplicavel]:
    """NBA-06: Prioridade Maxima. Prioridade 1, tipo oportunidade.

    Engaging + valor >= P75 + dias <= 88.
    """
    if deal.get("deal_stage") != "Engaging":
        return None

    valor = deal.get("valor_deal", 0) or 0
    if valor < contexto.percentil_75_valor:
        return None

    dias = deal.get("dias_no_stage")
    if dias is None:
        return None

    if dias > contexto.referencia_engaging:
        return None

    mensagem = (
        f"Deal saudavel e de alto valor (${valor:,.0f}). "
        f"Prioridade maxima para fechar esta semana."
    )

    return RegraAplicavel(
        id="NBA-06",
        nome="Prioridade Maxima",
        prioridade=1,
        mensagem=mensagem,
        tipo="oportunidade",
    )


def _regra_nba_02(deal: dict, contexto: NBAContext) -> Optional[RegraAplicavel]:
    """NBA-02: Deal em Risco. Prioridade 2, tipo risco.

    1.5 < ratio <= 2.0.  Apenas Engaging.
    """
    dias = deal.get("dias_no_stage")
    if dias is None:
        return None

    if deal.get("deal_stage") != "Engaging":
        return None

    # Zombies nao recebem NBA-02
    if deal.get("is_zombie", False):
        return None

    ref = contexto.referencia_engaging
    ratio = dias / ref if ref > 0 else 0

    if ratio <= RATIO_RISCO or ratio > RATIO_ZUMBI:
        return None

    setor = deal.get("setor_conta")
    if setor:
        mensagem = (
            f"Deal em risco — parado ha {dias} dias. "
            f"Enviar case de sucesso do setor {setor}."
        )
    else:
        mensagem = (
            f"Deal em risco — parado ha {dias} dias. "
            f"Enviar case de sucesso do setor."
        )

    return RegraAplicavel(
        id="NBA-02",
        nome="Deal em Risco",
        prioridade=2,
        mensagem=mensagem,
        tipo="risco",
    )


def _regra_nba_05(deal: dict, contexto: NBAContext) -> Optional[RegraAplicavel]:
    """NBA-05: Conta Problematica. Prioridade 2, tipo risco.

    losses_conta >= 2.
    """
    account = deal.get("account")
    if account is None:
        return None

    losses = deal.get("losses_conta", 0) or 0
    if losses < THRESHOLD_LOSSES_CONTA:
        return None

    mensagem = (
        f"Esta conta ja teve {losses} deals perdidos. "
        f"Revisar approach antes de investir mais tempo."
    )

    return RegraAplicavel(
        id="NBA-05",
        nome="Conta Problematica",
        prioridade=2,
        mensagem=mensagem,
        tipo="risco",
    )


def _regra_nba_06b(deal: dict, contexto: NBAContext) -> Optional[RegraAplicavel]:
    """NBA-06B: Prospecting Alto Valor. Prioridade 2, tipo oportunidade.

    Prospecting + valor >= P75.
    """
    if deal.get("deal_stage") != "Prospecting":
        return None

    valor = deal.get("valor_deal", 0) or 0
    if valor < contexto.percentil_75_valor:
        return None

    produto = deal.get("product", "")

    mensagem = (
        f"Oportunidade de alto valor ({produto}, ${valor:,.0f}) em Prospecting. "
        f"Priorizar qualificacao para mover para Engaging."
    )

    return RegraAplicavel(
        id="NBA-06B",
        nome="Prospecting Alto Valor",
        prioridade=2,
        mensagem=mensagem,
        tipo="oportunidade",
    )


def _regra_nba_01(deal: dict, contexto: NBAContext) -> Optional[RegraAplicavel]:
    """NBA-01: Deal Parado. Prioridade 3, tipo alerta.

    1.0 < ratio <= 1.5.  Apenas Engaging.
    """
    dias = deal.get("dias_no_stage")
    if dias is None:
        return None

    if deal.get("deal_stage") != "Engaging":
        return None

    # Zombies nao recebem NBA-01
    if deal.get("is_zombie", False):
        return None

    ref = contexto.referencia_engaging
    ratio = dias / ref if ref > 0 else 0

    if ratio <= RATIO_PARADO or ratio > RATIO_RISCO:
        return None

    mensagem = (
        f"Deal parado ha {dias} dias "
        f"(media do stage: {ref} dias). "
        f"Agendar follow-up ou requalificar."
    )

    return RegraAplicavel(
        id="NBA-01",
        nome="Deal Parado",
        prioridade=3,
        mensagem=mensagem,
        tipo="alerta",
    )


def _regra_nba_04(deal: dict, contexto: NBAContext) -> Optional[RegraAplicavel]:
    """NBA-04: Seller Fit Baixo. Prioridade 4, tipo orientacao.

    seller_wr < team_wr * 0.8 AND deals >= 5.
    """
    setor = deal.get("setor_conta")
    if setor is None:
        return None

    deals_count = deal.get("deals_vendedor_no_setor", 0) or 0
    if deals_count < SELLER_FIT_MIN_DEALS:
        return None

    seller_wr = deal.get("seller_sector_winrate", 0) or 0
    team_wr = deal.get("team_sector_winrate", 0) or 0

    if team_wr == 0:
        return None

    if seller_wr >= team_wr * RATIO_FIT_BAIXO:
        return None

    wr_v = round(seller_wr * 100, 1)
    wr_t = round(team_wr * 100, 1)

    top_seller = contexto.top_sellers_por_setor.get(setor)

    if top_seller:
        mensagem = (
            f"Seu historico em {setor} esta abaixo da media "
            f"({wr_v}% vs {wr_t}% do time). "
            f"Consultar {top_seller} para estrategia."
        )
    else:
        mensagem = (
            f"Seu historico em {setor} esta abaixo da media "
            f"({wr_v}% vs {wr_t}% do time). "
            f"Buscar cases de sucesso internos para aprimorar abordagem."
        )

    return RegraAplicavel(
        id="NBA-04",
        nome="Seller Fit Baixo",
        prioridade=4,
        mensagem=mensagem,
        tipo="orientacao",
    )


# All rules in evaluation order
_ALL_RULES = [
    _regra_nba_zb,
    _regra_nba_06,
    _regra_nba_02,
    _regra_nba_05,
    _regra_nba_06b,
    _regra_nba_01,
    _regra_nba_04,
]


# ---------------------------------------------------------------------------
# Task 4.3 — Priority resolution
# ---------------------------------------------------------------------------


def _build_fallback(deal_stage: str) -> RegraAplicavel:
    """Build fallback RegraAplicavel when no rules apply."""
    if deal_stage == "Prospecting":
        mensagem = (
            "Deal em fase inicial de qualificacao. "
            "Proximo passo: validar fit e agendar primeiro contato."
        )
    else:
        mensagem = (
            "Deal dentro dos parametros normais. "
            "Manter acompanhamento regular."
        )

    return RegraAplicavel(
        id="FALLBACK",
        nome="Fallback",
        prioridade=5,
        mensagem=mensagem,
        tipo="orientacao",
    )


def resolver_nba(regras_aplicaveis: list[RegraAplicavel]) -> NBAResult:
    """Resolve a lista de regras aplicaveis em NBAResult.

    - Ordena por prioridade (menor numero = maior prioridade).
    - Excecao: NBA-05 prevalece sobre NBA-06.
    - Acoes secundarias limitadas a max 2.
    """
    if not regras_aplicaveis:
        # Caller should handle fallback before calling resolver
        # but just in case, return an Engaging fallback
        fallback = _build_fallback("Engaging")
        return NBAResult(acao_principal=fallback, acoes_secundarias=[])

    # Sort by priority (lowest number = highest priority)
    regras_sorted = sorted(regras_aplicaveis, key=lambda r: r.prioridade)

    acao_principal = regras_sorted[0]
    remaining = regras_sorted[1:]

    # Exception: NBA-05 overrides NBA-06
    if acao_principal.id == "NBA-06" and any(
        r.id == "NBA-05" for r in regras_aplicaveis
    ):
        nba05 = next(r for r in regras_aplicaveis if r.id == "NBA-05")
        acao_principal = nba05
        remaining = [r for r in regras_sorted if r.id != "NBA-05"]

    # Remove principal from secondary list
    acoes_secundarias = [r for r in remaining if r.id != acao_principal.id][:2]

    return NBAResult(
        acao_principal=acao_principal,
        acoes_secundarias=acoes_secundarias,
    )


# ---------------------------------------------------------------------------
# Task 4.4 — Context calculation
# ---------------------------------------------------------------------------


def build_nba_context(
    pipeline_df: pd.DataFrame,
    products_df: pd.DataFrame,
) -> NBAContext:
    """Build pre-calculated NBA context shared across all deals.

    Args:
        pipeline_df: Full pipeline (all stages, enriched with sector).
        products_df: Products table (with sales_price).

    Returns:
        NBAContext with top sellers per sector, P75 value, and reference days.
    """
    # --- Top sellers per sector ---
    top_sellers = _calculate_top_sellers(pipeline_df)

    # --- P75 of deal values (using product prices as proxy for active deals) ---
    p75_valor = _calculate_p75_valor(pipeline_df, products_df)

    return NBAContext(
        top_sellers_por_setor=top_sellers,
        percentil_75_valor=p75_valor,
        referencia_prospecting=REFERENCIA_PROSPECTING,
        referencia_engaging=REFERENCIA_ENGAGING,
    )


def _calculate_top_sellers(pipeline_df: pd.DataFrame) -> dict[str, str]:
    """Calculate best seller per sector (highest win rate with >= 5 deals).

    Returns dict mapping sector to seller name.
    """
    closed = pipeline_df[pipeline_df["deal_stage"].isin(["Won", "Lost"])].copy()

    if closed.empty or "sector" not in closed.columns:
        return {}

    closed = closed.dropna(subset=["sector"])

    if closed.empty:
        return {}

    closed["is_win"] = (closed["deal_stage"] == "Won").astype(int)

    stats = (
        closed.groupby(["sales_agent", "sector"])
        .agg(wins=("is_win", "sum"), total=("is_win", "count"))
        .reset_index()
    )

    # Filter sellers with at least 5 deals in the sector
    stats = stats[stats["total"] >= SELLER_FIT_MIN_DEALS].copy()

    if stats.empty:
        return {}

    stats["winrate"] = stats["wins"] / stats["total"]

    # For each sector, pick the seller with highest win rate
    # (tiebreak by total deals descending)
    stats = stats.sort_values(
        ["sector", "winrate", "total"], ascending=[True, False, False]
    )
    top = stats.groupby("sector").first().reset_index()

    return dict(zip(top["sector"], top["sales_agent"]))


def _calculate_p75_valor(
    pipeline_df: pd.DataFrame,
    products_df: pd.DataFrame,
) -> float:
    """Calculate P75 of deal values for active deals.

    Uses sales_price (product price proxy) for active deals.
    """
    from scoring.constants import ACTIVE_STAGES

    active = pipeline_df[pipeline_df["deal_stage"].isin(ACTIVE_STAGES)]

    if "sales_price" in active.columns and not active.empty:
        values = active["sales_price"].dropna()
        if not values.empty:
            return float(values.quantile(PERCENTIL_VALOR))

    # Fallback: use product prices
    if not products_df.empty and "sales_price" in products_df.columns:
        return float(products_df["sales_price"].quantile(PERCENTIL_VALOR))

    return 0.0


# ---------------------------------------------------------------------------
# Task 4.5 — Main functions
# ---------------------------------------------------------------------------


def calcular_nba(
    deal_data: dict,
    contexto: NBAContext,
    pipeline_df: pd.DataFrame,
) -> NBAResult:
    """Calculate NBA for a single deal.

    Args:
        deal_data: Dict with deal data (see spec for structure).
        contexto: Pre-calculated NBAContext.
        pipeline_df: Full pipeline DataFrame (used for context if needed).

    Returns:
        NBAResult with acao_principal and acoes_secundarias.
    """
    regras: list[RegraAplicavel] = []

    for rule_fn in _ALL_RULES:
        result = rule_fn(deal_data, contexto)
        if result is not None:
            regras.append(result)

    if not regras:
        deal_stage = deal_data.get("deal_stage", "Engaging")
        fallback = _build_fallback(deal_stage)
        return NBAResult(acao_principal=fallback, acoes_secundarias=[])

    return resolver_nba(regras)


def calcular_nba_batch(
    scored_df: pd.DataFrame,
    pipeline_df: pd.DataFrame,
    products_df: Optional[pd.DataFrame] = None,
) -> dict[str, NBAResult]:
    """Calculate NBA for all active deals.

    Args:
        scored_df: DataFrame output from ScoringEngine.score_pipeline().
        pipeline_df: Full pipeline DataFrame (all stages).
        products_df: Products table. If None, will try to build context
            from pipeline_df alone.

    Returns:
        Dict mapping opportunity_id to NBAResult.
    """
    if scored_df.empty:
        return {}

    # Build products_df fallback if not provided
    if products_df is None:
        products_df = pd.DataFrame(columns=["product", "sales_price"])

    # Build context
    contexto = build_nba_context(pipeline_df, products_df)

    # Pre-calculate losses per account
    losses_per_account = _calculate_losses_per_account(pipeline_df)

    # Pre-calculate seller fit stats
    fit_stats = _get_seller_fit_stats(pipeline_df)

    results: dict[str, NBAResult] = {}

    for _, row in scored_df.iterrows():
        deal_data = _build_deal_data(row, fit_stats, losses_per_account)
        opp_id = deal_data["opportunity_id"]
        results[opp_id] = calcular_nba(deal_data, contexto, pipeline_df)

    return results


def _calculate_losses_per_account(pipeline_df: pd.DataFrame) -> dict[str, int]:
    """Count Lost deals per account from the full pipeline."""
    lost = pipeline_df[pipeline_df["deal_stage"] == "Lost"]

    if lost.empty:
        return {}

    counts = lost.groupby("account")["opportunity_id"].count()
    return counts.to_dict()


def _get_seller_fit_stats(pipeline_df: pd.DataFrame) -> dict:
    """Get seller fit stats for batch processing.

    Returns a dict with seller_sector and team_sector DataFrames.
    """
    # Need accounts_df for sector info; if pipeline already has sector, use it
    if "sector" in pipeline_df.columns:
        # Create a minimal accounts_df from pipeline data
        accounts_df = (
            pipeline_df[["account", "sector"]]
            .dropna(subset=["account", "sector"])
            .drop_duplicates(subset=["account"])
        )
    else:
        accounts_df = pd.DataFrame(columns=["account", "sector"])

    return build_seller_fit_stats(pipeline_df, accounts_df)


def _build_deal_data(
    row: pd.Series,
    fit_stats: dict,
    losses_per_account: dict[str, int],
) -> dict:
    """Build deal_data dict from a scored DataFrame row."""
    account = row.get("account")
    if isinstance(account, float) and pd.isna(account):
        account = None

    sector = row.get("sector")
    if isinstance(sector, float) and pd.isna(sector):
        sector = None

    sales_agent = row.get("sales_agent", "")

    # Get seller and team winrates from fit stats
    seller_wr = 0.0
    team_wr = 0.0
    deals_in_sector = 0

    if sector is not None and fit_stats:
        seller_sector_df = fit_stats.get("seller_sector", pd.DataFrame())
        team_sector_df = fit_stats.get("team_sector", pd.DataFrame())

        if not seller_sector_df.empty:
            seller_row = seller_sector_df[
                (seller_sector_df["sales_agent"] == sales_agent)
                & (seller_sector_df["sector"] == sector)
            ]
            if not seller_row.empty:
                seller_wr = float(seller_row.iloc[0]["winrate"])
                deals_in_sector = int(seller_row.iloc[0]["total"])

        if not team_sector_df.empty:
            team_row = team_sector_df[team_sector_df["sector"] == sector]
            if not team_row.empty:
                team_wr = float(team_row.iloc[0]["winrate"])

    # Get losses for this account
    losses_conta = 0
    if account is not None:
        losses_conta = losses_per_account.get(account, 0)

    # Get days_in_stage (may be None for Prospecting)
    dias = row.get("days_in_stage")
    if dias is not None and pd.notna(dias):
        dias = int(dias)
    else:
        dias = None

    # Get value
    valor = row.get("effective_value") or row.get("sales_price", 0)
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        valor = 0

    return {
        "opportunity_id": row.get("opportunity_id", ""),
        "sales_agent": sales_agent,
        "product": row.get("product", ""),
        "account": account,
        "deal_stage": row.get("deal_stage", ""),
        "dias_no_stage": dias,
        "valor_deal": float(valor),
        "seller_sector_winrate": seller_wr,
        "team_sector_winrate": team_wr,
        "deals_vendedor_no_setor": deals_in_sector,
        "losses_conta": losses_conta,
        "setor_conta": sector,
        "is_zombie": bool(row.get("is_zombie", False)),
        "score_final": float(row.get("score_final", 0)),
    }
