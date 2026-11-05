"""How far can ticket routing be trusted, and does it transfer to customer tickets?

Thresholds are chosen on a validation split and reported on an untouched test split.
Usage: python classifier_benchmark.py <all_tickets_processed_improved_v3.csv> <customer_support_tickets.csv>
"""
import sys
import warnings

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

warnings.filterwarnings("ignore")
pd.set_option("display.width", 200, "display.max_columns", 30, "display.max_rows", 60)
it = pd.read_csv(sys.argv[1])
support = pd.read_csv(sys.argv[2])
it["sorted"] = it["Document"].str.split().map(lambda w: " ".join(sorted(w)))
print("rows", len(it), "| exact duplicates", it["Document"].duplicated().sum(), "| same words in another order", it["sorted"].duplicated().sum())
print("words per ticket", it["Document"].str.split().str.len().describe().round(1).to_dict())
print("share by class", it["Topic_group"].value_counts(normalize=True).round(3).to_dict())

train, rest = train_test_split(it, test_size=0.4, random_state=0, stratify=it["Topic_group"])
val, test = train_test_split(rest, test_size=0.5, random_state=0, stratify=rest["Topic_group"])
print("split", len(train), len(val), len(test), "| train/test overlap by word set", test["sorted"].isin(train["sorted"]).mean().round(4))
print("majority baseline", round(test["Topic_group"].value_counts(normalize=True).iloc[0], 3))

tfidf = dict(sublinear_tf=True, ngram_range=(1, 2), min_df=2)
models = {
    "LogReg full": make_pipeline(TfidfVectorizer(**tfidf), LogisticRegression(max_iter=400, C=10)),
    "LinearSVC": make_pipeline(TfidfVectorizer(**tfidf), LinearSVC(C=0.5)),
    "ComplementNB": make_pipeline(TfidfVectorizer(**tfidf), ComplementNB()),
    "LogReg 5k unigrams": make_pipeline(TfidfVectorizer(sublinear_tf=True, max_features=5000), LogisticRegression(max_iter=400, C=10)),
    "LogReg 3k unigrams": make_pipeline(TfidfVectorizer(sublinear_tf=True, max_features=3000), LogisticRegression(max_iter=400, C=10)),
}
for name, model in models.items():
    model.fit(train["Document"], train["Topic_group"])
    predicted = model.predict(val["Document"])
    print(f"{name:20s} val acc {accuracy_score(val['Topic_group'], predicted):.3f} macro F1 {f1_score(val['Topic_group'], predicted, average='macro'):.3f}")

model = models["LogReg 5k unigrams"]
labels = model.classes_
print("\nchosen for the browser: LogReg 5k unigrams")
print("5-fold accuracy", cross_val_score(make_pipeline(TfidfVectorizer(sublinear_tf=True, max_features=5000), LogisticRegression(max_iter=400, C=10)), it["Document"], it["Topic_group"], cv=5).round(3))


def report(frame, name):
    proba = model.predict_proba(frame["Document"])
    confidence = proba.max(axis=1)
    predicted = labels[proba.argmax(axis=1)]
    return proba, confidence, predicted


_, conf_val, pred_val = report(val, "val")
rows = []
for threshold in (0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95):
    keep = conf_val >= threshold
    rows.append((threshold, round(keep.mean(), 3), round(accuracy_score(val["Topic_group"][keep], pred_val[keep]), 3)))
print("validation: threshold, coverage, accuracy\n", pd.DataFrame(rows, columns=["thr", "coverage", "acc"]).to_string(index=False))

_, conf_test, pred_test = report(test, "test")
print("\nTEST overall acc", round(accuracy_score(test["Topic_group"], pred_test), 3), "macro F1", round(f1_score(test["Topic_group"], pred_test, average="macro"), 3))
for threshold in (0.6, 0.8, 0.9):
    keep = conf_test >= threshold
    print(f"TEST thr {threshold}: coverage {keep.mean():.3f} acc {accuracy_score(test['Topic_group'][keep], pred_test[keep]):.3f}")

print("\nPer class at thr 0.8 on test")
table = []
for label in labels:
    in_class = test["Topic_group"].values == label
    routed = (conf_test >= 0.8) & (pred_test == label)
    table.append(
        {
            "class": label,
            "share": round(in_class.mean(), 3),
            "recall_all": round(((pred_test == label) & in_class).sum() / in_class.sum(), 3),
            "precision_all": round(((pred_test == label) & in_class).sum() / max(1, (pred_test == label).sum()), 3),
            "coverage_08": round(((conf_test >= 0.8) & in_class).sum() / in_class.sum(), 3),
            "precision_08": round((routed & in_class).sum() / max(1, routed.sum()), 3),
        }
    )
print(pd.DataFrame(table).to_string(index=False))

cm = pd.DataFrame(confusion_matrix(test["Topic_group"], pred_test, labels=labels), index=labels, columns=labels)
pairs = cm.where(~np.eye(len(labels), dtype=bool)).stack().sort_values(ascending=False).head(6)
print("\nTop confusions\n", pairs.to_string())

print("\nCalibration on test")
bands = pd.cut(conf_test, [0, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0])
calib = pd.DataFrame({"band": bands, "conf": conf_test, "right": pred_test == test["Topic_group"].values}).groupby("band", observed=True).agg(n=("right", "size"), conf=("conf", "mean"), acc=("right", "mean")).round(3)
print(calib.to_string())

wrong = test[(pred_test != test["Topic_group"].values) & (conf_test >= 0.9)].assign(pred=pred_test[(pred_test != test["Topic_group"].values) & (conf_test >= 0.9)])
print("\nConfident and wrong:", len(wrong), "of", (conf_test >= 0.9).sum())
for _, row in wrong.head(5).iterrows():
    print(f" label={row['Topic_group']} pred={row['pred']} | {row['Document'][:150]}")
low = test[conf_test < 0.4]
print("\nVery unsure:", len(low))
for _, row in low.head(4).iterrows():
    print(f" label={row['Topic_group']} | {row['Document'][:150]}")

print("\nSensitive words by class (share of tickets that contain them)")
for word in ("termination", "terminated", "resign", "leaver", "salary", "payroll", "harassment", "complaint", "password", "admin", "breach", "urgent"):
    has = it["Document"].str.contains(rf"\b{word}\b", regex=True)
    top = it[has]["Topic_group"].value_counts(normalize=True).head(2).round(2).to_dict()
    print(f"  {word:12s} {has.sum():5d} {top}")

print("\n== Transfer to the customer support dataset")
texts = support["Ticket Description"].fillna("")
proba = model.predict_proba(texts)
confidence = proba.max(axis=1)
print("confidence test IT     ", pd.Series(conf_test).describe().round(3).to_dict())
print("confidence support     ", pd.Series(confidence).describe().round(3).to_dict())
for threshold in (0.6, 0.8, 0.9):
    print(f"  coverage at {threshold}: IT test {(conf_test >= threshold).mean():.3f} | support {(confidence >= threshold).mean():.3f}")
vocab = set(model.steps[0][1].vocabulary_)
known = texts.str.lower().str.findall(r"\b\w\w+\b").map(lambda w: np.mean([x in vocab for x in w]) if w else 0)
print("words known to the model: IT test", round(test["Document"].str.findall(r"\b\w\w+\b").map(lambda w: np.mean([x in vocab for x in w]) if w else 0).mean(), 3), "| support", round(known.mean(), 3))
predicted = pd.Series(labels[proba.argmax(axis=1)])
print("predicted classes on support", predicted.value_counts(normalize=True).round(3).to_dict())
print("predicted class by Ticket Type (should vary if it means something)")
print(pd.crosstab(support["Ticket Type"], predicted, normalize="index").round(2).to_string())
