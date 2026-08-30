"""Exportação do dataset processado — CSV consolidado, regravado por
completo a cada carga (nunca incrementalmente).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import constants
from .fit import FitContext
from .pipeline import ScoredPipeline
from .repository import Dataset
from .shrinkage import GroupCounts

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


# ---------------------------------------------------------------------------
# Artefatos de análise vendedor x produto / vendedor x setor —
# pipeline-api spec, Requirement "Exportação da análise de carga e fit".
#
# Substituem `analysis_by_product_detailed.csv` e `analysis_by_sector_
# detailed.csv`: os artefatos anteriores calculavam `Taxa Vitória % = Won /
# Total`, com `Total` incluindo `Engaging` e `Prospecting` (159 de 179
# linhas e 219 de 292 linhas incorretas, erro médio 14,89pp — proposal.md).
# Aqui a taxa é sempre `Won / (Won + Lost)`; `Engaging`/`Prospecting`
# aparecem em colunas próprias, informativas, nunca somadas ao denominador
# — nenhuma coluna chamada "Total" existe neste artefato.
#
# Won/Lost vêm de `FitContext.vendor_product`/`vendor_sector`
# (`scoring/fit.py`) — as mesmas contagens que alimentam o fit encolhido
# na API, não uma agregação paralela: "o número exibido = o número
# exportado" (CLAUDE.md).
# ---------------------------------------------------------------------------

ANALYSIS_COLUNAS_BASE = ["Won", "Lost", "Fechados", "Taxa Vitória %", "Engaging", "Prospecting"]


def _open_counts(dataset: Dataset, dimensao_col: str) -> pd.DataFrame:
    aberto = dataset.pipeline[dataset.pipeline["deal_stage"].isin(constants.DEAL_STAGES_ABERTOS)]
    aberto = aberto.dropna(subset=[dimensao_col])
    contagens = (
        aberto.groupby(["sales_agent", dimensao_col, "deal_stage"]).size().unstack("deal_stage", fill_value=0)
    )
    for estagio in ("Engaging", "Prospecting"):
        if estagio not in contagens.columns:
            contagens[estagio] = 0
    return contagens[["Engaging", "Prospecting"]]


def build_analysis_table(
    fit_groups: dict[tuple[str, str], GroupCounts],
    dataset: Dataset,
    dimensao_col: str,
    dimensao_label: str,
) -> pd.DataFrame:
    abertos = _open_counts(dataset, dimensao_col)
    chaves = set(fit_groups) | set(abertos.index)

    linhas: list[dict] = []
    for vendedor, dimensao in sorted(chaves):
        gc = fit_groups.get((vendedor, dimensao))
        won = gc.wins if gc is not None else 0
        fechados = gc.n if gc is not None else 0
        lost = fechados - won
        taxa = round(won / fechados * 100, 2) if fechados > 0 else None
        eng, pros = (
            (int(abertos.loc[(vendedor, dimensao), "Engaging"]), int(abertos.loc[(vendedor, dimensao), "Prospecting"]))
            if (vendedor, dimensao) in abertos.index
            else (0, 0)
        )
        linhas.append(
            {
                "Vendedor": vendedor,
                dimensao_label: dimensao,
                "Won": won,
                "Lost": lost,
                "Fechados": fechados,
                "Taxa Vitória %": taxa,
                "Engaging": eng,
                "Prospecting": pros,
            }
        )
    colunas = ["Vendedor", dimensao_label] + ANALYSIS_COLUNAS_BASE
    return pd.DataFrame(linhas, columns=colunas)


def export_analysis_by_product(dataset: Dataset, fit_ctx: FitContext, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_analysis_table(fit_ctx.vendor_product, dataset, "product", "Produto").to_csv(output_path, index=False)
    return output_path


def export_analysis_by_sector(dataset: Dataset, fit_ctx: FitContext, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_analysis_table(fit_ctx.vendor_sector, dataset, "sector", "Setor").to_csv(output_path, index=False)
    return output_path
