import unittest
from test_app import app

class QualityGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):app.init_db()
    def test_blocked_not_in_pipeline(self):
        d=app.dashboard({'page_size':100})
        self.assertTrue(all(r['quality_gate']['eligible'] for r in d['rows']))
        self.assertEqual(d['total']+d['quality_gate']['blocked_total'],len(app.ROWS))
    def test_rework_jobs_include_blocked(self):
        key=next(r['opportunity_id'] for r in app.ROWS if not r['account_known'])
        self.assertTrue(any(j['job_type']=='IDENTIFY_ACCOUNT' for j in app.jobs_for(key)))
    def test_quality_observation_provenance(self):
        m=app.quality_metrics()
        self.assertEqual(m['observed'],len(app.ROWS))
        self.assertIn('não no instante',m['note'])
    def test_account_fix_releases_deal(self):
        row=next(r for r in app.ROWS if not r['account_known'])
        key=row['opportunity_id']
        self.assertFalse(app.quality_gate(row)['eligible'])
        result=app.save_account(key,{'account':'Cliente Teste - cadastro local'})
        self.assertTrue(result['quality_gate']['eligible'])
        job=next(j for j in app.jobs_for(key,include_history=True) if j['job_type']=='IDENTIFY_ACCOUNT')
        self.assertEqual(job['status'],'VERIFIED')
        self.assertTrue(any(e['event_type']=='VERIFIED' for e in job['events']))
        self.assertTrue(any(e['event_type']=='GATE_PASSED' for e in app.quality_metrics()['events']))
