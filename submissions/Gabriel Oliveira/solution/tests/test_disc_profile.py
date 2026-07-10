"""Tests para inferencia DISC."""
from __future__ import annotations

import unittest

import pandas as pd

from disc_profile import build_lead_profile, infer_disc_profile


class DiscProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.today = pd.Timestamp("2017-12-31")

    def test_returns_defined_disc_for_complete_data(self) -> None:
        row = pd.Series(
            {
                "opportunity_id": "1C1I7A6R",
                "sales_agent": "Moses Frase",
                "product": "GTK 500",
                "account": "Cancity",
                "deal_stage": "Engaging",
                "engage_date": "2017-11-10",
                "close_value": 18000,
                "sector": "technolgy",
                "subsidiary_of": "Acme Corporation",
                "revenue": 3_500.0,
                "employees": 8000,
                "year_established": 1992,
                "manager": "Dustin Brinkmann",
                "regional_office": "Central",
            }
        )

        disc = infer_disc_profile(row, today=self.today)
        self.assertIn(disc.disc_profile, {"D", "I", "S", "C"})
        self.assertGreaterEqual(disc.disc_confidence, 45)

    def test_fallback_when_critical_data_missing(self) -> None:
        row = pd.Series(
            {
                "opportunity_id": None,
                "sales_agent": "Moses Frase",
                "product": "GTK 500",
                "account": None,
                "deal_stage": None,
                "engage_date": None,
                "close_value": 0,
                "sector": None,
                "subsidiary_of": None,
                "revenue": None,
                "employees": None,
                "year_established": None,
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
