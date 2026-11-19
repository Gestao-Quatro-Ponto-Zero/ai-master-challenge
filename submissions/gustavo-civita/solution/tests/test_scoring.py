"""Testes da lógica de priorização. Uso: python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backtest  # noqa: E402
import scoring  # noqa: E402


class ScoringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deals = scoring.load_pipeline()
        cls.today = scoring.reference_date(cls.deals)
        cls.scored, cls.model = scoring.score_open_deals(cls.deals, cls.today)

    def test_join_keeps_every_opportunity_and_fixes_product_name(self):
        self.assertEqual(len(self.deals), 8800)
        self.assertEqual(self.deals["sales_price"].isna().sum(), 0)
        self.assertNotIn("GTXPro", set(self.deals["product"]))

    def test_today_is_the_last_date_in_the_crm(self):
        self.assertEqual(self.today, pd.Timestamp("2017-12-31"))

    def test_every_open_deal_gets_exactly_one_list(self):
        open_count = self.deals["deal_stage"].isin(["Engaging", "Prospecting"]).sum()
        self.assertEqual(len(self.scored), open_count)
        self.assertTrue(self.scored["lista"].isin(["foco", "abordar", "reativar", "encerrar"]).all())

    def test_chance_is_a_probability_and_dies_with_age(self):
        chance = self.model["chance_by_age"]
        self.assertTrue(all(0 <= p <= 1 for p in chance))
        self.assertEqual(chance[self.model["longest_cycle"]], 0.0)
        self.assertGreater(chance[0], 0.3)

    def test_classification_rules(self):
        self.assertEqual(scoring.classify("Prospecting", float("nan"), 550, 0.5), "abordar")
        self.assertEqual(scoring.classify("Engaging", 30, 550, 0.5), "foco")
        self.assertEqual(scoring.classify("Engaging", 150, 550, 0.0), "reativar")
        self.assertEqual(scoring.classify("Engaging", 151, 550, 0.0), "encerrar")
        self.assertEqual(scoring.classify("Engaging", 180, 3393, 0.0), "reativar")
        self.assertEqual(scoring.classify("Engaging", 181, 3393, 0.0), "encerrar")

    def test_chance_bands(self):
        self.assertEqual(scoring.band(0.45), "alta")
        self.assertEqual(scoring.band(0.25), "media")
        self.assertEqual(scoring.band(0.05), "baixa")

    def test_prospects_have_no_chance_and_no_score(self):
        prospects = self.scored[self.scored["lista"] == "abordar"]
        self.assertEqual(len(prospects), 500)
        self.assertEqual(prospects["chance"].max(), 0)
        self.assertEqual(prospects["score"].max(), 0)
        self.assertTrue(prospects["faixa"].isna().all())

    def test_only_deals_in_focus_have_score_and_value(self):
        others = self.scored[self.scored["lista"] != "foco"]
        self.assertEqual(others["valor_esperado"].sum(), 0)
        self.assertEqual(others["score"].max(), 0)
        focus = self.scored[self.scored["lista"] == "foco"]
        self.assertTrue(focus["score"].between(0, 100).all())
        self.assertGreaterEqual(focus["score"].max(), 99)
        self.assertTrue(focus["faixa"].isin(["alta", "media", "baixa"]).all())

    def test_score_follows_expected_value(self):
        focus = self.scored[self.scored["lista"] == "foco"].sort_values("valor_esperado")
        self.assertTrue(focus["score"].is_monotonic_increasing)

    def test_no_leakage_from_the_future(self):
        """A chance calculada numa data não muda se apagarmos o que aconteceu depois."""
        as_of = pd.Timestamp("2017-08-15")
        past = self.deals.copy()
        later = past["close_date"] > as_of
        past.loc[later, ["close_date", "close_value"]] = [pd.NaT, float("nan")]
        past.loc[later, "deal_stage"] = "Engaging"
        past = past[past["engage_date"].isna() | (past["engage_date"] <= as_of)]
        self.assertEqual(
            scoring.win_chance_by_age(self.deals, as_of), scoring.win_chance_by_age(past, as_of)
        )


class BacktestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = backtest.run_backtest(scoring.load_pipeline())

    def test_covers_both_quarters_week_by_week(self):
        self.assertGreaterEqual(len(self.result["semanas"]), 20)
        self.assertEqual(len(self.result["resumo"]), 2)

    def test_beats_the_fair_simple_rule_in_total(self):
        """Contra "preço entre deals recentes", com desempate neutro, ganha no total dos dois trimestres."""
        for quarter in self.result["resumo"]:
            self.assertGreater(quarter["ferramenta"], quarter["precoRecentes"], quarter["trimestre"])

    def test_chance_improves_the_order_not_only_the_cut(self):
        """Com o mesmo corte, ordenar por preço x chance rende mais que ordenar só por preço, em toda semana."""
        for quarter in self.result["resumo"]:
            self.assertGreater(quarter["ferramenta"], quarter["precoVivas"], quarter["trimestre"])
            self.assertEqual(quarter["semanasGanhasVivas"], quarter["semanas"], quarter["trimestre"])

    def test_known_weakness_is_still_reported(self):
        """O limite declarado no README: no 4º trimestre a regra "preço, depois a mais nova" empata ou ganha.

        Se este teste falhar, o texto do README sobre o 4º trimestre precisa ser revisto.
        """
        fourth = next(q for q in self.result["resumo"] if q["trimestre"].startswith("4"))
        self.assertLess(fourth["ferramenta"], fourth["precoRecentesNova"] * 1.02)

    def test_tie_break_is_reproducible(self):
        again = backtest.run_backtest(scoring.load_pipeline())
        self.assertEqual(again["resumo"], self.result["resumo"])

    def test_beats_random_every_week(self):
        for week in self.result["semanas"]:
            self.assertGreater(week["ferramenta"], 2 * week["acaso"], week["data"])

    def test_no_parked_deal_was_won(self):
        self.assertGreater(self.result["parados"]["total"], 1000)
        self.assertEqual(self.result["parados"]["ganhos"], 0)

    def test_higher_band_wins_more(self):
        rates = {row["faixa"]: row["ganhos"] for row in self.result["faixas"]}
        self.assertGreater(rates["alta"], rates["media"])
        self.assertGreater(rates["media"], rates["baixa"])

    def test_deals_flagged_as_closing_soon_close_more_often(self):
        soon = self.result["esteMes"]
        self.assertGreater(soon["ganhosMarcados"], 5 * soon["ganhosNaoMarcados"])


if __name__ == "__main__":
    unittest.main()
