"""Estágios oficiais do pipeline no dataset do challenge (build-003).

CRP-REAL-03: única taxonomia válida em runtime para listagem, filtros e payloads HTTP.
"""

from __future__ import annotations

from typing import Final, Literal

# Valores canónicos em `sales_pipeline.deal_stage` / metadata oficial
OFFICIAL_DEAL_STAGES: Final[tuple[str, ...]] = (
    "Prospecting",
    "Engaging",
    "Won",
    "Lost",
)
OFFICIAL_DEAL_STAGES_SET: Final[frozenset[str]] = frozenset(OFFICIAL_DEAL_STAGES)

DealStage = Literal["Prospecting", "Engaging", "Won", "Lost"]


def is_official_deal_stage(value: str) -> bool:
    return (value or "").strip() in OFFICIAL_DEAL_STAGES_SET


def normalize_deal_stage(value: str | None) -> str:
    """Normaliza para um dos quatro estágios.

    Desconhecido -> Engaging (conservador para scoring).
    """
    v = (value or "").strip()
    if v in OFFICIAL_DEAL_STAGES_SET:
        return v
    # Legado interno pré-REAL-03
    if v == "Open":
        return "Engaging"
    return "Engaging"


def is_pipeline_open_stage(stage: str) -> bool:
    """Contagem de 'abertas' alinhada ao negócio: Prospecting + Engaging."""
    s = (stage or "").strip()
    return s in {"Prospecting", "Engaging"}
