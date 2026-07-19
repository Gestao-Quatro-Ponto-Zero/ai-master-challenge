# -*- coding: utf-8 -*-
"""FASE 5 — Classificador de tickets e busca semântica (Dataset 2).

Fonte única dos modelos — treinada por ``python src/train_models.py``,
apresentada em notebooks/ml_models.ipynb e consumida pelo protótipo Streamlit
(FASE 6: AI Copilot). Artefatos ficam em ``models/`` (fora do git se pesados).

Diretrizes herdadas (D-007): split ESTRATIFICADO 80/20 com seed fixa;
métricas principais macro-F1 + F1 por classe (desbalanceamento 7,7:1);
mapeamento de classes congelado (TOPIC_CLASSES, FASE 2); Miscellaneous tratada
via threshold de confiança (gate do fluxo da FASE 4).

Candidatos comparados (exigência do plano: TF-IDF, Sentence Transformers,
Embeddings):
- tfidf_logreg  — TF-IDF (uni+bigramas) + Regressão Logística (probabilística)
- tfidf_linsvc  — TF-IDF + LinearSVC calibrado (CalibratedClassifierCV)
- embed_logreg  — Sentence-Transformers all-MiniLM-L6-v2 + Regressão Logística
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_score,
                             recall_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.data_prep import TOPIC_CLASSES, build_dataset2

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
SEED = 42
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
#: Embedder multilíngue (pt-BR ↔ en no mesmo espaço vetorial) — usado pelo
#: portal do cliente (D-018): pergunta em português encontra tickets em inglês.
MULTILINGUAL_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


# ===========================================================================
# Dados e avaliação
# ===========================================================================

def load_split(test_size: float = 0.2, seed: int = SEED):
    """Split estratificado 80/20 (D-007). Retorna (train_df, test_df)."""
    d2 = build_dataset2()
    tr, te = train_test_split(d2, test_size=test_size, random_state=seed,
                              stratify=d2["Topic_group"])
    return tr.reset_index(drop=True), te.reset_index(drop=True)


def evaluate(y_true, y_pred, model_name: str) -> dict:
    """Métricas exigidas pelo plano + macro (D-007)."""
    return {
        "model": model_name,
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_macro": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "f1_weighted": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "per_class": classification_report(y_true, y_pred, labels=TOPIC_CLASSES,
                                           output_dict=True, zero_division=0),
        "confusion": confusion_matrix(y_true, y_pred, labels=TOPIC_CLASSES).tolist(),
    }


# ===========================================================================
# Candidatos
# ===========================================================================

def make_tfidf_logreg() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_df=0.9,
                                  sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=2000, C=4.0, random_state=SEED)),
    ])


def make_tfidf_linsvc() -> Pipeline:
    # LinearSVC não emite probabilidade -> calibração sigmoide 3-fold
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_df=0.9,
                                  sublinear_tf=True)),
        ("clf", CalibratedClassifierCV(LinearSVC(C=1.0, random_state=SEED),
                                       method="sigmoid", cv=3)),
    ])


_EMBED_MODELS: dict[str, object] = {}


def _get_embedder(model_name: str = EMBED_MODEL_NAME):
    """Singleton por modelo — carregar custa segundos; embutir 1x por nome."""
    if model_name not in _EMBED_MODELS:
        from sentence_transformers import SentenceTransformer
        _EMBED_MODELS[model_name] = SentenceTransformer(model_name, device="cpu")
    return _EMBED_MODELS[model_name]


def embed_texts(texts: list[str], batch_size: int = 256, show_progress: bool = False,
                model_name: str = EMBED_MODEL_NAME) -> np.ndarray:
    """Embeddings normalizados (L2) — usados por classificador E busca."""
    return _get_embedder(model_name).encode(texts, batch_size=batch_size,
                                            normalize_embeddings=True,
                                            show_progress_bar=show_progress)


def make_embed_logreg() -> LogisticRegression:
    return LogisticRegression(max_iter=2000, C=10.0, random_state=SEED)


# ===========================================================================
# Threshold de confiança (gate do fluxo — FASE 4 §6 etapa 3)
# ===========================================================================

def coverage_accuracy_curve(proba: np.ndarray, y_true: np.ndarray,
                            classes: list[str]) -> pd.DataFrame:
    """Para cada threshold: cobertura (% acima) e accuracy dos cobertos."""
    conf = proba.max(axis=1)
    pred = np.asarray(classes)[proba.argmax(axis=1)]
    rows = []
    for t in np.arange(0.30, 0.96, 0.05):
        m = conf >= t
        rows.append({
            "threshold": round(float(t), 2),
            "coverage": float(m.mean()),
            "accuracy_covered": float((pred[m] == np.asarray(y_true)[m]).mean()) if m.any() else np.nan,
            "n_covered": int(m.sum()),
        })
    return pd.DataFrame(rows)


def pick_threshold(curve: pd.DataFrame, min_accuracy: float = 0.90) -> float:
    """Menor threshold cuja accuracy dos cobertos atinge o alvo (maximiza cobertura)."""
    ok = curve[curve["accuracy_covered"] >= min_accuracy]
    return float(ok["threshold"].min()) if len(ok) else float(curve["threshold"].max())


# ===========================================================================
# Artefatos de produção (consumidos pela FASE 6)
# ===========================================================================

class EmbeddingClassifier:
    """Classificador sobre embeddings (D-018): embute o texto com o embedder
    nomeado e delega à LogReg. Picklável (guarda só a LogReg + o nome)."""

    def __init__(self, logreg, embedder_name: str):
        self.logreg = logreg
        self.embedder_name = embedder_name

    @property
    def classes_(self):
        return self.logreg.classes_

    def predict_proba(self, texts) -> np.ndarray:
        emb = embed_texts(list(texts), model_name=self.embedder_name)
        return self.logreg.predict_proba(emb)


@dataclass
class TicketAI:
    """API de inferência do protótipo: classificar + buscar similares."""
    classifier: object          # pipeline TF-IDF OU EmbeddingClassifier
    threshold: float            # gate de confiança (accuracy>=90% nos cobertos)
    corpus: pd.DataFrame        # doc_id, Document, Topic_group (base da busca)
    index: object               # FAISS IndexFlatIP sobre embeddings normalizados
    embedder_name: str = EMBED_MODEL_NAME

    def classify(self, text: str) -> dict:
        proba = self.classifier.predict_proba([text])[0]
        order = np.argsort(proba)[::-1]
        classes = list(self.classifier.classes_)
        top = order[0]
        return {
            "label": classes[top],
            "confidence": float(proba[top]),
            "auto_ok": bool(proba[top] >= self.threshold),  # False -> triagem humana
            "top3": [(classes[i], float(proba[i])) for i in order[:3]],
        }

    def embed(self, text: str) -> np.ndarray:
        """Embedding do texto no espaço do índice (1, dim) — reuso p/ KB."""
        return embed_texts([text], model_name=self.embedder_name).astype(np.float32)

    def find_similar(self, text: str, k: int = 5) -> pd.DataFrame:
        emb = self.embed(text)
        scores, idx = self.index.search(emb, k)
        out = self.corpus.iloc[idx[0]][["doc_id", "Document", "Topic_group"]].copy()
        out["similarity"] = scores[0]
        return out.reset_index(drop=True)


def save_artifacts(classifier, threshold: float, corpus: pd.DataFrame,
                   embeddings: np.ndarray, metrics: dict) -> None:
    import faiss
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(classifier, MODELS_DIR / "classifier.joblib")
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings.astype(np.float32))
    faiss.write_index(index, str(MODELS_DIR / "faiss.index"))
    corpus[["doc_id", "Document", "Topic_group"]].to_parquet(MODELS_DIR / "corpus.parquet")
    np.save(MODELS_DIR / "embeddings.npy", embeddings.astype(np.float32))
    (MODELS_DIR / "metadata.json").write_text(json.dumps({
        "threshold": threshold, "embedder": EMBED_MODEL_NAME,
        "classes": TOPIC_CLASSES, "seed": SEED,
    }, indent=2), encoding="utf-8")
    (MODELS_DIR / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")


def load_ticket_ai() -> TicketAI:
    import faiss
    meta = json.loads((MODELS_DIR / "metadata.json").read_text(encoding="utf-8"))
    clf = joblib.load(MODELS_DIR / "classifier.joblib")
    # pipeline multilíngue (D-018): a LogReg salva opera sobre embeddings —
    # reconstrói o wrapper que embute com o embedder do metadata
    if meta.get("classifier_type") == "embed_logreg" and not isinstance(clf, EmbeddingClassifier):
        clf = EmbeddingClassifier(clf, meta["embedder"])
    return TicketAI(
        classifier=clf,
        threshold=meta["threshold"],
        corpus=pd.read_parquet(MODELS_DIR / "corpus.parquet"),
        index=faiss.read_index(str(MODELS_DIR / "faiss.index")),
        embedder_name=meta["embedder"],
    )
