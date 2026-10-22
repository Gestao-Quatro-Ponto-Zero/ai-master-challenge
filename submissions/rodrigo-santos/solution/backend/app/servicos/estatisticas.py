"""
Estatísticas históricas, calculadas a partir dos negócios já fechados (ganhos ou perdidos).

São a régua do score: qual a taxa de vitória da empresa, quanto tempo os
negócios levam para se resolver e qual a faixa de preços.
"""

from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from app.dados.carregador import ETAPA_GANHO, ETAPAS_FECHADAS, carregar_deals


@dataclass(frozen=True)
class EstatisticasHistoricas:
    """Resumo do histórico usado para pontuar os negócios abertos."""

    # Taxa de vitória da empresa (0 a 1).
    taxa_vitoria_geral: float

    # Dias entre o início da negociação e o fechamento.
    ciclo_mediano_dias: int  # mediana dos negócios ganhos (o "normal")
    limite_dias: int         # o mais longo do histórico, ganho ou perdido

    # Faixa de preços dos produtos (para normalizar o valor).
    preco_minimo: float
    preco_maximo: float


def calcular_estatisticas_de(fechados: pd.DataFrame, precos: pd.Series) -> EstatisticasHistoricas:
    """
    Calcula as estatísticas a partir de um conjunto de negócios fechados.

    Recebe os dados como parâmetro (em vez de ler tudo) para que a validação
    possa usar só o que já tinha fechado numa data do passado.
    """
    ganho = fechados["deal_stage"] == ETAPA_GANHO
    duracao = (fechados["close_date"] - fechados["engage_date"]).dt.days

    return EstatisticasHistoricas(
        taxa_vitoria_geral=float(ganho.mean()),
        ciclo_mediano_dias=int(duracao[ganho].median()),
        limite_dias=int(duracao.max()),
        preco_minimo=float(precos.min()),
        preco_maximo=float(precos.max()),
    )


@lru_cache(maxsize=1)
def calcular_estatisticas() -> EstatisticasHistoricas:
    """Estatísticas de todo o histórico (calculadas uma vez)."""
    deals = carregar_deals()
    fechados = deals[deals["deal_stage"].isin(ETAPAS_FECHADAS)]
    return calcular_estatisticas_de(fechados, deals["sales_price"].dropna())
