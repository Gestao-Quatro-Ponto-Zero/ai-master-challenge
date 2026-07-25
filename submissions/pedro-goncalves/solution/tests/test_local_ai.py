import unittest

from src.support_copilot.local_ai import LocalAIResult, _normalized_review


class LocalAITests(unittest.TestCase):
    def test_normalizes_granite_aliases_without_accepting_new_claims(self):
        result = LocalAIResult(
            True,
            "ibm/granite4.1:8b",
            {
                "status": "revisao_humana",
                "checkpoints": ["Conferir denominador."],
                "limit": "ROI é cenário, não resultado observado.",
            },
        )
        normalized = _normalized_review(result, kind="opinion")
        self.assertEqual(normalized.payload["status"], "revisao_humana")
        self.assertEqual(
            normalized.payload["checagens"],
            ["Conferir denominador."],
        )
        self.assertIn("cenário", normalized.payload["limite"])

    def test_unknown_status_fails_closed_to_human_review(self):
        result = LocalAIResult(
            True,
            "ibm/granite4.1:8b",
            {"status": "executar_automaticamente"},
        )
        normalized = _normalized_review(result, kind="opinion")
        self.assertEqual(normalized.payload["status"], "revisao_humana")


if __name__ == "__main__":
    unittest.main()
