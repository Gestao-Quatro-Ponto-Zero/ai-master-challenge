"""Reprodução do impacto da reclassificação de 200 dias — Requirement
"Reprodução do impacto da reclassificação de 200 dias".

Reporta, lado a lado, contagem reclassificada, tamanho do funil aberto,
base rate global e taxa de vitória por produto — antes (população
orgânica) e depois (população de calibração) da reclassificação — e
destaca produtos cuja variação é dominada por amostra pequena.
"""

from __future__ import annotations

from dataclasses import dataclass

from scoring import constants
from scoring.repository import Dataset
from scoring.shrinkage import product_group_counts

# Abaixo deste `n` de negócios fechados na população de calibração, a
# variação de taxa do produto é dominada por amostra pequena — separa
# limpo GTK 500 (n=35) do restante do catálogo (n >= 824).
AMOSTRA_PEQUENA_N_MAXIMO = 100


@dataclass(frozen=True)
class ProdutoVariacao:
    produto: str
    n_antes: int
    n_depois: int
    taxa_antes: float
    taxa_depois: float
    variacao_pp: float
    amostra_pequena: bool


@dataclass(frozen=True)
class ReclassificationReport:
    n_reclassificados: int
    funil_antes: int
    funil_depois: int
    base_rate_antes: float
    base_rate_depois: float
    produtos: list[ProdutoVariacao]


def build_report(dataset: Dataset) -> ReclassificationReport:
    pipeline = dataset.pipeline
    fechado = pipeline["deal_stage"].isin(constants.DEAL_STAGES_FECHADOS)
    organico = pipeline[fechado & ~pipeline["reclassificado"]]
    calibracao = pipeline[fechado]

    n_reclass = int(pipeline["reclassificado"].sum())
    funil_depois = int(pipeline["deal_stage"].isin(constants.DEAL_STAGES_ABERTOS).sum())
    funil_antes = funil_depois + n_reclass

    base_antes = float((organico["deal_stage"] == "Won").mean())
    base_depois = float((calibracao["deal_stage"] == "Won").mean())

    counts_antes = product_group_counts(organico)
    counts_depois = product_group_counts(calibracao)

    produtos = []
    for produto in constants.PRECO_TABELA:
        antes = counts_antes.get(produto)
        depois = counts_depois.get(produto)
        n_antes = antes.n if antes else 0
        n_depois = depois.n if depois else 0
        taxa_antes = antes.rate if antes else 0.0
        taxa_depois = depois.rate if depois else 0.0
        produtos.append(
            ProdutoVariacao(
                produto=produto,
                n_antes=n_antes,
                n_depois=n_depois,
                taxa_antes=taxa_antes,
                taxa_depois=taxa_depois,
                variacao_pp=(taxa_depois - taxa_antes) * 100,
                amostra_pequena=n_depois <= AMOSTRA_PEQUENA_N_MAXIMO,
            )
        )

    return ReclassificationReport(
        n_reclassificados=n_reclass,
        funil_antes=funil_antes,
        funil_depois=funil_depois,
        base_rate_antes=base_antes,
        base_rate_depois=base_depois,
        produtos=produtos,
    )
