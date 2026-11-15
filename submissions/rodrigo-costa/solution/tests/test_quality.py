from __future__ import annotations

import importlib.util
import json
import unittest
from datetime import date

from engine import facts, quality
from engine.core import available_dates, get_dataset, snapshot, summarize

D = date(2017, 12, 4)
HAS_PROOF = importlib.util.find_spec("engine.proof") is not None


class DataQualityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = get_dataset()
        cls.page = quality.data_quality(cls.ds, D)
        cls.items = {i["key"]: i for i in cls.page["items"]}

    def test_serializable(self):
        json.dumps(self.page, allow_nan=False)  # o servidor usa allow_nan=False

    def test_coverage(self):
        cov = self.page["coverage"]
        self.assertEqual(cov[0]["value"], "8.800 deals")
        self.assertEqual(cov[0]["detail"], "4.238 ganhos · 2.473 perdidos · 1.589 em negociação · 500 em prospecção")
        self.assertEqual((cov[1]["value"], cov[1]["detail"]), ("85 clientes", "todos com pelo menos um deal fechado"))
        self.assertEqual((cov[2]["value"], cov[2]["detail"]), ("35 vendedores", "30 com deals e 5 só no cadastro"))
        self.assertEqual((cov[3]["value"], cov[3]["detail"]), ("14 meses", "de 20 out 2016 a 31 dez 2017"))

    def test_items(self):
        self.assertEqual([i["scope"] for i in self.page["items"]],
                         ["base inteira", "base inteira", "na data", "base inteira", "na data"])
        early = self.items["early_engage"]
        self.assertEqual(early["number"], "1.185 deals")
        self.assertEqual(early["title"], "A base não registra fechamento antes de 1 mar 2017")
        self.assertIn("a partir de 6 mar 2017", early["action"])
        acc = self.items["open_account"]
        self.assertEqual(acc["number"], "68%")
        self.assertEqual(acc["body"], "No fim da base, 68% dos deals abertos não têm cliente. Nos que têm, a regional do vendedor "
                                      "bate com a do cliente em 32% dos casos. Nos fechados, em 95%.")
        leak = self.items["account_leak"]
        self.assertEqual(leak["number"], "0 de 549")
        self.assertEqual(leak["body"], "Todo deal fechado tem cliente. Em 4 dez 2017, nenhum dos 549 deals vivos sem "
                                       "cliente fechou até o fim da base. Dos 750 com cliente, 404 viraram venda.")
        quarter = self.items["quarter_rhythm"]
        self.assertEqual(quarter["number"], "0 de 3.438")
        # o texto diz de onde vem o 3.438: três dias somados, com o mesmo deal podendo contar mais de uma vez
        self.assertEqual(quarter["body"], "Nos dias 1 abr 2017, 1 jul 2017 e 1 out 2017, havia 673, 1.015 e 1.750 "
                                          "deals abertos com mais de 30 dias (3.438 somando os dias; o mesmo deal "
                                          "pode contar mais de uma vez). Nenhum deles fechou naquele mês. No último "
                                          "mês do trimestre, 81% dos fechamentos são venda. Nos outros meses, 52%.")
        cycle = self.items["max_cycle"]
        self.assertEqual((cycle["number"], cycle["title"]), ("138 dias", "Nenhum deal fechou depois de 138 dias"))
        self.assertEqual(cycle["body"], "É o maior ciclo da base, ganho ou perdido. Em 4 dez 2017, 779 dos 2.078 "
                                        "deals abertos (37%) já tinham passado disso.")

    def test_base_numbers(self):
        b = facts.base_facts(self.ds)
        early = b["early"]
        self.assertEqual(sum(1 for x in early if x.close_date is not None), 972)
        self.assertEqual(sum(1 for x in early if x.close_date is None), 213)
        self.assertEqual((len(b["unfinished"]), b["open_no_account"], b["open_with_account"], b["open_home"]),
                         (2089, 1425, 664, 211))
        self.assertEqual((b["closed_with_account"], b["closed_home"]), (6711, 6348))
        self.assertEqual([r[1] for r in b["quarter_rows"]], [673, 1015, 1750])
        self.assertEqual(sum(r[2] for r in b["quarter_rows"]), 0)
        self.assertEqual({k: v[1] for k, v in b["by_month"].items()}, {0: 1779, 1: 2358, 2: 2574})
        self.assertEqual(b["max_cycle"], 138)

    def test_fields_regions_fixes(self):
        texts = {f["field"]: f["text"] for f in self.page["fields"]}
        self.assertEqual(texts["Cliente"], "Vazio em 1.425 dos 8.800 deals, todos abertos.")
        self.assertTrue(texts["Data de entrada"].startswith("Vazia nos 500 deals em prospecção."))
        self.assertEqual(texts["Data de fechamento"], "Vazia nos 2.089 deals abertos, como esperado.")
        self.assertTrue(texts["Valor fechado"].startswith("Só nas 4.238 vendas."))
        rows = {r["region"]: (r["open_count"], r["stale_count"]) for r in self.page["regions"]["rows"]}
        self.assertEqual(rows, {"Central": (598, 0), "East": (579, 291), "West": (901, 488)})
        self.assertTrue(self.page["regions"]["sentence"].startswith(
            "A Central só tem deals abertos recentes, e os 500 em prospecção são todos dela. Por isso"))
        self.assertEqual(self.page["fixes"]["text"], "Três nomes vinham com grafia errada e foram corrigidos: "
                                                     "GTXPro, technolgy e Philipines.")

    def test_other_dates(self):
        for d in available_dates(self.ds):
            page = quality.data_quality(self.ds, d)
            json.dumps(page)
            region = page["regions"]
            central = next(r for r in region["rows"] if r["region"] == "Central")
            if central["stale_count"]:
                self.assertNotIn("só tem deals abertos recentes", region["sentence"])
                self.assertIn("são todos da Central", region["sentence"])
                # sem a Central "limpa", a regra não decorre das partes: nada de "Por isso"
                self.assertNotIn("Por isso", region["sentence"])
            for item in page["items"]:
                for text in (item["title"], item["body"], item["action"]):
                    self.assertNotIn("  ", text)
                    self.assertTrue(text.strip())
        late = quality.data_quality(self.ds, date(2017, 12, 25))
        self.assertIn("vai de 67% (Leste) a 77% (Central)", late["regions"]["sentence"])
        first = {i["key"]: i for i in quality.data_quality(self.ds, date(2017, 7, 3))["items"]}
        self.assertIn("Em 3 jul 2017, 158 dos 1.714 deals abertos (9%)", first["max_cycle"]["body"])


class SourcesAndMetaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = get_dataset()

    def test_sources(self):
        s = quality.sources(self.ds)
        json.dumps(s)
        self.assertEqual(s["alert"], "Tela apenas para referência, os dados vêm da base fornecida para o desafio "
                                     "e não de alguma integração.")
        files = s["active"]["files"]
        self.assertEqual([f["count_label"] for f in files], ["8.800 deals", "85 clientes", "7 produtos", "35 vendedores"])
        self.assertEqual(files[0]["description"], "Oportunidades, de out 2016 a dez 2017")
        self.assertEqual([c["initials"] for c in s["crms"]["items"]], ["SF", "HS", "PD", "RD", "ZH", "DY"])
        self.assertEqual(len(s["requirements"]["items"]), 5)
        self.assertTrue(s["requirements"]["items"][1]["text"].startswith("Falta em 68% dos deals abertos no fim desta base"))

    def test_meta(self):
        m = quality.meta(self.ds)
        json.dumps(m)
        ds_ = m["dataset"]
        self.assertEqual(ds_["by_stage"], {"Won": 4238, "Lost": 2473, "Engaging": 1589, "Prospecting": 500})
        self.assertEqual((ds_["deals"], ds_["accounts"], ds_["sellers_total"], ds_["sellers_with_deals"],
                          ds_["managers"], ds_["regions"]), (8800, 85, 35, 30, 6, 3))
        self.assertEqual((ds_["first_engage"], ds_["last_engage"], ds_["first_close"], ds_["last_close"]),
                         ("2016-10-20", "2017-12-27", "2017-03-01", "2017-12-31"))
        self.assertEqual(ds_["period_label"], "de out 2016 a dez 2017")
        self.assertEqual(m["default_date"], "2017-12-04")
        self.assertEqual(len(m["dates"]), 26)
        self.assertEqual(m["dates"][0]["month_label"], "jul")
        self.assertEqual(sum(1 for x in m["dates"] if x["in_proof"]), 22)
        self.assertEqual(len(m["sellers"]), 30)
        rocco = next(x for x in m["managers"] if x["name"] == "Rocco Neubert")
        self.assertEqual(rocco["team"], ["Boris Faz", "Cassey Cress", "Daniell Hammack", "Donn Cantrell",
                                         "Reed Clapper"])
        self.assertEqual(rocco["region_label"], "Leste")
        self.assertEqual(len(m["products"]), 7)

    @unittest.skipUnless(HAS_PROOF, "engine.proof ainda não existe")
    def test_in_proof_matches_proof(self):
        from engine.proof import proof
        tested = {x["date"] for x in proof(self.ds)["per_date"]}
        flagged = {x["iso"] for x in quality.meta(self.ds)["dates"] if x["in_proof"]}
        self.assertEqual(tested, flagged)


class LoginTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = get_dataset()
        cls.page = quality.login(cls.ds, D)

    def test_suggestions(self):
        s = self.page["suggestions"]
        self.assertEqual([x["name"] for x in s], ["Daniell Hammack", "Reed Clapper", "Darcel Schlecht"])
        self.assertEqual([x["tag"] for x in s], ["Carteira com deals sem desfecho", "Carteira em dia",
                                                 "Maior carteira"])
        self.assertEqual([x["descriptor"] for x in s], ["Leste · 47 sem desfecho", "Leste · nenhum deal sem desfecho",
                                                        "Central · 118 vivos e 111 em prospecção"])

    def test_lists(self):
        self.assertEqual(len(self.page["sellers"]), 30)
        managers = {m["name"]: m for m in self.page["managers"]}
        self.assertEqual(len(managers), 6)
        self.assertEqual({k: v["region_label"] for k, v in managers.items()},
                         {"Cara Losch": "Leste", "Celia Rouche": "Oeste", "Dustin Brinkmann": "Central",
                          "Melvin Marxen": "Central", "Rocco Neubert": "Leste", "Summer Sewald": "Oeste"})
        rocco = managers["Rocco Neubert"]
        self.assertEqual((rocco["team_size"], rocco["open_count"], rocco["stale_count"]), (5, 307, 138))
        self.assertEqual(rocco["descriptor"], "Leste · 5 vendedores · 138 sem desfecho")
        garret = next(x for x in self.page["sellers"] if x["name"] == "Garret Kinder")
        self.assertEqual(garret["descriptor"], "Leste · nenhum deal sem desfecho")

    def test_panel(self):
        p = self.page["panel"]
        self.assertEqual((p["declared_value"], p["live_value"], p["open_count"], p["stale_count"], p["max_cycle"]),
                         (5006104, 2945683, 2078, 779, 138))
        self.assertEqual(p["headline_1"], "US$ 5,0 milhões em negociação.")
        self.assertEqual(p["headline_2"], "US$ 2,9 milhões vivos.")
        self.assertEqual(p["sentence"], "Em 4 dez 2017, a data em que o app abre, 779 dos 2.078 deals em "
                                        "negociação já tinham passado de 138 dias. Nenhum deal desta empresa fechou "
                                        "depois desse prazo.")
        self.assertEqual(p["stats"][0], {"value": "8.800", "label": "oportunidades na base inteira, até 31 dez 2017"})
        self.assertEqual(p["stats"][2]["label"], "de receita contra ordenar por valor, já tirando os sem desfecho")
        self.assertEqual(p["stats"][1], {"value": "22", "label": "segundas-feiras testadas no passado"})

    @unittest.skipUnless(HAS_PROOF, "engine.proof ainda não existe")
    def test_panel_lift(self):
        self.assertEqual(self.page["panel"]["stats"][2]["value"], "+22%")

    def test_other_dates(self):
        for d in (date(2017, 7, 3), date(2017, 10, 2), date(2017, 12, 25)):
            page = quality.login(self.ds, d)
            json.dumps(page)
            self.assertNotIn("a data em que o app abre", page["panel"]["sentence"])
            self.assertEqual(page["panel"]["stats"][0]["value"], "8.800")
        # "Maior carteira" só quando é mesmo o maior valor declarado na data (em 3 jul e 25 dez, é a Markita)
        for d in available_dates(self.ds):
            snap = snapshot(self.ds, d)
            declared = {n: summarize(v)["declared_value"] for n, v in snap.by_seller.items()}
            for x in quality.login(self.ds, d)["suggestions"]:
                is_biggest = declared[x["name"]] == max(declared.values())
                self.assertEqual(x["tag"] == "Maior carteira", is_biggest, (d, x))
        tags = {d: quality.login(self.ds, d)["suggestions"][2]["tag"] for d in (date(2017, 7, 3), date(2017, 12, 25))}
        self.assertEqual(tags, {date(2017, 7, 3): "Carteira em dia",
                                date(2017, 12, 25): "Carteira com deals sem desfecho"})
        late = quality.login(self.ds, date(2017, 12, 25))
        darcel = next(x for x in late["sellers"] if x["name"] == "Darcel Schlecht")
        self.assertTrue(darcel["stale_count"] > 0)
        self.assertTrue(darcel["descriptor"].endswith("sem desfecho"))


if __name__ == "__main__":
    unittest.main()
