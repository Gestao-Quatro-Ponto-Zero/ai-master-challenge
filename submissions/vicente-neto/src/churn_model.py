"""
RavenStack | Modelo preditivo de churn (painel de fotos mensais)
Pergunta: dada uma conta ativa na data D, ela terá o primeiro churn nos 90 dias seguintes?
- Uma linha por (conta, data D), D = 1o dia de cada mês, só contas cadastradas antes de D e sem churn até D.
- Variáveis usam SOMENTE dados com data <= D (sem vazamento). Uso: só registros a partir do cadastro.
- Rótulo: primeiro churn_event em (D, D+90].
- Validação temporal: treino D <= 2024-03-01, teste D em 2024-04..2024-10 (rótulo observável até 31/12/2024).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DATA as _DATA, OUT as _OUT
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.inspection import permutation_importance
IN = sys.argv[1] if len(sys.argv)>1 else _DATA
OUT= sys.argv[2] if len(sys.argv)>2 else _OUT
H=90
a=pd.read_csv(f'{IN}/ravenstack_accounts.csv',parse_dates=['signup_date'])
s=pd.read_csv(f'{IN}/ravenstack_subscriptions.csv',parse_dates=['start_date','end_date'])
f=pd.read_csv(f'{IN}/ravenstack_feature_usage.csv',parse_dates=['usage_date'])
t=pd.read_csv(f'{IN}/ravenstack_support_tickets.csv',parse_dates=['submitted_at'])
c=pd.read_csv(f'{IN}/ravenstack_churn_events.csv',parse_dates=['churn_date'])
first=c.groupby('account_id').churn_date.min(); a['first_churn']=a.account_id.map(first)
u=f.merge(s[['subscription_id','account_id']],on='subscription_id').merge(a[['account_id','signup_date']],on='account_id')
u=u[u.usage_date>=u.signup_date]
def snapshot(D):
    D=pd.Timestamp(D)
    act=a[(a.signup_date<D)&(a.first_churn.isna()|(a.first_churn>D))].copy()
    X=act[['account_id','industry','country','referral_source','plan_tier','seats','is_trial','signup_date']].copy()
    X['snapshot']=D; X['idade_dias']=(D-X.signup_date).dt.days
    # assinaturas conhecidas até D
    sd=s[s.start_date<=D]
    viva=sd[sd.end_date.isna()|(sd.end_date>D)]
    g=sd.groupby('account_id'); gv=viva.groupby('account_id')
    X['n_subs']=X.account_id.map(g.size()).fillna(0)
    X['n_subs_vivas']=X.account_id.map(gv.size()).fillna(0)
    X['n_subs_encerradas']=X['n_subs']-X['n_subs_vivas']
    X['mrr_vivo']=X.account_id.map(viva[~viva.is_trial].groupby('account_id').mrr_amount.sum()).fillna(0)
    X['n_upgrades']=X.account_id.map(g.upgrade_flag.sum()).fillna(0)
    X['n_downgrades']=X.account_id.map(g.downgrade_flag.sum()).fillna(0)
    X['pct_anual']=X.account_id.map(g.apply(lambda d:(d.billing_frequency=='annual').mean()))
    X['pct_auto_renew_off']=X.account_id.map(g.apply(lambda d:(~d.auto_renew_flag).mean()))
    X['tem_trial_vivo']=X.account_id.map(gv.is_trial.any()).fillna(False).astype(int)
    X['dias_desde_ultima_sub']=(D-X.account_id.map(g.start_date.max())).dt.days
    # uso válido até D
    ud=u[u.usage_date<=D]; dd=(D-ud.usage_date).dt.days
    w30=ud[dd<30]; w90=ud[dd<90]; p90=ud[(dd>=90)&(dd<180)]
    X['uso_30d']=X.account_id.map(w30.groupby('account_id').usage_count.sum()).fillna(0)
    X['uso_90d']=X.account_id.map(w90.groupby('account_id').usage_count.sum()).fillna(0)
    X['uso_90d_ant']=X.account_id.map(p90.groupby('account_id').usage_count.sum()).fillna(0)
    X['tend_uso']=(X.uso_90d-X.uso_90d_ant)/(X.uso_90d_ant+1)
    X['erros_90d_por_100']=100*X.account_id.map(w90.groupby('account_id').error_count.sum()).fillna(0)/(X.uso_90d+1)
    X['features_90d']=X.account_id.map(w90.groupby('account_id').feature_name.nunique()).fillna(0)
    X['beta_90d']=X.account_id.map(w90[w90.is_beta_feature].groupby('account_id').usage_count.sum()).fillna(0)/(X.uso_90d+1)
    X['dias_sem_uso']=(D-X.account_id.map(ud.groupby('account_id').usage_date.max())).dt.days
    X['uso_por_dia_vida']=X.account_id.map(ud.groupby('account_id').usage_count.sum()).fillna(0)/X.idade_dias.clip(lower=1)
    # tickets até D
    td=t[t.submitted_at<=D]; tdd=(D-td.submitted_at).dt.days; t90=td[tdd<90]
    X['tickets_90d']=X.account_id.map(t90.groupby('account_id').size()).fillna(0)
    X['tickets_total']=X.account_id.map(td.groupby('account_id').size()).fillna(0)
    X['escalados_90d']=X.account_id.map(t90.groupby('account_id').escalation_flag.sum()).fillna(0)
    X['urgentes_90d']=X.account_id.map(t90[t90.priority.isin(['urgent','high'])].groupby('account_id').size()).fillna(0)
    X['csat_medio']=X.account_id.map(td.groupby('account_id').satisfaction_score.mean())
    X['pct_sem_nota']=X.account_id.map(td.groupby('account_id').satisfaction_score.apply(lambda x:x.isna().mean()))
    X['resolucao_media_h']=X.account_id.map(td.groupby('account_id').resolution_time_hours.mean())
    X['primeira_resposta_min']=X.account_id.map(td.groupby('account_id').first_response_time_minutes.mean())
    # rótulo
    fc=act.set_index('account_id').first_churn
    X['churn_90d']=X.account_id.map(((fc>D)&(fc<=D+pd.Timedelta(days=H))).astype(int))
    return X
dates=pd.date_range('2023-04-01','2024-10-01',freq='MS')
P=pd.concat([snapshot(d) for d in dates],ignore_index=True)
CAT=['industry','country','referral_source','plan_tier']
NUM=['seats','is_trial','idade_dias','n_subs','n_subs_vivas','n_subs_encerradas','mrr_vivo','n_upgrades','n_downgrades','pct_anual','pct_auto_renew_off','tem_trial_vivo','dias_desde_ultima_sub',
     'uso_30d','uso_90d','uso_90d_ant','tend_uso','erros_90d_por_100','features_90d','beta_90d','dias_sem_uso','uso_por_dia_vida',
     'tickets_90d','tickets_total','escalados_90d','urgentes_90d','csat_medio','pct_sem_nota','resolucao_media_h','primeira_resposta_min']
def matrix(df,cols=None):
    X=pd.concat([df[NUM].astype(float),pd.get_dummies(df[CAT].astype(str),drop_first=False).astype(float)],axis=1)
    return X.reindex(columns=cols,fill_value=0) if cols is not None else X
tr=P[P.snapshot<=pd.Timestamp('2024-03-01')]; te=P[P.snapshot>=pd.Timestamp('2024-04-01')]
Xtr=matrix(tr); Xte=matrix(te,Xtr.columns); ytr=tr.churn_90d; yte=te.churn_90d

# ---------------- treino e avaliação ----------------
rng=np.random.default_rng(42)
def boot_auc(y,p,acc,n=500):
    # bootstrap por conta (fotos da mesma conta não são independentes)
    ids=acc.unique(); idx={k:np.where(acc.values==k)[0] for k in ids}; out=[]
    for _ in range(n):
        smp=np.concatenate([idx[k] for k in rng.choice(ids,len(ids))])
        if y.values[smp].min()==y.values[smp].max(): continue
        out.append(roc_auc_score(y.values[smp],p[smp]))
    return np.percentile(out,[2.5,97.5])
def lift(y,p,q=0.2):
    k=int(len(p)*q); top=np.argsort(-p)[:k]; return y.values[top].mean()/y.mean(), y.values[top].mean()
models={
 'Referência: só idade da conta':(['idade_dias'],make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000))),
 'Regressão logística (todas as variáveis)':(None,make_pipeline(SimpleImputer(),StandardScaler(),LogisticRegression(max_iter=5000,C=0.1))),
 'Gradient boosting (todas as variáveis)':(None,HistGradientBoostingClassifier(max_depth=3,learning_rate=0.05,max_iter=300,l2_regularization=1.0,random_state=1)),
 'Gradient boosting sem idade da conta':('noage',HistGradientBoostingClassifier(max_depth=3,learning_rate=0.05,max_iter=300,l2_regularization=1.0,random_state=1)),
}
res=[]; preds={}
for nm,(cols,mod) in models.items():
    if cols=='noage': c_=[x for x in Xtr.columns if x not in ('idade_dias','uso_por_dia_vida','dias_desde_ultima_sub')]
    elif cols is None: c_=list(Xtr.columns)
    else: c_=cols
    mod.fit(Xtr[c_],ytr); p=mod.predict_proba(Xte[c_])[:,1]; preds[nm]=(mod,c_,p)
    lo,hi=boot_auc(yte,p,te.account_id)
    l,prec=lift(yte,p)
    res.append(dict(modelo=nm,auc_teste=round(roc_auc_score(yte,p),3),auc_ic95=f"{lo:.3f}–{hi:.3f}",pr_auc=round(average_precision_score(yte,p),3),
                    taxa_base=round(yte.mean(),3),precisao_top20=round(prec,3),lift_top20=round(l,2),brier=round(brier_score_loss(yte,p),3)))
# modelo final candidato: log(idade)
lg=make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000)).fit(np.log1p(tr[['idade_dias']]),ytr)
p=lg.predict_proba(np.log1p(te[['idade_dias']]))[:,1]; lo,hi=boot_auc(yte,p,te.account_id); l,prec=lift(yte,p)
res.append(dict(modelo='Modelo final: log da idade da conta',auc_teste=round(roc_auc_score(yte,p),3),auc_ic95=f"{lo:.3f}–{hi:.3f}",pr_auc=round(average_precision_score(yte,p),3),
                taxa_base=round(yte.mean(),3),precisao_top20=round(prec,3),lift_top20=round(l,2),brier=round(brier_score_loss(yte,p),3)))
R=pd.DataFrame(res); print(R.to_string(index=False)); R.to_csv(f'{OUT}/model_results.csv',index=False)

# ---------------- ganho de cada variável sobre a idade (teste) ----------------
base=roc_auc_score(yte,p); gain=[]
for v in [c_ for c_ in NUM if c_ not in ('idade_dias',)]+CAT:
    A=tr.assign(lidade=np.log1p(tr.idade_dias)); B=te.assign(lidade=np.log1p(te.idade_dias))
    if v in CAT:
        XA=pd.concat([A[['lidade']],pd.get_dummies(A[v].astype(str)).astype(float)],axis=1); XB=pd.concat([B[['lidade']],pd.get_dummies(B[v].astype(str)).astype(float)],axis=1).reindex(columns=XA.columns,fill_value=0)
    else: XA=A[['lidade',v]].astype(float); XB=B[['lidade',v]].astype(float)
    m_=make_pipeline(SimpleImputer(),StandardScaler(),LogisticRegression(max_iter=2000)).fit(XA,ytr)
    gain.append(dict(variavel=v,ganho_auc_sobre_idade=round(roc_auc_score(yte,m_.predict_proba(XB)[:,1])-base,3)))
G=pd.DataFrame(gain).sort_values('ganho_auc_sobre_idade',ascending=False); G.to_csv(f'{OUT}/model_feature_gain.csv',index=False)

# ---------------- curva de risco por idade e calibração ----------------
bins=[0,30,60,90,180,365,10000]; lab=['0-30','31-60','61-90','91-180','181-365','366+']
cur=[]
for nm,d in [('treino (abr/23-mar/24)',tr),('teste (abr/24-out/24)',te)]:
    g=d.groupby(pd.cut(d.idade_dias,bins,labels=lab),observed=True).churn_90d.agg(['size','mean'])
    for k,r in g.iterrows(): cur.append(dict(periodo=nm,faixa_idade_dias=k,fotos=int(r['size']),churn_90d=round(r['mean'],3)))
pd.DataFrame(cur).to_csv(f'{OUT}/model_risk_by_age.csv',index=False)
dec=pd.DataFrame({'p':p,'y':yte.values}); dec['decil']=pd.qcut(dec.p.rank(method='first'),10,labels=range(1,11))
D_=dec.groupby('decil',observed=True).agg(fotos=('y','size'),prob_prevista=('p','mean'),churn_real=('y','mean')).round(3); D_.to_csv(f'{OUT}/model_test_deciles.csv')

# ---------------- modelo final: treina em todas as fotos rotuladas, recalibra no período recente ----------------
fin=make_pipeline(StandardScaler(),LogisticRegression(max_iter=2000)).fit(np.log1p(P[['idade_dias']]),P.churn_90d)
rec=P[P.snapshot>=pd.Timestamp('2024-05-01')]
from scipy.optimize import brentq
from scipy.special import logit, expit
z=fin.decision_function(np.log1p(rec[['idade_dias']]))
shift=brentq(lambda b: expit(z+b).mean()-rec.churn_90d.mean(),-5,5)   # ajusta o intercepto à taxa recente
Dn=pd.Timestamp('2025-01-01'); S=snapshot(Dn)
S['prob_churn_90d']=expit(fin.decision_function(np.log1p(S[['idade_dias']]))+shift).round(3)
S['faixa_risco']=pd.cut(S.prob_churn_90d,[0,0.25,0.35,1],labels=['menor','médio','maior'])
S['mrr_esperado_em_risco']=(S.prob_churn_90d*S.mrr_vivo).round(0)
sc=S.sort_values(['prob_churn_90d','mrr_vivo'],ascending=[False,False])[['account_id','industry','referral_source','plan_tier','signup_date','idade_dias','mrr_vivo','prob_churn_90d','faixa_risco','mrr_esperado_em_risco','uso_90d','tickets_90d','escalados_90d']]
sc['signup_date']=sc.signup_date.dt.strftime('%Y-%m-%d'); sc.to_csv(f'{OUT}/model_scores_2025-01-01.csv',index=False)
print('\nintercepto recalibrado:',round(shift,3),'| taxa recente',round(rec.churn_90d.mean(),3))
print('contas pontuadas',len(sc),'| prob média',round(sc.prob_churn_90d.mean(),3),'| churns esperados em 90d',round(sc.prob_churn_90d.sum(),1),'| MRR esperado em risco',int(sc.mrr_esperado_em_risco.sum()))
print(sc.faixa_risco.value_counts().to_dict())
print(D_.to_string()); print(G.head(5).to_string(index=False)); print(G.tail(3).to_string(index=False))
