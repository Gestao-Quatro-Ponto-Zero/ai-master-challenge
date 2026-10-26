import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEMP=tempfile.TemporaryDirectory()
os.environ['G4_DB_PATH']=str(Path(TEMP.name)/'test.sqlite3')
spec=importlib.util.spec_from_file_location('g4_app',ROOT/'app.py')
app=importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class WorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):app.init_db()
    def test_real_data(self):
        self.assertEqual(len(app.ROWS),2089)
        self.assertEqual(len(app.INDEX),2089)
    def test_dashboard_kpis(self):
        d=app.dashboard()
        self.assertEqual(d['kpis']['engaging'],sum(r['deal_stage']=='Engaging' and app.quality_gate(r)['eligible'] for r in app.ROWS))
        self.assertEqual(d['kpis']['prospecting'],sum(r['deal_stage']=='Prospecting' and app.quality_gate(r)['eligible'] for r in app.ROWS))
        self.assertEqual(d['kpis']['account_missing'],1425)
    def test_stage_filter(self):
        d=app.dashboard({'deal_stage':'Prospecting'})
        self.assertEqual(d['total'],sum(r['deal_stage']=='Prospecting' and app.quality_gate(r)['eligible'] for r in app.ROWS))
        self.assertTrue(all(r['deal_stage']=='Prospecting' for r in d['rows']))
    def test_manager_filter(self):
        manager=app.ROWS[0]['manager']
        d=app.dashboard({'manager':manager})
        self.assertTrue(d['total']>0)
        self.assertTrue(all(r['manager']==manager for r in d['rows']))
    def test_explanation_components(self):
        d=app.dashboard()
        for r in d['rows']:
            self.assertAlmostEqual(sum(c['points'] for c in r['score_explanation']),r['priority_score'],delta=.16)
    def test_persistence(self):
        key=app.ROWS[0]['opportunity_id']
        app.save_qualification(key,{'decision_maker':'yes','timeline':'yes','budget':'unknown','notes':'Confirmed'})
        app.save_activity(key,{'action':'CONTACT','note':'Called'})
        q,acts=app.get_state()
        self.assertEqual(q[key]['decision_maker'],'yes')
        self.assertTrue(any(a['opportunity_id']==key for a in acts))
    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):app.save_activity(app.ROWS[0]['opportunity_id'],{'action':'DROP TABLE activities'})
        with self.assertRaises(KeyError):app.save_qualification('NONEXISTENT',{})
    def test_missing_account_is_neutral(self):
        for r in app.ROWS:
            if not r['account_known']:
                self.assertEqual(r['account_component'],50)
                break

if __name__=='__main__':unittest.main()
