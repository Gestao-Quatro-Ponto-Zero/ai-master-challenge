import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import numpy as np, pandas as pd
from scipy import stats
import scoring
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
d = scoring.load_pipeline(); today = scoring.reference_date(d)
teams = pd.read_csv(scoring.DATA_DIR / "sales_teams.csv")
print(teams[~teams.sales_agent.isin(d.sales_agent)])
print(teams.groupby("regional_office").size())
od, meta = scoring.score_open_deals(d, today)
print("chance por idade:", {a: round(meta["chance_by_age"][a], 2) for a in range(0, 141, 10)})
print("chance 30d por idade:", {a: round(meta["soon_by_age"][a], 2) for a in range(0, 141, 10)})
eng = d[d.engage_date.notna()]
print("engage por mes x escritorio"); print(pd.crosstab(eng.engage_date.dt.to_period("M"), eng.regional_office))
print("ultima engage por escritorio"); print(eng.groupby("regional_office").engage_date.max())
print("Engaging abertas por escritorio x mes de engage"); o = od[od.deal_stage == "Engaging"]; print(pd.crosstab(o.engage_date.dt.to_period("Q"), o.regional_office))
print("fechamentos Q4 por escritorio"); h = d[d.close_date >= "2017-10-01"]; print(pd.crosstab(h.regional_office, h.deal_stage))
# regra de trimestre
q = lambda s: s.dt.year * 4 + s.dt.quarter
cl = d[d.deal_stage.isin(["Won", "Lost"])]
print("fechadas: trimestres engage->close"); print(pd.crosstab(q(cl.close_date) - q(cl.engage_date), cl.deal_stage))
tq = today.year * 4 + today.quarter
print("abertas Engaging: trimestres desde engage"); print((tq - q(o.engage_date)).value_counts().sort_index())
print("lista x trimestres"); print(pd.crosstab(tq - q(o.engage_date), o.lista))
# regras simples vs modelo
morto = o.lista.isin(["encerrar", "reativar"])
for name, rule in [("idade>138", o.age > 138), ("idade>120", o.age > 120), ("idade>90", o.age > 90), ("engage antes do trimestre atual", q(o.engage_date) < tq), ("engage ha 2+ trimestres", tq - q(o.engage_date) >= 2)]:
    print(f"{name:32s} encerra {rule.sum():5d} | concorda c/ modelo morto {(rule & morto).sum()} de {morto.sum()} | mata vivas {(rule & ~morto).sum()}")
# valor ganho no dia do trimestre: concentracao no fim do trimestre?
won = cl[cl.deal_stage == "Won"]
doq = (won.close_date - won.close_date.dt.to_period("Q").dt.start_time).dt.days
print("ganhos por terco do trimestre"); print(pd.cut(doq, [-1, 30, 60, 92]).value_counts(sort=False))
lost = cl[cl.deal_stage == "Lost"]; doq = (lost.close_date - lost.close_date.dt.to_period("Q").dt.start_time).dt.days
print("perdidos por terco do trimestre"); print(pd.cut(doq, [-1, 30, 60, 92]).value_counts(sort=False))
# coortes de engage: % ganho, perdido, aberto
eng = eng.assign(m=eng.engage_date.dt.to_period("M"))
c = pd.crosstab(eng.m, eng.deal_stage, normalize="index").round(3); c["n"] = eng.groupby("m").size(); print(c)
# zumbis por coorte e vendedor: taxa de 'nao encerrado' varia por vendedor?
old = eng[eng.engage_date < "2017-07-01"]
z = old.groupby("sales_agent").apply(lambda g: (g.deal_stage == "Engaging").mean()); print("taxa de zumbi (coorte <jul/17) por vendedor: min/med/max", z.min().round(3), z.median().round(3), z.max().round(3))
ct = pd.crosstab(old.sales_agent, old.deal_stage == "Engaging"); print("qui2 zumbi~vendedor p=", stats.chi2_contingency(ct)[1])
ct = pd.crosstab(old["product"], old.deal_stage == "Engaging"); print("qui2 zumbi~produto p=", stats.chi2_contingency(ct)[1]); print((ct[True] / ct.sum(axis=1)).round(3))
ct = pd.crosstab(old.regional_office, old.deal_stage == "Engaging"); print("zumbi~escritorio p=", stats.chi2_contingency(ct)[1]); print((ct[True] / ct.sum(axis=1)).round(3))
# rapidez: deals ganhos <=14d por vendedor
won = won.assign(dur=(won.close_date - won.engage_date).dt.days)
f = won.groupby("sales_agent").apply(lambda g: (g.dur <= 14).mean()); print("share ganhos <=14d por vendedor min/med/max", f.min().round(2), f.median().round(2), f.max().round(2))
# vivas por dia: tamanho da fila do vendedor
foco = od[od.lista == "foco"]; print("foco: chance_soon>=.10:", (foco.chance_soon >= .10).sum(), " VE por faixa"); print(foco.groupby("faixa").agg(n=("faixa", "size"), ve=("valor_esperado", "sum"), preco=("sales_price", "sum")))
print("foco por idade"); print(pd.cut(foco.age, [0, 30, 60, 80, 100]).value_counts(sort=False))
