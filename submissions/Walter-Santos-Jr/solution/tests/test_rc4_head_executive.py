import unittest
import app

class ExecutiveIntelligenceTests(unittest.TestCase):
    def test_central_sectors_and_stage_counts(self):
        d=app.executive_intelligence('Central')
        self.assertEqual(len(d['sectors']),12)
        self.assertEqual(d['account360']['deals'],3512)
        self.assertEqual(d['stages'],{'Won':1629,'Lost':975,'Prospecting':500,'Engaging':408})
        self.assertEqual(next(s['deals'] for s in d['sectors'] if s['name']=='retail'),412)
    def test_region_filter_and_manager_filter(self):
        d=app.executive_intelligence('Central','Dustin Brinkmann')
        self.assertLess(d['account360']['deals'],3512)
        self.assertGreater(d['account360']['deals'],0)
        self.assertEqual(sum(s['deals'] for s in d['sectors'] if s['name']!='All Sectors'),d['account360']['deals'])
    def test_sector_drilldown_is_consistent(self):
        d=app.executive_intelligence('Central',sector='retail')
        self.assertEqual(d['account360']['deals'],412)
        self.assertEqual(sum(d['stages'].values()),412)
    def test_lost_exposure_is_not_revenue(self):
        d=app.executive_intelligence('Central')
        self.assertGreater(d['derived']['catalog_lost_exposure'],0)
        self.assertIn('não é receita recuperável',d['derived']['catalog_exposure_reason'])
if __name__=='__main__':unittest.main()
