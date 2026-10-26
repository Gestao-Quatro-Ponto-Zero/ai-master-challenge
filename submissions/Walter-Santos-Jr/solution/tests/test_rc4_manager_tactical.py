import unittest
import app

class ManagerTacticalTests(unittest.TestCase):
    def test_three_regions(self):
        data=app.management_intelligence('Central')
        self.assertEqual([r['name'] for r in data['regions']],['Central','East','West'])
        self.assertEqual(data['team']['deals'],3512)
    def test_manager_team(self):
        data=app.management_intelligence('Central','Dustin Brinkmann')
        self.assertTrue(data['sellers'])
        self.assertEqual(sum(x['deals'] for x in data['sellers']),data['team']['deals'])
    def test_region_changes_counts(self):
        self.assertNotEqual(app.management_intelligence('Central')['team']['deals'],app.management_intelligence('East')['team']['deals'])
    def test_live_pipeline_is_separate(self):
        data=app.management_intelligence('Central','Melvin Marxen')
        self.assertEqual(data['live_team_pipeline'],sum(x['active_pipeline'] for x in data['sellers']))
