import unittest

from streamlit.testing.v1 import AppTest


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file("app.py", default_timeout=30)
        self.app.run()
        self.assertFalse(self.app.exception)

    def test_daily_use_tabs_and_safe_default(self):
        self.assertFalse(self.app.toggle[0].value)
        self.assertEqual(
            [tab.label for tab in self.app.tabs],
            ["Triagem", "Aprendizado", "Ajuda"],
        )
        self.assertTrue(
            any(
                expander.label == "Analisar uma fila em CSV"
                for expander in self.app.expander
            )
        )
        self.assertEqual(len(self.app.file_uploader), 1)

    def test_demo_request_can_be_loaded(self):
        demo = next(
            item for item in self.app.selectbox if item.label == "Exemplo"
        )
        demo.select("Acesso sensível").run()
        self.assertIn("administrative access", self.app.text_area[0].value.lower())

    def test_ticket_analysis_runs_without_exception(self):
        self.app.radio[0].set_value("Suporte interno de TI")
        self.app.text_area[0].input(
            "Please replace the broken laptop assigned to my team."
        )
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        metric_values = [metric.value for metric in self.app.metric]
        self.assertIn("Sugestão registrada para comparação", metric_values)

    def test_kill_switch_forces_human_review(self):
        self.app.toggle[0].set_value(True)
        self.app.text_area[0].input(
            "Please grant administrative access to the shared server."
        )
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        metric_values = [metric.value for metric in self.app.metric]
        self.assertIn("Encaminhar para uma pessoa", metric_values)

    def test_sensitive_category_is_human_in_shadow(self):
        self.app.radio[0].set_value("Suporte interno de TI")
        self.app.text_area[0].input(
            "Please reset access permissions for the payroll account."
        )
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        metric_values = [metric.value for metric in self.app.metric]
        self.assertIn("Encaminhar para uma pessoa", metric_values)

    def test_customer_complaint_forces_human_care(self):
        self.app.text_area[0].input(
            "Estou há dias sem solução, fui cobrado duas vezes e ninguém responde."
        )
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        metric_values = [metric.value for metric in self.app.metric]
        self.assertIn("Encaminhar para uma pessoa", metric_values)
        self.assertIn("Atendimento ao cliente", metric_values)
        self.assertNotIn("Equipamento", metric_values)
        self.assertTrue(
            any(
                "Cuidado prioritário com o cliente" in error.value
                for error in self.app.error
            )
        )


if __name__ == "__main__":
    unittest.main()
