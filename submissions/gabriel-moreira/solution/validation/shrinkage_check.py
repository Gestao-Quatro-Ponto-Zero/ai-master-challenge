"""Reprodução do encolhimento hierárquico — Requirement "Reprodução do
encolhimento hierárquico".

Recalcula, para cada nível da hierarquia, a variância observada, a
variância esperada por acaso e o k resultante — usando exatamente a mesma
função (`scoring.shrinkage.level_stats`) que o motor de scoring usaria se
computasse esses níveis dinamicamente. O motor de produção usa
`constants.K_PRODUTO` (congelado nesta calibração); este módulo existe para
auditar esse congelamento contra os dados carregados, não para substituí-lo.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from scoring import constants
from scoring.shrinkage import (
    LevelStats,
    account_product_group_counts,
    level_stats,
    p_hat_produto,
    product_group_counts,
    product_sector_group_counts,
)


@dataclass(frozen=True)
class ShrinkageReport:
    conta_produto: LevelStats
    produto_setor: LevelStats
    produto: LevelStats
    p_hat_por_produto_recalculado: dict[str, float]
    p_hat_por_produto_congelado: dict[str, float]


def build_report(closed: pd.DataFrame) -> ShrinkageReport:
    prod_counts = product_group_counts(closed)
    ps_counts = product_sector_group_counts(closed)
    ap_counts = account_product_group_counts(closed)

    conta_produto_stats = level_stats(ap_counts, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    produto_setor_stats = level_stats(ps_counts, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    produto_stats = level_stats(prod_counts, constants.GLOBAL_WIN_RATE_CALIBRACAO)

    p_hat_recalc = {
        produto: p_hat_produto(produto, prod_counts, k=produto_stats.k)
        if produto_stats.k != float("inf")
        else constants.GLOBAL_WIN_RATE_CALIBRACAO
        for produto in constants.PRECO_TABELA
    }
    p_hat_congelado = {
        produto: p_hat_produto(produto, prod_counts) for produto in constants.PRECO_TABELA
    }

    return ShrinkageReport(
        conta_produto=conta_produto_stats,
        produto_setor=produto_setor_stats,
        produto=produto_stats,
        p_hat_por_produto_recalculado=p_hat_recalc,
        p_hat_por_produto_congelado=p_hat_congelado,
    )
