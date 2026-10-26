import unittest
from pathlib import Path

JS = (Path(__file__).resolve().parents[1] / 'static' / 'app.js').read_text()

class ReworkContextTests(unittest.TestCase):
    def test_six_jobs_per_page(self):
        self.assertIn('reworkPageSize:6', JS)
    def test_whole_card_click(self):
        self.assertIn("querySelectorAll('[data-job-card]').forEach(card=>", JS)
    def test_race_protection(self):
        self.assertIn('if(detailRequest!==state.detailRequest||requestedWorkspace!==state.workspace)return', JS)
    def test_workspace_resets_stale_selection(self):
        self.assertIn('state.selected=null;state.detailRequest++', JS)
    def test_rework_uses_execution_tab(self):
        self.assertIn("rework:'execution'", JS)
