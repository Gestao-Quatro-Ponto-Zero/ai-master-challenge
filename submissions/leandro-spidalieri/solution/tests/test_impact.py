from dataclasses import replace

import pytest

from supportops.impact import BASE, calculate


def test_independent_calculation_and_units():
    s = replace(
        BASE,
        volume=200,
        elegibilidade=0.5,
        cobertura=0.5,
        adesao=0.5,
        antes_min=9,
        depois_min=1,
        revisao_min=1,
        retrabalho_taxa=0.5,
        retrabalho_min=2,
        hora_brl=80,
        ia_mensal_brl=10,
        infra_mensal_brl=5,
        manutencao_mensal_brl=10,
        implantacao_brl=150,
        conversao_caixa=0.5,
    )
    r = calculate(s)
    assert r["processados_mes"] == 25
    assert r["horas_liquidas_mes"] == 2.5
    assert r["valor_capacidade_mes"] == 200
    assert r["custo_recorrente_mes"] == 25
    assert r["caixa_liquido_mes"] == 75
    assert r["payback_meses"] == 2
    assert r["roi_financeiro_12m"] == pytest.approx(750 / 450)


def test_volume_zero_negative_result_and_zero_cost():
    zero = calculate(replace(BASE, volume=0))
    assert zero["horas_liquidas_mes"] == 0
    assert zero["caixa_liquido_mes"] == -150
    assert zero["payback_meses"] is None
    loss = calculate(replace(BASE, antes_min=0, elegibilidade=1, cobertura=1, adesao=1))
    assert loss["horas_liquidas_mes"] < 0
    assert loss["valor_liquido_capacidade_mes"] < 0
    assert loss["payback_meses"] is None
    free = calculate(replace(BASE, manutencao_mensal_brl=0, implantacao_brl=0))
    assert free["roi_financeiro_12m"] is None


@pytest.mark.parametrize(
    "kwargs", [{"cobertura": 1.01}, {"volume": -1}, {"antes_min": float("nan")}]
)
def test_invalid_values_are_rejected(kwargs):
    with pytest.raises(ValueError, match="Premissa"):
        calculate(replace(BASE, **kwargs))
