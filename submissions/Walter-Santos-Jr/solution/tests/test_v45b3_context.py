import unittest
from pathlib import Path
JS=(Path(__file__).resolve().parents[1]/'static'/'app.js').read_text(encoding='utf-8')
class ContextIntegrityTests(unittest.TestCase):
 def test_job_snapshot_bound_to_detail(self):
  self.assertIn('function reworkDetail(d, selectedJob)',JS)
  self.assertIn('const r=d.opportunity,j=selectedJob;',JS)
 def test_stale_requests_rejected(self):
  self.assertIn('requestedWorkspace!==state.workspace',JS)
  self.assertIn("jobId!==String(state.selectedReworkJob??'')",JS)
 def test_opportunity_matches_job(self):
  self.assertIn('String(currentJob.opportunity_id)!==String(id)',JS)
 def test_click_preserves_main_until_detail_arrives(self):
  self.assertNotIn('Carregando Job #',JS)
  self.assertIn('openDetail(String(job.opportunity_id),false,jobId)',JS)
 def test_first_job_has_explicit_identity(self):
  self.assertIn("workspace==='rework'?String(first.id):null",JS)
