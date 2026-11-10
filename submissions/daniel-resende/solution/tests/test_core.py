"""The scoring core on the real rows: no mocks, no network.

Run:  python -m unittest discover -s submissions/daniel-resende/solution/tests
"""
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build  # noqa: E402
import confirm  # noqa: E402
import validate as v  # noqa: E402

ONE_DAY = dt.timedelta(days=1)


def listed(score):
    """block name -> {deal id: record}, over every seller of one score file."""
    out = {"alive": {}, "queue": {}, "clean": {}}
    for seller in score["sellers"]:
        for key in out:
            out[key].update({r["id"]: r for r in seller[key]})
    return out


class CoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deals = v.load()
        cls.teams = v.read("sales_teams.csv")
        cls.last_day = max(d[k] for d in cls.deals for k in ("engage", "close") if d[k])
        cls.cuts = sorted(confirm.SHAPING_CUTS + confirm.CONFIRM_CUTS)
        cls.by_id = {d["id"]: d for d in cls.deals}
        cls.cache = {}

    def monday(self, monday):
        if monday not in self.cache:
            self.cache[monday] = build.build_monday(self.deals, self.teams, monday, self.last_day)
        return self.cache[monday]

    def test_twelve_cuts_exist(self):
        self.assertEqual(len(self.cuts), 12)

    def test_no_leak_field_reaches_a_score(self):
        for cut in self.cuts + [self.last_day]:
            world = v.world_at(self.deals, cut)
            rows = v.open_at(world, cut)
            self.assertTrue(rows)
            for row in rows:
                self.assertEqual(set(row), v.KNOWN_FIELDS, cut)
                self.assertFalse(set(row) & v.LEAK_FIELDS, cut)
            for w in world:  # the world itself holds no outcome beyond the cut
                self.assertLessEqual(w["engage"], cut)
                self.assertTrue(w["close"] is None or w["close"] <= cut)
                self.assertFalse(set(w) & {"stage", "close_value", "account"})

    def test_blocks_follow_the_frozen_rule_on_the_twelve_cuts(self):
        for cut in self.cuts:
            with self.subTest(cut=str(cut)):
                world = v.world_at(self.deals, cut)
                rules = v.fit_rules(world, cut)
                open_rows = v.open_at(world, cut)
                want_dead = {k["id"] for k in open_rows if v.is_dead(rules, k)}
                want_alive = {k["id"] for k in open_rows} - want_dead
                blocks = listed(self.monday(cut + ONE_DAY))
                self.assertEqual(set(blocks["clean"]), want_dead)
                self.assertEqual(set(blocks["alive"]), want_alive)
                self.assertTrue(want_dead and want_alive)

    def test_a_deal_past_the_window_is_never_alive(self):
        for cut in self.cuts:
            with self.subTest(cut=str(cut)):
                monday = cut + ONE_DAY
                score = self.monday(monday)
                longest = score["meta"]["window"]["longest_win_days"]
                for record in listed(score)["alive"].values():
                    self.assertLessEqual(record["days_open"], longest)
                    self.assertGreaterEqual((dt.date.fromisoformat(record["deadline"]) - monday).days, 0)
                    self.assertGreaterEqual(record["days_left"], 0)
                for record in listed(score)["clean"].values():
                    past_age = record["days_open"] > longest
                    past_deadline = dt.date.fromisoformat(record["deadline"]) < monday
                    self.assertTrue(past_age or past_deadline)

    def test_a_closed_deal_is_never_listed_as_work(self):
        for monday in [cut + ONE_DAY for cut in self.cuts] + [build.DEFAULT_MONDAY]:
            cut = monday - ONE_DAY
            with self.subTest(monday=str(monday)):
                blocks = listed(self.monday(monday))
                for block, records in blocks.items():
                    for deal_id in records:
                        deal = self.by_id[deal_id]
                        self.assertTrue(deal["close"] is None or deal["close"] > cut, (block, deal_id))
                        if block != "queue":
                            self.assertTrue(deal["engage"] <= cut, (block, deal_id))

    def pick(self, engage_from, engage_to, close_after):
        """A real deal engaged in the range and still open after `close_after`."""
        found = [d for d in self.deals
                 if d["engage"] and engage_from <= d["engage"] <= engage_to
                 and (d["close"] is None or d["close"] > close_after)]
        self.assertTrue(found)
        return min(found, key=lambda d: d["id"])

    def test_the_deadline_day_is_alive_and_the_next_day_is_to_clean(self):
        cases = [("Q3 engage, deadline 2017-12-31",
                  self.pick(dt.date(2017, 9, 1), dt.date(2017, 9, 30), dt.date(2017, 12, 31))),
                 ("Q2 engage, deadline 2017-09-30",
                  self.pick(dt.date(2017, 6, 1), dt.date(2017, 6, 30), dt.date(2017, 9, 30)))]
        for label, deal in cases:
            with self.subTest(label):
                deadline = v.deadline(deal["engage"])
                on_deadline = listed(self.monday(deadline))
                self.assertIn(deal["id"], on_deadline["alive"])
                self.assertEqual(on_deadline["alive"][deal["id"]]["days_left"], 0)
                after = listed(self.monday(deadline + ONE_DAY))
                self.assertIn(deal["id"], after["clean"])
                self.assertNotIn(deal["id"], after["alive"])
                self.assertEqual(after["clean"][deal["id"]]["clean_fact"], "prazo")

    def test_the_queue_is_empty_on_every_past_monday(self):
        for monday in build.PAST_MONDAYS:
            with self.subTest(monday=str(monday)):
                score = self.monday(monday)
                self.assertTrue(score["meta"]["past"])
                self.assertEqual(listed(score)["queue"], {})
                for seller in score["sellers"]:
                    self.assertEqual(seller["queue"], [])
                    self.assertIsNone(seller["headline"]["queue"])
                self.assertEqual(score["team"]["total"]["queue"], 0)

    def test_the_default_monday_keeps_the_queue(self):
        score = self.monday(build.DEFAULT_MONDAY)
        self.assertFalse(score["meta"]["past"])
        prospecting = {d["id"] for d in self.deals if d["stage"] == "Prospecting"}
        self.assertEqual(set(listed(score)["queue"]), prospecting)


if __name__ == "__main__":
    unittest.main()
