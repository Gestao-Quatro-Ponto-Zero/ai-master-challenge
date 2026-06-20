"""EDA — Lead Scorer 003. Cruza as 4 tabelas e testa H1-H5. Output = evidência."""
import pandas as pd, numpy as np
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"
acc = pd.read_csv(D/"accounts.csv")
prod = pd.read_csv(D/"products.csv")
team = pd.read_csv(D/"sales_teams.csv")
pipe = pd.read_csv(D/"sales_pipeline.csv")

print("="*70); print("H5 — HIGIENE DE DADOS"); print("="*70)
print(f"pipeline={len(pipe)}  accounts={len(acc)}  products={len(prod)}  teams={len(team)}")
print("\nProdutos no pipeline vs catálogo:")
pp = set(pipe['product'].unique()); pc = set(prod['product'].unique())
print(f"  no pipeline mas NÃO no catálogo: {sorted(pp-pc)}")
print(f"  catálogo: {sorted(pc)}")
print("\nNulos por coluna (pipeline):"); print(pipe.isna().sum().to_string())
print(f"\nContas no pipeline ausentes em accounts: {len(set(pipe['account'].dropna())-set(acc['account']))}")
print(f"Agentes no pipeline ausentes em teams: {set(pipe['sales_agent'].unique())-set(team['sales_agent'])}")

# fix GTXPro -> GTX Pro
pipe['product'] = pipe['product'].replace({'GTXPro':'GTX Pro'})
print(f"\n[FIX] GTXPro -> GTX Pro aplicado. Produtos agora batem catálogo: {set(pipe['product'].unique())<=pc}")

print("\n"+"="*70); print("H1 — DISTRIBUIÇÃO DE ESTÁGIO E WIN-RATE"); print("="*70)
print(pipe['deal_stage'].value_counts().to_string())
closed = pipe[pipe['deal_stage'].isin(['Won','Lost'])].copy()
closed['won'] = (closed['deal_stage']=='Won').astype(int)
print(f"\nDeals fechados (Won+Lost): {len(closed)}  | win-rate global: {closed['won'].mean():.1%}")
open_deals = pipe[pipe['deal_stage'].isin(['Prospecting','Engaging'])]
print(f"Deals ABERTOS (universo a scorar): {len(open_deals)}  "
      f"[Prospecting={ (open_deals['deal_stage']=='Prospecting').sum() }, Engaging={ (open_deals['deal_stage']=='Engaging').sum() }]")

print("\n"+"="*70); print("H2 — WIN-RATE POR DIMENSÃO (sinal não-óbvio)"); print("="*70)
def wr(df, by):
    g = df.groupby(by)['won'].agg(['mean','count']).sort_values('mean', ascending=False)
    return g
print("\nPor VENDEDOR (top5/bottom5 com n>=30):")
g = wr(closed,'sales_agent'); g=g[g['count']>=30]
print("  spread:", f"{g['mean'].min():.1%} a {g['mean'].max():.1%}")
print(g.head(5).to_string()); print("  ..."); print(g.tail(5).to_string())

# join product/account/team
m = closed.merge(prod, on='product', how='left').merge(acc, on='account', how='left').merge(team, on='sales_agent', how='left')
print("\nPor PRODUTO:")
print(wr(m,'product').to_string())
print("\nPor SETOR (top/bottom):")
gs=wr(m,'sector'); print(gs.head(4).to_string()); print(gs.tail(3).to_string())
print("\nPor REGIONAL:")
print(wr(m,'regional_office').to_string())
print("\nPor MANAGER (spread):")
gm=wr(m,'manager'); print(f"  {gm['mean'].min():.1%} a {gm['mean'].max():.1%}")

print("\nH2-combinações — tamanho das células agente×produto (justifica smoothing):")
cell = closed.groupby(['sales_agent','product'])['won'].agg(['mean','count'])
print(f"  células: {len(cell)}  | n<10: {(cell['count']<10).mean():.0%}  | n<5: {(cell['count']<5).mean():.0%}")
print("  -> células pequenas frequentes => smoothing bayesiano necessário")

print("\n"+"="*70); print("H3 — CICLO DE VENDA (urgência data-driven)"); print("="*70)
for c in ['engage_date','close_date']: closed[c]=pd.to_datetime(closed[c], errors='coerce')
won = closed[closed['deal_stage']=='Won'].copy()
won['cycle'] = (won['close_date']-won['engage_date']).dt.days
won_c = won['cycle'].dropna()
print(f"Ciclo dos Won (dias): mediana={won_c.median():.0f}  p25={won_c.quantile(.25):.0f}  "
      f"p75={won_c.quantile(.75):.0f}  p90={won_c.quantile(.90):.0f}")
lost = closed[closed['deal_stage']=='Lost'].copy()
lost['cycle']=(lost['close_date']-lost['engage_date']).dt.days
print(f"Ciclo dos Lost (dias): mediana={lost['cycle'].median():.0f}")
print(f"-> threshold 'esfriando' sugerido = ~{won_c.median():.0f}d (mediana Won); "
      f"crítico > {won_c.quantile(.75):.0f}d (p75 Won)")

print("\n"+"="*70); print("H4 — VALOR vs PROBABILIDADE"); print("="*70)
mw = m.copy()
mw['val_bucket']=pd.qcut(mw['sales_price'], 4, duplicates='drop')
print("Win-rate por faixa de preço do produto:")
print(mw.groupby('val_bucket', observed=True)['won'].agg(['mean','count']).to_string())
print(f"\nclose_value dos Won: mediana={won['close_value'].median():.0f}  "
      f"total pipeline Won={won['close_value'].sum():,.0f}")
print("\n>> EDA concluída.")
