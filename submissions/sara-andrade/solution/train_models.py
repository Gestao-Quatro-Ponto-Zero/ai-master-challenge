from __future__ import annotations

import json
from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
SOLUTION = Path(__file__).resolve().parent
MODEL_DIR = SOLUTION / "models"
OUT_DIR = SOLUTION / "outputs"
MODEL_DIR.mkdir(exist_ok=True)
(OUT_DIR / "tables").mkdir(parents=True, exist_ok=True)

D1_CANDIDATES = [
    ROOT / "data" / "customer_support_tickets.csv",
    ROOT / "customer_support_tickets.csv",
    Path("/mnt/data/customer_support_tickets.csv"),
]
D2_CANDIDATES = [
    ROOT / "data" / "all_tickets_processed_improved_v3.csv",
    ROOT / "all_tickets_processed_improved_v3.csv",
    Path("/mnt/data/all_tickets_processed_improved_v3.csv"),
]


def find_file(candidates: list[Path]) -> Path:
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"Arquivo não encontrado. Tente uma destas localizações: {candidates}")


def gate_table(model_name: str, y_true, y_pred, max_conf) -> list[dict]:
    rows = []
    for th in [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95]:
        mask = max_conf >= th
        rows.append(
            {
                "model": model_name,
                "threshold": th,
                "coverage": float(mask.mean()),
                "accuracy_in_gate": float(accuracy_score(y_true[mask], y_pred[mask])) if mask.any() else None,
                "n_in_gate": int(mask.sum()),
            }
        )
    return rows


def evaluate(pipe, name: str, X_train, X_test, y_train, y_test):
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    proba = pipe.predict_proba(X_test)
    max_conf = proba.max(axis=1)
    return {
        "model": pipe,
        "name": name,
        "accuracy": float(accuracy_score(y_test, pred)),
        "f1_macro": float(f1_score(y_test, pred, average="macro")),
        "f1_weighted": float(f1_score(y_test, pred, average="weighted")),
        "gate": gate_table(name, y_test, pred, max_conf),
    }


def main():
    d1 = pd.read_csv(find_file(D1_CANDIDATES))
    d2 = pd.read_csv(find_file(D2_CANDIDATES))

    # Data audit
    closed = d1[d1["Ticket Status"] == "Closed"].copy()
    closed["fr"] = pd.to_datetime(closed["First Response Time"], errors="coerce")
    closed["tr"] = pd.to_datetime(closed["Time to Resolution"], errors="coerce")
    closed["delta_hours"] = (closed["tr"] - closed["fr"]).dt.total_seconds() / 3600

    status_counts = d1["Ticket Status"].value_counts()
    csat_counts = closed["Customer Satisfaction Rating"].dropna().astype(int).value_counts().sort_index()
    csat_chi = stats.chisquare(csat_counts.values)
    status_channel_p = stats.chi2_contingency(pd.crosstab(d1["Ticket Status"], d1["Ticket Channel"]))[1]
    valid = closed[closed["delta_hours"] >= 0].copy()
    kr_channel_p = stats.kruskal(*[g["delta_hours"].values for _, g in valid.groupby("Ticket Channel")]).pvalue

    # Dataset 1 weak text signal
    X1 = (d1["Ticket Subject"].fillna("") + " " + d1["Ticket Description"].fillna("")).astype(str)
    y1 = d1["Ticket Type"].astype(str)
    X1_train, X1_test, y1_train, y1_test = train_test_split(
        X1, y1, test_size=0.2, stratify=y1, random_state=42
    )
    d1_probe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(min_df=2, max_features=20000, ngram_range=(1, 2), sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=150, solver="saga", random_state=42, n_jobs=1)),
        ]
    )
    d1_probe.fit(X1_train, y1_train)
    d1_probe_pred = d1_probe.predict(X1_test)

    # Dataset 2 models
    X = d2["Document"].fillna("").astype(str)
    y = d2["Topic_group"].astype(str)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    nb = Pipeline(
        [
            ("tfidf", TfidfVectorizer(min_df=3, max_features=30000, ngram_range=(1, 2), sublinear_tf=True)),
            ("clf", ComplementNB(alpha=0.1)),
        ]
    )
    logreg = Pipeline(
        [
            ("tfidf", TfidfVectorizer(min_df=3, max_features=20000, ngram_range=(1, 2), sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=150, solver="saga", C=2.0, random_state=42, n_jobs=1)),
        ]
    )

    nb_res = evaluate(nb, "ComplementNB baseline", X_train, X_test, y_train, y_test)
    lr_res = evaluate(logreg, "LogisticRegression selected", X_train, X_test, y_train, y_test)

    # Domain router
    n = min(len(d1), len(d2))
    d1_text = (d1["Ticket Subject"].fillna("") + " " + d1["Ticket Description"].fillna("")).astype(str)
    d2_text = d2["Document"].fillna("").astype(str)
    Xdom = pd.concat(
        [d1_text.sample(n, random_state=42), d2_text.sample(n, random_state=42)], ignore_index=True
    )
    ydom = pd.Series(["B2C_EXTERNAL"] * n + ["B2E_IT"] * n)
    Xdom_train, Xdom_test, ydom_train, ydom_test = train_test_split(
        Xdom, ydom, test_size=0.2, stratify=ydom, random_state=42
    )
    domain_router = Pipeline(
        [
            ("tfidf", TfidfVectorizer(min_df=2, max_features=20000, ngram_range=(1, 2), sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=100, solver="saga", random_state=42, n_jobs=1)),
        ]
    )
    domain_router.fit(Xdom_train, ydom_train)
    dom_pred = domain_router.predict(Xdom_test)

    # Domain shift: IT classifier applied to Dataset 1
    d1_as_it_pred = lr_res["model"].predict(d1_text)
    d1_as_it_proba = lr_res["model"].predict_proba(d1_text)
    d1_as_it_conf = d1_as_it_proba.max(axis=1)

    joblib.dump(lr_res["model"], MODEL_DIR / "topic_classifier_logreg.joblib")
    joblib.dump(nb_res["model"], MODEL_DIR / "topic_classifier_nb_baseline.joblib")
    joblib.dump(domain_router, MODEL_DIR / "domain_router_b2c_b2e.joblib")

    pd.DataFrame(lr_res["gate"]).to_csv(OUT_DIR / "tables" / "gate_table_logreg.csv", index=False)
    pd.DataFrame(nb_res["gate"]).to_csv(OUT_DIR / "tables" / "gate_table_nb.csv", index=False)
    pd.DataFrame(
        [
            {"model": nb_res["name"], "accuracy": nb_res["accuracy"], "f1_macro": nb_res["f1_macro"]},
            {"model": lr_res["name"], "accuracy": lr_res["accuracy"], "f1_macro": lr_res["f1_macro"]},
        ]
    ).to_csv(OUT_DIR / "tables" / "model_comparison.csv", index=False)

    metrics = {
        "dataset_1_rows": int(len(d1)),
        "dataset_2_rows": int(len(d2)),
        "status_counts": {k: int(v) for k, v in status_counts.items()},
        "non_closed_pct": float((d1["Ticket Status"] != "Closed").mean() * 100),
        "pending_customer_response_pct": float((d1["Ticket Status"] == "Pending Customer Response").mean() * 100),
        "negative_delta_pct_closed": float((closed["delta_hours"] < 0).mean() * 100),
        "templated_description_pct": float(d1["Ticket Description"].str.contains("{product_purchased}", regex=False, na=False).mean() * 100),
        "csat_uniform_chi_square_pvalue": float(csat_chi.pvalue),
        "status_channel_chi_square_pvalue": float(status_channel_p),
        "kruskal_positive_delta_by_channel_pvalue": float(kr_channel_p),
        "d1_text_to_ticket_type_accuracy": float(accuracy_score(y1_test, d1_probe_pred)),
        "d1_text_to_ticket_type_f1_macro": float(f1_score(y1_test, d1_probe_pred, average="macro")),
        "d2_nb_accuracy": nb_res["accuracy"],
        "d2_nb_f1_macro": nb_res["f1_macro"],
        "d2_logreg_accuracy": lr_res["accuracy"],
        "d2_logreg_f1_macro": lr_res["f1_macro"],
        "domain_router_accuracy": float(accuracy_score(ydom_test, dom_pred)),
        "d1_as_it_predicted_distribution": pd.Series(d1_as_it_pred).value_counts().to_dict(),
        "d1_as_it_mean_confidence": float(np.mean(d1_as_it_conf)),
    }
    (OUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
