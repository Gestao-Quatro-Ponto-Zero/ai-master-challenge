import pandas as pd, numpy as np, sys
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
D=sys.argv[1]
p=pd.read_csv(f"{D}/sales_pipeline.csv"); a=pd.read_csv(f"{D}/accounts.csv")
pr=pd.read_csv(f"{D}/products.csv"); t=pd.read_csv(f"{D}/sales_teams.csv")
p['product']=p['product'].replace('GTXPro','GTX Pro')
for c in ['engage_date','close_date']: p[c]=pd.to_datetime(p[c])
p=p.merge(pr,on='product',how='left').merge(t,on='sales_agent',how='left').merge(a,on='account',how='left')
c=p[p.deal_stage.isin(['Won','Lost'])].copy().sort_values('engage_date'); c['won']=(c.deal_stage=='Won').astype(int)
# repeat-customer signal: prior won deals for account before this engage date
c['prior_wins']=0
for acc,g in c.groupby('account'):
    for idx,row in g.iterrows():
        c.loc[idx,'prior_wins']=((g.close_date<row.engage_date)&(g.won==1)).sum()
c['prior_same_prod']=0
for (acc,prod),g in c.groupby(['account','product']):
    for idx,row in g.iterrows():
        c.loc[idx,'prior_same_prod']=((g.close_date<row.engage_date)&(g.won==1)).sum()
c['eng_month']=c.engage_date.dt.month; c['eng_dow']=c.engage_date.dt.dayofweek
c['price_to_rev']=c.sales_price/(c.revenue*1e6)
cat=['sales_agent','product','manager','regional_office','sector','office_location']
num=['sales_price','revenue','employees','year_established','prior_wins','prior_same_prod','eng_month','eng_dow','price_to_rev']
X=pd.get_dummies(c[cat].astype(str)).join(c[num].fillna(-1))
y=c.won
cv=StratifiedKFold(5,shuffle=True,random_state=42)
gb=HistGradientBoostingClassifier(max_depth=3,learning_rate=0.05,max_iter=200,random_state=42)
print("GBM static features AUC:", cross_val_score(gb,X,y,cv=cv,scoring='roc_auc').mean().round(3))
lr=LogisticRegression(max_iter=2000)
print("LogReg static AUC:", cross_val_score(lr,X,y,cv=cv,scoring='roc_auc').mean().round(3))
Xt=c[['eng_month']].copy(); Xt['cycle']=(c.close_date-c.engage_date).dt.days
print("GBM cycle-only AUC (uses outcome timing, not available ex-ante):", cross_val_score(gb,Xt[['cycle']],y,cv=cv,scoring='roc_auc').mean().round(3))
print("prior_wins win rate:", c.groupby(pd.cut(c.prior_wins,[-1,0,2,5,10,100])).won.agg(['size','mean']).round(3).to_dict())
