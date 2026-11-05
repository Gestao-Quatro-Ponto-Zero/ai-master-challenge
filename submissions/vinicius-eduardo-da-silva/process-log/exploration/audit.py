import sys, pandas as pd
pd.set_option('display.width',200); pd.set_option('display.max_columns',50); pd.set_option('display.max_rows',100)
d=sys.argv[1]
a=pd.read_csv(f'{d}/accounts.csv'); pr=pd.read_csv(f'{d}/products.csv'); t=pd.read_csv(f'{d}/sales_teams.csv'); p=pd.read_csv(f'{d}/sales_pipeline.csv',parse_dates=['engage_date','close_date'])
print(pd.read_csv(f'{d}/metadata.csv').to_string())
for n,x in dict(accounts=a,products=pr,teams=t,pipeline=p).items():
    print('\n==',n,x.shape); print(x.head(3).to_string()); print(x.isna().sum()[lambda s:s>0].to_string())
print('\ndup opp',p.opportunity_id.duplicated().sum())
print(p.deal_stage.value_counts())
print('\nnulls by stage'); print(p.groupby('deal_stage')[['account','engage_date','close_date','close_value']].apply(lambda g:g.isna().sum()))
print('\nengage',p.engage_date.min(),p.engage_date.max(),'close',p.close_date.min(),p.close_date.max())
print('\nJOIN gaps')
print('products not in cat',set(p['product'])-set(pr['product']),'unused',set(pr['product'])-set(p['product']))
print('accounts not in cat',set(p.account.dropna())-set(a.account))
print('agents not in team',set(p.sales_agent)-set(t.sales_agent),'no deals',set(t.sales_agent)-set(p.sales_agent))
print(t.groupby(['regional_office','manager']).size())
print(a.subsidiary_of.notna().sum(),'subsidiaries'); print(a.sector.value_counts()); print(a.office_location.value_counts().head(5))
c=p[p.deal_stage.isin(['Won','Lost'])].copy(); c['won']=(c.deal_stage=='Won').astype(int); c['cycle']=(c.close_date-c.engage_date).dt.days
print('\nwin rate',c.won.mean(),'n',len(c)); print(c.groupby('deal_stage').cycle.describe()); print('value',c[c.won==1].close_value.describe())
print('lost close_value nonzero',(c[c.won==0].close_value>0).sum())
c['q']=c.close_date.dt.to_period('Q'); print(c.groupby('q').agg(n=('won','size'),wr=('won','mean'),rev=('close_value','sum')))
c['eq']=c.engage_date.dt.to_period('Q'); print(c.groupby('eq').agg(n=('won','size'),wr=('won','mean')))
print(p.groupby(p.engage_date.dt.to_period('M')).deal_stage.value_counts().unstack().fillna(0))
op=p[p.deal_stage=='Engaging'].copy(); snap=p[['engage_date','close_date']].max().max(); op['age']=(snap-op.engage_date).dt.days
print('\nsnap',snap); print(op.age.describe()); print('prospecting account nulls',p[p.deal_stage=='Prospecting'].account.isna().mean())
print('open by agent'); print(p[p.deal_stage.isin(['Engaging','Prospecting'])].groupby('sales_agent').deal_stage.value_counts().unstack().fillna(0).describe())
