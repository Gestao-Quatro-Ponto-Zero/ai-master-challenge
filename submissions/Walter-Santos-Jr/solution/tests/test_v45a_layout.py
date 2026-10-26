import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
ROOT=Path(__file__).resolve().parents[1]
class LayoutV45ATests(unittest.TestCase):
 def test_six_deals_per_page(self):
  d=app.dashboard({'page':'1','page_size':'6'})
  self.assertLessEqual(len(d['rows']),6)
  self.assertEqual(d['pages'],(d['total']+5)//6)
 def test_no_filters_visible(self):
  h=(ROOT/'static/index.html').read_text()
  self.assertIn('hidden-filter-controls',h)
  self.assertIn('data-workspace="rework"',h)
  self.assertIn('id="hierarchyBack"',h)
  self.assertNotIn('id="workspaceHelp"',h)
 def test_xai_gauges_preserved(self):
  js=(ROOT/'static/app.js').read_text()
  self.assertIn('xai-gauge-grid',js)
  self.assertIn("params.set('page_size',8)",js)
  self.assertIn('policyBtn',js)
