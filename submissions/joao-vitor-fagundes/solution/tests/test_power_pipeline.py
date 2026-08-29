from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SOLUTION_DIR = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = SOLUTION_DIR / "scripts" / "build_power_dataset.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_power_dataset", BUILD_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load POWER builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PowerPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory(prefix="power-test-")
        cls.output_dir = Path(cls.temp_dir.name)
        cls.builder = load_builder()
        cls.summary = cls.builder.build(cls.output_dir)

        with (cls.output_dir / "products.csv").open(encoding="utf-8", newline="") as handle:
            cls.products = list(csv.DictReader(handle))
        with (cls.output_dir / "power_scores.csv").open(encoding="utf-8", newline="") as handle:
            cls.scores = list(csv.DictReader(handle))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def test_expected_row_counts_and_coverage(self) -> None:
        self.assertEqual(self.summary["rows"]["opportunities"], 8800)
        self.assertEqual(self.summary["rows"]["power_scores"], 8800)
        self.assertEqual(
            self.summary["coverage"],
            {
                "propensity": 7795,
                "opportunity_value": 8800,
                "warmth": 8800,
                "execution_fit": 7742,
            },
        )

    def test_catalog_tiers_are_derived_from_price_rank(self) -> None:
        tiers = {row["product"]: row["value_tier"] for row in self.products}
        self.assertEqual(
            tiers,
            {
                "GTX Basic": "Bronze",
                "GTX Pro": "Gold",
                "MG Special": "Bronze",
                "MG Advanced": "Silver",
                "GTX Plus Pro": "Gold",
                "GTX Plus Basic": "Silver",
                "GTK 500": "Diamond",
            },
        )

    def test_scores_stay_in_range_and_ids_are_unique(self) -> None:
        self.assertEqual(len({row["opportunity_id"] for row in self.scores}), 8800)
        for row in self.scores:
            for field in (
                "propensity_score",
                "opportunity_value_score",
                "warmth_score",
                "execution_fit_score",
            ):
                if row[field]:
                    self.assertGreaterEqual(float(row[field]), 0)
                    self.assertLessEqual(float(row[field]), 100)
            self.assertEqual(len(row["input_hash"]), 64)

    def test_execution_fit_contains_only_implemented_criteria(self) -> None:
        evidence = json.loads(next(row for row in self.scores if row["execution_fit_score"])["execution_fit_evidence"])
        self.assertEqual(
            [fit["name"] for fit in evidence["fits"]],
            ["product", "sector", "ticket"],
        )
        self.assertEqual(evidence["company_fit"]["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
