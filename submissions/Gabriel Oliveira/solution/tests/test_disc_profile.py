"""Tests para inferencia DISC."""
from __future__ import annotations

import unittest

import pandas as pd

from disc_profile import build_lead_profile, infer_disc_profile


class DiscProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.today = pd.Timestamp("2025-07-01")

    def test_returns_defined_disc_for_complete_data(self) -> None:
        row = pd.Series(
            {
                "opportunity_id": "OPP_X",
                "sales_agent": "Ana",
                "product": "GTX Enterprise",
                "account": "account_0001",
                "deal_stage": "Engaging",
                "engage_date": "05/20/2025",
                "close_value": 18000,
                "industry": "Technology",
                "acquisition_channel": "social",
                "revenue": 3_500_000,
                "employees": 800,
                "has_trial": True,
                "manager": "Carlos",
                "regional_office": "Sao Paulo",
            }
        )

        disc = infer_disc_profile(row, today=self.today)
        self.assertIn(disc.disc_profile, {"D", "I", "S", "C"})
        self.assertGreaterEqual(disc.disc_confidence, 45)

    def test_fallback_when_critical_data_missing(self) -> None:
        row = pd.Series(
            {
                "opportunity_id": None,
                "sales_agent": "Ana",
                "product": "GTX Enterprise",
                "account": None,
                "deal_stage": None,
                "engage_date": None,
                "close_value": 0,
                "industry": None,
                "acquisition_channel": None,
                "revenue": None,
                "employees": None,
                "has_trial": None,
                "manager": None,
                "regional_office": None,
            }
        )

        profile = build_lead_profile(row, today=self.today)
        self.assertEqual(profile["disc_profile"], "indefinido")
        self.assertIsInstance(profile["disc_rationale"], str)
        self.assertGreater(len(profile["disc_rationale"]), 20)


if __name__ == "__main__":
    unittest.main()
