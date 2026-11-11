"""PASSO 1 — Modelos clássicos de classificação de tickets.

Protocolo de validação: holdout estratificado 80/20, seed 7, ÚNICO split
para todos os modelos. random_state=7 em tudo que é estocástico.

Modelos comparados no MESMO split:
  a) TF-IDF word 1-2g + LinearSVC
  b) TF-IDF word 1-2g + LogReg
  c) TF-IDF char 3-5g + LinearSVC
  d) Ensemble soft: FeatureUnion(word tfidf, char tfidf) + LinearSVC
  e) VotingClassifier (soft, proba de LogReg) word+char + LogReg final

Saída: solution/artifacts/model_best.joblib (pipeline completo do melhor
modelo por acurácia de teste) + tabela de resultados impressa.
"""

import json
import time
from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import VotingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

SEED = 7
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasources" / "all_tickets_processed_improved_v3.csv"
ART = ROOT / "artifacts"


def build_models():
    word = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2, max_features=200_000)
    char = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), sublinear_tf=True, min_df=2, max_features=500_000)

    models = {
        "tfidf_word12_svm": Pipeline([
            ("vec", word),
            ("clf", LinearSVC(random_state=SEED)),
        ]),
        "tfidf_word12_logreg": Pipeline([
            ("vec", word),
            ("clf", LogisticRegression(max_iter=2000, C=10.0, random_state=SEED)),
        ]),
        "tfidf_char35_svm": Pipeline([
            ("vec", char),
            ("clf", LinearSVC(random_state=SEED)),
        ]),
        "tfidf_wordchar_svm": Pipeline([
            ("features", FeatureUnion([
                ("word", word),
                ("char", char),
            ])),
            ("clf", LinearSVC(random_state=SEED)),
        ]),
    }

    # (e) VotingClassifier soft — usa proba de LogReg em word e char.
    vote = VotingClassifier(
        estimators=[
            ("w", Pipeline([
                ("vec", word),
                ("clf", LogisticRegression(max_iter=2000, C=10.0, random_state=SEED)),
            ])),
            ("c", Pipeline([
                ("vec", char),
                ("clf", LogisticRegression(max_iter=2000, C=10.0, random_state=SEED)),
            ])),
        ],
        voting="soft",
        n_jobs=-1,
    )
    models["voting_wordchar_logreg"] = vote
    return models


def main():
    df = pd.read_csv(DATA)
    X_train, X_test, y_train, y_test = train_test_split(
        df["Document"], df["Topic_group"], test_size=0.20, random_state=SEED, stratify=df["Topic_group"]
    )
    print(f"train={len(X_train)} test={len(X_test)} classes={df['Topic_group'].nunique()}")

    results = {}
    best_name, best_score, best_model = None, -1.0, None
    for name, model in build_models().items():
        t0 = time.time()
        model.fit(X_train, y_train)
        acc = accuracy_score(y_test, model.predict(X_test))
        dt = time.time() - t0
        results[name] = {"accuracy": round(acc, 4), "fit_seconds": round(dt, 1)}
        print(f"{name:26s} acc={acc:.4f}  ({dt:.1f}s)")
        if acc > best_score:
            best_name, best_score, best_model = name, acc, model

    ART.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, ART / "model_best.joblib")
    (ART / "step1_results.json").write_text(
        json.dumps({"results": results, "best": best_name, "best_accuracy": best_score}, indent=2)
    )
    print(f"\nBEST: {best_name} acc={best_score:.4f} -> artifacts/model_best.joblib")


if __name__ == "__main__":
    main()
