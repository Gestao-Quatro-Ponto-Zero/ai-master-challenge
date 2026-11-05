import sys,json,re,pandas as pd,numpy as np
from sklearn.metrics import roc_auc_score
d=sys.argv[1]; corpus_path=sys.argv[2]
rng=np.random.default_rng(7)
p=pd.read_csv(f'{d}/sales_pipeline.csv',parse_dates=['engage_date','close_date']); p['product']=p['product'].replace({'GTXPro':'GTX Pro'})
a=pd.read_csv(f'{d}/accounts.csv'); pr=pd.read_csv(f'{d}/products.csv'); t=pd.read_csv(f'{d}/sales_teams.csv')
p=p.merge(pr,on='product',how='left').merge(t,on='sales_agent',how='left').merge(a,on='account',how='left')
c=p[p.deal_stage.isin(['Won','Lost'])].copy(); c['won']=(c.deal_stage=='Won').astype(int); c['cycle']=(c.close_date-c.engage_date).dt.days
# A. Is the 138-day ceiling stable over time?
print('A. max cycle by close month'); print(c.groupby(c.close_date.dt.to_period('M')).cycle.agg(['max','median','count']).T.to_string())
# B. Walk-forward factor gate. Rates from deals closed before T; test on deals closed in the next month.
c['size']=pd.qcut(c.revenue,4,labels=['q1','q2','q3','q4']).astype(str)
FACT=['sales_agent','product','sector','regional_office','manager','size','account']
months=pd.date_range('2017-06-01','2017-12-01',freq='MS')
def wf(df,col,k=20):
    rows=[]
    for T in months:
        tr=df[df.close_date<T]; te=df[(df.close_date>=T)&(df.close_date<T+pd.offsets.MonthBegin(1))]; g=tr.won.mean(); s=tr.groupby(col).won.agg(['sum','count']); r=(s['sum']+k*g)/(s['count']+k)
        x=te[col].map(r).fillna(g); rows.append((te.won.values,x.values))
    y=np.concatenate([q[0] for q in rows]); x=np.concatenate([q[1] for q in rows]); au=roc_auc_score(y,x)
    # bootstrap CI
    b=[]; n=len(y)
    for _ in range(300):
        i=rng.integers(0,n,n)
        if y[i].min()==y[i].max(): continue
        b.append(roc_auc_score(y[i],x[i]))
    return au,np.percentile(b,2.5),np.percentile(b,97.5),n
print('\nB. walk-forward AUC per factor (gate: lower bound > 0.55)')
for f in FACT:
    au,lo,hi,n=wf(c,f); print(f'{f:16s} AUC {au:.3f} [{lo:.3f},{hi:.3f}] n={n} gate={"ABRE" if lo>0.55 else "fechado"}')
# C. Can the gate open at all? plant a seller effect and measure, over repeats
print('\nC. planted seller effect: share of repeats in which the gate opens')
ag=c.sales_agent.unique()
for lift in [0,.05,.10,.15,.20,.30]:
    op=0;R=30;A=[]
    for _ in range(R):
        q=c.copy(); good=rng.choice(ag,size=len(ag)//3,replace=False); u=rng.random(len(q)); g=q.sales_agent.isin(good).values
        # flip lost→won with prob for good sellers; won→lost for the others, keeping the base rate roughly fixed
        q.loc[g&(q.won==0).values&(u<lift),'won']=1; q.loc[(~g)&(q.won==1).values&(u<lift/2),'won']=0
        au,lo,hi,n=wf(q,'sales_agent'); A.append(au); op+=lo>.55
    print(f'lift flip {lift:.2f}: gate open {op}/{R}, mean AUC {np.mean(A):.3f}')
# D. Switchback power: seller-week revenue, plant a lift in treated seller-weeks
print('\nD. switchback power on real seller-week revenue')
w=c[c.close_date>='2017-03-06'].copy(); w['wk']=w.close_date.dt.to_period('W').dt.start_time
tab=w[w.won==1].groupby(['sales_agent','wk']).close_value.sum().unstack(fill_value=0)
allw=sorted(w.wk.unique()); tab=tab.reindex(index=c.sales_agent.unique(),columns=allw,fill_value=0).astype(float)
print('sellers',tab.shape[0],'weeks',tab.shape[1],'mean rev per seller-week',round(tab.values.mean()),'sd',round(tab.values.std()),'zero share',round((tab.values==0).mean(),3))
def run(Y,treat):
    # two-way demean; diff in means of residuals
    R=Y-Y.mean(1,keepdims=True)-Y.mean(0,keepdims=True)+Y.mean(); return R[treat==1].mean()-R[treat==0].mean()
def assign(S,W):
    return np.array([rng.permutation(np.r_[np.ones(W//2),np.zeros(W-W//2)]) for _ in range(S)])
for W in [4,8,12,26]:
    out=[]
    for lift in [.05,.10,.20,.30,.50]:
        pw=0;R=200
        for _ in range(R):
            st=rng.integers(0,tab.shape[1]-W+1); Y=tab.values[:,st:st+W].copy(); tr=assign(Y.shape[0],W)
            Yt=Y*(1+lift*tr); obs=run(Yt,tr); null=[run(Yt,assign(Y.shape[0],W)) for _ in range(60)]
            pw+=(np.mean(np.abs(null)>=abs(obs))<.05)
        out.append(f'+{int(lift*100)}%:{pw/R:.2f}')
    print(f'{W} weeks: power', ' '.join(out))
# E. prior art in corpus
c_=json.load(open(corpus_path)); kw={'switchback':r'switchback','stepped':r'stepped[- ]wedge','grupo de controle':r'grupo[- ]controle|grupo de controle|control group','holdout':r'holdout','randomiz':r'randomiz|aleatoriz','experimento':r'experimento (controlad|embutid|randomi)','a/b':r'\ba/b\b|teste ab\b','gate de fator':r'(fator|factor|feature|sinal).{0,40}(desbloque|ativ[ao].{0,12}(quando|ap[oó]s|s[oó])|gate|portão|licen)','score aprende':r'(re)?calibra.{0,30}(semana|autom[aá]tic|cont[ií]nu)|aprende com|online learning|feedback loop|loop de feedback','pr[eé]-registr':r'pr[eé]-?regist','poder/mde':r'\bmde\b|poder estat|statistical power|minimum detectable|efeito m[ií]nimo'}
for k,r in kw.items():
    ids=[int(n) for n,v in c_.items() if re.search(r,v,re.I)]; print(f'{k:18s}{len(ids):4d}',sorted(ids)[:30])
for n in ['110','176','204','77','137','200']:
    v=c_.get(n,'')
    for m in list(re.finditer(r'switchback|randomiz|aleatoriz|grupo[- ]controle|grupo de controle',v,re.I))[:2]: print(f'  #{n}:',re.sub(r'\s+',' ',v[max(0,m.start()-170):m.end()+170]))
