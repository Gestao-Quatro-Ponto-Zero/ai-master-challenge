"""Requirement "Explicabilidade do score e plano de ação"."""

from scoring import constants
from scoring.explicacao import fracao_vitorias_ate, plano_de_acao, plano_de_acao_passos
from scoring.model import Componentes


def test_fracao_vitorias_ate_is_percentage():
    ages = [10.0, 20.0, 30.0, 40.0]
    assert fracao_vitorias_ate(ages, 30.0) == 75.0
    assert fracao_vitorias_ate(ages, 100.0) == 100.0
    assert fracao_vitorias_ate(ages, 0.0) == 0.0


def test_plano_de_acao_desistir_recommends_batch_review():
    componentes = Componentes(p_hat=0.632, valor=1000.0, urgencia=0.15, prioridade=94.8)
    texto = plano_de_acao(
        "desistir", "Engaging", has_account=True, age_days=200,
        confianca_nivel="D", componentes=componentes,
    )
    assert "revisão em lote" in texto
    assert "precedente histórico" in texto


def test_plano_de_acao_qualificar_recommends_enrichment():
    componentes = Componentes(p_hat=0.637, valor=550.0, urgencia=0.47, prioridade=164.71)
    texto = plano_de_acao(
        "qualificar", "Prospecting", has_account=False, age_days=None,
        confianca_nivel="C", componentes=componentes,
    )
    assert "enriqueça o cadastro" in texto.lower() or "cadastro" in texto.lower()


def test_plano_de_acao_foco_urgente_mentions_fraction_of_wins():
    componentes = Componentes(p_hat=0.764, valor=5865.74, urgencia=1.0, prioridade=4482.0)
    texto = plano_de_acao(
        "foco_urgente", "Engaging", has_account=True, age_days=122,
        confianca_nivel="A", componentes=componentes,
        ages_won_ordenadas=[10.0, 50.0, 100.0, 130.0],
    )
    assert "%" in texto
    assert "priorize contato" in texto.lower()


def _todos_estados_variacoes():
    for estado_key in constants.ESTADOS:
        for has_account in (True, False):
            for age_days in (None, 30.0, 200.0):
                yield estado_key, has_account, age_days


def test_plano_de_acao_passos_quantidade_dentro_do_limite():
    for estado_key, has_account, age_days in _todos_estados_variacoes():
        passos = plano_de_acao_passos(estado_key, has_account, age_days)
        assert 2 <= len(passos) <= 4


def test_plano_de_acao_passos_enriquecimento_apenas_sem_conta():
    for estado_key in constants.ESTADOS:
        com_conta = plano_de_acao_passos(estado_key, has_account=True, age_days=None)
        sem_conta = plano_de_acao_passos(estado_key, has_account=False, age_days=None)
        assert not any("enriqueça o cadastro" in p.lower() for p in com_conta)
        assert any("enriqueça o cadastro" in p.lower() for p in sem_conta)
        assert sem_conta[0].lower().startswith("enriqueça o cadastro")


def test_plano_de_acao_passos_revisao_em_lote_apenas_se_censurado():
    for estado_key in constants.ESTADOS:
        nao_censurado = plano_de_acao_passos(estado_key, has_account=True, age_days=30.0)
        censurado = plano_de_acao_passos(estado_key, has_account=True, age_days=200.0)
        assert not any("lote de revisão" in p.lower() for p in nao_censurado)
        assert "lote de revisão" in censurado[-1].lower()


def test_plano_de_acao_passos_determinismo():
    for estado_key, has_account, age_days in _todos_estados_variacoes():
        primeira = plano_de_acao_passos(estado_key, has_account, age_days)
        segunda = plano_de_acao_passos(estado_key, has_account, age_days)
        assert primeira == segunda


def test_plano_de_acao_passos_sem_separador_do_csv(scored_pipeline):
    for passos in scored_pipeline.scored["plano_de_acao_passos"]:
        for passo in passos:
            assert "|" not in passo
