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


def test_gtk_500_colapsa_para_a_taxa_global(dataset):
    """GTK 500 tem 25 negócios fechados com desfecho observado. O nível de
    produto inteiro colapsa (k = ∞), então ele recebe a taxa global — o
    encolhimento máximo, que é a resposta certa para o produto de menor
    amostra do catálogo.

    Chegou a receber p̂ = 0,4314 (n=35) entre 2026-08-21 e 2026-08-29: 10
    daquelas 35 "perdas" eram atribuídas pelo expurgo de 200 dias, e eram
    elas que faziam o nível deixar de colapsar."""
    counts = product_group_counts(_closed(dataset))
    assert counts["GTK 500"].n == 25
    produto_stats = level_stats(counts, constants.GLOBAL_WIN_RATE)
    assert produto_stats.colapsa
    p_hat = p_hat_produto("GTK 500", counts, k=produto_stats.k)
    assert p_hat == constants.GLOBAL_WIN_RATE


def test_mg_special_barely_adjusted_high_volume(dataset):
    """Mesmo o produto de maior volume recebe a taxa global: com o nível
    colapsado, volume não compra taxa própria. É a tradução em código do
    achado de que produto não prevê ganho/perda."""
    counts = product_group_counts(_closed(dataset))
    assert counts["MG Special"].n == 1223
    produto_stats = level_stats(counts, constants.GLOBAL_WIN_RATE)
    p_hat = p_hat_produto("MG Special", counts, k=produto_stats.k)
    assert p_hat == constants.GLOBAL_WIN_RATE


def test_product_level_collapses(dataset):
    """O nível de produto colapsa sobre desfecho observado — variância
    entre produtos menor que o ruído amostral esperado."""
    counts = product_group_counts(_closed(dataset))
    stats = level_stats(counts, constants.GLOBAL_WIN_RATE)
    assert stats.var_em_excesso <= 0
    assert math.isinf(stats.k)


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
    stats = level_stats(groups, constants.GLOBAL_WIN_RATE)
    assert stats.var_em_excesso <= 0
    assert math.isinf(stats.k)
    for produto in groups:
        p_hat = p_hat_produto(produto, groups, k=stats.k)
        assert p_hat == constants.GLOBAL_WIN_RATE


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
    produto_stats = level_stats(counts, constants.GLOBAL_WIN_RATE)
    for produto in constants.PRECO_TABELA:
        direct = p_hat_produto(produto, counts, k=produto_stats.k)
        via_ctx = ctx.p_hat_produto(produto)
        assert round(direct, 6) == round(via_ctx, 6)
