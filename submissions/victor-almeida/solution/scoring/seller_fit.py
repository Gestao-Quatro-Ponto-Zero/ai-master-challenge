"""
Componente Seller-Deal Fit do Scoring Engine.

Avalia a afinidade do vendedor com o setor da conta.
Compara o win rate do vendedor em determinado setor com a media do time,
gerando um multiplicador que e normalizado para 0-100.

Referencia: specs/scoring_engine.md, secao 6 (Componente 4).
"""

from __future__ import annotations

import pandas as pd

from scoring.constants import (
    FIT_MULTIPLIER_MAX,
    FIT_MULTIPLIER_MIN,
    FIT_NEUTRAL_SCORE,
    SELLER_FIT_MIN_DEALS,
    SELLER_FIT_SCALE_FACTOR,
)


def build_seller_fit_stats(
    pipeline_df: pd.DataFrame,
    accounts_df: pd.DataFrame,
) -> dict:
    """Pre-calcula estatisticas de win rate por vendedor x setor e time x setor.

    Filtra apenas deals fechados (Won + Lost), faz join com accounts para
    obter o setor, e calcula win rates agregados.

    Parameters
    ----------
    pipeline_df : pd.DataFrame
        Pipeline bruto (todas as oportunidades). Deve conter as colunas:
        ``deal_stage``, ``sales_agent``, ``account``.
    accounts_df : pd.DataFrame
        Tabela de contas. Deve conter: ``account``, ``sector``.

    Returns
    -------
    dict
        ``"seller_sector"`` : DataFrame com colunas
            [sales_agent, sector, wins, total, winrate]
        ``"team_sector"`` : DataFrame com colunas
            [sector, wins, total, winrate]
    """
    # Filtrar apenas deals fechados (Won ou Lost)
    closed = pipeline_df[pipeline_df["deal_stage"].isin(["Won", "Lost"])].copy()

    # Obter setor: se pipeline ja tem 'sector' (enriquecido), usar direto
    if "sector" not in closed.columns:
        closed = closed.merge(
            accounts_df[["account", "sector"]],
            on="account",
            how="left",
        )

    # Remover linhas sem setor (account nao encontrado ou setor nulo)
    closed = closed.dropna(subset=["sector"])

    # Marcar wins
    closed["is_win"] = (closed["deal_stage"] == "Won").astype(int)

    # Stats por vendedor x setor
    seller_sector = (
        closed.groupby(["sales_agent", "sector"])
        .agg(wins=("is_win", "sum"), total=("is_win", "count"))
        .reset_index()
    )
    seller_sector["winrate"] = seller_sector["wins"] / seller_sector["total"]

    # Stats por setor (media do time)
    team_sector = (
        closed.groupby("sector")
        .agg(wins=("is_win", "sum"), total=("is_win", "count"))
        .reset_index()
    )
    team_sector["winrate"] = team_sector["wins"] / team_sector["total"]

    return {
        "seller_sector": seller_sector,
        "team_sector": team_sector,
    }


def calculate_seller_fit_score(
    sales_agent: str,
    account_sector: str | None,
    fit_stats: dict,
) -> tuple[float, dict]:
    """Calcula o score de Seller-Deal Fit para um deal especifico.

    O score compara o win rate do vendedor no setor da conta com a media
    do time nesse setor, gerando um multiplicador normalizado para 0-100.

    Parameters
    ----------
    sales_agent : str
        Nome do vendedor.
    account_sector : str | None
        Setor da conta (pode ser None/NaN se a conta nao foi encontrada).
    fit_stats : dict
        Dicionario retornado por ``build_seller_fit_stats()``.

    Returns
    -------
    tuple[float, dict]
        ``(score, metadata)`` onde score esta em [0, 100] e metadata contem
        dados para explicabilidade.
    """
    metadata: dict = {
        "sales_agent": sales_agent,
        "sector": account_sector,
    }

    # Sem setor -> score neutro
    if account_sector is None or (isinstance(account_sector, float) and pd.isna(account_sector)):
        metadata["reason"] = "sem_setor"
        return FIT_NEUTRAL_SCORE, metadata

    seller_sector = fit_stats["seller_sector"]
    team_sector = fit_stats["team_sector"]

    # Buscar stats do vendedor neste setor
    seller_row = seller_sector[
        (seller_sector["sales_agent"] == sales_agent)
        & (seller_sector["sector"] == account_sector)
    ]

    # Buscar stats do time neste setor
    team_row = team_sector[team_sector["sector"] == account_sector]

    # Verificar se ha dados suficientes do vendedor
    if seller_row.empty or seller_row.iloc[0]["total"] < SELLER_FIT_MIN_DEALS:
        metadata["reason"] = "dados_insuficientes"
        metadata["seller_deals_in_sector"] = (
            0 if seller_row.empty else int(seller_row.iloc[0]["total"])
        )
        return FIT_NEUTRAL_SCORE, metadata

    seller_wr = seller_row.iloc[0]["winrate"]
    seller_total = int(seller_row.iloc[0]["total"])

    # Verificar se ha dados do time no setor
    if team_row.empty or team_row.iloc[0]["winrate"] == 0:
        metadata["reason"] = "sem_referencia_time"
        return FIT_NEUTRAL_SCORE, metadata

    team_wr = team_row.iloc[0]["winrate"]

    # Calcular multiplicador
    raw_multiplier = seller_wr / team_wr
    clamped_multiplier = max(FIT_MULTIPLIER_MIN, min(raw_multiplier, FIT_MULTIPLIER_MAX))

    # Normalizar para 0-100 centrado em 50
    # multiplier 1.0  -> score 50 (igual a media do time)
    # multiplier 1.25 -> score 70 (acima da media)
    # multiplier 0.5  -> score 10 (abaixo da media)
    score = 50 + (clamped_multiplier - 1.0) * SELLER_FIT_SCALE_FACTOR
    score = max(0.0, min(100.0, score))

    metadata.update(
        {
            "seller_winrate": round(seller_wr, 3),
            "team_winrate": round(team_wr, 3),
            "raw_multiplier": round(raw_multiplier, 3),
            "clamped_multiplier": round(clamped_multiplier, 3),
            "seller_deals_in_sector": seller_total,
            "reason": "calculado",
        }
    )

    return round(score, 1), metadata
