from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE))
from investigate import SNAPSHOT_END, SNAPSHOT_START, _covered_all_year, active, investigate  # noqa: E402


def write_table(root: Path, name: str, headers: list[str], rows: list[dict[str, str]]) -> None:
    with (root / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


class ContractChurnForensicsTests(unittest.TestCase):
    def test_real_csv_revalidates_66_rows_57_accounts_and_443_conflicts(self) -> None:
        result = investigate(MODULE.parents[1] / "data" / "raw")
        counts = result["revalidation"]
        self.assertEqual((counts["opening_accounts"], counts["opening_subscription_ids"]), (191, 655))
        self.assertEqual((counts["subscription_rows_ended_before_2025_boundary"], counts["distinct_accounts_in_66"]), (66, 57))
        self.assertEqual(counts["ended_subscriptions_with_another_active_at_end"], 66)
        self.assertEqual(counts["ended_subscriptions_with_successor_start_on_or_after_end"], 55)
        self.assertEqual(counts["ended_subscriptions_with_upgrade_flag"], 8)
        self.assertEqual(counts["ended_subscriptions_with_downgrade_flag"], 1)
        self.assertEqual(counts["ended_subscriptions_with_plan_different_from_account_initial_plan"], 48)
        self.assertEqual(counts["opening_accounts_with_any_2024_coverage_gap"], 0)
        self.assertEqual(counts["events_with_any_active_subscription"], 443)
        self.assertEqual(counts["distinct_accounts_among_events_with_active_subscription"], 302)
        self.assertEqual(counts["events_with_multiple_active_subscriptions"], 395)
        self.assertEqual(result["reactivation_summary"], {
            "event_rows": 55, "distinct_accounts": 49, "rows_with_active_subscription_on_event_date": 51,
            "rows_after_any_same_account_subscription_end": 20,
            "rows_with_later_same_account_subscription_start": 45,
            "rows_after_prior_nonreactivation_event": 33,
            "distinct_accounts_in_2024_opening_base": 14,
            "interpretation": result["reactivation_summary"]["interpretation"],
        })
        self.assertEqual(result["event_end_proximity_counts"]["443_events_with_active_subscription"], {
            "within_0_days": 5, "within_7_days": 39, "within_30_days": 104, "within_60_days": 160,
        })

    def test_snapshot_boundary_is_exclusive_for_end_date(self) -> None:
        self.assertTrue(active({"start_date": "2023-01-01", "end_date": "2024-01-02"}, SNAPSHOT_START))
        self.assertFalse(active({"start_date": "2023-01-01", "end_date": "2024-01-01"}, SNAPSHOT_START))
        self.assertFalse(active({"start_date": "2025-01-01", "end_date": ""}, SNAPSHOT_START))

    def test_coverage_merge_detects_exact_successor_and_real_gap(self) -> None:
        exact_successor = [
            {"start_date": "2023-01-01", "end_date": "2024-06-01"},
            {"start_date": "2024-06-01", "end_date": ""},
        ]
        gap = [
            {"start_date": "2023-01-01", "end_date": "2024-06-01"},
            {"start_date": "2024-06-02", "end_date": ""},
        ]
        self.assertTrue(_covered_all_year(exact_successor))
        self.assertFalse(_covered_all_year(gap))
        self.assertEqual(SNAPSHOT_END.isoformat(), "2025-01-01")

    def test_synthetic_case_covers_overlapping_contract_successor_gap_and_event_join_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_table(root, "ravenstack_accounts.csv",
                        ["account_id", "account_name", "industry", "country", "signup_date", "referral_source", "plan_tier", "seats", "is_trial", "churn_flag"], [
                            {"account_id": "A", "account_name": "Synthetic A", "industry": "X", "country": "US", "signup_date": "2023-01-01", "referral_source": "organic", "plan_tier": "Pro", "seats": "3", "is_trial": "False", "churn_flag": "True"},
                            {"account_id": "B", "account_name": "Synthetic B", "industry": "Y", "country": "CA", "signup_date": "2023-01-01", "referral_source": "ads", "plan_tier": "Basic", "seats": "1", "is_trial": "False", "churn_flag": "False"},
                        ])
            write_table(root, "ravenstack_subscriptions.csv",
                        ["subscription_id", "account_id", "start_date", "end_date", "plan_tier", "seats", "mrr_amount", "arr_amount", "is_trial", "upgrade_flag", "downgrade_flag", "churn_flag", "billing_frequency", "auto_renew_flag"], [
                            {"subscription_id": "A1", "account_id": "A", "start_date": "2023-01-01", "end_date": "2024-06-01", "plan_tier": "Pro", "seats": "3", "mrr_amount": "100", "arr_amount": "1200", "is_trial": "False", "upgrade_flag": "True", "downgrade_flag": "False", "churn_flag": "True", "billing_frequency": "monthly", "auto_renew_flag": "True"},
                            {"subscription_id": "A2", "account_id": "A", "start_date": "2023-12-01", "end_date": "", "plan_tier": "Pro", "seats": "3", "mrr_amount": "100", "arr_amount": "1200", "is_trial": "False", "upgrade_flag": "False", "downgrade_flag": "False", "churn_flag": "False", "billing_frequency": "monthly", "auto_renew_flag": "True"},
                            {"subscription_id": "A3", "account_id": "A", "start_date": "2024-06-01", "end_date": "", "plan_tier": "Enterprise", "seats": "4", "mrr_amount": "200", "arr_amount": "2400", "is_trial": "False", "upgrade_flag": "False", "downgrade_flag": "False", "churn_flag": "False", "billing_frequency": "annual", "auto_renew_flag": "True"},
                            {"subscription_id": "B1", "account_id": "B", "start_date": "2023-01-01", "end_date": "2024-02-01", "plan_tier": "Basic", "seats": "1", "mrr_amount": "50", "arr_amount": "600", "is_trial": "False", "upgrade_flag": "False", "downgrade_flag": "False", "churn_flag": "True", "billing_frequency": "monthly", "auto_renew_flag": "False"},
                        ])
            write_table(root, "ravenstack_churn_events.csv",
                        ["churn_event_id", "account_id", "churn_date", "reason_code", "refund_amount_usd", "preceding_upgrade_flag", "preceding_downgrade_flag", "is_reactivation", "feedback_text"], [
                            {"churn_event_id": "E1", "account_id": "A", "churn_date": "2024-05-20", "reason_code": "pricing", "refund_amount_usd": "12", "preceding_upgrade_flag": "True", "preceding_downgrade_flag": "False", "is_reactivation": "False", "feedback_text": ""},
                            {"churn_event_id": "E2", "account_id": "B", "churn_date": "2024-02-01", "reason_code": "support", "refund_amount_usd": "0", "preceding_upgrade_flag": "False", "preceding_downgrade_flag": "False", "is_reactivation": "False", "feedback_text": ""},
                            {"churn_event_id": "E3", "account_id": "B", "churn_date": "2024-06-01", "reason_code": "reactivated", "refund_amount_usd": "0", "preceding_upgrade_flag": "False", "preceding_downgrade_flag": "False", "is_reactivation": "True", "feedback_text": ""},
                        ])
            result = investigate(root)
            counts = result["revalidation"]
            self.assertEqual((counts["opening_accounts"], counts["opening_subscription_ids"]), (2, 3))
            self.assertEqual(counts["subscription_rows_ended_before_2025_boundary"], 2)
            self.assertEqual(counts["distinct_accounts_in_66"], 2)
            self.assertEqual(counts["ended_subscriptions_with_another_active_at_end"], 1)
            self.assertEqual(counts["ended_subscriptions_with_later_subscription_start"], 0)
            self.assertEqual(counts["opening_accounts_with_any_2024_coverage_gap"], 1)
            self.assertEqual(counts["opening_accounts_lost_all_coverage_at_2025_boundary"], 1)
            self.assertEqual(counts["events_with_any_active_subscription"], 1)
            event = result["conflicting_events"][0]
            self.assertEqual(event["churn_event_id"], "E1")
            self.assertIn("UNKNOWN", event["event_subscription_link"])
            self.assertNotIn("subscription_id", event)
            self.assertEqual(result["financial_descriptives"]["event_refunds_2024_recorded_sum_usd"], 12)
            self.assertEqual(counts["ended_subscriptions_with_successor_start_on_or_after_end"], 1)
            self.assertEqual(result["reactivation_summary"]["rows_with_active_subscription_on_event_date"], 0)
            self.assertEqual(result["reactivation_events"][0]["prior_nonreactivation_event_ids"], ["E2"])

    def test_revenue_row_sum_is_explicitly_not_accounting_revenue(self) -> None:
        result = investigate(MODULE.parents[1] / "data" / "raw")
        money = result["financial_descriptives"]
        self.assertEqual(money["sum_mrr_rows_not_current_revenue"], 93159)
        self.assertEqual(money["sum_arr_rows_not_revenue_lost"], 1117908)
        self.assertIn("non-authoritative row totals", money["interpretation"])
        self.assertEqual((money["conflicting_event_refund_nonzero_rows"], money["conflicting_event_refund_recorded_sum_usd"]), (110, 7044.82))


if __name__ == "__main__":
    unittest.main()
