from __future__ import annotations

import json
import threading
import unittest
from datetime import date

from engine import core, proof

REF = date(2017, 12, 4)
DS = core.get_dataset()
BY_ID = {x.id: x for x in DS.deals}
SCORE_IDS = ["LFI3BGEE", "HF1GSBT4", "9DY57A6F", "HP9TUR60", "XZKZYO55", "IDKBZCAF", "YPSXMDRH", "D3HUUVPL",
             "S53EVWFC", "5J7T0GZU"]
VALUE_IDS = ["UAE5ZC7O", "QM6VR1H5", "M16D8PYH", "DZ57QIQN", "RQULJHTU", "FM505XD5", "0KEO3OP7", "Q2CLAKLM",
             "KJHM27ZM", "HEWKNHTH"]


class ProofTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = proof.proof(DS)

    def test_shape_and_counts(self):
        p = self.p
        json.dumps(p)
        self.assertEqual((p["n_dates"], p["n_lists"], p["top_n"]), (22, 659, 10))
        self.assertEqual((p["first_date"]["iso"], p["last_date"]["iso"]), ("2017-07-03", "2017-11-27"))
        self.assertEqual(p["period_label"], "de 3 jul a 27 nov 2017")
        self.assertEqual(len(p["per_date"]), 22)
        self.assertEqual(sum(r["lists"] for r in p["per_date"]), 659)
        first = p["per_date"][0]
        self.assertEqual((first["date"], first["label"], first["month_label"]), ("2017-07-03", "3 jul", "jul"))

    def test_rule_totals(self):
        r = self.p["rules"]
        self.assertAlmostEqual(r["value_only"]["revenue"] / 1e6, 4.92, delta=0.03)
        self.assertAlmostEqual(r["value_no_stale"]["revenue"] / 1e6, 5.71, delta=0.03)
        self.assertAlmostEqual(r["score"]["revenue"] / 1e6, 7.00, delta=0.03)
        self.assertAlmostEqual(r["value_only"]["wins_per_list"], 1.33, delta=0.01)
        self.assertAlmostEqual(r["value_no_stale"]["wins_per_list"], 1.60, delta=0.01)
        self.assertAlmostEqual(r["score"]["wins_per_list"], 2.18, delta=0.01)
        self.assertGreater(r["oracle"]["revenue"], r["score"]["revenue"])
        self.assertLess(r["random"]["revenue"], r["value_only"]["revenue"])

    def test_gains(self):
        g = self.p["gains"]
        self.assertAlmostEqual(g["vs_value_only"], 0.42, delta=0.01)
        self.assertAlmostEqual(g["vs_value_no_stale"], 0.225, delta=0.005)
        self.assertAlmostEqual(g["vs_value_no_stale_newest"], 0.20, delta=0.01)
        w = self.p["dates_won"]
        self.assertEqual((w["vs_value_only"]["won"], w["vs_value_only"]["total"]), (22, 22))
        self.assertEqual(w["vs_value_no_stale"]["won"], 20)
        self.assertEqual(w["vs_value_no_stale"]["lost_labels"], ["30 out", "6 nov"])

    def test_periods(self):
        jul, out = self.p["by_period"]
        self.assertEqual((jul["key"], jul["label"], jul["n_dates"]), ("jul-set", "julho a setembro", 13))
        self.assertEqual((out["key"], out["label"], out["n_dates"]), ("out-nov", "outubro e novembro", 9))
        self.assertAlmostEqual(jul["gain_vs_value_no_stale"], 0.30, delta=0.01)
        self.assertAlmostEqual(out["gain_vs_value_no_stale"], 0.11, delta=0.01)
        self.assertAlmostEqual(out["gain_vs_value_no_stale_newest"], -0.01, delta=0.015)

    def test_auc_sensitivity_peak(self):
        a = self.p["auc"]
        self.assertNotIn("score", a)  # a AUC de 0,780 é da chance, não do score
        self.assertAlmostEqual(a["chance"], 0.780, delta=0.001)
        self.assertAlmostEqual(a["expected_value"], 0.7057, delta=0.0005)
        self.assertAlmostEqual(a["age_only"], 0.693, delta=0.001)
        self.assertAlmostEqual(a["price"], 0.504, delta=0.001)
        self.assertEqual((a["pairs"], a["positives"]), (50138, 5982))
        s = self.p["sensitivity"]
        self.assertEqual((s["top5"]["n_lists"], s["top20"]["n_lists"]), (660, 646))
        self.assertGreater(s["top5"]["gain_vs_value_no_stale"], 0)
        self.assertGreater(s["top20"]["gain_vs_value_no_stale"], 0)
        peak = self.p["peak"]
        self.assertEqual((peak["date"], peak["label"], peak["lists"]), ("2017-09-04", "4 set", 30))
        self.assertAlmostEqual(peak["wins"], 108, delta=1)

    def test_sentences(self):
        s = self.p["sentences"]
        self.assertEqual(s["headline"], "+22%")
        self.assertEqual(s["headline_detail"], "de receita em 30 dias contra ordenar por valor já sem os deals sem "
                                               "desfecho. Contra ordenar só por valor, +42%.")
        self.assertEqual(s["method"], "Soma das 659 listas de 10 deals, em 22 segundas-feiras de 3 jul a 27 nov "
                                      "2017. A cada 10 indicados, 2,2 viraram venda pelo score, 1,6 pela regra "
                                      "simples e 1,3 só por valor.")
        titles = [x["title"] for x in s["limits"]]
        self.assertEqual(titles, ["Vence em 20 de 22 semanas", "Mais forte de julho a setembro",
                                  "Mede a ordem, não o efeito", "Conferida duas vezes"])
        self.assertEqual(s["limits"][0]["body"], "Contra a regra simples, o score perdeu em 30 out e 6 nov. "
                                                 "Contra ordenar só por valor, venceu nas 22.")
        jul, out = self.p["by_period"]
        self.assertEqual(s["limits"][1]["body"], (
            "+%s no 3º trimestre e +%s em outubro e novembro. Se a regra simples puser o deal mais novo na frente, "
            "nesses dois meses quase empata: o score fica 1%% abaixo." % (
                proof.fmt.pct(jul["gain_vs_value_no_stale"]), proof.fmt.pct(out["gain_vs_value_no_stale"]))))

    def test_cached_and_thread_safe(self):
        fresh = core.load_dataset()  # base nova: o cache dela começa vazio e as threads disputam o cálculo
        results = []
        threads = [threading.Thread(target=lambda: results.append(proof.proof(fresh))) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(results), 4)
        self.assertTrue(all(r is results[0] for r in results))
        self.assertIs(proof.proof(fresh), results[0])
        self.assertEqual(results[0]["gains"], self.p["gains"])


class HelpersTest(unittest.TestCase):
    def test_expected_top_splits_tie_group(self):
        snap = core.snapshot(DS, REF)
        mine = snap.by_seller["Daniell Hammack"]
        wins, revenue = proof._expected_top(mine, lambda s: (not s.stale, s.deal.price), REF, 10)
        self.assertAlmostEqual(wins, 4.27, delta=0.005)
        self.assertAlmostEqual(revenue, 21632, delta=1)
        wins_all, _ = proof._expected_top(mine, lambda s: 0, REF, len(mine))
        self.assertEqual(wins_all, sum(proof._sale(s, REF)[0] for s in mine))

    def test_auc(self):
        self.assertEqual(proof._auc([(1.0, 0), (2.0, 1)]), 1.0)
        self.assertEqual(proof._auc([(1.0, 0), (1.0, 1)]), 0.5)
        self.assertIsNone(proof._auc([(1.0, 1)]))

    def test_signed_pct(self):
        self.assertEqual(proof._signed_pct(0.42), "+42%")
        self.assertEqual(proof._signed_pct(-0.05), "-5%")
        self.assertEqual(proof._signed_pct(0.001), "0%")


class TimeMachineTest(unittest.TestCase):
    def test_daniell_reference(self):
        t = proof.time_machine(DS, REF, "daniell hammack")
        json.dumps(t)
        self.assertEqual(t["seller"]["name"], "Daniell Hammack")
        self.assertEqual(t["date"]["iso"], "2017-12-04")
        self.assertTrue(t["enough"])
        w = t["window"]
        self.assertEqual((w["days"], w["until_label"]), (27, "31 dez 2017"))
        self.assertEqual(w["sentence"], "Desfecho real até 31 dez 2017, último dia da base: 27 dias depois. "
                                        "Venda mostra o valor fechado no CRM.")
        score = t["lists"]["score"]
        self.assertEqual(score["title"], "Pelo score")
        self.assertEqual([r["id"] for r in score["rows"]], SCORE_IDS)
        self.assertEqual((score["wins"], score["revenue"], score["total_label"]), (5, 25687, "5 vendas · US$ 25.687"))
        sales = {r["id"]: (r["outcome"]["value"], r["outcome"]["date_label"]) for r in score["rows"]
                 if r["outcome"]["kind"] == "venda"}
        self.assertEqual(sales, {"HP9TUR60": (5627, "24 dez"), "XZKZYO55": (4865, "16 dez"),
                                 "YPSXMDRH": (4976, "23 dez"), "D3HUUVPL": (5255, "4 dez"),
                                 "5J7T0GZU": (4964, "14 dez")})
        row = score["rows"][3]
        self.assertEqual(row["outcome"]["label"], "Venda · US$ 5.627")
        self.assertEqual(score["rows"][0]["outcome"], {"kind": "aberto", "label": "Segue aberto", "value": None,
                                                       "date_label": None})
        self.assertNotIn("account", row)
        value = t["lists"]["value_only"]
        self.assertEqual(value["title"], "Só por valor")
        self.assertEqual([r["id"] for r in value["rows"]], VALUE_IDS)
        self.assertEqual([r["age_days"] for r in value["rows"]], [364, 334, 333, 320, 263, 240, 221, 218, 203, 169])
        self.assertTrue(all(r["stale"] for r in value["rows"]))
        self.assertEqual((value["wins"], value["revenue"], value["total_label"]), (0, 0, "0 vendas · US$ 0"))

    def test_daniell_fair(self):
        f = proof.time_machine(DS, REF, "Daniell Hammack")["fair"]
        self.assertEqual(f["oldest_first"], {"wins": 3, "revenue": 15807})
        self.assertEqual(f["newest_first"], {"wins": 6, "revenue": 29617})
        self.assertAlmostEqual(f["expected"]["wins"], 4.27, delta=0.005)
        self.assertEqual(f["title"], "E ordenando por valor, já sem os deals sem desfecho?")
        self.assertEqual(f["sentence"], (
            "Depende de quem vem primeiro entre deals do mesmo preço: 3 vendas com o mais antigo na frente, 6 com "
            "o mais novo e 4,3 em média no sorteio (%s). O score fez 5 vendas e US$ 25.687: acima da média, abaixo "
            "do melhor desempate." % proof.fmt.money(f["expected"]["revenue"])))

    def test_window_full_horizon(self):
        w = proof.time_machine(DS, date(2017, 7, 3), "Darcel Schlecht")["window"]
        self.assertEqual((w["days"], w["truncated"], w["until"]), (30, False, "2017-08-01"))
        self.assertEqual(w["sentence"], "Desfecho real nos 30 dias seguintes, até 1 ago 2017. "
                                        "Venda mostra o valor fechado no CRM.")

    def test_lists_use_only_what_was_known(self):
        d = date(2017, 10, 2)
        t = proof.time_machine(DS, d, "Reed Clapper")
        snap = core.snapshot(DS, d)
        mine = snap.by_seller["Reed Clapper"]
        self.assertEqual([r["id"] for r in t["lists"]["score"]["rows"]], [s.deal.id for s in mine[:10]])
        for r in t["lists"]["score"]["rows"] + t["lists"]["value_only"]["rows"]:
            x = BY_ID[r["id"]]
            self.assertTrue(x.is_open_at(d))
            self.assertEqual(r["age_days"], (d - x.engage_date).days)

    def test_few_deals_and_last_date(self):
        t = proof.time_machine(DS, date(2017, 12, 25), "Garret Kinder")
        self.assertFalse(t["enough"])
        self.assertEqual(len(t["lists"]["score"]["rows"]), t["open_count"])
        self.assertEqual(t["window"]["sentence"], "Desfecho real até 31 dez 2017, último dia da base: 6 dias depois. "
                                                  "Venda mostra o valor fechado no CRM.")
        self.assertEqual(t["lists"]["score"]["total_label"], "1 venda · US$ 54")
        self.assertIn("a ordem não muda o resultado: 1 venda (US$ 54)", t["fair"]["sentence"])

    def test_seller_without_deals(self):
        with self.assertRaisesRegex(ValueError, "Carl Lin só está no cadastro"):
            proof.time_machine(DS, REF, "Carl Lin")
        self.assertEqual(proof._fair((), REF, {"wins": 0, "revenue": 0})["sentence"], "Nenhum deal aberto nesta data.")

    def test_all_dates_and_sellers_serialize(self):
        for d in core.available_dates(DS):
            for name in DS.deals_by_seller:
                t = proof.time_machine(DS, d, name)
                json.dumps(t)
                self.assertTrue(t["fair"]["sentence"].endswith("."))
                self.assertLessEqual(len(t["lists"]["score"]["rows"]), 10)

    def test_note_and_errors(self):
        t = proof.time_machine(DS, REF, "Daniell Hammack")
        self.assertEqual(t["hidden_account_note"]["title"], "Por que o cliente não aparece aqui")
        with self.assertRaisesRegex(ValueError, "Vendedor não encontrado"):
            proof.time_machine(DS, REF, "Fulano")


if __name__ == "__main__":
    unittest.main()
