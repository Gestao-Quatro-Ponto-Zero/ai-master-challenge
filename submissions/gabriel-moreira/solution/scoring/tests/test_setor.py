"""Task 2.4 — `mult_setor(produto, setor)`, lead-scoring spec, Requirement
"Ajuste de desempenho produto×setor sobre p̂".

O nível produto×setor tem variância em excesso <= 0 nos dados calibrados e
colapsa (k=∞ — ver `tests/test_shrinkage.py::test_product_sector_level_collapses`):
a resposta estatisticamente correta seria mult_setor ≡ 1,000 para todas as
células. `K_SETOR=25` é uma constante de POLÍTICA que sobrepõe esse
colapso deliberadamente, exatamente como `K_FIT=25` sobrepõe o colapso
análogo de vendedor×produto/vendedor×setor (`scoring/fit.py`,
`tests/test_fit.py`) — os testes abaixo verificam o comportamento
resultante dessa política, não um resultado estatístico "correto".
"""

import math

import pytest

from scoring import constants
from scoring.setor import MultSetorContext, mult_setor, n_celula, setor_desconhecido
from scoring.shrinkage import GroupCounts, level_stats, product_sector_group_counts


def test_setor_desconhecido_none_e_nan():
    assert setor_desconhecido(None) is True
    assert setor_desconhecido(float("nan")) is True
    assert setor_desconhecido("technology") is False


def test_setor_desconhecido_e_neutro():
    """Requirement "Ajuste de desempenho produto×setor sobre p̂", Scenario
    "Setor desconhecido é neutro"."""
    ctx = MultSetorContext(
        cell_counts={("GTX Pro", "technology"): GroupCounts(n=120, wins=82)},
        p_hat_by_product={"GTX Pro": 0.60},
    )
    assert mult_setor(ctx, "GTX Pro", None) == 1.0
    assert mult_setor(ctx, "GTX Pro", float("nan")) == 1.0


def test_celula_ausente_e_neutra():
    """Célula sem nenhum negócio fechado (produto×setor nunca observado
    juntos na calibração) -> neutro, nunca inventado."""
    ctx = MultSetorContext(cell_counts={}, p_hat_by_product={"GTX Pro": 0.60})
    assert mult_setor(ctx, "GTX Pro", "aerospace") == 1.0


def test_celula_grande_acima_da_media_dentro_do_clip():
    """Requirement "Ajuste de desempenho produto×setor sobre p̂", Scenario
    "Célula com desempenho acima da média do produto" — célula grande com
    taxa bruta acima de p̂_produto: n=100, taxa=0,68, p̂_produto=0,60 ->
    taxa_encolhida=(100×0,68+25×0,60)/125=0,664, mult_setor≈1,107, dentro
    do limite de 1,15."""
    ctx = MultSetorContext(
        cell_counts={("GTX Pro", "technology"): GroupCounts(n=100, wins=68)},
        p_hat_by_product={"GTX Pro": 0.60},
    )
    valor = mult_setor(ctx, "GTX Pro", "technology")
    assert round(valor, 3) == 1.107
    assert valor < constants.MULT_SETOR_MAX


def test_celula_infima_e_puxada_quase_inteiramente_para_1():
    """Requirement "Ajuste de desempenho produto×setor sobre p̂", Scenario
    "Célula com amostra ínfima não domina o resultado": n=2, ambos ganhos
    (taxa bruta 1,0), p̂_produto=0,60 ->
    taxa_encolhida=(2×1,0+25×0,60)/27≈0,6222, mult_setor≈1,049 — a amostra
    de 2 negócios pesa pouco frente a K_SETOR=25, bem mais perto de 1,0 do
    que o mult≈1,107 da célula de 100 negócios acima."""
    ctx = MultSetorContext(
        cell_counts={("GTX Pro", "technology"): GroupCounts(n=2, wins=2)},
        p_hat_by_product={"GTX Pro": 0.60},
    )
    valor = mult_setor(ctx, "GTX Pro", "technology")
    assert round(valor, 3) == 1.049
    assert valor < 1.06  # puxado quase inteiramente para 1,0 pelo encolhimento


def test_teto_do_clip_e_aplicado_no_limite_superior():
    """Requirement "Ajuste de desempenho produto×setor sobre p̂", Scenario
    "Teto de variação aplicado" — célula que produziria mult_setor > 1,15
    sem o teto é limitada exatamente a 1,15."""
    # taxa bruta 1,0 (todos ganhos), n grande o bastante para dominar o
    # encolhimento e ultrapassar o teto sem o clip.
    ctx = MultSetorContext(
        cell_counts={("GTX Pro", "technology"): GroupCounts(n=500, wins=500)},
        p_hat_by_product={"GTX Pro": 0.60},
    )
    valor = mult_setor(ctx, "GTX Pro", "technology")
    assert valor == constants.MULT_SETOR_MAX
    assert valor == 1.15


def test_teto_do_clip_e_aplicado_no_limite_inferior():
    ctx = MultSetorContext(
        cell_counts={("GTX Pro", "technology"): GroupCounts(n=500, wins=0)},
        p_hat_by_product={"GTX Pro": 0.60},
    )
    valor = mult_setor(ctx, "GTX Pro", "technology")
    assert valor == constants.MULT_SETOR_MIN
    assert valor == 0.85


def test_n_celula_reflete_o_tamanho_amostral():
    ctx = MultSetorContext(
        cell_counts={("GTX Pro", "technology"): GroupCounts(n=120, wins=82)},
        p_hat_by_product={"GTX Pro": 0.60},
    )
    assert n_celula(ctx, "GTX Pro", "technology") == 120
    assert n_celula(ctx, "GTX Pro", "retail") == 0  # célula ausente
    assert n_celula(ctx, "GTX Pro", None) == 0  # setor desconhecido


def test_produto_sector_level_colapsa_sobre_dados_reais(dataset):
    """Documenta, sobre os dados reais de calibração, que o nível
    produto×setor colapsa (k=∞) — a mesma verificação de
    `test_shrinkage.py::test_product_sector_level_collapses`, repetida
    aqui para deixar explícito que `K_SETOR` é uma constante de política
    sobre um nível que colapsa, não um resultado que o encolhimento
    natural produziria (análogo à ressalva já registrada para `K_FIT` em
    `constants.py`)."""
    from scoring.pipeline import fechados_calibracao

    closed = fechados_calibracao(dataset)
    groups = product_sector_group_counts(closed)
    stats = level_stats(groups, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    assert stats.var_em_excesso <= 0
    assert math.isinf(stats.k)


def test_mult_setor_determinismo():
    ctx = MultSetorContext(
        cell_counts={("GTX Pro", "technology"): GroupCounts(n=120, wins=82)},
        p_hat_by_product={"GTX Pro": 0.60},
    )
    assert mult_setor(ctx, "GTX Pro", "technology") == mult_setor(ctx, "GTX Pro", "technology")
