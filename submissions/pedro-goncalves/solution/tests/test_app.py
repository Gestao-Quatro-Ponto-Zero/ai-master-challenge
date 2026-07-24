import unittest

from streamlit.testing.v1 import AppTest


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file("app.py", default_timeout=30)
        self.app.run()
        self.assertFalse(self.app.exception)

    def test_default_is_shadow_mode(self):
        self.assertEqual(self.app.selectbox[0].value, "Shadow mode")
        self.assertFalse(self.app.toggle[0].value)

    def test_ticket_analysis_runs_without_exception(self):
        self.app.text_area[0].input(
            "Please replace the broken laptop assigned to my team."
        )
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        metric_values = [metric.value for metric in self.app.metric]
        self.assertIn("SHADOW_RECOMMENDATION", metric_values)

    def test_kill_switch_forces_human_review(self):
        self.app.toggle[0].set_value(True)
        self.app.text_area[0].input(
            "Please grant administrative access to the shared server."
        )
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        metric_values = [metric.value for metric in self.app.metric]
        self.assertIn("HUMAN_REVIEW", metric_values)

    def test_sensitive_category_is_human_in_shadow(self):
        self.app.text_area[0].input(
            "Please reset access permissions for the payroll account."
        )
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        metric_values = [metric.value for metric in self.app.metric]
        self.assertIn("HUMAN_REVIEW", metric_values)


if __name__ == "__main__":
    unittest.main()
