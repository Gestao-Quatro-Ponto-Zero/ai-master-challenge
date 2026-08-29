"""Único sinal validado no dataset (ver outputs/auditoria.txt e outputs/validacao_modelo.json):
o tempo desde o engajamento até agora prevê, de forma modesta mas estatisticamente real,
a chance histórica de o negócio fechar como Ganho. Produto, setor e vendedor não têm sinal —
não entram aqui.
"""
from __future__ import annotations

import pandas as pd

N_FAIXAS = 10


def calcular_tabela_sobrevivencia(fechados: pd.DataFrame, n_faixas: int = N_FAIXAS) -> list[tuple[float, float]]:
    """Recebe deals Won/Lost com coluna 'dias_ciclo' e 'ganhou'.
    Retorna lista [(limite_superior_dias, taxa_historica_de_vitoria), ...] ordenada.
    """
    validos = fechados.dropna(subset=["dias_ciclo"]).copy()
    validos["faixa"] = pd.qcut(validos["dias_ciclo"], n_faixas, duplicates="drop")
    taxas = validos.groupby("faixa", observed=True)["ganhou"].mean()
    return [(intervalo.right, taxa) for intervalo, taxa in taxas.items()]


def probabilidade_por_dias(dias: float, tabela: list[tuple[float, float]]) -> float:
    """Aplica a tabela de faixas a um número de dias. Fora do range treinado, usa a última faixa."""
    for limite, taxa in tabela:
        if dias <= limite:
            return taxa
    return tabela[-1][1]
