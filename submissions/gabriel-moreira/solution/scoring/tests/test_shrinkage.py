"""Tasks 2.1, 2.2, 2.18 — encolhimento hierárquico e colapso de níveis.

Task 1.4 (add-mult-setor) — `K_PRODUTO` foi removido: o `k` do nível de
produto agora é sempre DERIVADO (`level_stats`), nunca uma constante
congelada. Os testes abaixo passam `k` explicitamente, exatamente como
`pipeline.build_scoring_context` faz em produção.
"""

import math

from scoring import constants
from scoring.shrinkage import (
    GroupCounts,
    account_product_group_counts,
    level_stats,
    p_hat_produto,
    product_group_counts,
    product_sector_group_counts,
)


def _closed(dataset):
    return dataset.pipeline[dataset.pipeline["deal_stage"].isin(constants.DEAL_STAGES_FECHADOS)]


def test_gtk_500_shrinks_toward_global(dataset):
    """`_closed` agora é a população de calibração (7.364 = 6.711 + 653
    reclassificados) — GTK 500 sobe de n=25 para n=35 (design.md, D2). Com
    `k` derivado (≈0,6966, não mais o `K_PRODUTO=4` congelado), o
    encolhimento é mais fraco: p̂_produto ≈ 0,4314, não 0,4436 (lead-scoring
    spec, Scenario "Produto de baixo volume encolhe para o global")."""
    counts = product_group_counts(_closed(dataset))
    assert counts["GTK 500"].n == 35
    produto_stats = level_stats(counts, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    assert not produto_stats.colapsa
    p_hat = p_hat_produto("GTK 500", counts, k=produto_stats.k)
    assert round(p_hat, 4) == 0.4314


def test_mg_special_barely_adjusted_high_volume(dataset):
    counts = product_group_counts(_closed(dataset))
    assert counts["MG Special"].n == 1326
    produto_stats = level_stats(counts, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    p_hat = p_hat_produto("MG Special", counts, k=produto_stats.k)
    assert round(p_hat, 4) == 0.5980


def test_account_product_level_collapses(dataset):
    closed = _closed(dataset)
    groups = account_product_group_counts(closed)
    stats = level_stats(groups, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    assert stats.var_em_excesso <= 0
    assert math.isinf(stats.k)


def test_product_sector_level_collapses(dataset):
    closed = _closed(dataset)
    groups = product_sector_group_counts(closed)
    stats = level_stats(groups, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    assert stats.var_em_excesso <= 0
    assert math.isinf(stats.k)


def test_produto_level_colapsa_quando_variancia_em_excesso_simulada_nao_positiva():
    """Requirement "Probabilidade de ganho por encolhimento hierárquico",
    Scenario "Nível de produto também pode colapsar" — simulado com grupos
    de taxa idêntica (variância observada = 0), não com a calibração real
    (que tem variância em excesso positiva). Sem constante de política a
    sobrepor, `k` infinito colapsa p̂_produto para a taxa global em todos
    os produtos, sem intervenção manual."""
    groups = {
        "A": GroupCounts(n=100, wins=58),
        "B": GroupCounts(n=200, wins=116),
        "C": GroupCounts(n=50, wins=29),
    }
    stats = level_stats(groups, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    assert stats.var_em_excesso <= 0
    assert math.isinf(stats.k)
    for produto in groups:
        p_hat = p_hat_produto(produto, groups, k=stats.k)
        assert p_hat == constants.GLOBAL_WIN_RATE_CALIBRACAO


def test_p_hat_produto_k_infinito_colapsa_sem_produzir_nan():
    """Task 1.3 — `(n*taxa + inf*global) / (n+inf)` é uma indeterminação
    `inf/inf` em ponto flutuante; `p_hat_produto` trata `k=inf`
    explicitamente para retornar a taxa global, não NaN."""
    counts = {"X": GroupCounts(n=10, wins=6)}
    p_hat = p_hat_produto("X", counts, global_win_rate=0.5755, k=math.inf)
    assert p_hat == 0.5755
    assert not math.isnan(p_hat)


def test_p_hat_produto_unaffected_by_removing_collapsed_levels(dataset, ctx):
    """p̂_produto usa só o nível de produto — os níveis colapsados nunca
    contribuem, então removê-los do cálculo (o que já é o caso) não muda
    nada, por construção. `ctx` vem de `build_scoring_context`, que deriva
    o mesmo `k` calculado aqui diretamente."""
    counts = product_group_counts(_closed(dataset))
    produto_stats = level_stats(counts, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    for produto in constants.PRECO_TABELA:
        direct = p_hat_produto(produto, counts, k=produto_stats.k)
        via_ctx = ctx.p_hat_produto(produto)
        assert round(direct, 6) == round(via_ctx, 6)
