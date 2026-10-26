import sys, pandas as pd, numpy as np
D=sys.argv[1]
p=pd.read_csv(f"{D}/sales_pipeline.csv",parse_dates=["engage_date","close_date"])
prod=pd.read_csv(f"{D}/products.csv"); p["product"]=p["product"].replace({"GTXPro":"GTX Pro"}); p=p.merge(prod,on="product")
for T in ["2017-06-30","2017-09-30"]:
    T=pd.Timestamp(T)
    s=p[(p.engage_date<=T)&((p.close_date>T)|p.close_date.isna())].copy()
    s["age"]=(T-s.engage_date).dt.days
    s["out"]=np.where(s.deal_stage=="Won","won",np.where(s.deal_stage=="Lost","lost","still_open"))
    s["bin"]=pd.cut(s.age,[-1,30,60,90,138,200,1000])
    g=s.groupby("bin",observed=True).out.value_counts().unstack(fill_value=0)
    g["n"]=g.sum(axis=1); g["win_if_closed"]=(g.won/(g.won+g.lost)).round(3); g["pct_still_open_end"]=(g.still_open/g.n).round(3)
    g["pct_won_of_all"]=(g.won/g.n).round(3)
    print("\n### snapshot",T.date(),"open deals:",len(s)); print(g)
# Do Engaging deals ever close after long age? max cycle of closed deals by engage cohort
c=p[p.deal_stage.isin(["Won","Lost"])].copy(); c["cycle"]=(c.close_date-c.engage_date).dt.days
print("\nclosed deals cycle>138:",(c.cycle>138).sum())
print("cycle max by engage quarter:\n",c.groupby(c.engage_date.dt.to_period("Q")).cycle.max())
# Engaging age at end by engage quarter
e=p[p.deal_stage=="Engaging"].copy(); print("\nEngaging by engage quarter:\n",e.groupby(e.engage_date.dt.to_period("Q")).size())
print("\nClosed (won+lost) by engage quarter:\n",c.groupby(c.engage_date.dt.to_period("Q")).size())
