"""Requirement "Explicabilidade do score e plano de ação"."""

from scoring.explicacao import fracao_vitorias_ate, plano_de_acao
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
