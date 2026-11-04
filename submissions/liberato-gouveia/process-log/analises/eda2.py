import pandas as pd, numpy as np, sys
D=sys.argv[1]
p=pd.read_csv(f"{D}/sales_pipeline.csv"); a=pd.read_csv(f"{D}/accounts.csv")
pr=pd.read_csv(f"{D}/products.csv"); t=pd.read_csv(f"{D}/sales_teams.csv")
p['product']=p['product'].replace('GTXPro','GTX Pro')
for c in ['engage_date','close_date']: p[c]=pd.to_datetime(p[c])
p=p.merge(pr,on='product',how='left').merge(t,on='sales_agent',how='left').merge(a,on='account',how='left')
c=p[p.deal_stage.isin(['Won','Lost'])].copy(); c['won']=(c.deal_stage=='Won').astype(int)
c['cycle']=(c.close_date-c.engage_date).dt.days
print("overall win rate", round(c.won.mean(),3), "n", len(c))
def wr(col, minn=0):
    g=c.groupby(col).agg(n=('won','size'),wr=('won','mean')).sort_values('wr')
    g=g[g.n>=minn]; print(f"\n-- {col}: spread {g.wr.min():.3f}-{g.wr.max():.3f}"); print(g.round(3).to_string())
for col in ['product','series','regional_office','manager','sector']: wr(col)
wr('sales_agent')
c['acct_known']=c.account.notna(); wr('acct_known')
c['subsidiary']=c.subsidiary_of.notna(); wr('subsidiary')
c['size']=pd.qcut(c.revenue,4,labels=['Q1 small','Q2','Q3','Q4 big']); wr('size')
print("\ncycle days won vs lost:\n", c.groupby('deal_stage').cycle.describe().round(1))
c['cyc_b']=pd.cut(c.cycle,[-1,7,14,30,60,90,120,200]); wr('cyc_b')
print("\nclose_value / list price (won):", (c[c.won==1].close_value/c[c.won==1].sales_price).describe().round(3).to_dict())
print("lost close_value nonzero:", (c[c.won==0].close_value>0).sum())
c['eq']=c.engage_date.dt.to_period('Q'); wr('eq')
c['cm']=c.close_date.dt.month; wr('cm')
