"""Tasks 2.4-2.8, 2.15, 2.20 — componentes, censura, Prospecting, exemplos
de referência dos specs."""

from scoring import constants
from scoring.model import mult_porte, prioridade, urgencia, valor, preco_tabela
from scoring.model import p_hat as p_hat_fn


def test_gtx_plus_pro_upper_porte_valor():
    assert valor("GTX Plus Pro", "Upper") == 5865.74


def test_valor_unknown_account_uses_neutral_prior():
    with_account = valor("GTX Plus Pro", "Upper")
    without_account = valor("GTX Plus Pro", None)
    assert without_account == 5482.00
    assert abs(with_account - without_account) / with_account <= 0.08


def test_censorship_reverts_to_prior_not_extrapolation(ctx):
    p_hat_value = p_hat_fn(ctx, "GTX Plus Pro", "Engaging", age_days=377)
    urgencia_value = urgencia("Engaging", age_days=377)
    # Censura reverte à taxa ORGÂNICA (0,632) — não à taxa de calibração
    # (0,5755), que só alimenta p̂_produto (lead-scoring spec, Requirement
    # "Censura acima de 138 dias").
    assert p_hat_value == constants.GLOBAL_WIN_RATE_ORGANICO
    assert urgencia_value == 0.15
    # nunca o valor mais alto da curva (0,751), que premiaria o abandono.
    assert p_hat_value != 0.751


def test_prospecting_gets_full_priority_without_imputed_age(ctx):
    p_hat_value = p_hat_fn(ctx, "GTX Basic", "Prospecting", age_days=None)
    urgencia_value = urgencia("Prospecting", age_days=None)
    assert round(p_hat_value, 3) == 0.577
    assert urgencia_value == constants.PROSPECTING_URGENCIA


def test_prioridade_rounds_to_cents():
    assert prioridade(0.5, 100.001, 1.0) == 50.00


def test_decomposition_sums_to_priority(ctx):
    p = p_hat_fn(ctx, "GTX Plus Pro", "Engaging", age_days=122)
    v = valor("GTX Plus Pro", "Upper")
    u = urgencia("Engaging", age_days=122)
    assert prioridade(p, v, u) == round(p * v * u, 2)


def test_mult_porte_ranges():
    assert mult_porte("SMB") == 0.95
    assert mult_porte("Mid") == 0.91
    assert mult_porte("Upper") == 1.07
    assert mult_porte("Enterprise") == 1.06
    assert mult_porte(None) == 1.00
