"""
Testes para utils/formatters.py

Cobre: format_currency, format_percentage, format_days, score_color, score_label.
"""

from utils.formatters import (
    format_currency,
    format_days,
    format_percentage,
    score_color,
    score_label,
)


# ── Moeda ────────────────────────────────────────────────────────────────────

class TestFormatCurrency:
    def test_format_currency_millions(self):
        assert format_currency(1_200_000) == "$1.2M"

    def test_format_currency_thousands(self):
        assert format_currency(45_000) == "$45K"

    def test_format_currency_small(self):
        assert format_currency(55) == "$55"

    def test_format_currency_zero(self):
        assert format_currency(0) == "$0"

    def test_format_currency_hundreds(self):
        assert format_currency(550) == "$550"


# ── Percentual ───────────────────────────────────────────────────────────────

class TestFormatPercentage:
    def test_format_percentage_normal(self):
        assert format_percentage(0.632) == "63.2%"

    def test_format_percentage_zero(self):
        assert format_percentage(0.0) == "0.0%"

    def test_format_percentage_one(self):
        assert format_percentage(1.0) == "100.0%"


# ── Dias ─────────────────────────────────────────────────────────────────────

class TestFormatDays:
    def test_format_days_normal(self):
        assert format_days(34) == "34 dias"

    def test_format_days_none(self):
        assert format_days(None) == "\u2014"


# ── Cor por score ────────────────────────────────────────────────────────────

class TestScoreColor:
    def test_score_color_green_80_plus(self):
        assert score_color(85) == "#2ecc71"

    def test_score_color_yellow_60_to_79(self):
        assert score_color(65) == "#f1c40f"

    def test_score_color_orange_40_to_59(self):
        assert score_color(45) == "#e67e22"

    def test_score_color_red_below_40(self):
        assert score_color(20) == "#e74c3c"
