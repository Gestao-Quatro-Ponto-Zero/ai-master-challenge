"""Série mensal de churn, uso e suporte (RavenStack).
- Taxa de primeiro churn: contas com 1o churn no mês / contas já ativas no início do mês
  (cadastro antes do mês e sem churn antes dele). Contas novas do mês não entram no numerador nem na base.
- Uso: só uso válido (registros a partir da data de cadastro da conta).
Uso: python build_monthly_trend.py [pasta_dos_csvs] [pasta_saida]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DATA as _DATA, OUT as _OUT
import sys, pandas as pd, numpy as np
IN  = sys.argv[1] if len(sys.argv) > 1 else _DATA
OUT = sys.argv[2] if len(sys.argv) > 2 else _OUT
a=pd.read_csv(f'{IN}/ravenstack_accounts.csv',parse_dates=['signup_date'])
s=pd.read_csv(f'{IN}/ravenstack_subscriptions.csv')
f=pd.read_csv(f'{IN}/ravenstack_feature_usage.csv',parse_dates=['usage_date'])
t=pd.read_csv(f'{IN}/ravenstack_support_tickets.csv',parse_dates=['submitted_at'])
c=pd.read_csv(f'{IN}/ravenstack_churn_events.csv',parse_dates=['churn_date'])
first=c.groupby('account_id').churn_date.min()
a['first_churn']=a.account_id.map(first)
u=f.merge(s[['subscription_id','account_id']],on='subscription_id').merge(a[['account_id','signup_date']],on='account_id')
u['valido']=u.usage_date>=u.signup_date
rows=[]
for p in pd.period_range('2023-01','2024-12',freq='M'):
    ini,fim=p.start_time,p.end_time
    base=a[(a.signup_date<ini)&(a.first_churn.isna()|(a.first_churn>=ini))]
    churn_base=((base.first_churn>=ini)&(base.first_churn<=fim)).sum()
    ativas=a[(a.signup_date<=fim)&(a.first_churn.isna()|(a.first_churn>=ini))]
    um=u[(u.usage_date>=ini)&(u.usage_date<=fim)]
    uv=um[um.valido]
    tk=t[(t.submitted_at>=ini)&(t.submitted_at<=fim)]
    ev=c[(c.churn_date>=ini)&(c.churn_date<=fim)]
    rows.append(dict(
        month=str(p),
        signups=int(((a.signup_date>=ini)&(a.signup_date<=fim)).sum()),
        contas_ativas_inicio=len(base),
        churn_events=len(ev),
        contas_primeiro_churn=int(((a.first_churn>=ini)&(a.first_churn<=fim)).sum()),
        primeiro_churn_da_base=int(churn_base),
        taxa_primeiro_churn_pct=round(100*churn_base/len(base),2) if len(base)>=30 else None,
        refund_usd=round(ev.refund_amount_usd.sum(),2),
        uso_registrado=int(um.usage_count.sum()),
        uso_valido=int(uv.usage_count.sum()),
        pct_uso_antes_cadastro=round(100*(1-uv.usage_count.sum()/max(um.usage_count.sum(),1)),1),
        contas_ativas_no_mes=len(ativas),
        uso_valido_por_conta_ativa=round(uv[uv.account_id.isin(ativas.account_id)].usage_count.sum()/max(len(ativas),1),1),
        erros_por_100_usos_validos=round(100*uv.error_count.sum()/max(uv.usage_count.sum(),1),2),
        tickets=len(tk),
        avg_csat=round(tk.satisfaction_score.mean(),2),
        pct_tickets_com_nota=round(100*tk.satisfaction_score.notna().mean(),1),
        pct_escalados=round(100*tk.escalation_flag.mean(),1)))
df=pd.DataFrame(rows); df.to_csv(f'{OUT}/monthly_trend.csv',index=False)
print(df[['month','contas_ativas_inicio','primeiro_churn_da_base','taxa_primeiro_churn_pct','uso_valido_por_conta_ativa','pct_uso_antes_cadastro']].to_string(index=False))
