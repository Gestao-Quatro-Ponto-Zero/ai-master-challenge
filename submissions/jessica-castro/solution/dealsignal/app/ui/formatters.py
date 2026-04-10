"""
DealSignal UI — Display formatting utilities.

Pure functions that convert raw values to human-readable strings or HTML.
No Streamlit state; safe to call from any UI module.
"""

import pandas as pd

from config.constants import ENGINE_SCORE_MODERATE, ENGINE_SCORE_STRONG, RATING_COLORS
from app.ui.ui_constants import _BADGE_STYLE, _ENGINE_INTERPRETATIONS


def format_probability_bar(prob: float) -> str:
    """Renders a text-based probability bar, e.g. '72.0%  ███████░░░'."""
    pct    = round(float(prob) * 100, 1)
    filled = max(0, min(10, round(float(prob) * 10)))
    return f"{pct}%  {'█' * filled}{'░' * (10 - filled)}"


def format_currency(value: float) -> str:
    """Formats a numeric value as a currency string, e.g. '$42,000'."""
    return f"${value:,.0f}" if pd.notna(value) else "—"


def _engine_label(score: int) -> str:
    """Returns an emoji + label string for a 0–100 engine score."""
    if score >= ENGINE_SCORE_STRONG:
        return "🟢 Forte"
    if score >= ENGINE_SCORE_MODERATE:
        return "🟡 Moderado"
    return "🔴 Fraco"


def _engine_position(score: int) -> str:
    """Returns a descriptive position string for a 0–100 engine score."""
    if score >= ENGINE_SCORE_STRONG:
        return "Entre os mais fortes"
    if score >= ENGINE_SCORE_MODERATE:
        return "Na faixa intermediária"
    return "Entre os mais fracos"


def _engine_interpretation(engine: str, score: int) -> str:
    """Returns the interpretation text for the given engine and score band."""
    texts = _ENGINE_INTERPRETATIONS.get(engine, {})
    if score >= ENGINE_SCORE_STRONG:
        return texts.get("strong", "")
    if score >= ENGINE_SCORE_MODERATE:
        return texts.get("moderate", "")
    return texts.get("weak", "")


def _rating_badge(rating: str) -> str:
    """Returns a coloured HTML badge for a rating label (e.g. 'AAA')."""
    color = RATING_COLORS.get(rating, "#888888")
    return f'<span style="background:{color}; {_BADGE_STYLE}">{rating}</span>'
