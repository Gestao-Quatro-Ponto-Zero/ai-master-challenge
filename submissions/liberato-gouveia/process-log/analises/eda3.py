import pandas as pd, numpy as np, sys
from scipy import stats
D=sys.argv[1]
p=pd.read_csv(f"{D}/sales_pipeline.csv"); a=pd.read_csv(f"{D}/accounts.csv")
pr=pd.read_csv(f"{D}/products.csv"); t=pd.read_csv(f"{D}/sales_teams.csv")
p['product']=p['product'].replace('GTXPro','GTX Pro')
for c in ['engage_date','close_date']: p[c]=pd.to_datetime(p[c])
p=p.merge(pr,on='product',how='left').merge(t,on='sales_agent',how='left')
ASOF=pd.Timestamp('2017-12-31')
c=p[p.deal_stage.isin(['Won','Lost'])].copy(); c['won']=(c.deal_stage=='Won').astype(int)
c['cycle']=(c.close_date-c.engage_date).dt.days
# cohort engaged Mar-Aug 2017: full follow-up >=120d
co=c[(c.engage_date>='2017-03-01')&(c.engage_date<='2017-08-31')]
allco=p[(p.engage_date>='2017-03-01')&(p.engage_date<='2017-08-31')]
print("cohort Mar-Aug17: total",len(allco),"closed",len(co),"still open",(allco.deal_stage=='Engaging').sum())
co=co.assign(b=pd.cut(co.cycle,[-1,7,14,30,60,90,120,200]))
print(co.groupby('b',observed=True).won.agg(['size','mean']).round(3))
# conditional: P(win | still open at day t) using full cohort
for tday in [0,7,14,30,60,90,120]:
    s=co[co.cycle>tday]; print(f"P(win|alive>{tday}d) = {s.won.mean():.3f} (n={len(s)})")
print("\nmax cycle closed:",c.cycle.max(), " p95:",c.cycle.quantile(.95), " p99:", c.cycle.quantile(.99))
o=p[p.deal_stage=='Engaging'].copy(); o['age']=(ASOF-o.engage_date).dt.days
print("\nEngaging age as of 2017-12-31:\n", o.age.describe().round(0).to_dict())
print(pd.cut(o.age,[-1,30,60,90,138,200,300,500]).value_counts().sort_index())
print("open engage months:\n", o.engage_date.dt.to_period('M').value_counts().sort_index().to_dict())
# account dispersion vs binomial
g=c.dropna(subset=['account']).groupby('account').won.agg(['size','sum'])
ov=c.won.mean(); chi=(((g['sum']-g['size']*ov)**2)/(g['size']*ov*(1-ov))).sum()
print(f"\naccount heterogeneity chi2={chi:.1f} df={len(g)-1} p={1-stats.chi2.cdf(chi,len(g)-1):.3f}")
for col in ['sales_agent','product','manager']:
    g=c.groupby(col).won.agg(['size','sum']); chi=(((g['sum']-g['size']*ov)**2)/(g['size']*ov*(1-ov))).sum()
    print(f"{col} heterogeneity chi2={chi:.1f} df={len(g)-1} p={1-stats.chi2.cdf(chi,len(g)-1):.4f}")
g=c.groupby(['sales_agent','product']).won.agg(['size','sum']); g=g[g['size']>=15]
chi=(((g['sum']-g['size']*ov)**2)/(g['size']*ov*(1-ov))).sum()
print(f"agent x product chi2={chi:.1f} df={len(g)-1} p={1-stats.chi2.cdf(chi,len(g)-1):.4f}")
# value
print("\nopen pipeline list value by product:\n", p[p.deal_stage.isin(['Engaging','Prospecting'])].groupby(['product']).agg(n=('opportunity_id','size'),list_value=('sales_price','sum')).sort_values('list_value'))
print("agent open load:\n", p[p.deal_stage.isin(['Engaging','Prospecting'])].groupby('sales_agent').size().describe().round(1).to_dict())
print("agents with zero history but in teams have open deals?", p[p.sales_agent.isin(['Elizabeth Anderson','Carl Lin'])].shape)
