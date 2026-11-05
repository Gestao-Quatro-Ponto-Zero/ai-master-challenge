import sys,json,re,pandas as pd,numpy as np
from sklearn.metrics import roc_auc_score
d=sys.argv[1]; corpus_path=sys.argv[2]; rng=np.random.default_rng(11)
p=pd.read_csv(f'{d}/sales_pipeline.csv',parse_dates=['engage_date','close_date']); p['product']=p['product'].replace({'GTXPro':'GTX Pro'})
a=pd.read_csv(f'{d}/accounts.csv'); pr=pd.read_csv(f'{d}/products.csv'); t=pd.read_csv(f'{d}/sales_teams.csv')
p=p.merge(pr,on='product',how='left').merge(t,on='sales_agent',how='left').merge(a,on='account',how='left')
c=p[p.deal_stage.isin(['Won','Lost'])].copy(); c['won']=(c.deal_stage=='Won').astype(int); c['cycle']=(c.close_date-c.engage_date).dt.days
c['size']=pd.qcut(c.revenue,4,labels=['q1','q2','q3','q4']).astype(str)
months=pd.date_range('2017-06-01','2017-12-01',freq='MS')
def folds(df,col,k=20):
    out=[]
    for T in months:
        tr=df[df.close_date<T]; te=df[(df.close_date>=T)&(df.close_date<T+pd.offsets.MonthBegin(1))]; g=tr.won.mean(); s=tr.groupby(col).won.agg(['sum','count']); r=(s['sum']+k*g)/(s['count']+k)
        out.append((te.won.values,te[col].map(r).fillna(g).values))
    return out
def within(fs):  # mean within-month AUC, weighted by size
    A=[];W=[]
    for y,x in fs:
        if y.min()!=y.max() and len(set(x))>1: A.append(roc_auc_score(y,x)); W.append(len(y))
    return np.average(A,weights=W)
def ci(fs,B=200):
    b=[]
    for _ in range(B):
        ss=[]
        for y,x in fs:
            i=rng.integers(0,len(y),len(y)); ss.append((y[i],x[i]))
        b.append(within(ss))
    return np.percentile(b,[2.5,97.5])
print('B. walk-forward, within-month AUC')
for f in ['sales_agent','product','sector','regional_office','manager','size','account']:
    fs=folds(c,f); au=within(fs); lo,hi=ci(fs); print(f'{f:16s}{au:.3f} [{lo:.3f},{hi:.3f}] gate(lo>.53)={"ABRE" if lo>.53 else "fechado"}')
print('\nC. planted seller gap, gate lo>.53')
ag=c.sales_agent.unique()
for lift in [0,.05,.10,.20,.30]:
    op=0;R=20;A=[];G=[]
    for _ in range(R):
        q=c.copy(); good=rng.choice(ag,size=len(ag)//3,replace=False); u=rng.random(len(q)); g=q.sales_agent.isin(good).values
        q.loc[g&(q.won==0).values&(u<lift),'won']=1; q.loc[(~g)&(q.won==1).values&(u<lift/2),'won']=0
        fs=folds(q,'sales_agent'); A.append(within(fs)); lo,_=ci(fs,B=60); op+=lo>.53; G.append(q[g].won.mean()-q[~g].won.mean())
    print(f'flip {lift:.2f}: real gap {np.mean(G)*100:.1f}pp, mean AUC {np.mean(A):.3f}, gate {op}/{R}')
# A2. calendar pattern detail
c['qm']=(c.close_date.dt.month-1)%3+1
print('\nA2. by month position in quarter (1=first)'); print(c.groupby('qm').agg(n=('won','size'),win=('won','mean'),cyc_med=('cycle','median'),cyc_max=('cycle','max')).round(3).to_string())
c['eng_q']=c.engage_date.dt.to_period('Q'); c['cl_q']=c.close_date.dt.to_period('Q'); print('same quarter engage/close by month position'); print(c.groupby('qm').apply(lambda g:(g.eng_q==g.cl_q).mean(),include_groups=False).round(3).to_dict())
print('win by cycle band within month position'); print(c.groupby(['qm',pd.cut(c.cycle,[0,14,60,100,140])],observed=True).won.agg(['mean','count']).round(3).to_string())
# Open deals: age at ref + next possible windows? count by age band
e=p[p.deal_stage=='Engaging'].copy(); ref=pd.Timestamp('2017-12-31'); e['age']=(ref-e.engage_date).dt.days
print('open Engaging age bands',pd.cut(e.age,[0,13,60,138,1000]).value_counts().sort_index().to_dict())
print('value <=138',e[e.age<=138].sales_price.sum(),'>138',e[e.age>138].sales_price.sum())
# F. deal-level experiment sizing
wk=c[c.close_date>='2017-03-06']; weekly=len(wk)/wk.close_date.dt.to_period('W').nunique(); base=c.won.mean(); print(f'\nF. closed/week {weekly:.0f}, base win {base:.3f}, median cycle {c.cycle.median()}')
for dp in [.03,.05,.10]:
    n=2*(1.96+.84)**2*base*(1-base)/dp**2; print(f'+{int(dp*100)}pp: {n:.0f} per arm; total {2*n:.0f}; weeks of closes {2*n/weekly:.1f}')
# zombies sampling: CI half width for resurrection rate
for n in [50,100,200]:
    for pp in [.05,.2,.5]:
        print(f'zombie sample n={n}, true {pp}: ±{1.96*np.sqrt(pp*(1-pp)/n)*100:.1f}pp',end='; ')
    print()
z=e[e.age>138]; print('zombies',len(z),'value',z.sales_price.sum(),'avg',round(z.sales_price.mean()),'by product',z.groupby('product').size().to_dict()); print('per seller',z.groupby('sales_agent').size().describe().round(1).to_dict())
# Prior art
C=json.load(open(corpus_path)); P={x['number']:x for x in json.load(open(corpus_path.replace('corpus.json','prs_plus.json')))}
is3=lambda n:'003' in P[n]['title'] or 'lead' in P[n]['title'].lower()
print('\nG. prior art, 003 only: lines on control/holdout/A-B/experiment')
pat=re.compile(r'grupo[- ]controle|grupo de controle|control group|holdout|\ba/b\b|teste ab\b|randomiz|aleatoriz|experimento|piloto',re.I)
for n,v in sorted(C.items(),key=lambda kv:int(kv[0])):
    n=int(n)
    if not is3(n): continue
    hits=[m for m in pat.finditer(v)]
    if not hits: continue
    seen=0;L=[]
    for m in hits:
        s=re.sub(r'\s+',' ',v[max(0,m.start()-90):m.end()+110])
        if 'submissions/' in s: continue
        L.append(s); seen+=1
        if seen>=2: break
    if L: print(f'#{n}:',' || '.join(L)[:430])
print('\nH. calendar pattern mentioned?')
for r in [r'primeiro m[eê]s do (tri|quarter)',r'first month of (the )?quarter',r'\b13 dias\b',r'calend[aá]rio.{0,50}(ciclo|artefato)|artefato.{0,50}calend',r'm[eê]s.{0,20}(trimestre).{0,60}ciclo']:
    print(r,sorted(int(n) for n,v in C.items() if re.search(r,v,re.I))[:25])
