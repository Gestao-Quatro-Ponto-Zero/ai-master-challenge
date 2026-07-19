# -*- coding: utf-8 -*-
"""Testes da FASE 5 — contratos do split, métricas e gate de confiança.

Testes rápidos (sem rede/torch): embeddings e FAISS são exercitados pelo
script de treino e verificados via artefatos no notebook.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_prep import TOPIC_CLASSES
from src.ticket_ai import (coverage_accuracy_curve, evaluate, load_split,
                           make_tfidf_logreg, pick_threshold)


@pytest.fixture(scope="module")
def split():
    return load_split()


def test_split_is_stratified_and_disjoint(split):
    train, test = split
    assert len(train) + len(test) == 47_823
    assert abs(len(test) / 47_823 - 0.2) < 0.001
    assert not set(train["doc_id"]).intersection(test["doc_id"])
    ptr = train["Topic_group"].value_counts(normalize=True)
    pte = test["Topic_group"].value_counts(normalize=True)
    assert (ptr - pte).abs().max() < 0.005  # proporções preservadas (D-007)


def test_split_deterministic(split):
    train2, _ = load_split()
    assert train2["doc_id"].tolist() == split[0]["doc_id"].tolist()


def test_evaluate_reports_required_metrics():
    y = ["Hardware", "Access", "Hardware", "Storage"]
    p = ["Hardware", "Access", "Access", "Storage"]
    r = evaluate(y, p, "toy")
    assert {"accuracy", "precision_macro", "recall_macro", "f1_macro",
            "per_class", "confusion"} <= set(r)
    assert r["accuracy"] == 0.75
    assert len(r["confusion"]) == len(TOPIC_CLASSES)


def test_coverage_curve_and_threshold_logic():
    # 4 previsões: confianças 0.95/0.90/0.60/0.40; acertos nas 2 primeiras
    proba = np.array([[0.95, 0.05], [0.90, 0.10], [0.60, 0.40], [0.40, 0.60]])
    y = np.array(["A", "A", "B", "A"])  # pred: A A A B -> acertos: sim sim não não
    curve = coverage_accuracy_curve(proba, y, ["A", "B"])
    assert curve.loc[curve["threshold"] == 0.90, "coverage"].iloc[0] == 0.5
    assert curve.loc[curve["threshold"] == 0.90, "accuracy_covered"].iloc[0] == 1.0
    thr = pick_threshold(curve, min_accuracy=0.90)
    # erradas têm conf 0.60 -> 0.65 é o MENOR threshold que as exclui (accuracy=1.0)
    assert thr == 0.65


def test_classifier_contract_on_small_sample(split):
    train, _ = split
    sample = train.groupby("Topic_group", observed=True).head(60)
    m = make_tfidf_logreg()
    m.fit(sample["Document"].tolist(), sample["Topic_group"].astype(str).values)
    proba = m.predict_proba(["please reset my password for the external account"])
    assert proba.shape == (1, 8)
    assert abs(proba.sum() - 1) < 1e-6
    assert set(m.classes_) == set(TOPIC_CLASSES)
