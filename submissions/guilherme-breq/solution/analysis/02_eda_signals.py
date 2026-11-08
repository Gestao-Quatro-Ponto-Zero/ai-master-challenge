import pandas as pd, numpy as np
pd.set_option('display.width',200)
d='../data/'
p=pd.read_csv(d+'sales_pipeline.csv',parse_dates=['engage_date','close_date'])
a=pd.read_csv(d+'accounts.csv'); pr=pd.read_csv(d+'products.csv'); t=pd.read_csv(d+'sales_teams.csv')
p['product']=p['product'].replace('GTXPro','GTX Pro')
p=p.merge(a,on='account',how='left').merge(pr,on='product',how='left').merge(t,on='sales_agent',how='left')
print('missing account by stage:\n',p[p.account.isna()].deal_stage.value_counts())
c=p[p.deal_stage.isin(['Won','Lost'])].copy(); c['won']=(c.deal_stage=='Won').astype(int)
c['days']=(c.close_date-c.engage_date).dt.days
def wr(col):
    g=c.groupby(col).won.agg(['mean','count']); print(g.sort_values('mean'),'\n')
for col in ['product','series','sector','regional_office','manager']: wr(col)
g=c.groupby('sales_agent').won.agg(['mean','count']); print('agent wr range',g['mean'].min(),g['mean'].max(), g['mean'].std())
g=c.groupby('account').won.agg(['mean','count']); print('account wr range',g['mean'].min(),g['mean'].max(),g['mean'].std(),'n',g['count'].median())
print('days won vs lost\n',c.groupby('deal_stage').days.describe())
c['dbin']=pd.cut(c.days,[-1,7,14,30,45,60,90,120,200])
print(c.groupby('dbin').won.agg(['mean','count']))
c['revbin']=pd.qcut(c.revenue,4); print(c.groupby('revbin').won.agg(['mean','count']))
c['empbin']=pd.qcut(c.employees,4); print(c.groupby('empbin').won.agg(['mean','count']))
c['sub']=c.subsidiary_of.notna(); print(c.groupby('sub').won.agg(['mean','count']))
# close_value vs price
w=c[c.won==1]; print('close/price ratio', (w.close_value/w.sales_price).describe())
# monthly/quarter seasonality
c['cm']=c.close_date.dt.month; print(c.groupby('cm').won.agg(['mean','count']))
# open deals age at 2017-12-31
o=p[p.deal_stage=='Engaging'].copy(); ref=pd.Timestamp('2017-12-31'); o['age']=(ref-o.engage_date).dt.days
print('open engaging age\n',o.age.describe())
print(o.groupby(pd.cut(o.age,[-1,30,60,90,120,200,500])).size())
# agent x product interaction
ap=c.groupby(['sales_agent','product']).won.agg(['mean','count']); print('agent-product wr std',ap[ap['count']>=10]['mean'].std())
# repeat account: prior wins
print('open per agent', p[p.deal_stage.isin(['Engaging','Prospecting'])].groupby('sales_agent').size().describe())
