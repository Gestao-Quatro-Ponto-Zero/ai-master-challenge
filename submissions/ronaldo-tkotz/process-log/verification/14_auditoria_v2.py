"""14 — Audita os horários dos tickets (achado do Ronaldo) e a base do "ARR perdido" da planilha V2 (Gemini). Uso: python -I 14_auditoria_v2.py <pasta_dados>"""
print("=== tickets")
import sys, pandas as pd
t = pd.read_csv(f"{sys.argv[1]}/ravenstack_support_tickets.csv")
print("submitted_at exemplos:", t.submitted_at.head(3).tolist(), "| tem hora?", t.submitted_at.str.contains(":").mean())
sub = pd.to_datetime(t.submitted_at); clo = pd.to_datetime(t.closed_at)
print("submitted às 00:00:", (sub.dt.hour.eq(0) & sub.dt.minute.eq(0)).mean())
print("closed_at minutos == 0:", clo.dt.minute.eq(0).mean(), "| horas distintas em closed_at:", clo.dt.hour.nunique())
d = (clo - sub).dt.total_seconds()/3600
print("closed - submitted == resolution_time_hours:", (d - t.resolution_time_hours).abs().lt(1e-6).mean())
print("resolution_time_hours inteiro:", (t.resolution_time_hours % 1 == 0).mean(), "| min/max", t.resolution_time_hours.min(), t.resolution_time_hours.max())
print("first_response em min: min/max", t.first_response_time_minutes.min(), t.first_response_time_minutes.max(), "| primeira resposta > resolução:", (t.first_response_time_minutes/60 > t.resolution_time_hours).sum())
print("closed_at nulo:", t.closed_at.isna().sum())
import numpy as np
print("resolução: distribuição por faixa de 12h:", pd.cut(t.resolution_time_hours,[0,12,24,36,48,60,72]).value_counts().sort_index().to_dict())
print("=== ARR encerrado x churn_flag")
D = sys.argv[1]; a = pd.read_csv(f"{D}/ravenstack_accounts.csv"); s = pd.read_csv(f"{D}/ravenstack_subscriptions.csv")
e = s[s.end_date.notna()]; flag = set(a[a.churn_flag].account_id)
print("ARR encerrado total:", e.arr_amount.sum(), "| assinaturas", len(e), "| contas distintas", e.account_id.nunique())
x = e[e.account_id.isin(flag)]; print("  dessas, de contas com churn_flag:", x.arr_amount.sum(), f"({x.arr_amount.sum()/e.arr_amount.sum():.0%})", "| contas", x.account_id.nunique())
y = e[~e.account_id.isin(flag)]; print("  de contas SEM churn_flag (ativas):", y.arr_amount.sum(), "| contas", y.account_id.nunique())
