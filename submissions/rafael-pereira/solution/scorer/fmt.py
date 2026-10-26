"""Formatação de números e datas em PT-BR (milhar com ponto, decimal com vírgula)."""

from __future__ import annotations

import math
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

MONTHS_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MISSING = "—"


def round_half_up(x: float, ndigits: int = 0) -> float:
    """Arredonda metade para cima (o `round` do Python arredonda metade para o par).

    Antes, descarta o ruído de ponto flutuante (14.499999999999998 vale 14.5).
    """
    quantum = Decimal(1).scaleb(-ndigits)
    return float(Decimal(str(round(float(x), 10))).quantize(quantum, rounding=ROUND_HALF_UP))


def _is_missing(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def _to_pt(number: str) -> str:
    """Troca os separadores do formato en-US ('1,234.5') para o PT-BR ('1.234,5')."""
    return number.replace(",", "\0").replace(".", ",").replace("\0", ".")


def fmt_int(x) -> str:
    """fmt_int(1291) -> '1.291'."""
    if _is_missing(x):
        return MISSING
    return _to_pt(f"{int(round_half_up(x)):,}")


def fmt_dec(x, ndigits: int = 2) -> str:
    """fmt_dec(0.996, 3) -> '0,996'."""
    if _is_missing(x):
        return MISSING
    return _to_pt(f"{round_half_up(x, ndigits):,.{ndigits}f}")


def fmt_pct(frac, ndigits: int = 1) -> str:
    """fmt_pct(0.632, 1) -> '63,2%' (recebe a fração, não a porcentagem)."""
    if _is_missing(frac):
        return MISSING
    return fmt_dec(frac * 100, ndigits) + "%"


def fmt_pp(diff_frac, ndigits: int = 1) -> str:
    """Diferença em pontos percentuais com sinal: fmt_pp(0.019) -> '+1,9 pp'."""
    if _is_missing(diff_frac):
        return MISSING
    text = fmt_dec(diff_frac * 100, ndigits)
    return ("+" if diff_frac > 0 else "") + text + " pp"


def fmt_usd(x) -> str:
    """fmt_usd(4821) -> 'US$ 4.821'."""
    if _is_missing(x):
        return MISSING
    sign = "-" if x < 0 else ""
    return f"{sign}US$ {fmt_int(abs(x))}"


def fmt_usd_compact(x, decimals: int | None = None) -> str:
    """Valor compacto: 3198664 -> 'US$ 3,2 mi'; 393000 -> 'US$ 393 mil'.

    `decimals` troca o número de casas (padrão: 1 em milhões, 0 em milhares).
    """
    if _is_missing(x):
        return MISSING
    sign = "-" if x < 0 else ""
    value = abs(x)
    if value >= 1_000_000:
        return f"{sign}US$ {fmt_dec(value / 1_000_000, 1 if decimals is None else decimals)} mi"
    if value >= 1_000:
        return f"{sign}US$ {fmt_dec(value / 1_000, 0 if decimals is None else decimals)} mil"
    return fmt_usd(x)


def _as_date(x) -> date:
    if isinstance(x, str):
        return date.fromisoformat(x[:10])
    return x


def fmt_date(x) -> str:
    """fmt_date('2017-12-31') -> '31/12/2017' (aceita texto ISO, date ou Timestamp)."""
    if _is_missing(x) or str(x) == "NaT":
        return MISSING
    return _as_date(x).strftime("%d/%m/%Y")


def fmt_month(x) -> str:
    """fmt_month('2017-03') -> 'mar/2017'."""
    year, month = str(x)[:7].split("-")
    return f"{MONTHS_PT[int(month) - 1]}/{year}"


def fmt_quarter(x) -> str:
    """fmt_quarter('2017Q1') -> '2017-Q1'."""
    text = str(x)
    return text if "-Q" in text else text.replace("Q", "-Q")
