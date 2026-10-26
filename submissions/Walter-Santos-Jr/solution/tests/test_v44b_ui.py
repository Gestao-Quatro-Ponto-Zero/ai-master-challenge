import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class VisualUXTests(unittest.TestCase):
 def test_single_deal_queue(self):
  html=(ROOT/'static/index.html').read_text()
  self.assertNotIn('My Priority Queue',html)
  self.assertIn('id="asideDealCards"',html)
  self.assertIn('id="stage"',html)
 def test_workspace_handler_unique(self):
  js=(ROOT/'static/app.js').read_text()
  self.assertEqual(js.count('function setWorkspace('),1)
 def test_gauges_use_backend_data(self):
  js=(ROOT/'static/app.js').read_text()
  self.assertIn('r.score_explanation',js)
  self.assertIn('xai-gauge',js)
 def test_account_rework_not_qualification(self):
  js=(ROOT/'static/app.js').read_text()
  a=js.index("if(tab==='qualification')content=")
  b=js.index("if(tab==='execution')content=",a)
  self.assertNotIn('accountForm',js[a:b])
  self.assertIn('accountForm',js[b:])
