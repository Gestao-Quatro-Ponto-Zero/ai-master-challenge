"""Pontos por atributo no método de pontuação do HubSpot: pontos = taxa de fechamento do valor ÷ taxa geral.

Uso: python -X utf8 metodo_hubspot.py <solution/data/deals.json>
Saída bruta: evidencias/metodo-hubspot.txt. Só lê o deals.json (as 4 tabelas já juntas).

Taxa de fechamento = ganhos ÷ fechados (Won + Lost). Um atributo de perfil só "pontua" se os
pontos dele se afastam de 1,0. "conta_preenchida" mostra que todos os fechados têm conta: por isso
"sem conta" não pode penalizar um negócio aberto (seria vazamento do desfecho).
"""
import json
import sys

import pandas as pd

j = json.load(open(sys.argv[1], encoding="utf-8"))
df = pd.DataFrame(j["deals"])
f = df[df.deal_stage.isin(["Won", "Lost"])].copy()
f["won"] = f.deal_stage == "Won"
geral = f.won.mean()
print(f"taxa geral de fechamento (ganho/fechados): {geral:.1%} de {len(f)}")
f["porte"] = pd.qcut(f.revenue, 4, labels=["Q1 menor", "Q2", "Q3", "Q4 maior"])
f["conta_preenchida"] = f.account.notna()
for col in ["sector", "product", "regional_office", "porte", "conta_preenchida"]:
    g = f.groupby(col, observed=True).won.agg(["mean", "size"])
    pts = g["mean"] / geral
    print(f"\n{col}: pontos (taxa/geral) min {pts.min():.2f} max {pts.max():.2f}")
    for k, r in g.iterrows():
        print(f"  {k}: {r['mean']:.1%} de {int(r['size'])} -> {r['mean'] / geral:.2f}")
g = f.groupby("sales_agent").won.mean() / geral
print(f"\nsales_agent ({len(g)} com negócio fechado): pontos min {g.min():.2f} max {g.max():.2f}")

# Eixo de Interesse: a idade do negócio aberto. Não dá para medir nos fechados (a idade de um aberto
# não existe depois que ele fecha), então a base é o replay da ferramenta: abertos 92 dias antes da
# referência (30/09/2017), idade nesse corte, ganhou até a referência (31/12/2017).
fim = pd.Timestamp(j["referencia"])
corte = fim - pd.Timedelta(days=92)
df["eng"] = pd.to_datetime(df.engage_date)
df["fech"] = pd.to_datetime(df.close_date)
ab = df[df.eng.notna() & (df.eng <= corte) & (df.fech.isna() | (df.fech > corte))].copy()
ab["idade"] = ((corte - ab.eng).dt.days).astype(int)
ab["ganhou"] = (ab.deal_stage == "Won") & ab.fech.notna() & (ab.fech <= fim)
base = ab.ganhou.mean()
print(f"\nidade (replay {corte.date()} -> {fim.date()}): taxa geral {base:.1%} de {len(ab)}")
fx = pd.cut(ab.idade, [-1, 10, 20, 30, 40, 50, 60, 90, 10**6], labels=["0-10", "11-20", "21-30", "31-40", "41-50", "51-60", "61-90", ">90"])
gi = ab.groupby(fx, observed=True).ganhou.agg(["mean", "size"])
pts = gi["mean"] / base
print(f"idade: pontos (taxa/geral) min {pts.min():.2f} max {pts.max():.2f}")
for k, r in gi.iterrows():
    print(f"  {k} d: {r['mean']:.1%} de {int(r['size'])} -> {r['mean'] / base:.2f}")
