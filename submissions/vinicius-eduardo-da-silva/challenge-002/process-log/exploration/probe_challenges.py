"""Quick diagnosis of the other challenges' data: is there real signal, and what are the traps?"""
import sys
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, r2_score, roc_auc_score
from sklearn.model_selection import cross_val_score, train_test_split

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220, "display.max_columns", 60, "display.max_rows", 80)
S = sys.argv[1]


def encode(df):
    out = df.copy()
    for c in out.columns:
        if out[c].dtype == object or str(out[c].dtype) in ("str", "string", "bool", "boolean"):
            out[c] = out[c].astype("category").cat.codes
    return out


print("######## 001 CHURN")
a = pd.read_csv(f"{S}/ds-churn/ravenstack_accounts.csv")
sub = pd.read_csv(f"{S}/ds-churn/ravenstack_subscriptions.csv")
use = pd.read_csv(f"{S}/ds-churn/ravenstack_feature_usage.csv")
t = pd.read_csv(f"{S}/ds-churn/ravenstack_support_tickets.csv")
c = pd.read_csv(f"{S}/ds-churn/ravenstack_churn_events.csv")
for n, x in dict(accounts=a, subs=sub, usage=use, tickets=t, churn=c).items():
    print(n, x.shape, list(x.columns))
print("churn_flag rate", a["churn_flag"].mean(), "| accounts with churn event", c["account_id"].nunique(), "of", len(a))
print("flag vs event overlap", a.assign(ev=a["account_id"].isin(c["account_id"])).groupby("churn_flag")["ev"].mean().round(3).to_dict())
print("subs churn_flag", sub["churn_flag"].mean(), "orphans usage", (~use["subscription_id"].isin(sub["subscription_id"])).mean(), "usage dup rows", use.duplicated().mean())
print("reason", c["reason_code"].value_counts().to_dict())
print("churn date", c["churn_date"].min(), c["churn_date"].max(), "reactivation", c.get("is_reactivation", pd.Series(dtype=bool)).mean())
print(c.groupby(pd.to_datetime(c["churn_date"]).dt.to_period("Q")).size().to_dict())
print("churn before signup", (pd.to_datetime(c["churn_date"]) < pd.to_datetime(c.merge(a, on="account_id")["signup_date"])).mean())
print("feedback distinct", c["feedback_text"].nunique(), c["feedback_text"].value_counts(dropna=False).head(6).to_dict())
f = a.set_index("account_id")[["industry", "country", "referral_source", "plan_tier", "seats", "is_trial", "churn_flag"]].copy()
tk = t.groupby("account_id").agg(n=("ticket_id", "size"), res=("resolution_time_hours", "mean"), frt=("first_response_time_minutes", "mean"), sat=("satisfaction_score", "mean"), esc=("escalation_flag", "mean"))
s2 = sub.merge(use.groupby("subscription_id").agg(cnt=("usage_count", "sum"), dur=("usage_duration_secs", "sum"), err=("error_count", "sum")), on="subscription_id", how="left").groupby("account_id").agg(mrr=("mrr_amount", "sum"), cnt=("cnt", "sum"), dur=("dur", "sum"), err=("err", "sum"), up=("upgrade_flag", "mean"), down=("downgrade_flag", "mean"), subs=("subscription_id", "size"))
f = f.join(tk).join(s2)
print(f.groupby("churn_flag")[["n", "res", "frt", "sat", "esc", "mrr", "cnt", "dur", "err", "up", "down", "seats"]].mean().round(2).to_string())
for col in ("plan_tier", "industry", "referral_source", "is_trial", "country"):
    g = f.groupby(col)["churn_flag"].agg(["mean", "size"]).round(3)
    print(col, g.sort_values("mean").iloc[[0, -1]].to_dict("index"))
X = encode(f.drop(columns="churn_flag"))
print("AUC account model (5-fold)", cross_val_score(HistGradientBoostingClassifier(max_depth=3, max_iter=80), X, f["churn_flag"], cv=5, scoring="roc_auc").mean().round(3))
y = np.random.default_rng(0).permutation(f["churn_flag"].values)
print("AUC with shuffled label", cross_val_score(HistGradientBoostingClassifier(max_depth=3, max_iter=80), X, y, cv=5, scoring="roc_auc").mean().round(3))

print("\n######## 002 SUPPORT")
s = pd.read_csv(f"{S}/ds-support/customer_support_tickets.csv")
print(s.shape, list(s.columns))
print(s["Ticket Status"].value_counts().to_dict(), "rating nulls", s["Customer Satisfaction Rating"].isna().mean())
print("rating dist", s["Customer Satisfaction Rating"].value_counts(normalize=True).sort_index().round(3).to_dict())
for col in ("Ticket Type", "Ticket Priority", "Ticket Channel", "Product Purchased"):
    print(col, s.groupby(col)["Customer Satisfaction Rating"].mean().round(2).agg(["min", "max"]).to_dict(), s[col].nunique())
s["frt"] = pd.to_datetime(s["First Response Time"], errors="coerce")
s["ttr"] = pd.to_datetime(s["Time to Resolution"], errors="coerce")
s["buy"] = pd.to_datetime(s["Date of Purchase"], errors="coerce")
s["res_h"] = (s["ttr"] - s["frt"]).dt.total_seconds() / 3600
print("frt null", s["frt"].isna().mean(), "ttr null", s["ttr"].isna().mean(), "negative res share", (s["res_h"] < 0).mean(), "frt range", s["frt"].min(), s["frt"].max(), "purchase range", s["buy"].min(), s["buy"].max())
print("res_h", s["res_h"].describe().round(1).to_dict())
closed = s[s["Customer Satisfaction Rating"].notna()]
print("corr rating/res_h", closed[["Customer Satisfaction Rating", "res_h", "Customer Age"]].corr().iloc[0].round(3).to_dict())
print("pivot res_h by priority/channel range", closed.pivot_table(index="Ticket Priority", columns="Ticket Channel", values="res_h").round(1).to_string())
Xs = encode(closed[["Ticket Type", "Ticket Priority", "Ticket Channel", "Product Purchased", "Customer Age", "Customer Gender", "Ticket Subject"]]).assign(res=closed["res_h"])
print("rating high(>=4) AUC", cross_val_score(HistGradientBoostingClassifier(max_depth=3, max_iter=80), Xs, (closed["Customer Satisfaction Rating"] >= 4).astype(int), cv=5, scoring="roc_auc").mean().round(3))
print("placeholder in text", s["Ticket Description"].str.contains(r"\{product_purchased\}").mean(), "| distinct resolution", s["Resolution"].nunique(), "of", s["Resolution"].notna().sum())
print("subject-vs-type AUC-free: type by subject share max", s.groupby("Ticket Subject")["Ticket Type"].agg(lambda v: v.value_counts(normalize=True).iloc[0]).mean().round(3))
sample = s["Ticket Description"].iloc[0][:230], s["Resolution"].dropna().iloc[0][:120]
print(sample)
tr, te = train_test_split(s, test_size=0.25, random_state=0)
v = TfidfVectorizer(max_features=20000, ngram_range=(1, 2)).fit(tr["Ticket Description"])
for target in ("Ticket Type", "Ticket Priority", "Ticket Subject"):
    m = LogisticRegression(max_iter=300).fit(v.transform(tr["Ticket Description"]), tr[target])
    print("text predicts", target, "acc", round(accuracy_score(te[target], m.predict(v.transform(te["Ticket Description"]))), 3), "chance", round(tr[target].value_counts(normalize=True).iloc[0], 3))
it = pd.read_csv(f"{S}/ds-it/all_tickets_processed_improved_v3.csv")
print(it.shape, it["Topic_group"].value_counts(normalize=True).round(3).to_dict(), "dup text", it["Document"].duplicated().mean())
tr, te = train_test_split(it, test_size=0.25, random_state=0, stratify=it["Topic_group"])
v = TfidfVectorizer(max_features=40000, ngram_range=(1, 2), sublinear_tf=True).fit(tr["Document"])
m = LogisticRegression(max_iter=300).fit(v.transform(tr["Document"]), tr["Topic_group"])
p = m.predict(v.transform(te["Document"]))
print("IT tfidf+LR acc", round(accuracy_score(te["Topic_group"], p), 3), "macro f1", round(f1_score(te["Topic_group"], p, average="macro"), 3))
proba = m.predict_proba(v.transform(te["Document"])).max(axis=1)
for th in (0.6, 0.8, 0.9):
    k = proba >= th
    print(f" confidence>={th}: coverage {k.mean():.2f} acc {accuracy_score(te['Topic_group'][k], p[k]):.3f}")
print(it["Document"].iloc[0][:200])

print("\n######## 004 SOCIAL")
m = pd.read_csv(f"{S}/ds-social/social_media_dataset.csv")
print(m.shape, list(m.columns))
print(m.iloc[0].to_dict())
print(m.isna().mean()[lambda x: x > 0].round(3).to_dict())
print(m.describe().T[["mean", "std", "min", "50%", "max"]].round(2).to_string())
num = m.select_dtypes("number")
print("corr with views/likes:\n", num.corr().round(2).to_string())
