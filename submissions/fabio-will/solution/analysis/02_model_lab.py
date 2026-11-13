"""Model lab: which ticket router is worth shipping, and how much can it route alone?

Protocol
- Dataset 2 split 70/15/15 (stratified, fixed seed). Thresholds are chosen on validation and
  reported on test, so the coverage numbers are not tuned on the data they are reported on.
- Candidates: majority class, Complement Naive Bayes, logistic regression on word 1-2 grams,
  linear SVM (calibrated), logistic regression on character 3-5 grams.
- Confidence gate: auto-route when max probability >= t_auto (precision >= 95% on validation),
  suggest to a human when >= t_assist (precision >= 80%), else manual triage.
- Domain shift: apply the router to Dataset 1 descriptions (customer product tickets) to check
  that out-of-domain text falls below the gate instead of being routed with false confidence.
Outputs: outputs/lab.json
"""
from __future__ import annotations

import time

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from common import load_tickets, write_json
from router import AUTO_PRECISION, expected_calibration_error, gate_curve, make_split, pick_threshold, word_tfidf

ASSIST_PRECISION = 0.80


def candidates() -> dict[str, Pipeline]:
    return {
        "majority": Pipeline([("tfidf", word_tfidf()), ("clf", DummyClassifier(strategy="most_frequent"))]),
        "complement_nb": Pipeline([("tfidf", word_tfidf()), ("clf", ComplementNB(alpha=0.3))]),
        "logreg_word": Pipeline([("tfidf", word_tfidf()), ("clf", LogisticRegression(C=8, max_iter=2000))]),
        "svm_word_calibrated": Pipeline([("tfidf", word_tfidf()), ("clf", CalibratedClassifierCV(LinearSVC(C=0.5), cv=3, method="sigmoid"))]),
        "logreg_char": Pipeline([
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, max_features=60000, sublinear_tf=True)),
            ("clf", LogisticRegression(C=8, max_iter=2000)),
        ]),
    }


def main() -> None:
    sp = make_split()
    X_train, X_val, X_test, y_train, y_val, y_test = sp.X_train, sp.X_val, sp.X_test, sp.y_train, sp.y_val, sp.y_test
    classes = sorted(set(y_train))

    results = {}
    fitted = {}
    for name, pipe in candidates().items():
        t0 = time.perf_counter()
        pipe.fit(X_train, y_train)
        fit_s = time.perf_counter() - t0
        t0 = time.perf_counter()
        proba = pipe.predict_proba(X_test)
        infer_ms_per_1k = (time.perf_counter() - t0) / len(X_test) * 1000 * 1000
        pred = pipe.classes_[proba.argmax(1)]
        conf = proba.max(1)
        correct = pred == y_test
        p, r, f, s = precision_recall_fscore_support(y_test, pred, labels=classes, zero_division=0)
        results[name] = {
            "accuracy": round(float(accuracy_score(y_test, pred)), 4),
            "macro_f1": round(float(f1_score(y_test, pred, average="macro", zero_division=0)), 4),
            "weighted_f1": round(float(f1_score(y_test, pred, average="weighted", zero_division=0)), 4),
            "ece": round(expected_calibration_error(conf, correct), 4),
            "fit_seconds": round(fit_s, 1),
            "infer_ms_per_1k": round(infer_ms_per_1k, 1),
            "per_class": {c: {"precision": round(float(p[i]), 3), "recall": round(float(r[i]), 3), "f1": round(float(f[i]), 3), "support": int(s[i])} for i, c in enumerate(classes)},
        }
        fitted[name] = pipe
        print(f"{name:22s} acc={results[name]['accuracy']:.4f} macroF1={results[name]['macro_f1']:.4f} ece={results[name]['ece']:.4f} fit={fit_s:.1f}s")

    # Gate on the browser-portable model (logistic regression on words): thresholds from validation.
    chosen = "logreg_word"
    pipe = fitted[chosen]
    val_proba = pipe.predict_proba(X_val)
    val_curve = gate_curve(val_proba.max(1), pipe.classes_[val_proba.argmax(1)] == y_val)
    t_auto = pick_threshold(val_curve, AUTO_PRECISION)
    t_assist = pick_threshold(val_curve, ASSIST_PRECISION)

    test_proba = pipe.predict_proba(X_test)
    test_pred = pipe.classes_[test_proba.argmax(1)]
    test_conf = test_proba.max(1)
    test_correct = test_pred == y_test
    tiers = {
        "auto": test_conf >= t_auto,
        "assist": (test_conf >= t_assist) & (test_conf < t_auto),
        "human": test_conf < t_assist,
    }
    gate = {
        "model": chosen,
        "t_auto": t_auto,
        "t_assist": t_assist,
        "targets": {"auto_precision": AUTO_PRECISION, "assist_precision": ASSIST_PRECISION},
        "test": {k: {"share": round(float(m.mean()), 4), "precision": round(float(test_correct[m].mean()), 4) if m.any() else None} for k, m in tiers.items()},
        "test_curve": gate_curve(test_conf, test_correct),
        "auto_share_by_class": {c: round(float((tiers["auto"] & (y_test == c)).sum() / (y_test == c).sum()), 3) for c in classes},
    }
    print(f"gate: t_auto={t_auto} t_assist={t_assist} → {gate['test']}")

    cm = confusion_matrix(y_test, test_pred, labels=classes)

    # Out-of-domain check on Dataset 1 descriptions.
    d1 = load_tickets()
    d1_text = (d1["Ticket Subject"].fillna("") + " " + d1["Ticket Description"].fillna("")).str.replace("{product_purchased}", "product", regex=False).str.lower().values
    d1_proba = pipe.predict_proba(d1_text)
    d1_conf = d1_proba.max(1)
    d1_pred = pipe.classes_[d1_proba.argmax(1)]
    domain_shift = {
        "records": int(len(d1_text)),
        "predicted_distribution": {k: int(v) for k, v in zip(*np.unique(d1_pred, return_counts=True))},
        "median_confidence": round(float(np.median(d1_conf)), 3),
        "would_auto_route_share": round(float((d1_conf >= t_auto).mean()), 4),
        "would_go_to_human_share": round(float((d1_conf < t_assist).mean()), 4),
        "in_domain_median_confidence": round(float(np.median(test_conf)), 3),
    }
    print(f"domain shift: {domain_shift}")

    # Size vs quality trade-off for shipping the model to the browser.
    size_tradeoff = []
    for k in [3000, 6000, 10000, 20000]:
        p = Pipeline([("tfidf", word_tfidf(k)), ("clf", LogisticRegression(C=8, max_iter=2000))]).fit(X_train, y_train)
        pr = p.predict(X_test)
        size_tradeoff.append({"max_features": k, "accuracy": round(float(accuracy_score(y_test, pr)), 4), "macro_f1": round(float(f1_score(y_test, pr, average="macro")), 4)})
    print(f"size trade-off: {size_tradeoff}")

    write_json("lab.json", {
        "split": {"train": len(X_train), "val": len(X_val), "test": len(X_test), "seed": 42},
        "classes": classes,
        "models": results,
        "gate": gate,
        "confusion_matrix": {"labels": classes, "matrix": cm.tolist()},
        "domain_shift": domain_shift,
        "size_tradeoff": size_tradeoff,
    })


if __name__ == "__main__":
    main()
