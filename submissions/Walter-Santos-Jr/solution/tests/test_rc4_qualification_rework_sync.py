import tempfile
import unittest
from pathlib import Path
import app

class QualificationReworkSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old=app.DB_PATH
        app.DB_PATH=Path(self.tmp.name)/"isolated.sqlite3"
        app.init_db()
        self.key=next(k for k,r in app.INDEX.items() if app.quality_gate(r)["eligible"] and r["deal_stage"] in ("Prospecting","Engaging"))
    def tearDown(self):
        app.DB_PATH=self.old
        self.tmp.cleanup()
    def test_open_job_auto_verifies_on_complete_qualification(self):
        app.save_qualification(self.key,{"decision_maker":"unknown","timeline":"unknown","budget":"unknown","notes":""})
        job=next(j for j in app.jobs_for(self.key) if j["job_type"]=="QUALIFY_OPPORTUNITY")
        self.assertEqual(job["status"],"OPEN")
        app.save_qualification(self.key,{"decision_maker":"yes","timeline":"yes","budget":"yes","notes":"deal ok"})
        self.assertFalse(any(j["id"]==job["id"] for j in app.jobs_for(self.key)))
        verified=next(j for j in app.jobs_for(self.key,include_history=True) if j["id"]==job["id"])
        self.assertEqual(verified["status"],"VERIFIED")
        self.assertTrue(any(e["event_type"]=="VERIFIED" for e in verified["events"]))
    def test_incomplete_qualification_keeps_job_open(self):
        app.save_qualification(self.key,{"decision_maker":"yes","timeline":"unknown","budget":"yes","notes":"em progresso"})
        self.assertTrue(any(j["job_type"]=="QUALIFY_OPPORTUNITY" for j in app.jobs_for(self.key)))
