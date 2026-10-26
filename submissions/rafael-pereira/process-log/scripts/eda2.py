import sys, pandas as pd, numpy as np
D=sys.argv[1]
p=pd.read_csv(f"{D}/sales_pipeline.csv",parse_dates=["engage_date","close_date"])
t=pd.read_csv(f"{D}/sales_teams.csv"); prod=pd.read_csv(f"{D}/products.csv")
p["product"]=p["product"].replace({"GTXPro":"GTX Pro"})
print("agents in teams",len(t),"in pipeline",p.sales_agent.nunique(),"| without deals:",sorted(set(t.sales_agent)-set(p.sales_agent)))
ref=pd.Timestamp("2017-12-31")
c=p[p.deal_stage.isin(["Won","Lost"])].copy(); c["cycle"]=(c.close_date-c.engage_date).dt.days
mx=c.cycle.max(); print("max closed cycle",mx,"p90 won",c[c.deal_stage=='Won'].cycle.quantile(.9))
o=p[p.deal_stage=="Engaging"].copy(); o["age"]=(ref-o.engage_date).dt.days
o=o.merge(prod,on="product")
print("Engaging n",len(o),"older than max closed cycle:",(o.age>mx).sum(),"=",round((o.age>mx).mean(),3),"| value of those",o[o.age>mx].sales_price.sum(),"of",o.sales_price.sum())
print(o.age.describe().round(0).to_dict())
print("age buckets\n",pd.cut(o.age,[-1,30,60,90,138,200,300,500]).value_counts().sort_index())
# lost cycle bimodality
print("Lost cycle hist\n",pd.cut(c[c.deal_stage=='Lost'].cycle,[0,7,14,30,60,90,140]).value_counts().sort_index())
print("Won cycle hist\n",pd.cut(c[c.deal_stage=='Won'].cycle,[0,7,14,30,60,90,140]).value_counts().sort_index())
# agent noise test: chi-square
from scipy.stats import chi2_contingency
c["won"]=(c.deal_stage=="Won").astype(int)
for col in ["sales_agent","product"]:
    ct=pd.crosstab(c[col],c.won); chi,pv,_,_=chi2_contingency(ct); print(col,"chi2 p-value",round(pv,4))
# account-level: accounts with no account (nulls) win rate
c["has_acct"]=c.account.notna()
print(c.groupby("has_acct").won.agg(["size","mean"]).round(3))
# win rate by engage month trend, and by rep x time stability (H1 vs H2 correlation)
c["h"]=np.where(c.engage_date<"2017-07-01","H1","H2")
a=c.groupby(["sales_agent","h"]).won.mean().unstack().dropna(); print("agent win-rate corr H1 vs H2:",round(a.corr().iloc[0,1],3))
# deals per agent per account repeats
print("accounts total",p.account.nunique(),"deals/account mean",round(p.groupby('account').size().mean(),1))
# discount behavior
w=c[c.deal_stage=="Won"].merge(prod,on="product"); w["ratio"]=w.close_value/w.sales_price
print("won ratio by product\n",w.groupby("product").ratio.agg(["mean","min","max"]).round(2))
# Won cycle by product
print(w.groupby("product").cycle.median())
# prospecting by agent/product
pr=p[p.deal_stage=="Prospecting"].merge(prod,on="product"); print("prospecting value",pr.sales_price.sum(),pr.groupby("product").size().to_dict())
