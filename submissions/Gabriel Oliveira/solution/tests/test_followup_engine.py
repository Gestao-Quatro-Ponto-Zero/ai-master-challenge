"""Tests da engine de follow-up."""
from __future__ import annotations

import unittest

from followup_engine import generate_followup_package


class FollowupEngineTests(unittest.TestCase):
    def test_three_unique_tones_and_cta_present(self) -> None:
        profile = {
            "lead_id": "OPP_1",
            "lead_name": "account_001",
            "owner": "Ana",
            "product": "GTX Enterprise",
            "deal_stage": "Engaging",
            "disc_profile": "D",
            "disc_rationale": "Lead orientado a resultado.",
        }

        result = generate_followup_package(profile)
        copies = result["copies"]

        self.assertEqual(len(copies), 3)
        tones = {c["tone"] for c in copies}
        self.assertEqual(tones, {"consultivo", "direto", "provocativo elegante"})

        for copy in copies:
            self.assertIn("?", copy["text"], "Copy deve conter CTA explicito")
            self.assertGreaterEqual(len(copy["text"].split()), 60)
            self.assertLessEqual(len(copy["text"].split()), 130)

    def test_fallback_when_lead_fields_missing(self) -> None:
        result = generate_followup_package({"disc_profile": "indefinido"})
        self.assertEqual(len(result["copies"]), 3)
        self.assertIsInstance(result["next_best_action"], str)
        self.assertTrue(result["next_best_action"].strip())


if __name__ == "__main__":
    unittest.main()
