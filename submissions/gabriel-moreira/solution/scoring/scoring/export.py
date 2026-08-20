"""Exportação do dataset processado — CSV consolidado, regravado por
completo a cada carga (nunca incrementalmente).
"""

from __future__ import annotations

from pathlib import Path

from .pipeline import ScoredPipeline

EXPORT_COLUMNS = [
    "opportunity_id",
    "sales_agent",
    "manager",
    "regional_office",
    "product",
    "account",
    "sector",
    "porte",
    "deal_stage",
    "age_days",
    "p_hat",
    "valor",
    "urgencia",
    "prioridade",
    "score",
    "confianca",
    "razao_confianca",
    "estado",
    "estado_label",
    "plano_de_acao",
]


def export_processed_dataset(scored_pipeline: ScoredPipeline, output_path: str | Path) -> Path:
    """Grava o CSV consolidado com as oportunidades abertas + campos derivados.

    Cobre todas as oportunidades abertas, incluindo as sem conta vinculada
    (o campo `account` fica vazio, não a linha inteira).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scored_pipeline.scored[EXPORT_COLUMNS].to_csv(output_path, index=False)
    return output_path
