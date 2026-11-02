"""Independent denominator, aggregation, permutation and effort-accounting checks."""

import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("diagnosis", ROOT / "solution/diagnose_support.py")
diagnosis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnosis)


def ticket(status="Closed", score="", channel="Chat", priority="High", kind="Technical issue", text="example"):
    return {**dict.fromkeys(diagnosis.AUDIT.CUSTOMER_COLUMNS, ""), "Ticket Status": status,
            "Customer Satisfaction Rating": score, "Ticket Channel": channel,
            "Ticket Priority": priority, "Ticket Type": kind, "Ticket Description": text}


def case(**changes):
    return {"name": "fixture", "tickets": 100, "eligible_share": .5, "assisted_share": .8,
            "manual_minutes": 10, "assisted_minutes": 4, "review_share": 1, "review_minutes": 1,
            "error_share": .1, "rework_minutes": 5, "fixed_minutes": 20, "hourly_value_brl": 60,
            **changes}


class DiagnosisTests(unittest.TestCase):
    def test_ratings_population_and_missing_scores_have_explicit_denominators(self):
        result = diagnosis.summarize([ticket(score="5"), ticket(score="1"), ticket(),
                                      ticket("Open", "5"), ticket("Pending Customer Response", "invalid")])
        self.assertEqual(result["tickets"], 5)
        self.assertEqual(result["closed"], 3)
        self.assertEqual(result["nonclosed_share"], .4)
        self.assertEqual(result["valid_rated_all"], 3)
        self.assertEqual(result["rated_closed"], 2)
        self.assertEqual(result["rated_nonclosed"], 1)
        self.assertEqual(result["unrated_closed"], 1)
        self.assertEqual(result["invalid_nonblank_ratings"], 1)
        self.assertEqual(result["csat_mean"], 3)
        self.assertEqual(result["csat_coverage_all"], .6)
        self.assertAlmostEqual(result["csat_coverage_closed"], 2 / 3, places=6)
        self.assertEqual(result["low_csat_share"], .5)

    def test_empty_population_is_unavailable_not_zero_satisfaction(self):
        result = diagnosis.summarize([])
        self.assertEqual(result["tickets"], 0)
        self.assertIsNone(result["csat_mean"])
        self.assertIsNone(result["csat_coverage_all"])
        self.assertIsNone(result["low_csat_share"])

    def test_cartesian_groups_keep_empty_combinations_and_reconcile_totals(self):
        rows = [ticket(score="4", channel="Chat", priority="High"),
                ticket("Open", channel="Email", priority="Low")]
        table = diagnosis.segments(rows)
        triples = [r for r in table if r["grouping"] == " + ".join(diagnosis.DIMENSIONS)]
        self.assertEqual(len(triples), 4)
        self.assertEqual(sum(r["tickets"] for r in triples), 2)
        self.assertEqual(sum(r["closed"] for r in triples), 1)
        self.assertEqual(sum(r["tickets"] == 0 for r in triples), 2)
        self.assertTrue(all(r["csat_mean"] is None for r in triples if not r["rated_closed"]))

    def test_conflicting_labels_are_flagged_without_dropping_records(self):
        rows = [ticket(kind="Technical issue", text="Ａ  test"), ticket(kind="Refund request", text="a test")]
        duplicate, conflicts = diagnosis.quality_groups(rows)
        result = diagnosis.summarize(rows, duplicate, conflicts)
        self.assertEqual(result["tickets"], 2)
        self.assertEqual(result["conflicting_type_rows"], 2)
        self.assertEqual(result["duplicate_description_rows"], 2)

    def test_mean_variation_distinguishes_separated_and_balanced_groups(self):
        self.assertEqual(diagnosis.mean_variation([1, 1, 5, 5], ["A", "A", "B", "B"]), 1)
        self.assertEqual(diagnosis.mean_variation([1, 5, 1, 5], ["A", "A", "B", "B"]), 0)
        result = diagnosis.association([ticket(score="3"), ticket(score="3", channel="Email")],
                                       "Ticket Channel", repeats=9, seed=1)
        self.assertEqual(result["permutation_p"], 1)

    def test_holm_correction_preserves_original_field_order(self):
        adjusted = diagnosis.holm_adjust([.01, .04, .03])
        for observed, expected in zip(adjusted, [.03, .06, .06]):
            self.assertAlmostEqual(observed, expected)

    def test_effort_accounting_subtracts_review_rework_and_fixed_overhead(self):
        result = diagnosis.scenario(case())
        # 40 assisted * (10-4) - 40*1 - 40*.1*5 - 20 = 160 minutes.
        self.assertEqual(result["assisted_cases"], 40)
        self.assertAlmostEqual(result["net_capacity_hours"], 160 / 60, places=6)
        self.assertEqual(result["capacity_value_at_assumed_rate_brl"], 160)
        self.assertEqual(result["break_even_manual_minutes_per_assisted_case"], 6)

    def test_negative_savings_and_zero_coverage_are_preserved(self):
        loss = diagnosis.scenario(case(assisted_minutes=12))
        self.assertLess(loss["net_capacity_hours"], 0)
        zero = diagnosis.scenario(case(eligible_share=0))
        self.assertAlmostEqual(zero["net_capacity_hours"], -20 / 60, places=6)
        self.assertIsNone(zero["break_even_manual_minutes_per_assisted_case"])

    def test_invalid_scenario_parameters_are_rejected(self):
        for change in [{"eligible_share": 1.1}, {"review_share": -.1}, {"fixed_minutes": -1},
                       {"manual_minutes": float("nan")}, {"tickets": True}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                diagnosis.scenario(case(**change))

    def test_diagnosis_uses_hash_locked_csv_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data").mkdir()
            config = json.loads((ROOT / "data/diagnosis-assumptions.json").read_text())
            config["permutation_repeats"] = 9
            (root / "data/diagnosis-assumptions.json").write_text(json.dumps(config))
            source = root / "data/tickets.csv"
            with source.open("w", newline="") as output:
                writer = csv.DictWriter(output, fieldnames=diagnosis.AUDIT.CUSTOMER_COLUMNS)
                writer.writeheader()
                writer.writerows([ticket(score="1"), ticket(score="5", channel="Email")])
            manifest = {"datasets": {"customer_support": {"file": {
                "path": "data/tickets.csv", "sha256": diagnosis.AUDIT.sha256(source)}}}}
            (root / "data/manifest.json").write_text(json.dumps(manifest))
            first = diagnosis.diagnose(root)
            self.assertEqual(first, diagnosis.diagnose(root))
            with source.open("a") as output:
                output.write("changed\n")
            with self.assertRaisesRegex(ValueError, "hash differs"):
                diagnosis.diagnose(root)


if __name__ == "__main__":
    unittest.main()
