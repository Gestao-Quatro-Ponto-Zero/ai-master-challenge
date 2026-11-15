from __future__ import annotations

import json
import re
import unittest
from datetime import date, timedelta

from engine import core, seller

REF = date(2017, 12, 4)
DS = core.get_dataset()
BY_ID = {x.id: x for x in DS.deals}
DATES = core.available_dates(DS)
PEOPLE = ("Daniell Hammack", "Darcel Schlecht", "Reed Clapper", "Garret Kinder")
SINGULAR_PLURAL = re.compile(r"(?<![\d.])1 (deals|dias)\b")
CHECK_DATES = (date(2017, 7, 3), date(2017, 10, 2), REF, date(2017, 12, 25))


class FocusReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dh = seller.focus(DS, REF, "daniell hammack")

    def test_summary(self):
        s = self.dh["summary"]
        self.assertEqual((s["open_count"], s["live_count"], s["stale_count"]), (85, 38, 47))
        self.assertEqual((s["declared_value"], s["live_value"], s["stale_value"]), (253368, 106459, 146909))
        self.assertEqual(round(s["expected_30d"]), 42162)
        self.assertEqual(s["sentence"], "Do que está declarado (US$ 253.368 a preço de tabela), 42% ainda pode "
                                        "fechar. Os outros 58% são 47 deals em negociação há mais de 138 dias.")
        self.assertEqual(self.dh["seller"]["name"], "Daniell Hammack")
        self.assertEqual(self.dh["date"]["context_sentence"],
                         "É o último mês do trimestre, quando os deals maduros desta base mais fecham.")

    def test_bands_and_rates(self):
        got = {b["key"]: (b["count"], b["with_account"], b["without_account"]) for b in self.dh["bands"]}
        self.assertEqual([b["key"] for b in self.dh["bands"]], ["quente", "morno", "frio", "sem_desfecho"])
        self.assertEqual(got["quente"], (16, 7, 9))
        self.assertEqual(got["morno"][0] + got["frio"][0], 22)
        self.assertEqual((got["morno"][0], got["frio"][0]), (17, 5))
        self.assertEqual(got["morno"][1] + got["frio"][1], 14)
        self.assertEqual(got["sem_desfecho"], (47, 17, 30))
        r = self.dh["rates"]
        self.assertEqual((r["won"], r["lost"]), (103, 70))
        self.assertEqual(core.fmt.pct1(r["official"]), "59,5%")
        self.assertEqual(core.fmt.pct1(r["with_stale"]), "46,8%")
        self.assertEqual(self.dh["window"]["from_days"], 61)
        self.assertEqual((self.dh["window"]["to_days"], self.dh["window"]["max_days"]), (105, 138))

    def test_priority_order(self):
        top = [(d["id"], d["score"], d["age_days"]) for d in self.dh["deals"][:10]]
        self.assertEqual(top, [
            ("LFI3BGEE", 98, 73), ("HF1GSBT4", 97, 102), ("9DY57A6F", 96, 82), ("HP9TUR60", 96, 77),
            ("XZKZYO55", 94, 75), ("IDKBZCAF", 94, 74), ("YPSXMDRH", 94, 73), ("D3HUUVPL", 94, 71),
            ("S53EVWFC", 91, 103), ("5J7T0GZU", 86, 57)])
        self.assertEqual([d["price"] for d in self.dh["deals"][:3]], [5482, 5482, 4821])
        self.assertEqual(len(self.dh["deals"]), 85)
        self.assertTrue(all(not d["stale"] for d in self.dh["deals"][:38]))
        self.assertTrue(all(d["stale"] for d in self.dh["deals"][38:]))

    def test_deal_texts(self):
        d = self.dh["deals"][0]
        self.assertEqual(d["position"], "janela")
        self.assertEqual(d["base"], {"n": 391, "y": 196, "level": "semana", "bucket_label": "61–75"})
        why = d["why"]
        self.assertEqual(why["reason"], "50% de chance vezes US$ 5.482 dá US$ 2.748 esperados em 30 dias. "
                                        "Só 2% dos deals vivos da empresa têm receita esperada maior.")
        self.assertEqual(why["source"], "391 deals já estiveram assim: 61 a 75 dias, nesta mesma semana do "
                                        "trimestre. Deles, 196 viraram venda em 30 dias.")
        self.assertEqual(why["excluded"], seller.EXCLUDED_TEXT)
        self.assertEqual(d["summary_text"], (
            "#LFI3BGEE · GTX Plus Pro · US$ 5.482 · aberto há 73 dias · score 98 · 50% de chance de virar "
            "venda em 30 dias (196 de 391 deals parecidos). O que fazer: o deal está na faixa de idade em que "
            "mais se fecha. Proponha o fechamento ainda em dezembro."))
        early = self.dh["deals"][9]
        self.assertEqual((early["position"], early["position_label"]), ("cedo", "ainda é cedo"))
        self.assertIn("entre 61 e 105 dias", early["why"]["action"])
        stale = self.dh["deals"][-1]
        self.assertEqual((stale["position"], stale["share_above"], stale["score"]), ("sem_desfecho", None, None))
        self.assertEqual(stale["why"]["source"], "Dos 522 deals que já estiveram além desse prazo nessa altura "
                                                 "do trimestre, nenhum virou venda em 30 dias.")
        self.assertTrue(stale["why"]["reason"].startswith("Aberto há %d dias." % stale["age_days"]))

    def test_insights(self):
        moment, pipe, ind = self.dh["insights"]
        self.assertEqual((moment["kind"], moment["label"], moment["highlight"]), ("momento", "MOMENTO", True))
        self.assertEqual(moment["title"], "É mês de fechar.")
        in_window = sum(1 for d in self.dh["deals"] if d["position"] == "janela")
        self.assertEqual(moment["body"], "%d dos seus deals vivos estão na faixa de 61 a 105 dias. Nesta altura "
                                         "do trimestre, metade dos deals nessa faixa virou venda em 30 dias."
                         % in_window)
        self.assertEqual((moment["link_label"], moment["link_target"]), ("Ver os %d deals" % in_window, "janela"))
        # o empate de preço estica o top 10 para 12: o título diz que são os 12 GTX Plus Pro
        self.assertEqual(pipe["title"], "10 dos seus 12 deals de GTX Plus Pro passaram de 138 dias.")
        # o título fala de 10 deals e o link abre os 47: o rótulo diz isso
        self.assertEqual((pipe["link_label"], pipe["link_target"]),
                         ("Ver todos os 47 sem desfecho", "sem_desfecho"))
        self.assertEqual(ind["body"], "Hoje o CRM mostra 59,5%: 103 ganhos em 173 deals fechados. Com os 47 deals "
                                      "sem desfecho contados como não ganhos, são 103 em 220, ou 46,8%. Cada deal "
                                      "que você confirma com o cliente ou encerra aproxima os dois números.")
        # a conta está no próprio cartão: ele não leva a outra tela
        self.assertEqual((ind["link_label"], ind["link_target"]), (None, None))


class FocusOtherPeopleTest(unittest.TestCase):
    def test_reed_clapper(self):
        r = seller.focus(DS, REF, "Reed Clapper")
        s = r["summary"]
        self.assertEqual((s["open_count"], s["stale_count"], s["declared_value"]), (26, 0, 76586))
        self.assertEqual(round(s["expected_30d"]), 25869)
        self.assertEqual([b["count"] for b in r["bands"]], [9, 13, 4, 0])
        self.assertEqual(s["sentence"], "Tudo o que está declarado (US$ 76.586 a preço de tabela) ainda pode "
                                        "fechar: nenhum deal passou de 138 dias.")
        ind = r["insights"][2]
        self.assertEqual(ind["title"], "Sua taxa de ganho conta a história toda.")
        self.assertEqual(ind["body"], "Você não tem deal aberto há mais de 138 dias, então os 66,0% do CRM não "
                                      "escondem nada.")
        self.assertEqual(r["insights"][1]["title"], "Seus maiores deals estão todos vivos.")
        self.assertIsNone(r["insights"][1]["link_label"])

    def test_darcel_schlecht(self):
        r = seller.focus(DS, REF, "Darcel Schlecht")
        s = r["summary"]
        self.assertEqual((s["open_count"], s["stale_count"]), (118, 0))
        self.assertEqual((s["declared_value"], s["live_value"]), (398189, 398189))
        self.assertEqual(round(s["expected_30d"]), 106743)
        self.assertEqual([b["count"] for b in r["bands"]], [26, 71, 21, 0])
        self.assertEqual(r["insights"][1]["body"], "Nenhum dos seus 118 deals abertos passou de 138 dias.")

    def test_unknown_seller(self):
        with self.assertRaisesRegex(ValueError, "Vendedor não encontrado"):
            seller.focus(DS, REF, "Fulano")
        with self.assertRaisesRegex(ValueError, "Vendedor não encontrado"):
            seller.pipeline(DS, REF, "Fulano")


class TopByPriceTest(unittest.TestCase):
    def test_extends_ties(self):
        items = core.snapshot(DS, REF).by_seller["Daniell Hammack"]
        top = seller.top_by_price(items)
        self.assertEqual(len(top), 12)
        self.assertNotEqual(top[-1].deal.price, sorted((s.deal.price for s in items), reverse=True)[12])
        small = items[:3]
        self.assertEqual(len(seller.top_by_price(small)), 3)


class ContextSentenceTest(unittest.TestCase):
    def test_every_date_agrees_with_table(self):
        for d in DATES:
            snap = core.snapshot(DS, d)
            text = seller.context_sentence(DS, snap)
            w = snap.window
            self.assertTrue(text.startswith(seller.PHASE_OPENERS[snap.quarter_phase]), (d, text))
            if "maduros" in text:
                self.assertGreaterEqual(w.min_age, seller.MATURE_AGE, d)
            old = [b.chance for b in snap.bands if b.max_age is not None and b.min_age >= seller.OLD_AGE]
            if "quase não vira venda" in text:
                self.assertLess(max(old), seller.NEARLY_ZERO, d)
                self.assertGreater(max(old), 0, d)
            if "nenhum deal com mais de 60 dias" in text:
                self.assertEqual(max(old), 0, d)
            if "maduros" in text:
                self.assertTrue(core.closing_is_strong(snap), d)
            if "deals novos" in text:
                self.assertEqual(w.first_band, 0, d)
            if "acelerar" in text:
                before = core.snapshot(DS, d - timedelta(days=28)).window
                self.assertGreater(w.peak_chance, before.peak_chance, d)
            if "estão entre" in text:
                self.assertIn("entre %d e %d dias" % (w.min_age, w.max_age), text)


class AllDatesTest(unittest.TestCase):
    """Toda frase continua bem formada e coerente em outras datas e pessoas."""

    def test_texts_hold(self):
        for d in CHECK_DATES:
            snap = core.snapshot(DS, d)
            for name in PEOPLE:
                r = seller.focus(DS, d, name)
                json.dumps(r)
                s = r["summary"]
                self.assertEqual(s["open_count"], s["live_count"] + s["stale_count"])
                self.assertEqual(s["open_count"], len(r["deals"]))
                self.assertEqual(sum(b["count"] for b in r["bands"]), s["open_count"])
                self.assertEqual(r["rates"]["won"], sum(x.won for x in DS.closed_before(d, seller=name)))
                for deal in r["deals"]:
                    text = deal["summary_text"]
                    self.assertIsNone(SINGULAR_PLURAL.search(text), text)
                    self.assertIn("aberto há %d dia" % deal["age_days"], text)
                    if deal["position"] == "janela":
                        self.assertTrue(snap.window.min_age <= deal["age_days"] <= snap.window.max_age)
                    if deal["position"] == "cedo":
                        self.assertLess(deal["age_days"], snap.window.min_age)
                    if not deal["stale"]:
                        self.assertIn("score %d" % deal["score"], text)
                for card in r["insights"]:
                    self.assertTrue(card["title"] and card["body"])
                    self.assertIsNone(SINGULAR_PLURAL.search(card["body"] + card["title"] + (card["link_label"] or "")))
                if s["stale_count"] == 0:
                    self.assertTrue(s["sentence"].startswith("Tudo o que está declarado"))

    def test_no_future_data(self):
        """Nada fechado em d ou depois aparece nas telas da data d."""
        d = date(2017, 10, 2)
        for name in PEOPLE:
            r = seller.focus(DS, d, name)
            for deal in r["deals"]:
                x = BY_ID[deal["id"]]
                self.assertTrue(x.close_date is None or x.close_date >= d)
                for key in ("won", "close_value", "close_date", "stage"):
                    self.assertNotIn(key, deal)
            p = seller.pipeline(DS, d, name)
            for col in p["columns"][3:]:
                for deal in col["deals"]:
                    self.assertLess(deal["close_date"], d.isoformat())
                    self.assertGreaterEqual(deal["close_date"], (d - timedelta(days=30)).isoformat())

    def test_stale_seller_card(self):
        r = seller.focus(DS, date(2017, 7, 3), "Daniell Hammack")
        self.assertEqual(r["date"]["quarter_phase"], "abre")
        self.assertEqual(r["insights"][0]["title"], "Começo de trimestre.")
        self.assertIn("dos seus deals vivos", r["insights"][0]["body"])
        self.assertIn("% dos deals nessa faixa viraram venda", r["insights"][0]["body"])

    def test_single_deal(self):
        r = seller.focus(DS, date(2017, 12, 25), "Garret Kinder")
        self.assertEqual(r["summary"]["open_count"], 1)
        self.assertEqual(r["insights"][1]["title"], "Seu deal aberto está vivo.")
        self.assertEqual(r["insights"][0]["body"], "Você não tem deal na faixa de 76 a 120 dias, a que mais "
                                                   "fecha nesta altura do trimestre.")
        self.assertIsNone(r["insights"][0]["link_label"])


class ActionTextTest(unittest.TestCase):
    def test_first_month_actions_hold(self):
        # 3 jul: a janela é 0 a 14 dias; deal de 15 dias não é tratado como esfriando
        r = seller.focus(DS, date(2017, 7, 3), "Daniell Hammack")
        late = [x for x in r["deals"] if x["position"] == "tarde"]
        self.assertTrue(late)
        for x in late:
            action = x["why"]["action"]
            if x["age_days"] < 138 - seller.NEAR_LIMIT_DAYS:
                self.assertNotIn("segue de pé", action, x["id"])
            self.assertNotIn("já passou da faixa que mais fecha agora", action)
        # 6R6S91WE: 100 dias, faixa 91–105 com 17% contra 18% da melhor
        deal = next(x for x in r["deals"] if x["id"] == "6R6S91WE")
        self.assertEqual(deal["why"]["action"], "a faixa de idade deste deal fecha quase tanto quanto a melhor "
                                                 "agora (17% contra 18%). Trate como prioridade.")

    def test_closing_month_titles_follow_the_table(self):
        late = seller.focus(DS, date(2017, 12, 25), "Cassey Cress")
        self.assertEqual(late["insights"][0]["title"], "Fim de trimestre.")
        self.assertNotIn("maduros", late["date"]["context_sentence"])
        for x in late["deals"]:
            self.assertNotIn("ainda em dezembro", x["why"]["action"])
        sept = seller.focus(DS, date(2017, 9, 25), "Cassey Cress")
        self.assertEqual(sept["insights"][0]["title"], "Fim de trimestre.")
        for x in sept["deals"]:
            self.assertNotIn("ainda em setembro", x["why"]["action"])
        self.assertEqual(seller.focus(DS, REF, "Cassey Cress")["insights"][0]["title"], "É mês de fechar.")

    def test_tie_extended_group_label(self):
        r = seller.focus(DS, date(2017, 12, 25), "Darcel Schlecht")
        title = r["insights"][1]["title"]
        self.assertNotIn("maiores", title)
        self.assertEqual(title, "42 dos seus 49 deals de maior preço passaram de 138 dias.")

    def test_seller_only_in_registry(self):
        for func in (seller.focus, seller.pipeline):
            with self.assertRaisesRegex(ValueError, "Carl Lin só está no cadastro"):
                func(DS, REF, "Carl Lin")


class SentenceEdgeTest(unittest.TestCase):
    def test_no_open_and_all_stale(self):
        base = {"open": 0, "live": 0, "stale": 0, "declared_value": 0, "live_value": 0, "stale_value": 0}
        self.assertEqual(seller._summary_sentence(base, 138), "Você não tem deal em negociação nesta data.")
        one = dict(base, open=1, stale=1, declared_value=55, stale_value=55)
        self.assertEqual(seller._summary_sentence(one, 138), "Do que está declarado (US$ 55 a preço de tabela), "
                                                             "nada ainda pode fechar: é 1 deal em negociação há "
                                                             "mais de 138 dias.")


class PipelineTest(unittest.TestCase):
    def test_daniell(self):
        p = seller.pipeline(DS, REF, "Daniell Hammack")
        self.assertEqual(p["counts"], {"all": 85, "with_account": 38, "without_account": 47})
        cols = {c["key"]: c for c in p["columns"]}
        self.assertEqual([c["key"] for c in p["columns"]], ["prospecting", "engaging", "stale", "won", "lost"])
        self.assertEqual((cols["engaging"]["count"], cols["engaging"]["value"]), (38, 106459))
        self.assertEqual(cols["engaging"]["hint"], "US$ 106.459 · até 138 dias")
        self.assertEqual((cols["stale"]["count"], cols["stale"]["value"]), (47, 146909))
        self.assertEqual(cols["stale"]["hint"], "US$ 146.909 · mais de 138 dias")
        self.assertEqual((cols["won"]["count"], cols["won"]["value"]), (5, 4713))
        self.assertEqual(cols["won"]["hint"], "US$ 4.713 · últimos 30 dias")
        self.assertEqual(cols["lost"]["count"], 13)
        self.assertEqual(cols["prospecting"]["count"], 0)
        self.assertEqual(cols["prospecting"]["note"], "Só a regional Central usa a prospecção. Lá são 500 deals, "
                                                      "todos sem data, então entram na lista só pelo valor.")
        self.assertEqual(cols["engaging"]["deals"][0]["id"], "LFI3BGEE")
        dates = [x["close_date"] for x in cols["won"]["deals"]]
        self.assertEqual(dates, sorted(dates, reverse=True))
        self.assertIn("context_sentence", p["date"])

    def test_darcel_prospecting(self):
        p = seller.pipeline(DS, REF, "Darcel Schlecht")
        col = p["columns"][0]
        self.assertEqual(col["count"], 111)
        self.assertEqual(col["note"], "Sem data de entrada: não dá para calcular idade nem score, nem saber desde "
                                      "quando estão aqui. A lista é a do fim da base, em ordem de valor.")
        keys = [(-x["price"], x["id"]) for x in col["deals"]]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(set(col["deals"][0]), {"id", "product", "price", "account"})


if __name__ == "__main__":
    unittest.main()
