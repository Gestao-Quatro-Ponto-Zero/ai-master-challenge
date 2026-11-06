"""Testes do scorer. Rodar de solution/: python -m unittest discover tests"""
import datetime as dt
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import scorer as S  # noqa: E402

REF = dt.date(2017, 12, 31)


def deal(stage="Won", engage="2017-01-01", close="2017-01-20", agent="A", product="P", account="C"):
    return {"id": "x", "agent": agent, "product": product, "account": account, "stage": stage,
            "engage": S._date(engage), "close": S._date(close), "value": None}


def aged(age):
    return deal("Engaging", engage=(REF - dt.timedelta(days=age)).isoformat(), close="")


class TestMath(unittest.TestCase):
    def test_auc_perfect_random_ties(self):
        self.assertEqual(S.auc([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1]), 1.0)
        self.assertEqual(S.auc([0.9, 0.8, 0.2, 0.1], [0, 0, 1, 1]), 0.0)
        self.assertEqual(S.auc([0.5] * 4, [0, 1, 0, 1]), 0.5)

    def test_auc_ci_contains_point(self):
        s, y = [i / 100 for i in range(100)], [i % 3 == 0 for i in range(100)]
        lo, hi = S.auc_ci(s, y)
        self.assertLessEqual(lo, S.auc(s, y))
        self.assertGreaterEqual(hi, S.auc(s, y))

    def test_smoothing_pulls_small_groups_to_prior(self):
        self.assertAlmostEqual(S.smoothed((1, 1), 0.5, k=40), 21 / 41)
        self.assertAlmostEqual(S.smoothed((0, 0), 0.63), 0.63)

    def test_value_pts_bounds(self):
        self.assertAlmostEqual(S.value_pts(55, 55, 26768), 0)
        self.assertAlmostEqual(S.value_pts(26768, 55, 26768), S.PTS_VALOR)


class TestModel(unittest.TestCase):
    def setUp(self):
        # perdas rápidas (5 dias), ganhos em 60 dias, maior ciclo = 100
        closed = ([deal("Lost", close="2017-01-06")] * 30 + [deal("Won", close="2017-03-02")] * 60
                  + [deal("Won", close="2017-04-11")])
        self.m = S.fit(closed)

    def test_survival_curve(self):
        self.assertEqual(self.m["max_cycle"], 100)
        self.assertEqual(self.m["survival"][0], (61, 91))
        self.assertEqual(self.m["survival"][6], (61, 61))
        self.assertEqual(self.m["survival"][101], (0, 0))
        self.assertEqual(self.m["early_loss"], 1.0)

    def test_time_prob_uses_next_day(self):
        # aberto há 5 dias => ciclo final >= 6, então perdas do dia 5 não contam
        self.assertAlmostEqual(S.time_prob(self.m, 5), S.smoothed((61, 61), self.m["base"]))
        self.assertIsNone(S.time_prob(self.m, None))   # Prospecting: desconhecido
        self.assertIsNone(S.time_prob(self.m, 101))    # zumbi

    def test_states_and_actions(self):
        cases = {None: ("prospecting", "Avançar para Engaging"), 5: ("janela_risco", "Contato urgente"),
                 50: ("maduro", "Manter cadência"), 95: ("reta_final", "Empurrar fechamento"),
                 101: ("zumbi", "Verificar no CRM")}
        for age, (st, act) in cases.items():
            d = deal("Prospecting", engage="") if age is None else aged(age)
            s = S.score_deal(self.m, d, 550, 55, 26768)
            self.assertEqual((s["state"], s["action"]), (st, act), age)

    def test_action_independent_of_price(self):
        # crítica #3: ticket baixo também pode ser "empurrar fechamento"
        for price in (55, 26768):
            self.assertEqual(S.score_deal(self.m, aged(95), price, 55, 26768)["action"], "Empurrar fechamento")

    def test_unknown_chance_has_no_expected_value(self):
        for d in (deal("Prospecting", engage=""), aged(150)):
            s = S.score_deal(self.m, d, 5000, 55, 26768)
            self.assertIsNone(s["p"])
            self.assertIsNone(s["ev"])

    def test_momentum_order(self):
        m = S.MOMENTO
        self.assertGreater(m["janela_risco"], m["reta_final"])
        self.assertGreater(m["reta_final"], m["maduro"])
        self.assertGreater(m["maduro"], m["prospecting"])
        self.assertGreater(m["prospecting"], m["zumbi"])

    def test_gated_factor_changes_chance_only_when_selected(self):
        closed = [deal("Won", agent="Good")] * 50 + [deal("Lost", agent="Bad")] * 50
        off, on = S.fit(closed), S.fit(closed, ["vendedor_produto"])
        g, b = deal(agent="Good"), deal(agent="Bad")
        self.assertAlmostEqual(S.chance(off, g, 10), S.chance(off, b, 10))
        self.assertGreater(S.chance(on, g, 10), S.chance(on, b, 10))

    def test_score_bounds(self):
        for age in (None, 0, 14, 15, 89, 90, 100, 101):
            for price in (55, 26768):
                d = deal("Prospecting", engage="") if age is None else aged(age)
                self.assertTrue(0 <= S.score_deal(self.m, d, price, 55, 26768)["score"] <= 100)


class TestRealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acc, cls.prod, cls.teams, cls.deals = S.load()
        closed = [d for d in cls.deals if d["stage"] in ("Won", "Lost")]
        cls.m = S.fit(closed)
        cls.rows = S.score_open(cls.m, cls.acc, cls.prod, cls.teams, cls.deals)

    def test_data_quality_fixes(self):
        self.assertNotIn("GTXPro", {d["product"] for d in self.deals})
        self.assertNotIn("technolgy", {a["sector"] for a in self.acc.values()})
        self.assertEqual(len(self.deals), 8800)

    def test_open_pipeline(self):
        self.assertEqual(len(self.rows), 2089)
        self.assertEqual(self.m["max_cycle"], 138)
        self.assertEqual(sum(r["state"] == "zumbi" for r in self.rows), 1291)
        self.assertTrue(all(r["reasons"] for r in self.rows))
        first_z = next(i for i, r in enumerate(self.rows) if r["state"] == "zumbi")
        self.assertTrue(all(r["state"] == "zumbi" for r in self.rows[first_z:]))
        active = [r["score"] for r in self.rows[:first_z]]
        self.assertEqual(active, sorted(active, reverse=True))

    def test_reason_formatting(self):
        info = next(t for r in self.rows if r["account"] for k, t in r["reasons"] if "receita" in t)
        self.assertRegex(info, r"^\w+, receita R\$ [\d.,]+ (mi|bi)/ano, [\d.]+ funcionários$")

    def test_brazilian_names_are_one_to_one(self):
        br = S.br_names()
        self.assertEqual(len(br["vendedor"]), 35)
        self.assertEqual(set(br["regiao"].values()), {"Centro-Oeste", "Sudeste", "Sul"})
        self.assertEqual(set(self.teams), set(br["vendedor"].values()))           # todo vendedor mapeado
        self.assertEqual({t["original"] for t in self.teams.values()}, set(br["vendedor"]))
        firsts = [n.split()[0] for n in br["vendedor"].values()]
        self.assertEqual(len(firsts), len(set(firsts)))  # motivos usam o primeiro nome: sem ambiguidade
        originals = {"Central", "East", "West", "Darcel Schlecht", "Melvin Marxen"}
        self.assertFalse(any(r["region"] in originals or r["agent"] in originals or r["manager"] in originals
                             for r in self.rows))

    def test_values_in_brl(self):
        # dataset em US$, tela em R$ pela PTAX fixa
        self.assertEqual(S.brl(100), round(100 * S.USD_BRL))
        self.assertEqual(S.fmt_brl(S.brl(26768)), "R$ 146.209")
        self.assertEqual(S.fmt_brl_mi(1100.04), "R$ 6,0 bi")
        self.assertEqual(S.fmt_brl_mi(100), "R$ 546 mi")
        for r in self.rows:
            self.assertEqual(r["price"], S.brl(r["price_usd"]))
        self.assertFalse(any("US$" in t for r in self.rows for _, t in r["reasons"]))

    def test_no_snapshot_leakage(self):
        for c in S.CUTOFFS:
            m, test = S.snapshot(self.deals, c)
            self.assertTrue(all(d["engage"] < c <= d["close"] for d in test))
            self.assertEqual(m["n"], sum(1 for d in self.deals if d["close"] and d["close"] < c))

    def test_backtest_rejects_noise(self):
        bt = S.backtest(self.deals)
        self.assertEqual(bt["selected"], [])
        t0, t14 = bt["stability"][0], bt["stability"][2]
        self.assertGreater(t14[1][0], t0[1][0])
        self.assertGreater(t14[2][0], t0[2][0])


if __name__ == "__main__":
    unittest.main()
