"""Formatação em português do Brasil: dinheiro, percentuais, números, datas e plural.

Arredondamento sempre "meio para cima" (59,45 vira 59,5), nunca o arredondamento bancário.
"""
from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Optional, Union

Number = Union[int, float]

MONTHS_SHORT = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
MONTHS_LONG = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
               "outubro", "novembro", "dezembro")
WEEKDAYS_SHORT = ("seg", "ter", "qua", "qui", "sex", "sáb", "dom")
WEEKDAYS_LONG = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo")


def _round(value: Number, places: int) -> Decimal:
    return Decimal(repr(value)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def number(value: Number, places: int = 0) -> str:
    """8800 -> "8.800"; number(59.45, 1) -> "59,5"."""
    q = _round(value, places)
    sign = "-" if q < 0 else ""
    text = "{:,.{p}f}".format(abs(q), p=places)
    return sign + text.replace(",", "_").replace(".", ",").replace("_", ".")


def money(value: Number) -> str:
    """"US$ 5.482" (inteiro)."""
    text = number(value)
    return ("-US$ " + text[1:]) if text.startswith("-") else "US$ " + text


def money_short(value: Number) -> str:
    """Curto para cartões: "US$ 3,0 bi", "US$ 7,0 mi", "US$ 929 mil", "US$ 42,2 mil", "US$ 550"."""
    v = abs(value)
    sign = "-" if value < 0 else ""
    if _round(v / 1e9, 1) >= 1 or _round(v / 1e6, 1) >= 1000:
        return "%sUS$ %s bi" % (sign, number(v / 1e9, 1))
    if _round(v / 1e6, 1) >= 1 or _round(v / 1e3, 0) >= 1000:
        return "%sUS$ %s mi" % (sign, number(v / 1e6, 1))
    if v >= 1000:
        places = 0 if _round(v / 1e3, 1) >= 100 else 1
        return "%sUS$ %s mil" % (sign, number(v / 1e3, places))
    return money(value)


def money_long(value: Number) -> str:
    """Por extenso: "US$ 5,0 milhões", "US$ 1,5 milhão", "US$ 3,03 bilhões"; abaixo de 1 milhão, money()."""
    v = abs(value)
    sign = "-" if value < 0 else ""
    if _round(v / 1e9, 2) >= 1 or _round(v / 1e6, 1) >= 1000:
        q = _round(v / 1e9, 2)
        return "%sUS$ %s %s" % (sign, number(v / 1e9, 2), "bilhão" if q < 2 else "bilhões")
    if _round(v / 1e6, 1) >= 1:
        q = _round(v / 1e6, 1)
        return "%sUS$ %s %s" % (sign, number(v / 1e6, 1), "milhão" if q < 2 else "milhões")
    return money(value)


def pct(fraction: Optional[float]) -> str:
    """Fração 0-1 para "50%"; None vira "—"."""
    return "—" if fraction is None else number(fraction * 100, 0) + "%"


def pct1(fraction: Optional[float]) -> str:
    """Fração 0-1 para "59,5%"; None vira "—"."""
    return "—" if fraction is None else number(fraction * 100, 1) + "%"


def plural_word(n: Number, singular: str, plural_form: Optional[str] = None) -> str:
    """Só a palavra: plural_word(2, "deal") -> "deals". Plural irregular em plural_form."""
    return singular if abs(n) == 1 else (plural_form or singular + "s")


def plural(n: Number, singular: str, plural_form: Optional[str] = None) -> str:
    """Número formatado e palavra: "1 deal", "2.078 deals", plural(3, "vendedor", "vendedores")."""
    return "%s %s" % (number(n), plural_word(n, singular, plural_form))


def join(items: Iterable[str]) -> str:
    """"A", "A e B", "A, B e C"; lista vazia vira ""."""
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return "%s e %s" % (", ".join(items[:-1]), items[-1])


def days(n: int) -> str:
    """"1 dia", "73 dias"."""
    return plural(n, "dia")


def day_month(d: date) -> str:
    """"4 dez"."""
    return "%d %s" % (d.day, MONTHS_SHORT[d.month - 1])


def date_label(d: date) -> str:
    """"4 dez 2017"."""
    return "%s %d" % (day_month(d), d.year)


def date_short(d: date) -> str:
    """"seg, 4 dez 2017"."""
    return "%s, %s" % (WEEKDAYS_SHORT[d.weekday()], date_label(d))


def date_long(d: date) -> str:
    """"segunda-feira, 4 de dezembro de 2017"."""
    return "%s, %s" % (WEEKDAYS_LONG[d.weekday()], day_long(d))


def day_long(d: date) -> str:
    """"4 de dezembro de 2017"."""
    return "%d de %s de %d" % (d.day, MONTHS_LONG[d.month - 1], d.year)


def month_name(d: date) -> str:
    """"dezembro"."""
    return MONTHS_LONG[d.month - 1]


def date_in_context(d: date, ref: date) -> str:
    """"22 set" quando o ano é o mesmo de ref; senão "5 dez 2016"."""
    return day_month(d) if d.year == ref.year else date_label(d)
