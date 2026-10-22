"""Gera evidence.csv (cada número do relatório, com fonte, tabelas cruzadas e teste) e at_risk_accounts.csv"""
import os
__file__ = os.path.abspath(__file__)
exec(open(os.path.join(os.path.dirname(__file__),'analysis_base.py')).read().split("sec('A. TENDENCIA")[0])
E=[]
def add(i,insight,value,tables,test=''): E.append(dict(id=i,insight=insight,valor=value,tabelas_cruzadas=tables,teste=test))
Q=lambda p:str(p)
# --- base
ev=c.assign(q=c.churn_date.dt.to_period('Q').astype(str)).groupby('q').size()
add('E01','Eventos de churn 1T23 -> 4T24',f"{ev['2023Q1']} -> {ev['2024Q4']} por trimestre",'churn_events')
def hazard(df,qq):
    # base correta: contas já ativas no início do trimestre (signup antes do trimestre, sem churn antes)
    st,en=pd.Period(qq).start_time,pd.Period(qq).end_time
    base=df[(df.signup_date<st)&(df.first_churn_date.isna()|(df.first_churn_date>=st))]
    num=((df.first_churn_date>=st)&(df.first_churn_date<=en)&(df.signup_date<st)).sum()
    return 100*num/max(len(base),1),len(base)
h1,b1=hazard(m,'2023Q4'); h2,b2=hazard(m,'2024Q4')
add('E02','Taxa trimestral de 1o churn (base = contas já ativas no início do trimestre)',f"{h1:.1f}% (4T23, base {b1}) -> {h2:.1f}% (4T24, base {b2})",'accounts + churn_events')
rng=[]
for k in ['referral_source','plan_tier_account','industry','size_band']:
    for v,d in m.groupby(k): rng.append((hazard(d,'2024Q4')[0],f'{k}={v}'))
lo,hi=min(rng),max(rng); add('E03','A alta é generalizada: taxa 4T24 em todos os 17 segmentos (canal, plano, indústria, porte)',f"min {lo[0]:.1f}% ({lo[1]}) | max {hi[0]:.1f}% ({hi[1]})",'accounts + churn_events')
# --- definicoes de churn
n_flag=int(m.churn_flag_account.sum()); n_endsub=int((m.n_subs_ended>0).sum()); n_ev=int(m.has_churn_event.sum())
allended=int(((m.n_subs_active==0)).sum())
add('E04','Três definições de churn dão números diferentes',f"flag em accounts={n_flag} ({n_flag/5:.1f}%) | >=1 assinatura encerrada={n_endsub} ({n_endsub/5:.1f}%) | >=1 churn_event={n_ev} ({n_ev/5:.1f}%) | contas com TODAS as assinaturas encerradas={allended}",'accounts + subscriptions + churn_events')
add('E05','Interseção flag x eventos',f"{int((m.churn_flag_account&m.has_churn_event).sum())} contas nos dois; chi2 p={stats.chi2_contingency(pd.crosstab(m.churn_flag_account,m.has_churn_event))[1]:.2f}",'accounts + churn_events','chi2')
ch=m[m.has_churn_event]
add('E06','Contas com churn_event que ainda têm assinaturas pagantes ativas e MRR',f"{int((ch.n_subs_active_paying>0).sum())} de {len(ch)} contas; MRR US$ {int(ch.mrr_active_sum.sum()):,} de {int(m.mrr_active_sum.sum()):,} ({100*ch.mrr_active_sum.sum()/m.mrr_active_sum.sum():.1f}%)",'subscriptions + churn_events + accounts')
u=f.merge(s[['subscription_id','account_id']],on='subscription_id').merge(m[['account_id','first_churn_date','has_churn_event']],on='account_id')
uc=u[u.has_churn_event]; tc=t.merge(m[['account_id','first_churn_date','has_churn_event']],on='account_id').query('has_churn_event')
add('E07','Atividade DEPOIS da data de churn (contas churnadas)',f"{100*(uc.usage_date>uc.first_churn_date).mean():.1f}% das linhas de uso ({int((uc.usage_date>uc.first_churn_date).sum())}/{len(uc)}) e {100*(tc.submitted_at>tc.first_churn_date).mean():.1f}% dos tickets ({int((tc.submitted_at>tc.first_churn_date).sum())}/{len(tc)})",'feature_usage + subscriptions + churn_events; support_tickets + churn_events')
# --- CS
g1=m[m.has_churn_event].avg_csat.dropna(); g2=m[~m.has_churn_event].avg_csat.dropna()
add('E08','CSAT: churnadas vs retidas',f"{t.merge(m[['account_id','has_churn_event']],on='account_id').query('has_churn_event').satisfaction_score.mean():.2f} vs {t.merge(m[['account_id','has_churn_event']],on='account_id').query('not has_churn_event').satisfaction_score.mean():.2f} (nível ticket); conta: p={stats.mannwhitneyu(g1,g2)[1]:.2f}",'support_tickets + churn_events + accounts','Mann-Whitney')
add('E09','Qualidade da métrica de satisfação',f"{100*t.satisfaction_score.isna().mean():.1f}% dos tickets sem nota; notas existentes só {sorted(int(x) for x in t.satisfaction_score.dropna().unique())}; mín=3",'support_tickets')
tp=t.merge(m[['account_id','cutoff_date','has_churn_event']],on='account_id'); tp['d']=(tp.cutoff_date-tp.submitted_at).dt.days
w=tp[(tp.d>=0)&(tp.d<90)].groupby('account_id').agg(t90=('ticket_id','size'),e90=('escalation_flag','sum')); m2=m.merge(w,on='account_id',how='left').fillna({'t90':0,'e90':0})
add('E10','Tickets nos 90 dias antes do churn (retidas: 90 dias antes de 31/12/24)',f"{m2[m2.has_churn_event].t90.mean():.2f} vs {m2[~m2.has_churn_event].t90.mean():.2f} por conta; p={stats.mannwhitneyu(m2[m2.has_churn_event].t90,m2[~m2.has_churn_event].t90)[1]:.2f}",'support_tickets + churn_events + accounts','Mann-Whitney')
ts=t.merge(m[['account_id','has_churn_event']],on='account_id')
add('E11','Escalação e resolução: churnadas vs retidas',f"escalação {100*ts[ts.has_churn_event].escalation_flag.mean():.1f}% vs {100*ts[~ts.has_churn_event].escalation_flag.mean():.1f}%; resolução {ts[ts.has_churn_event].resolution_time_hours.mean():.1f}h vs {ts[~ts.has_churn_event].resolution_time_hours.mean():.1f}h; 1a resposta {ts[ts.has_churn_event].first_response_time_minutes.mean():.0f} vs {ts[~ts.has_churn_event].first_response_time_minutes.mean():.0f} min",'support_tickets + churn_events')
add('E12','Churn "silencioso" (conta sem ticket)',f"{int((~m.has_ticket).sum())} contas sem ticket, {int(m[~m.has_ticket].has_churn_event.sum())} com churn; hipótese de silêncio não testável (n=8)",'accounts + support_tickets + churn_events')
# --- Produto (SÓ USO VÁLIDO: registros a partir do cadastro da conta)
u=u.merge(a[['account_id','signup_date']],on='account_id'); u['valido']=u.usage_date>=u.signup_date
u['q']=u.usage_date.dt.to_period('Q').astype(str)
tot_all=u.groupby('q').usage_count.sum(); tot=u[u.valido].groupby('q').usage_count.sum()
add('E13','Uso registrado x uso válido (após o cadastro)',f"{100*(1-u[u.valido].usage_count.sum()/u.usage_count.sum()):.1f}% do volume registrado é anterior ao cadastro da conta ({100*(1-tot['2023Q1']/tot_all['2023Q1']):.1f}% no 1T23, {100*(1-tot['2024Q4']/tot_all['2024Q4']):.1f}% no 4T24); o total registrado (+{100*(tot_all['2024Q4']/tot_all['2023Q1']-1):.1f}% em 8 trimestres) não mede crescimento",'feature_usage + subscriptions + accounts')
qs=pd.period_range('2023Q1','2024Q4',freq='Q')
def ativas(qq,ids=None):
    st,en=qq.start_time,qq.end_time
    d=m[(m.signup_date<=en)&(m.first_churn_date.isna()|(m.first_churn_date>=st))]
    return d if ids is None else d[d.account_id.isin(ids)]
def upc(qq,ids=None):
    d=ativas(qq,ids); return u[u.valido&(u.q==str(qq))&u.account_id.isin(d.account_id)].usage_count.sum()/max(len(d),1)
u1,u4=upc(pd.Period('2024Q1')),upc(pd.Period('2024Q4'))
add('E14','Uso válido por conta ativa 1T24 -> 4T24',f"{u1:.1f} -> {u4:.1f} usos por conta por trimestre ({100*(u4/u1-1):+.1f}%)",'feature_usage + subscriptions + accounts + churn_events')
def seg(col):
    out={}
    for v,d in m.groupby(col):
        a1,a4=upc(pd.Period('2024Q1'),d.account_id),upc(pd.Period('2024Q4'),d.account_id); out[v]=round(100*(a4/a1-1),1)
    return out
grid=[]
for qq in [pd.Period('2024Q1'),pd.Period('2024Q4')]:
    d=ativas(qq); x=u[u.valido&(u.q==str(qq))].groupby('account_id').usage_count.sum()
    grid.append(d[['account_id','industry','plan_tier_account','size_band','referral_source']].assign(q=str(qq),uso=d.account_id.map(x).fillna(0)))
gr=pd.concat(grid).pivot_table(index=['account_id','industry','plan_tier_account','size_band','referral_source'],columns='q',values='uso').fillna(0).reset_index()
gr['delta']=gr['2024Q4']-gr['2024Q1']
kp={c_:round(stats.kruskal(*[x.delta for _,x in gr.groupby(c_)])[1],2) for c_ in ['industry','plan_tier_account','size_band','referral_source']}
add('E15','Uso válido por conta ativa 1T24 -> 4T24 por indústria (%)',str(seg('industry')),'feature_usage + subscriptions + accounts','Kruskal p='+str(kp['industry']))
add('E16','Uso válido por conta ativa 1T24 -> 4T24 por plano (%)',str(seg('plan_tier_account')),'feature_usage + subscriptions + accounts','Kruskal p='+str(kp['plan_tier_account']))
add('E17','Uso válido por conta ativa 1T24 -> 4T24 por porte e canal (%)',f"porte {seg('size_band')}; canal {seg('referral_source')}",'feature_usage + subscriptions + accounts',f"Kruskal p porte={kp['size_band']}, canal={kp['referral_source']}")
add('E18','A variação de uso por conta difere entre segmentos?',f"Kruskal p: {kp}",'feature_usage + subscriptions + accounts','Kruskal')
# janelas pré-corte, só uso válido
uv=u[u.valido].merge(m[['account_id','cutoff_date']],on='account_id'); uv['d']=(uv.cutoff_date-uv.usage_date).dt.days
w90=uv[(uv.d>=0)&(uv.d<90)].groupby('account_id').agg(u90=('usage_count','sum'),e90=('error_count','sum'),b90=('usage_count',lambda x:x[uv.loc[x.index,'is_beta_feature']].sum()))
p90=uv[(uv.d>=90)&(uv.d<180)].groupby('account_id').usage_count.sum().rename('p90')
upre=uv[uv.d>=0].groupby('account_id').usage_count.sum().rename('upre')
mv=m.set_index('account_id').join(w90).join(p90).join(upre).fillna({'u90':0,'e90':0,'b90':0,'p90':0,'upre':0})
mv['err100']=100*mv.e90/mv.u90.replace(0,np.nan); mv['beta']=mv.b90/mv.u90.replace(0,np.nan)
mv['tenure']=(mv.cutoff_date-mv.signup_date).dt.days; mv['rate30']=mv.upre/mv.tenure.clip(lower=30)*30
mv['trend_v']=(mv.u90-mv.p90)/mv.p90.replace(0,np.nan)
C=mv.has_churn_event
add('E19','Erros por 100 usos nos 90 dias antes do corte (uso válido)',f"mediana {mv[C].err100.median():.2f} churnadas vs {mv[~C].err100.median():.2f} retidas; p={stats.mannwhitneyu(mv[C].err100.dropna(),mv[~C].err100.dropna())[1]:.2f}; taxa de erro geral {100*u[u.valido&(u.q=='2024Q1')].error_count.sum()/tot['2024Q1']:.2f} (1T24) -> {100*u[u.valido&(u.q=='2024Q4')].error_count.sum()/tot['2024Q4']:.2f} (4T24)",'feature_usage + subscriptions + accounts + churn_events','Mann-Whitney')
mv['tb']=pd.qcut(mv.tenure,4); strat=[round(stats.mannwhitneyu(d[d.has_churn_event].rate30,d[~d.has_churn_event].rate30)[1],2) for _,d in mv.groupby('tb') if d.has_churn_event.sum()>2 and (~d.has_churn_event).sum()>2]
add('E20','Usos por 30 dias desde o cadastro (uso válido): diferença é efeito do tempo de vida',f"mediana {mv[C].rate30.median():.1f} vs {mv[~C].rate30.median():.1f} (p={stats.mannwhitneyu(mv[C].rate30,mv[~C].rate30)[1]:.3f}); dentro de quartis de tempo de vida, p={strat}",'feature_usage + subscriptions + accounts + churn_events','Mann-Whitney estratificado')
dq=mv[mv.p90>0].assign(q=lambda x:x.trend_v<-0.4); ct=pd.crosstab(dq.q,dq.has_churn_event)
add('E21','Queda de uso válido >40% (90d vs 90d anteriores) como sinal de churn',f"churn {100*dq[dq.q].has_churn_event.mean():.1f}% (n={int(dq.q.sum())}) vs {100*dq[~dq.q].has_churn_event.mean():.1f}% (n={int((~dq.q).sum())}); p={stats.chi2_contingency(ct)[1]:.2f}; beta {mv[C].beta.mean():.3f} vs {mv[~C].beta.mean():.3f}",'feature_usage + subscriptions + churn_events','chi2')
# --- segmentos
pv={}
m['billing_mix']=pd.cut(m.pct_subs_annual,[-.01,.33,.66,1.0],labels=['mensal','misto','anual'])
for k in ['referral_source','industry','plan_tier_account','country','size_band','billing_mix','is_trial_account','mrr_band']: pv[k]=round(stats.chi2_contingency(pd.crosstab(m[k],m.has_churn_event))[1],3)
r=m.groupby('referral_source').has_churn_event.mean().mul(100).round(1).to_dict(); cn=m.groupby('country').has_churn_event.mean().mul(100).round(1)
add('E22','Nenhum atributo estático separa quem churna (p-valores chi2)',str(pv),'accounts + subscriptions + churn_events','chi2')
add('E23','Churn por canal (maior spread) e país',f"canal {r}; país min {cn.idxmin()} {cn.min()}% (n={int((m.country==cn.idxmin()).sum())}) max {cn.idxmax()} {cn.max()}%",'accounts + churn_events')
sp={k:round(stats.chi2_contingency(pd.crosstab(s[k],s.churn_flag))[1],3) for k in ['billing_frequency','auto_renew_flag','plan_tier','downgrade_flag','upgrade_flag']}
add('E24','Nível assinatura: nada separa as 486 encerradas (p-valores)',str(sp)+f"; encerradas {int(s.churn_flag.sum())}/{len(s)}={100*s.churn_flag.mean():.1f}%",'subscriptions','chi2')
s['sq']=s.start_date.dt.to_period('Q').astype(str); er=s.groupby('sq').churn_flag.agg(['size','mean']); 
add('E25','Assinaturas iniciadas por trimestre explodem (base cresce); % encerradas por trimestre de início',f"inícios {int(er['size'].iloc[0])}->{int(er['size'].iloc[-1])}; end% {er['mean'].round(3).to_dict()}",'subscriptions')
# --- motivos
r2=c.merge(m[['account_id','n_tickets_pre','n_tickets_escalated_pre','mrr_active_sum','error_per_100_uses_pre','avg_csat_pre']],on='account_id'); kp={col:round(stats.kruskal(*[x[col].dropna() for _,x in r2.groupby('reason_code')])[1],2) for col in ['n_tickets_pre','n_tickets_escalated_pre','mrr_active_sum','error_per_100_uses_pre','avg_csat_pre']}
add('E26','Motivo declarado x comportamento real (Kruskal p)',str(kp),'churn_events + support_tickets + feature_usage + subscriptions','Kruskal')
add('E27','Motivo declarado x texto de feedback',f"chi2 p={stats.chi2_contingency(pd.crosstab(c.reason_code,c.feedback_text.fillna('NULL')))[1]:.2f}; reason='support' tem {r2[r2.reason_code=='support'].n_tickets_pre.mean():.2f} tickets pré-churn vs {r2[r2.reason_code!='support'].n_tickets_pre.mean():.2f} nos demais",'churn_events + support_tickets')
cs=c.merge(s[['account_id','start_date','downgrade_flag']],on='account_id'); cs['dd']=(cs.churn_date-cs.start_date).dt.days
x=cs[(cs.dd>=0)&(cs.dd<=90)].groupby('churn_event_id').downgrade_flag.any(); c3=c.assign(dg=c.churn_event_id.map(x).fillna(False))
add('E28','Downgrade antes do churn: flag do evento vs assinaturas',f"{int(c.preceding_downgrade_flag.sum())} eventos marcados; só {int((c3.preceding_downgrade_flag&c3.dg).sum())} confirmados por assinatura downgrade<=90d. Contas com downgrade: churn {100*m[m.n_downgrades>0].has_churn_event.mean():.1f}% vs {100*m[m.n_downgrades==0].has_churn_event.mean():.1f}%, p={stats.chi2_contingency(pd.crosstab(m.n_downgrades>0,m.has_churn_event))[1]:.2f}",'churn_events + subscriptions','chi2')
add('E29','Peso em MRR = peso em contas',f"{100*ch.mrr_active_sum.sum()/m.mrr_active_sum.sum():.1f}% do MRR vs {100*len(ch)/500:.1f}% das contas; top 50 contas por MRR: churn {100*m.nlargest(50,'mrr_active_sum').has_churn_event.mean():.0f}% vs {100*m.nsmallest(450,'mrr_active_sum').has_churn_event.mean():.1f}% no resto",'subscriptions + churn_events + accounts')
add('E30','Refunds',f"US$ {c.refund_amount_usd.sum():,.2f} em 600 eventos ({100*(c.refund_amount_usd>0).mean():.1f}% com refund) = {100*c.refund_amount_usd.sum()/ch.mrr_active_sum.sum():.3f}% do MRR de contas com churn",'churn_events + subscriptions')
# modelo
from sklearn.model_selection import cross_val_score,StratifiedKFold
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
num=['seats_account','n_subs','pct_subs_annual','n_downgrades','n_upgrades','n_subs_auto_renew_off','mrr_active_sum','err100','beta','n_tickets','pct_tickets_rated','avg_csat','pct_tickets_escalated','avg_resolution_hours','avg_first_response_min']
X=pd.concat([mv[num].astype(float),pd.get_dummies(mv[['referral_source','industry','country','plan_tier_account']],drop_first=True).astype(float)],axis=1); y=mv.has_churn_event.astype(int); cv=StratifiedKFold(5,shuffle=True,random_state=1)
au={nm:round(cross_val_score(mod,X,y,cv=cv,scoring='roc_auc').mean(),3) for nm,mod in [('logistica',make_pipeline(SimpleImputer(),StandardScaler(),LogisticRegression(max_iter=1000))),('gradient_boosting',make_pipeline(SimpleImputer(),GradientBoostingClassifier(n_estimators=100,max_depth=2,random_state=1)))]}
add('E31','Modelo preditivo com as 5 tabelas, uso válido e sem variáveis ligadas ao tempo de vida (AUC em 5-fold CV; 0,5 = acaso)',str(au),'as 5 tabelas via accounts_master','CV AUC')
# lista de acao
ret=m[~m.has_churn_event].copy(); ret['usage_trend_pct']=ret.account_id.map(mv.trend_v).round(3); ret['sinal_queda_uso']=ret.usage_trend_pct<-0.4; ret['sinal_escalacao']=ret.n_tickets_escalated>0; ret['sinal_downgrade']=ret.n_downgrades>0; ret['sinal_sem_nota_csat']=ret.n_tickets_rated==0
ret['n_sinais']=ret[['sinal_queda_uso','sinal_escalacao','sinal_downgrade','sinal_sem_nota_csat']].sum(axis=1)
lst=ret[ret.n_sinais>=1].sort_values(['n_sinais','mrr_active_sum'],ascending=[False,False])[['account_id','account_name','industry','referral_source','plan_tier_account','mrr_active_sum','usage_trend_pct','n_tickets','n_tickets_escalated','n_downgrades','avg_csat','sinal_queda_uso','sinal_escalacao','sinal_downgrade','sinal_sem_nota_csat','n_sinais']]
lst.to_csv(f'{OUT}/at_risk_accounts.csv',index=False)
add('E32','Contas retidas (sem churn_event): total e com >=1 sinal de alerta',f"{len(ret)} contas, MRR US$ {int(ret.mrr_active_sum.sum()):,}; com >=1 sinal: {len(lst)} (MRR US$ {int(lst.mrr_active_sum.sum()):,}); com >=2 sinais: {int((lst.n_sinais>=2).sum())} (MRR US$ {int(lst[lst.n_sinais>=2].mrr_active_sum.sum()):,}); queda de uso válido >40%: {int(ret.sinal_queda_uso.sum())} contas (MRR US$ {int(ret[ret.sinal_queda_uso].mrr_active_sum.sum()):,})",'accounts + subscriptions + feature_usage + support_tickets + churn_events')
import re
for e in E: e['valor']=re.sub(r'np\.float64\(([^)]*)\)',r'\1',e['valor'])
pd.DataFrame(E).to_csv(f'{OUT}/evidence.csv',index=False)
for e in E: print(e['id'],'|',e['insight'],'|',e['valor'])
