"""Automated UI fixtures; never counted as human productivity observations."""

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"solution"))
from batch_workflow import WorkflowStore
from triage.repository import Repository
from test_batch_workflow import study_sample, Service


class BatchUITests(unittest.TestCase):
    def test_start_review_real_train_inference_finish_and_reload(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{"TRIAGE_WORKFLOW_DB_PATH":str(Path(d)/"workflow.sqlite3")}):
            app=AppTest.from_string("from batch_ui import render_batch_workspace\nrender_batch_workspace()",default_timeout=20).run()
            self.assertFalse(app.exception)
            self.assertFalse((Path(d)/"workflow.sqlite3").exists())
            app.text_input(key="batch_operator").set_value("automated UI fixture")
            app.selectbox(key="batch_actor").select("automated_test")
            app.checkbox(key="batch_domain").check()
            app.button(key="FormSubmitter:batch_start-Iniciar lote e cronômetro").click().run()
            self.assertFalse(app.exception)
            store=WorkflowStore(Path(d)/"workflow.sqlite3");batch=store.batches()[0];bid=batch["id"]
            self.assertEqual(batch["actor_type"],"automated_test")
            app.run();self.assertEqual(len(store.batches()),1)
            example=json.loads((ROOT/"data/models/it-triage-v1/demo-examples.json").read_text())[0]
            store.attach(bid,[{"ticket_id":example["case_id"],"text":example["text"],"source":example["source"]}])
            app.run()
            app.button(key=f"prepare_{bid}").click().run()
            self.assertFalse(app.exception)
            saved=Repository(store.path).list_runs()
            self.assertEqual(len(saved),1)
            self.assertEqual(saved[0]["source"]["partition"],"train")
            batch=store.batch(bid)
            editor_key=f"batch_editor_{bid}_{batch['revision']}"
            app.session_state[editor_key]={"edited_rows":{0:{"Revisado":True,"Categoria final":"Hardware"}},"added_rows":[],"deleted_rows":[]}
            app.checkbox(key=f"attest_{bid}_{batch['revision']}").check()
            app.button(key=f"FormSubmitter:batch_decisions_{bid}-Registrar linhas revisadas").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(store.decisions(bid),{example["case_id"]:"Hardware"})
            app.checkbox(key=f"final_ack_{bid}_{store.batch(bid)['revision']}").check().run()
            app.button(key=f"finish_{bid}").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(store.batch(bid)["state"],"completed")
            self.assertTrue(any("Arquivo preparado" in x.value for x in app.success))
            before=store.batch(bid)
            app.run()
            self.assertEqual(store.batch(bid),before)
            self.assertEqual(len(Repository(store.path).list_runs()),1)

    def test_study_ui_hides_reference_quality_until_both_stages_and_marks_automation(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{"TRIAGE_WORKFLOW_DB_PATH":str(Path(d)/"workflow.sqlite3")}):
            store=WorkflowStore(Path(d)/"workflow.sqlite3")
            sid=store.create_study("automated UI fixture","automated_test","ui-fixture",sample=study_sample())
            app=AppTest.from_string("from batch_ui import render_experiment\nrender_experiment()",default_timeout=15).run()
            self.assertFalse(app.exception)
            self.assertTrue(any("0 concluídos por operador declarado" in c.value for c in app.caption))
            app.button(key=f"begin_arm_{sid}").click().run()
            self.assertFalse(app.exception)
            first=next(b for b in store.batches() if b["study_id"]==sid)
            if first["mode"]=="assisted":store.prepare(first["id"],Service());app.run()
            self.assertNotIn("reference_category",str([frame.value.columns.tolist() for frame in app.dataframe]))
            self.assertNotIn("reference_concordance",str([frame.value.columns.tolist() for frame in app.dataframe]))
            for i in range(2):
                bid=store.start_arm(sid);batch=store.batch(bid)
                if batch["mode"]=="assisted":store.prepare(bid,Service())
                store.save_decisions(bid,{r["ticket_id"]:r["reference_category"] for r in batch["items"]},f"ui-{i}",store.batch(bid)["revision"])
                store.finish(bid)
            app.run()
            self.assertFalse(app.exception)
            self.assertTrue(any("Resultado de teste automatizado" in w.value for w in app.warning))
            self.assertTrue(any("0 concluídos por operador declarado" in c.value for c in app.caption))
            self.assertTrue(any("1 concluídos como teste automatizado" in c.value for c in app.caption))

    def test_corrupt_workflow_database_is_visible_without_app_exception(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{"TRIAGE_WORKFLOW_DB_PATH":str(Path(d)/"workflow.sqlite3")}):
            (Path(d)/"workflow.sqlite3").write_text("corrupt fixture")
            app=AppTest.from_string("from batch_ui import render_batch_workspace\nrender_batch_workspace()",default_timeout=15).run()
            self.assertFalse(app.exception)
            self.assertTrue(app.error)


if __name__=="__main__":unittest.main()
