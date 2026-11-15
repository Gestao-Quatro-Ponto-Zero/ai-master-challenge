from __future__ import annotations

import threading
import time
import unittest
from collections import Counter
from datetime import date, timedelta

from engine import core

REF = date(2017, 12, 4)
DS = core.get_dataset()
BY_ID = {x.id: x for x in DS.deals}


def truncated(d: date) -> core.Dataset:
    """A base como estaria em d: só deals que já tinham entrado, sem desfecho de quem fechou em d ou depois."""
    deals = []
    for x in DS.deals:
        if x.engage_date is not None and x.engage_date >= d:
            continue
        if x.close_date is not None and x.close_date >= d:
            x = x._replace(stage="Engaging", close_date=None, close_value=None, won=False, lost=False)
        deals.append(x)
    return core.Dataset(DS.products, DS.sellers, DS.accounts, tuple(deals))


def snap(d: date = REF) -> core.Snapshot:
    return core.snapshot(DS, d)


class LoadTest(unittest.TestCase):
    def test_counts_and_normalization(self):
        self.assertEqual(len(DS.deals), 8800)
        self.assertEqual(len(DS.sellers), 35)
        self.assertEqual(len(DS.deals_by_seller), 30)
        self.assertNotIn("GTXPro", {x.product for x in DS.deals})
        self.assertEqual(BY_ID["Z063OYW0"].product, "GTX Pro")
        self.assertEqual(BY_ID["Z063OYW0"].price, 4821)
        self.assertEqual(DS.accounts["Acme Corporation"].sector, "technology")
        self.assertEqual(DS.accounts["Acme Corporation"].sector_label, "Tecnologia")
        self.assertEqual(DS.accounts["Bioholding"].office_location, "Philippines")
        self.assertEqual(DS.accounts["Bioholding"].country_label, "Filipinas")
        self.assertEqual(DS.end_date, date(2017, 12, 31))

    def test_blank_fields(self):
        self.assertEqual(sum(1 for x in DS.deals if x.account is None), 1425)
        self.assertTrue(all(x.close_date is None for x in DS.deals if x.account is None))
        self.assertEqual(len(DS.prospecting), 500)
        self.assertEqual(Counter(x.region for x in DS.prospecting), {"Central": 500})
        prices = [(-x.price, x.id) for x in DS.prospecting]
        self.assertEqual(prices, sorted(prices))
        lost = [x for x in DS.deals if x.lost]
        self.assertTrue(all(x.close_value == 0 for x in lost))
        self.assertTrue(all(x.close_value is None for x in DS.deals if x.stage in ("Engaging", "Prospecting")))

    def test_load_is_fast(self):
        start = time.perf_counter()
        core.load_dataset()
        self.assertLess(time.perf_counter() - start, 1.0)


class RulesTest(unittest.TestCase):
    def test_age_band(self):
        self.assertEqual(core.age_band(0), 0)
        self.assertEqual(core.age_band(14), 0)
        self.assertEqual(core.age_band(15), 1)
        self.assertEqual(core.age_band(138), 8)
        self.assertEqual(core.age_band(139), 9)
        self.assertEqual(core.AGE_BAND_LABELS[9], "139+")
        self.assertEqual(core.band_bounds(4), (61, 75))
        self.assertEqual(core.band_bounds(9), (139, None))

    def test_quarter_point(self):
        self.assertEqual(core.quarter_point(REF), (9, 2, "fecha"))
        self.assertEqual(core.quarter_point(date(2017, 7, 3)), (0, 0, "abre"))
        self.assertEqual(core.quarter_point(date(2017, 3, 6)), (9, 2, "fecha"))
        self.assertEqual(core.quarter_point(date(2017, 8, 14))[2], "meio")

    def test_score_band(self):
        self.assertEqual(core.score_band(80), "quente")
        self.assertEqual(core.score_band(79), "morno")
        self.assertEqual(core.score_band(40), "morno")
        self.assertEqual(core.score_band(39), "frio")
        self.assertEqual(core.score_band(None), "sem_desfecho")

    def test_open_at_hides_future(self):
        won = next(x for x in DS.deals if x.won and x.close_date == date(2017, 12, 20))
        self.assertTrue(won.is_open_at(REF))
        self.assertFalse(won.closed_before(REF))
        self.assertTrue(won.closed_before(date(2017, 12, 25)))
        self.assertFalse(DS.prospecting[0].is_open_at(REF))

    def test_phase_title_follows_the_table(self):
        self.assertEqual(core.phase_title(snap(REF)), "É mês de fechar")
        self.assertEqual(core.phase_title(snap(date(2017, 7, 3))), "Começo de trimestre")
        # 25 dez: último mês, mas a melhor faixa fecha só 22%
        late = snap(date(2017, 12, 25))
        self.assertLess(late.window.peak_chance, core.CLOSING_PEAK_MIN)
        self.assertEqual(core.phase_title(late), "Fim de trimestre")
        self.assertEqual(core.days_to_quarter_end(REF), 27)
        self.assertEqual(core.days_to_quarter_end(date(2017, 12, 31)), 0)
        self.assertEqual(core.days_to_quarter_end(date(2017, 9, 25)), 5)

    def test_home_region(self):
        self.assertIsNone(core.home_region(()))
        acme = DS.closed_before(REF, account="Mathtouch")
        self.assertEqual(core.home_region(acme), "East")
        # Kan-code: dividido entre Leste e Oeste, a casa muda com a data (só fechados antes dela)
        self.assertEqual(core.home_region(DS.closed_before(date(2017, 7, 3), account="Kan-code")), "West")
        self.assertEqual(core.home_region(DS.closed_before(date(2017, 9, 11), account="Kan-code")), "East")

    def test_win_rate(self):
        self.assertIsNone(core.win_rate(0, 0))
        self.assertAlmostEqual(core.win_rate(1, 1, 2), 0.25)


class DatesTest(unittest.TestCase):
    def test_available_dates(self):
        dates = core.available_dates(DS)
        self.assertEqual(len(dates), 26)
        self.assertEqual(dates[0], date(2017, 7, 3))
        self.assertEqual(dates[-1], date(2017, 12, 25))
        self.assertTrue(all(d.weekday() == 0 for d in dates))
        self.assertIn(core.DEFAULT_DATE, dates)

    def test_parse_date(self):
        self.assertEqual(core.parse_date(DS, "2017-12-04"), REF)
        self.assertEqual(core.parse_date(DS, ""), core.DEFAULT_DATE)
        self.assertEqual(core.parse_date(DS, None), core.DEFAULT_DATE)
        for text in ("04/12/2017", "20171204", "2017-W49-1", "2017-12-4", "2017-12-04T00:00"):
            with self.assertRaisesRegex(core.InputError, "Data inválida", msg=text):
                core.parse_date(DS, text)
        with self.assertRaisesRegex(ValueError, "fora do período.*3 jul 2017.*25 dez 2017"):
            core.parse_date(DS, "2017-12-05")
        with self.assertRaisesRegex(ValueError, "fora do período"):
            core.parse_date(DS, "2017-06-26")

    def test_dates_do_not_depend_on_the_end_of_the_base(self):
        cut = truncated(REF)
        self.assertLess(cut.end_date, REF)
        self.assertEqual(core.available_dates(cut), core.available_dates(DS))
        self.assertEqual(core.parse_date(cut, "2017-12-04"), REF)
        # a base cortada em d dá o mesmo retrato que a base inteira em d
        full, part = core.summarize(snap().deals), core.summarize(core.snapshot(cut, REF).deals)
        self.assertEqual(full, part)


class CompanySnapshotTest(unittest.TestCase):
    def test_totals(self):
        s = snap()
        t = core.summarize(s.deals)
        self.assertEqual((t["open"], t["live"], t["stale"]), (2078, 1299, 779))
        self.assertEqual(t["declared_value"], 5006104)
        self.assertEqual(t["live_value"], 2945683)
        self.assertEqual(t["stale_value"], 2060421)
        self.assertEqual(round(t["expected_value"]), 929174)
        self.assertEqual(s.max_cycle, 138)
        self.assertEqual((s.week_of_quarter, s.month_in_quarter, s.quarter_phase), (9, 2, "fecha"))

    def test_chance_table(self):
        s = snap()
        expected = [(17, 989), (6, 812), (10, 786), (35, 450), (None, 391), (51, 409), (49, 344), (35, 220),
                    (19, 133), (0, 522)]
        for row, (pct, n) in zip(s.bands, expected):
            self.assertEqual(row.level, "semana")
            self.assertEqual(row.n, n)
            if pct is not None:
                self.assertEqual(int(round(100 * row.chance)), pct, row.label)
        self.assertEqual((s.bands[4].y, s.bands[4].n), (196, 391))
        self.assertEqual(s.model.week_mondays, (date(2017, 3, 6), date(2017, 6, 5), date(2017, 9, 4)))

    def test_window(self):
        w = snap().window
        self.assertEqual((w.min_age, w.max_age, w.label), (61, 105, "61 a 105 dias"))
        self.assertEqual((w.first_band, w.last_band, w.peak_band), (4, 6, 5))

    def test_window_none_when_all_zero(self):
        bands = [core.BandRow(i, core.AGE_BAND_LABELS[i], 0, 1, 0.0, 50, 0, "semana") for i in range(10)]
        self.assertIsNone(core.find_window(bands))

    def test_window_picks_segment_with_peak(self):
        chances = [0.18, 0.01, 0.01, 0.03, 0.04, 0.0, 0.17, 0.02, 0.0, 0.0]
        bands = [core.BandRow(i, "", core.band_bounds(i)[0], core.band_bounds(i)[1], c, 50, 0, "semana")
                 for i, c in enumerate(chances)]
        w = core.find_window(bands)
        self.assertEqual((w.first_band, w.last_band), (0, 0))

    def test_stale_rules_and_scores(self):
        s = snap()
        for x in s.stale:
            self.assertGreater(x.age_days, s.max_cycle)
            self.assertEqual((x.chance, x.expected_value, x.score, x.score_band), (0.0, 0.0, None, "sem_desfecho"))
            self.assertEqual(x.n, s.bands[9].n)
        n = len(s.live)
        for x in s.live:
            k = sum(1 for o in s.live if o.expected_value <= x.expected_value)
            self.assertEqual(x.score, int(round(100.0 * k / n)))
        self.assertEqual(list(s.live), sorted(s.live, key=core.priority_key))
        self.assertEqual(list(s.stale), sorted(s.stale, key=core.stale_key))
        self.assertEqual(s.deals, s.live + s.stale)
        self.assertEqual(s.fraction_above(max(s.live_evs)), 0.0)
        self.assertEqual(s.fraction_above(-1.0), 1.0)

    def test_regions(self):
        s = snap()
        got = {}
        for region in ("Central", "East", "West"):
            t = core.summarize(s.for_sellers(core.select_sellers(DS, region=region)))
            got[region] = (t["open"], t["stale"])
        self.assertEqual(got, {"Central": (598, 0), "East": (579, 291), "West": (901, 488)})

    def test_snapshot_cache_threads_and_speed(self):
        d = date(2017, 10, 2)
        start = time.perf_counter()
        fresh = core.Snapshot(DS, d)
        self.assertLess(time.perf_counter() - start, 0.3)
        results = []
        threads = [threading.Thread(target=lambda: results.append(core.snapshot(DS, d))) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertTrue(all(r is results[0] for r in results))
        self.assertEqual([x.score for x in results[0].deals], [x.score for x in fresh.deals])

    def test_no_future_in_model(self):
        # O modelo de d só usa segundas cujo desfecho de 30 dias já era conhecido em d.
        for d in core.available_dates(DS):
            model = snap(d).model
            self.assertTrue(all(m + timedelta(days=30) <= d for m in model.mondays))
            self.assertEqual(snap(d).max_cycle, 138)


class ReferenceImplementationTest(unittest.TestCase):
    """Reimplementação direta (como nos scripts de análise) comparada deal a deal."""

    def brute(self, d: date):
        dated = [x for x in DS.deals if x.engage_date]
        counts = {"semana": Counter(), "mes": Counter(), "idade": Counter()}
        totals = [0, 0]
        wk, mo, _ = core.quarter_point(d)
        for m in core.mondays(date(2017, 3, 6), date(2017, 12, 25)):
            if m + timedelta(days=30) > d:
                continue
            mw, mm, _ = core.quarter_point(m)
            for x in dated:
                if x.engage_date < m and (x.close_date is None or x.close_date >= m):
                    b = core.age_band((m - x.engage_date).days)
                    y = 1 if x.won and x.close_date < m + timedelta(days=30) else 0
                    for level, key in (("semana", (b, mw)), ("mes", (b, mm)), ("idade", b)):
                        counts[level][key, "y"] += y
                        counts[level][key, "n"] += 1
                    totals[0] += y
                    totals[1] += 1
        maxc = max((x.close_date - x.engage_date).days for x in dated if x.close_date and x.close_date < d)
        out = {}
        for x in dated:
            if x.engage_date < d and (x.close_date is None or x.close_date >= d):
                age = (d - x.engage_date).days
                b = core.age_band(age)
                p = totals[0] / float(totals[1])
                for level, key in (("semana", (b, wk)), ("mes", (b, mo)), ("idade", b)):
                    if counts[level][key, "n"] >= 30:
                        p = counts[level][key, "y"] / float(counts[level][key, "n"])
                        break
                out[x.id] = 0.0 if age > maxc else p
        return out

    def test_matches_brute_force(self):
        for d in (date(2017, 7, 3), date(2017, 9, 18), REF, date(2017, 12, 25)):
            expected = self.brute(d)
            s = snap(d)
            by_id = {x.deal.id: x for x in s.deals}
            self.assertEqual(set(expected), set(by_id))
            for deal_id, p in expected.items():
                self.assertAlmostEqual(by_id[deal_id].chance, p, places=12)

    def test_edge_dates_totals(self):
        first = core.summarize(snap(date(2017, 7, 3)).deals)
        self.assertEqual((first["open"], first["live"], first["stale"]), (1714, 1556, 158))
        self.assertEqual(round(first["expected_value"]), 232684)
        last = core.summarize(snap(date(2017, 12, 25)).deals)
        self.assertEqual((last["open"], last["live"], last["stale"]), (1744, 524, 1220))
        self.assertEqual(round(last["expected_value"]), 151430)
        self.assertEqual(snap(date(2017, 12, 25)).window.label, "76 a 120 dias")


class SellerTest(unittest.TestCase):
    def test_daniell(self):
        s = snap()
        mine = s.by_seller["Daniell Hammack"]
        t = core.summarize(mine)
        self.assertEqual((t["open"], t["hot"], t["warm"], t["cold"], t["stale"]), (85, 16, 17, 5, 47))
        self.assertEqual((t["declared_value"], t["live_value"], t["stale_value"]), (253368, 106459, 146909))
        self.assertEqual(round(t["expected_value"]), 42162)
        rec = core.win_record(DS, s, "Daniell Hammack")
        self.assertEqual((rec.won, rec.lost, rec.stale), (103, 70, 47))
        self.assertEqual(round(rec.official_rate * 1000), 595)
        self.assertEqual(round(rec.rate_with_stale * 1000), 468)
        live = [x for x in mine if not x.stale]
        stale = [x for x in mine if x.stale]
        self.assertEqual((sum(1 for x in live if x.deal.account), sum(1 for x in live if not x.deal.account)), (21, 17))
        self.assertEqual((sum(1 for x in stale if x.deal.account), sum(1 for x in stale if not x.deal.account)),
                         (17, 30))
        hot = [x for x in mine if x.score_band == "quente"]
        self.assertEqual(sum(1 for x in hot if x.deal.account), 7)
        top = [(x.deal.id, x.score, x.age_days) for x in mine[:10]]
        self.assertEqual(top, [
            ("LFI3BGEE", 98, 73), ("HF1GSBT4", 97, 102), ("9DY57A6F", 96, 82), ("HP9TUR60", 96, 77),
            ("XZKZYO55", 94, 75), ("IDKBZCAF", 94, 74), ("YPSXMDRH", 94, 73), ("D3HUUVPL", 94, 71),
            ("S53EVWFC", 91, 103), ("5J7T0GZU", 86, 57)])
        self.assertEqual({x.deal.price for x in mine[:2]}, {5482})
        self.assertEqual({x.deal.price for x in mine[2:10]}, {4821})
        by_product = Counter((x.deal.product, x.stale) for x in mine)
        expected = {"GTX Plus Pro": (2, 10), "GTX Pro": (15, 12), "GTX Plus Basic": (17, 9), "GTX Basic": (2, 7),
                    "MG Advanced": (1, 6), "MG Special": (1, 3)}
        for product, (n_live, n_stale) in expected.items():
            self.assertEqual((by_product[product, False], by_product[product, True]), (n_live, n_stale), product)

    def test_darcel(self):
        t = core.summarize(snap().by_seller["Darcel Schlecht"])
        self.assertEqual((t["open"], t["hot"], t["warm"], t["cold"], t["stale"]), (118, 26, 71, 21, 0))
        self.assertEqual((t["declared_value"], t["live_value"]), (398189, 398189))
        self.assertEqual(round(t["expected_value"]), 106743)
        self.assertEqual(sum(1 for x in DS.prospecting if x.seller == "Darcel Schlecht"), 111)

    def test_reed(self):
        s = snap()
        t = core.summarize(s.by_seller["Reed Clapper"])
        self.assertEqual((t["open"], t["hot"], t["warm"], t["cold"], t["stale"]), (26, 9, 13, 4, 0))
        self.assertEqual(t["declared_value"], 76586)
        self.assertEqual(round(t["expected_value"]), 25869)
        self.assertEqual(round(core.win_record(DS, s, "Reed Clapper").official_rate * 1000), 660)

    def test_rocco_team(self):
        s = snap()
        names = [n for n in core.select_sellers(DS, manager="Rocco Neubert") if n in s.by_seller]
        self.assertEqual(names, ["Boris Faz", "Cassey Cress", "Daniell Hammack", "Donn Cantrell", "Reed Clapper"])
        t = core.summarize(s.for_sellers(names))
        self.assertEqual((t["open"], t["live"], t["stale"], t["hot"]), (307, 169, 138, 55))
        self.assertEqual((t["declared_value"], t["live_value"], t["stale_value"]), (824840, 438104, 386736))
        # 153.814 é a soma dos esperados de cada vendedor já arredondados; o total cru é 153.814,92.
        self.assertAlmostEqual(t["expected_value"], 153814.92, places=2)
        self.assertEqual(sum(round(core.summarize(s.by_seller[n])["expected_value"]) for n in names), 153814)
        expected = {
            "Cassey Cress": (263367, 121303, 53, 43450, 620, 508),
            "Daniell Hammack": (253368, 106459, 47, 42162, 595, 468),
            "Boris Faz": (180676, 82913, 38, 25431, 632, 491),
            "Reed Clapper": (76586, 76586, 0, 25869, 660, 660),
            "Donn Cantrell": (50843, 50843, 0, 16902, 568, 568),
        }
        for name, (declared, live, stale, ev, rate, rate_stale) in expected.items():
            t = core.summarize(s.by_seller[name])
            rec = core.win_record(DS, s, name)
            self.assertEqual((t["declared_value"], t["live_value"], t["stale"], round(t["expected_value"])),
                             (declared, live, stale, ev), name)
            self.assertEqual((round(rec.official_rate * 1000), round(rec.rate_with_stale * 1000)), (rate, rate_stale))
        team = core.win_record(DS, s, names)
        self.assertEqual(team.stale, 138)

    def test_seller_without_deals(self):
        idle = sorted(set(DS.sellers) - set(DS.deals_by_seller))
        self.assertEqual(len(idle), 5)
        s = snap()
        for name in idle:
            self.assertEqual(s.by_seller.get(name, ()), ())
            self.assertEqual(core.summarize(s.for_sellers([name]))["open"], 0)
            rec = core.win_record(DS, s, name)
            self.assertEqual((rec.won, rec.lost, rec.official_rate, rec.rate_with_stale), (0, 0, None, None))
            self.assertEqual(DS.closed_before(REF, seller=name), ())

    def test_closed_before(self):
        rows = DS.closed_before(REF, seller="Daniell Hammack")
        self.assertEqual(len(rows), 173)
        self.assertTrue(all(x.close_date < REF for x in rows))
        self.assertEqual(len(DS.closed_before(date(2017, 1, 1))), 0)
        everything = DS.closed_before(date(2018, 1, 1))
        self.assertEqual(len(everything), sum(1 for x in DS.deals if x.close_date))
        acct = DS.closed_before(REF, account="Acme Corporation")
        self.assertTrue(acct and all(x.account == "Acme Corporation" and x.close_date < REF for x in acct))
        self.assertEqual(DS.max_cycle_before(date(2017, 1, 1)), 0)


class NamesTest(unittest.TestCase):
    def test_resolution(self):
        self.assertEqual(core.resolve_seller(DS, "  daniell   HAMMACK "), "Daniell Hammack")
        self.assertEqual(core.resolve_manager(DS, "rocco neubert"), "Rocco Neubert")
        self.assertEqual(core.resolve_region(DS, "East"), "East")
        self.assertEqual(core.resolve_region(DS, "leste"), "East")
        self.assertEqual(core.resolve_region(DS, "Oeste"), "West")
        self.assertEqual(core.resolve_account(DS, "acme corporation"), "Acme Corporation")

    def test_unknown_names(self):
        with self.assertRaisesRegex(ValueError, "Vendedor não encontrado"):
            core.resolve_seller(DS, "Fulano")
        with self.assertRaisesRegex(ValueError, "Gestor não encontrado"):
            core.resolve_manager(DS, "Daniell Hammack")
        with self.assertRaisesRegex(ValueError, "Regional não encontrada"):
            core.resolve_region(DS, "Norte")
        with self.assertRaisesRegex(ValueError, "Cliente não encontrado"):
            core.resolve_account(DS, "Nada")
        with self.assertRaises(ValueError):
            core.select_sellers(DS, manager="Ninguém")

    def test_error_echo_is_clipped(self):
        with self.assertRaises(core.InputError) as ctx:
            core.resolve_seller(DS, "A" * 60000)
        self.assertLess(len(str(ctx.exception)), 120)
        with self.assertRaises(core.InputError) as ctx:
            core.parse_date(DS, "9" * 5000)
        self.assertLess(len(str(ctx.exception)), 160)

    def test_seller_only_in_registry(self):
        self.assertEqual(core.resolve_seller(DS, "Carl Lin"), "Carl Lin")
        with self.assertRaisesRegex(core.InputError, "Carl Lin só está no cadastro"):
            core.resolve_working_seller(DS, "carl lin")
        self.assertEqual(core.resolve_working_seller(DS, "daniell hammack"), "Daniell Hammack")

    def test_select_sellers(self):
        self.assertEqual(len(core.select_sellers(DS)), 35)
        east = core.select_sellers(DS, region="Leste")
        self.assertIn("Daniell Hammack", east)
        self.assertEqual(core.select_sellers(DS, manager="Rocco Neubert", seller="daniell hammack"), ["Daniell Hammack"])
        self.assertEqual(core.select_sellers(DS, region="West", seller="Daniell Hammack"), [])


if __name__ == "__main__":
    unittest.main()
