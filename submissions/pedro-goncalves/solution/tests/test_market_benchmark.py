from __future__ import annotations

import unittest

from src.support_copilot.market_benchmark import calculate_market_benchmark


class MarketBenchmarkTests(unittest.TestCase):
    def test_calculates_public_variable_cost_range(self):
        result = calculate_market_benchmark(
            annual_volume=30_000,
            technical_coverage=0.697,
        )

        self.assertAlmostEqual(result.covered_monthly, 1742.5)
        self.assertAlmostEqual(result.covered_weekly, 402.1153846)
        self.assertAlmostEqual(result.monthly_low_usd, 853.825)
        self.assertAlmostEqual(result.monthly_high_usd, 1725.075)
        self.assertAlmostEqual(result.weekly_low_usd, 197.0365385)
        self.assertAlmostEqual(result.weekly_high_usd, 398.0942308)

    def test_rejects_invalid_coverage(self):
        with self.assertRaises(ValueError):
            calculate_market_benchmark(
                annual_volume=30_000,
                technical_coverage=1.01,
            )
