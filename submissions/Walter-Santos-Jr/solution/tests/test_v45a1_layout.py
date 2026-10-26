import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class LayoutHotfixTests(unittest.TestCase):
 def test_eight_pipeline_deals(self):
  js=(ROOT/'static/app.js').read_text()
  self.assertIn("params.set('page_size',8)",js)
 def test_rework_pagination(self):
  js=(ROOT/'static/app.js').read_text()
  html=(ROOT/'static/index.html').read_text()
  self.assertIn('visibleReworkJobs()',js)
  self.assertIn('reworkPageSize:6',js)
  self.assertIn('id="reworkNext"',html)
 def test_workflow_selection(self):
  js=(ROOT/'static/app.js').read_text()
  self.assertIn('selectWorkspaceFirst(workspace)',js)
  self.assertIn("workspace==='rework'?first?.opportunity_id:state.dealOrder[0]",js)
