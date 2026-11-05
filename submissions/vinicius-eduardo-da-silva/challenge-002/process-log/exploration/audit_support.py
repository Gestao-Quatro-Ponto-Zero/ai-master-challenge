"""Can the support dataset answer the Director's three questions?

Every pattern is compared with shuffled data, so noise is not reported as a finding.
Usage: python audit_support.py <customer_support_tickets.csv>
"""
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import cross_val_score

warnings.filterwarnings("ignore")
pd.set_option("display.width", 200, "display.max_columns", 30, "display.max_rows", 60)
rng = np.random.default_rng(0)
s = pd.read_csv(sys.argv[1])
s["frt"] = pd.to_datetime(s["First Response Time"], errors="coerce")
s["ttr"] = pd.to_datetime(s["Time to Resolution"], errors="coerce")
s["bought"] = pd.to_datetime(s["Date of Purchase"], errors="coerce")
s["hours"] = (s["ttr"] - s["frt"]).dt.total_seconds() / 3600
s["rating"] = s["Customer Satisfaction Rating"]

print("== 1. Integrity")
print("rows", len(s), "(brief says ~30,000) | duplicate IDs", s["Ticket ID"].duplicated().sum(), "| duplicate emails", s["Customer Email"].duplicated().sum())
print(s.groupby("Ticket Status")[["frt", "ttr", "rating", "Resolution"]].apply(lambda g: g.notna().mean()).round(3).to_string())
print("first response range", s["frt"].min(), "to", s["frt"].max(), "| distinct days", s["frt"].dt.date.nunique())
print("resolution range", s["ttr"].min(), "to", s["ttr"].max(), "| distinct days", s["ttr"].dt.date.nunique())
print("purchase range", s["bought"].min(), "to", s["bought"].max())
print("no ticket creation column:", not any("creat" in c.lower() or "open" in c.lower() for c in s.columns), list(s.columns))
closed = s[s["hours"].notna()]
print("closed with resolution BEFORE first response:", round((closed["hours"] < 0).mean(), 3), "| hours", closed["hours"].describe().round(1).to_dict())
print("closed hours is uniform on [-24,24]? KS p =", round(stats.kstest((closed["hours"] + 24) / 48, "uniform").pvalue, 3))
print("volume by first-response hour is flat? share by day", s["frt"].dt.date.value_counts(normalize=True).round(3).to_dict())

print("\n== 2. Where does the flow get stuck? Only positive durations, as the brief would read them")
valid = closed[closed["hours"] > 0].copy()
print("valid rows", len(valid))
for col in ("Ticket Channel", "Ticket Priority", "Ticket Type"):
    print(valid.groupby(col)["hours"].agg(["mean", "median", "size"]).round(2).to_string())
keys = ["Ticket Channel", "Ticket Priority", "Ticket Type"]
combo = valid.groupby(keys)["hours"].agg(["mean", "size"]).sort_values("mean")
print("combinations", len(combo), "| n per combo", combo["size"].min(), "-", combo["size"].max())
print("worst 3\n", combo.tail(3).round(2).to_string())
print("best 3\n", combo.head(3).round(2).to_string())
observed = combo["mean"].max() - combo["mean"].min()
fake = []
labels = valid[keys].copy()
for _ in range(2000):
    shuffled = rng.permutation(valid["hours"].values)
    means = pd.Series(shuffled).groupby([labels[k].values for k in keys]).mean()
    fake.append(means.max() - means.min())
print(f"best-to-worst gap {observed:.2f}h; in shuffled data the gap is {np.mean(fake):.2f}h on average; p = {np.mean(np.array(fake) >= observed):.3f}")
for col in keys:
    groups = [g["hours"].values for _, g in valid.groupby(col)]
    print(col, "ANOVA p =", round(stats.f_oneway(*groups).pvalue, 3))
pooled = s[s["Ticket Priority"].notna()]
print("do critical tickets get resolved faster? critical vs low mean hours", valid[valid["Ticket Priority"] == "Critical"]["hours"].mean().round(2), valid[valid["Ticket Priority"] == "Low"]["hours"].mean().round(2))

print("\n== 3. What drives satisfaction?")
rated = s[s["rating"].notna()].copy()
print("rated", len(rated), "of", len(s), "(only Closed)")
counts = rated["rating"].value_counts().sort_index()
print("distribution", counts.to_dict(), "| uniform chi2 p =", round(stats.chisquare(counts).pvalue, 3))
tests = {}
for col in ("Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject", "Customer Gender", "Product Purchased"):
    tests[col] = stats.f_oneway(*[g["rating"].values for _, g in rated.groupby(col)]).pvalue
    print(col, "rating range", rated.groupby(col)["rating"].mean().round(2).agg(["min", "max"]).to_dict(), "p =", round(tests[col], 3))
print("smallest p", round(min(tests.values()), 3), "| Bonferroni threshold", round(0.05 / len(tests), 4))
print("rating vs hours Pearson", tuple(round(v, 3) for v in stats.pearsonr(rated["hours"], rated["rating"])), "| vs age", tuple(round(v, 3) for v in stats.pearsonr(rated["Customer Age"], rated["rating"])))
features = rated[["Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject", "Customer Gender", "Product Purchased"]].apply(lambda c: c.astype("category").cat.codes)
features = features.assign(hours=rated["hours"], age=rated["Customer Age"], purchase=rated["bought"].astype("int64"))
model = HistGradientBoostingRegressor(max_depth=3, max_iter=80)
print("predict rating, R2 (5-fold)", cross_val_score(model, features, rated["rating"], cv=5, scoring="r2").mean().round(3))
print("same, shuffled labels", cross_val_score(model, features, rng.permutation(rated["rating"].values), cv=5, scoring="r2").mean().round(3))
print("predict rating>=4, AUC", cross_val_score(HistGradientBoostingClassifier(max_depth=3, max_iter=80), features, (rated["rating"] >= 4).astype(int), cv=5, scoring="roc_auc").mean().round(3))

print("\n== 4. Is the ticket text real?")
print("subject vs type independent? chi2 p =", round(stats.chi2_contingency(pd.crosstab(s["Ticket Subject"], s["Ticket Type"]))[1], 3))
print("subject vs priority independent? chi2 p =", round(stats.chi2_contingency(pd.crosstab(s["Ticket Subject"], s["Ticket Priority"]))[1], 3))
print("type vs channel independent? chi2 p =", round(stats.chi2_contingency(pd.crosstab(s["Ticket Type"], s["Ticket Channel"]))[1], 3))
text = s["Ticket Description"]
print("literal {product_purchased} placeholder", round(text.str.contains(r"\{product_purchased\}").mean(), 3))
first = text.str.split(r"(?<=[.!?])\s", regex=True).str[0]
print("distinct first sentences", first.nunique(), "| top", first.value_counts().head(3).to_dict())
print("mentions the purchased product by name", round(np.mean([str(p).lower() in str(d).lower() for p, d in zip(s["Product Purchased"], text)]), 3))
subject_words = [set(str(x).lower().split()) - {"issue", "the", "with", "a"} for x in s["Ticket Subject"]]
print("description shares a subject word", round(np.mean([bool(w & set(str(d).lower().split())) for w, d in zip(subject_words, text)]), 3))
rated_text = s[s["Resolution"].notna()]
v = TfidfVectorizer(stop_words="english").fit(pd.concat([rated_text["Ticket Description"], rated_text["Resolution"]]))
a, b = v.transform(rated_text["Ticket Description"]), v.transform(rated_text["Resolution"])
same = np.asarray(a.multiply(b).sum(axis=1)).ravel().mean()
other = np.asarray(a.multiply(b[rng.permutation(b.shape[0])]).sum(axis=1)).ravel().mean()
print(f"description-resolution similarity: real pair {same:.4f} vs random pair {other:.4f}")
print("resolution length (words)", rated_text["Resolution"].str.split().str.len().describe().round(1).to_dict())
for _, row in s[s["Resolution"].notna()].head(3).iterrows():
    print(" EXAMPLE |", row["Ticket Subject"], "|", row["Ticket Description"][:150].replace("\n", " "), "| RESOLUTION:", row["Resolution"])

print("\n== 5. What is left that is usable")
print(s["Ticket Status"].value_counts(normalize=True).round(3).to_dict())
print(s["Ticket Channel"].value_counts(normalize=True).round(3).to_dict())
print(s["Ticket Priority"].value_counts(normalize=True).round(3).to_dict())
print(s["Ticket Type"].value_counts(normalize=True).round(3).to_dict())
