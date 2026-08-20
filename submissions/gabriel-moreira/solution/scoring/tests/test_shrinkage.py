"""Tasks 2.1, 2.2, 2.18 — encolhimento hierárquico e colapso de níveis."""

import math

from scoring import constants
from scoring.shrinkage import (
    account_product_group_counts,
    level_stats,
    p_hat_produto,
    product_group_counts,
    product_sector_group_counts,
)


def _closed(dataset):
    return dataset.pipeline[dataset.pipeline["deal_stage"].isin(constants.DEAL_STAGES_FECHADOS)]


def test_gtk_500_shrinks_toward_global(dataset):
    counts = product_group_counts(_closed(dataset))
    assert counts["GTK 500"].n == 25
    p_hat = p_hat_produto("GTK 500", counts)
    assert round(p_hat, 3) == 0.604


def test_mg_special_barely_adjusted_high_volume(dataset):
    counts = product_group_counts(_closed(dataset))
    assert counts["MG Special"].n == 1223
    p_hat = p_hat_produto("MG Special", counts)
    assert round(p_hat, 3) == 0.648


def test_account_product_level_collapses(dataset):
    closed = _closed(dataset)
    groups = account_product_group_counts(closed)
    stats = level_stats(groups, constants.GLOBAL_WIN_RATE)
    assert stats.var_em_excesso <= 0
    assert math.isinf(stats.k)


def test_product_sector_level_collapses(dataset):
    closed = _closed(dataset)
    groups = product_sector_group_counts(closed)
    stats = level_stats(groups, constants.GLOBAL_WIN_RATE)
    assert stats.var_em_excesso <= 0
    assert math.isinf(stats.k)


def test_p_hat_produto_unaffected_by_removing_collapsed_levels(dataset, ctx):
    """p̂_produto usa só o nível de produto — os níveis colapsados nunca
    contribuem, então removê-los do cálculo (o que já é o caso) não muda
    nada, por construção."""
    counts = product_group_counts(_closed(dataset))
    for produto in constants.PRECO_TABELA:
        direct = p_hat_produto(produto, counts)
        via_ctx = ctx.p_hat_produto(produto)
        assert round(direct, 6) == round(via_ctx, 6)
