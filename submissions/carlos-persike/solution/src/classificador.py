"""Classificador de categoria de ticket (Dataset 2 — IT Service Ticket).

Compara baseline burro (classe majoritaria) contra TF-IDF + LinearSVC,
com holdout estratificado e matriz de confusao. Dataset 2 tem texto real
(nao templated como o Dataset 1 — ver auditoria.py), entao serve pra
treinar um classificador de verdade.
"""
import json
from pathlib import Path

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

RAIZ = Path(__file__).resolve().parents[4]
DATASETS = RAIZ / "datasets"
OUTPUTS = RAIZ / "submissions" / "carlos-persike" / "solution" / "outputs"

SEMENTE_ALEATORIA = 42


def carregar() -> pd.DataFrame:
    df = pd.read_csv(DATASETS / "all_tickets_processed_improved_v3.csv")
    return df.dropna(subset=["Document", "Topic_group"])


def treinar(X_treino: pd.Series, y_treino: pd.Series) -> Pipeline:
    # LinearSVC nao expoe predict_proba nativamente; CalibratedClassifierCV
    # seria mais caro pra 46k linhas. Uso decision_function normalizada
    # como proxy de confianca no prototipo (roteador.py).
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=20000, ngram_range=(1, 2), min_df=2)),
        ("clf", LinearSVC(class_weight="balanced", random_state=SEMENTE_ALEATORIA)),
    ])
    pipeline.fit(X_treino, y_treino)
    return pipeline


def separar_treino_teste(df: pd.DataFrame):
    return train_test_split(
        df["Document"], df["Topic_group"],
        test_size=0.2, stratify=df["Topic_group"], random_state=SEMENTE_ALEATORIA,
    )


def treinar_e_avaliar() -> dict:
    df = carregar()
    X_treino, X_teste, y_treino, y_teste = separar_treino_teste(df)

    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(X_treino, y_treino)
    pred_baseline = baseline.predict(X_teste)
    acc_baseline = (pred_baseline == y_teste).mean()

    pipeline = treinar(X_treino, y_treino)
    pred = pipeline.predict(X_teste)

    acc = (pred == y_teste).mean()
    f1_macro = f1_score(y_teste, pred, average="macro")
    relatorio = classification_report(y_teste, pred, zero_division=0)
    matriz = confusion_matrix(y_teste, pred, labels=sorted(df["Topic_group"].unique()))

    resultado = {
        "baseline_classe_majoritaria_acc": round(float(acc_baseline), 4),
        "modelo_tfidf_linearsvc_acc": round(float(acc), 4),
        "modelo_tfidf_linearsvc_f1_macro": round(float(f1_macro), 4),
        "ganho_sobre_baseline_pp": round(float(acc - acc_baseline) * 100, 2),
        "n_treino": len(X_treino),
        "n_teste": len(X_teste),
        "classes": sorted(df["Topic_group"].unique().tolist()),
    }

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / "classificador_metricas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    texto_matriz = "Matriz de confusao (linhas=real, colunas=previsto)\n"
    texto_matriz += "Classes: " + ", ".join(resultado["classes"]) + "\n\n"
    texto_matriz += pd.DataFrame(matriz, index=resultado["classes"], columns=resultado["classes"]).to_string()
    texto_matriz += "\n\n" + relatorio
    (OUTPUTS / "classificador_matriz_confusao.txt").write_text(texto_matriz, encoding="utf-8")

    return resultado


def main() -> None:
    resultado = treinar_e_avaliar()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
