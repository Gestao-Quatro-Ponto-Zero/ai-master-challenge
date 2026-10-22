"""Exploração: compara a lógica de tempo v1 (penaliza após 88 dias) com a v2 (chance condicional à idade)."""
import sys

import numpy as np
import pandas as pd

DADOS = sys.argv[1]
p = pd.read_csv(f"{DADOS}/sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
p["product"] = p["product"].replace({"GTXPro": "GTX Pro"})
contas = pd.read_csv(f"{DADOS}/accounts.csv")
prod = pd.read_csv(f"{DADOS}/products.csv")
p = p.merge(contas[["account", "sector"]], on="account", how="left").merge(prod, on="product", how="left")
p["dur"] = (p.close_date - p.engage_date).dt.days
p["ganho"] = p.deal_stage == "Won"
M = 20


def auc(score, y):
    r = pd.Series(score).rank().values
    y = np.asarray(y)
    n1, n0 = y.sum(), (~y).sum()
    return (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


for corte in ["2017-05-01", "2017-07-01", "2017-09-01"]:
    T = pd.Timestamp(corte)
    treino = p[p.close_date < T]
    geral = treino.ganho.mean()
    aval = p[(p.engage_date < T) & (p.close_date >= T)].copy()
    zumbis = p[(p.engage_date < T) & (p.close_date.isna() | (p.close_date >= T)) & ((T - p.engage_date).dt.days > 138)]
    aval["idade"] = (T - aval.engage_date).dt.days

    # chance por dimensão (suavizada), como no produto
    ch = 0
    pesos = {"product": 0.3, "sales_agent": 0.3, "sector": 0.2, "account": 0.2}
    soma = 0
    for col, w in pesos.items():
        g = treino.groupby(col).ganho.agg(["sum", "count"])
        taxa = aval[col].map((g["sum"] + M * geral) / (g["count"] + M))
        ch = ch + taxa.fillna(0) * w
        soma = soma + taxa.notna() * w
    aval["chance_dim"] = ch / soma

    # chance condicional à idade (v2)
    def cond(d):
        s = treino[treino.dur > d]
        return (s.ganho.sum() + M * geral) / (len(s) + M)
    aval["mult_idade"] = aval.idade.map(cond) / geral
    aval["chance_v2"] = aval.chance_dim * aval.mult_idade

    # fator tempo v1: 1 até p75 do ciclo ganho, 0 no p98
    ciclo = treino[treino.ganho].dur
    n, l = ciclo.quantile(0.75), ciclo.quantile(0.98)
    aval["tempo_v1"] = (1 - (aval.idade - n) / (l - n)).clip(0, 1)

    y = aval.ganho.values
    print(f"\n=== corte {corte}: treino={len(treino)} avaliados={len(aval)} vitória={y.mean():.1%} | "
          f"abertos >138d no corte={len(zumbis)} (fechados depois: {zumbis.close_date.notna().sum()})")
    for nome, s in [("chance por dimensão", aval.chance_dim), ("idade (v2)", aval.mult_idade),
                    ("chance v2 (dim × idade)", aval.chance_v2), ("tempo v1", aval.tempo_v1),
                    ("só valor", aval.sales_price)]:
        print(f"  AUC {nome:<26} {auc(s, y):.3f}")
    aval["faixa_idade"] = pd.cut(aval.idade, [-1, 15, 30, 60, 88, 125, 138])
    print(aval.groupby("faixa_idade", observed=True).ganho.agg(["count", "mean"]).round(3).to_string())
