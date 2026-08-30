"""Limitações metodológicas por oportunidade — só o que incide sobre o
score daquele negócio, sempre com o componente que ela move."""

import pytest

from scoring import constants
from scoring.limitacoes import (
    COMPONENTE_CONFIANCA,
    COMPONENTE_P_HAT,
    COMPONENTE_URGENCIA,
    COMPONENTE_VALOR,
    limitacoes_do_score,
)
from scoring.model import ScoringContext

PRODUTO = "GTX Basic"


def _ctx(ages_won=None, product_counts=None):
    """Por padrão: produto com amostra saturada e precedente farto em torno
    de 30 dias — assim cada teste liga só a limitação que quer observar."""
    return ScoringContext(
        p_hat_by_product={PRODUTO: 0.6},
        ages_won_ordenadas=sorted(ages_won if ages_won is not None else [30.0] * 100),
        product_closed_counts=product_counts or {PRODUTO: 500},
    )


def _ids(limitacoes):
    return [limitacao.id for limitacao in limitacoes]


def _por_id(limitacoes, limitacao_id):
    return next(limitacao for limitacao in limitacoes if limitacao.id == limitacao_id)


def test_caso_sem_ressalva_ainda_declara_o_que_o_score_e():
    """Um negócio completo, jovem, com conta e produto de amostra farta não
    tem ressalva nenhuma — exceto a que define o número, que é justamente a
    leitura errada mais provável de quem vê um SCORE alto."""
    limitacoes = limitacoes_do_score(
        _ctx(), product=PRODUTO, stage="Engaging", age_days=30.0, has_account=True, porte="Mid"
    )

    assert _ids(limitacoes) == ["score_nao_e_probabilidade"]


def test_prospecting_nomeia_urgencia_fixa_e_o_que_ela_apaga():
    limitacoes = limitacoes_do_score(
        _ctx(), product=PRODUTO, stage="Prospecting", age_days=None, has_account=True, porte="Mid"
    )

    sem_idade = _por_id(limitacoes, "sem_idade")
    assert COMPONENTE_URGENCIA in sem_idade.componentes
    assert f"{constants.PROSPECTING_URGENCIA:.2f}".replace(".", ",") in sem_idade.impacto
    # Prospecting é "idade desconhecida", nunca "sem precedente".
    assert "sem_precedente" not in _ids(limitacoes)


def test_idade_acima_da_censura_avisa_que_o_score_para_de_reagir():
    idade = constants.CENSURA_DIAS + 20
    limitacoes = limitacoes_do_score(
        _ctx(), product=PRODUTO, stage="Engaging", age_days=float(idade), has_account=True, porte="Mid"
    )

    censura = _por_id(limitacoes, "acima_da_censura")
    assert set(censura.componentes) == {COMPONENTE_P_HAT, COMPONENTE_URGENCIA}
    assert f"{constants.CENSURA_URGENCIA:.2f}".replace(".", ",") in censura.impacto
    assert "curva_congelada" not in _ids(limitacoes), "censura e congelamento se excluem"


def test_idade_na_faixa_congelada_avisa_que_a_idade_deixou_de_diferenciar():
    idade = float(constants.CURVA_LIMITE_CONFIAVEL_DIAS + 5)
    limitacoes = limitacoes_do_score(
        _ctx(ages_won=[idade] * 100),
        product=PRODUTO, stage="Engaging", age_days=idade, has_account=True, porte="Mid",
    )

    congelada = _por_id(limitacoes, "curva_congelada")
    assert str(constants.CURVA_LIMITE_CONFIAVEL_DIAS) in congelada.titulo
    assert str(constants.CENSURA_DIAS) in congelada.impacto


def test_sem_precedente_aparece_quando_nenhuma_vitoria_cerca_a_idade():
    limitacoes = limitacoes_do_score(
        _ctx(ages_won=[5.0] * 100),
        product=PRODUTO, stage="Engaging", age_days=100.0, has_account=True, porte="Mid",
    )

    sem_precedente = _por_id(limitacoes, "sem_precedente")
    assert COMPONENTE_CONFIANCA in sem_precedente.componentes
    assert "Revisão em lote" in sem_precedente.impacto


def test_sem_conta_explica_o_multiplicador_neutro_no_valor():
    limitacoes = limitacoes_do_score(
        _ctx(), product=PRODUTO, stage="Engaging", age_days=30.0, has_account=False, porte=None
    )

    porte = _por_id(limitacoes, "porte_desconhecido")
    assert COMPONENTE_VALOR in porte.componentes
    assert f"{constants.MULT_PORTE_DESCONHECIDO:.2f}".replace(".", ",") in porte.impacto


def test_conta_sem_funcionarios_tambem_cai_no_porte_neutro_com_outra_origem():
    com_conta = _por_id(
        limitacoes_do_score(
            _ctx(), product=PRODUTO, stage="Engaging", age_days=30.0, has_account=True, porte=None
        ),
        "porte_desconhecido",
    )
    sem_conta = _por_id(
        limitacoes_do_score(
            _ctx(), product=PRODUTO, stage="Engaging", age_days=30.0, has_account=False, porte=None
        ),
        "porte_desconhecido",
    )

    # Mesmo efeito no VALOR, causas diferentes — e a ação para corrigir é
    # diferente em cada caso, então o título não pode ser o mesmo.
    assert com_conta.impacto == sem_conta.impacto
    assert com_conta.titulo != sem_conta.titulo


def test_produto_com_amostra_pequena_avisa_que_p_hat_e_do_catalogo():
    limitacoes = limitacoes_do_score(
        _ctx(product_counts={PRODUTO: 35}),
        product=PRODUTO, stage="Engaging", age_days=30.0, has_account=True, porte="Mid",
    )

    amostra = _por_id(limitacoes, "amostra_do_produto")
    assert "35" in amostra.titulo
    assert str(constants.SUPORTE_SATURACAO_N) in amostra.titulo


@pytest.mark.parametrize(
    "stage,age_days,has_account,porte",
    [
        ("Engaging", 30.0, True, "Mid"),
        ("Prospecting", None, False, None),
        ("Engaging", 200.0, False, None),
        ("Engaging", 130.0, True, "SMB"),
    ],
)
def test_toda_limitacao_nomeia_componente_e_impacto(stage, age_days, has_account, porte):
    limitacoes = limitacoes_do_score(
        _ctx(product_counts={PRODUTO: 35}),
        product=PRODUTO, stage=stage, age_days=age_days, has_account=has_account, porte=porte,
    )

    assert limitacoes
    for limitacao in limitacoes:
        assert limitacao.componentes, "limitação sem componente afetado não tem onde ser exibida"
        assert limitacao.rotulo_curto and len(limitacao.rotulo_curto) <= 20
        assert limitacao.titulo.strip()
        # Sem o impacto concreto, a limitação vira decoração: o leitor a lê
        # e continua usando o número exatamente como antes.
        assert limitacao.impacto.strip()
    assert len({limitacao.id for limitacao in limitacoes}) == len(limitacoes)
