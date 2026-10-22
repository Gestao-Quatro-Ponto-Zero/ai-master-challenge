"""Exploração: algum atributo prevê vitória fora da amostra (AUC por corte temporal)?"""
import sys
import numpy as np, pandas as pd
D = sys.argv[1]
p = pd.read_csv(f"{D}/sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
p["product"] = p["product"].replace({"GTXPro": "GTX Pro"})
p = (p.merge(pd.read_csv(f"{D}/accounts.csv"), on="account", how="left")
      .merge(pd.read_csv(f"{D}/products.csv"), on="product", how="left")
      .merge(pd.read_csv(f"{D}/sales_teams.csv"), on="sales_agent", how="left"))
p["ganho"] = p.deal_stage == "Won"
p["dur"] = (p.close_date - p.engage_date).dt.days
p["agente_produto"] = p.sales_agent + "|" + p["product"]
p["setor_produto"] = p.sector.astype(str) + "|" + p["product"]
p["porte"] = pd.qcut(p.revenue, 4, labels=False)
p["func"] = pd.qcut(p.employees, 4, labels=False)
p["mes_inicio"] = p.engage_date.dt.month
p["idade_conta"] = pd.qcut(2017 - p.year_established, 4, labels=False)
def auc(s, y):
    r = pd.Series(s).rank().values; y = np.asarray(y); n1, n0 = y.sum(), (~y).sum()
    return (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
cols = ["sales_agent", "manager", "regional_office", "product", "series", "sector", "account", "office_location",
        "porte", "func", "idade_conta", "agente_produto", "setor_produto", "mes_inicio"]
res = {c: [] for c in cols}
for corte in ["2017-05-01", "2017-07-01", "2017-09-01", "2017-11-01"]:
    T = pd.Timestamp(corte); tr = p[p.close_date < T]; av = p[(p.engage_date < T) & (p.close_date >= T)]
    g0 = tr.ganho.mean()
    for c in cols:
        g = tr.groupby(c).ganho.agg(["sum", "count"]); taxa = (g["sum"] + 20 * g0) / (g["count"] + 20)
        m = av[c].notna(); res[c].append(auc(av[c].map(taxa).fillna(g0)[m], av.ganho[m]))
print("AUC fora da amostra por corte (0.5 = sorteio):")
for c, v in sorted(res.items(), key=lambda x: -np.mean(x[1])):
    print(f"  {c:<16} média={np.mean(v):.3f}  cortes={[round(x,3) for x in v]}")
# Teste de significância in-sample: as taxas por vendedor diferem mais que o acaso?
c = p[p.deal_stage.isin(["Won", "Lost"])]
from math import sqrt
g = c.groupby("sales_agent").ganho.agg(["mean", "count"]); g0 = c.ganho.mean()
z = (g["mean"] - g0) / np.sqrt(g0 * (1 - g0) / g["count"])
print(f"\nVendedores com taxa fora de ±2 erros-padrão: {(z.abs() > 2).sum()} de {len(g)} (esperado por acaso: ~{0.046*len(g):.1f})")
