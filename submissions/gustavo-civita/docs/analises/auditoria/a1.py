import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import numpy as np, pandas as pd
import scoring, backtest
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
d = scoring.load_pipeline()
today = scoring.reference_date(d)
print(d.deal_stage.value_counts())
print("engage", d.engage_date.min(), d.engage_date.max(), "close", d.close_date.min(), d.close_date.max())
d["em"] = d.engage_date.dt.to_period("M"); d["cm"] = d.close_date.dt.to_period("M")
print("\n== engage month x stage")
print(pd.crosstab(d.em, d.deal_stage))
print("\n== engage month x close month (closed)")
print(pd.crosstab(d.em, d.cm))
c = d[d.close_date.notna()].copy(); c["cyc"] = (c.close_date - c.engage_date).dt.days
print("\ncycle describe", c.cyc.describe())
print(c.groupby("deal_stage").cyc.describe())
# quarter claim
c["eqq"] = c.engage_date.dt.to_period("Q"); c["cq"] = c.close_date.dt.to_period("Q")
c["qdiff"] = (c.cq.dt.year - c.eqq.dt.year) * 4 + (c.cq.dt.quarter - c.eqq.dt.quarter)
print("\nquarter diff", c.qdiff.value_counts().to_dict())
# day-of-quarter of engage vs max cycle
c["doq"] = (c.engage_date - c.eqq.dt.start_time).dt.days
print(c.groupby(pd.cut(c.doq, [-1, 15, 30, 45, 60, 75, 92])).cyc.agg(["size", "max", "median"]))
# close date day of month distribution
print("\nclose day-of-quarter hist")
c["cdoq"] = (c.close_date - c.cq.dt.start_time).dt.days
print(c.groupby(pd.cut(c.cdoq, [-1, 15, 30, 45, 60, 75, 92])).size())
print("\nengage day-of-quarter hist (all with engage)")
e = d[d.engage_date.notna()].copy(); e["doq"] = (e.engage_date - e.engage_date.dt.to_period("Q").dt.start_time).dt.days
print(pd.crosstab(pd.cut(e.doq, [-1, 15, 30, 45, 60, 75, 92]), e.deal_stage))

# open deals today
sc, model = scoring.score_open_deals(d, today)
print("\nlista counts", sc.lista.value_counts().to_dict())
print(pd.crosstab(sc.regional_office, sc.lista))
print(pd.crosstab(sc.regional_office, sc.deal_stage))
print("foco age describe", sc[sc.lista == "foco"].age.describe())
print("foco chance describe", sc[sc.lista == "foco"].chance.describe())
print("foco fechaEsteMes", (sc[sc.lista == "foco"].chance_soon >= 0.10).sum())
print("EV by lista", sc.groupby("lista").valor_esperado.sum())
print("foco per agent:", sc[sc.lista == "foco"].groupby("sales_agent").size().describe())
print("agents with zero foco:", 35 - sc[sc.lista == "foco"].sales_agent.nunique(), " agents in pipeline:", d.sales_agent.nunique())
eng = sc[sc.deal_stage == "Engaging"]
print("Engaging open age hist", pd.cut(eng.age, [-1, 30, 60, 97, 138, 150, 180, 250, 500]).value_counts().sort_index())
print("open engaging by engage month x region")
print(pd.crosstab(eng.engage_date.dt.to_period("M"), eng.regional_office))
print("account missing among open:", sc.account.isna().mean(), sc.groupby("deal_stage").account.apply(lambda s: s.isna().mean()))
print("chance_by_age[0], soon[0]:", model["chance_by_age"][0], model["soon_by_age"][0])
print("score distribution abordar:", sc[sc.lista == "abordar"].groupby("product").agg(n=("score", "size"), score=("score", "mean"), ev=("valor_esperado", "mean")))
print("score distribution foco unique chance*price combos:", sc[sc.lista == "foco"][["valor_esperado"]].nunique())
