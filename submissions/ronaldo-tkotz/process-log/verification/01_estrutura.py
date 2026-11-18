"""01 — Estrutura e integridade das 5 tabelas. Uso: python -I 01_estrutura.py <pasta_dados>"""
import sys, pandas as pd
D = sys.argv[1]
t = {n: pd.read_csv(f"{D}/ravenstack_{n}.csv") for n in ["accounts","subscriptions","feature_usage","support_tickets","churn_events"]}
for n, d in t.items():
    print(f"\n=== {n}: {len(d)} linhas x {d.shape[1]} cols")
    print(d.isna().sum()[lambda s: s>0].to_string() or "sem nulos")
    for c in d.columns:
        if "date" in c or c in ("submitted_at","closed_at"):
            x = pd.to_datetime(d[c], errors="coerce"); print(f"  {c}: {x.min()} → {x.max()}")
a, s, u, tk, ce = (t[k] for k in ["accounts","subscriptions","feature_usage","support_tickets","churn_events"])
print("\n=== chaves")
print("accounts únicos:", a.account_id.nunique(), "| subs únicos:", s.subscription_id.nunique())
print("subs→accounts órfãos:", (~s.account_id.isin(a.account_id)).sum(), "| usage→subs órfãos:", (~u.subscription_id.isin(s.subscription_id)).sum())
print("tickets→accounts órfãos:", (~tk.account_id.isin(a.account_id)).sum(), "| churn→accounts órfãos:", (~ce.account_id.isin(a.account_id)).sum())
print("usage_id duplicados:", u.usage_id.duplicated().sum(), "| linhas usage duplicadas (sem id):", u.drop(columns="usage_id").duplicated().sum())
print("\n=== coerência de churn")
ce_acc = set(ce.account_id)
print("accounts.churn_flag=True:", a.churn_flag.sum(), "| contas com evento de churn:", len(ce_acc), "| eventos:", len(ce), "| reativações:", ce.is_reactivation.sum())
print(pd.crosstab(a.churn_flag, a.account_id.isin(ce_acc), rownames=["churn_flag"], colnames=["tem evento"]))
print("subs churn_flag=True:", s.churn_flag.sum(), "| subs com end_date:", s.end_date.notna().sum())
print(pd.crosstab(s.churn_flag, s.end_date.notna(), rownames=["sub churn_flag"], colnames=["tem end_date"]))
print("subs por conta:", s.groupby("account_id").size().describe().round(1).to_dict())
# conta: plano em accounts vs plano das subs
last = s.sort_values("start_date").groupby("account_id").tail(1).set_index("account_id")
print("plan_tier conta == plano da última sub:", (a.set_index("account_id").plan_tier == last.plan_tier.reindex(a.account_id)).mean().round(3))
print("seats conta == seats última sub:", (a.set_index("account_id").seats == last.seats.reindex(a.account_id)).mean().round(3))
# datas: churn_date vs signup e vs subs
m = ce.merge(a[["account_id","signup_date","churn_flag"]], on="account_id")
print("churn antes do signup:", (pd.to_datetime(m.churn_date) < pd.to_datetime(m.signup_date)).sum())
sub_end = s.groupby("account_id").end_date.max()
m["sub_end_max"] = m.account_id.map(sub_end); m["active_subs"] = m.account_id.map(s[s.end_date.isna()].groupby("account_id").size()).fillna(0)
print("eventos de churn em contas que ainda têm sub ativa:", (m.active_subs>0).sum(), "de", len(m))
print("\n=== distribuições")
for c in ["industry","country","referral_source","plan_tier","is_trial"]: print(c, a[c].value_counts().to_dict())
for c in ["plan_tier","billing_frequency","is_trial","upgrade_flag","downgrade_flag","auto_renew_flag"]: print("subs."+c, s[c].value_counts().to_dict())
print("mrr por plano:", s.groupby("plan_tier").mrr_amount.describe().round(0).to_string())
print("mrr/seat por plano:", (s.mrr_amount/s.seats).groupby(s.plan_tier).describe().round(1).to_string())
print("arr == 12*mrr:", (s.arr_amount == 12*s.mrr_amount).mean())
print("ce.reason_code:", ce.reason_code.value_counts(dropna=False).to_dict())
print("ce.feedback_text:", ce.feedback_text.value_counts(dropna=False).to_dict())
print("tickets prioridade:", tk.priority.value_counts().to_dict(), "| satisfação:", tk.satisfaction_score.value_counts(dropna=False).sort_index().to_dict())
print("features:", u.feature_name.nunique(), "| beta share:", u.is_beta_feature.mean().round(3))
