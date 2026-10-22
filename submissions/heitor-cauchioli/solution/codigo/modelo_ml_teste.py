import pandas as pd, numpy as np
a=pd.read_csv('ravenstack_accounts.csv',parse_dates=['signup_date'])
s=pd.read_csv('ravenstack_subscriptions.csv',parse_dates=['start_date','end_date'])
u=pd.read_csv('ravenstack_feature_usage.csv',parse_dates=['usage_date'])
t=pd.read_csv('ravenstack_support_tickets.csv',parse_dates=['submitted_at','closed_at'])
c=pd.read_csv('ravenstack_churn_events.csv',parse_dates=['churn_date'])

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
sig=a.set_index('account_id').signup_date
uu=u.merge(s[['subscription_id','account_id']],on='subscription_id')
uu=uu[uu.usage_date>=uu.account_id.map(sig)]
tv=t[t.submitted_at>=t.account_id.map(sig)]
def build(cut):
    cut=pd.Timestamp(cut); A=a[a.signup_date<=cut].set_index('account_id').copy()
    S=s[s.start_date<=cut]; act=S[(S.end_date.isna())|(S.end_date>cut)]
    A['mrr']=act.groupby('account_id').mrr_amount.sum().reindex(A.index).fillna(0)
    A['act_seats']=act.groupby('account_id').seats.sum().reindex(A.index).fillna(0)
    A['n_act']=act.groupby('account_id').size().reindex(A.index).fillna(0)
    new90=act[act.start_date>cut-pd.Timedelta(days=90)]
    A['new_subs_90']=new90.groupby('account_id').size().reindex(A.index).fillna(0)
    A['share_new']=A.new_subs_90/A.n_act.replace(0,np.nan)
    A['trial_share']=act.groupby('account_id').is_trial.mean().reindex(A.index)
    A['autorenew_share']=act.groupby('account_id').auto_renew_flag.mean().reindex(A.index)
    A['monthly_share']=act.groupby('account_id').billing_frequency.apply(lambda x:(x=='monthly').mean()).reindex(A.index)
    A['down_ever']=S.groupby('account_id').downgrade_flag.sum().reindex(A.index).fillna(0)
    A['up_ever']=S.groupby('account_id').upgrade_flag.sum().reindex(A.index).fillna(0)
    C=c[c.churn_date<=cut]
    A['churn_ev_180']=C[C.churn_date>cut-pd.Timedelta(days=180)].groupby('account_id').size().reindex(A.index).fillna(0)
    A['churn_ev_all']=C.groupby('account_id').size().reindex(A.index).fillna(0)
    A['subs_churned_180']=S[(S.end_date<=cut)&(S.end_date>cut-pd.Timedelta(days=180))].groupby('account_id').size().reindex(A.index).fillna(0)
    U=uu[(uu.usage_date<=cut)&(uu.usage_date>cut-pd.Timedelta(days=90))]
    A['use90']=U.groupby('account_id').usage_count.sum().reindex(A.index).fillna(0)
    A['use_per_seat']=A.use90/A.act_seats.replace(0,np.nan)
    A['err_rate']=(U.groupby('account_id').error_count.sum()/U.groupby('account_id').usage_count.sum()).reindex(A.index)
    T=tv[(tv.submitted_at<=cut)&(tv.submitted_at>cut-pd.Timedelta(days=180))]
    A['tix180']=T.groupby('account_id').size().reindex(A.index).fillna(0)
    A['esc180']=T.groupby('account_id').escalation_flag.sum().reindex(A.index).fillna(0)
    A['csat180']=T.groupby('account_id').satisfaction_score.mean().reindex(A.index)
    A['frt180']=T.groupby('account_id').first_response_time_minutes.mean().reindex(A.index)
    A['tenure']=(cut-A.signup_date).dt.days
    # target: any subscription of account ends (churn) in next 90d, MRR lost
    nxt=s[(s.end_date>cut)&(s.end_date<=cut+pd.Timedelta(days=90))]
    A['y']=A.index.isin(nxt.account_id)
    A['y_mrr']=nxt.groupby('account_id').mrr_amount.sum().reindex(A.index).fillna(0)
    return A
NUM=['mrr','act_seats','n_act','new_subs_90','share_new','trial_share','autorenew_share','monthly_share','down_ever','up_ever','churn_ev_180','churn_ev_all','subs_churned_180','use90','use_per_seat','err_rate','tix180','esc180','csat180','frt180','tenure','seats']
CAT=['industry','referral_source','plan_tier','country']
def X(A,cols=None):
    d=pd.get_dummies(A[NUM+CAT],columns=CAT,dtype=float)
    d=d.fillna(d.median(numeric_only=True)).fillna(0)
    if cols is not None: d=d.reindex(columns=cols,fill_value=0)
    return d

if __name__ == "__main__":
    tr = pd.concat([build(c_) for c_ in ['2024-03-31', '2024-06-30']]); te = build('2024-09-30')
    Xtr = X(tr); Xte = X(te, Xtr.columns)
    for nm, mdl in [('logit', make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=2000))),
                    ('gbm', GradientBoostingClassifier(n_estimators=150, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0))]:
        mdl.fit(Xtr, tr.y); print(nm, 'AUC', round(roc_auc_score(te.y, mdl.predict_proba(Xte)[:, 1]), 3))
