import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import numpy as np, pandas as pd, scoring
d = scoring.load_pipeline()
today = scoring.reference_date(d)
print(d.deal_stage.value_counts())
print("engage", d.engage_date.min(), d.engage_date.max(), "close", d.close_date.min(), d.close_date.max())
sc, m = scoring.score_open_deals(d, today)
print(sc.lista.value_counts())
print(sc.groupby("lista").age.describe())
print("foco por faixa", sc[sc.lista=="foco"].faixa.value_counts())
print("foco por vendedor", sc[sc.lista=="foco"].groupby("sales_agent").size().describe())
print("vendedores com foco", sc[sc.lista=="foco"].sales_agent.nunique(), "de", d.sales_agent.nunique(), "com deals:", sc.sales_agent.nunique())
print("abertos sem conta:", sc.account.isna().sum(), "de", len(sc))
print(sc.groupby("lista").account.apply(lambda s: s.isna().mean()))
# ciclo
c = d[d.close_date.notna()].copy(); c["cyc"]=(c.close_date-c.engage_date).dt.days
print(c.groupby("deal_stage").cyc.describe())
print("quantis ciclo won", c[c.deal_stage=="Won"].cyc.quantile([.5,.75,.9,.95,.99,1]).to_dict())
# engaging abertos: mes de engage
e = d[d.deal_stage=="Engaging"]
print(e.engage_date.dt.to_period("M").value_counts().sort_index())
# por coorte de mes de engage: fração won/lost/aberto
d["m"]=d.engage_date.dt.to_period("M")
print(pd.crosstab(d.m, d.deal_stage, normalize="index").round(3))
print(pd.crosstab(d.m, d.deal_stage))
# chance curve
ch = m["chance_by_age"]; print([ (a, round(ch[a],3)) for a in range(0,200,10)])
# foco: idades
print(sc[sc.lista=="foco"].age.describe())
# vendedores engaging abertos por vendedor
print("abertos Engaging por vendedor", e.groupby("sales_agent").size().describe())
# win rate por idade ao fechar (entre fechados)
c["bin"]=pd.cut(c.cyc,[-1,7,14,30,60,90,140])
print(c.groupby("bin").apply(lambda g: pd.Series({"n":len(g),"win":(g.deal_stage=="Won").mean()})))
# preço x valor
print(d.groupby("product").agg(price=("sales_price","first"), n=("product","size")))
won=d[d.deal_stage=="Won"]; print("receita por produto", (won.groupby("product").close_value.sum()/won.close_value.sum()).round(3).to_dict())
