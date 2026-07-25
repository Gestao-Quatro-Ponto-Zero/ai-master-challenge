import unittest
import sqlite3
import json
from io import BytesIO
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
from src.support_copilot.demo_matrix import CASE_MATRIX, evaluate_matrix
from src.support_copilot.inference import TicketClassifier
from src.support_copilot.memory import (
    find_approved_lessons,
    list_lessons,
    list_operational_lessons,
    record_feedback,
    seed_case_memory,
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
from src.support_copilot.operational_metrics import (
    EfficiencyScenario,
    calculate_efficiency,
)
from src.support_copilot.universal_analysis import (
    apply_schema,
    compare_summaries,
    profile_dataframe,
    read_spreadsheet,
    summarize_table,
    validate_schema,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_ROOT = (
    PROJECT_ROOT if (PROJECT_ROOT / "docs").exists() else PROJECT_ROOT.parent
)


class PolicyTests(unittest.TestCase):
    def test_pareto_opinion_matches_audited_artifacts(self):
        audit = json.loads(
            Path("artifacts/data_audit.json").read_text(encoding="utf-8")
        )
        metrics = json.loads(
            Path("artifacts/classifier_metrics.json").read_text(encoding="utf-8")
        )
        opinion = (SUBMISSION_ROOT / "docs/gate-3/parecer-80-20.md").read_text(
            encoding="utf-8"
        )
        d1 = audit["dataset_1"]
        final_test = metrics["threshold_selection"]["final_test"]
        final_rows = metrics["data"]["final_test_rows"]
        correct_covered = (
            final_test["covered_tickets"] - final_test["errors_when_covered"]
        )

        expected = (
            f"{d1['repeated_unresolved_rows']} casos, "
            f"{d1['repeated_unresolved_rows'] / d1['rows']:.2%}".replace(".", ","),
            (
                f"{d1['negative_response_to_resolution_rows']:,} resoluções "
                f"anteriores à primeira resposta ÷ "
                f"{d1['paired_timestamp_rows']:,} pares"
            ).replace(",", "."),
            (
                f"{final_test['covered_tickets']:,} mensagens acima do limite "
                f"de 75% ÷ {final_rows:,} mensagens"
            ).replace(",", "."),
            (
                f"{correct_covered:,} previsões corretas ÷ "
                f"{final_test['covered_tickets']:,} previsões cobertas"
            ).replace(",", "."),
        )
        for proof in expected:
            with self.subTest(proof=proof):
                self.assertIn(proof, opinion)

    def test_efficiency_scenario_exposes_every_component(self):
        result = calculate_efficiency(
            EfficiencyScenario(
                volume=1_000,
                eligible_share=0.20,
                adoption=0.50,
                manual_minutes=10,
                assisted_minutes=3,
                safe_success_rate=0.90,
            )
        )
        self.assertAlmostEqual(result.adopted_cases, 100)
        self.assertAlmostEqual(result.manual_hours, 1000 / 60)
        self.assertAlmostEqual(result.assisted_hours, 300 / 60)
        self.assertAlmostEqual(result.rework_hours, 100 / 60)
        self.assertAlmostEqual(result.net_hours_released, 10)
        self.assertAlmostEqual(result.time_reduction_rate, 0.60)

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

    def test_data_audit_does_not_delete_distinct_repeated_events(self):
        audit = json.loads(
            Path("artifacts/data_audit.json").read_text(encoding="utf-8")
        )["dataset_1"]
        self.assertEqual(audit["exact_duplicate_rows"], 0)
        self.assertEqual(audit["duplicate_ticket_id_rows"], 0)
        self.assertGreater(
            audit["description_normalized_rows_in_duplicate_groups"],
            0,
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

    def test_case_memory_is_seeded_once_with_reviewed_evidence(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "learning.sqlite3"
            for _ in range(2):
                seed_case_memory(
                    database,
                    model_version="model-test",
                    policy_version=POLICY_VERSION,
                )

            operational = list_operational_lessons(database)
            classifier_lessons = [
                lesson
                for lesson in list_lessons(database)
                if lesson["status"] == "approved"
            ]
            self.assertEqual(len(operational), 6)
            self.assertEqual(len(classifier_lessons), 1)
            self.assertTrue(
                all(
                    lesson["approved_by"] == "revisao-independente"
                    for lesson in operational
                )
            )
            self.assertEqual(
                classifier_lessons[0]["recommended_category"],
                "Purchase",
            )

    def test_case_matrix_passes_all_sixteen_scenarios(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "learning.sqlite3"
            classifier = TicketClassifier(
                Path("artifacts/models/ticket_classifier.joblib")
            )
            seed_case_memory(
                database,
                model_version=classifier.model_sha256,
                policy_version=POLICY_VERSION,
            )
            results = evaluate_matrix(
                classifier=classifier,
                threshold=0.75,
                memory_path=database,
            )
            self.assertEqual(len(results), 16)
            self.assertEqual(results["Resultado"].value_counts().to_dict(), {"PASS": 16})

    def test_case_matrix_preserves_repeated_text_as_distinct_events(self):
        repeated = [
            case
            for case in CASE_MATRIX
            if case["case_id"] in {"CLI-07A", "CLI-07B"}
        ]
        self.assertEqual(len(repeated), 2)
        self.assertEqual(repeated[0]["message"], repeated[1]["message"])
        self.assertNotEqual(repeated[0]["case_id"], repeated[1]["case_id"])

    def test_universal_schema_requires_human_validated_order(self):
        frame = pd.DataFrame(
            {
                "Ticket ID": [1, 2],
                "Description": ["A", "B"],
                "Status": ["Open", "Closed"],
            }
        )
        schema = profile_dataframe(frame)
        schema.loc[schema["Coluna"].eq("Status"), "Usar"] = False
        schema.loc[schema["Coluna"].eq("Description"), "Ordem"] = 1
        schema.loc[schema["Coluna"].eq("Ticket ID"), "Ordem"] = 2
        prepared = apply_schema(frame, schema)
        self.assertEqual(prepared.columns.tolist(), ["Description", "Ticket ID"])

    def test_universal_schema_rejects_ambiguous_order(self):
        frame = pd.DataFrame({"id": [1], "text": ["A"]})
        schema = profile_dataframe(frame)
        schema["Ordem"] = 1
        with self.assertRaises(ValueError):
            validate_schema(schema, list(frame.columns))

    def test_universal_summary_preserves_repeated_events(self):
        frame = pd.DataFrame(
            {
                "Ticket ID": [1, 2],
                "Description": ["Mesmo problema", "Mesmo problema"],
                "Status": ["Open", "Open"],
            }
        )
        schema = profile_dataframe(frame)
        summary = summarize_table(frame, schema, name="Fila")
        self.assertEqual(summary.exact_duplicate_rows, 0)
        self.assertEqual(summary.duplicate_identifier_rows, 0)
        self.assertEqual(summary.rows, 2)
        comparison = compare_summaries(summary, summary)
        self.assertEqual(len(comparison), 2)

    def test_universal_reader_accepts_csv_and_xlsx(self):
        csv_frame = read_spreadsheet(
            BytesIO(b"id,status\n1,Open\n"),
            filename="fila.csv",
        )
        self.assertEqual(csv_frame.to_dict("records"), [{"id": 1, "status": "Open"}])

        xlsx_buffer = BytesIO()
        pd.DataFrame({"id": [2], "status": ["Closed"]}).to_excel(
            xlsx_buffer,
            index=False,
        )
        xlsx_frame = read_spreadsheet(
            xlsx_buffer,
            filename="fila.xlsx",
        )
        self.assertEqual(
            xlsx_frame.to_dict("records"),
            [{"id": 2, "status": "Closed"}],
        )

    def test_case_demo_samples_are_bounded_and_remove_direct_identifiers(self):
        support = pd.read_csv(
            PROJECT_ROOT / "artifacts/demo/customer_support_case_sample.csv"
        )
        it_service = pd.read_csv(
            PROJECT_ROOT / "artifacts/demo/it_service_case_sample.csv"
        )
        self.assertEqual(len(support), 5000)
        self.assertEqual(len(it_service), 5000)
        self.assertTrue(
            {
                "Ticket ID",
                "Customer Name",
                "Customer Email",
                "Customer Age",
                "Customer Gender",
            }.isdisjoint(support.columns)
        )
        self.assertEqual(support.iloc[0]["Date of Purchase"], "2021-03-22")
        self.assertIn("Ticket Description", support.columns)
        self.assertEqual(list(it_service.columns), ["Document", "Topic_group"])


if __name__ == "__main__":
    unittest.main()
