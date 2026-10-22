from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE))
from reconstruct import _annual_record, active_subscription_rows, reconstruct  # noqa: E402


def account(account_id: str, churn_flag: str = "False") -> dict[str, str]:
    return {"account_id": account_id, "churn_flag": churn_flag}


def subscription(subscription_id: str, account_id: str, start: str, end: str = "", churn_flag: str = "False") -> dict[str, str]:
    return {"subscription_id": subscription_id, "account_id": account_id, "start_date": start, "end_date": end, "churn_flag": churn_flag}


class HistoricalChurnTests(unittest.TestCase):
    def test_snapshot_end_date_is_exclusive_and_multiple_subscriptions_collapse_to_account(self) -> None:
        rows = [subscription("s1", "a", "2023-01-01"), subscription("s2", "a", "2023-05-01", "2024-01-01", "True")]
        active = active_subscription_rows(rows, date(2024, 1, 1))
        self.assertEqual([r["subscription_id"] for r in active], ["s1"])

    def test_account_can_churn_then_reactivate_within_year(self) -> None:
        accounts = [account("a")]
        subscriptions = [
            subscription("s1", "a", "2023-01-01", "2024-03-01", "True"),
            subscription("s2", "a", "2024-04-01"),
        ]
        result = _annual_record(2024, accounts, subscriptions, [])
        self.assertEqual(result["opening_accounts"], 1)
        self.assertEqual(result["gross_opening_account_exits_any_gap"], 1)
        self.assertEqual(result["reactivated_opening_accounts_after_gap"], 1)
        self.assertEqual(result["opening_accounts_inactive_at_year_end"], 0)
        self.assertEqual(result["classical_logo_churn_rate_gross_exit"], 1.0)

    def test_account_with_final_subscription_end_is_a_gross_logo_exit(self) -> None:
        result = _annual_record(2024, [account("a")], [subscription("s", "a", "2023-01-01", "2024-09-01", "True")], [])
        self.assertEqual(result["gross_opening_account_exits_any_gap"], 1)
        self.assertEqual(result["opening_accounts_inactive_at_year_end"], 1)
        self.assertEqual(result["classical_logo_churn_rate_gross_exit"], 1.0)

    def test_zero_opening_denominator_is_undefined_not_zero_percent(self) -> None:
        result = _annual_record(2023, [account("a")], [subscription("s", "a", "2023-01-09")], [])
        self.assertEqual(result["opening_accounts"], 0)
        self.assertIsNone(result["classical_logo_churn_rate_gross_exit"])
        self.assertIsNone(result["subscription_churn_rate_opening_cohort"])

    def test_source_reconstruction_uses_real_csv_counts_and_reports_conditional_rate(self) -> None:
        solution = MODULE.parents[1]
        result = reconstruct(solution / "data" / "raw")
        self.assertEqual(result["source_counts"], {"accounts": 500, "subscriptions": 5000, "churn_events": 600})
        self.assertEqual(result["snapshots"]["2023-01-01"]["active_accounts"], 0)
        self.assertEqual(result["snapshots"]["2024-01-01"]["active_accounts"], 191)
        self.assertEqual(result["snapshots"]["2025-01-01"]["active_accounts"], 500)
        self.assertEqual(result["annual"]["2023"]["classical_logo_churn_rate_gross_exit"], None)
        self.assertEqual(result["annual"]["2024"]["classical_logo_churn_rate_gross_exit"], 0.0)
        self.assertEqual(result["annual"]["2024"]["opening_subscription_rows"], 655)
        self.assertEqual(result["annual"]["2024"]["opening_subscriptions_not_active_at_year_end"], 66)
        self.assertEqual(result["data_quality"]["invalid_nonpositive_subscription_intervals"], 13)
        self.assertEqual(result["event_date_conflicts"]["2024"]["rows_during_any_date_active_subscription"], 443)
        self.assertEqual(len(result["monthly"]), 24)
        self.assertIsNone(result["monthly"][0]["logo_churn_rate"])
        monthly_exit_months = [row["month"] for row in result["monthly"] if row["gross_logo_exits_any_interval_gap"]]
        self.assertEqual(monthly_exit_months, ["2023-11", "2024-03", "2024-04", "2024-09"])


if __name__ == "__main__":
    unittest.main()
