"""Critical flows with deterministic automated fixtures, no classifier fitting."""

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "solution"))
from triage.artifacts import BOUND_INPUTS, BUNDLE, ROOT, load_metadata, sha256, write_json
from triage.core import CLASSES, build_reference, from_scores, metrics_for, normalize
from triage.repository import Repository, RequestConflict
from triage.runtime import TriageService, run_worker


def fixture(category="Hardware", score=.9):
    policy = {"id": "fixture-policy", "mode": "qualified", "threshold": .6,
              "specialist_categories": ["Access", "Administrative rights", "Purchase", "HR Support"]}
    reference = {"id": "fixture-reference", "context": "it_service_en", "normalization": "nfkc-casefold-space-v1",
                 "model_version": "fixture-model", "minimum": 100, "method": "fixture-bounds", "tail": .01,
                 "groups": {name: {"model_score": {"n": 100, "lower": .5, "upper": .95},
                                    "text_chars": {"n": 100, "lower": 10., "upper": 100.}} for name in CLASSES}}
    values = [(1 - score) / 7] * 8
    values[CLASSES.index(category)] = score
    return {"classes": list(CLASSES), "scores": values, "known_features": 4, "policy": policy, "reference": reference,
            "model_version": "fixture-model", "model_sha256": "fixture-hash", "policy_version": "fixture-policy",
            "policy_sha256": "fixture-policy-hash", "reference_version": "fixture-reference", "reference_sha256": "fixture-ref-hash"}


class TriageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "triage.sqlite3"
        self.repo = Repository(self.path)
        self.reply = fixture()
        self.calls = 0

    def worker(self, text):
        self.calls += 1
        return deepcopy(self.reply)

    def submit(self, text="hardware printer needs help", **options):
        return TriageService(self.repo, self.worker).submit(text, options.pop("context", "it_service_en"), **options)

    def test_normal_suggestion_and_reload_preserve_original_precision(self):
        result = self.submit(request_id="request")
        self.assertEqual((result["outcome"], result["review_queue"]), ("suggested", "standard_review"))
        self.assertTrue(result["persisted"] and result["confirmation_required"])
        saved = Repository(self.path).get_run(result["run_id"])
        self.assertEqual(saved["result"], result)
        self.assertEqual(saved["original_text"], "hardware printer needs help")
        self.assertEqual(len(self.repo.filter_metrics()), 2)
        self.assertEqual({row["review_state"] for row in self.repo.filter_metrics()}, {"not_required"})

    def test_invalid_input_does_not_call_worker_or_store_unbounded_text(self):
        for value in [None, 1, "", "   ", "x" * 10001, "ﬃ" * 4000]:
            with self.subTest(value=str(value)[:15]):
                result = self.submit(value)
                self.assertEqual(result["reason_codes"], ["invalid_input"])
                self.assertIsNone(result["score"])
                self.assertTrue(result["persisted"])
                self.assertIsNone(self.repo.get_run(result["run_id"])["original_text"])
        self.assertEqual(self.calls, 0)

    def test_unknown_customer_context_never_calls_model(self):
        for context in ["customer_support", "unknown", "invented"]:
            self.assertEqual(self.submit(context=context)["reason_codes"], ["unsupported_context"])
        self.assertEqual(self.calls, 0)

    def test_missing_model_and_zero_features_are_explicit(self):
        self.reply = {"error": "not_ready"}
        self.assertEqual(self.submit()["outcome"], "failed")
        self.reply = fixture()
        self.reply["known_features"] = 0
        result = self.submit()
        self.assertEqual(result["reason_codes"], ["no_known_features"])
        self.assertTrue(all(row["status"] == "not_evaluated" for row in result["metrics"]))

    def test_invalid_output_vectors_never_become_suggestions(self):
        cases = [dict(scores=[float("nan")] * 8), dict(scores=[float("inf")] * 8),
                 dict(scores=[.1] * 8), dict(scores=[-1.] + [2/7]*7), dict(scores=[1.]),
                 dict(classes=["Unknown"] * 8)]
        for overrides in cases:
            self.reply = {**fixture(), **overrides}
            result = self.submit()
            self.assertEqual(result["reason_codes"], ["invalid_model_output"])
            self.assertIsNone(result["score"])
            json.dumps(result, allow_nan=False)

    def test_timeout_and_worker_failure_have_no_late_success(self):
        for error, expected in [(subprocess.TimeoutExpired("fixture", 5), "timeout"), (RuntimeError("fixture"), "inference_error")]:
            def broken(text):
                raise error
            result = TriageService(self.repo, broken).submit("hardware printer needs help", "it_service_en")
            self.assertEqual(result["reason_codes"], [expected])
            self.assertEqual(result["outcome"], "failed")

    def test_high_low_equal_constant_and_insufficient_reference(self):
        ref = fixture()["reference"]
        for score, length, direction in [(.96, 40, "high"), (.4, 40, "low"), (.5, 10, None), (.95, 100, None)]:
            records = metrics_for("Hardware", score, length, ref)
            self.assertEqual(records[0]["direction"], direction)
            self.assertEqual(records[1]["direction"], None)
        ref["groups"]["Hardware"]["model_score"] = {"n": 100, "lower": .9, "upper": .9}
        self.assertEqual(metrics_for("Hardware", .9, 40, ref)[0]["status"], "ordinary")
        ref["groups"]["Hardware"]["model_score"] = {"n": 99, "lower": None, "upper": None}
        self.assertEqual(metrics_for("Hardware", .9, 40, ref)[0]["reason"], "insufficient_reference")

    def test_low_anomaly_is_saved_filtered_and_reviewed_without_changing_value(self):
        result = self.submit("hi")
        self.assertEqual(result["reason_codes"], ["anomaly_review"])
        rows = Repository(self.path).filter_metrics(direction="low", metric="text_chars", status="possible_anomaly")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["value"], 2)
        self.repo.review(result["run_id"], "confirmed_issue", "fixture", "short text inspected", metric="text_chars", reviewer_type="automated_test")
        self.assertEqual(self.repo.filter_metrics(direction="low", review_state="confirmed_issue")[0]["value"], 2)

    def test_reference_quantiles_use_predicted_class_and_minimum_support(self):
        ref = build_reference(["Hardware"] * 100 + ["Storage"] * 99, [.8] * 199, list(range(199)), .01, "m", "membership")
        self.assertAlmostEqual(ref["groups"]["Hardware"]["text_chars"]["lower"], .99)
        self.assertEqual(ref["groups"]["Storage"]["text_chars"]["lower"], None)

    def test_anomalies_and_uncertainty_precede_specialist_queue(self):
        self.reply = fixture("Access", .96)
        result = self.submit()
        self.assertEqual(result["review_queue"], "triage_review")
        self.assertEqual(set(result["reason_codes"]), {"anomaly_review", "policy_human_category"})
        self.reply = fixture("Access", .9)
        self.assertEqual(self.submit()["review_queue"], "specialist_review")
        self.reply = fixture("Access", .55)
        self.assertEqual(self.submit()["reason_codes"], ["low_score", "policy_human_category"])
        self.reply = fixture()
        self.reply["reference"]["groups"] = {}
        self.assertEqual(self.submit()["reason_codes"], ["insufficient_reference"])
        self.reply = fixture()
        self.reply["policy"].update(mode="manual_only", threshold=None)
        self.assertEqual(self.submit()["reason_codes"], ["no_feasible_gate"])

    def test_duplicate_delivery_and_conflict_do_not_create_extra_rows(self):
        result = self.submit(request_id="same")
        self.assertEqual(self.submit(request_id="same"), result)
        self.assertEqual(self.calls, 1)
        conflict = self.submit("different text for same request", request_id="same")
        self.assertFalse(conflict["persisted"])
        self.assertEqual(conflict["reason_codes"], ["request_conflict"])
        self.assertEqual(len(self.repo.list_runs()), 1)
        self.assertEqual(len(self.repo.filter_metrics()), 2)

    def test_concurrent_duplicate_delivery_returns_one_atomic_run(self):
        barrier = threading.Barrier(2)
        def worker(text):
            barrier.wait(timeout=3)
            return fixture()
        service = TriageService(self.repo, worker)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(service.submit, "hardware printer needs help", "it_service_en", "concurrent") for _ in range(2)]
            first, second = [future.result(timeout=5) for future in futures]
        self.assertEqual(first, second)
        self.assertEqual(len(self.repo.list_runs()), 1)
        self.assertEqual(len(self.repo.filter_metrics()), 2)

    def test_failed_metric_insert_rolls_back_case_run_and_metrics(self):
        with self.repo.connect() as connection:
            connection.execute("CREATE TRIGGER fail_metric BEFORE INSERT ON metrics WHEN NEW.metric='text_chars' BEGIN SELECT RAISE(ABORT,'fixture'); END;")
        result = self.submit()
        self.assertFalse(result["persisted"])
        self.assertEqual(result["reason_codes"], ["persistence_error"])
        self.assertEqual(self.repo.list_runs(), [])
        with self.repo.connect() as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM cases").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT count(*) FROM metrics").fetchone()[0], 0)

    def test_bound_filters_latest_reviews_and_original_values(self):
        self.reply = fixture(score=.96)
        result = self.submit()
        run_id = result["run_id"]
        first = self.repo.review(run_id, "confirmed_valid", "fixture", "valid high value", metric="model_score", reviewer_type="automated_test", event_id="review1")
        self.assertEqual(self.repo.review(run_id, "confirmed_valid", "fixture", "valid high value", metric="model_score", reviewer_type="automated_test", event_id="review1"), first)
        self.repo.review(run_id, "deferred", "fixture", "needs investigation", metric="model_score", reviewer_type="automated_test")
        rows = self.repo.filter_metrics(status="possible_anomaly", direction="high", reason="outside_reference", review_state="deferred", category="Hardware", metric="model_score", model_version="fixture-model")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["value"], .96)
        self.assertEqual(self.repo.filter_metrics(review_state="confirmed_valid"), [])
        self.assertEqual(self.repo.filter_metrics(reason="' OR 1=1 --"), [])
        self.repo.review(run_id, "corrected", "fixture", "different category", corrected_category="Storage", reviewer_type="automated_test")
        detail = Repository(self.path).get_run(run_id)
        self.assertEqual(detail["result"], result)
        self.assertEqual(len(detail["reviews"]), 3)
        with self.assertRaises(RequestConflict):
            self.repo.review(run_id, "deferred", "fixture", "conflict", metric="model_score", reviewer_type="automated_test", event_id="review1")

    def test_non_it_handoff_can_be_accepted_but_not_given_it_correction(self):
        result = self.submit(context="unknown")
        self.repo.review(result["run_id"], "accepted", "fixture", "manual handoff accepted", reviewer_type="automated_test")
        with self.assertRaises(ValueError):
            self.repo.review(result["run_id"], "corrected", "fixture", "unsupported", corrected_category="Access", reviewer_type="automated_test")

    def test_stale_or_missing_artifact_is_rejected_before_deserialization(self):
        with self.assertRaises(FileNotFoundError):
            load_metadata(Path(self.temp.name), environment=False)
        directory = Path(self.temp.name) / BUNDLE
        directory.mkdir(parents=True)
        write_json(directory / "bundle.json", {"schema_version": 1, "protocol_id": "it-triage-v1", "input_sha256": {}})
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            load_metadata(Path(self.temp.name), environment=False)

    def test_changed_code_and_model_bytes_invalidate_owned_bundle(self):
        root = Path(self.temp.name)
        directory = root / BUNDLE
        directory.mkdir(parents=True)
        for name in BOUND_INPUTS:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / name).read_bytes())
        reply = fixture()
        for name in ["majority.pkl", "multinomial_nb.pkl", "logistic_c05.pkl", "logistic_c20.pkl"]:
            (directory / name).write_text("non-executable test bytes")
        version = sha256(directory / "logistic_c05.pkl")
        membership_hash = json.loads((root / "data/evaluation-manifest.json").read_text())["membership"]["sha256"]
        ref = {**reply["reference"], "model_version": version, "membership_sha256": membership_hash, "method": "linear-empirical-quantile-v1"}
        write_json(directory / "policy.json", reply["policy"])
        write_json(directory / "reference.json", ref)
        write_json(directory / "demo-examples.json", [])
        names = [p.name for p in directory.iterdir()]
        write_json(directory / "bundle.json", {"schema_version": 1, "protocol_id": "it-triage-v1", "input_sha256": {name: sha256(root / name) for name in BOUND_INPUTS},
                    "files": {name: sha256(directory / name) for name in names}, "selected_model": "logistic_c05",
                    "model_version": version, "membership_sha256": membership_hash, "classes": list(CLASSES)})
        load_metadata(root, environment=False)
        code = root / "solution/triage/core.py"
        before = code.read_bytes()
        code.write_text("changed code")
        with self.assertRaisesRegex(ValueError, "Stale"):
            load_metadata(root, environment=False)
        code.write_bytes(before)
        (directory / "logistic_c05.pkl").write_text("changed model")
        with self.assertRaisesRegex(ValueError, "hash"):
            load_metadata(root, environment=False)

    def test_subprocess_deadline_terminates_real_slow_worker(self):
        root = Path(self.temp.name)
        (root / "solution").mkdir()
        (root / "solution/predict_worker.py").write_text("import time\ntime.sleep(3)\nprint('{}')\n")
        result = TriageService(self.repo, lambda text: run_worker(text, root, timeout=.05)).submit("hardware printer needs help", "it_service_en")
        self.assertEqual(result["reason_codes"], ["timeout"])
        self.assertIsNone(result["predicted_category"])
        self.assertEqual(len(self.repo.list_runs()), 1)


if __name__ == "__main__":
    unittest.main()
