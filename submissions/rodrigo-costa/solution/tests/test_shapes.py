from __future__ import annotations

import json
import unittest
from datetime import date, timedelta

from engine import core, shapes

REF = date(2017, 12, 4)
DS = core.get_dataset()


class ShapesTest(unittest.TestCase):
    def test_date_dict(self):
        d = shapes.date_dict(REF)
        self.assertEqual(d, {
            "iso": "2017-12-04", "label": "4 dez 2017", "label_short": "seg, 4 dez 2017",
            "label_long": "segunda-feira, 4 de dezembro de 2017", "day_month": "4 dez", "month_name": "dezembro",
            "week_of_quarter": 9, "month_in_quarter": 2, "quarter_phase": "fecha"})

    def test_person_dict(self):
        p = shapes.person_dict(DS, "daniell hammack")
        self.assertEqual(p, {"name": "Daniell Hammack", "first_name": "Daniell", "initials": "DH",
                             "manager": "Rocco Neubert", "region": "East", "region_label": "Leste"})
        m = shapes.person_dict(DS, "Rocco Neubert")
        self.assertEqual((m["manager"], m["region"], m["region_label"]), (None, "East", "Leste"))
        with self.assertRaisesRegex(ValueError, "Pessoa não encontrada"):
            shapes.person_dict(DS, "Fulano de Tal")

    def test_open_deal_dict(self):
        snap = core.snapshot(DS, REF)
        top = snap.by_seller["Daniell Hammack"][0]
        d = shapes.open_deal_dict(snap, top)
        self.assertEqual(d["id"], "LFI3BGEE")
        self.assertEqual((d["product"], d["price"], d["score"], d["age_days"]), ("GTX Plus Pro", 5482, 98, 73))
        self.assertEqual((d["band"], d["band_label"], d["stale"], d["region_label"]), ("quente", "Quente", False, "Leste"))
        self.assertEqual(d["age_band"], "61–75")
        self.assertEqual(d["engage_date"], (REF - timedelta(days=73)).isoformat())
        self.assertEqual(d["engage_label"], "22 set")
        self.assertAlmostEqual(d["expected_value"], round(top.chance * 5482, 2))
        for key in ("deal_stage", "close_date", "close_value", "won"):
            self.assertNotIn(key, d)
        old = next(x for x in snap.stale if x.deal.engage_date.year == 2016)
        od = shapes.open_deal_dict(snap, old)
        self.assertEqual((od["score"], od["band"], od["chance"], od["expected_value"]), (None, "sem_desfecho", 0.0, 0.0))
        self.assertTrue(od["engage_label"].endswith("2016"))
        no_account = next(x for x in snap.live if x.deal.account is None)
        self.assertIsNone(shapes.open_deal_dict(snap, no_account)["account"])
        json.dumps([shapes.open_deal_dict(snap, x) for x in snap.deals])

    def test_closed_deal_dict(self):
        deal = next(x for x in DS.deals if x.id == "Z063OYW0")
        d = shapes.closed_deal_dict(DS, deal)
        self.assertEqual(d, {
            "id": "Z063OYW0", "product": "GTX Pro", "price": 4821, "account": "Isdom", "seller": "Darcel Schlecht",
            "region_label": "Central", "close_date": "2017-03-11", "close_label": "11 mar 2017", "won": True,
            "close_value": 4514, "cycle_days": 137})
        lost = next(x for x in DS.deals if x.lost)
        self.assertEqual(shapes.closed_deal_dict(DS, lost)["close_value"], 0)
        with self.assertRaises(ValueError):
            shapes.closed_deal_dict(DS, DS.prospecting[0])


if __name__ == "__main__":
    unittest.main()
