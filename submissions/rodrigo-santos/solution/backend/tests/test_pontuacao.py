"""Testes do score e das explicações."""

from app import config
from app.servicos.estatisticas import calcular_estatisticas
from app.servicos.pontuacao import (
    PRIORIDADE_BAIXA,
    SITUACAO_ATIVO,
    SITUACAO_PARADO,
    SITUACAO_PROSPECCAO,
    explicar_deal,
    explicar_partes,
    pontuar_deals_abertos,
    sugerir_acao,
)


def test_pontua_apenas_deals_abertos():
    deals = pontuar_deals_abertos()
    assert len(deals) == 2089
    assert set(deals["deal_stage"]) == {"Prospecting", "Engaging"}


def test_score_entre_0_e_100_e_ordenado():
    scores = pontuar_deals_abertos()["score"]
    assert scores.between(0, 100).all()
    assert scores.is_monotonic_decreasing


def test_pontos_maximos_somam_100():
    assert sum(config.PONTOS_MAXIMOS.values()) == 100


def test_score_e_a_soma_dos_pontos_das_partes():
    for _, deal in pontuar_deals_abertos().sample(200, random_state=1).iterrows():
        partes = explicar_partes(deal)
        assert sum(p.pontos for p in partes) == deal["score"]
        assert all(0 <= p.pontos <= p.maximo for p in partes)


def test_limite_e_o_negocio_mais_longo_do_historico():
    # Nenhum negócio fechado (ganho ou perdido) ficou aberto mais de 138 dias.
    assert calcular_estatisticas().limite_dias == 138


def test_situacao_de_cada_negocio():
    estat = calcular_estatisticas()
    deals = pontuar_deals_abertos()
    prospeccao = deals[deals["deal_stage"] == "Prospecting"]
    em_negociacao = deals[deals["deal_stage"] == "Engaging"]

    assert (prospeccao["situacao"] == SITUACAO_PROSPECCAO).all()
    assert (em_negociacao[em_negociacao["dias_aberto"] > estat.limite_dias]["situacao"] == SITUACAO_PARADO).all()
    assert (em_negociacao[em_negociacao["dias_aberto"] <= estat.limite_dias]["situacao"] == SITUACAO_ATIVO).all()


def test_parado_e_sempre_baixa_e_nao_conta_no_valor_esperado():
    parados = pontuar_deals_abertos().query("parado")
    assert not parados.empty
    assert (parados["prioridade"] == PRIORIDADE_BAIXA).all()
    assert (parados["valor_esperado"] == 0).all()
    assert (parados["pontos_situacao"] == 0).all()


def test_parado_recebe_sugestao_de_atualizar_ou_encerrar():
    deal = pontuar_deals_abertos().query("parado").iloc[0]
    assert sugerir_acao(deal).startswith("Atualize ou encerre")


def test_todo_deal_tem_motivos_sugestao_e_motivo_principal():
    deals = pontuar_deals_abertos()
    assert deals["motivo_principal"].str.len().gt(0).all()
    for _, deal in deals.sample(100, random_state=2).iterrows():
        assert explicar_deal(deal), deal["opportunity_id"]
        assert sugerir_acao(deal)


def test_motivo_principal_de_prioridade_alta_nunca_e_negativo():
    altas = pontuar_deals_abertos().query("prioridade == 'Alta'")
    assert not altas["motivo_principal"].str.startswith(("Parado", "Valor baixo")).any()
