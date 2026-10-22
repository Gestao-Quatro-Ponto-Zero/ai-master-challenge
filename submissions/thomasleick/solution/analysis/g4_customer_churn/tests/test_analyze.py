from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE))
from analyze import _period, active_rows, analyze  # noqa: E402


def sub(sid: str, account: str, start: str, end: str = "") -> dict[str, str]:
    return {"subscription_id": sid, "account_id": account, "start_date": start, "end_date": end}


class G4CustomerChurnTests(unittest.TestCase):
    def test_boundary_is_end_exclusive_and_two_subscriptions_are_one_logo(self) -> None:
        rows = [sub("s1", "a", "2023-01-01", "2024-04-01"), sub("s2", "a", "2024-03-01")]
        self.assertEqual(len(active_rows(rows, date(2024, 3, 1))), 2)
        self.assertEqual(len({r["account_id"] for r in active_rows(rows, date(2024, 3, 1))}), 1)
        self.assertEqual(len(active_rows(rows, date(2024, 4, 1))), 1)

    def test_temporary_coverage_gap_counts_as_gross_conditional_loss(self) -> None:
        accounts = [{"account_id": "a", "churn_flag": "False"}]
        rows = [sub("s1", "a", "2023-01-01", "2024-03-01"), sub("s2", "a", "2024-04-01")]
        result = _period(2024, accounts, rows, [])
        self.assertEqual(result["opening_accounts_with_any_date_coverage_gap"], 1)
        self.assertEqual(result["opening_accounts_without_coverage_at_close"], 0)
        self.assertEqual(result["conditional_gross_date_churn_rate"], 1.0)

    def test_lost_account_with_no_successor_is_one_distinct_customer(self) -> None:
        accounts = [{"account_id": "a", "churn_flag": "False"}]
        result = _period(2024, accounts, [sub("s1", "a", "2023-01-01", "2024-06-01")], [])
        self.assertEqual(result["opening_active_accounts"], 1)
        self.assertEqual(result["opening_accounts_without_coverage_at_close"], 1)
        self.assertEqual(result["conditional_closing_date_loss_rate"], 1.0)

    def test_reactivation_marker_is_not_automatically_an_active_base_loss(self) -> None:
        accounts = [{"account_id": "a", "churn_flag": "False"}]
        events = [{"account_id": "a", "churn_date": "2024-05-01", "is_reactivation": "True"}]
        result = _period(2024, accounts, [sub("s1", "a", "2023-01-01")], events)
        self.assertEqual(result["opening_accounts_with_any_date_coverage_gap"], 0)
        self.assertEqual(result["event_rows_nonreactivation"], 0)

    def test_real_data_primary_rate_is_unknown_and_conditional_rate_is_disclosed(self) -> None:
        solution = MODULE.parents[1]
        result = analyze(solution / "data" / "raw")
        self.assertEqual(result["primary_customer_churn"]["classification"], "C — CUSTOMER CHURN NOT IDENTIFIABLE")
        self.assertIsNone(result["annual"]["2023"]["conditional_gross_date_churn_rate"])
        self.assertEqual(result["annual"]["2024"]["opening_active_accounts"], 191)
        self.assertEqual(result["annual"]["2024"]["opening_accounts_with_any_date_coverage_gap"], 0)
        self.assertEqual(result["annual"]["2024"]["opening_accounts_with_nonreactivation_event"], 103)
        self.assertEqual(result["annual"]["2024"]["nonreactivation_event_rows_with_active_subscription"], 443)
        self.assertEqual(len(result["cohorts"]["rows"]), 300)
        self.assertEqual(len(result["quarterly"]), 8)
        self.assertEqual(result["reconciliation"]["movement_bridge"]["residual"], 0)


if __name__ == "__main__":
    unittest.main()
