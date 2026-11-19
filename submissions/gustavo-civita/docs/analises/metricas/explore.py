import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import pandas as pd, numpy as np
import scoring
pd.set_option("display.width",250); pd.set_option("display.max_columns",40); pd.set_option("display.max_rows",200)
d = scoring.load_pipeline()
ref = scoring.reference_date(d)
print(ref, len(d))
print(d.deal_stage.value_counts())
print(d.groupby("deal_stage")[["engage_date","close_date","close_value"]].agg(lambda s: s.notna().sum()))
print(d.engage_date.min(), d.engage_date.max(), d.close_date.min(), d.close_date.max())
print(d.groupby(["regional_office","manager"]).sales_agent.nunique())
print("agents in teams", pd.read_csv(scoring.DATA_DIR/"sales_teams.csv").sales_agent.nunique(), "with deals", d.sales_agent.nunique())
d["cm"]=d.close_date.dt.to_period("M"); d["em"]=d.engage_date.dt.to_period("M")
print(d.groupby(["cm","deal_stage"]).size().unstack())
print(d[d.deal_stage=="Won"].groupby("cm").close_value.sum())
print(d.groupby("em").size())
c=d[d.close_date.notna()].copy(); c["cyc"]=(c.close_date-c.engage_date).dt.days
print(c.groupby("deal_stage").cyc.describe())
o,_=scoring.score_open_deals(d,ref)
print(o.lista.value_counts()); print(o.groupby("lista").age.describe())
print(o.groupby("lista").sales_price.sum())
print(pd.Series(_["chance_by_age"]).round(3).iloc[::5].to_dict())
print(o.account.isna().groupby(o.lista).mean())
