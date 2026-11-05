import sys, pandas as pd, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, brier_score_loss
d=sys.argv[1]
p=pd.read_csv(f'{d}/sales_pipeline.csv',parse_dates=['engage_date','close_date']); p['product']=p['product'].replace({'GTXPro':'GTX Pro'})
a=pd.read_csv(f'{d}/accounts.csv'); pr=pd.read_csv(f'{d}/products.csv'); t=pd.read_csv(f'{d}/sales_teams.csv')
p=p.merge(pr,on='product',how='left').merge(t,on='sales_agent',how='left').merge(a,on='account',how='left')
ref=p.close_date.max()
c=p[p.deal_stage.isin(['Won','Lost'])].copy(); c['won']=(c.deal_stage=='Won').astype(int); c['cycle']=(c.close_date-c.engage_date).dt.days
e=p[p.deal_stage=='Engaging'].copy(); e['age']=(ref-e.engage_date).dt.days
mx=c.cycle.max(); print('max closed cycle',mx,'p99',c.cycle.quantile(.99),'p95',c.cycle.quantile(.95))
for th in [90,120,138]: print(f'Engaging age>{th}:',(e.age>th).sum(),f'{(e.age>th).mean():.1%}', 'list value',e[e.age>th].sales_price.sum())
print('Engaging total list value',e.sales_price.sum(),'mean age',e.age.mean()); print('Engaging age<=138 n',(e.age<=138).sum())
# survival/censoring-aware: at-risk at age a counts closed with cycle>=a + open with age>=a
print('\nage a | closed after a | open older than a | win rate if closed after a | share closing within next 30d (of those observable)')
for A in [0,7,14,30,60,90,120,138]:
    cl=c[c.cycle>=A]; op=e[e.age>=A]
    obs=c[(c.cycle>=A)&(c.engage_date+pd.to_timedelta(A+30,'D')<=ref)]; opobs=e[(e.age>=A+30)]
    den=len(obs)+len(opobs); n30=(obs.cycle<A+30).sum()
    print(A,len(cl),len(op),round(cl.won.mean(),3),round(n30/den,3) if den else None)
# quarter-end
c['qe']=c.close_date.dt.month.isin([3,6,9,12]); print('\nwin rate by qtr-end close month',c.groupby('qe').won.agg(['mean','count']))
c['mq']=c.close_date.dt.month%3
print('won/lost per month position',c.groupby('mq').won.agg(['sum','count']))
print('by close day-of-month within qtr end',c[c.qe].groupby(pd.cut(c[c.qe].close_date.dt.day,[0,10,20,31])).won.agg(['mean','count']))
# temporal backtest, at-engage features only
cut=pd.Timestamp('2017-09-01')
tr=c[c.close_date<cut].copy(); te=c[c.engage_date>=cut].copy()
print('\ntrain',len(tr),tr.won.mean(),'test',len(te),te.won.mean())
for df in (tr,te):
    df['age_yrs']=df.engage_date.dt.year-df.year_established; df['log_rev']=np.log1p(df.revenue); df['log_emp']=np.log1p(df.employees); df['log_price']=np.log1p(df.sales_price)
    df['has_parent']=df.subsidiary_of.notna().astype(int); df['eng_month']=df.engage_date.dt.month; df['eng_mq']=df.engage_date.dt.month%3
# history-based rates from train only
gl=tr.won.mean()
def rate(col,k=20):
    s=tr.groupby(col).won.agg(['sum','count']); return ((s['sum']+k*gl)/(s['count']+k))
for col in ['sales_agent','account','product','sector']:
    r=rate(col)
    for df in (tr,te): df['r_'+col]=df[col].map(r).fillna(gl)
tr['ap']=tr.sales_agent+'|'+tr['product']; te['ap']=te.sales_agent+'|'+te['product']
r=rate('ap',10); tr['r_ap']=tr.ap.map(r).fillna(gl); te['r_ap']=te.ap.map(r).fillna(gl)
num=['log_rev','log_emp','log_price','has_parent','age_yrs','r_sales_agent','r_account','r_product','r_sector','r_ap']
cat=['sector','product','regional_office','manager']
def ev(name,m,cols):
    m.fit(tr[cols],tr.won); s=m.predict_proba(te[cols])[:,1]
    q=pd.qcut(s,5,labels=False,duplicates='drop'); tb=te.won.groupby(q).mean().round(3).to_dict()
    print(f'{name:38s} AUC {roc_auc_score(te.won,s):.3f} Brier {brier_score_loss(te.won,s):.3f} quintiles {tb}')
    return s
print('base Brier',brier_score_loss(te.won,np.full(len(te),gl)))
ct=ColumnTransformer([('n',StandardScaler(),num),('c',OneHotEncoder(handle_unknown='ignore'),cat)])
ev('Logistic (at-engage)',make_pipeline(ct,LogisticRegression(max_iter=2000,C=.5)),num+cat)
ev('Logistic (agent rate only)',make_pipeline(StandardScaler(),LogisticRegression()),['r_sales_agent'])
ev('Logistic (agent+account rates)',make_pipeline(StandardScaler(),LogisticRegression()),['r_sales_agent','r_account'])
ev('GBM (at-engage)',HistGradientBoostingClassifier(max_depth=3,max_iter=150,learning_rate=.05,random_state=0),num)
# Sensitivity: rolling splits
print('\nrolling, logistic rates:')
for cu in ['2017-06-01','2017-07-01','2017-08-01','2017-09-01','2017-10-01']:
    cu=pd.Timestamp(cu); a_=c[c.close_date<cu]; b_=c[c.engage_date>=cu]; g=a_.won.mean()
    s=a_.groupby('sales_agent').won.agg(['sum','count']); r=((s['sum']+20*g)/(s['count']+20))
    x=b_.sales_agent.map(r).fillna(g)
    print(cu.date(),len(a_),len(b_),'AUC agent rate',round(roc_auc_score(b_.won,x),3))
# Timing leakage test: cycle+close month power (leaky features - informational)
te2=te.copy(); te2['qe']=te2.close_date.dt.month.isin([3,6,9,12]).astype(int); print('\nLEAKY qtr-end close alone AUC',round(roc_auc_score(te2.won,te2.qe),3),' cycle alone AUC',round(roc_auc_score(te2.won,te2.cycle),3))
# Value concentration
print('\nvalue share by product among open'); o=p[p.deal_stage.isin(['Engaging','Prospecting'])]; print(o.groupby('product').sales_price.agg(['sum','count']).sort_values('sum',ascending=False))
print('open total',o.sales_price.sum(),'; won total',c.close_value.sum())
c['ev_price']=c.sales_price; print('corr price with won',c[['sales_price','won']].corr().iloc[0,1])
# effort on lost
print('lost deal-days',c[c.won==0].cycle.sum(),'won deal-days',c[c.won==1].cycle.sum(), 'share lost',round(c[c.won==0].cycle.sum()/c.cycle.sum(),3))
print('lost under 14d',(c[c.won==0].cycle<=14).mean(),'won under 14d',(c[c.won==1].cycle<=14).mean())
