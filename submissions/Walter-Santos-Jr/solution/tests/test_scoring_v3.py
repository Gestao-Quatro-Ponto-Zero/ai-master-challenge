import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scoring_v3 import assess, POLICY_VERSION

ROW = dict(priority_score=70.0, stage_component=75, product_component=80,
           account_component=48, account_known=True, deal_stage='Engaging')

class ScoringV3Tests(unittest.TestCase):
    def test_baseline_preserved(self):
        result = assess(ROW)
        self.assertEqual(result['priority_score'], 70)
        self.assertEqual(result['policy_version'], POLICY_VERSION)
        self.assertAlmostEqual(sum(c['points'] for c in result['score_explanation']), 70, delta=.2)
    def test_unknown_is_not_negative(self):
        result = assess(ROW)
        self.assertEqual(result['buying_readiness'], 'UNASSESSED')
        self.assertEqual(result['qualification_evidence_summary']['negative'], 0)
        self.assertEqual(result['data_confidence_detail']['qualification_known'], 0)
    def test_qualified_evidence(self):
        result = assess(ROW, dict(decision_maker='yes', budget='yes', timeline='yes'))
        self.assertEqual(result['buying_readiness'], 'QUALIFIED')
        self.assertEqual(result['next_best_action'], 'REVIEW_ENGAGEMENT')
        self.assertEqual(result['priority_score'], 70)
    def test_blocker_changes_action_not_attractiveness(self):
        result = assess(ROW, dict(decision_maker='no', budget='unknown', timeline='yes'))
        self.assertEqual(result['buying_readiness'], 'BLOCKED')
        self.assertEqual(result['job_priority_hint'], 'P1')
        self.assertEqual(result['next_best_action'], 'RESOLVE_QUALIFICATION_BLOCKER')
        self.assertEqual(result['priority_score'], 70)
    def test_missing_account_neutral_and_actionable(self):
        result = assess({**ROW, 'account_known': False})
        self.assertEqual(result['next_best_action'], 'IDENTIFY_ACCOUNT')
        self.assertIn('ACCOUNT_MISSING', [r['code'] for r in result['deal_health_flags']])
    def test_invalid_evidence(self):
        with self.assertRaises(ValueError):
            assess(ROW, {'budget':'maybe'})
    def test_no_clock_based_stagnation(self):
        first = assess({**ROW, 'engage_date':'2017-01-01'})
        second = assess({**ROW, 'engage_date':'2026-10-21'})
        self.assertEqual(first['priority_score'], second['priority_score'])
        self.assertEqual(first['job_priority_hint'], second['job_priority_hint'])
    def test_boundary_bands(self):
        self.assertEqual(assess({**ROW, 'priority_score':45})['priority_band'],'LOW')
        self.assertEqual(assess({**ROW, 'priority_score':65})['priority_band'],'MEDIUM')
        self.assertEqual(assess({**ROW, 'priority_score':65.1})['priority_band'],'HIGH')

if __name__ == '__main__': unittest.main()
