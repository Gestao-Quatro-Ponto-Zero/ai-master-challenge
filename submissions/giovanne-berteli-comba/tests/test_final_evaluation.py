"""Evaluation arithmetic/exposure guards using synthetic fixtures, never final data."""

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solution"))
import evaluate_triage as driver
from triage.artifacts import sha256, write_json
from triage.core import CLASSES, no_prediction
from triage.evaluation import acceptance, latency_summary, runtime_sample, summarize_assisted


class FinalEvaluationTests(unittest.TestCase):
    def test_runtime_sample_is_stable_unique_and_unrelated_to_predictions(self):
        ids = [f"fixture:{i}" for i in range(100)]
        self.assertEqual(runtime_sample(ids, 64, "seed"), runtime_sample(list(reversed(ids)), 64, "seed"))
        self.assertEqual(len(set(runtime_sample(ids, 64, "seed"))), 64)
        with self.assertRaises(ValueError):
            runtime_sample(["duplicate", "duplicate"], 1, "seed")

    def test_denominators_include_failed_writes_and_deduplicate_two_metric_flags(self):
        standard = {**no_prediction("fixture"), "outcome": "suggested", "review_queue": "standard_review", "predicted_category": "Hardware", "persisted": True}
        anomaly = {**no_prediction("fixture"), "persisted": True}
        for record in anomaly["metrics"]:
            record.update(status="possible_anomaly", direction="high")
        failed = {**no_prediction("persistence_error", failed=True), "persisted": False}
        report = summarize_assisted(["Hardware", "Access", "Hardware"], [standard, anomaly, failed])
        self.assertEqual((report["attempted"], report["stored"], report["standard_cases"]), (3, 2, 1))
        self.assertEqual(report["standard_coverage"], 1 / 3)
        self.assertEqual(report["anomaly_cases"], 1)
        self.assertEqual(report["failed_outcomes"], 1)
        self.assertEqual(sum(report["metric_record_counts"].values()), 6)

    def test_frozen_targets_fail_without_eligible_standard_population(self):
        protocol = json.loads((ROOT / "data/evaluation-protocol.json").read_text())
        models = {"selected": {"macro_f1": .8}, "majority": {"macro_f1": .05}, "multinomial_nb": {"macro_f1": .78}}
        report = acceptance(models, "selected", {"standard_cases": 0, "standard_coverage": 0, "standard_accuracy_wilson_lower_95": None}, protocol)
        self.assertFalse(report["all_quality_targets_passed"])
        self.assertTrue(report["checks"]["min_macro_f1"])
        self.assertFalse(report["checks"]["min_standard_accuracy_wilson_lower_95"])

    def test_latency_tail_preserves_failed_attempt_time(self):
        report = latency_summary([10, 20, 5000])
        self.assertEqual(report["attempted"], 3)
        self.assertEqual(report["p50_ms"], 20)
        self.assertEqual(report["max_ms"], 5000)
        self.assertAlmostEqual(report["p95_ms"], 4502)

    def test_changed_freeze_inputs_and_external_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.py"
            source.write_text("original fixture")
            write_json(root / driver.FREEZE, {"input_sha256": {"source.py": sha256(source)}})
            driver.verify_freeze(root)
            source.write_text("changed")
            with self.assertRaisesRegex(ValueError, "changed"):
                driver.verify_freeze(root)
            write_json(root / driver.FREEZE, {"input_sha256": {"../outside": "unused"}})
            with self.assertRaisesRegex(ValueError, "changed"):
                driver.verify_freeze(root)

    @unittest.skipUnless(importlib.util.find_spec("threadpoolctl"), "Run in locked .venv")
    def test_completed_result_reuse_cannot_make_new_predictions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            write_json(root / driver.FREEZE, {"input_sha256": {}})
            write_json(root / driver.OUTPUT, {"evaluation_id": "fixture"})
            write_json(root / driver.LOCAL / "attempt.json", {"state": "completed", "freeze_sha256": sha256(root / driver.FREEZE), "result_sha256": sha256(root / driver.OUTPUT)})
            with patch.object(driver, "score_model", side_effect=AssertionError("Must not predict")), patch.object(driver, "load_metadata", side_effect=AssertionError("Must not load")), redirect_stdout(io.StringIO()):
                self.assertEqual(driver.evaluate(root), {"evaluation_id": "fixture"})
            (root / driver.OUTPUT).write_text("changed")
            with self.assertRaisesRegex(ValueError, "differs"):
                driver.completed_result(root)

    def test_interrupted_or_orphaned_attempt_cannot_be_presented_as_clean(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            write_json(root / driver.LOCAL / "attempt.json", {"state": "started"})
            with self.assertRaisesRegex(ValueError, "interrupted"):
                driver.completed_result(root)
            (root / driver.LOCAL / "attempt.json").unlink()
            (root / driver.LOCAL / "predictions.json").write_text("fixture")
            with self.assertRaisesRegex(ValueError, "Orphaned"):
                driver.completed_result(root)

    @unittest.skipUnless(importlib.util.find_spec("sklearn"), "Run in locked .venv")
    def test_classifier_report_includes_all_eight_classes_even_without_support(self):
        import numpy as np
        class FixtureModel:
            classes_ = CLASSES
            def predict(self, data):
                return np.array(["Access"] * len(data))
        report, _, _, _ = driver.score_model(FixtureModel(), ["fixture"], ["Access"], majority=True)
        self.assertEqual(report["accuracy"], 1)
        self.assertEqual(report["macro_f1"], 1 / 8)
        self.assertEqual(report["per_class"]["Storage"]["support"], 0)
        self.assertEqual(sum(map(sum, report["confusion"])), 1)


if __name__ == "__main__":
    unittest.main()
