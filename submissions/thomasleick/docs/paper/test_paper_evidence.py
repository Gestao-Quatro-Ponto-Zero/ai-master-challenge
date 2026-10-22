"""Reproducibility checks for the executive paper's highest-impact claims."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOLUTION = ROOT / "solution"
DATA = SOLUTION / "data/raw"
LEDGER = json.loads((SOLUTION / "analysis/daily_portfolio_churn/outputs/g4-alignment/daily-portfolio-churn.json").read_text())
BUSINESS = json.loads((SOLUTION / "analysis/business_drivers/outputs/g4-alignment/business-investigation.json").read_text())
PDF = HERE / "RAVENSTACK-THE-CHURN-PARADOX.pdf"
MD = HERE / "RAVENSTACK-THE-CHURN-PARADOX.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PaperEvidenceTests(unittest.TestCase):
    def test_source_hashes_match_reconstructed_ledger(self):
        for name, expected in LEDGER["metadata"]["source_hashes_sha256"].items():
            self.assertEqual(digest(DATA / name), expected, name)

    def test_event_intensity_and_exposure_denominators(self):
        monthly = LEDGER["periods"]["MONTHLY"]
        self.assertEqual(len(monthly), 24)
        january = next(row for row in monthly if row["period"] == "2023-01")
        self.assertEqual(january["opening_plan_relations"], 0)
        self.assertIsNone(january["opening_cohort_churn_any_pct"])
        self.assertIsNone(january["opening_cohort_churn_at_close_pct"])
        expected = {
            "2023": (845, 1406, 73, 6, 2),
            "2024": (3909, 9414, 527, 56, 6),
        }
        for year, (account_months, relation_months, events, plan_losses, customer_losses) in expected.items():
            rows = [r for r in monthly if r["period"].startswith(year)]
            self.assertEqual(sum(r["opening_customers"] for r in rows), account_months)
            self.assertEqual(sum(r["opening_plan_relations"] for r in rows), relation_months)
            self.assertEqual(sum(r["recorded_event_rows"] for r in rows), events)
            self.assertEqual(sum(r["gross_plan_relation_loss_events"] for r in rows), plan_losses)
            self.assertEqual(sum(r["gross_customer_churn_events"] for r in rows), customer_losses)

    def test_october_and_december_monthly_highlights(self):
        monthly = LEDGER["periods"]["MONTHLY"]
        october = next(row for row in monthly if row["period"] == "2024-10")
        december = next(row for row in monthly if row["period"] == "2024-12")
        self.assertEqual((october["opening_relations_lost_any_time"], october["opening_plan_relations"]), (9, 1073))
        self.assertAlmostEqual(october["opening_cohort_churn_any_pct"], .84, places=2)
        self.assertEqual(max(row["opening_cohort_churn_any_pct"] for row in monthly if row["opening_cohort_churn_any_pct"] is not None), october["opening_cohort_churn_any_pct"])
        self.assertEqual((december["gross_plan_relation_loss_events"], december["opening_relations_lost_any_time"], december["opening_plan_relations"]), (11, 5, 1279))
        self.assertAlmostEqual(december["opening_cohort_churn_any_pct"], .39, places=2)
        self.assertEqual(max(row["gross_plan_relation_loss_events"] for row in monthly), december["gross_plan_relation_loss_events"])

    def test_2024_opening_cohort_and_plan_segments(self):
        row = next(r for r in LEDGER["periods"]["ANNUAL"] if r["period"] == "2024")
        self.assertEqual((row["opening_customers"], row["opening_plan_relations"]), (190, 374))
        self.assertEqual((row["opening_relations_lost_any_time"], row["opening_relations_lost_at_close"]), (7, 3))
        self.assertEqual((row["opening_customers_lost_at_close"], row["opening_customers_lost_any_time"]), (0, 0))
        expected = {"Enterprise": (120, 5), "Basic": (132, 2), "Pro": (122, 0)}
        actual = {r["plan_tier"]: (r["opening_relations"], r["opening_relations_lost_any_time"]) for r in row["plan_segments"]}
        self.assertEqual(actual, expected)

    def test_usage_support_and_event_reason_claims(self):
        usage = {r["year"]: r for r in BUSINESS["usage"]["yearly_source_trend"]}
        self.assertEqual(usage[2023]["recorded_usage_count"], 124561)
        self.assertEqual(usage[2024]["recorded_usage_count"], 125964)
        self.assertEqual(BUSINESS["usage"]["concentration"]["valid_interval_usage_rows"], 5568)
        counts = {}
        with (DATA / "ravenstack_churn_events.csv").open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                counts[row["reason_code"]] = counts.get(row["reason_code"], 0) + 1
        self.assertEqual(counts, {"features": 114, "support": 104, "budget": 104, "unknown": 95, "competitor": 92, "pricing": 91})
        support = {r["group"]: r for r in BUSINESS["support"]["by_label"] if r["label"] == "any_event"}
        self.assertEqual(support["positive"]["satisfaction_scored_tickets"], 815)
        self.assertEqual(support["negative"]["satisfaction_scored_tickets"], 360)

    def test_scenario_arithmetic_includes_downside(self):
        scenarios = [(60, .4, .02, 100, 3), (60, .6, .05, 200, 6), (60, .8, .10, 400, 9)]
        results = []
        for eligible, uptake, lift, monthly, months in scenarios:
            retained = eligible * uptake * lift
            cost = eligible * 20
            gross = retained * monthly * months
            results.append((retained, gross, gross - cost, cost / (retained * months)))
        expected = [(.48, 144.0, -1056.0, 833.3333333333334), (1.8, 2160.0, 960.0, 111.11111111111111), (4.8, 17280.0, 16080.0, 27.77777777777778)]
        for actual_row, expected_row in zip(results, expected):
            for actual, expected_value in zip(actual_row, expected_row):
                self.assertAlmostEqual(actual, expected_value, places=9)
        self.assertLess(results[0][2], 0)

    def test_pdf_pages_text_and_hash_manifest(self):
        info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True, check=True).stdout
        self.assertIn("Pages:           7", info)
        text = subprocess.run(["pdftotext", str(PDF), "-"], capture_output=True, text=True, check=True).stdout
        normalized_text = " ".join(text.split())
        for phrase in (
            "Q1 / WHY?", "Q2 / WHO?", "Q3 / WHAT NEXT?", "UNDEFINED, not 0%",
            "OCT '24", "9 opening-cohort losses / 1,073 = 0.84% rate peak", "DEC '24", "11 gross events",
            "5/1,279 opening cohort = 0.39%", "historical investigation cases, not a verified current eligible retention population",
            "-$1,056", "$16,080", "UNKNOWN",
        ):
            self.assertIn(phrase, normalized_text)
        markdown = " ".join(MD.read_text(encoding="utf-8").split())
        for phrase in (
            "62 account–plan-tier coverage losses", "54 cases (87.1%)", "feature/value fit (114/600 event rows; 19.0%)",
            "October 2024 had the period's highest opening-cohort plan-loss rate: 9/1,073 = **0.84%**",
            "December 2024 had the highest absolute count, **11 gross plan-loss events**",
            "The 60 accounts are historical investigation cases, not a verified current eligible retention population.",
        ):
            self.assertIn(phrase, markdown)
        manifest = json.loads((HERE / "EVIDENCE-MANIFEST.json").read_text())
        self.assertEqual(manifest["paper"]["pdf_sha256"], digest(PDF))
        self.assertEqual(manifest["paper"]["markdown_sha256"], digest(MD))
        self.assertEqual(manifest["paper"]["pdf_pages"], 7)
        self.assertTrue((HERE / "PAPER-NUMERICAL-EVIDENCE-MANIFEST.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
