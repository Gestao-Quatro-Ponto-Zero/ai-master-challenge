"""06 — Checagens finais: pico de dez/2024 e mudança de plano x encerramento. Uso: python -I 06_checagens.py <pasta_dados>"""
import sys, pandas as pd
from scipy import stats
D = sys.argv[1]; s = pd.read_csv(f"{D}/ravenstack_subscriptions.csv", parse_dates=["start_date","end_date"])
e = s.end_date.dropna()
print("encerramentos em dez/2024:", (e.dt.to_period("M")=="2024-12").sum(), "| no dia 31/12:", (e=="2024-12-31").sum(), "| últimos 7 dias:", (e>="2024-12-25").sum())
print("dias até o fim, por assinatura encerrada (mediana):", (e - s.loc[e.index,"start_date"]).dt.days.median())
print("assinaturas que começaram em dez/2024:", (s.start_date.dt.to_period("M")=="2024-12").sum(), "| em nov:", (s.start_date.dt.to_period("M")=="2024-11").sum())
for f in ["upgrade_flag","downgrade_flag","is_trial","auto_renew_flag","billing_frequency","plan_tier"]:
    ct = pd.crosstab(s[f], s.churn_flag); p = stats.chi2_contingency(ct)[1]
    print(f"encerramento por {f}: " + ", ".join(f"{k}={v:.1%}" for k, v in s.groupby(f).churn_flag.mean().items()) + f" | p={p:.3f}")
# controle por idade da assinatura: encerramento por ano de início
print("taxa de encerramento por trimestre de início:", s.groupby(s.start_date.dt.to_period("Q")).churn_flag.mean().round(3).to_dict())
