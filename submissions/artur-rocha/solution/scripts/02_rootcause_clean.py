import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
"""
Challenge 001 — Passo 2: causa-raiz FEITA DIREITO.
Corrige o bug da tabela mestre (nivel conta, 500 linhas), testa significancia
estatistica dos sinais de segmento, e testa a hipotese de QUEDA DE USO pre-churn
(o sinal pode estar no tempo, nao na media all-time).
"""
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, mannwhitneyu

pd.set_option('display.width', 200); pd.set_option('display.max_columns', 60)
DATA = os.path.join(_ROOT,'data')
OUT  = os.path.join(_ROOT,'solution','outputs')

acc = pd.read_csv(f'{DATA}/ravenstack_accounts.csv', parse_dates=['signup_date'])
sub = pd.read_csv(f'{DATA}/ravenstack_subscriptions.csv', parse_dates=['start_date','end_date'])
use = pd.read_csv(f'{DATA}/ravenstack_feature_usage.csv', parse_dates=['usage_date'])
tik = pd.read_csv(f'{DATA}/ravenstack_support_tickets.csv', parse_dates=['submitted_at','closed_at'])
chn = pd.read_csv(f'{DATA}/ravenstack_churn_events.csv', parse_dates=['churn_date'])

# ---------- tabela mestre NIVEL CONTA (1 linha por conta) ----------
m = acc.copy()  # 500 linhas, churn_flag e a label
# MRR da assinatura mais recente
latest = sub.sort_values('start_date').groupby('account_id').tail(1).set_index('account_id')
m = m.merge(latest[['mrr_amount','arr_amount','billing_frequency','auto_renew_flag']],
            left_on='account_id', right_index=True, how='left')
# uso agregado (via subscription->account)
sub_acc = sub[['subscription_id','account_id']].drop_duplicates()
use = use.merge(sub_acc, on='subscription_id', how='left')
use_agg = use.groupby('account_id').agg(usage_events=('usage_count','sum'),
                                        errors=('error_count','sum'),
                                        usage_days=('usage_date','nunique')).reset_index()
m = m.merge(use_agg, on='account_id', how='left')
# suporte agregado
tik_agg = tik.groupby('account_id').agg(tickets=('ticket_id','count'),
                                        avg_resolution_h=('resolution_time_hours','mean'),
                                        avg_satisfaction=('satisfaction_score','mean'),
                                        escalations=('escalation_flag','sum')).reset_index()
m = m.merge(tik_agg, on='account_id', how='left')
assert len(m) == 500, len(m)
print(f"Tabela mestre LIMPA: {len(m)} contas (churn={m.churn_flag.sum()}, {m.churn_flag.mean():.1%})")

# ---------- discrepancia churn_flag vs churn_events ----------
flag = set(m.loc[m.churn_flag,'account_id']); evt = set(chn.account_id)
print(f"\n[DATA QUALITY] churn_flag=True: {len(flag)} | contas em churn_events: {len(evt)}")
print(f"  so no flag: {len(flag-evt)} | so nos eventos: {len(evt-flag)} | nos dois: {len(flag&evt)}")
print("  -> as duas fontes de churn se contradizem. Usaremos churn_flag como label oficial e sinalizaremos isso.")

# ---------- significancia dos sinais categoricos ----------
print("\n" + "="*90); print("SINAIS CATEGORICOS — sao reais ou ruido? (qui-quadrado)"); print("="*90)
def cat_test(col):
    ct = pd.crosstab(m[col], m.churn_flag)
    chi2, p, _, _ = chi2_contingency(ct)
    rates = (m.groupby(col).churn_flag.mean()*100).round(1)
    print(f"\n{col}: p-value={p:.4f}  {'<-- SIGNIFICATIVO' if p<0.05 else '(nao significativo / ruido)'}")
    print("  churn rate %:", rates.to_dict())
for c in ['industry','referral_source','plan_tier','billing_frequency','is_trial','auto_renew_flag']:
    cat_test(c)

# ---------- significancia dos sinais numericos (Mann-Whitney) ----------
print("\n" + "="*90); print("SINAIS NUMERICOS — churned vs retained (Mann-Whitney)"); print("="*90)
for c in ['mrr_amount','usage_events','errors','usage_days','tickets','avg_resolution_h','avg_satisfaction','escalations']:
    a = m.loc[m.churn_flag, c].dropna(); b = m.loc[~m.churn_flag, c].dropna()
    try:
        u,p = mannwhitneyu(a,b)
    except Exception:
        p = float('nan')
    print(f"{c:20s} churned_med={a.median():8.2f}  retained_med={b.median():8.2f}  p={p:.4f}  {'<-- sig' if p<0.05 else ''}")

# ---------- HIPOTESE-CHAVE: queda de uso PRE-CHURN (sinal no tempo) ----------
print("\n" + "="*90); print("HIPOTESE: uso CAI nas 8 semanas antes do churn?"); print("="*90)
# para contas churnadas com data de churn, comparar uso 0-30d antes vs 30-90d antes
chn_last = chn.sort_values('churn_date').groupby('account_id').tail(1)[['account_id','churn_date']]
u2 = use.merge(chn_last, on='account_id', how='inner')
u2['days_before'] = (u2['churn_date'] - u2['usage_date']).dt.days
recent = u2[(u2.days_before>=0)&(u2.days_before<30)].groupby('account_id').usage_count.sum()
prior  = u2[(u2.days_before>=30)&(u2.days_before<90)].groupby('account_id').usage_count.sum()
comp = pd.DataFrame({'recent_0_30':recent,'prior_30_90':prior}).dropna()
comp['ratio'] = comp.recent_0_30/(comp.prior_30_90/2)  # normaliza janela (30d vs 60d)
print(f"contas churnadas analisadas: {len(comp)}")
print(f"  uso medio 0-30d antes:  {comp.recent_0_30.mean():.1f}")
print(f"  uso medio 30-90d antes (por 30d): {(comp.prior_30_90/2).mean():.1f}")
print(f"  razao recente/anterior (1.0 = estavel, <1 = caindo): {comp.ratio.median():.2f} (mediana)")
print("  -> se ~1.0, NAO ha queda pre-churn detectavel (sinal ausente nos dados sinteticos)")

m.to_csv(f'{OUT}/account_master_clean.csv', index=False)
print(f"\nSalvo: account_master_clean.csv ({len(m)} contas)")

# ---------- resumo revenue-weighted preview ----------
print("\n" + "="*90); print("PREVIEW churn ponderado por receita"); print("="*90)
churned = m[m.churn_flag]
print(f"churn por CONTAGEM: {m.churn_flag.mean():.1%}")
print(f"MRR total perdido (contas churnadas): ${churned.mrr_amount.sum():,.0f}/mes  (ARR ${churned.arr_amount.sum():,.0f})")
print(f"MRR medio churnado ${churned.mrr_amount.mean():,.0f} vs retido ${m[~m.churn_flag].mrr_amount.mean():,.0f}")
by_ind = m.groupby('industry').apply(lambda d: pd.Series({
    'contas':len(d),'churn_rate_%':round(d.churn_flag.mean()*100,1),
    'MRR_perdido':int(d.loc[d.churn_flag,'mrr_amount'].sum())})).sort_values('MRR_perdido',ascending=False)
print("\nMRR perdido por industria:"); print(by_ind.to_string())
