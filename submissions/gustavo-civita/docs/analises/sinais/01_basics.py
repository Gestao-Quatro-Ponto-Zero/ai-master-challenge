from common import *
d = load()
print(d.deal_stage.value_counts())
print(d.groupby("deal_stage")[["account","engage_date","close_date","close_value"]].apply(lambda g: g.isna().mean()))
print(d.engage_date.describe()); print(d.close_date.describe())
print(d.groupby(d.engage_date.dt.to_period("M")).deal_stage.value_counts().unstack())
print(d.groupby(d.close_date.dt.to_period("M")).deal_stage.value_counts().unstack())
c = d[d.closed]
print(c.groupby("deal_stage").cycle.describe())
print(c.groupby("product").agg(n=("won","size"), wr=("won","mean"), cyc=("cycle","median"), price=("sales_price","first")))
w = c[c.won==1]
print(w.groupby("product").ratio.describe())
print("lost close_value", c[c.won==0].close_value.describe())
o = d[~d.closed]
print(o.groupby(["deal_stage"]).agg(n=("product","size"), noacc=("account", lambda s: s.isna().mean())))
print(o[o.deal_stage=="Engaging"].groupby(o.engage_date.dt.to_period("M")).agg(n=("product","size"), noacc=("account", lambda s: s.isna().mean())))
print(o.groupby(["regional_office","deal_stage"]).agg(n=("product","size"), noacc=("account", lambda s: s.isna().mean())))
print(o.groupby(["sales_agent","deal_stage"]).agg(n=("product","size"), noacc=("account", lambda s: s.isna().mean())).unstack())
print(d.groupby("sales_agent").deal_stage.value_counts().unstack())
