import unittest
from app import hierarchy, ROWS

class HierarchyTests(unittest.TestCase):
    def test_region_counts_match_active_rows(self):
        h=hierarchy()
        self.assertEqual(sum(r["total"] for r in h["regions"]),len(ROWS))
        for r in h["regions"]:
            self.assertEqual(sum(m["total"] for m in r["managers"]),r["total"])
            self.assertEqual(sum(s["total"] for m in r["managers"] for s in m["sellers"]),r["total"])
            self.assertEqual(sum(s["total"] for s in r["sectors"]),r["total"])
    def test_only_active_outcomes(self):
        self.assertEqual(hierarchy()["scope"],"active_opportunities")
