"""
Transformer-based zero-shot classifier using HuggingFace pipeline.
Wraps the model for classification and embedding-based similarity search.
"""

import logging
from functools import lru_cache
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
from config import CLASSIFIER_MODEL, EMBEDDING_MODEL, TOPIC_LABELS, DATASET1_PATH

logger = logging.getLogger(__name__)


class TicketClassifier:
    def __init__(self):
        self._classifier = None
        self._embedder = None
        self._resolution_embeddings = None
        self._resolution_data = None

    def _load_classifier(self):
        if self._classifier is None:
            logger.info("Loading zero-shot classifier: %s", CLASSIFIER_MODEL)
            self._classifier = pipeline(
                "zero-shot-classification",
                model=CLASSIFIER_MODEL,
                device=-1,
            )
        return self._classifier

    def _load_embedder(self):
        if self._embedder is None:
            logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
            self._embedder = SentenceTransformer(EMBEDDING_MODEL)
        return self._embedder

    def _load_resolution_corpus(self):
        """Pre-compute embeddings for resolved tickets from Dataset 1."""
        if self._resolution_data is not None:
            return

        logger.info("Loading resolution corpus from Dataset 1...")
        df = pd.read_csv(DATASET1_PATH)
        closed = df[df["Ticket Status"] == "Closed"].dropna(subset=["Resolution", "Ticket Description"])
        closed = closed[closed["Resolution"].str.len() > 10]

        self._resolution_data = closed[["Ticket Description", "Resolution"]].reset_index(drop=True)

        embedder = self._load_embedder()
        texts = self._resolution_data["Ticket Description"].tolist()
        logger.info("Computing embeddings for %d resolved tickets...", len(texts))
        self._resolution_embeddings = embedder.encode(texts, show_progress_bar=False, batch_size=64)
        logger.info("Resolution corpus ready.")

    def classify(self, text: str, labels: list[str] | None = None) -> dict:
        clf = self._load_classifier()
        candidate_labels = labels or TOPIC_LABELS

        result = clf(text, candidate_labels, multi_label=False)

        scores = {label: round(score, 4) for label, score in zip(result["labels"], result["scores"])}
        best_label = result["labels"][0]
        best_score = result["scores"][0]

        return {
            "category": best_label,
            "confidence": round(best_score, 4),
            "all_scores": scores,
        }

    def find_similar_tickets(self, text: str, top_k: int = 3) -> list[dict]:
        self._load_resolution_corpus()
        embedder = self._load_embedder()

        query_emb = embedder.encode([text])
        similarities = np.dot(self._resolution_embeddings, query_emb.T).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "text": self._resolution_data.iloc[idx]["Ticket Description"],
                "resolution": self._resolution_data.iloc[idx]["Resolution"],
                "similarity_score": round(float(similarities[idx]), 4),
            })
        return results


@lru_cache(maxsize=1)
def get_classifier() -> TicketClassifier:
    return TicketClassifier()
