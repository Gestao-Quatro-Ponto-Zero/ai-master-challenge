"""
DealSignal — Central constants module.

Single source of truth for all numeric thresholds, visual palettes, and
configuration values used across the application. Import from here instead
of defining literals inline in individual modules.
"""

# ── Rating thresholds ────────────────────────────────────────────────────────
# (win_probability_floor, rating_label) — ordered from highest to lowest
RATING_THRESHOLDS: list[tuple[float, str]] = [
    (0.90, "AAA"),
    (0.80, "AA"),
    (0.70, "A"),
    (0.60, "BBB"),
    (0.50, "BB"),
    (0.40, "B"),
    (0.00, "CCC"),
]

RATING_ORDER: list[str] = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]

RATING_RANGES: dict[str, str] = {
    "AAA": "> 90%",
    "AA":  "80 – 90%",
    "A":   "70 – 80%",
    "BBB": "60 – 70%",
    "BB":  "50 – 60%",
    "B":   "40 – 50%",
    "CCC": "< 40%",
}

# ── UI colour palette (hex — Streamlit / Plotly) ─────────────────────────────
RATING_COLORS: dict[str, str] = {
    "AAA": "#1a7a1a",
    "AA":  "#2ecc71",
    "A":   "#82e0aa",
    "BBB": "#f39c12",
    "BB":  "#e67e22",
    "B":   "#e74c3c",
    "CCC": "#922b21",
}

# Emoji indicators used in the pipeline table
RATING_EMOJI: dict[str, str] = {
    "AAA": "🟢",
    "AA":  "🟢",
    "A":   "🟢",
    "BBB": "🟠",
    "BB":  "🟠",
    "B":   "🔴",
    "CCC": "🔴",
}

# ── PDF colour palette (R, G, B tuples — fpdf2) ──────────────────────────────
RATING_RGB: dict[str, tuple[int, int, int]] = {
    "AAA": (26, 122, 26),
    "AA":  (46, 204, 113),
    "A":   (130, 224, 170),
    "BBB": (243, 156, 18),
    "BB":  (230, 126, 34),
    "B":   (231, 76, 60),
    "CCC": (146, 43, 33),
}

# ── Health engine ────────────────────────────────────────────────────────────
# pd.cut bins and labels for deal_health_score (0–100)
HEALTH_BINS: list[float]  = [-0.1, 45.0, 70.0, 100.1]
HEALTH_LABELS: list[str]  = ["Em risco", "Atenção", "Saudável"]

# ── Priority engine ──────────────────────────────────────────────────────────
# Multiplier applied to priority_score based on current deal health
HEALTH_MULTIPLIER: dict[str, float] = {
    "Saudável": 1.20,
    "Atenção":  0.90,
    "Em risco": 0.60,
}

# ── WoE transformer defaults ─────────────────────────────────────────────────
WOE_CAP: float           = 3.0   # clips WoE values to ±WOE_CAP to prevent outlier distortion
WOE_MIN_BIN_SIZE: float  = 0.05  # minimum fraction of rows per quantile bin

# ── Engine score thresholds (UI) ─────────────────────────────────────────────
# Used to colour-code the 0–100 engine bars in the deal panel
ENGINE_SCORE_STRONG: int   = 70   # >= this → "strong" (green)
ENGINE_SCORE_MODERATE: int = 45   # >= this → "moderate" (yellow); below → "weak" (red)
