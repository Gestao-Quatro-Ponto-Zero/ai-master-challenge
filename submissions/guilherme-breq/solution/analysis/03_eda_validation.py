import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
d='../data/'
p=pd.read_csv(d+'sales_pipeline.csv',parse_dates=['engage_date','close_date'])
t=pd.read_csv(d+'sales_teams.csv'); pr=pd.read_csv(d+'products.csv')
p['product']=p['product'].replace('GTXPro','GTX Pro')
c=p[p.deal_stage.isin(['Won','Lost'])].copy(); c['won']=(c.deal_stage=='Won').astype(int)
c['days']=(c.close_date-c.engage_date).dt.days
# 1) P(win | deal still open at age X)
for x in [0,7,14,30,60,90,120,130,138]:
    s=c[c.days>x]; print(f'age>{x}: n={len(s)} wr={s.won.mean():.3f}')
# 2) open deals vs max cycle
o=p[p.deal_stage=='Engaging'].copy(); ref=p.close_date.max(); o['age']=(ref-o.engage_date).dt.days
print('ref',ref,'open engaging older than 138d:',(o.age>138).sum(),'/',len(o))
print('engage_date of open:',o.engage_date.describe())
print('closed engage months:',c.engage_date.dt.to_period('M').value_counts().sort_index().tail(6))
print('open engage months:',o.engage_date.dt.to_period('M').value_counts().sort_index())
# 3) quarter-end: is it about close date only? deals closed in qtr-end months — by days?
c['qe']=c.close_date.dt.month.isin([3,6,9,12])
print(c.groupby('qe').won.agg(['mean','count']))
# lost deals close date day distribution
# 4) agent stability: first half vs second half
c['h']=np.where(c.close_date<'2017-07-01','H1','H2')
g=c.groupby(['sales_agent','h']).won.mean().unstack(); print('agent wr corr H1-H2',g.corr().iloc[0,1])
g=c.groupby(['sales_agent','product','h']).won.agg(['mean','count']).unstack()
m=g[(g['count']['H1']>=8)&(g['count']['H2']>=8)]['mean']; print('agent-product corr H1-H2',m.corr().iloc[0,1],len(m))
g=c.groupby(['account','h']).won.mean().unstack(); print('account wr corr',g.corr().iloc[0,1])
g=c.groupby(['product','h']).won.mean().unstack(); print(g)
# agents without open/closed
print('agents total',t.sales_agent.nunique(),'with closed',c.sales_agent.nunique(),'with open',p[p.deal_stage.isin(['Engaging','Prospecting'])].sales_agent.nunique())
print('agents no deals at all', set(t.sales_agent)-set(p.sales_agent))
# value
print('open value by product', p[p.deal_stage!='Won'].merge(pr,on='product').groupby('deal_stage').sales_price.sum())
