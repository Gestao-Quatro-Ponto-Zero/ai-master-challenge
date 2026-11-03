"""Management boundaries, simulator behavior and filtered operational exports."""

import csv
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solution"))
from management import EXPORT_FIELDS, business_actions, csv_bytes, load_reports, operational_export
from triage.repository import Repository
from triage.runtime import TriageService


class ManagementTests(unittest.TestCase):
    def test_reports_need_only_three_public_aggregates(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root / "data").mkdir()
            for name in ["diagnosis.json", "final-evaluation.json", "diagnosis-assumptions.json"]:
                shutil.copy(ROOT / "data" / name, root / "data" / name)
            diagnosis,evaluation,_=load_reports(root)
            self.assertEqual(diagnosis["overall"]["tickets"],8469)
            self.assertEqual(evaluation["population"],7175)
            self.assertEqual(len(business_actions(diagnosis,evaluation)),5)
            self.assertFalse((root/"data/models").exists())

    def test_export_reconciles_filter_and_preserves_latest_review_and_event_history(self):
        with tempfile.TemporaryDirectory() as d:
            repo=Repository(Path(d)/"state.sqlite3")
            service=TriageService(repo)
            first=service.submit("A private customer text", "unknown", "case-a")
            service.submit("Another private text", "unknown", "case-b")
            repo.review(first["run_id"],"accepted","Private name","Private reason",reviewer_type="automated_test",event_id="event-1")
            repo.review(first["run_id"],"deferred","Private name","Private reason",reviewer_type="automated_test",event_id="event-2")
            repo.review(first["run_id"],"confirmed_valid","Private name","Private reason",metric="model_score",reviewer_type="automated_test",event_id="event-3")
            rows=[r for r in repo.filter_metrics(metric="model_score") if r["run_id"]==first["run_id"]]
            exported=operational_export(repo,rows,exported_at="fixture-time")
            self.assertEqual({k:len(v) for k,v in exported.items()},{"cases":1,"metrics":1,"reviews":3})
            self.assertEqual(exported["cases"][0]["case_review_state"],"deferred")
            self.assertEqual(exported["cases"][0]["case_reviewer_type"],"automated_test")
            self.assertEqual(exported["metrics"][0]["review_state"],"confirmed_valid")
            for kind, records in exported.items():
                content=csv_bytes(kind,records).decode("utf-8-sig")
                parsed=list(csv.DictReader(io.StringIO(content)))
                self.assertEqual(len(parsed),len(records))
                self.assertEqual(list(csv.DictReader(io.StringIO(content)).fieldnames),list(EXPORT_FIELDS[kind]))
                self.assertNotIn("Private",content)
                self.assertNotIn("private",content)
                self.assertTrue(all(r["run_id"]==first["run_id"] for r in parsed))
            both=[r for r in repo.filter_metrics() if r["run_id"]==first["run_id"]]
            self.assertEqual(len(operational_export(repo,both)["cases"]),1)
            self.assertEqual(len(repo.get_run(first["run_id"])["reviews"]),3)

    def test_empty_export_has_schema_and_formula_cells_are_text(self):
        self.assertEqual(len(list(csv.DictReader(io.StringIO(csv_bytes("reviews",[]).decode("utf-8-sig"))))),0)
        value=csv_bytes("reviews",[{"event_id":" =HYPERLINK(unsafe)"}]).decode("utf-8-sig")
        self.assertEqual(list(csv.DictReader(io.StringIO(value)))[0]["event_id"],"' =HYPERLINK(unsafe)")


class ManagementUITests(unittest.TestCase):
    def test_company_view_skips_model_and_database_and_switching_reveals_instructor(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {"TRIAGE_DB_PATH": str(Path(d) / "must-not-open.sqlite3")}):
            db = Path(d) / "must-not-open.sqlite3"
            with patch("triage.artifacts.load_metadata", side_effect=AssertionError("Company must not load model")):
                app = AppTest.from_file(str(ROOT / "solution/app.py"), default_timeout=15).run()
                self.assertFalse(app.exception)
                self.assertEqual([tab.label for tab in app.tabs], ["Resultados do suporte", "Capacidade"])
                self.assertFalse(db.exists())
                self.assertFalse(app.text_area)
                self.assertFalse(any("Macro F1" in m.label for m in app.metric))
                self.assertFalse(any("CodeTour" in m.value for m in app.markdown))
            app.selectbox(key="audience").select("instructor").run()
            self.assertFalse(app.exception)
            self.assertIn("Guia do instrutor", [tab.label for tab in app.tabs])
            self.assertTrue(any("review.sh" in code.value for code in app.code))
            self.assertTrue(any("Carregar exemplo" == b.label for b in app.button))
            app.selectbox(key="audience").select("company").run()
            self.assertFalse(app.exception)
            self.assertEqual([tab.label for tab in app.tabs], ["Resultados do suporte", "Capacidade"])
            self.assertFalse(app.text_area)

    def test_consultation_switch_changes_content_without_runtime_database(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {"TRIAGE_DB_PATH": str(Path(d) / "unused.sqlite3")}):
            app = AppTest.from_file(str(ROOT / "solution/overview_app.py"), default_timeout=15).run()
            self.assertFalse(app.exception)
            self.assertEqual([tab.label for tab in app.tabs], ["Resultados do suporte", "Capacidade"])
            app.selectbox(key="audience").select("instructor").run()
            self.assertFalse(app.exception)
            self.assertEqual([tab.label for tab in app.tabs], ["Guia do instrutor", "Diagnóstico e resultados", "Capacidade", "Evoluções planejadas"])
            self.assertTrue(any(m.label == "Casos avaliados" for m in app.metric))
            self.assertFalse(list(Path(d).iterdir()))

    def test_overview_and_simulator_work_without_raw_model_or_runtime(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"data").mkdir()
            for name in ["diagnosis.json","final-evaluation.json","diagnosis-assumptions.json"]:
                shutil.copy(ROOT/"data"/name,root/"data"/name)
            source=f"from pathlib import Path\nfrom management_ui import render_overview, render_capacity, render_future\nrender_overview(Path({str(root)!r}))\nrender_capacity(Path({str(root)!r}))\nrender_future()\n"
            app=AppTest.from_string(source,default_timeout=15).run()
            self.assertFalse(app.exception)
            metric=lambda label: next(m.value for m in app.metric if m.label==label)
            self.assertEqual(metric("Capacidade líquida (h/mês)"),"29,75")
            self.assertEqual(metric("Casos avaliados"),"7.175")
            app.selectbox(key="capacity_scenario_choice").set_value(json.loads((root/"data/diagnosis-assumptions.json").read_text())["scenarios"][0]).run()
            self.assertFalse(app.exception)
            self.assertEqual(metric("Capacidade líquida (h/mês)"),"-26,67")
            app.number_input(key="capacity_downside_tickets").set_value(0.0)
            app.button(key="FormSubmitter:capacity_form-Calcular cenário").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(metric("Capacidade líquida (h/mês)"),"-10,00")
            self.assertTrue(any("indefinido" in m.value for m in app.markdown))
            self.assertEqual(sorted(p.name for p in (root/"data").iterdir()),["diagnosis-assumptions.json","diagnosis.json","final-evaluation.json"])

    def test_overview_launcher_cannot_prepare_data_or_train(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            shutil.copy(ROOT/"run.sh",root/"run.sh")
            (root/".venv/bin").mkdir(parents=True)
            python=root/".venv/bin/python"
            python.write_text('#!/bin/bash\ncase "$*" in\n *setup_triage*) exit 99 ;;\n *streamlit*) printf "%s\\n" "$*" >"launcher.txt" ;;\nesac\n')
            python.chmod(0o700)
            result=subprocess.run(["bash",str(root/"run.sh"),"--overview"],capture_output=True,text=True,cwd=root)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn("solution/overview_app.py",(root/"launcher.txt").read_text())
            self.assertFalse((root/"data").exists())


if __name__ == "__main__":
    unittest.main()
