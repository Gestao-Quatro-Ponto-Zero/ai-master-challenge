#!/usr/bin/env python3
"""Verify the locked V00 runtime and construct candidates without fitting them."""

import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import re
import sqlite3
import sys


ROOT = Path(__file__).resolve().parents[1]


def check():
    from sklearn.dummy import DummyClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    import streamlit

    canonical = lambda name: re.sub(r"[-_.]+", "-", name).lower()
    lock = ROOT / "requirements.lock"
    expected = {}
    for line in lock.read_text().splitlines():
        if line and not line.startswith("#"):
            name, version = line.split("==")
            expected[canonical(name)] = version
    installed = {canonical(item.metadata["Name"]): item.version for item in metadata.distributions()}
    if expected != installed:
        raise ValueError("Installed environment differs from requirements.lock")
    config = json.loads((ROOT / "data/evaluation-protocol.json").read_text())
    objects = []
    constructors = {"DummyClassifier": DummyClassifier, "MultinomialNB": MultinomialNB,
                    "LogisticRegression": LogisticRegression}
    for candidate in config["model_selection"]["candidates"]:
        params = {key: value for key, value in candidate.items() if key not in {"id", "role", "estimator"}}
        model = constructors[candidate["estimator"]](**params)
        if candidate["id"] != "majority":
            features = dict(config["model_selection"]["tfidf"])
            features["ngram_range"] = tuple(features["ngram_range"])
            model = Pipeline([("tfidf", TfidfVectorizer(**features)), ("classifier", model)])
        if hasattr(model, "classes_"):
            raise AssertionError("V00 must not fit models")
        objects.append(candidate["id"])
    with sqlite3.connect(":memory:") as connection:
        connection.execute("CREATE TABLE smoke (value TEXT)")
        connection.execute("INSERT INTO smoke VALUES (?)", ("fixture",))
        connection.rollback()
        assert connection.execute("SELECT count(*) FROM smoke").fetchone()[0] == 0
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    return {"python": platform.python_version(), "platform": sys.platform, "machine": platform.machine(),
            "sqlite": sqlite3.sqlite_version, "packages": dict(sorted(installed.items())),
            "unfitted_candidates_constructed": objects, "streamlit_imported": bool(streamlit.__version__),
            "sqlite_memory_transaction_rollback": True, "model_fits": 0,
            "input_sha256": {name: digest(ROOT / name) for name in
                             ["requirements.in", "requirements.lock", "data/evaluation-protocol.json",
                              "solution/check_evaluation_environment.py"]},
            "limits": "Import/constructor/SQLite checks only; no trained model, UI or performance evaluation"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/review-evidence/evaluation-environment.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = check()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in ["python", "platform", "unfitted_candidates_constructed", "model_fits"]}, indent=2))
