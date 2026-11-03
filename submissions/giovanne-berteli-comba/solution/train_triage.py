#!/usr/bin/env python3
"""Execute the four-fit V00 budget on train; select on validation, never final test."""

from collections import Counter
from datetime import datetime, timezone
import csv
import json
import pickle
from pathlib import Path
import sys
import time
import warnings

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluation_rules import assumed_cost, choose_gate, choose_model, wilson_lower
from triage.artifacts import BOUND_INPUTS, BUNDLE, ROOT, check_environment, sha256, write_json
from triage.core import CLASSES, NORMALIZATION, build_reference, from_scores, normalize
from triage.setup_state import reuse_completed


def populations(root=ROOT):
    manifest = json.loads((root / "data/evaluation-manifest.json").read_text())
    for name, expected in manifest["input_sha256"].items():
        if sha256(root / name) != expected:
            raise ValueError("Stale evaluation preparation")
    membership = root / manifest["membership"]["path"]
    if sha256(membership) != manifest["membership"]["sha256"]:
        raise ValueError("Membership differs from frozen split")
    with membership.open(newline="") as handle:
        selected = {int(row["row_index"]): row for row in csv.DictReader(handle) if row["partition"] in {"train", "validation"}}
    source = json.loads((root / "data/manifest.json").read_text())["datasets"]["it_service"]["file"]["path"]
    result = {name: [] for name in ("train", "validation")}
    with (root / source).open(encoding="utf-8-sig", newline="") as handle:
        for i, row in enumerate(csv.DictReader(handle), 1):
            if i in selected:
                result[selected[i]["partition"]].append({**selected[i], "text": normalize(row["Document"]),
                                                          "original_text": row["Document"], "target": row["Topic_group"]})
    if any(len(result[name]) != manifest["partition_rows"][name] for name in result):
        raise ValueError("Population count mismatch")
    return result, manifest


def main():
    if reuse_completed(ROOT):
        return
    import numpy as np
    from sklearn.dummy import DummyClassifier
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from threadpoolctl import threadpool_limits

    check_environment(ROOT)
    protocol = json.loads((ROOT / "data/evaluation-protocol.json").read_text())
    if protocol["protocol_id"] != "it-triage-v1" or protocol["model_selection"]["max_fits"] != 4:
        raise ValueError("Unexpected fit budget/protocol")
    directory = ROOT / BUNDLE
    directory.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents accidental additional fits under the same protocol.
    attempt_path = directory / "training-attempt.json"
    try:
        with attempt_path.open("x") as handle:
            json.dump({"started_at": datetime.now(timezone.utc).isoformat(), "fits_started": [], "state": "started"}, handle)
    except FileExistsError:
        reuse_completed(ROOT)
        return
    attempt = json.loads(attempt_path.read_text())
    data, split = populations()
    train, validation = data["train"], data["validation"]
    x, y = [r["text"] for r in train], [r["target"] for r in train]
    vx, vy = [r["text"] for r in validation], [r["target"] for r in validation]
    report = {"schema_version": 1, "protocol_id": protocol["protocol_id"],
              "scope": "TRAIN/VALIDATION DEVELOPMENT RESULTS ONLY; final test not predicted or scored",
              "training_rows": len(train), "validation_rows": len(validation), "final_test_predictions": 0,
              "classes": list(CLASSES), "candidates": {}, "gate_grid": [], "selected_model": None,
              "selected_gate": None, "cost_unit": protocol["assumed_error_costs"]["unit"]}
    saved_predictions = {}
    constructors = {"DummyClassifier": DummyClassifier, "MultinomialNB": MultinomialNB, "LogisticRegression": LogisticRegression}
    with threadpool_limits(limits=1):
        for candidate in protocol["model_selection"]["candidates"]:
            name = candidate["id"]
            params = {key: value for key, value in candidate.items() if key not in {"id", "role", "estimator"}}
            model = constructors[candidate["estimator"]](**params)
            if name != "majority":
                features = {**protocol["model_selection"]["tfidf"]}
                features["ngram_range"] = tuple(features["ngram_range"])
                model = Pipeline([("tfidf", TfidfVectorizer(**features)), ("classifier", model)])
            attempt["fits_started"].append(name)
            write_json(attempt_path, attempt)
            started = time.perf_counter()
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always", ConvergenceWarning)
                model.fit(x if name != "majority" else np.zeros((len(x), 1)), y)
            predictions = model.predict(vx if name != "majority" else np.zeros((len(vx), 1))).tolist()
            report["candidates"][name] = {"macro_f1": float(f1_score(vy, predictions, labels=CLASSES, average="macro", zero_division=0)),
                                          "accuracy": float(accuracy_score(vy, predictions)),
                                          "per_class": classification_report(vy, predictions, labels=CLASSES, output_dict=True, zero_division=0),
                                          "confusion": confusion_matrix(vy, predictions, labels=CLASSES).tolist(),
                                          "fit_and_validation_seconds": time.perf_counter() - started,
                                          "warnings": [str(item.message) for item in captured]}
            with (directory / (name + ".pkl")).open("wb") as handle:
                pickle.dump(model, handle, protocol=5)
            if name.startswith("logistic"):
                vectors = model.named_steps["tfidf"].transform(vx)
                saved_predictions[name] = {"classes": model.classes_.tolist(), "scores": model.named_steps["classifier"].predict_proba(vectors).tolist(),
                                           "known_features": [int(n) for n in vectors.getnnz(axis=1)]}
            print(json.dumps({"candidate": name, "validation_macro_f1": report["candidates"][name]["macro_f1"]}), flush=True)
    winner = choose_model({name: item["macro_f1"] for name, item in report["candidates"].items()}, protocol)
    report["selected_model"] = winner
    model_version = sha256(directory / (winner + ".pkl")) if winner else None
    policy = {"id": "it-triage-policy-v1", "mode": "manual_only", "threshold": None,
              "specialist_categories": protocol["gating"]["specialist_categories"]}
    reference = {"context": "it_service_en", "model_version": model_version, "normalization": NORMALIZATION,
                 "membership_sha256": split["membership"]["sha256"], "method": "linear-empirical-quantile-v1",
                 "tail": None, "minimum": protocol["gating"]["reference_min_records"], "groups": {}}
    gate_decisions = {}
    if winner:
        scored = saved_predictions[winner]
        cats = [CLASSES[max(range(8), key=values.__getitem__)] for values in scored["scores"]]
        scores = [max(values) for values in scored["scores"]]
        lengths = [len(text) for text in vx]
        references = {}
        for tail in protocol["gating"]["anomaly_tail_grid"]:
            references[tail] = build_reference(cats, scores, lengths, tail, model_version, split["membership"]["sha256"], protocol["gating"]["reference_min_records"])
            for threshold in protocol["gating"]["score_threshold_grid"]:
                trial_policy = {**policy, "mode": "qualified", "threshold": threshold}
                decisions = [from_scores(scored["classes"], values, known, length, trial_policy, references[tail])
                             for values, known, length in zip(scored["scores"], scored["known_features"], lengths)]
                mask = [i for i, result in enumerate(decisions) if result["review_queue"] == "standard_review"]
                correct = sum(cats[i] == vy[i] for i in mask)
                item = {"threshold": threshold, "tail": tail, "standard_cases": len(mask), "standard_correct": correct,
                        "scored_cases": len(decisions), "standard_coverage": len(mask) / len(decisions),
                        "standard_accuracy_wilson_lower_95": wilson_lower(correct, len(mask)),
                        "anomaly_cases": sum(any(metric["status"] == "possible_anomaly" for metric in result["metrics"]) for result in decisions),
                        "not_evaluated_cases": sum(any(metric["status"] == "not_evaluated" for metric in result["metrics"]) for result in decisions),
                        "queue_counts": dict(Counter(result["review_queue"] for result in decisions)),
                        "mean_cost": assumed_cost(vy, cats, [result["review_queue"] for result in decisions], protocol)}
                report["gate_grid"].append(item)
                gate_decisions[(threshold, tail)] = decisions
        chosen = choose_gate(report["gate_grid"], protocol)
        report["selected_gate"] = chosen
        if chosen:
            policy.update(mode="qualified", threshold=chosen["threshold"])
            reference = references[chosen["tail"]]
            decisions = gate_decisions[(chosen["threshold"], chosen["tail"])]
            report["cost_sensitivity_validation_only"] = {}
            for multiplier in protocol["assumed_error_costs"]["sensitivity_multiplier_for_specialist_error"]:
                revised = {**protocol, "assumed_error_costs": {**protocol["assumed_error_costs"], "wrong_standard_category_when_true_class_is_specialist": protocol["assumed_error_costs"]["wrong_standard_category_when_true_class_is_specialist"] * multiplier}}
                report["cost_sensitivity_validation_only"][str(multiplier)] = assumed_cost(vy, cats, [item["review_queue"] for item in decisions], revised)
    reference["id"] = "it-validation-reference-v1"
    write_json(directory / "policy.json", policy)
    write_json(directory / "reference.json", reference)
    examples = [{"case_id": row["case_id"], "text": row["original_text"], "source": {"dataset": "it_service", "partition": "train", "row_index": int(row["row_index"])}} for row in train[:3]]
    write_json(directory / "demo-examples.json", examples)
    write_json(directory / "validation-predictions.json", {"case_ids": [r["case_id"] for r in validation], "predictions": saved_predictions})
    files = [item["id"] + ".pkl" for item in protocol["model_selection"]["candidates"]] + ["policy.json", "reference.json", "demo-examples.json"]
    bundle = {"schema_version": 1, "protocol_id": protocol["protocol_id"], "classes": list(CLASSES),
              "selected_model": winner, "model_version": model_version, "membership_sha256": split["membership"]["sha256"],
              "input_sha256": {name: sha256(ROOT / name) for name in BOUND_INPUTS},
              "files": {name: sha256(directory / name) for name in files}}
    write_json(directory / "bundle.json", bundle)
    report["bundle_sha256"] = sha256(directory / "bundle.json")
    report["input_sha256"] = {**bundle["input_sha256"], "data/processed/evaluation-membership.csv": split["membership"]["sha256"],
                               "data/raw/it_service-v1.csv": sha256(ROOT / "data/raw/it_service-v1.csv")}
    report["artifact_sha256"] = {**bundle["files"], "bundle.json": sha256(directory / "bundle.json"),
                                  "validation-predictions.json": sha256(directory / "validation-predictions.json")}
    write_json(ROOT / "data/triage-development.json", report)
    attempt.update(state="completed", final_test_predictions=0)
    write_json(attempt_path, attempt)
    print(json.dumps({"selected_model": winner, "selected_gate": report["selected_gate"], "final_test_predictions": 0}), flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, ImportError) as error:
        print(f"Não foi possível preparar o treino: {error}\nPara a inicialização guiada, execute: bash run.sh", file=sys.stderr)
        sys.exit(1)
