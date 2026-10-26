import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'static/app.js').read_text()
HTML=(ROOT/'static/index.html').read_text()
CSS=(ROOT/'static/style.css').read_text()
class NavbarConversionTests(unittest.TestCase):
 def test_six_rework_jobs(self):
  self.assertIn('reworkPageSize:6',JS)
 def test_quality_block_removed_from_frontend(self):
  self.assertNotIn('id="navQuality"',HTML)
  self.assertNotIn("$('navQuality')",JS)
 def test_conversion_toggle(self):
  self.assertIn('data-kpi="conversion"',JS)
  self.assertIn("activeTrendKey==='conversion'",JS)
  self.assertNotIn('id="conversionDetail"',JS)
 def test_conversion_layout(self):
  self.assertIn('.conversion-heading',CSS)
  self.assertIn('.conversion-trend',CSS)
