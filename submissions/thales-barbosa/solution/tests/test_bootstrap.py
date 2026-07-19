# -*- coding: utf-8 -*-
"""Contratos do bootstrap multiplataforma da submissão."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bootstrap as bs


def test_progress_requires_marker_complete_and_output(tmp_path):
    marker = tmp_path / "progress.json"
    output = tmp_path / "embeddings.npy"
    marker.write_text(json.dumps({"done": 10, "total": 10}), encoding="utf-8")
    assert not bs._progress_complete(marker, output)
    output.write_bytes(b"ok")
    assert bs._progress_complete(marker, output)


def test_served_model_must_be_multilingual_embedding_classifier(tmp_path):
    meta = tmp_path / "metadata.json"
    meta.write_text(json.dumps({"classifier_type": "tfidf_logreg", "embedder": "MiniLM"}))
    assert not bs._served_model_is_multilingual(meta)
    meta.write_text(json.dumps({
        "classifier_type": "embed_logreg",
        "embedder": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    }))
    assert bs._served_model_is_multilingual(meta)


def test_bootstrap_runs_baseline_before_multilingual_serving(monkeypatch, tmp_path):
    processed = tmp_path / "data" / "processed"
    models = tmp_path / "models"
    processed.mkdir(parents=True)
    models.mkdir()

    processed_files = (
        processed / "tickets_features.parquet",
        processed / "it_tickets_clean.parquet",
    )
    final_files = (
        models / "classifier.joblib",
        models / "faiss.index",
        models / "corpus.parquet",
        models / "metadata.json",
        models / "metrics.json",
        models / "metrics_ml.json",
    )
    monkeypatch.setattr(bs, "ROOT", tmp_path)
    monkeypatch.setattr(bs, "PROCESSED", processed)
    monkeypatch.setattr(bs, "MODELS", models)
    monkeypatch.setattr(bs, "PROCESSED_FILES", processed_files)
    monkeypatch.setattr(bs, "FINAL_MODEL_FILES", final_files)

    calls = []

    def fake_run(script):
        calls.append(script)
        if script == "src/data_prep.py":
            for path in processed_files:
                path.write_bytes(b"data")
        elif script == "src/embed_corpus.py":
            (models / "embeddings_d2.npy").write_bytes(b"en")
            (models / "embed_progress.json").write_text(
                json.dumps({"done": 10, "total": 10}), encoding="utf-8"
            )
        elif script == "src/train_models.py":
            (models / "metrics.json").write_text("{}", encoding="utf-8")
            (models / "corpus.parquet").write_bytes(b"corpus")
        elif script == "src/embed_corpus_ml.py":
            (models / "embeddings_d2_ml.npy").write_bytes(b"ml")
            (models / "embed_progress_ml.json").write_text(
                json.dumps({"done": 10, "total": 10}), encoding="utf-8"
            )
        elif script == "src/train_multilingual.py":
            for name in ("classifier.joblib", "faiss.index"):
                (models / name).write_bytes(b"model")
            (models / "metadata.json").write_text(json.dumps({
                "classifier_type": "embed_logreg",
                "embedder": "paraphrase-multilingual-MiniLM-L12-v2",
            }), encoding="utf-8")
            (models / "metrics_ml.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(bs, "_run", fake_run)
    bs.bootstrap()

    assert calls == [
        "src/data_prep.py",
        "src/embed_corpus.py",
        "src/train_models.py",
        "src/embed_corpus_ml.py",
        "src/train_multilingual.py",
    ]
    assert bs.check()
