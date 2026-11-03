#!/usr/bin/env python3
"""Freeze and execute a single reserved-test evaluation, never fitting a model."""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import pickle
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluation_rules import assumed_cost
from triage.artifacts import BOUND_INPUTS, BUNDLE, ROOT, load_metadata, sha256, write_json
from triage.core import CLASSES, normalize
from triage.evaluation import acceptance, latency_summary, runtime_sample, summarize_assisted
from triage.repository import Repository
from triage.runtime import TriageService, run_worker

FREEZE = "data/final-evaluation-freeze.json"
PLAN = "data/final-evaluation-plan.json"
OUTPUT = "data/final-evaluation.json"
LOCAL = "data/processed/final-evaluation"


def frozen_members(root=ROOT):
    split = json.loads((root / "data/evaluation-manifest.json").read_text())
    path = root / split["membership"]["path"]
    if sha256(path) != split["membership"]["sha256"]:
        raise ValueError("Membership differs from frozen V00")
    with path.open(newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["partition"] == "final_test"]
    if len(rows) != split["partition_rows"]["final_test"]:
        raise ValueError("Final membership count mismatch")
    return rows


def verify_freeze(root=ROOT):
    frozen = json.loads((root / FREEZE).read_text())
    for name, digest in frozen["input_sha256"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or sha256(path) != digest:
            raise ValueError(f"Frozen evaluation input changed: {name}")
    return frozen


def freeze(root=ROOT):
    manifest, _, _ = load_metadata(root)
    plan = json.loads((root / PLAN).read_text())
    source = json.loads((root / "data/manifest.json").read_text())["datasets"]["it_service"]
    for key in ("file", "archive"):
        if sha256(root / source[key]["path"]) != source[key]["sha256"]:
            raise ValueError("Raw IT bytes differ from the frozen source manifest")
    split = json.loads((root / "data/evaluation-manifest.json").read_text())
    for name, digest in split["input_sha256"].items():
        if sha256(root / name) != digest:
            raise ValueError("V00 preparation inputs changed")
    names = set(BOUND_INPUTS) | {PLAN, "data/manifest.json", "data/raw/it_service-v1.csv", "data/raw/it_service-v1.zip",
                                "data/processed/evaluation-membership.csv", "solution/evaluate_triage.py",
                                "solution/triage/evaluation.py", "solution/evaluation_rules.py", "tests/test_final_evaluation.py"}
    names |= set(split["input_sha256"])
    names |= {(BUNDLE / name).as_posix() for name in manifest["files"]}
    names.add((BUNDLE / "bundle.json").as_posix())
    inputs = {name: sha256(root / name) for name in sorted(names)}
    if (root / FREEZE).exists():
        existing = verify_freeze(root)
        if existing["input_sha256"] != inputs:
            raise ValueError("Existing freeze has different dependency membership")
        return existing
    members = frozen_members(root)
    value = {"schema_version": 1, "evaluation_id": plan["evaluation_id"],
             "frozen_at": datetime.now(timezone.utc).isoformat(), "selected_model": manifest["selected_model"],
             "input_sha256": inputs, "runtime_case_ids": runtime_sample([r["case_id"] for r in members], plan["runtime_sample_size"], plan["runtime_sample_seed"]),
             "exposure": "Frozen before any final-test classifier prediction; membership/support were already inspected in V00"}
    with (root / FREEZE).open("x") as output:
        output.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return value


def completed_result(root=ROOT):
    path = root / LOCAL / "attempt.json"
    if not path.exists():
        if (root / LOCAL).exists() and any((root / LOCAL).iterdir()):
            raise ValueError("Orphaned evaluation output; preserve it and inspect exposure")
        return None
    attempt = json.loads(path.read_text())
    if attempt.get("state") != "completed":
        raise ValueError("Evaluation already started/interrupted. Preserve its exposure; do not rerun as a clean test")
    if attempt["freeze_sha256"] != sha256(root / FREEZE) or attempt["result_sha256"] != sha256(root / OUTPUT):
        raise ValueError("Evaluation result/freeze differs from the completed attempt")
    return json.loads((root / OUTPUT).read_text())


def score_model(model, texts, truth, majority=False):
    import numpy as np
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
    if list(model.classes_) != list(CLASSES):
        raise ValueError("Estimator class order differs from the frozen eight classes")
    if majority:
        predictions = model.predict(np.zeros((len(texts), 1))).tolist()
        scores, known = None, None
    else:
        vectors = model.named_steps["tfidf"].transform(texts)
        scores = model.named_steps["classifier"].predict_proba(vectors).tolist()
        known = [int(n) for n in vectors.getnnz(axis=1)]
        predictions = [CLASSES[max(range(8), key=row.__getitem__)] for row in scores]
    matrix = confusion_matrix(truth, predictions, labels=CLASSES).tolist()
    errors = [{"true_class": actual, "predicted_class": predicted, "count": matrix[i][j]}
              for i, actual in enumerate(CLASSES) for j, predicted in enumerate(CLASSES) if i != j and matrix[i][j]]
    report = {"macro_f1": float(f1_score(truth, predictions, labels=CLASSES, average="macro", zero_division=0)),
              "accuracy": float(accuracy_score(truth, predictions)),
              "per_class": classification_report(truth, predictions, labels=CLASSES, output_dict=True, zero_division=0),
              "confusion": matrix, "largest_confusions": sorted(errors, key=lambda x: (-x["count"], x["true_class"], x["predicted_class"]))[:10]}
    return report, predictions, scores, known


def reply_for(values, known, manifest, policy, reference):
    return {"classes": list(CLASSES), "scores": values, "known_features": known,
            "policy": policy, "reference": reference, "model_version": manifest["model_version"],
            "model_sha256": manifest["files"][manifest["selected_model"] + ".pkl"],
            "policy_version": policy["id"], "policy_sha256": manifest["files"]["policy.json"],
            "reference_version": reference["id"], "reference_sha256": manifest["files"]["reference.json"]}


def database_counts(repository):
    with repository.connect() as connection:
        return {table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("cases", "runs", "metrics", "reviews")}


def fault_fixtures(directory, manifest, policy, reference):
    repository = Repository(directory / "fixtures.sqlite3")
    base = reply_for([.125] * 8, 1, manifest, policy, reference)
    def broken(text):
        raise RuntimeError("automated fixture")
    with tempfile.TemporaryDirectory(prefix="triage-timeout-fixture-") as folder:
        slow = Path(folder)
        (slow / "solution").mkdir()
        (slow / "solution/predict_worker.py").write_text("import time\ntime.sleep(3)\nprint('{}')\n")
        fixtures = [("invalid_input", "", "it_service_en", None, "invalid_input", True),
                    ("oversized_input", "x" * 10001, "it_service_en", None, "invalid_input", True),
                    ("unsupported_context", "support request", "unknown", None, "unsupported_context", True),
                    ("no_known_features", "zzqxvptrnzzzz", "it_service_en", lambda _: {**base, "known_features": 0}, "no_known_features", True),
                    ("not_ready", "support request", "it_service_en", lambda _: {"error": "not_ready"}, "not_ready", True),
                    ("timeout", "support request", "it_service_en", lambda text: run_worker(text, slow, timeout=.05), "timeout", True),
                    ("inference_error", "support request", "it_service_en", broken, "inference_error", True),
                    ("invalid_model_output", "support request", "it_service_en", lambda _: {**base, "scores": [float("nan")] * 8}, "invalid_model_output", True),
                    ("persistence_error", "support request", "unknown", None, "persistence_error", False)]
        records = []
        for name, text, context, worker, expected, saved in fixtures:
            if name == "persistence_error":
                with repository.connect() as connection:
                    connection.execute("CREATE TRIGGER force_failure BEFORE INSERT ON metrics BEGIN SELECT RAISE(ABORT,'automated fixture'); END;")
            service = TriageService(repository, worker) if worker else TriageService(repository)
            result = service.submit(text, context, request_id=f"fault:{name}", source={"dataset": "automated_fixture"})
            records.append({"fixture": name, "expected_reason": expected, "reason_codes": result["reason_codes"],
                            "outcome": result["outcome"], "stored": result["persisted"],
                            "passed": result["reason_codes"] == [expected] and result["persisted"] == saved})
    return {"population": "Synthetic automated fixtures, not held-out accuracy or observed runtime failures",
            "attempted": len(records), "stored": sum(r["stored"] for r in records),
            "all_passed": all(r["passed"] for r in records), "cases": records, "database": database_counts(repository)}


def evaluate(root=ROOT):
    from threadpoolctl import threadpool_limits
    frozen = verify_freeze(root)
    previous = completed_result(root)
    if previous is not None:
        print("Avaliação já concluída: reutilizando o relatório, sem prever novamente.", flush=True)
        return previous
    manifest, policy, reference = load_metadata(root)
    protocol = json.loads((root / "data/evaluation-protocol.json").read_text())
    plan = json.loads((root / PLAN).read_text())
    members = frozen_members(root)
    by_row = {int(item["row_index"]): item for item in members}
    rows = []
    with (root / "data/raw/it_service-v1.csv").open(encoding="utf-8-sig", newline="") as handle:
        for i, row in enumerate(csv.DictReader(handle), 1):
            if i in by_row:
                rows.append({**by_row[i], "text": row["Document"], "target": row["Topic_group"]})
    if len(rows) != len(members) or set(row["target"] for row in rows) != set(CLASSES):
        raise ValueError("Final rows/classes mismatch")
    directory = root / LOCAL
    directory.mkdir(parents=True, exist_ok=True)
    attempt = {"state": "started", "started_at": datetime.now(timezone.utc).isoformat(),
               "freeze_sha256": sha256(root / FREEZE), "population": len(rows)}
    with (directory / "attempt.json").open("x") as handle:
        handle.write(json.dumps(attempt, indent=2) + "\n")
    texts, truth = [normalize(r["text"]) for r in rows], [r["target"] for r in rows]
    reports = {}
    with threadpool_limits(limits=1):
        for name in ("majority", "multinomial_nb", manifest["selected_model"]):
            with (root / BUNDLE / (name + ".pkl")).open("rb") as handle:
                model = pickle.load(handle)
            reports[name], predictions, scores, known = score_model(model, texts, truth, name == "majority")
            if name == manifest["selected_model"]:
                selected_predictions, selected_scores, selected_known = predictions, scores, known
            print(f"Computed reserved-test predictions: {name}", flush=True)
    offline_repo = Repository(directory / "offline.sqlite3")
    results = []
    for i, row in enumerate(rows):
        reply = reply_for(selected_scores[i], selected_known[i], manifest, policy, reference)
        service = TriageService(offline_repo, lambda _, reply=reply: reply)
        results.append(service.submit(row["text"], "it_service_en", f"offline:{row['case_id']}", row["case_id"],
                                      {"dataset": "it_service", "partition": "final_test", "row_index": int(row["row_index"])}))
    assisted = summarize_assisted(truth, results)
    assisted["database"] = database_counts(offline_repo)
    assisted["execution"] = plan["offline_execution"]
    assisted["assumed_cost"] = assumed_cost(truth, selected_predictions, [r["review_queue"] for r in results], protocol)
    runtime_repo = Repository(directory / "runtime.sqlite3")
    service = TriageService(runtime_repo)
    lookup = {r["case_id"]: i for i, r in enumerate(rows)}
    timings, runtime_results, parity_mismatches = [], [], []
    for position, case in enumerate(frozen["runtime_case_ids"], 1):
        i = lookup[case]
        row = rows[i]
        started = time.perf_counter()
        result = service.submit(row["text"], "it_service_en", f"runtime:{case}", case,
                                {"dataset": "it_service", "partition": "final_test", "row_index": int(row["row_index"])})
        timings.append((time.perf_counter() - started) * 1000)
        runtime_results.append(result)
        expected = results[i]
        same = all(result[key] == expected[key] for key in ("predicted_category", "outcome", "review_queue", "reason_codes"))
        same &= [(m["status"], m["direction"], m["reason"]) for m in result["metrics"]] == [(m["status"], m["direction"], m["reason"]) for m in expected["metrics"]]
        same &= (result["score"] is None and expected["score"] is None) or (result["score"] is not None and expected["score"] is not None and abs(result["score"] - expected["score"]) <= 1e-12)
        if not same:
            parity_mismatches.append(case)
        if position % 16 == 0:
            print(f"Actual worker/persistence runtime sample: {position}/{len(frozen['runtime_case_ids'])}", flush=True)
    runtime = {**latency_summary(timings), "stored": sum(r["persisted"] for r in runtime_results),
               "failed_outcomes": sum(r["outcome"] == "failed" for r in runtime_results),
               "reason_case_counts_overlapping": dict(Counter(reason for r in runtime_results for reason in r["reason_codes"])),
               "parity_mismatches": parity_mismatches, "database": database_counts(runtime_repo), "execution": plan["runtime_execution"],
               "limits": plan["latency"]}
    faults = fault_fixtures(directory, manifest, policy, reference)
    if [r["fixture"] for r in faults["cases"]] != plan["fault_fixtures"]:
        raise ValueError("Fixture catalog differs from frozen plan")
    checks = acceptance(reports, manifest["selected_model"], assisted, protocol)
    checks["software_execution_passed"] = (assisted["attempted"] == assisted["stored"] == assisted["database"]["runs"] and
                                            assisted["database"]["metrics"] == 2 * assisted["attempted"] and
                                            assisted["failed_outcomes"] == 0 and runtime["failed_outcomes"] == 0 and
                                            runtime["stored"] == runtime["attempted"] == runtime["database"]["runs"] and
                                            runtime["database"]["metrics"] == 2 * runtime["attempted"] and not parity_mismatches and faults["all_passed"])
    verify_freeze(root)
    write_json(directory / "predictions.json", {"case_ids": [r["case_id"] for r in rows], "classes": list(CLASSES),
                                                 "selected_model": manifest["selected_model"], "scores": selected_scores,
                                                 "known_features": selected_known})
    report = {"schema_version": 1, "evaluation_id": plan["evaluation_id"], "freeze_sha256": sha256(root / FREEZE),
              "completed_at": datetime.now(timezone.utc).isoformat(), "population": len(rows), "classes": list(CLASSES),
              "selected_model": manifest["selected_model"], "policy": policy, "reference_sha256": manifest["files"]["reference.json"],
              "classifier_metrics": reports, "assisted": assisted, "runtime_sample": runtime,
              "automated_fault_fixtures": faults, "acceptance": checks, "classifier_fits": 0,
              "model_or_gate_or_reference_changed": False, "test_used_for_selection": False,
              "limits": ["Retrospective processed IT text; prospective input availability and entity independence unproven",
                         "Whole-group split protects only the declared token similarity; within-group dependence limits naive confidence interpretation",
                         "Classifier metrics include all texts, even zero known features; valid suggestion coverage/errors follow the core policy",
                         "Anomalies are numerical flags, not human-adjudicated issues or measured false alerts",
                         "No customer-domain accuracy, production SLA, autonomous resolution, business acceptance or measured savings"],
              "local_output_sha256": {p.relative_to(root).as_posix(): sha256(p) for p in directory.iterdir() if p.is_file() and p.name != "attempt.json"}}
    write_json(root / OUTPUT, report)
    attempt.update(state="completed", result_sha256=sha256(root / OUTPUT), classifier_fits=0)
    write_json(directory / "attempt.json", attempt)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["freeze", "evaluate"])
    args = parser.parse_args()
    try:
        result = freeze() if args.action == "freeze" else evaluate()
        print(json.dumps({"evaluation_id": result["evaluation_id"], "action": args.action,
                          "acceptance": result.get("acceptance"), "classifier_fits": result.get("classifier_fits", 0)}, indent=2))
    except (OSError, ValueError, KeyError) as error:
        print(f"Avaliação não concluída: {error}. Preserve o registro da tentativa; não substitua um teste já exposto.", file=sys.stderr)
        sys.exit(1)
