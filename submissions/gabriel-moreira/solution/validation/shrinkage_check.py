"""Reprodução do encolhimento hierárquico — Requirement "Reprodução do
encolhimento hierárquico".

Recalcula, para cada nível da hierarquia, a variância observada, a
variância esperada por acaso e o k resultante — usando exatamente a mesma
função (`scoring.shrinkage.level_stats`) que o motor de scoring usa para
derivar `k` do nível de produto em tempo de carga
(`scoring.pipeline.build_scoring_context`). Não há mais uma constante de
política congelada para comparar: `p_hat_por_produto` já é o valor que o
motor de scoring usa, calculado com o mesmo `k` derivado aqui.
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
    p_hat_por_produto: dict[str, float]


def build_report(closed: pd.DataFrame) -> ShrinkageReport:
    prod_counts = product_group_counts(closed)
    ps_counts = product_sector_group_counts(closed)
    ap_counts = account_product_group_counts(closed)

    conta_produto_stats = level_stats(ap_counts, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    produto_setor_stats = level_stats(ps_counts, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    produto_stats = level_stats(prod_counts, constants.GLOBAL_WIN_RATE_CALIBRACAO)

    p_hat_por_produto = {
        produto: p_hat_produto(produto, prod_counts, k=produto_stats.k)
        for produto in constants.PRECO_TABELA
    }

    return ShrinkageReport(
        conta_produto=conta_produto_stats,
        produto_setor=produto_setor_stats,
        produto=produto_stats,
        p_hat_por_produto=p_hat_por_produto,
    )
