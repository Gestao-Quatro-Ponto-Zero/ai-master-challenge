import tempfile
import unittest
from pathlib import Path

from analysis.business_drivers.run import run, wilson


class BusinessDriverTests(unittest.TestCase):
    def test_wilson_interval_bounds(self):
        low, high = wilson(5, 10)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)

    def test_real_data_labels_and_cohort_safety(self):
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as temp:
            result = run(root / "data" / "raw", Path(temp))
        self.assertEqual(result["record_counts"], {"accounts": 500, "subscriptions": 5000, "usage_rows": 25000, "support_tickets": 2000, "event_rows": 600})
        self.assertEqual(result["labels"]["account_positive_counts"], {"account_flag": 110, "any_event": 352, "nonreactivation_event": 339, "subscription_flag_account": 312})
        self.assertEqual(result["labels"]["any_label_disagreement_accounts"], 401)
        self.assertIsNone(result["cohorts"]["retention_heatmap"])
        self.assertEqual(result["cohorts"]["status"], "NOT_IDENTIFIABLE")
        self.assertTrue(result["cohorts"]["first_subscription_start_rows"])

    def test_join_interval_bounds_and_duplicate_accounting(self):
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as temp:
            result = run(root / "data" / "raw", Path(temp))
        c = result["usage"]["concentration"]
        self.assertEqual(c["duplicate_usage_id_groups"], 21)
        self.assertEqual(c["rows_in_duplicate_usage_id_groups"], 42)
        self.assertEqual(c["excess_rows_after_one_per_usage_id"], 21)
        self.assertEqual(c["valid_unique_usage_ids_with_any_valid_row"], 5565)
        self.assertEqual(c["valid_rows_after_first_source_occurrence"], 5562)
        self.assertEqual(c["valid_rows_with_duplicate_ids"], 14)
        self.assertEqual(c["valid_rows_after_excluding_all_rows_in_duplicate_id_groups"], 5554)
        self.assertLess(c["valid_interval_usage_rows"], 25000)
        self.assertLessEqual(c["top_10_accounts_share"], c["top_50_accounts_share"])

    def test_segments_and_accounts_keep_label_semantics(self):
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as temp:
            result = run(root / "data" / "raw", Path(temp))
        labels = {row["label"] for row in result["segments"]}
        self.assertEqual(labels, {"account_flag", "any_event", "nonreactivation_event", "subscription_flag_account"})
        self.assertTrue(all("future-risk estimate" in row["selection_reason"] for row in result["account_investigation_candidates"]))

    def test_usage_growth_is_reported_as_raw_and_interval_bounded_series(self):
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as temp:
            result = run(root / "data" / "raw", Path(temp))
        years = {row["year"]: row for row in result["usage"]["yearly_source_trend"]}
        self.assertEqual(len(result["usage"]["monthly_source_trend"]), 24)
        self.assertEqual(years[2023]["source_rows"], 12430)
        self.assertEqual(years[2024]["source_rows"], 12570)
        self.assertEqual(years[2023]["distinct_accounts_observed"], 500)
        self.assertEqual(years[2024]["distinct_accounts_observed"], 500)
        self.assertEqual(years[2023]["recorded_usage_count"], 124561)
        self.assertEqual(years[2024]["recorded_usage_count"], 125964)
        self.assertEqual(years[2023]["valid_interval_rows"], 514)
        self.assertEqual(years[2024]["valid_interval_rows"], 5054)

    def test_support_comparison_keeps_account_grain_and_missing_scores_visible(self):
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as temp:
            result = run(root / "data" / "raw", Path(temp))
        support = result["support"]
        event_yes = next(row for row in support["by_label"] if row["label"] == "any_event" and row["group"] == "positive")
        event_no = next(row for row in support["by_label"] if row["label"] == "any_event" and row["group"] == "negative")
        self.assertEqual(support["satisfaction_missing_all_tickets"], 825)
        self.assertEqual(event_yes["account_count"], 352)
        self.assertEqual(event_yes["ticket_rows"], 1395)
        self.assertEqual(event_yes["satisfaction_missing_tickets"], 580)
        self.assertEqual(event_no["ticket_rows"], 605)
        self.assertIsNotNone(event_yes["satisfaction_mean_account_average"])
        self.assertIsNotNone(event_no["mean_account_escalation_rate"])


if __name__ == "__main__":
    unittest.main()
