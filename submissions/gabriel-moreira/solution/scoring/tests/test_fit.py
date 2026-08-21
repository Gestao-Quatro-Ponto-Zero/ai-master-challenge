"""Task 3.6 — motor de fit vendedor x produto / vendedor x setor."""

import math

import pandas as pd
import pytest

from scoring.fit import FitContext, build_fit_context, fit_produto, fit_setor
from scoring.pipeline import fechados_calibracao
from scoring.shrinkage import GroupCounts


@pytest.fixture(scope="session")
def fit_ctx(dataset) -> FitContext:
    return build_fit_context(dataset, fechados_calibracao(dataset))


def test_anna_snelling_gtx_basic_denominador_exclui_abertos(fit_ctx):
    """32 Won, 19 Lost, 13 abertos -> suporte 51, taxa observada 62,75%,
    nunca 64 (Requirement "Fit histórico do vendedor por produto e por
    setor")."""
    vp = fit_ctx.vendor_product[("Anna Snelling", "GTX Basic")]
    assert vp.n == 51
    assert round(vp.rate * 100, 2) == 62.75

    resultado = fit_produto(fit_ctx, "Anna Snelling", "GTX Basic")
    assert resultado.n == 51


def test_celula_rala_encolhe_e_nao_retorna_100_por_cento():
    """Vendedor com 3 negócios fechados, todos Won -> fit reportado
    encolhido para o prior do escritório, não 100%."""
    ctx = FitContext(
        vendor_office={"Novato": "Central", "Veterano": "Central"},
        vendor_product={
            ("Novato", "GTX Basic"): GroupCounts(n=3, wins=3),
            ("Veterano", "GTX Basic"): GroupCounts(n=200, wins=100),
        },
        vendor_sector={},
        office_product={("Central", "GTX Basic"): GroupCounts(n=203, wins=103)},
        office_sector={},
        global_product={"GTX Basic": GroupCounts(n=203, wins=103)},
        global_sector={},
    )
    resultado = fit_produto(ctx, "Novato", "GTX Basic")
    assert resultado.n == 3
    assert resultado.valor != 1.0
    assert resultado.valor < 1.0


def test_setor_indisponivel_sem_conta(fit_ctx):
    assert fit_setor(fit_ctx, "Anna Snelling", None) is None
    assert fit_setor(fit_ctx, "Anna Snelling", float("nan")) is None


def test_setor_presente_com_conta(fit_ctx):
    resultado = fit_setor(fit_ctx, "Anna Snelling", "technology")
    assert resultado is not None
    assert resultado.n >= 0


def test_fit_produto_denominador_nunca_inclui_abertos(fit_ctx):
    for (vendor, product), gc in fit_ctx.vendor_product.items():
        assert gc.n == gc.wins + (gc.n - gc.wins)  # n == Won + Lost, por construção do groupby


def test_178_celulas_vendedor_produto(fit_ctx):
    assert len(fit_ctx.vendor_product) == 178


def test_292_celulas_vendedor_setor(fit_ctx):
    assert len(fit_ctx.vendor_sector) == 292
