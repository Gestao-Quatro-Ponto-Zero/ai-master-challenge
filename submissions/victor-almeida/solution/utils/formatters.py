"""
Funcoes de formatacao para exibicao na UI.

Moeda, percentual, dias e cores/labels de score.
"""

from scoring.constants import SCORE_BANDS


def format_currency(value: float) -> str:
    """Formata valor como moeda USD abreviada.

    >= 1_000_000 -> "$1.2M"
    >= 1_000    -> "$45K"
    < 1_000     -> "$55"
    """
    if value >= 1_000_000:
        formatted = f"{value / 1_000_000:.1f}"
        # Remove trailing ".0" for clean whole numbers
        if formatted.endswith(".0"):
            formatted = formatted[:-2]
        return f"${formatted}M"
    if value >= 1_000:
        formatted = f"{value / 1_000:.1f}"
        if formatted.endswith(".0"):
            formatted = formatted[:-2]
        return f"${formatted}K"
    return f"${value:g}"


def format_percentage(value: float) -> str:
    """Formata ratio (0-1) como string de percentual. 0.632 -> '63.2%'."""
    return f"{value * 100:.1f}%"


def format_days(days) -> str:
    """Formata contagem de dias. None -> '\u2014', 34 -> '34 dias'."""
    if days is None:
        return "\u2014"
    return f"{int(days)} dias"


def score_color(score: float) -> str:
    """Retorna cor hex para a faixa do score.

    >= 80 -> '#2ecc71' (verde)
    60-79 -> '#f1c40f' (amarelo)
    40-59 -> '#e67e22' (laranja)
    < 40  -> '#e74c3c' (vermelho)
    """
    for band in SCORE_BANDS:
        if band["min"] <= score <= band["max"]:
            return band["color"]
    # Fallback: score fora de range (< 0 ou > 100)
    if score > 100:
        return SCORE_BANDS[-1]["color"]
    return SCORE_BANDS[0]["color"]


def score_label(score: float) -> str:
    """Retorna label para a faixa do score.

    >= 80 -> 'Alta Prioridade'
    60-79 -> 'Atencao'
    40-59 -> 'Risco'
    < 40  -> 'Critico'
    """
    for band in SCORE_BANDS:
        if band["min"] <= score <= band["max"]:
            return band["name"]
    if score > 100:
        return SCORE_BANDS[-1]["name"]
    return SCORE_BANDS[0]["name"]
