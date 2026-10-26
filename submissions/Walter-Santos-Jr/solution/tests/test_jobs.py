import unittest
from test_app import app

class JobEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.init_db()

    def test_idempotent_generation(self):
        before=len(app.jobs_for(limit=500))
        app.sync_jobs()
        self.assertEqual(before,len(app.jobs_for(limit=500)))
        with app.connect() as db:
            duplicates=db.execute('SELECT opportunity_id,job_type,COUNT(*) n FROM opportunity_jobs GROUP BY 1,2 HAVING n>1').fetchall()
        self.assertFalse(duplicates)

    def test_workflow_and_evidence_verification(self):
        row=next(r for r in app.ROWS if r['account_known'])
        key=row['opportunity_id']
        app.save_qualification(key,{'decision_maker':'unknown','timeline':'unknown','budget':'unknown'})
        job=next(j for j in app.jobs_for(key) if j['job_type']=='QUALIFY_OPPORTUNITY')
        with self.assertRaises(ValueError):app.transition_job(job['id'],'RESOLVE')
        self.assertEqual(app.transition_job(job['id'],'START')['status'],'IN_PROGRESS')
        self.assertEqual(app.transition_job(job['id'],'RESOLVE')['status'],'RESOLVED')
        self.assertTrue(any(j['id']==job['id'] for j in app.jobs_for(key)))
        app.save_qualification(key,{'decision_maker':'yes','timeline':'yes','budget':'yes'})
        self.assertFalse(any(j['id']==job['id'] for j in app.jobs_for(key)))
        verified=next(j for j in app.jobs_for(key,include_history=True) if j['id']==job['id'])
        self.assertEqual(verified['status'],'VERIFIED')
        self.assertTrue(any(e['event_type']=='VERIFIED' for e in verified['events']))
        app.save_qualification(key,{'decision_maker':'unknown','timeline':'yes','budget':'yes'})
        reopened=next(j for j in app.jobs_for(key) if j['id']==job['id'])
        self.assertEqual(reopened['status'],'REOPENED')

    def test_unverifiable_account_not_auto_closed(self):
        row=next(r for r in app.ROWS if not r['account_known'])
        job=next(j for j in app.jobs_for(row['opportunity_id']) if j['job_type']=='IDENTIFY_ACCOUNT')
        if job['status'] in ('OPEN','REOPENED'):
            app.transition_job(job['id'],'START')
        if any(j['id']==job['id'] and j['status']=='IN_PROGRESS' for j in app.jobs_for(row['opportunity_id'])):
            app.transition_job(job['id'],'RESOLVE')
        self.assertEqual(next(j for j in app.jobs_for(row['opportunity_id']) if j['id']==job['id'])['status'],'RESOLVED')
