"""Tema Foco — façade que reexporta tokens, CSS e componentes.

O tema foi quebrado em submódulos por responsabilidade — `tokens` (paleta /
estilos), `styles` (CSS + injeção) e `components` (HTML dos cards/breakdown/
brief/funil) — mas o ponto de import continua sendo `app.theme`:

    from app.theme import inject_css, deal_card_html, COLORS  # inalterado

Quebra é só organização: a aparência renderizada é idêntica.
"""
from app.theme.tokens import COLORS, TIER_STYLE, SIGNAL_STYLE, SIGNAL_ICON
from app.theme.styles import CSS, inject_css
from app.theme.components import (
    tier_pill, deal_card_html, deal_card_compact_html, kanban_head_html,
    brief_panel_html, funnel_html, breakdown_html, rep_card_html,
)

__all__ = [
    "COLORS", "TIER_STYLE", "SIGNAL_STYLE", "SIGNAL_ICON",
    "CSS", "inject_css",
    "tier_pill", "deal_card_html", "deal_card_compact_html", "kanban_head_html",
    "brief_panel_html", "funnel_html", "breakdown_html", "rep_card_html",
]
