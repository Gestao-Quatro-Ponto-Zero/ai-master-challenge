"""
Componente de Velocidade / Decay por Tempo.

Penaliza deals parados no stage alem do esperado.
Referencia calibrada com P75 dos deals Won (88 dias para Engaging).
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from scoring.constants import (
    DECAY_TABLE,
    REFERENCE_DATE,
    STAGE_REFERENCE_DAYS,
    VELOCITY_NEUTRAL_SCORE,
    ZOMBIE_THRESHOLD,
)


def calculate_days_in_stage(
    deal_stage: str,
    engage_date: Optional[pd.Timestamp],
    reference_date: pd.Timestamp = REFERENCE_DATE,
) -> Optional[int]:
    """Calcula dias no stage atual.

    Prospecting: retorna None (sem dados temporais no dataset).
    Engaging: (reference_date - engage_date).days.
    Valores negativos sao tratados como 0.
    """
    if deal_stage == "Prospecting":
        return None

    if deal_stage == "Engaging":
        if engage_date is None or pd.isna(engage_date):
            return None

        days = (reference_date - engage_date).days
        return max(days, 0)

    # Stage desconhecido ou fechado
    return None


def calculate_velocity_score(
    deal_stage: str,
    days_in_stage: Optional[int],
    stage_reference_days: Optional[dict[str, Optional[int]]] = None,
) -> tuple[float, str, dict]:
    """Calcula score de velocidade com decay por tempo.

    Retorna (score, label, metadata):
    - score: 0-100
    - label: classificacao textual (saudavel, atencao, alerta, ...)
    - metadata: dados para explicabilidade
    """
    if stage_reference_days is None:
        stage_reference_days = STAGE_REFERENCE_DAYS

    # Sem dados temporais -> score neutro
    if days_in_stage is None:
        return (
            VELOCITY_NEUTRAL_SCORE,
            "sem_referencia",
            {"ratio": None},
        )

    reference = stage_reference_days.get(deal_stage)

    # Referencia ausente ou invalida -> score neutro
    if reference is None or reference <= 0:
        return (
            VELOCITY_NEUTRAL_SCORE,
            "sem_referencia",
            {"ratio": None},
        )

    ratio = days_in_stage / reference

    # Lookup na tabela de decay
    decay = 0.10
    label = "quase_morto"
    for ratio_max, decay_factor, decay_label in DECAY_TABLE:
        if ratio <= ratio_max:
            decay = decay_factor
            label = decay_label
            break

    score = decay * 100

    metadata = {
        "days_in_stage": days_in_stage,
        "reference_days": reference,
        "ratio": round(ratio, 2),
        "decay_factor": decay,
        "is_zombie": ratio >= ZOMBIE_THRESHOLD,
    }

    return score, label, metadata
