#!/usr/bin/env python3
"""Audit recorded final-test outputs without loading models or predicting again."""

import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solution"))
from evaluate_triage import LOCAL, OUTPUT, completed_result, frozen_members, verify_freeze
from triage.artifacts import BUNDLE, load_metadata, sha256, write_json
from triage.core import CLASSES, from_scores, normalize
from triage.evaluation import acceptance, summarize_assisted
import csv


def check():
    frozen = verify_freeze()
    report = completed_result()
    if report is None:
        raise ValueError("No completed final evaluation to audit")
    for name, expected in report["local_output_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise ValueError(f"Recorded local output changed: {name}")
    manifest, policy, reference = load_metadata()
    members = frozen_members()
    by_index = {int(row["row_index"]): row["case_id"] for row in members}
    observed = {}
    with (ROOT / "data/raw/it_service-v1.csv").open(encoding="utf-8-sig", newline="") as handle:
        for i, row in enumerate(csv.DictReader(handle), 1):
            if i in by_index:
                observed[by_index[i]] = (row["Topic_group"], len(normalize(row["Document"])))
    cache = json.loads((ROOT / LOCAL / "predictions.json").read_text())
    assert cache["classes"] == list(CLASSES)
    assert set(cache["case_ids"]) == set(observed) and len(cache["case_ids"]) == report["population"]
    db = ROOT / LOCAL / "offline.sqlite3"
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as connection:
        runs = {case: json.loads(value) for case, value in connection.execute("SELECT case_id,result_json FROM runs")}
    truth, saved = [], []
    for case, scores, known in zip(cache["case_ids"], cache["scores"], cache["known_features"], strict=True):
        actual, length = observed[case]
        replayed = from_scores(CLASSES, scores, known, length, policy, reference)
        assert all(replayed[key] == runs[case][key] for key in replayed), case
        truth.append(actual)
        saved.append(runs[case])
    assisted = summarize_assisted(truth, saved)
    assert all(report["assisted"][key] == value for key, value in assisted.items())
    for metrics in report["classifier_metrics"].values():
        matrix = metrics["confusion"]
        assert len(matrix) == len(CLASSES) and all(len(row) == len(CLASSES) for row in matrix)
        assert sum(map(sum, matrix)) == report["population"]
        f1 = []
        for i, label in enumerate(CLASSES):
            support = sum(matrix[i])
            predicted = sum(row[i] for row in matrix)
            f1.append(2 * matrix[i][i] / (support + predicted) if support + predicted else 0)
            assert metrics["per_class"][label]["support"] == support
            assert abs(metrics["per_class"][label]["f1-score"] - f1[-1]) <= 1e-12
        assert abs(sum(f1) / len(CLASSES) - metrics["macro_f1"]) <= 1e-12
        assert abs(sum(matrix[i][i] for i in range(8)) / report["population"] - metrics["accuracy"]) <= 1e-12
    accepted = acceptance(report["classifier_metrics"], report["selected_model"], assisted,
                          json.loads((ROOT / "data/evaluation-protocol.json").read_text()))
    assert accepted["checks"] == report["acceptance"]["checks"]
    assert len(frozen["runtime_case_ids"]) == report["runtime_sample"]["attempted"]
    return {"scope": "Reaggregation of recorded score vectors, frozen references, SQLite decisions and public confusion matrices only",
            "model_loads": 0, "new_predictions": 0, "classifier_fits": 0,
            "cached_decisions_replayed_and_matched": len(saved),
            "all_three_model_confusion_metrics_reconciled": True,
            "assisted_denominators_and_acceptance_reconciled": True,
            "all_frozen_inputs_and_local_output_hashes_match": True,
            "limits": "External-clock latency aggregates are recorded by the frozen driver; individual external-clock samples were not persisted for reaggregation. SQLite elapsed_ms is a distinct pre-persistence clock, not a substitute.",
            "input_sha256": {name: sha256(ROOT / name) for name in ["scripts/check_final_evaluation.py", OUTPUT, "data/final-evaluation-freeze.json"]}}


if __name__ == "__main__":
    result = check()
    write_json(ROOT / "docs/review-evidence/final-evaluation-checks.json", result)
    print(json.dumps({key: value for key, value in result.items() if key != "input_sha256"}, indent=2))
