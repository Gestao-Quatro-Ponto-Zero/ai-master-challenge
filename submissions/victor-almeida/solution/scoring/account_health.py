"""
Componente de Saude da Conta (Account Health).

Avalia o historico de sucesso (wins vs losses) de cada conta.
Contas com alto win rate historico indicam relacionamento saudavel;
contas com muitos losses recentes recebem penalizacao adicional.
"""

from __future__ import annotations

from typing import Optional, Union

import pandas as pd

from scoring.constants import (
    ACCOUNT_HEALTH_MIN_DEALS,
    ACCOUNT_HEALTH_NEUTRAL,
    ACCOUNT_HEALTH_WR_MAX,
    ACCOUNT_HEALTH_WR_MIN,
    MAX_LOSS_PENALTY,
    RECENT_LOSS_PENALTY,
    RECENT_LOSS_WINDOW_DAYS,
    REFERENCE_DATE,
)


def build_account_health_stats(
    pipeline_df: pd.DataFrame,
    reference_date: pd.Timestamp = REFERENCE_DATE,
) -> pd.DataFrame:
    """Pre-calcula estatisticas de saude por conta.

    Filtra apenas deals fechados (Won + Lost) e agrupa por conta para
    calcular wins, losses, total, winrate e losses recentes.

    Args:
        pipeline_df: DataFrame do pipeline (ja enriquecido, com close_date
            como datetime).
        reference_date: Data de referencia para calcular losses recentes.
            Default: 2017-12-31.

    Returns:
        DataFrame com colunas:
            account, wins, losses, total, winrate, recent_losses.
        Retorna DataFrame vazio com as colunas corretas se nao houver
        deals fechados.
    """
    result_columns = ["account", "wins", "losses", "total", "winrate", "recent_losses"]

    closed = pipeline_df[pipeline_df["deal_stage"].isin(["Won", "Lost"])].copy()

    if closed.empty:
        return pd.DataFrame(columns=result_columns)

    # Stats gerais por conta
    stats = (
        closed.groupby("account")
        .agg(
            wins=("deal_stage", lambda x: (x == "Won").sum()),
            losses=("deal_stage", lambda x: (x == "Lost").sum()),
            total=("deal_stage", "count"),
        )
        .reset_index()
    )
    stats["winrate"] = stats["wins"] / stats["total"]

    # Losses recentes (dentro da janela antes da data de referencia)
    cutoff_date = reference_date - pd.Timedelta(days=RECENT_LOSS_WINDOW_DAYS)
    recent_lost = closed[
        (closed["deal_stage"] == "Lost")
        & (closed["close_date"] >= cutoff_date)
    ]
    recent_counts = (
        recent_lost.groupby("account").size().reset_index(name="recent_losses")
    )

    stats = stats.merge(recent_counts, on="account", how="left")
    stats["recent_losses"] = stats["recent_losses"].fillna(0).astype(int)

    return stats


def calculate_account_health_score(
    account: Optional[Union[str, float]],
    account_stats: pd.DataFrame,
) -> tuple[float, dict]:
    """Calcula o score de saude da conta.

    Logica:
    - Conta None/NaN: retorna score neutro (50).
    - Conta nao encontrada ou < 3 deals fechados: score neutro (50).
    - Caso contrario: base_score = winrate * 100, com penalizacao
      por losses recentes (ate -30 pontos).

    Args:
        account: Nome da conta. Pode ser None ou NaN para deals sem conta.
        account_stats: DataFrame pre-calculado por build_account_health_stats().

    Returns:
        Tupla (score, metadata):
        - score: float entre 0 e 100.
        - metadata: dict com dados para explicabilidade.
    """
    # Conta ausente (None ou NaN)
    if account is None or (isinstance(account, float) and pd.isna(account)):
        return ACCOUNT_HEALTH_NEUTRAL, {
            "account": None,
            "reason": "sem_conta",
        }

    metadata: dict = {"account": account}

    row = account_stats[account_stats["account"] == account]

    if row.empty or row.iloc[0]["total"] < ACCOUNT_HEALTH_MIN_DEALS:
        metadata["reason"] = "dados_insuficientes"
        metadata["total_deals"] = 0 if row.empty else int(row.iloc[0]["total"])
        return ACCOUNT_HEALTH_NEUTRAL, metadata

    r = row.iloc[0]
    winrate = r["winrate"]
    recent_losses = int(r["recent_losses"])

    # Score base = winrate normalizado para range completo 0-100
    # Mapeia [WR_MIN, WR_MAX] para [25, 100], clamped em [0, 100]
    wr_range = ACCOUNT_HEALTH_WR_MAX - ACCOUNT_HEALTH_WR_MIN
    if wr_range > 0:
        base_score = 25 + (winrate - ACCOUNT_HEALTH_WR_MIN) / wr_range * 75
    else:
        base_score = 50.0
    base_score = max(0.0, min(100.0, base_score))

    # Penalizacao por losses recentes
    loss_penalty = min(recent_losses * RECENT_LOSS_PENALTY, MAX_LOSS_PENALTY)

    score = max(0.0, base_score - loss_penalty)

    metadata.update(
        {
            "wins": int(r["wins"]),
            "losses": int(r["losses"]),
            "total_deals": int(r["total"]),
            "winrate": round(winrate, 3),
            "recent_losses": recent_losses,
            "loss_penalty": loss_penalty,
            "reason": "calculado",
        }
    )

    return round(score, 1), metadata
