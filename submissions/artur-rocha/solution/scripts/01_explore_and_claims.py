import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
"""
Challenge 001 — RavenStack Churn
Passo 1: construir tabela mestre por conta + testar as 3 afirmacoes do CEO.

CEO disse:
  (1) "a satisfacao esta ok"
  (2) "o uso da plataforma cresceu"
  (3) "o churn subiu"
Vamos verificar cada uma com numeros, e checar se ha paradoxo de Simpson
(agregado sobe enquanto segmentos-chave caem).
"""
import pandas as pd
import numpy as np

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 60)
DATA = os.path.join(_ROOT,'data')

acc = pd.read_csv(f'{DATA}/ravenstack_accounts.csv', parse_dates=['signup_date'])
sub = pd.read_csv(f'{DATA}/ravenstack_subscriptions.csv', parse_dates=['start_date','end_date'])
use = pd.read_csv(f'{DATA}/ravenstack_feature_usage.csv', parse_dates=['usage_date'])
tik = pd.read_csv(f'{DATA}/ravenstack_support_tickets.csv', parse_dates=['submitted_at','closed_at'])
chn = pd.read_csv(f'{DATA}/ravenstack_churn_events.csv', parse_dates=['churn_date'])

print("="*90)
print("SANIDADE / INTEGRIDADE")
print("="*90)
print(f"accounts: {len(acc)} | churn_flag=True: {acc.churn_flag.sum()} ({acc.churn_flag.mean():.1%})")
print(f"churn_events rows: {len(chn)} | contas unicas com churn: {chn.account_id.nunique()}")
print(f"is_reactivation=True em churn_events: {chn.is_reactivation.sum()}")
# quantas contas churn_flag batem com churn_events?
acc_churned = set(acc.loc[acc.churn_flag,'account_id'])
evt_churned = set(chn.account_id)
print(f"contas churn_flag mas SEM evento: {len(acc_churned - evt_churned)}")
print(f"contas COM evento mas churn_flag=False: {len(evt_churned - acc_churned)}")

# ---- mapear subscription -> account, e MRR por conta (assinatura mais recente) ----
sub_sorted = sub.sort_values('start_date')
latest_sub = sub_sorted.groupby('account_id').tail(1).set_index('account_id')
acc = acc.merge(latest_sub[['mrr_amount','arr_amount','billing_frequency','auto_renew_flag',
                            'upgrade_flag','downgrade_flag']],
                left_on='account_id', right_index=True, how='left')

sub_acc = sub[['subscription_id','account_id']].drop_duplicates()
use2 = use.merge(sub_acc, on='subscription_id', how='left')
print(f"\nfeature_usage sem account mapeado: {use2.account_id.isna().sum()}")

# ---- agregados de uso por conta ----
use_agg = use2.groupby('account_id').agg(
    usage_events=('usage_count','sum'),
    usage_secs=('usage_duration_secs','sum'),
    errors=('error_count','sum'),
    usage_days=('usage_date','nunique'),
).reset_index()
acc = acc.merge(use_agg, on='account_id', how='left')

# ---- agregados de suporte por conta ----
tik_agg = tik.groupby('account_id').agg(
    tickets=('ticket_id','count'),
    avg_resolution_h=('resolution_time_hours','mean'),
    avg_first_resp_min=('first_response_time_minutes','mean'),
    avg_satisfaction=('satisfaction_score','mean'),
    escalations=('escalation_flag','sum'),
).reset_index()
acc = acc.merge(tik_agg, on='account_id', how='left')

# ---- churn reason por conta ----
acc = acc.merge(chn[['account_id','reason_code','churn_date','preceding_downgrade_flag',
                     'preceding_upgrade_flag','refund_amount_usd']],
                on='account_id', how='left')

acc.to_csv(f'{DATA}/../solution/outputs/account_master.csv', index=False)
print(f"\nTabela mestre salva: {len(acc)} contas x {acc.shape[1]} colunas")

churned = acc[acc.churn_flag]
retained = acc[~acc.churn_flag]

print("\n" + "="*90)
print("AFIRMACAO 3 DO CEO: 'o churn subiu'  ->  churn ao longo do tempo")
print("="*90)
chn['ym'] = chn.churn_date.dt.to_period('M')
monthly_churn = chn.groupby('ym').size()
print(monthly_churn.to_string())

print("\n" + "="*90)
print("AFIRMACAO 1 DO CEO: 'satisfacao esta ok'")
print("="*90)
print(f"satisfaction_score global (media, ignorando nulos): {tik.satisfaction_score.mean():.2f} / 5")
print(f"% de tickets SEM nota (cliente nao respondeu): {tik.satisfaction_score.isna().mean():.1%}")
print(f"satisfacao media - contas que FICARAM:   {retained.avg_satisfaction.mean():.2f}")
print(f"satisfacao media - contas que CHURNARAM:  {churned.avg_satisfaction.mean():.2f}")
# distribuicao de notas
print("distribuicao de notas (1-5):")
print(tik.satisfaction_score.value_counts(dropna=False).sort_index().to_string())

print("\n" + "="*90)
print("AFIRMACAO 2 DO CEO: 'o uso cresceu'  ->  uso agregado por mes")
print("="*90)
use['ym'] = use.usage_date.dt.to_period('M')
monthly_use = use.groupby('ym').usage_count.sum()
print(monthly_use.to_string())

# uso agregado: retained vs churned ao longo do tempo (paradoxo de Simpson?)
use2['ym'] = use2.usage_date.dt.to_period('M')
churn_map = acc.set_index('account_id').churn_flag.to_dict()
use2['churned'] = use2.account_id.map(churn_map)
pivot = use2.groupby(['ym','churned']).usage_count.sum().unstack()
print("\nUso mensal separando churned vs retained (paradoxo de Simpson?):")
print(pivot.to_string())

print("\n" + "="*90)
print("CHURN RATE POR DIMENSAO (correlacoes brutas)")
print("="*90)
def churn_by(col, bins=None, labels=None):
    d = acc.copy()
    key = col
    if bins is not None:
        key = col+'_bucket'
        d[key] = pd.cut(d[col], bins=bins, labels=labels)
    g = d.groupby(key, dropna=False).agg(n=('account_id','count'), churn_rate=('churn_flag','mean'))
    g['churn_rate'] = (g['churn_rate']*100).round(1)
    print(f"\n--- churn por {col} ---")
    print(g.to_string())

for c in ['plan_tier','billing_frequency','industry','referral_source','is_trial','auto_renew_flag']:
    churn_by(c)
churn_by('seats', bins=[0,5,20,50,1000], labels=['1-5','6-20','21-50','50+'])
churn_by('mrr_amount', bins=[-1,0,500,1500,100000], labels=['0','1-500','501-1500','1500+'])

print("\n" + "="*90)
print("CHURNED vs RETAINED — medias dos indicadores")
print("="*90)
cols = ['mrr_amount','arr_amount','seats','usage_events','errors','usage_days',
        'tickets','avg_resolution_h','avg_first_resp_min','avg_satisfaction','escalations']
comp = pd.DataFrame({
    'retained': retained[cols].mean(),
    'churned': churned[cols].mean(),
})
comp['razao_churn/ret'] = (comp['churned']/comp['retained']).round(2)
print(comp.round(2).to_string())

print("\n" + "="*90)
print("REASON CODES do churn (o que os proprios dados dizem)")
print("="*90)
print(chn.reason_code.value_counts().to_string())
print("\npreceding_downgrade entre churnados:", f"{chn.preceding_downgrade_flag.mean():.1%}")
print("preceding_upgrade entre churnados:", f"{chn.preceding_upgrade_flag.mean():.1%}")
