"""AUC dos grupos e das faixas de idade em uso na ferramenta, contra o score ingênuo (vendedor + conta + produto + setor).

Uso: python -X utf8 auc_faixas.py <pasta crm-sales-predictive-analytics>
Saída bruta: evidencias/auc-faixas.txt. Só lê os CSVs.

População: negócios abertos em 30/09/2017 (já tinham começado e não tinham fechado).
Alvo: ganhou até 31/12/2017. Métrica: AUC (0,5 = acaso).
- 3 grupos: Siga (<= 40 d) > Foque (41-60 d) > Nutrição (> 60 d), ordenados pela chance.
- 8 faixas: a taxa de ganho de cada faixa do indicador, medida NESTE MESMO replay (dentro da amostra).
- ingênuo: taxas de ganho encolhidas (k = 50) de vendedor, conta, produto e setor, treinadas nos
  fechados até 30/09/2017 (o mesmo de validar_sinal.py); conta vazia fica neutra.
- preço de tabela: "ordenar por valor".
Roda em duas populações: só quem tem até 138 dias (o negócio mais longo que já fechou) e todos.
"""
import sys

import pandas as pd

d = sys.argv[1]
p = pd.read_csv(d + "/sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
acc = pd.read_csv(d + "/accounts.csv")
prod = pd.read_csv(d + "/products.csv")
p["product"] = p["product"].replace({"GTXPro": "GTX Pro"})
p = p.merge(acc[["account", "sector"]], on="account", how="left").merge(prod, on="product", how="left")
p["sector"] = p.sector.fillna("sem conta")
p["account_f"] = p.account.fillna("sem conta")


def auc(score, y):
    r = pd.Series(score).reset_index(drop=True).rank(method="average")
    y = pd.Series(y).reset_index(drop=True).astype(int)
    n1 = int(y.sum())
    n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


corte, fim = pd.Timestamp("2017-09-30"), pd.Timestamp("2017-12-31")
fech = p[p.deal_stage.isin(["Won", "Lost"])].copy()
fech["won"] = (fech.deal_stage == "Won").astype(int)
tr = fech[fech.close_date < pd.Timestamp("2017-10-01")]
ab = p[(p.engage_date <= corte) & (p.close_date.isna() | (p.close_date > corte))].copy()
ab["idade"] = (corte - ab.engage_date).dt.days
ok = ab.close_date.notna() & (ab.close_date <= fim)
ab["ganhou"] = ((ab.deal_stage == "Won") & ok).astype(int)

m = tr.won.mean()
soma = pd.Series(0.0, index=ab.index)
for src in ["sales_agent", "account_f", "product", "sector"]:
    g = tr.groupby(src).won.agg(["sum", "size"])
    ab[src + "_t"] = ab[src].map((g["sum"] + 50 * m) / (g["size"] + 50)).fillna(m)
    soma += ab[src + "_t"] - m
ab["ingenuo"] = soma

grupo = pd.cut(ab.idade, [-1, 40, 60, 10**6], labels=False)  # 0 Siga, 1 Foque, 2 Nutrição
ab["score_grupos"] = -grupo  # ordenado pela chance
fx = pd.cut(ab.idade, [-1, 10, 20, 30, 40, 50, 60, 90, 10**6])
taxa = ab.groupby(fx, observed=True).ganhou.mean()
ab["score_8faixas"] = fx.map(taxa).astype(float)

for nome, pop in [("1.879 abertos em 30/09 com idade <= 138 d", ab[ab.idade <= 138]), ("2.409 abertos em 30/09 (todos)", ab)]:
    print(f"## {nome}: n={len(pop)} | ganharam até 31/12: {pop.ganhou.sum()}")
    print(f"  3 grupos em uso (Siga>Foque>Nutrição): AUC {auc(pop.score_grupos, pop.ganhou):.3f}")
    print(f"  8 faixas do indicador (taxa da faixa, dentro da amostra): AUC {auc(pop.score_8faixas, pop.ganhou):.3f}")
    print(f"  ingênuo (vendedor+conta+produto+setor, treino até 30/09): AUC {auc(pop.ingenuo, pop.ganhou):.3f}")
    print(f"  preço de tabela: AUC {auc(pop.sales_price, pop.ganhou):.3f}")
    print(pop.assign(g=grupo.loc[pop.index].map({0: "Siga <=40", 1: "Foque 41-60", 2: "Nutrição >60"})).groupby("g").ganhou.agg(["size", "mean"]).round(3))
