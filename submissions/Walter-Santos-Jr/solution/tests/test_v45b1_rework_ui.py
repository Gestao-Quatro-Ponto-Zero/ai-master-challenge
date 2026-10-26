import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'static/app.js').read_text(encoding='utf-8')
CSS=(ROOT/'static/style.css').read_text(encoding='utf-8')
class ReworkSimplificationTests(unittest.TestCase):
    def test_separate_rework_main(self):
        self.assertIn("requestedWorkspace==='rework'?reworkDetail(d,currentJob):decisionContent(d)", JS)
    def test_single_submit_action(self):
        self.assertIn('Salvar e verificar',JS)
        card=JS.split('function jobCard(j){',1)[1].split('function visibleReworkJobs()',1)[0]
        self.assertNotIn('Abrir deal',card)
        self.assertNotIn('jobButtons(',card)
    def test_confirmation_requires_backend_verified(self):
        self.assertIn("verified.status!=='VERIFIED'",JS)
        self.assertIn('state.reworkConfirmation={jobId:',JS)
    def test_explicit_next_job(self):
        self.assertIn('id="nextRework"',JS)
        self.assertIn('async function nextRework()',JS)
    def test_contrast(self):
        self.assertIn('body:not(.theme-light) .rework-guidance',CSS)
