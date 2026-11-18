"""02 — Séries mensais: o churn subiu? a satisfação está ok? o uso cresceu? Uso: python -I 02_tempo.py <pasta_dados>"""
import sys, pandas as pd, numpy as np
D = sys.argv[1]; r = lambda n: pd.read_csv(f"{D}/ravenstack_{n}.csv")
a, s, u, tk, ce = r("accounts"), r("subscriptions"), r("feature_usage"), r("support_tickets"), r("churn_events")
for d, c in [(a,"signup_date"),(s,"start_date"),(s,"end_date"),(u,"usage_date"),(tk,"submitted_at"),(ce,"churn_date")]: d[c] = pd.to_datetime(d[c])
M = pd.period_range("2023-01", "2024-12", freq="M")
q = lambda x: x.dt.to_period("Q")
rows = []
for m in M:
    st, en = m.start_time, m.end_time
    act_s = s[(s.start_date <= en) & (s.end_date.isna() | (s.end_date >= st))]
    act_a = a[a.signup_date <= en]
    um = u[u.usage_date.dt.to_period("M") == m]; tm = tk[tk.submitted_at.dt.to_period("M") == m]
    rows.append(dict(mes=str(m), contas_cadastradas=len(act_a), novas_contas=(a.signup_date.dt.to_period("M")==m).sum(),
        subs_ativas=len(act_s), mrr_ativo=act_s.mrr_amount.sum(), subs_encerradas=(s.end_date.dt.to_period("M")==m).sum(),
        eventos_churn=(ce.churn_date.dt.to_period("M")==m).sum(), mrr_subs_encerradas=s[s.end_date.dt.to_period("M")==m].mrr_amount.sum(),
        uso_eventos=len(um), uso_total=um.usage_count.sum(), uso_por_sub_ativa=um.usage_count.sum()/max(len(act_s),1),
        erros=um.error_count.sum(), tickets=len(tm), csat_media=tm.satisfaction_score.mean(), csat_resp=tm.satisfaction_score.notna().mean(),
        escal=tm.escalation_flag.mean()))
df = pd.DataFrame(rows)
df["taxa_churn_eventos_%"] = 100*df.eventos_churn/df.contas_cadastradas
df["taxa_subs_encerradas_%"] = 100*df.subs_encerradas/df.subs_ativas
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(df.round(2).to_string(index=False))
df.to_csv("outputs/02_series_mensais.csv", index=False)
print("\n=== por trimestre")
qq = pd.DataFrame({
 "eventos_churn": ce.groupby(q(ce.churn_date)).size(),
 "subs_encerradas": s.groupby(q(s.end_date)).size(),
 "novas_contas": a.groupby(q(a.signup_date)).size(),
 "uso_total": u.groupby(q(u.usage_date)).usage_count.sum(),
 "uso_eventos": u.groupby(q(u.usage_date)).size(),
 "tickets": tk.groupby(q(tk.submitted_at)).size(),
 "csat_media": tk.groupby(q(tk.submitted_at)).satisfaction_score.mean().round(2),
 "csat_resp_%": (100*tk.groupby(q(tk.submitted_at)).satisfaction_score.apply(lambda x: x.notna().mean())).round(1),
})
print(qq.to_string())
