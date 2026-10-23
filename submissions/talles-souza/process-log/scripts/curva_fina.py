"""Curva fina da chance pela idade e os grupos da tela (Siga <= 40 d, Foque 41-60 d, Nutrição > 60 d).

Uso: python -X utf8 curva_fina.py <pasta crm-sales-predictive-analytics>
Saída bruta: evidencias/curva-fina.txt. Só lê os CSVs.

Replay: os negócios que já tinham começado e seguiam abertos em 30/09/2017; mede-se a idade
de cada um nesse corte e conta-se quem ganhou até 31/12/2017 (o último fechamento do dataset).
No fim, quantos negócios abertos caem em cada grupo "hoje" (31/12/2017).
"""
import sys

import pandas as pd

p = pd.read_csv(sys.argv[1] + "/sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
corte, fim, hoje = pd.Timestamp("2017-09-30"), pd.Timestamp("2017-12-31"), p.close_date.max()
ab = p[(p.engage_date <= corte) & (p.close_date.isna() | (p.close_date > corte))].copy()
ab["idade"] = (corte - ab.engage_date).dt.days
ab["ganhou"] = ((ab.deal_stage == "Won") & (ab.close_date <= fim)).astype(int)
bins = [-1, 10, 20, 30, 40, 50, 60, 90, 138, 10**6]
print("replay 30/09 -> 31/12, abertos no corte:", len(ab))
print(ab.groupby(pd.cut(ab.idade, bins), observed=True).ganhou.agg(n="size", ganhou="mean").round(3))
blocos = pd.cut(ab.idade, [-1, 40, 60, 10**6], labels=["Siga <=40", "Foque 41-60", "Nutricao >60"])
print(ab.groupby(blocos, observed=True).ganhou.agg(n="size", ganhou="mean").round(3))
e = p[p.deal_stage == "Engaging"].copy()
e["idade"] = (hoje - e.engage_date).dt.days
print("hoje", hoje.date(), "| Engaging por bloco:", pd.cut(e.idade, [-1, 40, 60, 10**6], labels=["Siga", "Foque", "Nutricao"]).value_counts().to_dict(),
      "| Prospecting sem data:", int((p.deal_stage == "Prospecting").sum()), int(p[p.deal_stage == "Prospecting"].engage_date.isna().sum()))
