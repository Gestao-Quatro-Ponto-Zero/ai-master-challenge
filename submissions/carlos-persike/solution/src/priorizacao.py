"""Regra de negócio: prioriza oportunidades abertas por Valor Esperado =
probabilidade histórica de fechar (pelo tempo desde o engajamento) x valor do produto.

Por que não usar produto/setor/vendedor no score: outputs/auditoria.txt mostra que
nenhum dos três tem relação estatística com o resultado do negócio nesse dataset.
Incluir isso no score seria fingir um sinal que os dados provam que não existe.
"""
from __future__ import annotations

import pandas as pd

from probabilidade import probabilidade_por_dias

# Data de referência: o dataset termina em 2017-12-31, então "hoje" é a última data
# observada nos dados — não a data real do sistema, pra o resultado ser reproduzível.
DATA_REFERENCIA = pd.Timestamp("2017-12-31")


def calcular_dias_desde_engajamento(engage_date, data_referencia: pd.Timestamp = DATA_REFERENCIA) -> float:
    if pd.isna(engage_date):
        return 0.0  # Prospecting: ainda não engajou, sem tempo de sobrevivência ainda.
    return max((data_referencia - engage_date).days, 0)


def priorizar_pipeline_aberto(df_enriquecido: pd.DataFrame, tabela_sobrevivencia: list[tuple[float, float]]) -> pd.DataFrame:
    abertos = df_enriquecido[df_enriquecido["deal_stage"].isin(["Prospecting", "Engaging"])].copy()

    abertos["dias_desde_engajamento"] = abertos["engage_date"].apply(calcular_dias_desde_engajamento)
    abertos["probabilidade_historica"] = abertos["dias_desde_engajamento"].apply(
        lambda d: probabilidade_por_dias(d, tabela_sobrevivencia)
    )
    abertos["valor_produto"] = abertos["sales_price"].fillna(abertos["sales_price"].median())
    abertos["valor_esperado"] = abertos["probabilidade_historica"] * abertos["valor_produto"]

    abertos["explicacao"] = abertos.apply(_montar_explicacao, axis=1)
    return abertos.sort_values("valor_esperado", ascending=False)


def _montar_explicacao(linha: pd.Series) -> str:
    if linha["deal_stage"] == "Prospecting":
        situacao = "Ainda não foi engajado."
    else:
        situacao = f"Está aberto há {int(linha['dias_desde_engajamento'])} dias."
    return (
        f"{situacao} Negócios parecidos historicamente fecham em "
        f"{linha['probabilidade_historica']:.0%} dos casos."
    )
