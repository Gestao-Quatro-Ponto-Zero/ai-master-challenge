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
    "preco_tabela",
    "valor",
    "urgencia",
    "prioridade",
    "score",
    "confianca",
    "completude",
    "suporte",
    "sem_precedente",
    "razao_confianca",
    "estado",
    "estado_label",
    "plano_de_acao",
    "plano_de_acao_passos",
    "score_fatores",
]

PASSOS_SEPARADOR = " | "


def export_processed_dataset(scored_pipeline: ScoredPipeline, output_path: str | Path) -> Path:
    """Grava o CSV consolidado com as oportunidades abertas + campos derivados.

    Cobre todas as oportunidades abertas, incluindo as sem conta vinculada
    (o campo `account` fica vazio, não a linha inteira). Os passos do plano
    de ação e os fatores do score (explicação em linguagem de negócio) são
    listas serializadas com " | " em colunas próprias, preservando a coluna
    `plano_de_acao` (resumo de uma linha) existente.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export_df = scored_pipeline.scored[EXPORT_COLUMNS].copy()
    export_df["plano_de_acao_passos"] = export_df["plano_de_acao_passos"].apply(
        PASSOS_SEPARADOR.join
    )
    export_df["score_fatores"] = export_df["score_fatores"].apply(PASSOS_SEPARADOR.join)
    export_df.to_csv(output_path, index=False)
    return output_path
