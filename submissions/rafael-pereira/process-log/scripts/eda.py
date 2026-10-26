import sys
import pandas as pd, numpy as np
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30)
D = sys.argv[1]
acc = pd.read_csv(f"{D}/accounts.csv"); prod = pd.read_csv(f"{D}/products.csv")
teams = pd.read_csv(f"{D}/sales_teams.csv"); p = pd.read_csv(f"{D}/sales_pipeline.csv", parse_dates=["engage_date", "close_date"])

print("## SHAPE", p.shape)
print("\n## NULLS\n", p.isna().sum())
print("\n## STAGES\n", p.deal_stage.value_counts())
print("\n## PRODUCT names in pipeline vs catalog")
print(sorted(set(p["product"].dropna()) - set(prod["product"])))
print("\n## ACCOUNT names missing from accounts:", sorted(set(p.account.dropna()) - set(acc.account)))
print("## AGENTS missing from teams:", sorted(set(p.sales_agent) - set(teams.sales_agent)))
print("## accounts sectors:", acc.sector.value_counts().to_dict())
print("## dup opp ids:", p.opportunity_id.duplicated().sum())

# normalize
p["product"] = p["product"].replace({"GTXPro": "GTX Pro"})
print("\n## stage vs null dates")
print(p.groupby("deal_stage").agg(n=("opportunity_id", "size"), no_engage=("engage_date", lambda s: s.isna().sum()),
      no_close=("close_date", lambda s: s.isna().sum()), no_account=("account", lambda s: s.isna().sum()),
      cv_zero=("close_value", lambda s: (s == 0).sum()), cv_mean=("close_value", "mean")))

print("\n## date ranges\n", p.groupby("deal_stage")[["engage_date", "close_date"]].agg(["min", "max"]))

p = p.merge(prod, on="product", how="left").merge(teams, on="sales_agent", how="left").merge(acc, on="account", how="left")
p["cycle"] = (p.close_date - p.engage_date).dt.days
closed = p[p.deal_stage.isin(["Won", "Lost"])].copy()
closed["won"] = (closed.deal_stage == "Won").astype(int)
print("\n## OVERALL closed win rate", closed.won.mean().round(3), "n_closed", len(closed), "open", (~p.deal_stage.isin(['Won','Lost'])).sum())

print("\n## close_value vs list price (Won)")
w = closed[closed.won == 1]
print(((w.close_value / w.sales_price)).describe())

def wr(col, minn=0):
    g = closed.groupby(col).agg(n=("won", "size"), win=("won", "mean"), rev=("close_value", "sum")).sort_values("win", ascending=False)
    return g[g.n >= minn].round(3)

for c in ["product", "series", "sector", "regional_office", "manager", "office_location"]:
    print(f"\n## WIN RATE by {c}\n", wr(c))
print("\n## WIN RATE by agent (top/bottom)\n", wr("sales_agent").pipe(lambda d: pd.concat([d.head(5), d.tail(5)])))
print("agent win-rate spread:", wr("sales_agent").win.describe().round(3).to_dict())

closed["price_bin"] = pd.qcut(closed.sales_price, 4, duplicates="drop")
print("\n## WIN RATE by price quartile\n", wr("price_bin"))
closed["rev_bin"] = pd.qcut(closed.revenue, 4)
print("\n## WIN RATE by account revenue quartile\n", wr("rev_bin"))
closed["emp_bin"] = pd.qcut(closed.employees, 4)
print("\n## WIN RATE by employees quartile\n", wr("emp_bin"))
closed["age_bin"] = pd.cut(2017 - closed.year_established, [0, 15, 25, 35, 100])
print("\n## WIN RATE by account age\n", wr("age_bin"))
closed["subs"] = closed.subsidiary_of.notna()
print("\n## WIN RATE subsidiary\n", wr("subs"))

print("\n## CYCLE DAYS (closed) Won vs Lost\n", closed.groupby("won").cycle.describe().round(1))
closed["cyc_bin"] = pd.cut(closed.cycle, [-1, 7, 30, 60, 90, 120, 1000])
print(wr("cyc_bin"))
closed["month"] = closed.close_date.dt.to_period("Q")
print("\n## WIN RATE by close quarter\n", wr("month"))
closed["engage_q"] = closed.engage_date.dt.to_period("Q")
print("\n## WIN RATE by engage quarter\n", wr("engage_q"))

print("\n## OPEN PIPELINE")
o = p[~p.deal_stage.isin(["Won", "Lost"])].copy()
print(o.groupby("deal_stage").agg(n=("opportunity_id", "size"), potential=("sales_price", "sum"), no_acct=("account", lambda s: s.isna().sum()),
      engage_min=("engage_date", "min"), engage_max=("engage_date", "max")))
ref = p.close_date.max()
print("max close_date (data 'today'):", ref, "| max engage:", p.engage_date.max())
o["age"] = (p.engage_date.max() - o.engage_date).dt.days
print(o.groupby("deal_stage").age.describe().round(1))
print("\n## Open deals by agent (top 5 count)\n", o.groupby("sales_agent").size().sort_values(ascending=False).head(5))

print("\n## Concentration: share of Won revenue by product\n", (w.groupby("product").close_value.sum() / w.close_value.sum()).round(3).sort_values(ascending=False))
print("\n## Agents with accounts coverage: unique accounts per agent\n", p.groupby("sales_agent").account.nunique().describe().round(1))

# simple signal strength: logistic-ish via per-feature AUC proxy
from itertools import product as _p
def auc(x, y):
    from scipy.stats import rankdata
    r = rankdata(x); n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
print("\n## Single-feature AUC (closed deals; 0.5 = no signal)")
c2 = closed.dropna(subset=["cycle", "revenue"]).copy()
for f in ["sales_price", "cycle", "revenue", "employees", "year_established"]:
    print(f, round(auc(c2[f].values, c2.won.values), 3))
for cat in ["product", "sector", "sales_agent", "manager", "regional_office", "office_location"]:
    enc = c2.groupby(cat).won.transform("mean")  # in-sample (optimistic) target encoding
    print(cat, "in-sample target-enc AUC", round(auc(enc.values, c2.won.values), 3))
