"""Streamlit AppTest flows in a temporary database; no test-set examples."""

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solution"))
from triage.repository import Repository


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Run in the locked .venv for UI tests")
class WorkbenchTests(unittest.TestCase):
    @unittest.skipUnless((ROOT / "data/models/it-triage-v1/bundle.json").exists(), "Train the frozen bundle first")
    def test_train_example_uses_real_worker_and_persists_once(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.sqlite3"
            with patch.dict(os.environ, {"TRIAGE_DB_PATH": str(path), "TRIAGE_WORKFLOW_DB_PATH": str(Path(directory)/"workflow.sqlite3")}):
                app = AppTest.from_file(str(ROOT / "solution/app.py"), default_timeout=15).run()
                app.selectbox(key="audience").select("instructor").run()
                next(item for item in app.button if item.label == "Carregar exemplo").click().run()
                app.button(key="FormSubmitter:triage_form-Analisar e salvar").click().run()
                self.assertFalse(app.exception)
                repo = Repository(path)
                saved = repo.list_runs()
                self.assertEqual(len(saved), 1)
                self.assertEqual(saved[0]["source"]["partition"], "train")
                self.assertIsNotNone(saved[0]["predicted_category"])
                self.assertTrue(saved[0]["persisted"])
                app.run()
                self.assertEqual(len(repo.list_runs()), 1)

    def test_handoff_review_filters_and_rerun_do_not_duplicate_work(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.sqlite3"
            with patch.dict(os.environ, {"TRIAGE_DB_PATH": str(path), "TRIAGE_WORKFLOW_DB_PATH": str(Path(directory)/"workflow.sqlite3")}):
                app = AppTest.from_file(str(ROOT / "solution/app.py"), default_timeout=15).run()
                app.selectbox(key="audience").select("instructor").run()
                self.assertFalse(app.exception)
                app.text_area(key="ticket_text").set_value("Need help with a support request")
                app.button(key="FormSubmitter:triage_form-Analisar e salvar").click().run()
                self.assertFalse(app.exception)
                repo = Repository(path)
                self.assertEqual(len(repo.list_runs()), 1)
                self.assertEqual(repo.list_runs()[0]["reason_codes"], ["unsupported_context"])
                app.run()
                self.assertEqual(len(repo.list_runs()), 1)
                next(item for item in app.text_input if item.label == "Seu nome ou identificação").set_value("automated UI fixture")
                next(item for item in app.text_area if item.label == "Motivo da revisão").set_value("Accept manual handoff in fixture")
                next(item for item in app.selectbox if item.label == "Tipo de revisor").select("automated_test")
                app.button(key="FormSubmitter:review_form-Registrar revisão").click().run()
                self.assertFalse(app.exception)
                detail = repo.get_run(repo.list_runs()[0]["run_id"])
                self.assertEqual(len(detail["reviews"]), 1)
                self.assertEqual(detail["reviews"][0]["decision"], "accepted")
                self.assertEqual(detail["reviews"][0]["reviewer_type"], "automated_test")
                app.selectbox(key="filter_status").select("not_evaluated").run()
                self.assertFalse(app.exception)
                self.assertTrue(any("2 avaliações" in element.value for element in app.caption))
                app.run()
                self.assertEqual(len(repo.get_run(detail["result"]["run_id"])["reviews"]), 1)


if __name__ == "__main__":
    unittest.main()
