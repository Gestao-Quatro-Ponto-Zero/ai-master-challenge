"""Testes da formatação PT-BR."""

import math

import pytest

from scorer import fmt


@pytest.mark.parametrize(
    "value, expected",
    [(1291, "1.291"), (8800, "8.800"), (0, "0"), (3198664, "3.198.664"), (2.5, "3"), (1.4, "1")],
)
def test_fmt_int(value, expected):
    assert fmt.fmt_int(value) == expected


def test_fmt_pct_and_dec():
    assert fmt.fmt_pct(0.632, 1) == "63,2%"
    assert fmt.fmt_pct(0.8352, 1) == "83,5%"
    assert fmt.fmt_pct(0.0044, 1) == "0,4%"
    assert fmt.fmt_pct(0.145, 0) == "15%"  # metade arredonda para cima
    assert fmt.fmt_dec(0.9965, 3) == "0,997"
    assert fmt.fmt_dec(1234.5, 1) == "1.234,5"


def test_fmt_usd():
    assert fmt.fmt_usd(4821) == "US$ 4.821"
    assert fmt.fmt_usd(3198664) == "US$ 3.198.664"
    assert fmt.fmt_usd(-55) == "-US$ 55"


def test_fmt_usd_compact():
    assert fmt.fmt_usd_compact(3198664) == "US$ 3,2 mi"
    assert fmt.fmt_usd_compact(1073986, decimals=2) == "US$ 1,07 mi"
    assert fmt.fmt_usd_compact(392850) == "US$ 393 mil"
    assert fmt.fmt_usd_compact(55) == "US$ 55"


def test_fmt_pp_and_dates():
    assert fmt.fmt_pp(0.019) == "+1,9 pp"
    assert fmt.fmt_pp(-0.03) == "-3,0 pp"
    assert fmt.fmt_date("2017-12-31") == "31/12/2017"
    assert fmt.fmt_month("2017-03") == "mar/2017"
    assert fmt.fmt_quarter("2017Q1") == "2017-Q1"
    assert fmt.fmt_quarter("2017-Q1") == "2017-Q1"


def test_missing_values_become_a_dash():
    for func in (fmt.fmt_int, fmt.fmt_usd, fmt.fmt_usd_compact, fmt.fmt_pct, fmt.fmt_date):
        assert func(None) == "—"
    assert fmt.fmt_int(math.nan) == "—"
