import unittest
from app import hierarchy

class HierarchyPersonaTests(unittest.TestCase):
    def test_head_has_full_hierarchy(self):
        self.assertGreater(len(hierarchy({'role':'HEAD'})['regions']), 1)
    def test_manager_sees_only_own_team(self):
        h=hierarchy({'role':'MANAGER','manager':'Melvin Marxen'})
        self.assertTrue(h['regions'])
        self.assertTrue(all(m['name']=='Melvin Marxen' for r in h['regions'] for m in r['managers']))
    def test_seller_sees_only_own_portfolio(self):
        h=hierarchy({'role':'SELLER','seller':'Darcel Schlecht'})
        self.assertTrue(h['regions'])
        self.assertTrue(all(s['name']=='Darcel Schlecht' for r in h['regions'] for m in r['managers'] for s in m['sellers']))
