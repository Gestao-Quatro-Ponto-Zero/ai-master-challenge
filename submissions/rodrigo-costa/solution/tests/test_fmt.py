from __future__ import annotations

import unittest
from datetime import date

from engine import fmt


class NumberTest(unittest.TestCase):
    def test_number(self):
        self.assertEqual(fmt.number(8800), "8.800")
        self.assertEqual(fmt.number(5006104), "5.006.104")
        self.assertEqual(fmt.number(0), "0")
        self.assertEqual(fmt.number(59.45, 1), "59,5")
        self.assertEqual(fmt.number(-1234.5), "-1.235")
        self.assertEqual(fmt.number(2.5), "3")

    def test_money(self):
        self.assertEqual(fmt.money(5482), "US$ 5.482")
        self.assertEqual(fmt.money(929173.69), "US$ 929.174")
        self.assertEqual(fmt.money(55), "US$ 55")
        self.assertEqual(fmt.money(-300), "-US$ 300")

    def test_money_short(self):
        self.assertEqual(fmt.money_short(7006104), "US$ 7,0 mi")
        self.assertEqual(fmt.money_short(929174), "US$ 929 mil")
        self.assertEqual(fmt.money_short(42162), "US$ 42,2 mil")
        self.assertEqual(fmt.money_short(999960), "US$ 1,0 mi")
        self.assertEqual(fmt.money_short(3030000000), "US$ 3,0 bi")
        self.assertEqual(fmt.money_short(550), "US$ 550")

    def test_money_long(self):
        self.assertEqual(fmt.money_long(5006104), "US$ 5,0 milhões")
        self.assertEqual(fmt.money_long(1500000), "US$ 1,5 milhão")
        self.assertEqual(fmt.money_long(3030000000), "US$ 3,03 bilhões")
        self.assertEqual(fmt.money_long(1000000000), "US$ 1,00 bilhão")
        self.assertEqual(fmt.money_long(929174), "US$ 929.174")

    def test_pct(self):
        self.assertEqual(fmt.pct(0.5), "50%")
        self.assertEqual(fmt.pct(196 / 391.0), "50%")
        self.assertEqual(fmt.pct(0.005), "1%")
        self.assertEqual(fmt.pct1(103 / 173.0), "59,5%")
        self.assertEqual(fmt.pct1(103 / 220.0), "46,8%")
        self.assertEqual(fmt.pct1(0.66), "66,0%")
        self.assertEqual(fmt.pct(None), "—")
        self.assertEqual(fmt.pct1(None), "—")


class PluralTest(unittest.TestCase):
    def test_plural(self):
        self.assertEqual(fmt.plural(1, "deal"), "1 deal")
        self.assertEqual(fmt.plural(2, "deal"), "2 deals")
        self.assertEqual(fmt.plural(0, "deal"), "0 deals")
        self.assertEqual(fmt.plural(2078, "deal"), "2.078 deals")
        self.assertEqual(fmt.plural(3, "vendedor", "vendedores"), "3 vendedores")
        self.assertEqual(fmt.plural_word(1, "cliente"), "cliente")
        self.assertEqual(fmt.days(1), "1 dia")
        self.assertEqual(fmt.days(73), "73 dias")


class DateTest(unittest.TestCase):
    def test_labels(self):
        d = date(2017, 12, 4)
        self.assertEqual(fmt.day_month(d), "4 dez")
        self.assertEqual(fmt.date_label(d), "4 dez 2017")
        self.assertEqual(fmt.date_short(d), "seg, 4 dez 2017")
        self.assertEqual(fmt.date_long(d), "segunda-feira, 4 de dezembro de 2017")
        self.assertEqual(fmt.month_name(date(2017, 3, 6)), "março")
        self.assertEqual(fmt.date_short(date(2017, 12, 9)), "sáb, 9 dez 2017")

    def test_date_in_context(self):
        ref = date(2017, 12, 4)
        self.assertEqual(fmt.date_in_context(date(2017, 9, 22), ref), "22 set")
        self.assertEqual(fmt.date_in_context(date(2016, 12, 5), ref), "5 dez 2016")

    def test_join_and_day_long(self):
        self.assertEqual(fmt.join([]), "")
        self.assertEqual(fmt.join(["A"]), "A")
        self.assertEqual(fmt.join(["A", "B"]), "A e B")
        self.assertEqual(fmt.join(x for x in "ABC"), "A, B e C")
        self.assertEqual(fmt.day_long(date(2017, 12, 4)), "4 de dezembro de 2017")


if __name__ == "__main__":
    unittest.main()
