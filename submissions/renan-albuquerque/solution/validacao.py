"""Testa se as probabilidades do score batem com a realidade.

Treina com os deals que fecharam até 30/06/2017 e testa nos deals que entraram
em negociação depois disso. Para cada deal de teste, simula a ferramenta olhando
para ele em vários momentos (dia 0, 30, 60, 90...) enquanto ele ainda estava
aberto, e compara a chance prevista com o que realmente aconteceu.
"""

import numpy as np
import pandas as pd

from dados import carregar_dados, separar
from score import curva_idade, taxas_vendedor_produto

CORTE = pd.Timestamp("2017-07-01")
CHECKPOINTS = [0, 15, 30, 60, 90, 120]


def prever(teste, treino, metodo):
    taxa_global = (treino["deal_stage"] == "Won").mean()
    taxas = taxas_vendedor_produto(treino)
    curva, _ = curva_idade(treino)
    t = teste.merge(taxas[["sales_agent", "product", "taxa_ajustada"]],
                    on=["sales_agent", "product"], how="left")
    base = t["taxa_ajustada"].fillna(taxa_global).to_numpy()
    idade = curva.reindex(t["checkpoint"], method="ffill").to_numpy()
    if metodo == "só média geral":
        return np.full(len(t), taxa_global)
    if metodo == "só idade (escolhido)":
        return idade
    if metodo == "só vendedor×produto":
        return base
    if metodo == "multiplicando":
        return np.minimum(base * idade / taxa_global, 0.99)
    if metodo == "odds":
        odds = lambda p: p / (1 - p)
        o = odds(base) * odds(idade) / odds(taxa_global)
        return o / (1 + o)
    raise ValueError(metodo)


def auc(y, p):
    """Chance de um deal ganho receber nota maior que um perdido (0,5 = sorteio)."""
    r = pd.Series(p).rank().to_numpy()
    pos = y.sum()
    neg = len(y) - pos
    return (r[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg)


if __name__ == "__main__":
    fechados, _ = separar(carregar_dados())
    treino = fechados[fechados["close_date"] < CORTE]
    novos = fechados[fechados["engage_date"] >= CORTE]
    teste = pd.concat(
        [novos[novos["duracao_dias"] >= d].assign(checkpoint=d) for d in CHECKPOINTS]
    )
    y = (teste["deal_stage"] == "Won").astype(int).to_numpy()
    print(f"Treino: {len(treino)} deals | Teste: {len(novos)} deals, "
          f"{len(teste)} observações | Taxa real no teste: {y.mean():.1%}\n")

    for metodo in ["só média geral", "só vendedor×produto", "multiplicando", "odds", "só idade (escolhido)"]:
        p = prever(teste, treino, metodo)
        brier = np.mean((p - y) ** 2)
        print(f"{metodo:22s} AUC={auc(y, p):.3f}  erro (Brier)={brier:.4f}")
        if metodo in ("multiplicando", "só idade (escolhido)"):
            faixas = pd.cut(p, [0, .5, .6, .7, .8, .9, 1])
            tab = pd.DataFrame({"previsto": p, "real": y}).groupby(faixas, observed=True).agg(
                n=("real", "size"), previsto=("previsto", "mean"), real=("real", "mean"))
            print(tab.round(3).to_string(), "\n")
