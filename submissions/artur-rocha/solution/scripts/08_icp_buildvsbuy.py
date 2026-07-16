import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
"""
Challenge 001 - Passo 8: ICP + hipotese build-vs-buy (vibe coding).
A hipotese so vale pro ICP com capacidade tecnica de construir interno.
Perfilo a base e cruzo com churn, com foco em DevTools x EUA.
"""
import pandas as pd
from scipy.stats import chi2_contingency
pd.set_option('display.width',200)
OUT=os.path.join(_ROOT,'solution','outputs')
m=pd.read_csv(f'{OUT}/account_master_clean.csv')

print("="*80); print("PERFIL DA BASE (ICP) por industria"); print("="*80)
g=m.groupby('industry').agg(contas=('account_id','count'),
    pct_base=('account_id', lambda s: round(100*len(s)/len(m),1)),
    churn_rate=('churn_flag', lambda s: round(100*s.mean(),1)),
    MRR_medio=('mrr_amount','mean'),
    MRR_perdido=('account_id', lambda idx: 0))
mrr_lost=m[m.churn_flag].groupby('industry').mrr_amount.sum()
g['MRR_perdido']=g.index.map(mrr_lost).fillna(0).astype(int)
g['MRR_medio']=g['MRR_medio'].round(0).astype(int)
# rating qualitativo de capacidade de build interno (julgamento humano)
build_cap={'DevTools':'ALTA','Cybersecurity':'ALTA','FinTech':'MEDIA','HealthTech':'BAIXA','EdTech':'BAIXA'}
g['cap_build_interno']=g.index.map(build_cap)
print(g.sort_values('churn_rate',ascending=False).to_string())

print("\n" + "="*80); print("PAIS: base e churn (build-vs-buy e mais forte nos EUA)"); print("="*80)
gc=m.groupby('country').agg(contas=('account_id','count'),
    churn_rate=('churn_flag', lambda s: round(100*s.mean(),1))).sort_values('contas',ascending=False)
print(gc.head(10).to_string())
print(f"\n% da base nos EUA: {100*(m.country=='US').mean():.0f}%")

print("\n" + "="*80); print("O CRUZAMENTO-CHAVE: capacidade de build x churn"); print("="*80)
m['build_capable']=m.industry.map(lambda x: x in ['DevTools','Cybersecurity'])
ct=pd.crosstab(m.build_capable, m.churn_flag)
chi2,p,_,_=chi2_contingency(ct)
for cap,label in [(True,'ICP capaz de buildar (DevTools+Cyber)'),(False,'ICP nao-tecnico (Fin/Health/Ed)')]:
    sub=m[m.build_capable==cap]
    print(f"{label:42s} n={len(sub):3d}  churn={100*sub.churn_flag.mean():.1f}%")
print(f"qui-quadrado p={p:.3f}  ({'significativo' if p<0.05 else 'direcional, nao conclusivo'})")

print("\n--- foco: DevTools isolado x resto ---")
m['is_devtools']=m.industry=='DevTools'
for v,label in [(True,'DevTools'),(False,'Resto da base')]:
    sub=m[m.is_devtools==v]
    print(f"{label:16s} n={len(sub):3d}  churn={100*sub.churn_flag.mean():.1f}%  MRR_medio=${sub.mrr_amount.mean():,.0f}")

print("\n--- DevTools nos EUA (o ICP + o pais de maior risco build-vs-buy) ---")
dt_us=m[(m.industry=='DevTools')&(m.country=='US')]
dt_nonus=m[(m.industry=='DevTools')&(m.country!='US')]
print(f"DevTools EUA:      n={len(dt_us):3d}  churn={100*dt_us.churn_flag.mean():.1f}%")
print(f"DevTools fora EUA: n={len(dt_nonus):3d}  churn={100*dt_nonus.churn_flag.mean():.1f}%")

print("\nNOTA: sinais direcionais, nao conclusivos (n pequeno). Servem pra PRIORIZAR")
print("conversa humana com o ICP exposto, nao pra cravar causa.")
