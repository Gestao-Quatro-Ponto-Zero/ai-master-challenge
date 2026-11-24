"""Teste de composição e de safra: a taxa mensal de churn sobe por piora real ou por efeito de idade/data?
Uso: uv run --with pandas python -I solution/scripts/05_teste_safras.py data/raw
"""
import sys, pandas as pd, numpy as np
s=pd.read_csv(sys.argv[1]+'/ravenstack_subscriptions.csv',parse_dates=['start_date','end_date'])
c=pd.read_csv(sys.argv[1]+'/ravenstack_churn_events.csv',parse_dates=['churn_date'])
a=pd.read_csv(sys.argv[1]+'/ravenstack_accounts.csv',parse_dates=['signup_date'])
p=s[~s.is_trial].copy()
p['ym']=p.start_date.dt.to_period('M')
print("novas assinaturas pagas por mês:"); print(p.groupby('ym').size().loc['2024-01':].to_dict())
# hazard por idade × trimestre (pessoa-mês)
rows=[]
for m in pd.period_range('2023-07','2024-12',freq='M'):
    ini,fim=m.start_time,m.end_time
    at=p[(p.start_date<ini)&(p.end_date.isna()|(p.end_date>=ini))].copy()
    at['idade']=((ini-at.start_date).dt.days)
    at['enc']=(at.end_date>=ini)&(at.end_date<=fim)
    at['mes']=str(m); rows.append(at[['mes','idade','enc']])
r=pd.concat(rows)
r['faixa']=pd.cut(r.idade,[-1,30,90,180,365,10000],labels=['0-30d','31-90d','91-180d','181-365d','>1ano'])
r['tri']=pd.PeriodIndex(r.mes,freq='M').asfreq('Q').astype(str)
print("\ntaxa mensal por faixa de idade (linhas) e trimestre (colunas):")
print((r.pivot_table(index='faixa',columns='tri',values='enc',aggfunc='mean',observed=True)*100).round(2))
print("\nmix da base ativa por idade (%):")
print((pd.crosstab(r.faixa,r.tri,normalize='columns')*100).round(0))
# taxa padronizada: mix fixo de 2024Q1
w=pd.crosstab(r.faixa,r.tri,normalize='columns')['2024Q1']
h=r.pivot_table(index='faixa',columns='tri',values='enc',aggfunc='mean',observed=True)
print("\ntaxa bruta x padronizada (mix de 2024Q1):")
print(pd.DataFrame({'bruta':(r.groupby('tri').enc.mean()*100).round(2),'padronizada':((h.mul(w,axis=0)).sum()*100).round(2)}))
# dist da duração das encerradas
d=(p.end_date-p.start_date).dt.days.dropna(); print("\nduração das encerradas (dias):",d.describe().round(0).to_dict())
# eventos de churn por conta-base mês
