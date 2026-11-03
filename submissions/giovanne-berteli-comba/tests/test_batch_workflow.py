"""State, measurement boundaries and idempotency; simulated actors stay tests."""

import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"solution"))
from batch_workflow import WorkflowStore, parse_csv, pilot_sample, digest
from triage.core import CLASSES


class Clock:
    def __init__(self): self.second=0
    def __call__(self): return f"2026-11-03T00:{self.second//60:02}:{self.second%60:02}+00:00"


class Service:
    def __init__(self,failed=False): self.calls=[]; self.failed=failed
    def submit(self,text,context,**kwargs):
        self.calls.append((text,context,kwargs))
        return {"run_id":kwargs["request_id"],"predicted_category":None if self.failed else "Hardware",
                "model_version":"fixture-model","persisted":not self.failed,
                "outcome":"failed" if self.failed else "suggested", "review_queue":"triage_review",
                "reason_codes":["persistence_error"] if self.failed else ["standard_confirmation"]}


def rows():
    return [{"ticket_id":"a","text":"A hardware support request","reference_category":"Hardware"},
            {"ticket_id":"b","text":"Need storage support","reference_category":"Storage"}]


def study_sample():
    return {"source_sha256":"fixture", "membership_sha256":"fixture", "arms":{
        mode:[{"ticket_id":f"{mode}-{i}","text":f"Prepared task {mode} {i}","reference_category":label,
               "source":{"partition":"train","dataset":"fixture","group_id":f"{mode}-group-{i}"}}
              for i,label in enumerate(CLASSES)] for mode in ("manual","assisted")}}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"workflow.sqlite3";self.clock=Clock()
        self.store=WorkflowStore(self.path,clock=self.clock)

    def start(self,mode="assisted",token="one"):
        return self.store.start(mode,"automated fixture","automated_test",token)

    def confirm(self,bid,choices=None,token="confirm"):
        batch=self.store.batch(bid)
        self.store.save_decisions(bid,choices or {r["ticket_id"]:r["reference_category"] or "Hardware" for r in batch["items"]},token,batch["revision"])

    def test_csv_validation_is_bounded_and_rejects_entire_invalid_input(self):
        valid=parse_csv(b'\xef\xbb\xbfticket_id,text,reference_category\na,"a,b",Hardware\n')
        self.assertEqual(valid[0]["text"],"a,b")
        for payload in [b'ticket_id,text\na,one\na,two\n',b'ticket_id,text\na,\n',b'ticket_id,text,other\na,one,x\n',
                        b'ticket_id,ticket_id,text\na,a,one\n',b'ticket_id,text\na,one,extra\n',b'\xff',
                        ('ticket_id,text\n'+''.join(f'{i},text\n' for i in range(51))).encode(),b'x'*2_000_001]:
            with self.subTest(payload=payload[:45]):
                with self.assertRaises(ValueError): parse_csv(payload)

    def test_start_import_prepare_replays_are_idempotent_and_reference_not_inferred(self):
        bid=self.start();self.assertEqual(bid,self.start())
        self.store.attach(bid,rows());self.store.attach(bid,rows())
        with self.assertRaises(ValueError):self.store.attach(bid,[{"ticket_id":"c","text":"replacement"}])
        service=Service();self.store.prepare(bid,service);self.store.prepare(bid,service)
        self.assertEqual(len(service.calls),2)
        self.assertEqual(service.calls[0][0],rows()[0]["text"])
        self.assertNotIn("reference_category",json.dumps(service.calls[0][2]))
        self.assertEqual(len([e for e in self.store.events(bid) if e["kind"]=="suggestion_attempt"]),2)

    def test_manual_has_no_model_step_and_completion_requires_every_explicit_decision(self):
        bid=self.start("manual");self.store.attach(bid,rows())
        with self.assertRaises(ValueError):self.store.prepare(bid,Service())
        with self.assertRaises(ValueError):self.store.finish(bid)
        self.confirm(bid,{"a":"Hardware"},"partial")
        with self.assertRaises(ValueError):self.store.finish(bid)
        self.confirm(bid,{"b":"Storage"},"rest")
        self.clock.second=20;self.store.finish(bid)
        batch=self.store.batch(bid)
        self.assertEqual(batch["elapsed_seconds"],20)
        self.assertTrue(all(r["prediction"] is None for r in batch["items"]))
        self.assertEqual(len(list(csv.DictReader(io.StringIO(batch["artifact"])))),2)
        self.assertNotIn("reference_category",batch["artifact"])
        self.assertNotIn("automated fixture",batch["artifact"])

    def test_stale_decisions_conflicts_and_closed_batch_mutation_are_rejected(self):
        bid=self.start("manual");self.store.attach(bid,rows());rev=self.store.batch(bid)["revision"]
        self.confirm(bid,token="event")
        self.store.save_decisions(bid,{"a":"Hardware","b":"Storage"},"event",rev)
        self.assertEqual(len([e for e in self.store.events(bid) if e["kind"]=="decisions"]),1)
        with self.assertRaises(ValueError):self.store.save_decisions(bid,{"a":"Access"},"event",rev)
        with self.assertRaises(ValueError):self.store.save_decisions(bid,{"a":"Access"},"stale",rev)
        self.clock.second=1;self.store.finish(bid);before=self.store.batch(bid)
        self.clock.second=90;self.store.finish(bid)
        self.assertEqual(before,self.store.batch(bid))
        with self.assertRaises(ValueError):self.confirm(bid,{"a":"Access"},"late")

    def test_failed_suggestions_remain_visible_and_allow_manual_fallback_without_retry(self):
        bid=self.start();self.store.attach(bid,rows());service=Service(failed=True)
        self.store.prepare(bid,service);self.store.prepare(bid,service)
        self.assertEqual(len(service.calls),2)
        self.assertTrue(all(not r["prediction"]["persisted"] for r in self.store.batch(bid)["items"]))
        self.confirm(bid);self.store.finish(bid)
        self.assertEqual(self.store.batch(bid)["state"],"completed")

    def test_interruption_and_clock_rollback_preserve_attempt(self):
        bid=self.start("manual");self.store.attach(bid,rows());self.confirm(bid)
        self.store.batch(bid)
        self.store.abort(bid,"Fixture interruption")
        self.assertEqual(self.store.batch(bid)["state"],"aborted")
        with self.assertRaises(ValueError):self.store.finish(bid)
        self.clock.second=20;other=self.start("manual","clock");self.store.attach(other,rows());self.confirm(other,token="other")
        self.clock.second=10
        with self.assertRaises(ValueError):self.store.finish(other)
        self.assertEqual(self.store.batch(other)["state"],"active")

    def test_study_locks_disjoint_plan_hides_quality_and_retains_negative_difference(self):
        sid=self.store.create_study("Fixture","automated_test","study",sample=study_sample())
        self.assertEqual(sid,self.store.create_study("Fixture","automated_test","study",sample=study_sample()))
        public=self.store.studies()[0]
        self.assertNotIn("arms",public)
        first=self.store.start_arm(sid)
        self.assertEqual(first,self.store.start_arm(sid))
        self.assertFalse(self.store.study_result(sid)["completed"])
        self.assertNotIn("arms",self.store.study_result(sid))
        for position in range(2):
            bid=self.store.start_arm(sid);batch=self.store.batch(bid)
            if batch["mode"]=="assisted":self.store.prepare(bid,Service())
            self.confirm(bid,token=f"stage-{position}")
            self.clock.second+=20 if batch["mode"]=="assisted" else 10
            self.store.finish(bid)
        result=self.store.study_result(sid)
        self.assertTrue(result["completed"])
        self.assertEqual(result["manual_minus_assisted_seconds"],-10)
        self.assertEqual(result["actor_type"],"automated_test")
        self.assertEqual(result["arms"]["assisted"]["reference_matches"],8)
        self.assertNotIn("operator",result)
        self.assertNotIn("arms",self.store.studies()[0])
        with self.assertRaises(ValueError):self.store.start_arm(sid)

    def test_study_rejects_final_members_repeated_groups_and_unbalanced_classes(self):
        for change in ["partition","group","class"]:
            sample=study_sample()
            if change=="partition":sample["arms"]["manual"][0]["source"]["partition"]="final_test"
            if change=="group":sample["arms"]["assisted"][0]["source"]["group_id"]="manual-group-0"
            if change=="class":sample["arms"]["manual"][0]["reference_category"]="Hardware"
            with self.subTest(change=change):
                with self.assertRaises(ValueError):self.store.create_study("Fixture","automated_test",change,sample=sample)

    def test_deterministic_train_sampler_ignores_final_and_matches_lengths(self):
        root=Path(self.temp.name);(root/"data").mkdir()
        data="Document,Topic_group\n"+"".join(f"example {label} {i},{label}\n" for label in CLASSES for i in range(3))
        (root/"data/tickets.csv").write_text(data)
        membership="row_index,case_id,group_id,partition\n"+"".join(f"{i+1},case-{i},group-{i},{'final_test' if i%3==2 else 'train'}\n" for i in range(24))
        (root/"data/membership.csv").write_text(membership)
        (root/"data/evaluation-manifest.json").write_text(json.dumps({"membership":{"path":"data/membership.csv","sha256":digest(membership)}}))
        (root/"data/manifest.json").write_text(json.dumps({"datasets":{"it_service":{"file":{"path":"data/tickets.csv","sha256":digest(data)}}}}))
        first=pilot_sample("fixed",root)
        self.assertEqual(first,pilot_sample("fixed",root))
        all_rows=[r for v in first["arms"].values() for r in v]
        self.assertEqual(len({r["source"]["group_id"] for r in all_rows}),16)
        self.assertTrue(all(r["source"]["partition"]=="train" for r in all_rows))


if __name__=="__main__":unittest.main()
