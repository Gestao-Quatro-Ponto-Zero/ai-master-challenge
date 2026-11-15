from __future__ import annotations

import json
import unittest
from datetime import date

from engine import core, model_page

REF = date(2017, 12, 4)
DS = core.get_dataset()


def _proof_available() -> bool:
    try:
        from engine.proof import proof
        proof(DS)
        return True
    except Exception:
        return False


PROOF_OK = _proof_available()


def _model(d: date = REF, viewer=None):
    if not PROOF_OK:
        raise unittest.SkipTest("engine.proof ainda não disponível")
    return model_page.score_model(DS, d, viewer)


class ExampleTest(unittest.TestCase):
    def test_viewer_top_deal(self):
        e = _model(viewer="Daniell Hammack")["example"]
        self.assertEqual((e["id"], e["product"], e["price"], e["age_days"], e["score"]),
                         ("LFI3BGEE", "GTX Plus Pro", 5482, 73, 98))
        self.assertEqual((e["y"], e["n"], e["level"], e["band"], e["band_label"]), (196, 391, "semana", "quente", "Quente"))
        self.assertTrue(e["is_viewer"])
        self.assertIsNone(e["note"])
        self.assertAlmostEqual(e["expected_value"], round(196 / 391.0 * 5482, 2))
        self.assertEqual(e["steps"][2], "Receita esperada: 196 ÷ 391 × US$ 5.482 (preço de tabela) = US$ 2.748.")
        self.assertIn("98% dos 1.299 deals vivos", e["steps"][3])

    def test_company_top_without_viewer(self):
        snap = core.snapshot(DS, REF)
        e = _model()["example"]
        self.assertEqual(e["id"], snap.live[0].deal.id)
        self.assertFalse(e["is_viewer"])
        self.assertIsNone(e["note"])

    def test_seller_only_in_registry_is_rejected(self):
        # mesma regra das telas de vendedor e do time: quem só está no cadastro dá erro
        with self.assertRaisesRegex(ValueError, "Mei-Mei Johns só está no cadastro"):
            _model(viewer="Mei-Mei Johns")

    def test_manager_uses_team(self):
        e = _model(viewer="rocco neubert")["example"]
        self.assertTrue(e["is_viewer"])
        self.assertIn(e["seller"], DS.managers["Rocco Neubert"])

    def test_unknown_viewer(self):
        if not PROOF_OK:
            self.skipTest("engine.proof ainda não disponível")
        with self.assertRaisesRegex(ValueError, "não encontrad"):
            model_page.score_model(DS, REF, "Fulano de Tal")


class TableTest(unittest.TestCase):
    def test_reference_table(self):
        r = _model()
        table = r["table"]
        self.assertEqual([t["label"] for t in table], list(core.AGE_BAND_LABELS))
        self.assertEqual([t["n"] for t in table], [989, 812, 786, 450, 391, 409, 344, 220, 133, 522])
        self.assertEqual([t["chance_label"] for t in table],
                         ["17%", "6%", "10%", "35%", "50%", "51%", "49%", "35%", "19%", "0%"])
        self.assertTrue(all(t["level"] == "semana" for t in table))
        self.assertEqual([t["label"] for t in table if t["in_window"]], ["61–75", "76–90", "91–105"])
        self.assertEqual([t["label"] for t in table if t["stale"]], ["139+"])
        self.assertEqual((table[4]["y"], table[9]["to_days"], table[9]["from_days"]), (196, None, 139))
        self.assertEqual(r["table_sentence"], "Tabela usada na semana de 4 dez 2017. A janela boa vai de 61 a 105 dias.")
        self.assertEqual(r["max_cycle"], 138)

    def test_training_reference(self):
        t = _model()["training"]
        self.assertEqual([m["iso"] for m in t["mondays"]], ["2017-03-06", "2017-06-05", "2017-09-04"])
        self.assertEqual(t["sentence"], "Embaixo de cada faixa, em dias de idade, está o número de casos que formam "
                                        "a taxa. Eles vêm da mesma semana dos três trimestres anteriores "
                                        "(6 mar, 5 jun e 4 set 2017).")

    def test_training_first_date_with_fallback(self):
        t = _model(date(2017, 7, 3))["training"]
        self.assertEqual([m["iso"] for m in t["mondays"]], ["2017-04-03"])
        self.assertIn("da mesma semana do trimestre anterior (3 abr 2017).", t["sentence"])
        self.assertIn("Nas faixas 91–105, 106–120, 121–138 e 139+, a semana tinha menos de 30 casos; "
                      "a taxa usa o mesmo mês do trimestre.", t["sentence"])

    def test_training_two_quarters(self):
        t = _model(date(2017, 10, 2))["training"]
        self.assertIn("dos dois trimestres anteriores (3 abr e 3 jul 2017).", t["sentence"])
        self.assertNotIn("Na faixa", t["sentence"])

    def test_bands(self):
        b = _model()["bands"]
        self.assertEqual([x["rule"] for x in b["score"]], ["score 80 ou mais", "de 40 a 79", "abaixo de 40"])
        self.assertEqual(b["stale"]["rule"], "mais de 138 dias")
        self.assertTrue(b["stale"]["text"].startswith("Antes de 4 dez 2017, nenhum deal fechou com mais de 138 dias"))

    def test_all_dates_serialize(self):
        if not PROOF_OK:
            self.skipTest("engine.proof ainda não disponível")
        for d in core.available_dates(DS):
            r = model_page.score_model(DS, d, "Garret Kinder")
            json.dumps(r, ensure_ascii=False)
            self.assertIsNotNone(r["example"])
            self.assertTrue(r["example"]["steps"][3].endswith("score %d." % r["example"]["score"]))


class ProofBlockTest(unittest.TestCase):
    def test_proof_sentence(self):
        p = _model()["proof"]
        self.assertEqual(p["n_dates"], 22)
        self.assertGreater(p["gain_vs_value_only"], p["gain_vs_value_no_stale"])
        self.assertIn("Em 22 segundas-feiras", p["sentence"])
        self.assertIn("os 10 primeiros do score", p["sentence"])


class SignalsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {r["key"]: r for r in model_page.tested_signals(DS)}

    def test_shape(self):
        self.assertEqual(list(self.rows), ["revenue", "history", "product", "groups", "seller", "account_field"])
        for r in self.rows.values():
            self.assertEqual(set(r), {"key", "signal", "finding", "decision", "evidence"})
            self.assertTrue(r["evidence"])

    def test_revenue(self):
        r = self.rows["revenue"]
        self.assertIn("63,2%, 63,0% e 63,2% de ganho", r["evidence"])
        self.assertIn("11,1% no terço menor e 6,4% no maior", r["evidence"])

    def test_history(self):
        e = self.rows["history"]["evidence"]
        self.assertIn("22,3% quando o vendedor nunca tinha vendido para o cliente e 3,6% quando já tinha", e)
        self.assertIn("Entre os que fecharam desse mesmo grupo, a taxa de ganho é 59,5% com venda anterior "
                      "(2.305 deals) e 60,9% sem (729 deals)", e)
        self.assertIn("31,8% dos casos; no fechado, em 94,6%", e)

    def test_product(self):
        r = self.rows["product"]
        self.assertIn("entre 39 e 52 dias", r["finding"])
        self.assertIn("Só o GTK 500 foge (69 dias), mas tem apenas 9 vendas.", r["finding"])
        self.assertIn("entraram de 1 mar a 14 ago 2017", r["evidence"])

    def test_groups(self):
        e = self.rows["groups"]["evidence"]
        self.assertIn("setor de 61,2% a 64,8%; regional de 62,6% a 63,9%; gestor de 62,1% a 64,4%", e)

    def test_seller(self):
        e = self.rows["seller"]["evidence"]
        self.assertIn("de 55,0% a 70,4% entre os 30 vendedores (empresa: 63,2%)", e)
        self.assertIn("Só 2 vendedores ficam longe da média da empresa", e)
        self.assertIn("o acaso sozinho já daria 1 ou 2 casos assim", e)
        self.assertNotIn("5 vezes em 100", e)
        self.assertNotIn("cabem no acaso", self.rows["seller"]["finding"])

    def test_account_field(self):
        r = self.rows["account_field"]
        self.assertIn("só um em cada três", r["finding"])
        self.assertIn("todos os 6.711 fechados têm cliente; dos 2.089 abertos, 664 (31,8%)", r["evidence"])
        self.assertIn("nenhum dos 12.772 casos de deal vivo sem cliente virou venda em 30 dias", r["evidence"])
        self.assertIn("22,1%", r["evidence"])

    def test_cached_copy(self):
        a = model_page.tested_signals(DS)
        a[0]["finding"] = "x"
        self.assertNotEqual(model_page.tested_signals(DS)[0]["finding"], "x")


if __name__ == "__main__":
    unittest.main()
