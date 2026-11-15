from __future__ import annotations

import json
import re
import unittest
from datetime import date

from engine import core, fmt
from engine.team import team

REF = date(2017, 12, 4)
DS = core.get_dataset()
ROCCO = ("Boris Faz", "Cassey Cress", "Daniell Hammack", "Donn Cantrell", "Reed Clapper")


class TeamReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = team(DS, REF, manager="Rocco Neubert")

    def test_scope_and_options(self):
        out = self.out
        self.assertEqual(out["scope"], {"region": None, "region_label": None, "manager": "Rocco Neubert",
                                        "seller": None, "title": "Time de Rocco Neubert"})
        self.assertEqual(out["options"]["sellers"], list(ROCCO))
        self.assertEqual([r["key"] for r in out["options"]["regions"]], ["Central", "East", "West"])
        self.assertEqual(len(out["options"]["managers"]), 6)
        self.assertEqual(out["date"]["iso"], "2017-12-04")
        json.dumps(out)

    def test_summary(self):
        s = self.out["summary"]
        self.assertEqual((s["seller_count"], s["open_count"], s["live_count"], s["stale_count"]), (5, 307, 169, 138))
        self.assertEqual((s["declared_value"], s["live_value"], s["stale_value"]), (824840, 438104, 386736))
        # A soma crua é 153.814,92; a referência 153.814 é a soma dos valores já arredondados por vendedor.
        self.assertAlmostEqual(s["expected_30d"], 153814.92, places=2)
        self.assertEqual(s["hot_count"], 55)
        self.assertAlmostEqual(s["live_share"] + s["stale_share"], 1.0)
        self.assertEqual(s["headline"], "Declarado: US$ 824.840. Ainda vivo: US$ 438.104.")

    def test_rows(self):
        rows = self.out["rows"]
        self.assertEqual([r["name"] for r in rows],
                         ["Cassey Cress", "Daniell Hammack", "Boris Faz", "Reed Clapper", "Donn Cantrell"])
        expected = {  # declarado, vivo, sem desfecho, esperado, taxa oficial, com sem desfecho
            "Cassey Cress": (263367, 121303, 53, 43450, "62,0%", "50,8%"),
            "Daniell Hammack": (253368, 106459, 47, 42162, "59,5%", "46,8%"),
            "Boris Faz": (180676, 82913, 38, 25431, "63,2%", "49,1%"),
            "Reed Clapper": (76586, 76586, 0, 25869, "66,0%", "66,0%"),
            "Donn Cantrell": (50843, 50843, 0, 16902, "56,8%", "56,8%"),
        }
        for r in rows:
            dv, lv, st, ev, off, ws = expected[r["name"]]
            self.assertEqual((r["declared_value"], r["live_value"], r["stale_count"]), (dv, lv, st))
            self.assertEqual(round(r["expected_30d"]), ev)
            self.assertEqual((fmt.pct1(r["rate_official"]), fmt.pct1(r["rate_with_stale"])), (off, ws))
            self.assertEqual(r["stale_label"], "%d sem desfecho" % st)
            if st == 0:
                self.assertEqual(r["rate_delta_points"], 0)
        dan = rows[1]
        self.assertEqual((dan["won"], dan["lost"], dan["open_count"], dan["hot_count"]), (103, 70, 85, 16))
        self.assertEqual(rows[3]["hot_count"], 9)

    def test_agenda(self):
        decision, indicator, moment = self.out["agenda"]
        self.assertEqual(decision["kind"], "decisao")
        self.assertTrue(decision["highlight"])
        self.assertEqual(decision["title"], "138 deals sem desfecho esperam uma decisão.")
        self.assertEqual(decision["body"], "Cassey (53), Daniell (47) e Boris (38) concentram todos. Peça uma "
                                           "decisão por deal: confirmar com o cliente ou encerrar.")
        self.assertEqual((decision["link_label"], decision["link_target"]), ("Ver os 138 deals", "sem_desfecho"))
        self.assertEqual(indicator["title"], "A taxa oficial deixa de fora 138 deals sem desfecho.")
        self.assertEqual(indicator["body"], "Cassey, Daniell e Boris perdem de 11 a 14 pontos de taxa de ganho "
                                            "quando esses deals entram na conta. Reed e Donn não têm nenhum, "
                                            "e a deles não muda. A conta de cada um está na coluna Taxa de "
                                            "ganho.")
        # a conta está na tabela da própria tela: o cartão não promete outra
        self.assertEqual((indicator["link_label"], indicator["link_target"]), (None, None))
        self.assertEqual(moment["title"], "É mês de fechar: 55 deals quentes no time.")
        self.assertEqual(moment["body"], "A receita esperada em 30 dias é US$ 153.815. "
                                         "Daniell e Cassey concentram 31 desses deals.")
        self.assertEqual((moment["link_label"], moment["link_target"]), ("Ver os 55", "quentes"))

    def test_messages(self):
        msgs = self.out["messages"]
        self.assertEqual([m["seller"] for m in msgs], [r["name"] for r in self.out["rows"]])
        self.assertEqual(msgs[1]["text"],
                         "Daniell, bom dia. Dezembro é mês de fechar. Seus 3 deals de maior prioridade esta "
                         "semana: #LFI3BGEE (GTX Plus Pro, 73 dias), #HF1GSBT4 (GTX Plus Pro, 102 dias) e "
                         "#9DY57A6F (GTX Pro, 82 dias). Você também tem 47 deals abertos há mais de 138 dias. "
                         "Comece pelos 10 de maior valor e me diga até sexta quais seguem de pé e quais vamos "
                         "encerrar.")
        self.assertTrue(msgs[3]["text"].endswith("Você não tem deal sem desfecho: siga a ordem do score."))
        self.assertEqual((msgs[1]["first_name"], msgs[1]["initials"]), ("Daniell", "DH"))


class TeamScopesTest(unittest.TestCase):
    def test_company(self):
        out = team(DS, REF)
        s = out["summary"]
        self.assertEqual(out["scope"]["title"], "Empresa")
        self.assertEqual((s["seller_count"], s["open_count"], s["live_count"], s["stale_count"]), (30, 2078, 1299, 779))
        self.assertEqual((s["declared_value"], s["live_value"], s["stale_value"]), (5006104, 2945683, 2060421))
        self.assertEqual(round(s["expected_30d"]), 929174)
        self.assertIn("na empresa", out["agenda"][2]["title"])

    def test_regions(self):
        for name, code, opened, stale in (("Central", "Central", 598, 0), ("Leste", "East", 579, 291),
                                          ("west", "West", 901, 488)):
            out = team(DS, REF, region=name)
            self.assertEqual(out["scope"]["region"], code)
            self.assertEqual((out["summary"]["open_count"], out["summary"]["stale_count"]), (opened, stale))
            self.assertIn("na regional", out["agenda"][2]["title"])
            self.assertTrue(all(m["region"] == code for m in out["options"]["managers"]))
        central = team(DS, REF, region="Central")
        self.assertEqual(central["agenda"][0]["title"], "Nenhum deal sem desfecho na regional.")
        self.assertEqual(central["agenda"][0]["body"], "Ninguém tem deal aberto há mais de 138 dias.")
        self.assertFalse(central["agenda"][0]["highlight"])

    def test_single_seller(self):
        darcel = team(DS, REF, seller="Darcel Schlecht")
        r = darcel["rows"][0]
        self.assertEqual((r["open_count"], r["hot_count"], r["stale_count"]), (118, 26, 0))
        self.assertEqual((r["declared_value"], r["live_value"], round(r["expected_30d"])), (398189, 398189, 106743))
        self.assertEqual(darcel["scope"]["title"], "Carteira de Darcel Schlecht")
        self.assertEqual(len(darcel["options"]["sellers"]), 30)
        reed = team(DS, REF, manager="Rocco Neubert", seller="reed clapper")["rows"][0]
        self.assertEqual((reed["open_count"], reed["hot_count"], reed["declared_value"]), (26, 9, 76586))
        dan = team(DS, REF, seller="Daniell Hammack")
        self.assertEqual(dan["agenda"][0]["body"], "Todos são de Daniell. Peça uma decisão por deal: "
                                                   "confirmar com o cliente ou encerrar.")
        self.assertEqual(dan["agenda"][1]["body"], "Daniell perde 13 pontos de taxa de ganho quando esses "
                                                   "deals entram na conta. A conta está na coluna Taxa de ganho.")

    def test_indicator_points_match_the_table(self):
        # 62,9% -> 48,4%: a tabela mostra 14,5 pontos; a diferença sem arredondar (14,46) daria 14 no cartão
        d = date(2017, 12, 25)
        elease = team(DS, d, seller="Elease Gluck")
        row = elease["rows"][0]
        self.assertEqual((round(row["rate_official"], 3), round(row["rate_with_stale"], 3)), (0.629, 0.484))
        self.assertLess(row["rate_delta_points"], 14.5)
        self.assertEqual(elease["agenda"][1]["body"], "Elease perde 15 pontos de taxa de ganho quando esses deals "
                                                      "entram na conta. A conta está na coluna Taxa de ganho.")

    def test_errors(self):
        with self.assertRaisesRegex(ValueError, "não é gestor da regional Oeste"):
            team(DS, REF, manager="Rocco Neubert", region="Oeste")
        with self.assertRaisesRegex(ValueError, "não é do time de Rocco Neubert"):
            team(DS, REF, manager="Rocco Neubert", seller="Darcel Schlecht")
        with self.assertRaisesRegex(ValueError, "não é da regional Leste"):
            team(DS, REF, region="East", seller="Darcel Schlecht")
        with self.assertRaisesRegex(ValueError, "Carl Lin só está no cadastro: não tem deals na base"):
            team(DS, REF, seller="Carl Lin")
        with self.assertRaisesRegex(ValueError, "Gestor não encontrado"):
            team(DS, REF, manager="Fulano")
        with self.assertRaisesRegex(ValueError, "Regional não encontrada"):
            team(DS, REF, region="Norte")

    def test_accepts_empty_filters(self):
        self.assertEqual(team(DS, REF, manager="", region="", seller="")["summary"]["open_count"], 2078)

    def test_late_december_is_not_called_closing_month(self):
        # 25 dez: último mês, mas a melhor faixa fecha só 22% e faltam 6 dias
        out = team(DS, date(2017, 12, 25), manager="Rocco Neubert")
        self.assertTrue(out["agenda"][2]["title"].startswith("Fim de trimestre"))
        for m in out["messages"]:
            self.assertNotIn("mês de fechar", m["text"])
            self.assertIn("Dezembro fecha o trimestre.", m["text"])


class TeamTextsTest(unittest.TestCase):
    """Em várias datas e escopos, os textos continuam coerentes com os números."""

    DATES = (date(2017, 7, 3), date(2017, 10, 2), REF, date(2017, 12, 25))
    SCOPES = ({}, {"region": "Central"}, {"region": "East"}, {"manager": "Rocco Neubert"},
              {"manager": "Cara Losch"}, {"manager": "Melvin Marxen"}, {"seller": "Garret Kinder"},
              {"seller": "Darcel Schlecht"}, {"seller": "Daniell Hammack"})

    def test_all(self):
        for d in self.DATES:
            snap = core.snapshot(DS, d)
            for kw in self.SCOPES:
                with self.subTest(date=d, scope=kw):
                    out = team(DS, d, **kw)
                    self._check(out, snap)

    def _check(self, out, snap):
        s = out["summary"]
        rows = out["rows"]
        self.assertEqual(s["open_count"], sum(r["open_count"] for r in rows))
        self.assertEqual(s["stale_count"], sum(r["stale_count"] for r in rows))
        self.assertEqual(s["hot_count"], sum(r["hot_count"] for r in rows))
        self.assertEqual(rows, sorted(rows, key=lambda r: (-r["declared_value"], r["name"])))
        texts = [c["title"] for c in out["agenda"]] + [c["body"] for c in out["agenda"]]
        texts += [m["text"] for m in out["messages"]]
        for t in texts:
            self.assertNotRegex(t, r"\b1 deals\b|\b0 deals\b|Outros 1 |\b1 pontos\b|  |\.\.")
            self.assertNotIn("None", t)
        decision, indicator, moment = out["agenda"]
        if s["stale_count"]:
            self.assertTrue(decision["title"].startswith(fmt.plural(s["stale_count"], "deal")))
        else:
            self.assertTrue(decision["title"].startswith("Nenhum deal sem desfecho"))
        self.assertTrue(moment["title"].startswith(core.phase_title(snap)))
        for t in texts:
            self.assertNotRegex(t, r"parad|sem resposta")
        for r, m in zip(rows, out["messages"]):
            live = [x for x in snap.by_seller.get(r["name"], ()) if not x.stale]
            listed = re.findall(r"#(\w+)", m["text"])
            self.assertEqual(listed, [x.deal.id for x in live[:3]])
            if r["stale_count"] == 0:
                self.assertNotIn("há mais de", m["text"])
            if r["stale_count"] < 10:
                self.assertNotIn("Comece pelos 10", m["text"])


if __name__ == "__main__":
    unittest.main()
