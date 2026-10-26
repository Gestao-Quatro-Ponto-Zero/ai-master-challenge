import tempfile
import unittest
from pathlib import Path
import app

class SalesActionCenterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.old=app.DB_PATH
        app.DB_PATH=Path(self.temp.name)/'test.sqlite3'
        app.init_db()
        self.eligible=next(k for k,r in app.INDEX.items() if app.quality_gate(r)['eligible'])
        self.blocked=next(k for k,r in app.INDEX.items() if not app.quality_gate(r)['eligible'])
    def tearDown(self):
        app.DB_PATH=self.old
        self.temp.cleanup()
    def test_plan_create_and_status_and_audit(self):
        r=app.save_action_plan(self.eligible,{'title':'Ligar para decisor','owner':'Vendedor','due_date':'2099-01-01','priority':'HIGH'})
        state=app.sales_action_state(self.eligible)
        self.assertEqual(state['plans'][0]['id'],r['id'])
        self.assertEqual(state['plans'][0]['status'],'OPEN')
        app.update_action_plan(self.eligible,{'id':r['id'],'status':'DONE'})
        state=app.sales_action_state(self.eligible)
        self.assertEqual(state['plans'][0]['status'],'DONE')
        self.assertEqual(len(state['events']),2)
    def test_cross_deal_status_denied(self):
        other=next(k for k,r in app.INDEX.items() if app.quality_gate(r)['eligible'] and k!=self.eligible)
        pid=app.save_action_plan(self.eligible,{'title':'Follow-up','owner':'Vendedor','due_date':'2099-01-01','priority':'MEDIUM'})['id']
        with self.assertRaises(KeyError):app.update_action_plan(other,{'id':pid,'status':'DONE'})
    def test_quality_gate_blocks_commercial(self):
        with self.assertRaises(ValueError):app.save_action_plan(self.blocked,{'title':'Follow-up','owner':'Vendedor','due_date':'2099-01-01','priority':'HIGH'})
        with self.assertRaises(ValueError):app.save_activity(self.blocked,{'action':'CONTACT','note':'Teste'})
        with self.assertRaises(ValueError):app.save_qualification(self.blocked,{})
    def test_validation(self):
        with self.assertRaises(ValueError):app.save_action_plan(self.eligible,{'title':'','owner':'X','due_date':'2099-01-01','priority':'HIGH'})
        with self.assertRaises(ValueError):app.save_action_plan(self.eligible,{'title':'X','owner':'X','due_date':'2020-01-01','priority':'HIGH'})
    def test_qualification_and_activity_persist(self):
        app.save_qualification(self.eligible,{'decision_maker':'yes','budget':'unknown','timeline':'yes','notes':'Contato validado'})
        app.save_activity(self.eligible,{'action':'CONTACT','note':'Ligação realizada'})
        state=app.sales_action_state(self.eligible)
        self.assertEqual(state['qualification']['decision_maker'],'yes')
        self.assertEqual(state['activities'][0]['action'],'CONTACT')
        self.assertEqual(len(state['events']),2)

if __name__=='__main__':unittest.main()
