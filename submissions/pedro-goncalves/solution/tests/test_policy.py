import unittest
import sqlite3
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from src.support_copilot.audit import build_record
from src.support_copilot.batch import (
    CUSTOMER_SUPPORT,
    IT_SUPPORT,
    analyze_queue,
)
from src.support_copilot.customer_care import assess_customer_care
from src.support_copilot.inference import TicketClassifier
from src.support_copilot.memory import (
    find_approved_lessons,
    list_lessons,
    record_feedback,
    set_lesson_status,
)
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
    def test_customer_csv_uses_explicit_context_not_column_name(self):
        class ClassifierThatMustNotRun:
            def predict_many(self, texts):
                raise AssertionError(
                    "O modelo de TI não pode ler a fila de clientes."
                )

        frame = pd.DataFrame(
            {
                "case_reference": ["C-1", "C-2"],
                "body_text": [
                    "Já entrei em contato várias vezes e continuo sem solução.",
                    "Gostaria de configurar meu equipamento.",
                ],
                "Ticket Type": ["Billing inquiry", "Technical issue"],
            }
        )
        results = analyze_queue(
            frame,
            text_column="body_text",
            id_column="case_reference",
            context=CUSTOMER_SUPPORT,
            classifier=ClassifierThatMustNotRun(),
            threshold=0.75,
            kill_switch=False,
            limit=10,
        )
        self.assertEqual(
            [result["row_id"] for result in results],
            ["C-1", "C-2"],
        )
        self.assertTrue(results[0]["customer_care"]["requires_human"])
        self.assertIsNone(results[0]["prediction"]["category"])
        self.assertNotIn("continuo sem solução", json.dumps(results))

    def test_it_csv_uses_classifier_with_arbitrary_column_names(self):
        class StubClassifier:
            def __init__(self):
                self.calls = 0

            def predict_many(self, texts):
                self.calls += 1
                return [
                    {
                        "category": "Hardware",
                        "confidence": 0.95,
                        "top_predictions": [],
                    }
                    for _ in texts
                ]

        classifier = StubClassifier()
        frame = pd.DataFrame(
            {
                "reference": ["IT-1"],
                "customer_words": ["The company laptop is broken."],
            }
        )
        results = analyze_queue(
            frame,
            text_column="customer_words",
            id_column="reference",
            context=IT_SUPPORT,
            classifier=classifier,
            threshold=0.75,
            kill_switch=False,
            limit=10,
        )
        self.assertEqual(classifier.calls, 1)
        self.assertEqual(results[0]["prediction"]["category"], "Hardware")
        self.assertEqual(
            results[0]["decision"]["action"],
            "SHADOW_RECOMMENDATION",
        )
        self.assertNotIn("company laptop", json.dumps(results))

    def test_cross_dataset_audit_is_complete_and_explicitly_exploratory(self):
        audit = json.loads(
            Path("artifacts/cross_dataset_audit.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(audit["dataset_1_rows_scored"], 8469)
        self.assertGreater(audit["largest_category_share"], 0.80)
        self.assertIn("accuracy is unknown", audit["interpretation"])

    def test_data_audit_preserves_repeated_unresolved_customer_signal(self):
        audit = json.loads(
            Path("artifacts/data_audit.json").read_text(encoding="utf-8")
        )["dataset_1"]
        self.assertEqual(audit["repeated_unresolved_rows"], 460)
        self.assertEqual(
            audit["repeated_unresolved_by_status"],
            {
                "Pending Customer Response": 156,
                "Closed": 152,
                "Open": 152,
            },
        )

    def test_batch_prediction_matches_individual_prediction(self):
        classifier = TicketClassifier(
            Path("artifacts/models/ticket_classifier.joblib")
        )
        texts = [
            "Please replace the broken laptop.",
            "Please grant access to the payroll folder.",
        ]
        batch = classifier.predict_many(texts)
        individual = [classifier.predict(text) for text in texts]
        self.assertEqual(batch, individual)

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

    def test_customer_care_precedes_high_confidence_automation(self):
        result = decide(
            category="Hardware",
            confidence=0.99,
            threshold=0.80,
            mode=OperatingMode.SIMULATED_AUTOMATION,
            kill_switch=False,
            customer_care_required=True,
        )
        self.assertEqual(result.action, "HUMAN_REVIEW")
        self.assertIn("cliente", result.reason)

    def test_customer_care_detects_unresolved_financial_complaint(self):
        assessment = assess_customer_care(
            "Estou há dias sem solução e fui cobrado duas vezes."
        )
        self.assertTrue(assessment.requires_human)
        self.assertEqual(assessment.level, "critical")
        self.assertIn("UNRESOLVED_OR_REPEAT_CONTACT", assessment.signal_codes)
        self.assertIn("FINANCIAL_HARM", assessment.signal_codes)

    def test_customer_care_does_not_escalate_standard_request(self):
        assessment = assess_customer_care(
            "Gostaria de saber como configurar meu equipamento."
        )
        self.assertFalse(assessment.requires_human)
        self.assertEqual(assessment.signal_codes, ())

    def test_approved_memory_match_forces_human_review(self):
        result = decide(
            category="Hardware",
            confidence=0.99,
            threshold=0.80,
            mode=OperatingMode.SIMULATED_AUTOMATION,
            kill_switch=False,
            memory_match=True,
        )
        self.assertEqual(result.action, "HUMAN_REVIEW")
        self.assertIn("memória", result.reason)

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
            customer_care={
                "level": "critical",
                "requires_human": True,
                "signal_codes": ["FINANCIAL_HARM"],
            },
        )
        self.assertFalse(record["raw_text_stored"])
        self.assertFalse(record["text_fingerprint_stored"])
        self.assertNotIn("input_sha256", record)
        self.assertEqual(record["versions"]["model_sha256"], "a" * 64)
        self.assertTrue(record["patterns_masked"])
        self.assertTrue(record["customer_care"]["requires_human"])

    def test_memory_uses_only_approved_lessons(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "learning.sqlite3"
            feedback = record_feedback(
                database,
                decision_id="decision-1",
                predicted_category="Hardware",
                corrected_category="Access",
                confidence=0.91,
                model_version="model-1",
                policy_version=POLICY_VERSION,
                created_by="operador-1",
                trigger_terms=["administrative", "access"],
            )
            self.assertEqual(
                find_approved_lessons(
                    database,
                    text="Please grant administrative access.",
                    predicted_category="Hardware",
                ),
                [],
            )

            set_lesson_status(
                database,
                lesson_id=feedback["lesson_id"],
                status="approved",
                actor_id="revisor-1",
                reason="Regra conferida.",
            )
            matches = find_approved_lessons(
                database,
                text="Please grant administrative access.",
                predicted_category="Hardware",
            )
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["recommended_category"], "Access")

    def test_memory_consolidates_repeated_evidence(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "learning.sqlite3"
            shared = {
                "predicted_category": "Hardware",
                "corrected_category": "Access",
                "confidence": 0.91,
                "model_version": "model-1",
                "policy_version": POLICY_VERSION,
                "created_by": "operador-1",
                "trigger_terms": ["administrative", "access"],
            }
            first = record_feedback(database, decision_id="decision-1", **shared)
            second = record_feedback(database, decision_id="decision-2", **shared)
            lessons = list_lessons(database)
            self.assertEqual(first["lesson_id"], second["lesson_id"])
            self.assertEqual(len(lessons), 1)
            self.assertEqual(lessons[0]["evidence_count"], 2)

    def test_memory_rejects_sensitive_content(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "learning.sqlite3"
            with self.assertRaises(ValueError):
                record_feedback(
                    database,
                    decision_id="decision-1",
                    predicted_category="Hardware",
                    corrected_category="Access",
                    confidence=0.91,
                    model_version="model-1",
                    policy_version=POLICY_VERSION,
                    created_by="operador-1",
                    trigger_terms=["ana@example.com"],
                )

    def test_lesson_author_cannot_approve_own_lesson(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "learning.sqlite3"
            feedback = record_feedback(
                database,
                decision_id="decision-1",
                predicted_category="Hardware",
                corrected_category="Access",
                confidence=0.91,
                model_version="model-1",
                policy_version=POLICY_VERSION,
                created_by="operador-1",
                trigger_terms=["administrative", "access"],
            )
            with self.assertRaises(PermissionError):
                set_lesson_status(
                    database,
                    lesson_id=feedback["lesson_id"],
                    status="approved",
                    actor_id="operador-1",
                    reason="Tentativa de autoaprovação.",
                )

    def test_feedback_events_are_append_only(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "learning.sqlite3"
            record_feedback(
                database,
                decision_id="decision-1",
                predicted_category="Hardware",
                corrected_category="Hardware",
                confidence=0.91,
                model_version="model-1",
                policy_version=POLICY_VERSION,
                created_by="operador-1",
            )
            with sqlite3.connect(database) as connection:
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "UPDATE feedback_events SET confidence = 0.1"
                    )

    def test_memory_requires_all_trigger_terms(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "learning.sqlite3"
            feedback = record_feedback(
                database,
                decision_id="decision-1",
                predicted_category="Hardware",
                corrected_category="Access",
                confidence=0.91,
                model_version="model-1",
                policy_version=POLICY_VERSION,
                created_by="operador-1",
                trigger_terms=["administrative", "access"],
            )
            set_lesson_status(
                database,
                lesson_id=feedback["lesson_id"],
                status="approved",
                actor_id="revisor-1",
                reason="Regra conferida.",
            )
            self.assertEqual(
                find_approved_lessons(
                    database,
                    text="Administrative request without the second term.",
                    predicted_category="Hardware",
                ),
                [],
            )

    def test_memory_blocks_conflicting_approved_lessons(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "learning.sqlite3"
            first = record_feedback(
                database,
                decision_id="decision-1",
                predicted_category="Hardware",
                corrected_category="Access",
                confidence=0.91,
                model_version="model-1",
                policy_version=POLICY_VERSION,
                created_by="operador-1",
                trigger_terms=["administrative", "access"],
            )
            second = record_feedback(
                database,
                decision_id="decision-2",
                predicted_category="Hardware",
                corrected_category="Administrative rights",
                confidence=0.89,
                model_version="model-1",
                policy_version=POLICY_VERSION,
                created_by="operador-2",
                trigger_terms=["administrative", "access"],
            )
            set_lesson_status(
                database,
                lesson_id=first["lesson_id"],
                status="approved",
                actor_id="revisor-1",
                reason="Regra conferida.",
            )
            with self.assertRaises(ValueError):
                set_lesson_status(
                    database,
                    lesson_id=second["lesson_id"],
                    status="approved",
                    actor_id="revisor-2",
                    reason="Regra conflitante.",
                )
            approved = next(
                lesson
                for lesson in list_lessons(database)
                if lesson["lesson_id"] == first["lesson_id"]
            )
            self.assertEqual(approved["approved_by"], "revisor-1")
            self.assertIsNotNone(approved["approved_at"])


if __name__ == "__main__":
    unittest.main()
