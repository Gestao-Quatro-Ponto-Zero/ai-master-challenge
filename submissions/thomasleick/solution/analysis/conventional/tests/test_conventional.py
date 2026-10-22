import pathlib
import sys
import unittest

MODULE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR))
import run  # noqa: E402


DATA = MODULE_DIR.parents[1] / "data" / "raw"


class ConventionalAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run.build(DATA)
        cls.summary = cls.result[0]

    def test_source_tables_and_hashes(self):
        profiles = self.summary["table_profiles"]
        self.assertEqual({k: v["rows"] for k, v in profiles.items()}, {
            "accounts": 500, "subscriptions": 5000, "feature_usage": 25000,
            "support_tickets": 2000, "churn_events": 600,
        })
        self.assertTrue(all(len(v["sha256"]) == 64 for v in profiles.values()))

    def test_labels_are_distinct_and_reconciled(self):
        labels = {x["label"]: x["positive_accounts"] for x in self.summary["labels"]["overview"]}
        self.assertEqual(labels, {
            "account_churn_flag": 110,
            "any_event_account": 352,
            "has_nonreactivation_event": 339,
            "subscription_churn_flag_account": 312,
        })
        cross = self.summary["labels"]["account_flag_event_crosstab"]
        self.assertEqual(cross["account_flag_true_event_yes"], 75)
        self.assertEqual(sum(cross.values()), 500)

    def test_duplicate_usage_reconciliation_and_joins(self):
        quality = self.summary["usage"]["integrity_and_timing"]
        self.assertEqual((quality["duplicate_usage_ids"], quality["rows_in_duplicate_id_groups"], quality["excess_rows"]), (21, 42, 21))
        self.assertEqual(self.summary["key_cardinality"]["orphan_rows"], {
            "subscriptions_account": 0, "events_account": 0, "tickets_account": 0,
            "usage_subscription": 0, "usage_account": 0,
        })
        self.assertEqual(quality["usage_before_subscription_start"], 19142)
        self.assertEqual(quality["usage_after_subscription_end"], 290)
        repeats = self.summary["key_cardinality"]["account_child_tables"]["event_account_repetition"]
        self.assertEqual(repeats, {"accounts_with_multiple_event_rows": 175,
            "rows_in_repeated_account_groups": 423,
            "excess_event_rows_beyond_first_per_account": 248})

    def test_segment_denominators_and_intervals(self):
        rows = self.result[2]
        group = [r for r in rows if r["label"] == "account_churn_flag" and r["dimension"] == "industry"]
        self.assertEqual(sum(r["accounts"] for r in group), 500)
        for row in group:
            self.assertLessEqual(row["wilson_95_low"], row["prevalence"])
            self.assertGreaterEqual(row["wilson_95_high"], row["prevalence"])

    def test_support_missingness_and_revenue_semantics(self):
        self.assertEqual(self.summary["support"]["missing_satisfaction_tickets"], 825)
        self.assertIn("not unique/current/at-risk recurring revenue", self.summary["revenue"]["mrr_amount"]["label_comparisons"][0]["interpretation"])
        self.assertEqual(self.summary["revenue"]["refund_amount_usd"]["nonzero_event_rows"], 142)
        with (DATA / "ravenstack_subscriptions.csv").open(newline="", encoding="utf-8-sig") as f:
            import csv
            rows = list(csv.DictReader(f))
        expected = sum(float(r["mrr_amount"]) for r in rows)
        self.assertEqual(self.summary["revenue"]["mrr_amount"]["raw_subscription_row_sum"], expected)
        self.assertEqual(self.summary["revenue"]["mrr_amount"]["rows"]["n"], len(rows))

    def test_no_rate_or_probability_is_created(self):
        self.assertTrue(all(row["churn_rate"] is None for row in self.summary["labels"]["event_rows_by_month"]))
        self.assertTrue(all("prevalence" in x and "definition" in x for x in self.summary["labels"]["overview"]))
        self.assertTrue(all("not future churn risk" in x["explanation"] for x in self.result[1]))

    def test_label_disagreement_reconciles_historical_312(self):
        self.assertEqual(self.summary["labels"]["account_flag_vs_any_event_xor_accounts"], 312)
        self.assertEqual(self.summary["labels"]["account_vs_subscription_flag_xor_accounts"], 278)
        self.assertEqual(self.summary["labels"]["any_pairwise_label_disagreement_among_accounts"], 401)

    def test_bootstrap_is_deterministic_and_account_level(self):
        first = run.bootstrap_mean_difference([1, 2, 3], [0, 1, 2], seed=123)
        second = run.bootstrap_mean_difference([1, 2, 3], [0, 1, 2], seed=123)
        self.assertEqual(first, second)
        self.assertEqual(first["mean_difference"], 1.0)
        self.assertEqual(first["positive_accounts_with_measure"], 3)


if __name__ == "__main__":
    unittest.main()
