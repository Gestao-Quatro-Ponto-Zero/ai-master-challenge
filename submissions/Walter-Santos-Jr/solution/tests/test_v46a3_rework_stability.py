import unittest
from pathlib import Path
JS=(Path(__file__).resolve().parents[1]/'static'/'app.js').read_text(encoding='utf-8')
class ReworkStabilityTests(unittest.TestCase):
 def test_no_unverified_kpi_trend_buttons(self):
  self.assertNotIn('data-kpi="${key}"', JS)
  self.assertIn('data-kpi="conversion"', JS)
 def test_selection_does_not_replace_main_with_loading_placeholder(self):
  self.assertNotIn('Carregando Job #', JS)
 def test_selection_invalidates_workspace_autoselect(self):
  self.assertIn('state.selectedReworkJob=jobId;state.workspaceRequest++;',JS)
 def test_stale_detail_guard_remains(self):
  self.assertIn('detailRequest!==state.detailRequest',JS)
