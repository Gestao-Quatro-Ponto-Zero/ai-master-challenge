"""Tokens de marca — paleta, estilos de tier e de sinal.

Fonte única de verdade visual (espelha branding/BRANDING.md §3-4):
base clara, indigo como cor de ação, prioridade = cor + ícone + texto.
"""

COLORS = {
    # marca
    "ink": "#26324D", "ink_soft": "#3B4964", "slate": "#667085",
    "slate_2": "#98A2B3", "surface": "#FFFFFF", "canvas": "#F6F8FC",
    "canvas_2": "#EEF3FA", "border": "#D9E2EF", "border_soft": "#E9EEF6",
    "brand": "#5B5BD6", "brand_700": "#4747B8", "brand_soft": "#ECECFF",
    "accent": "#2F8EA8",
    # prioridade (tiers)
    "focus": "#C84242", "focus_soft": "#FFF1F1",
    "work": "#A96E1F", "work_soft": "#FFF5E5",
    "low": "#5F6F89", "low_soft": "#EEF3FA",
    # sinais de fator
    "positive": "#2F7D5B", "positive_soft": "#EAF5EF",
    "warning": "#A96E1F", "warning_soft": "#FFF5E5",
    "danger": "#C84242", "danger_soft": "#FFF1F1",
}

TIER_STYLE = {
    "Foco Agora":       {"icon": "🔥", "fg": COLORS["focus"], "bg": COLORS["focus_soft"]},
    "Trabalhar":        {"icon": "⭐", "fg": COLORS["work"],  "bg": COLORS["work_soft"]},
    "Baixa Prioridade": {"icon": "⏳", "fg": COLORS["low"],   "bg": COLORS["low_soft"]},
}

SIGNAL_STYLE = {
    "positivo": {"icon": "🟢", "fg": COLORS["positive"], "bg": COLORS["positive_soft"]},
    "alerta":   {"icon": "🟠", "fg": COLORS["warning"],  "bg": COLORS["warning_soft"]},
    "critico":  {"icon": "🔴", "fg": COLORS["danger"],   "bg": COLORS["danger_soft"]},
    "neutro":   {"icon": "⚪", "fg": COLORS["slate"],    "bg": COLORS["canvas_2"]},
}
SIGNAL_ICON = {k: v["icon"] for k, v in SIGNAL_STYLE.items()}
