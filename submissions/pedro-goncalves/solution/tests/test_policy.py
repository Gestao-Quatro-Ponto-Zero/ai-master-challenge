import unittest

from src.support_copilot.audit import build_record
from src.support_copilot.policy import (
    POLICY_VERSION,
    TAXONOMY_VERSION,
    OperatingMode,
    decide,
)
from src.support_copilot.privacy import mask_pii
from src.support_copilot.roi import (
    REFERENCE_SCENARIOS,
    CapacityScenario,
    calculate_capacity,
)


class PolicyTests(unittest.TestCase):
    def test_shadow_mode_always_requires_human(self):
        result = decide(
            category="Hardware",
            confidence=0.99,
            threshold=0.80,
            mode=OperatingMode.SHADOW,
            kill_switch=False,
        )
        self.assertTrue(result.requires_human)
        self.assertEqual(result.action, "SHADOW_RECOMMENDATION")

    def test_kill_switch_overrides_everything(self):
        result = decide(
            category="Hardware",
            confidence=0.99,
            threshold=0.80,
            mode=OperatingMode.SIMULATED_AUTOMATION,
            kill_switch=True,
        )
        self.assertEqual(result.action, "HUMAN_REVIEW")

    def test_sensitive_category_is_human_only(self):
        result = decide(
            category="Administrative rights",
            confidence=0.99,
            threshold=0.80,
            mode=OperatingMode.SIMULATED_AUTOMATION,
            kill_switch=False,
        )
        self.assertTrue(result.requires_human)

    def test_low_confidence_abstains(self):
        result = decide(
            category="Hardware",
            confidence=0.70,
            threshold=0.80,
            mode=OperatingMode.ASSISTED,
            kill_switch=False,
        )
        self.assertEqual(result.action, "ABSTAIN")

    def test_low_confidence_abstains_in_shadow(self):
        result = decide(
            category="Hardware",
            confidence=0.10,
            threshold=0.80,
            mode=OperatingMode.SHADOW,
            kill_switch=False,
        )
        self.assertEqual(result.action, "ABSTAIN")
        self.assertTrue(result.requires_human)

    def test_sensitive_category_precedes_shadow(self):
        result = decide(
            category="Access",
            confidence=0.99,
            threshold=0.80,
            mode=OperatingMode.SHADOW,
            kill_switch=False,
        )
        self.assertEqual(result.action, "HUMAN_REVIEW")
        self.assertTrue(result.requires_human)

    def test_simulated_route_never_claims_real_execution(self):
        result = decide(
            category="Hardware",
            confidence=0.90,
            threshold=0.80,
            mode=OperatingMode.SIMULATED_AUTOMATION,
            kill_switch=False,
        )
        self.assertTrue(result.simulated)
        self.assertFalse(result.requires_human)

    def test_masks_email_and_phone(self):
        masked, counts = mask_pii("Email me at ana@example.com or +55 11 99999-0000.")
        self.assertNotIn("ana@example.com", masked)
        self.assertEqual(counts["EMAIL"], 1)
        self.assertGreaterEqual(counts["PHONE"], 1)

    def test_masks_ip_and_long_identifier(self):
        masked, counts = mask_pii("Host 192.168.1.25, documento 12345678901.")
        self.assertNotIn("192.168.1.25", masked)
        self.assertNotIn("12345678901", masked)
        self.assertEqual(counts["IP"], 1)
        self.assertEqual(counts["LONG_ID"], 1)

    def test_does_not_claim_to_mask_names_or_addresses(self):
        text = "Maria mora na Rua das Flores, bloco A7B9."
        masked, counts = mask_pii(text)
        self.assertEqual(masked, text)
        self.assertFalse(any(counts.values()))

    def test_capacity_scenario_subtracts_review_effort(self):
        result = calculate_capacity(
            CapacityScenario(
                total_tickets=1000,
                eligible_share=0.50,
                adoption=0.50,
                minutes_saved_per_eligible_ticket=6,
                safe_success_rate=1.0,
                review_minutes_per_routed_ticket=2,
                rework_minutes_per_adopted_ticket=1,
            )
        )
        self.assertAlmostEqual(result.gross_hours_released, 25.0)
        self.assertAlmostEqual(result.review_hours_added, 8.3333333333)
        self.assertAlmostEqual(result.rework_hours_added, 4.1666666667)
        self.assertAlmostEqual(result.net_hours_released, 12.5)
        self.assertIsNone(result.net_value)

    def test_reference_scenarios_expose_reproducible_outputs(self):
        expected_hours = {
            "Conservador": 8.25,
            "Base": 187.5,
            "Expansão": 826.0,
        }
        self.assertEqual(len(REFERENCE_SCENARIOS), 3)
        for name, scenario in REFERENCE_SCENARIOS:
            self.assertEqual(scenario.total_tickets, 30_000)
            self.assertGreater(scenario.safe_success_rate, 0)
            self.assertAlmostEqual(
                calculate_capacity(scenario).net_hours_released,
                expected_hours[name],
            )

    def test_audit_record_stores_no_text_fingerprint_and_versions_artifacts(self):
        record = build_record(
            pii_counts={"EMAIL": 1, "IP": 0},
            prediction={"category": "Hardware", "confidence": 0.9},
            decision={"action": "SHADOW_RECOMMENDATION"},
            mode=OperatingMode.SHADOW.value,
            threshold=0.75,
            kill_switch=False,
            model_sha256="a" * 64,
            policy_version=POLICY_VERSION,
            taxonomy_version=TAXONOMY_VERSION,
            app_version="1.1.0",
        )
        self.assertFalse(record["raw_text_stored"])
        self.assertFalse(record["text_fingerprint_stored"])
        self.assertNotIn("input_sha256", record)
        self.assertEqual(record["versions"]["model_sha256"], "a" * 64)
        self.assertTrue(record["patterns_masked"])


if __name__ == "__main__":
    unittest.main()
