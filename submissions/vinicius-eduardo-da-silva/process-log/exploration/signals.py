import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier as H
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score as auc
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)
pd.set_option("display.max_rows", 120)
d = sys.argv[1]
a = pd.read_csv(f"{d}/accounts.csv")
pr = pd.read_csv(f"{d}/products.csv")
t = pd.read_csv(f"{d}/sales_teams.csv")
p = pd.read_csv(f"{d}/sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
p["product"] = p["product"].replace({"GTXPro": "GTX Pro"})
a["sector"] = a.sector.replace({"technolgy": "technology"})
p = p.merge(pr, on="product", how="left").merge(t, on="sales_agent", how="left").merge(a, on="account", how="left")
snap = pd.Timestamp("2017-12-31")
c = p[p.deal_stage.isin(["Won", "Lost"])].copy()
c["won"] = (c.deal_stage == "Won").astype(int)
c["cycle"] = (c.close_date - c.engage_date).dt.days
o = p[p.deal_stage == "Engaging"].copy()
o["age"] = (snap - o.engage_date).dt.days

print("== ZOMBIE: open Engaging older than max closed cycle")
print("max cycle", c.cycle.max())
for k in [60, 90, 120, 138]:
    print(" open age >", k, (o.age > k).sum(), round((o.age > k).mean(), 3))
print("list value open >138d", o[o.age > 138].sales_price.sum(), " <=138d", o[o.age <= 138].sales_price.sum())

print("\n== Closed cycle bins")
c["cb"] = pd.cut(c.cycle, [0, 7, 14, 30, 60, 90, 120, 138])
print(c.groupby("cb", observed=True).agg(n=("won", "size"), wr=("won", "mean")).round(3))

print("\n== Conditional on being alive at age t")
allE = pd.concat([c.assign(end=c.cycle, closed=1), o.assign(end=o.age, closed=0, won=np.nan)])
rows = []
for tt in [0, 7, 14, 30, 45, 60, 75, 90, 105, 120, 130, 138]:
    elig = allE[(snap - allE.engage_date).dt.days >= tt]
    alive = elig[elig.end >= tt]
    cl = alive[alive.closed == 1]
    rows.append((tt, len(alive), len(cl), round(cl.won.mean(), 3) if len(cl) else None, round(len(cl) / len(alive), 3)))
print(pd.DataFrame(rows, columns=["age", "alive", "closed_later", "win_if_closed", "closed_share"]).to_string(index=False))

print("\n== Truncation: cycle by engage month")
print(c.groupby(c.engage_date.dt.to_period("M")).agg(n=("won", "size"), wr=("won", "mean"), minc=("cycle", "min"), med=("cycle", "median"), maxc=("cycle", "max")).round(3))

print("\n== Close month")
print(c.groupby(c.close_date.dt.to_period("M")).agg(n=("won", "size"), wr=("won", "mean")).round(3))
print("engage dow", c.engage_date.dt.dayofweek.value_counts().sort_index().to_dict())
print("close dow", c.close_date.dt.dayofweek.value_counts().sort_index().to_dict())

print("\n== Jul-Aug 2017 Engaging spike")
j = o[o.engage_date.dt.to_period("M").astype(str).isin(["2017-07", "2017-08"])]
print(j.sales_agent.value_counts().head(8).to_dict())
print(j["product"].value_counts().to_dict())
print("by manager", j.manager.value_counts().to_dict())
print("top days", {str(k.date()): v for k, v in j.engage_date.value_counts().head(6).items()})

print("\n== Univariate")
for f in ["product", "regional_office", "manager", "sector"]:
    print(c.groupby(f).agg(n=("won", "size"), wr=("won", "mean"), val=("close_value", lambda s: s[s > 0].mean())).round(3).sort_values("wr"))
print(c.groupby("sales_agent").agg(n=("won", "size"), wr=("won", "mean"), rev=("close_value", "sum")).sort_values("wr").round(3).to_string())

print("\n== Realized price vs list")
w = c[c.won == 1]
print((w.close_value / w.sales_price).describe().round(3).to_dict())
print(w.assign(r=w.close_value / w.sales_price).groupby("product").r.median().round(3).to_dict())
print(c.groupby(pd.qcut(c.employees, 4), observed=True).won.mean().round(3).to_dict())
print(c.groupby(pd.qcut(c.revenue, 4), observed=True).won.mean().round(3).to_dict())
print("subsidiary", c.groupby(c.subsidiary_of.notna()).won.mean().round(3).to_dict())

print("\n== Open deals coverage")
print("agents with deals but no open Engaging", sorted(set(c.sales_agent) - set(o.sales_agent)))
print("agents total with any deal", p.sales_agent.nunique())
print("share missing account per agent", o.assign(na=o.account.isna()).groupby("sales_agent").na.mean().describe().round(3).to_dict())

# Point-in-time features: only deals CLOSED strictly before this deal's engage_date.
c = c.sort_values("engage_date").reset_index(drop=True)
pc = c.sort_values("close_date")
all_dates = pc.close_date.values
all_cum = pc.won.cumsum().values


def pit(df, key, name, prior=20):
    groups = {k: (g.close_date.values, g.won.cumsum().values) for k, g in pc[[key, "close_date", "won"]].dropna().groupby(key)}
    res = []
    for k, e in zip(df[key], df.engage_date.values):
        i = np.searchsorted(all_dates, e)
        base = all_cum[i - 1] / i if i > 0 else 0.63
        n = wins = 0
        if k in groups:
            n = np.searchsorted(groups[k][0], e)
            wins = groups[k][1][n - 1] if n > 0 else 0
        res.append((wins + prior * base) / (n + prior))
    df[name] = res


for k, n in [("sales_agent", "agent_wr"), ("product", "product_wr"), ("account", "account_wr"), ("sector", "sector_wr"), ("manager", "mgr_wr")]:
    pit(c, k, n)
c["agent_load"] = [((c.sales_agent == s) & (c.engage_date < e) & (c.close_date >= e)).sum() for s, e in zip(c.sales_agent, c.engage_date)]
c["acct_prev_n"] = [((c.account == s) & (c.close_date < e)).sum() for s, e in zip(c.account, c.engage_date)]
c["acct_prev_won"] = [((c.account == s) & (c.close_date < e) & (c.won == 1)).sum() for s, e in zip(c.account, c.engage_date)]
c["price_log"] = np.log(c.sales_price)
c["emp_log"] = np.log1p(c.employees)
c["rev_log"] = np.log1p(c.revenue)
c["qtr_pos"] = (c.engage_date.dt.month - 1) % 3

# Train: closed before cut. Test: engaged after cut. No overlap and no label leakage.
cut = pd.Timestamp("2017-07-01")
tr = c[c.close_date < cut]
te = c[c.engage_date >= cut]
print("\n== Temporal backtest: train", len(tr), round(tr.won.mean(), 3), "test", len(te), round(te.won.mean(), 3))
groups = {
    "agent": ["agent_wr"],
    "product": ["product_wr", "price_log"],
    "account_hist": ["account_wr", "acct_prev_n", "acct_prev_won"],
    "account_firmo": ["emp_log", "rev_log", "sector_wr"],
    "workload": ["agent_load"],
    "manager": ["mgr_wr"],
    "calendar": ["qtr_pos"],
}
allf = sum(groups.values(), [])


def fit(fs):
    m = H(max_depth=3, max_iter=150, learning_rate=0.05, random_state=0).fit(tr[fs], tr.won)
    l = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500)).fit(tr[fs], tr.won)
    return round(auc(te.won, m.predict_proba(te[fs])[:, 1]), 3), round(auc(te.won, l.predict_proba(te[fs])[:, 1]), 3)


print("ALL (GB, LR)", fit(allf))
for g, f in groups.items():
    print(g, "only", fit(f), "| drop", fit([x for x in allf if x not in f]))
leak = allf + ["cycle"]
print("LEAKY with cycle (GB)", round(auc(te.won, H(max_depth=3, max_iter=150, random_state=0).fit(tr[leak], tr.won).predict_proba(te[leak])[:, 1]), 3))

l = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500)).fit(tr[allf], tr.won)
te = te.assign(ps=l.predict_proba(te[allf])[:, 1])
te["q"] = pd.qcut(te.ps, 5, labels=False, duplicates="drop")
print(te.groupby("q").agg(n=("won", "size"), pred=("ps", "mean"), act=("won", "mean"), rev=("close_value", "sum")).round(3))
