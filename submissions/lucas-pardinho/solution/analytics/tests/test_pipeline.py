from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


ANALYTICS_DIR = Path(__file__).resolve().parents[1]
SOLUTION_DIR = ANALYTICS_DIR.parent
sys.path.insert(0, str(ANALYTICS_DIR))

from pipeline import run_pipeline  # noqa: E402


class PipelineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp_dir.name)
        cls.raw = SOLUTION_DIR / "data" / "raw"
        cls.normalized = cls.root / "normalized"
        cls.generated = cls.root / "generated"
        cls.result = run_pipeline(cls.raw, cls.normalized, cls.generated)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def test_real_data_contract_and_counts(self) -> None:
        dashboard = self.result["dashboard"]
        self.assertEqual(dashboard["summary"]["openOpportunities"], 2089)
        self.assertEqual(dashboard["summary"]["engaging"], 1589)
        self.assertEqual(dashboard["summary"]["prospecting"], 500)
        self.assertEqual(len(self.result["opportunities"]), 2089)
        self.assertTrue(self.result["dataQuality"]["validationPassed"])

    def test_raw_is_preserved_and_product_is_normalized(self) -> None:
        raw_text = (self.raw / "sales_pipeline.csv").read_text(encoding="utf-8")
        normalized_text = (self.normalized / "sales_pipeline.csv").read_text(
            encoding="utf-8"
        )
        self.assertIn(",GTXPro,", raw_text)
        self.assertNotIn(",GTXPro,", normalized_text)
        self.assertIn(",GTX Pro,", normalized_text)
        transformation = self.result["dataQuality"]["transformations"][0]
        self.assertEqual(transformation["count"], 1480)

    def test_outputs_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as other_temp:
            other = Path(other_temp)
            run_pipeline(self.raw, other / "normalized", other / "generated")
            for filename in (
                "opportunities.json",
                "dashboard.json",
                "model-report.json",
                "data-quality.json",
            ):
                self.assertEqual(
                    (self.generated / filename).read_bytes(),
                    (other / "generated" / filename).read_bytes(),
                    filename,
                )

    def test_engaging_scores_and_prospecting_scores_are_separate(self) -> None:
        for row in self.result["opportunities"]:
            if row["dealStage"] == "Engaging":
                self.assertIsNotNone(row["probability"])
                self.assertIsNotNone(row["priorityScore"])
                self.assertIsNone(row["qualificationScore"])
                self.assertGreaterEqual(row["probability"], 0)
                self.assertLessEqual(row["probability"], 1)
                self.assertGreaterEqual(row["priorityScore"], 0)
                self.assertLessEqual(row["priorityScore"], 100)
            else:
                self.assertIsNone(row["probability"])
                self.assertIsNone(row["priorityScore"])
                self.assertIsNotNone(row["qualificationScore"])
                self.assertEqual(row["queue"], "Qualificar")
                self.assertGreaterEqual(row["qualificationScore"], 0)
                self.assertLessEqual(row["qualificationScore"], 100)

    def test_focus_now_has_at_most_ten_per_agent_and_never_stale(self) -> None:
        focus = [
            row for row in self.result["opportunities"] if row["queue"] == "Foco agora"
        ]
        counts = Counter(row["salesAgent"] for row in focus)
        self.assertTrue(counts)
        self.assertTrue(all(count <= 10 for count in counts.values()))
        self.assertTrue(all(row["ageDays"] <= 138 for row in focus))

    def test_stale_rule_and_low_confidence_are_explicit(self) -> None:
        stale = [
            row
            for row in self.result["opportunities"]
            if row["dealStage"] == "Engaging" and row["ageDays"] > 138
        ]
        self.assertTrue(stale)
        self.assertTrue(
            all(row["queue"] == "Resgatar ou desqualificar" for row in stale)
        )
        self.assertTrue(all(row["confidence"] == "low" for row in stale))
        self.assertTrue(all(0 <= row["probability"] <= 1 for row in stale))
        self.assertNotIn("staleProbability", self.result["modelReport"]["finalModel"])
        self.assertTrue(
            self.result["modelReport"]["training"]["smoothing"][
                "noArbitraryStaleConstant"
            ]
        )

    def test_leakage_fields_are_excluded(self) -> None:
        features = self.result["modelReport"]["features"]
        used = set(features["candidateUsed"])
        excluded = set(features["excludedToPreventLeakage"])
        self.assertEqual(
            used, {"product_normalized", "pipeline_age_bucket_at_prediction_time"}
        )
        self.assertIn("close_date", excluded)
        self.assertIn("close_value", excluded)
        self.assertIn("sales_agent_manager_region", excluded)

    def test_open_deals_only_enter_training_with_observed_horizon(self) -> None:
        training = self.result["modelReport"]["training"]
        self.assertGreater(training["censoredOpenOpportunitiesWithObservedHorizon"], 0)
        self.assertGreater(training["censoredOpenSnapshots"], 0)
        self.assertLess(
            training["censoredOpenOpportunitiesWithObservedHorizon"],
            self.result["dashboard"]["summary"]["engaging"],
        )

    def test_referential_integrity_after_canonicalization(self) -> None:
        joins = self.result["dataQuality"]["referentialIntegrity"]
        self.assertEqual(joins["unknownSalesAgents"], 0)
        self.assertEqual(joins["unknownProductsAfterNormalization"], 0)
        self.assertEqual(joins["unknownNonblankAccounts"], 0)
        self.assertEqual(joins["missingAccountsAccepted"], 1425)

    def test_json_files_are_valid_and_match_memory_result(self) -> None:
        filenames = {
            "opportunities.json": "opportunities",
            "dashboard.json": "dashboard",
            "model-report.json": "modelReport",
            "data-quality.json": "dataQuality",
        }
        for filename, result_key in filenames.items():
            payload = json.loads((self.generated / filename).read_text(encoding="utf-8"))
            self.assertEqual(payload, self.result[result_key])


if __name__ == "__main__":
    unittest.main()
