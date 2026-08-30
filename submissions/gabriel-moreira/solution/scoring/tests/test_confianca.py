"""Requirement "Atribuição de confiança" — CONFIANÇA = min(completude, suporte)."""

import pytest

from scoring.confianca import completude, confianca, metade_governante, razao_confianca, sem_precedente, suporte
from scoring.model import ScoringContext


def _ctx(ages_won=None, product_counts=None, p_hat_by_product=None):
    return ScoringContext(
        p_hat_by_product=p_hat_by_product or {},
        ages_won_ordenadas=sorted(ages_won or []),
        product_closed_counts=product_counts or {},
    )


def test_completude_todos_os_campos_observados():
    valor, ausentes = completude(
        stage="Engaging", has_account=True, has_employees=True, has_sector=True, has_team=True
    )
    assert valor == 100.0
    assert ausentes == []


def test_completude_informacao_parcial():
    valor, ausentes = completude(
        stage="Engaging", has_account=True, has_employees=False, has_sector=False, has_team=True
    )
    assert valor == 60.0
    assert set(ausentes) == {"funcionários", "setor"}


def test_completude_informacao_minima():
    valor, ausentes = completude(
        stage="Prospecting", has_account=False, has_employees=False, has_sector=False, has_team=True
    )
    assert valor == 20.0
    assert set(ausentes) == {"engajamento", "conta", "funcionários", "setor"}


def test_confianca_maxima_com_precedente_denso():
    """Requirement "Atribuição de confiança", Scenario "Confiança máxima" —
    os dois termos de suporte saturados (idade e produto)."""
    ctx = _ctx(ages_won=[95.0] * 60, product_counts={"GTX Basic": 200})
    completude_valor, _ = completude(
        stage="Engaging", has_account=True, has_employees=True, has_sector=True, has_team=True
    )
    suporte_valor = suporte(ctx, "GTX Basic", age_days=100.0)
    assert completude_valor == 100.0
    assert suporte_valor == 100.0
    assert confianca(completude_valor, suporte_valor) == 100.0


def test_cadastro_completo_sem_precedente_historico():
    """Sem nenhum negócio ganho nesta faixa de idade: s_idade = 0 e o
    suporte cai proporcionalmente ao peso da idade —
    100 × (0,65×0 + 0,20×1) / (0,65+0,20) = 23,5."""
    ctx = _ctx(ages_won=[], product_counts={"GTX Basic": 200})
    completude_valor, _ = completude(
        stage="Engaging", has_account=True, has_employees=True, has_sector=True, has_team=True
    )
    suporte_valor = suporte(ctx, "GTX Basic", age_days=200.0)
    assert completude_valor == 100.0
    assert suporte_valor == 23.5
    assert confianca(completude_valor, suporte_valor) == 23.5
    assert metade_governante(completude_valor, suporte_valor) == "suporte"
    assert sem_precedente(ctx, 200.0) is True


def test_prospecting_nao_cobrada_duas_vezes_pela_idade_ausente():
    """Requirement "Atribuição de confiança", Scenario "Prospecting não é
    cobrada duas vezes pela idade ausente" — o termo de idade é omitido
    (não zerado), e suporte usa só o termo de produto."""
    ctx = _ctx(ages_won=[], product_counts={"GTX Basic": 200})
    completude_valor, ausentes = completude(
        stage="Prospecting", has_account=True, has_employees=True, has_sector=True, has_team=True
    )
    suporte_valor = suporte(ctx, "GTX Basic", age_days=None)
    assert completude_valor == 80.0  # falta só engajamento
    assert ausentes == ["engajamento"]
    # sem idade: suporte usa só o termo de produto (s_produto=1) -> 100, não 0
    assert suporte_valor == 100.0
    assert sem_precedente(ctx, None) is False


def test_suporte_nao_tem_termo_de_setor():
    """O termo s_célula (produto×setor) saiu de suporte junto com
    `mult_setor` (2026-08-29): `suporte` não aceita mais setor como
    insumo, e duas oportunidades idênticas em produto e idade têm o mesmo
    suporte, com ou sem setor no cadastro. A ausência de setor continua
    sendo cobrada — uma vez só, em completude."""
    import inspect

    assert "sector" not in inspect.signature(suporte).parameters
    ctx = _ctx(ages_won=[100.0] * 60, product_counts={"GTX Basic": 200})
    assert suporte(ctx, "GTX Basic", age_days=100.0) == 100.0


def test_produto_com_historico_raso_limita_suporte():
    ctx = _ctx(ages_won=[100.0] * 60, product_counts={"GTK 500": 25})
    suporte_valor = suporte(ctx, "GTK 500", age_days=100.0)
    # s_idade=1 (60>=50), s_produto=25/50=0.5
    # suporte = 100*(0.65*1+0.20*0.5)/(0.65+0.20) = 88.2
    assert suporte_valor == 88.2


def test_as_duas_metades_sao_expostas_e_identificaveis():
    completude_valor = 60.0
    suporte_valor = 20.0
    assert confianca(completude_valor, suporte_valor) == 20.0
    assert metade_governante(completude_valor, suporte_valor) == "suporte"


def test_confianca_nao_considera_idade_diretamente():
    """Mesma completude e mesma densidade de precedente relativa -> mesma
    CONFIANÇA, mesmo com idades diferentes — idade só entra via s_idade."""
    ctx = _ctx(ages_won=[50.0] * 60 + [100.0] * 60, product_counts={"GTX Basic": 200})
    completude_valor, _ = completude(
        stage="Engaging", has_account=True, has_employees=True, has_sector=True, has_team=True
    )
    s1 = suporte(ctx, "GTX Basic", age_days=50.0)
    s2 = suporte(ctx, "GTX Basic", age_days=100.0)
    assert confianca(completude_valor, s1) == confianca(completude_valor, s2) == 100.0


def test_razao_confianca_nomeia_campos_ausentes():
    texto = razao_confianca(40.0, ["conta", "setor", "funcionários"], 100.0, sem_precedente_flag=False)
    assert "conta" in texto and "setor" in texto and "funcionários" in texto


def test_razao_confianca_sem_precedente():
    texto = razao_confianca(100.0, [], 25.0, sem_precedente_flag=True)
    assert "precedente" in texto


def test_razao_confianca_nao_menciona_probabilidade():
    termos_proibidos = ("chance", "probabilidade", "provável", "provavel")
    textos = [
        razao_confianca(40.0, ["conta"], 100.0, sem_precedente_flag=False),
        razao_confianca(100.0, [], 25.0, sem_precedente_flag=True),
        razao_confianca(100.0, [], 100.0, sem_precedente_flag=False),
    ]
    for texto in textos:
        texto_lower = texto.lower()
        for termo in termos_proibidos:
            assert termo not in texto_lower


@pytest.mark.parametrize(
    "completude_valor,suporte_valor,esperado",
    [(50.0, 50.0, "empate"), (30.0, 70.0, "completude"), (70.0, 30.0, "suporte")],
)
def test_metade_governante(completude_valor, suporte_valor, esperado):
    assert metade_governante(completude_valor, suporte_valor) == esperado
