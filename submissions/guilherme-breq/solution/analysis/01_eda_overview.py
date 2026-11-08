import pandas as pd
d='../data/'
p=pd.read_csv(d+'sales_pipeline.csv',parse_dates=['engage_date','close_date'])
a=pd.read_csv(d+'accounts.csv'); pr=pd.read_csv(d+'products.csv'); t=pd.read_csv(d+'sales_teams.csv')
print(p.deal_stage.value_counts(dropna=False))
print(p.isna().sum())
print(sorted(p['product'].unique()), sorted(pr['product']))
print('acct not in accounts:', set(p.account.dropna())-set(a.account))
print('agent not in teams:', set(p.sales_agent)-set(t.sales_agent))
print(p.engage_date.min(),p.engage_date.max(),p.close_date.min(),p.close_date.max())
c=p[p.deal_stage.isin(['Won','Lost'])]
print('win rate',(c.deal_stage=='Won').mean())
print(p[p.deal_stage=='Won'].close_value.describe())
print(p.groupby('deal_stage')[['engage_date','close_date']].agg(lambda s:s.notna().sum()))
