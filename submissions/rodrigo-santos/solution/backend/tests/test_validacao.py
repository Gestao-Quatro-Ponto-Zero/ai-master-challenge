"""Testes da validação (backtest) do score."""

import pandas as pd

from app.dados.carregador import carregar_deals
from app.servicos.validacao import (
    _preparar_atributos,
    avaliar_corte,
    calcular_auc,
    executar_validacao,
    gerar_relatorio,
)


def test_auc_basico():
    ganho = pd.Series([True, True, False, False])
    assert calcular_auc(pd.Series([4, 3, 2, 1]), ganho) == 1.0   # separa perfeitamente
    assert calcular_auc(pd.Series([1, 2, 3, 4]), ganho) == 0.0   # separa ao contrário
    assert calcular_auc(pd.Series([1, 1, 1, 1]), ganho) == 0.5   # não separa nada


def test_corte_usa_apenas_negocios_fechados_antes_da_data():
    """Sem vazamento: o "treino" só pode conter o que já tinha fechado no dia do corte."""
    deals = _preparar_atributos(carregar_deals())
    resultado = avaliar_corte(deals, "2017-07-01")
    fechados_antes = deals[deals["close_date"] < pd.Timestamp("2017-07-01")]
    assert resultado["negocios_treino"] == len(fechados_antes)


def test_nenhum_negocio_parado_fechou_depois():
    """É a evidência que sustenta a regra "parado = atualize ou encerre"."""
    validacao = executar_validacao()
    assert validacao["parados"] > 1000
    assert validacao["parados_fechados_depois"] == 0


def test_prioridade_alta_concentra_mais_receita_por_negocio():
    por_prioridade = {p["prioridade"]: p for p in executar_validacao()["por_prioridade"]}
    assert por_prioridade["Alta"]["receita_media"] > 5 * por_prioridade["Média"]["receita_media"]


def test_nenhum_atributo_preve_vitoria_melhor_que_o_acaso():
    """Se um dia algum atributo passar a prever, este teste avisa que a lógica deve ser revista."""
    for atributo in executar_validacao()["atributos"]:
        assert 0.4 < atributo["auc_medio"] < 0.6, atributo


def test_relatorio_e_gerado():
    relatorio = gerar_relatorio()
    assert relatorio.startswith("# Validação da pontuação")
    assert "Vendedor" in relatorio
