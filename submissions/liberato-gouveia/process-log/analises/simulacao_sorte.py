"""Simulação: se TODOS os vendedores fossem igualmente bons (63% de chance em cada deal),
quão diferentes seriam as taxas de ganho só por sorte?"""
import pandas as pd, numpy as np, sys
D=sys.argv[1]
p=pd.read_csv(f"{D}/sales_pipeline.csv")
c=p[p.deal_stage.isin(['Won','Lost'])].copy(); c['won']=(c.deal_stage=='Won').astype(int)
real=c.groupby('sales_agent').won.agg(['size','mean'])
taxa=c.won.mean(); n=real['size'].values
rng=np.random.default_rng(42)
spreads=[]; mins=[]; maxs=[]
for _ in range(10000):
    sim=rng.binomial(n,taxa)/n
    mins.append(sim.min()); maxs.append(sim.max()); spreads.append(sim.max()-sim.min())
real_spread=real['mean'].max()-real['mean'].min()
print(f"taxa geral: {taxa:.3f}")
print(f"REAL: pior vendedor {real['mean'].min():.3f}, melhor {real['mean'].max():.3f}, diferença {real_spread:.3f}")
print(f"SORTE (mediana de 10.000 simulações): pior {np.median(mins):.3f}, melhor {np.median(maxs):.3f}, diferença {np.median(spreads):.3f}")
print(f"% de simulações com diferença >= real: {np.mean(np.array(spreads)>=real_spread)*100:.1f}%")
