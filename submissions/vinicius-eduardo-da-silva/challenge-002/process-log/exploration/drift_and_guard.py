"""Does accuracy hold on later tickets, and can unfamiliar tickets be detected?

The file has no dates, so row order is the only proxy for time, and it is only a hypothesis.
Usage: python drift_and_guard.py <all_tickets_processed_improved_v3.csv> <customer_support_tickets.csv>
"""
import sys
import warnings

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

warnings.filterwarnings("ignore")
pd.set_option("display.width", 200, "display.max_columns", 30, "display.max_rows", 60)
it = pd.read_csv(sys.argv[1])
support = pd.read_csv(sys.argv[2])


def build():
    return make_pipeline(TfidfVectorizer(sublinear_tf=True, max_features=5000), LogisticRegression(max_iter=400, C=10))


print("== Is the file ordered? class share by block of rows")
it["block"] = pd.cut(np.arange(len(it)), 10, labels=False)
print(pd.crosstab(it["block"], it["Topic_group"], normalize="index").round(2).to_string())
print("words per ticket by block", it.groupby("block")["Document"].apply(lambda d: d.str.split().str.len().median()).to_dict())

print("\n== Sequential evaluation: train on earlier rows, test on the next block")
rows = []
for end in range(3, 10):
    train = it[it["block"] < end]
    test = it[it["block"] == end]
    model = build().fit(train["Document"], train["Topic_group"])
    proba = model.predict_proba(test["Document"])
    confidence, predicted = proba.max(axis=1), model.classes_[proba.argmax(axis=1)]
    keep = confidence >= 0.9
    rows.append({"test_block": end, "train": len(train), "acc": round(accuracy_score(test["Topic_group"], predicted), 3), "cover_09": round(keep.mean(), 3), "acc_09": round(accuracy_score(test["Topic_group"][keep], predicted[keep]), 3)})
print(pd.DataFrame(rows).to_string(index=False))

print("\n== Random vs last-20% split, same model")
cut = int(len(it) * 0.8)
early, late = it.iloc[:cut], it.iloc[cut:]
random_train, random_test = train_test_split(it, test_size=0.2, random_state=0, stratify=it["Topic_group"])
for name, train, test in (("random", random_train, random_test), ("first 80% -> last 20%", early, late)):
    model = build().fit(train["Document"], train["Topic_group"])
    proba = model.predict_proba(test["Document"])
    confidence, predicted = proba.max(axis=1), model.classes_[proba.argmax(axis=1)]
    print(name, "acc", round(accuracy_score(test["Topic_group"], predicted), 3))
    for threshold in (0.6, 0.7, 0.8, 0.9, 0.95):
        keep = confidence >= threshold
        print(f"   thr {threshold}: coverage {keep.mean():.3f} acc {accuracy_score(test['Topic_group'][keep], predicted[keep]):.3f}")
    if name != "random":
        per_class = pd.DataFrame({"y": test["Topic_group"].values, "ok": predicted == test["Topic_group"].values}).groupby("y")["ok"].agg(["mean", "size"]).round(3)
        print(per_class.to_string())

print("\n== Unfamiliar-ticket guard, tuned on IT validation and checked on customer tickets")
train, rest = train_test_split(early, test_size=0.25, random_state=0, stratify=early["Topic_group"])
model = build().fit(train["Document"], train["Topic_group"])
vocabulary = set(model.steps[0][1].vocabulary_)


def known_share(texts):
    tokens = texts.fillna("").str.lower().str.findall(r"\b\w\w+\b")
    return tokens.map(lambda words: np.mean([word in vocabulary for word in words]) if words else 0.0).to_numpy()


it_known, late_known, support_known = known_share(rest["Document"]), known_share(late["Document"]), known_share(support["Ticket Description"])
print("known word share: IT val", np.percentile(it_known, [1, 5, 50]).round(3), "| later IT", np.percentile(late_known, [1, 5, 50]).round(3), "| customer", np.percentile(support_known, [5, 50, 95]).round(3))
print("separation AUC (IT val vs customer)", round(roc_auc_score(np.r_[np.ones(len(it_known)), np.zeros(len(support_known))], np.r_[it_known, support_known]), 3))
guard = float(np.percentile(it_known, 5))
print(f"guard = 5th percentile of IT validation = {guard:.3f}")
print(f"  blocked: IT val {(it_known < guard).mean():.3f} | later IT {(late_known < guard).mean():.3f} | customer {(support_known < guard).mean():.3f}")
support_conf = model.predict_proba(support["Ticket Description"].fillna("")).max(axis=1)
for threshold in (0.8, 0.9):
    print(f"  customer tickets auto-routed at {threshold}: without guard {(support_conf >= threshold).mean():.3f} | with guard {((support_conf >= threshold) & (support_known >= guard)).mean():.3f}")
for threshold in (0.8, 0.9):
    proba = model.predict_proba(late["Document"])
    keep = (proba.max(axis=1) >= threshold) & (late_known >= guard)
    print(f"  later IT at {threshold} with guard: coverage {keep.mean():.3f} acc {accuracy_score(late['Topic_group'][keep], model.classes_[proba.argmax(axis=1)][keep]):.3f}")
