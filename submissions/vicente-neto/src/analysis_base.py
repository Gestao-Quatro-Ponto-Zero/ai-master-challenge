import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
from scipy import stats
pd.set_option('display.width',250); pd.set_option('display.max_columns',50)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DATA as IN, OUT
a=pd.read_csv(f'{IN}/ravenstack_accounts.csv',parse_dates=['signup_date'])
s=pd.read_csv(f'{IN}/ravenstack_subscriptions.csv',parse_dates=['start_date','end_date'])
f=pd.read_csv(f'{IN}/ravenstack_feature_usage.csv',parse_dates=['usage_date'])
t=pd.read_csv(f'{IN}/ravenstack_support_tickets.csv',parse_dates=['submitted_at','closed_at'])
c=pd.read_csv(f'{IN}/ravenstack_churn_events.csv',parse_dates=['churn_date'])
m=pd.read_csv(f'{OUT}/accounts_master.csv',parse_dates=['signup_date','first_churn_date','cutoff_date'])
def sec(x): print('\n'+'='*8,x)
def chi(col,df=m,y='has_churn_event'):
    ct=pd.crosstab(df[col],df[y]); p=stats.chi2_contingency(ct)[1]
    r=df.groupby(col).agg(n=(y,'size'),churn_pct=(y,lambda x:round(100*x.mean(),1)),mrr=('mrr_active_sum','sum'))
    print(r.to_string()); print(f'  chi2 p={p:.3f}')
sec('A. TENDENCIA: churn por trimestre, contas e MRR')
q=m[m.has_churn_event].groupby('churn_quarter').agg(contas=('account_id','size'),mrr_cutoff=('mrr_at_cutoff','sum'),mrr_ativo=('mrr_active_sum','sum'))
print(q)
ev=c.assign(q=c.churn_date.dt.to_period('Q').astype(str)); print(ev.groupby('q').agg(eventos=('churn_event_id','size'),contas=('account_id','nunique'),react=('is_reactivation','sum'),refund=('refund_amount_usd','sum')))
sec('A2. Taxa por tenure vs calendario (hazard)')
mm=m.copy(); mm['ten_bin']=pd.cut(mm.tenure_days_at_cutoff,[-1,30,90,180,270,365,540,800])
print(mm.groupby('ten_bin').agg(n=('account_id','size'),churn=('has_churn_event','mean')).round(3))
c2=c.merge(a[['account_id','signup_date']],on='account_id'); c2['dias']=(c2.churn_date-c2.signup_date).dt.days
print('dias signup->churn (todos eventos):',c2.dias.describe().round(0).to_dict())
print('corr churn_date vs signup_date',np.corrcoef(c2.churn_date.astype('int64'),c2.signup_date.astype('int64'))[0,1].round(2))
print('churn por trimestre de signup'); chi('signup_quarter')
sec('B. SUBSCRIPTION-LEVEL churn (486 encerradas)')
s['q_end']=s.end_date.dt.to_period('Q').astype(str); print(s.groupby('q_end').size().to_dict())
for k in ['billing_frequency','auto_renew_flag','plan_tier','is_trial','downgrade_flag','upgrade_flag']:
    r=s.groupby(k).agg(n=('churn_flag','size'),end_pct=('churn_flag',lambda x:round(100*x.mean(),1))); p=stats.chi2_contingency(pd.crosstab(s[k],s.churn_flag))[1]; print(r.to_string(),f'p={p:.3f}')
sec('C. SEGMENTOS (conta, churn=has_churn_event)')
m['billing_mix']=pd.cut(m.pct_subs_annual,[-.01,.33,.66,1.0],labels=['mostly monthly','mixed','mostly annual'])
for k in ['referral_source','industry','plan_tier_account','country','size_band','billing_mix','is_trial_account']: print('--',k); chi(k)
sec('C2. Canal x Plano, canal x industria (celulas n>=15, top churn)')
x=m.groupby(['referral_source','plan_tier_account']).agg(n=('account_id','size'),ch=('has_churn_event','mean')).round(2); print(x[x.n>=15].sort_values('ch',ascending=False).head(5))
sec('D. SATISFACAO (CS)')
print('tickets nota nula %',round(100*t.satisfaction_score.isna().mean(),1),' valores',sorted(t.satisfaction_score.dropna().unique()))
ts=t.merge(m[['account_id','churn_status','first_churn_date']],on='account_id')
print(ts.groupby('churn_status').agg(tickets=('ticket_id','size'),csat=('satisfaction_score','mean'),pct_rated=('satisfaction_score',lambda x:x.notna().mean()),esc=('escalation_flag','mean'),res=('resolution_time_hours','mean'),frt=('first_response_time_minutes','mean')).round(3))
g1=m[m.has_churn_event].avg_csat.dropna(); g2=m[~m.has_churn_event].avg_csat.dropna(); print('CSAT conta MWU p=',round(stats.mannwhitneyu(g1,g2)[1],3),len(g1),len(g2))
print('contas sem ticket:',(~m.has_ticket).sum(),'churn deles',m[~m.has_ticket].has_churn_event.sum())
print('sem nota nenhuma (contas com ticket):',((m.n_tickets>0)&(m.n_tickets_rated==0)).sum(),' churn% ',round(100*m[(m.n_tickets>0)&(m.n_tickets_rated==0)].has_churn_event.mean(),1))
# tickets pre-churn: tickets nos 90d antes do churn vs janela equivalente retidas
tp=t.merge(m[['account_id','cutoff_date','has_churn_event']],on='account_id'); tp['d']=(tp.cutoff_date-tp.submitted_at).dt.days
w=tp[(tp.d>=0)&(tp.d<90)].groupby('account_id').agg(t90=('ticket_id','size'),esc90=('escalation_flag','sum'))
m2=m.merge(w,on='account_id',how='left').fillna({'t90':0,'esc90':0})
print('tickets nos 90d antes do corte (media):',m2.groupby('has_churn_event')[['t90','esc90']].mean().round(3).to_dict())
print('p MWU t90',round(stats.mannwhitneyu(m2[m2.has_churn_event].t90,m2[~m2.has_churn_event].t90)[1],3))
sec('E. USO (Produto)')
fu=f.merge(s[['subscription_id','account_id','plan_tier']],on='subscription_id').merge(a[['account_id','industry','referral_source','plan_tier','seats']].rename(columns={'plan_tier':'plan_acc'}),on='account_id').merge(m[['account_id','churn_status','size_band']],on='account_id')
fu['q']=fu.usage_date.dt.to_period('Q').astype(str)
tot=fu.groupby('q').usage_count.sum(); print('uso/trim',tot.to_dict()); print('var 1T23->4T24 %',round(100*(tot['2024Q4']/tot['2023Q1']-1),1),' 2024Q1->Q4',round(100*(tot['2024Q4']/tot['2024Q1']-1),1))
for k in ['plan_acc','industry','referral_source','size_band','churn_status']:
    p=fu.pivot_table(index=k,columns='q',values='usage_count',aggfunc='sum'); print('uso 2023T1->2024T4 por',k,(100*(p['2024Q4']/p['2023Q1']-1)).round(1).to_dict(),' | 2024Q1->Q4',(100*(p['2024Q4']/p['2024Q1']-1)).round(1).to_dict())
print('erros por 100 usos por trim',(100*fu.groupby('q').error_count.sum()/tot).round(2).to_dict())
sec('E2. uso pre-churn')
for col in ['usage_count_pre','error_per_100_uses_pre','distinct_features_pre','beta_share_pre','usage_trend_pct','days_since_last_usage_at_cutoff','usage_last90','usage_prev90']:
    g1=m[m.has_churn_event][col].dropna(); g2=m[~m.has_churn_event][col].dropna(); print(f'{col:35s} churn={g1.mean():.2f} ret={g2.mean():.2f} med {g1.median():.2f}/{g2.median():.2f} p={stats.mannwhitneyu(g1,g2)[1]:.3f}')
print('contas c/ queda uso >40% (90d vs prev90, prev90>0):'); d=m[m.usage_prev90>0]; 
dd=d.assign(queda=d.usage_trend_pct<-0.4); print(dd.groupby('queda').agg(n=('account_id','size'),churn=('has_churn_event','mean')).round(3))
sec('F. Reason codes vs comportamento')
r=c.merge(m[['account_id','n_tickets_pre','avg_csat_pre','n_tickets_escalated_pre','avg_resolution_hours_pre','distinct_features_pre','error_per_100_uses_pre','mrr_active_sum','n_downgrades_pre','seats_account','usage_count_pre']],on='account_id')
rr=r.groupby('reason_code')[['n_tickets_pre','avg_csat_pre','n_tickets_escalated_pre','avg_resolution_hours_pre','distinct_features_pre','error_per_100_uses_pre','mrr_active_sum','n_downgrades_pre']].mean().round(2); print(rr)
for col in ['n_tickets_pre','n_tickets_escalated_pre','mrr_active_sum','error_per_100_uses_pre']:
    grp=[x[col].dropna() for _,x in r.groupby('reason_code')]; print(col,'Kruskal p=',round(stats.kruskal(*grp)[1],3))
print('reason=support: media tickets_pre',r[r.reason_code=='support'].n_tickets_pre.mean().round(2),'vs resto',r[r.reason_code!='support'].n_tickets_pre.mean().round(2))
print('reason x feedback chi2 p=',round(stats.chi2_contingency(pd.crosstab(c.reason_code,c.feedback_text.fillna('NULL')))[1],3))
print('reason share',c.reason_code.value_counts(normalize=True).round(3).to_dict())
sec('G. Downgrades antes do churn (cruzando subs x churn_events)')
cs=c.merge(s[['account_id','start_date','downgrade_flag','upgrade_flag']],on='account_id'); cs['d']=(cs.churn_date-cs.start_date).dt.days
x=cs[(cs.d>=0)&(cs.d<=90)].groupby('churn_event_id').agg(dg=('downgrade_flag','any'),ug=('upgrade_flag','any')).reset_index()
c3=c.merge(x,on='churn_event_id',how='left').fillna({'dg':False,'ug':False})
print('flag evento vs subs (downgrade 90d):'); print(pd.crosstab(c3.preceding_downgrade_flag,c3.dg))
print('eventos com downgrade flag:',c.preceding_downgrade_flag.mean().round(3),' upgrade flag',c.preceding_upgrade_flag.mean().round(3))
print('churn por n_downgrades conta'); m['dg_bin']=m.n_downgrades.clip(upper=3); chi('dg_bin')
print('has downgrade vs churn'); m['has_dg']=m.n_downgrades>0; chi('has_dg')
sec('H. Refund & reativacao')
print('refund total',c.refund_amount_usd.sum().round(2),' eventos com refund>0',(c.refund_amount_usd>0).mean().round(3),' media',c[c.refund_amount_usd>0].refund_amount_usd.mean().round(2))
print('MRR total ativo',m.mrr_active_sum.sum(),' MRR contas c/ churn (ativo)',m[m.has_churn_event].mrr_active_sum.sum(),' share',round(m[m.has_churn_event].mrr_active_sum.sum()/m.mrr_active_sum.sum(),3))
print('reativacao eventos',c.is_reactivation.sum(),'; contas com >=2 eventos',(m.n_churn_events>=2).sum())
sec('I. Concentracao de MRR')
ms=m.sort_values('mrr_active_sum',ascending=False); print('top10% contas share MRR',round(ms.head(50).mrr_active_sum.sum()/ms.mrr_active_sum.sum(),3),' churn top50',ms.head(50).has_churn_event.mean(),' bottom',ms.tail(450).has_churn_event.mean().round(3))
chi('mrr_band')
sec('J. Modelo: ha sinal? (CV AUC, features pre-corte, sem tenure/mrr_at_cutoff)')
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
num=['seats_account','n_subs','pct_subs_annual','n_downgrades','n_upgrades','n_subs_auto_renew_off','mrr_active_sum','usage_count','error_per_100_uses','distinct_features','beta_share','n_tickets','pct_tickets_rated','avg_csat','pct_tickets_escalated','avg_resolution_hours','avg_first_response_min']
X=pd.get_dummies(m[num+['referral_source','industry','country','plan_tier_account']],drop_first=True); y=m.has_churn_event.astype(int)
cv=StratifiedKFold(5,shuffle=True,random_state=1)
for nm,mod in [('logit',make_pipeline(SimpleImputer(),StandardScaler(),LogisticRegression(max_iter=1000))),('gbm',make_pipeline(SimpleImputer(),GradientBoostingClassifier(n_estimators=100,max_depth=2,random_state=1)))]:
    sc=cross_val_score(mod,X,y,cv=cv,scoring='roc_auc'); print(nm,'AUC',sc.mean().round(3),sc.round(2))
