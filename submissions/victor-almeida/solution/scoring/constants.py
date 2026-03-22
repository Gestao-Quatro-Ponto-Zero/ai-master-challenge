"""
Constantes do Scoring Engine.

Pesos, thresholds, tabelas de decay e configuracoes do motor de scoring.
"""

import pandas as pd

# === Data de referencia ===
REFERENCE_DATE = pd.Timestamp("2017-12-31")

# === Stages ativos (recebem score) ===
ACTIVE_STAGES = ["Prospecting", "Engaging"]
CLOSED_STAGES = ["Won", "Lost"]

# === Pesos dos componentes ===
WEIGHTS = {
    "stage": 0.35,
    "expected_value": 0.25,
    "velocity": 0.15,
    "seller_fit": 0.10,
    "account_health": 0.15,
}

# === Stage Score ===
STAGE_SCORES = {
    "Prospecting": 15,
    "Engaging": 90,
}

# === Value Score ===
# Max value for log normalization (max product price)
VALUE_MAX_REFERENCE = 26768  # GTK 500

# === Velocity Score ===
STAGE_REFERENCE_DAYS = {
    "Prospecting": None,  # No temporal data available
    "Engaging": 88,       # P75 of Won deals (Engaging -> Close)
}

# Decay table: (ratio_max, decay_factor, label)
DECAY_TABLE = [
    (1.0, 1.00, "saudavel"),
    (1.5, 0.80, "atencao"),
    (2.0, 0.55, "alerta"),
    (3.0, 0.30, "candidato_zumbi"),
    (float("inf"), 0.10, "quase_morto"),
]

# Zombie thresholds
ZOMBIE_THRESHOLD = 2.0
ZOMBIE_CRITICAL_PERCENTILE = 75

# Velocity neutral score (for Prospecting or missing data)
VELOCITY_NEUTRAL_SCORE = 50.0

# === Seller Fit ===
SELLER_FIT_MIN_DEALS = 5
FIT_MULTIPLIER_MIN = 0.3
FIT_MULTIPLIER_MAX = 2.0
FIT_NEUTRAL_SCORE = 50.0
SELLER_FIT_SCALE_FACTOR = 80  # score = 50 + (mult - 1.0) * scale

# === Account Health ===
ACCOUNT_HEALTH_MIN_DEALS = 3
ACCOUNT_HEALTH_NEUTRAL = 50.0
RECENT_LOSS_PENALTY = 5.0
RECENT_LOSS_WINDOW_DAYS = 180
MAX_LOSS_PENALTY = 15.0
ACCOUNT_HEALTH_WR_MIN = 0.50
ACCOUNT_HEALTH_WR_MAX = 0.80

# === Score color bands (for UI) ===
SCORE_BANDS = [
    {"name": "Critico", "min": 0, "max": 40, "color": "#e74c3c"},
    {"name": "Risco", "min": 40, "max": 60, "color": "#e67e22"},
    {"name": "Atencao", "min": 60, "max": 80, "color": "#f1c40f"},
    {"name": "Alta Prioridade", "min": 80, "max": 100, "color": "#2ecc71"},
]
