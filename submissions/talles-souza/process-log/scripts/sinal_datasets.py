import sys, pandas as pd, numpy as np
D = sys.argv[1]
pd.set_option("display.width", 200)

print("===== 003 CRM")
p = pd.read_csv(f"{D}/crm-sales-predictive-analytics/sales_pipeline.csv")
print(p.shape, p.deal_stage.value_counts().to_dict())
print("nulos:", p.isna().sum().to_dict())
fech = p[p.deal_stage.isin(["Won", "Lost"])].copy()
fech["won"] = (fech.deal_stage == "Won").astype(int)
print("win rate geral", round(fech.won.mean(), 3))
for c in ["sales_agent", "product", "account"]:
    g = fech.groupby(c).won.agg(["mean", "count"])
    g = g[g["count"] >= 20]
    print(c, "win rate min/max", round(g["mean"].min(), 3), round(g["mean"].max(), 3), "n grupos", len(g))
fech["dias"] = (pd.to_datetime(fech.close_date) - pd.to_datetime(fech.engage_date)).dt.days
print("dias won/lost mediana", fech.groupby("won").dias.median().to_dict())
fech["faixa"] = pd.qcut(fech.dias, 5, duplicates="drop")
print(fech.groupby("faixa", observed=True).won.mean().round(3).to_dict())
print("datas", p.engage_date.min(), p.engage_date.max(), p.close_date.max())

print("\n===== 001 RavenStack")
R = f"{D}/saas-subscription-and-churn-analytics-dataset"
a = pd.read_csv(f"{R}/ravenstack_accounts.csv"); ce = pd.read_csv(f"{R}/ravenstack_churn_events.csv")
t = pd.read_csv(f"{R}/ravenstack_support_tickets.csv"); s = pd.read_csv(f"{R}/ravenstack_subscriptions.csv")
u = pd.read_csv(f"{R}/ravenstack_feature_usage.csv")
print(a.columns.tolist()); print(ce.columns.tolist())
print("churn flag:", a.get("churn_flag", pd.Series()).mean() if "churn_flag" in a else "n/a")
print("reason:", ce.reason_code.value_counts().to_dict() if "reason_code" in ce else "")
for c in ["industry", "referral_source", "plan_tier", "is_trial", "country"]:
    if c in a and "churn_flag" in a:
        print(c, a.groupby(c).churn_flag.mean().round(3).to_dict())
tt = t.groupby("account_id").agg(sat=("satisfaction_score", "mean"), esc=("escalation_flag", "mean"), res=("resolution_time_hours", "mean")).reset_index()
m = a.merge(tt, on="account_id", how="left")
print("sat/esc/res por churn:", m.groupby("churn_flag")[["sat", "esc", "res"]].mean().round(3).to_dict())
us = u.merge(s[["subscription_id", "account_id"]], on="subscription_id").groupby("account_id").agg(n=("usage_count", "sum"), err=("error_count", "sum")).reset_index()
m = m.merge(us, on="account_id", how="left")
print("uso/erros por churn:", m.groupby("churn_flag")[["n", "err"]].mean().round(1).to_dict())

print("\n===== 002 Suporte")
sp = pd.read_csv(f"{D}/customer-support-ticket-dataset/customer_support_tickets.csv")
print(sp.shape); print(sp.columns.tolist())
print("status", sp["Ticket Status"].value_counts().to_dict())
print("sat nulos", sp["Customer Satisfaction Rating"].isna().mean().round(3))
cl = sp.dropna(subset=["Customer Satisfaction Rating"])
for c in ["Ticket Channel", "Ticket Priority", "Ticket Type"]:
    print(c, cl.groupby(c)["Customer Satisfaction Rating"].mean().round(3).to_dict())
print("sat dist", cl["Customer Satisfaction Rating"].value_counts(normalize=True).round(3).sort_index().to_dict())
print(sp[["First Response Time", "Time to Resolution"]].head(3).to_string())
fr = pd.to_datetime(sp["First Response Time"], errors="coerce"); tr = pd.to_datetime(sp["Time to Resolution"], errors="coerce")
print("resolução antes da 1a resposta:", round(((tr < fr) & tr.notna()).sum() / tr.notna().sum(), 3))
print("descr exemplo:", sp["Ticket Description"].iloc[0][:250])
print("resolução exemplo:", str(sp["Resolution"].dropna().iloc[0])[:200])
print("descr com placeholder {product_purchased}:", round(sp["Ticket Description"].str.contains(r"\{product_purchased\}").mean(), 3))
it = pd.read_csv(f"{D}/it-service-ticket-classification-dataset/all_tickets_processed_improved_v3.csv")
print("IT", it.shape, it.Topic_group.value_counts().to_dict())

print("\n===== 004 Social")
so = pd.read_csv(f"{D}/social-media-sponsorship-and-engagement-dataset/social_media_dataset.csv")
print(so.shape); print(so.columns.tolist())
num = so.select_dtypes("number")
print(num.describe().T[["mean", "50%", "min", "max"]].round(2).to_string())
if "is_sponsored" in so:
    er = [c for c in so.columns if "engagement" in c.lower()]
    print("engajamento por patrocínio:", so.groupby("is_sponsored")[er + ["views"] if "views" in so else er].mean().round(4).to_dict())
for c in ["platform", "content_type", "content_category"]:
    if c in so:
        er = [x for x in so.columns if "engagement" in x.lower()][:1]
        if er: print(c, so.groupby(c)[er[0]].mean().round(4).to_dict())
fc = [c for c in so.columns if "follower" in c.lower()]; vc = [c for c in so.columns if c.lower() == "views"]
if fc and vc: print("corr seguidores x views:", round(so[fc[0]].corr(so[vc[0]]), 3))
lk = [c for c in so.columns if c.lower() == "likes"]
if lk and vc: print("corr likes x views:", round(so[lk[0]].corr(so[vc[0]]), 3))
