from __future__ import annotations

import json
import unittest
from datetime import date

from engine import accounts, core

REF = date(2017, 12, 4)
DS = core.get_dataset()
BY_ID = {x.id: x for x in DS.deals}
EDGE_DATES = (date(2017, 7, 3), date(2017, 10, 2), REF, date(2017, 12, 25))


class ListingTest(unittest.TestCase):
    def test_east_reference(self):
        out = accounts.listing(DS, REF, "Leste")
        self.assertEqual((out["region"], out["region_label"], out["count"]), ("East", "Leste", 27))
        self.assertEqual(out["title"], "Clientes da regional Leste")
        self.assertEqual(out["subtitle"], "27 clientes compram desta regional. Os números vêm dos deals fechados, "
                                          "onde o cliente é confiável.")
        self.assertEqual(out["note"], "Ordenado por valor ganho até 3 dez 2017. A taxa de ganho muda pouco de um "
                                      "cliente para outro, nada além do que o acaso explica, por isso não entra no "
                                      "score.")
        self.assertIn("pode mudar de uma semana para outra", out["home_region_note"])
        expected = [
            ("Mathtouch", 75, 0.667, 152556, "3 dez"), ("Umbrella Corporation", 72, 0.611, 139829, "29 nov"),
            ("Donquadtech", 74, 0.716, 135610, "1 dez"), ("Plussunin", 80, 0.600, 128348, "21 nov"),
            ("Xx-zobam", 74, 0.568, 123232, "24 nov"), ("Zotware", 63, 0.651, 118105, "25 nov"),
            ("Gekko & Co", 77, 0.688, 114323, "1 dez"), ("Vehement Capital Partners", 54, 0.593, 105910, "8 nov")]
        got = [(r["name"], r["closed_count"], round(r["win_rate"], 3), r["won_value"], r["last_sale_label"])
               for r in out["accounts"][:8]]
        self.assertEqual(got, expected)
        self.assertEqual(out["accounts"][0]["last_sale_date"], "2017-12-03")
        self.assertEqual(out["accounts"][0]["sector_label"], "Marketing")
        json.dumps(out)

    def test_all_and_partition(self):
        for d in EDGE_DATES:
            whole = accounts.listing(DS, d)
            self.assertEqual((whole["title"], whole["count"], whole["region"]), ("Clientes da empresa", 85, None))
            parts = sum(accounts.listing(DS, d, r)["count"] for r in ("Central", "East", "West"))
            homeless = sum(1 for r in whole["accounts"] if r["home_region"] is None)
            self.assertEqual(parts + homeless, 85)
            values = [(-r["won_value"], r["name"]) for r in whole["accounts"]]
            self.assertEqual(values, sorted(values))

    def test_only_past_closes(self):
        for d in EDGE_DATES:
            for r in accounts.listing(DS, d)["accounts"]:
                closed = [x for x in DS.deals_by_account.get(r["name"], ()) if x.close_date and x.close_date < d]
                self.assertEqual(r["closed_count"], len(closed))
                self.assertEqual(r["won_value"], sum(x.close_value for x in closed if x.won))
                if r["last_sale_date"]:
                    self.assertLess(r["last_sale_date"], d.isoformat())

    def test_unknown_region(self):
        with self.assertRaisesRegex(ValueError, "Regional não encontrada"):
            accounts.listing(DS, REF, "Norte")


class DetailTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = accounts.detail(DS, REF, "mathtouch", viewer="Reed Clapper")

    def test_account_and_history(self):
        a, h = self.out["account"], self.out["history"]
        self.assertEqual(a["name"], "Mathtouch")
        self.assertEqual((a["sector_label"], a["revenue_label"], a["employees"], a["year_established"]),
                         ("Marketing", "US$ 3,03 bilhões", 9516, 1984))
        self.assertEqual((a["office_label"], a["parent"], a["home_region"]), ("Jordânia", None, "East"))
        self.assertEqual(a["subtitle"], "Marketing · atendido pela regional Leste")
        self.assertEqual((h["closed_count"], h["won_count"], h["lost_count"], h["won_value"]), (75, 50, 25, 152556))
        self.assertEqual(round(h["avg_ticket"]), 3051)
        self.assertEqual((h["last_sale_label"], h["seller_count"], h["seller_regions"]), ("3 dez", 10, ["Leste"]))
        self.assertEqual(h["headline_detail"], "em 50 vendas. Dos 75 deals fechados, 25 foram perdidos.")
        self.assertEqual(h["sellers_label"], "vendedores com deal fechado, da regional Leste")
        self.assertEqual(a["home_region_note"], accounts.HOME_REGION_NOTE)
        self.assertEqual([(p["product"], p["won_count"], p["won_value"]) for p in self.out["top_products"]],
                         [("GTX Pro", 18, 83230), ("GTX Plus Pro", 6, 31494), ("MG Advanced", 8, 27735)])
        self.assertEqual(self.out["top_products"][0]["share"], 1.0)
        self.assertTrue(self.out["note"].startswith("Porte e histórico descrevem o cliente"))

    def test_open(self):
        o = self.out["open"]
        self.assertEqual((o["count"], o["live_count"], o["stale_count"], o["other_region_count"]), (13, 10, 3, 6))
        live = [(i["id"], i["score"], round(i["chance"] * 100), i["age_days"], i["seller"]) for i in o["live"]]
        self.assertEqual(live, [
            ("Z6ETLZQU", 98, 50, 64, "Corliss Cosme"), ("ESZPH44N", 96, 51, 86, "Violet Mclelland"),
            ("D3HUUVPL", 94, 50, 71, "Daniell Hammack"), ("8TFYRWZ6", 68, 19, 135, "Gladys Colclough"),
            ("HJLKGIH4", 61, 51, 77, "Reed Clapper"), ("IEIZU3TY", 59, 50, 70, "Reed Clapper"),
            ("O2BF1KAT", 19, 50, 65, "Garret Kinder"), ("9D43V124", 13, 35, 106, "Vicki Laflamme"),
            ("PR1H7NHK", 11, 19, 125, "Versie Hillebrand"), ("NNH4EBG8", 11, 19, 123, "Vicki Laflamme")])
        self.assertEqual({(i["id"], i["age_days"]) for i in o["stale"]},
                         {("CT3HBBI2", 323), ("RP7KA6HS", 302), ("26CH1NDR", 270)})
        self.assertTrue(all(i["score"] is None and i["chance"] == 0 for i in o["stale"]))
        self.assertEqual([i["id"] for i in o["live"] + o["stale"] if i["is_viewer"]], ["HJLKGIH4", "IEIZU3TY"])
        others = sorted(i["id"] for i in o["live"] + o["stale"] if i["other_region"])
        self.assertEqual(others, sorted(["8TFYRWZ6", "9D43V124", "PR1H7NHK", "NNH4EBG8", "CT3HBBI2", "RP7KA6HS"]))
        self.assertEqual(o["warning"]["title"], "O cliente de um deal aberto não é confiável nesta base")
        self.assertEqual(o["warning"]["body"], "Dos 13 abaixo, 6 estão com vendedores de outras regionais, que nunca "
                                               "fecharam negócio com a Mathtouch. Por isso o cliente não entra no score.")
        for i in o["live"] + o["stale"]:
            for key in ("close_date", "close_value", "won"):
                self.assertNotIn(key, i)

    def test_closed(self):
        c = self.out["closed"]
        self.assertEqual((c["count"], c["won_count"], c["lost_count"], c["won_value"]), (75, 50, 25, 152556))
        self.assertEqual(c["value_label"], "em vendas, até 3 dez 2017")
        self.assertEqual([(m["label"], m["won_count"]) for m in c["by_month"]], [
            ("mar", 9), ("abr", 3), ("mai", 5), ("jun", 9), ("jul", 2), ("ago", 4), ("set", 10), ("out", 2),
            ("nov", 5), ("dez", 1)])
        self.assertEqual([m["month"] for m in c["by_month"] if m["quarter_end"]],
                         ["2017-03", "2017-06", "2017-09", "2017-12"])
        self.assertEqual(c["month_sentence"], "Março, junho e setembro somam 28 das 50 vendas: é o ritmo de fim de "
                                              "trimestre. Dezembro conta só até o dia 3.")
        recent = [(x["id"], x["close_label"], x["product"], x["seller"], x["won"], x["close_value"], x["cycle_days"])
                  for x in c["deals"][:8]]
        self.assertEqual(recent, [
            ("5HKITTHD", "3 dez 2017", "GTX Plus Pro", "Boris Faz", True, 5703, 106),
            ("1W5FOS69", "30 nov 2017", "GTX Pro", "Cassey Cress", True, 4201, 91),
            ("6NWIZG2N", "24 nov 2017", "GTX Plus Basic", "Reed Clapper", True, 1035, 8),
            ("5SJP2J1J", "20 nov 2017", "GTX Plus Basic", "Boris Faz", True, 886, 1),
            ("8977L373", "19 nov 2017", "MG Advanced", "Wilburn Farren", True, 4011, 7),
            ("FYS6IZO4", "7 nov 2017", "MG Special", "Violet Mclelland", True, 59, 64),
            ("XVM3UK16", "6 nov 2017", "GTX Plus Pro", "Daniell Hammack", False, 0, 67),
            ("GXQJVJQT", "29 out 2017", "GTX Basic", "Corliss Cosme", True, 601, 2)])
        self.assertEqual(len(c["deals"]), 75)
        self.assertTrue(c["deals"][2]["is_viewer"])
        json.dumps(self.out)

    def test_no_future_leak(self):
        for d in EDGE_DATES:
            for name in ("Mathtouch", "Kan-code", "Isdom"):
                out = accounts.detail(DS, d, name)
                for x in out["closed"]["deals"]:
                    self.assertLess(x["close_date"], d.isoformat())
                for i in out["open"]["live"] + out["open"]["stale"]:
                    deal = BY_ID[i["id"]]
                    self.assertTrue(deal.is_open_at(d))

    def test_warning_variants(self):
        out = accounts.detail(DS, date(2017, 7, 3), "Mathtouch")
        self.assertEqual(out["open"]["warning"]["body"],
                         "Dos 15 abaixo, 2 estão com um vendedor de outra regional, que nunca fechou negócio com "
                         "a Mathtouch. Por isso o cliente não entra no score.")
        found_plain = found_closed_before = False
        for d in EDGE_DATES:
            for name in DS.accounts:
                o = accounts.detail(DS, d, name)["open"]
                w = o["warning"]
                if o["count"] == 0:
                    self.assertIsNone(w)
                    continue
                if o["other_region_count"] == 0:
                    found_plain = True
                    self.assertTrue(w["body"].startswith("Nesta base, só os deals fechados"))
                elif "nunca" not in w["body"]:
                    found_closed_before = True
                    self.assertTrue(w["body"].endswith(". Por isso o cliente não entra no score."))
                    names = {i["seller"] for i in o["live"] + o["stale"] if i["other_region"]}
                    closers = {x.seller for x in DS.closed_before(d, account=name)}
                    self.assertTrue(names & closers)
        self.assertTrue(found_plain and found_closed_before)

    def test_month_sentence_truth(self):
        for d in EDGE_DATES:
            for name in DS.accounts:
                c = accounts.detail(DS, d, name)["closed"]
                text = c["month_sentence"]
                if text is None or "ritmo" not in text:
                    continue
                done = c["by_month"][:-1]
                ends = [m["won_count"] for m in done if m["quarter_end"]]
                rest = [m["won_count"] for m in done if not m["quarter_end"]]
                self.assertGreaterEqual(sum(ends) / len(ends), accounts.QUARTER_END_LIFT * sum(rest) / len(rest))
                self.assertIn("das %d vendas" % c["won_count"], text)

    def test_month_sentence_needs_a_clear_lift(self):
        # Acme: março, junho e setembro somam 11 das 30 vendas, quase a média dos outros meses
        acme = accounts.detail(DS, REF, "Acme Corporation")["closed"]["month_sentence"]
        self.assertNotIn("ritmo", acme)
        self.assertTrue(acme.startswith("Os meses de fim de trimestre vendem só um pouco mais"))
        umbrella = accounts.detail(DS, REF, "Umbrella Corporation")["closed"]["month_sentence"]
        self.assertNotIn("ritmo", umbrella)

    def test_closed_order_matches_pipeline(self):
        deals = accounts.detail(DS, REF, "Condax")["closed"]["deals"]
        keys = [(-date.fromisoformat(x["close_date"]).toordinal(), x["id"]) for x in deals]
        self.assertEqual(keys, sorted(keys))

    def test_manager_viewer_marks_team_deals(self):
        out = accounts.detail(DS, REF, "Mathtouch", viewer="rocco neubert")
        self.assertEqual(out["viewer"], "Rocco Neubert")
        team = set(DS.managers["Rocco Neubert"])
        opened = out["open"]["live"] + out["open"]["stale"]
        self.assertEqual({i["id"] for i in opened if i["is_viewer"]},
                         {i["id"] for i in opened if i["seller"] in team})
        self.assertIn("D3HUUVPL", {i["id"] for i in opened if i["is_viewer"]})
        closed = out["closed"]["deals"]
        self.assertTrue(any(x["is_viewer"] for x in closed))
        self.assertTrue(all(x["is_viewer"] == (x["seller"] in team) for x in closed))

    def test_month_range_follows_date(self):
        c = accounts.detail(DS, date(2017, 10, 2), "Mathtouch")["closed"]
        self.assertEqual(c["by_month"][-1]["month"], "2017-10")
        self.assertTrue(c["month_sentence"].endswith("Outubro conta só até o dia 1."))
        self.assertEqual(c["value_label"], "em vendas, até 1 out 2017")

    def test_headline_variants(self):
        f = accounts._headline_detail
        self.assertEqual(f(0, 0, 0), "em nenhuma venda. Ainda não há deals fechados com este cliente.")
        self.assertEqual(f(1, 1, 0), "em 1 venda. O deal fechado foi ganho.")
        self.assertEqual(f(1, 0, 1), "em nenhuma venda. O deal fechado foi perdido.")
        self.assertEqual(f(3, 2, 1), "em 2 vendas. Dos 3 deals fechados, 1 foi perdido.")
        self.assertEqual(f(3, 3, 0), "em 3 vendas. Nenhum dos 3 deals fechados foi perdido.")

    def test_errors(self):
        with self.assertRaisesRegex(ValueError, "Cliente não encontrado"):
            accounts.detail(DS, REF, "Empresa Inexistente")
        with self.assertRaisesRegex(ValueError, "Pessoa não encontrada"):
            accounts.detail(DS, REF, "Mathtouch", viewer="Fulano")
        with self.assertRaisesRegex(ValueError, "só está no cadastro"):
            accounts.detail(DS, REF, "Mathtouch", viewer="Carl Lin")


if __name__ == "__main__":
    unittest.main()
