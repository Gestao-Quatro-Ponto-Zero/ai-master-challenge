"""03 — Visão por conta: o que diferencia quem deu churn? Uso: python -I 03_contas.py <pasta_dados>"""
import sys, pandas as pd, numpy as np
from scipy import stats
D = sys.argv[1]; r = lambda n: pd.read_csv(f"{D}/ravenstack_{n}.csv")
a, s, u, tk, ce = r("accounts"), r("subscriptions"), r("feature_usage"), r("support_tickets"), r("churn_events")
for d, c in [(a,"signup_date"),(s,"start_date"),(s,"end_date"),(u,"usage_date"),(tk,"submitted_at"),(ce,"churn_date")]: d[c] = pd.to_datetime(d[c])
# uso dentro da janela da assinatura?
us = u.merge(s[["subscription_id","account_id","start_date","end_date"]], on="subscription_id")
fora = (us.usage_date < us.start_date) | (us.end_date.notna() & (us.usage_date > us.end_date))
print(f"uso fora da janela da assinatura: {fora.mean():.1%}  | uso antes do signup da conta: {(us.usage_date < us.account_id.map(a.set_index('account_id').signup_date)).mean():.1%}")
print(f"tickets antes do signup: {(tk.submitted_at < tk.account_id.map(a.set_index('account_id').signup_date)).mean():.1%}")
print(f"reason_code x feedback_text (Cramér V):", end=" ")
ct = pd.crosstab(ce.reason_code, ce.feedback_text.fillna("(vazio)")); chi2 = stats.chi2_contingency(ct)[0]; print(round(np.sqrt(chi2/(ct.values.sum()*(min(ct.shape)-1))),3)); print(ct)
A = a.set_index("account_id").copy()
A["churn_evento"] = A.index.isin(ce.account_id)
A["n_eventos_churn"] = ce.groupby("account_id").size().reindex(A.index).fillna(0)
g = s.groupby("account_id")
A["n_subs"] = g.size(); A["mrr_medio_sub"] = g.mrr_amount.mean(); A["share_anual"] = g.billing_frequency.apply(lambda x: (x=="annual").mean())
A["share_autorenew"] = g.auto_renew_flag.mean(); A["n_upgrades"] = g.upgrade_flag.sum(); A["n_downgrades"] = g.downgrade_flag.sum()
gu = us.groupby("account_id")
A["uso_eventos"] = gu.size(); A["uso_total"] = gu.usage_count.sum(); A["erros"] = gu.error_count.sum(); A["dur_media_s"] = gu.usage_duration_secs.mean()
A["taxa_erro"] = A.erros / A.uso_total; A["share_beta"] = gu.is_beta_feature.mean(); A["n_features"] = gu.feature_name.nunique()
gt = tk.groupby("account_id")
A["tickets"] = gt.size(); A["csat"] = gt.satisfaction_score.mean(); A["csat_resp"] = gt.satisfaction_score.apply(lambda x: x.notna().mean())
A["escal"] = gt.escalation_flag.mean(); A["resol_h"] = gt.resolution_time_hours.mean(); A["frt_min"] = gt.first_response_time_minutes.mean()
A["urgentes"] = gt.priority.apply(lambda x: (x=="urgent").mean())
A = A.fillna({"tickets":0,"uso_eventos":0,"uso_total":0})
A["idade_dias"] = (pd.Timestamp("2024-12-31") - A.signup_date).dt.days
A["uso_por_seat"] = A.uso_total / A.seats
A.to_csv("outputs/03_contas.csv")
for alvo in ["churn_evento", "churn_flag"]:
    print(f"\n=========== alvo = {alvo}  (positivos: {A[alvo].sum()} de {len(A)})")
    for c in ["industry","country","referral_source","plan_tier","is_trial"]:
        ct = pd.crosstab(A[c], A[alvo]); p = stats.chi2_contingency(ct)[1]
        print(f"{c:16s} p={p:.3f} | taxa%: " + ", ".join(f"{k}={v:.0f}" for k,v in (100*A.groupby(c)[alvo].mean()).items()))
    print(f"{'variável':16s} {'quem ficou':>12s} {'churn':>12s}  p(MW)   AUC")
    for c in ["seats","idade_dias","n_subs","mrr_medio_sub","share_anual","share_autorenew","n_upgrades","n_downgrades","uso_eventos","uso_total","uso_por_seat","erros","taxa_erro","dur_media_s","share_beta","n_features","tickets","csat","csat_resp","escal","resol_h","frt_min","urgentes"]:
        x0, x1 = A.loc[~A[alvo], c].dropna(), A.loc[A[alvo], c].dropna()
        U, p = stats.mannwhitneyu(x1, x0); auc = U/(len(x0)*len(x1))
        print(f"{c:16s} {x0.median():12.3f} {x1.median():12.3f}  {p:.3f}  {auc:.2f}")
