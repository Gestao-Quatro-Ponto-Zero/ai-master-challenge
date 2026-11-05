"""Ticket classifier and the policy that decides what a machine may do with it.

The file has no dates, so row order stands in for time. The model learns from the
first 80% of rows and is judged on the last 20%, which is harder than a random split.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

IT_FILE = "all_tickets_processed_improved_v3.csv"
SUPPORT_FILE = "customer_support_tickets.csv"

TEST_SHARE = 0.2
VOCABULARY_SIZE = 5000
ROUTE_CONFIDENCE = 0.9
SUGGEST_CONFIDENCE = 0.5
GUARD_PERCENTILE = 5

ROUTE, SUGGEST, HUMAN = "rotear", "sugerir", "humano"

# Product decisions, not findings: a wrong move here harms a person or grants access.
SENSITIVE_WORDS = frozenset(
    {"termination", "terminated", "resign", "resignation", "dismissal", "salary", "payroll", "complaint", "harassment", "breach", "legal", "lawsuit", "fraud"}
)
NEVER_ROUTE_CATEGORIES = frozenset({"Administrative rights"})

TOKEN = re.compile(r"\b\w\w+\b")


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(str(text).lower())


@dataclass
class TriageModel:
    vectorizer: TfidfVectorizer
    classifier: LogisticRegression
    guard: float

    @property
    def categories(self) -> np.ndarray:
        return self.classifier.classes_

    def known_share(self, texts: pd.Series) -> np.ndarray:
        vocabulary = self.vectorizer.vocabulary_
        shares = []
        for text in texts.fillna(""):
            words = tokenize(text)
            shares.append(float(np.mean([word in vocabulary for word in words])) if words else 0.0)
        return np.array(shares)

    def probabilities(self, texts: pd.Series) -> np.ndarray:
        return self.classifier.predict_proba(self.vectorizer.transform(texts.fillna("")))


def load_it_tickets(data_dir: str | Path) -> pd.DataFrame:
    return pd.read_csv(Path(data_dir) / IT_FILE)


def load_support_tickets(data_dir: str | Path) -> pd.DataFrame:
    return pd.read_csv(Path(data_dir) / SUPPORT_FILE)


def split_by_order(tickets: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Train and guard rows come from the first 80%, and the test set is the last 20%."""
    cut = int(len(tickets) * (1 - TEST_SHARE))
    early, late = tickets.iloc[:cut], tickets.iloc[cut:]
    train, validation = train_test_split(early, test_size=0.25, random_state=0, stratify=early["Topic_group"])
    return train, validation, late


def train_model(train: pd.DataFrame, validation: pd.DataFrame) -> TriageModel:
    vectorizer = TfidfVectorizer(sublinear_tf=True, max_features=VOCABULARY_SIZE)
    features = vectorizer.fit_transform(train["Document"])
    classifier = LogisticRegression(max_iter=400, C=10).fit(features, train["Topic_group"])
    model = TriageModel(vectorizer, classifier, guard=0.0)
    model.guard = float(np.percentile(model.known_share(validation["Document"]), GUARD_PERCENTILE))
    return model


def has_sensitive_word(text: str) -> bool:
    return any(word in SENSITIVE_WORDS for word in tokenize(text))


def decide(confidence: float, category: str, known_share: float, sensitive: bool, guard: float) -> tuple[str, str]:
    """Return the lane and its reason. Checks run from most to least protective."""
    if sensitive:
        return HUMAN, "sensivel"
    if known_share < guard:
        return HUMAN, "desconhecido"
    if confidence < SUGGEST_CONFIDENCE:
        return HUMAN, "incerto"
    if category in NEVER_ROUTE_CATEGORIES:
        return SUGGEST, "categoria_protegida"
    if confidence < ROUTE_CONFIDENCE:
        return SUGGEST, "confianca_media"
    return ROUTE, "confianca_alta"


def triage_frame(model: TriageModel, texts: pd.Series) -> pd.DataFrame:
    """Everything the policy needs for each ticket."""
    proba = model.probabilities(texts)
    order = np.argsort(-proba, axis=1)
    frame = pd.DataFrame(
        {
            "predicted": model.categories[order[:, 0]],
            "second": model.categories[order[:, 1]],
            "confidence": proba.max(axis=1),
            "known": model.known_share(texts),
            "sensitive": [has_sensitive_word(text) for text in texts.fillna("")],
        },
        index=texts.index,
    )
    decisions = [decide(c, p, k, s, model.guard) for c, p, k, s in zip(frame["confidence"], frame["predicted"], frame["known"], frame["sensitive"])]
    frame["lane"] = [item[0] for item in decisions]
    frame["reason"] = [item[1] for item in decisions]
    return frame
