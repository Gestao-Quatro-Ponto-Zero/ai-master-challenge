import pandas as pd, numpy as np
a=pd.read_csv('ravenstack_accounts.csv',parse_dates=['signup_date'])
s=pd.read_csv('ravenstack_subscriptions.csv',parse_dates=['start_date','end_date'])
u=pd.read_csv('ravenstack_feature_usage.csv',parse_dates=['usage_date'])
t=pd.read_csv('ravenstack_support_tickets.csv',parse_dates=['submitted_at','closed_at'])
c=pd.read_csv('ravenstack_churn_events.csv',parse_dates=['churn_date'])

import json
from scipy import stats
OUT={}
END=pd.Timestamp('2024-12-31')
sig=a.set_index('account_id').signup_date
s['life']=(s.end_date-s.start_date).dt.days
s['e60']=s.churn_flag&(s.life<=60)
s['first']=s.groupby('account_id').start_date.rank(method='first')==1
# 1. quarterly: counts and rates
rows=[]
for q in pd.period_range('2023Q3','2024Q4',freq='Q'):
    st,en=q.start_time,q.end_time
    b=s[(s.start_date<st)&((s.end_date.isna())|(s.end_date>=st))]
    allch=s[(s.end_date>=st)&(s.end_date<=en)]
    bch=b[b.end_date<=en]
    newq=s[(s.start_date>=st)&(s.start_date<=en)]
    rows.append(dict(q=str(q),churned_subs=int(len(allch)),churned_mrr=int(allch.mrr_amount.sum()),base=int(len(b)),base_rate=round(len(bch)/len(b)*100,1),mrr_rate=round(bch.mrr_amount.sum()/b.mrr_amount.sum()*100,1),new_subs=int(len(newq)),churn_events=int(((c.churn_date>=st)&(c.churn_date<=en)).sum())))
OUT['quarters']=rows
# 2. monthly hazard new vs mature
hz=[]
for m in pd.period_range('2023-07','2024-12',freq='M'):
    st,en=m.start_time,m.end_time
    act=s[(s.start_date<st)&((s.end_date.isna())|(s.end_date>=st))].copy()
    new=(st-act.start_date).dt.days<=60
    ch=act.end_date<=en
    hz.append(dict(m=str(m),new_rate=round(ch[new].mean()*100,2),old_rate=round(ch[~new].mean()*100,2),new_n=int(new.sum()),old_n=int((~new).sum()),new_mrr_rate=round((act.mrr_amount*ch)[new].sum()/act.mrr_amount[new].sum()*100,2),old_mrr_rate=round((act.mrr_amount*ch)[~new].sum()/act.mrr_amount[~new].sum()*100,2)))
OUT['hazard']=hz
def hzp(months):
    R=[]
    for m in months:
        st,en=m.start_time,m.end_time
        act=s[(s.start_date<st)&((s.end_date.isna())|(s.end_date>=st))].copy()
        act['new']=(st-act.start_date).dt.days<=60; act['ch']=act.end_date<=en; R.append(act)
    R=pd.concat(R)
    g={}
    for k,d in R.groupby('new'):
        g['new' if k else 'old']=dict(n=int(len(d)),rate=round(d.ch.mean()*100,2),mrr=int(d.mrr_amount.sum()),chm=int((d.mrr_amount*d.ch).sum()),mrr_rate=round((d.mrr_amount*d.ch).sum()/d.mrr_amount.sum()*100,2))
    return g
OUT['hz_periods']={'2023H2':hzp(pd.period_range('2023-07','2023-12',freq='M')),'2024H1':hzp(pd.period_range('2024-01','2024-06',freq='M')),'2024JulNov':hzp(pd.period_range('2024-07','2024-11',freq='M')),'2024Dec':hzp(pd.period_range('2024-12','2024-12',freq='M')),'2024H2':hzp(pd.period_range('2024-07','2024-12',freq='M'))}
# 3. early churn by first vs expansion and cohort
y=s[s.start_date<='2024-10-31'].copy(); y['coh']=np.where(y.start_date>='2024-07-01','H2-24','antes')
g=y.groupby(['coh','first']).e60.agg(['size','sum','mean']).reset_index()
OUT['first_vs_exp']=[dict(coh=r.coh,first=bool(r['first']),n=int(r['size']),churn=int(r['sum']),rate=round(r['mean']*100,1)) for _,r in g.iterrows()]
e=y[~y['first']]; OUT['p_exp']=float(stats.fisher_exact(pd.crosstab(e.coh,e.e60)).pvalue)
h=y[y.coh=='H2-24']; OUT['p_first_vs_exp']=float(stats.fisher_exact(pd.crosstab(h['first'],h.e60)).pvalue)
OUT['share_exp_H2']=round(1-h['first'].mean(),3)
# early churn by plan
OUT['e60_plan']=y.groupby(['coh','plan_tier']).e60.mean().mul(100).round(1).unstack().to_dict()
xx=y[y.coh=='H2-24'].merge(a[['account_id','industry','referral_source']],on='account_id')
OUT['e60_seg_p']={col:round(float(stats.chi2_contingency(pd.crosstab(xx[col],xx.e60)).pvalue),2) for col in ['industry','referral_source','plan_tier','billing_frequency','auto_renew_flag']}
OUT['e60_industry']=xx.groupby('industry').e60.mean().mul(100).round(1).to_dict()
# Q4 churned MRR composition
q4=s[s.churn_flag&(s.end_date>='2024-10-01')]
OUT['q4']=dict(mrr=int(q4.mrr_amount.sum()),mrr_early=int(q4[q4.life<=60].mrr_amount.sum()),n=int(len(q4)),n_early=int((q4.life<=60).sum()),ent_mrr=int(q4[q4.plan_tier=='Enterprise'].mrr_amount.sum()),median_life=float(q4.life.median()))
q3=s[s.churn_flag&(s.end_date>='2024-07-01')&(s.end_date<'2024-10-01')]
OUT['q3_mrr']=int(q3.mrr_amount.sum())
OUT['plan_q']=s[s.churn_flag&(s.end_date>='2024-01-01')].assign(q=lambda d:d.end_date.dt.to_period('Q').astype(str)).groupby(['q','plan_tier']).mrr_amount.sum().unstack().fillna(0).astype(int).to_dict(orient='index')
# 4. usage per seat valid
uu=u.merge(s[['subscription_id','account_id','plan_tier']],on='subscription_id')
OUT['usage_before_signup']=round(float((uu.usage_date<uu.account_id.map(sig)).mean()),3)
tt=t.copy(); OUT['tickets_before_signup']=round(float((tt.submitted_at<tt.account_id.map(sig)).mean()),3)
OUT['usage_before_substart']=round(float((u.merge(s[['subscription_id','start_date']],on='subscription_id').pipe(lambda d:d.usage_date<d.start_date)).mean()),3)
v=uu[uu.usage_date>=uu.account_id.map(sig)]
tv=t[t.submitted_at>=t.account_id.map(sig)]
ur=[]
for q in pd.period_range('2023Q1','2024Q4',freq='Q'):
    st,en=q.start_time,q.end_time
    act=s[(s.start_date<=en)&((s.end_date.isna())|(s.end_date>=st))]
    uq=v[(v.usage_date>=st)&(v.usage_date<=en)]
    ur.append(dict(q=str(q),seats=int(act.seats.sum()),subs=int(len(act)),usage=int(uq.usage_count.sum()),usage_raw=int(u[(u.usage_date>=st)&(u.usage_date<=en)].usage_count.sum()),per_seat=round(uq.usage_count.sum()/act.seats.sum(),3),tickets=int(((t.submitted_at>=st)&(t.submitted_at<=en)).sum()),tickets_valid=int(((tv.submitted_at>=st)&(tv.submitted_at<=en)).sum())))
OUT['usage']=ur
ss=s.merge(a[['account_id','industry']],on='account_id')
def ps(col):
    out={}
    for q in ['2024Q1','2024Q4']:
        p=pd.Period(q); st,en=p.start_time,p.end_time
        act=ss[(ss.start_date<=en)&((ss.end_date.isna())|(ss.end_date>=st))]
        vv=v.merge(a[['account_id','industry']],on='account_id') if col=='industry' else v
        uq=vv[(vv.usage_date>=st)&(vv.usage_date<=en)]
        out[q]=(uq.groupby(col).usage_count.sum()/act.groupby(col).seats.sum()).round(3).to_dict()
    return out
OUT['per_seat_plan']=ps('plan_tier'); OUT['per_seat_ind']=ps('industry')
# 5. CSAT & tickets
OUT['csat_dist']={str(k):int(v_) for k,v_ in t.satisfaction_score.value_counts(dropna=False).items()}
OUT['csat_mean']=round(float(t.satisfaction_score.mean()),2)
OUT['csat_q']=t.groupby(t.submitted_at.dt.to_period('Q').astype(str)).satisfaction_score.mean().round(2).to_dict()
ch_acc=set(c.account_id)
tt['ch']=tt.account_id.isin(ch_acc)
OUT['csat_churn_vs_not']=tt.groupby('ch').satisfaction_score.mean().round(2).rename({True:'churn',False:'nochurn'}).to_dict()
pre=[]
for _,r in c.iterrows():
    d=tv[(tv.account_id==r.account_id)&(tv.submitted_at<=r.churn_date)&(tv.submitted_at>r.churn_date-pd.Timedelta(days=90))]
    pre.append(len(d))
pre=np.array(pre); OUT['pre_churn_tix']=dict(mean=round(pre.mean(),2),share_zero=round((pre==0).mean(),3))
# baseline: valid tickets per account per 90d of account life
life_days=(END-a.signup_date).dt.days.clip(lower=1).sum()
OUT['baseline_tix_90']=round(len(tv)/life_days*90,2)
ec=s[s.e60]; hits=0
for _,r in ec.iterrows():
    hits+=((tv.account_id==r.account_id)&(tv.submitted_at>=r.start_date)&(tv.submitted_at<=r.end_date)).any()
OUT['early_no_ticket']=round(1-hits/len(ec),3)
# 6. exit reasons
mp={'pricing':'too expensive','budget':'too expensive','features':'missing features','competitor':'switched to competitor'}
cc=c[c.feedback_text.notna()&c.reason_code.isin(mp)]
OUT['reason_consistent']=round(float((cc.reason_code.map(mp)==cc.feedback_text).mean()),3)
OUT['reason_unknown_blank']=round(float(((c.reason_code=='unknown')|c.feedback_text.isna()).mean()),3)
OUT['reason_counts']=c.reason_code.value_counts().to_dict()
OUT['reason_p']=round(float(stats.chi2_contingency(pd.crosstab(c.reason_code,c.feedback_text.fillna('blank'))).pvalue),2)
# 7. churn definitions
OUT['defs']=dict(acct_flag=int(a.churn_flag.sum()),event_accts=int(c.account_id.nunique()),sub_churn_accts=int(s[s.churn_flag].account_id.nunique()),acct_with_active=int(s[s.end_date.isna()].account_id.nunique()),overlap_flag_event=int(len(set(a[a.churn_flag].account_id)&set(c.account_id))),reactivations=int(c.is_reactivation.sum()))
# 8. logo churn by segment (accounts flag) with p
OUT['logo_seg']={}
for col in ['industry','referral_source','plan_tier','country']:
    OUT['logo_seg'][col]=dict(rates=a.groupby(col).churn_flag.mean().mul(100).round(1).to_dict(),n=a.groupby(col).size().to_dict(),p=round(float(stats.chi2_contingency(pd.crosstab(a[col],a.churn_flag)).pvalue),3))
# MRR concentration
act=s[s.end_date.isna()]
am=act.groupby('account_id').mrr_amount.sum().sort_values(ascending=False)
OUT['mrr_total']=int(am.sum()); OUT['top10pct_share']=round(am.head(50).sum()/am.sum(),3)
OUT['mrr_by_plan']=act.groupby('plan_tier').mrr_amount.sum().astype(int).to_dict()
json.dump(OUT,open('out.json','w'),indent=1,default=str)
print(json.dumps(OUT,indent=1,default=str)[:6000])
