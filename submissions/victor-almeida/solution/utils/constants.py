"""
Constantes globais do Lead Scorer.

Valores calibrados a partir da análise exploratória do dataset
CRM Sales Predictive Analytics (referência: 2017-12-31).
"""

import pandas as pd

# === Data de referência ===
REFERENCE_DATE = pd.Timestamp('2017-12-31')

# === Preços dos produtos ===
PRODUCT_PRICES = {
    'GTK 500': 26768,
    'GTX Plus Pro': 5482,
    'GTX Pro': 4821,
    'MG Advanced': 3393,
    'GTX Plus Basic': 1096,
    'GTX Basic': 550,
    'MG Special': 55,
}

MAX_PRODUCT_PRICE = 26768
MIN_PRODUCT_PRICE = 55
PRICE_RATIO = 486.7

# === Win rates por produto ===
PRODUCT_WIN_RATES = {
    'MG Special': 0.648,
    'GTX Plus Pro': 0.643,
    'GTX Basic': 0.637,
    'GTX Pro': 0.636,
    'GTX Plus Basic': 0.621,
    'MG Advanced': 0.603,
    'GTK 500': 0.600,
}

OVERALL_WIN_RATE = 0.632

# === Velocity benchmarks ===
VELOCITY_MEDIAN_WON = 57
VELOCITY_P75_WON = 88
VELOCITY_P90_WON = 106
VELOCITY_REFERENCE_ENGAGING = 88
VELOCITY_REFERENCE_PROSPECTING = None  # No dates for Prospecting

# === Deal Zombie thresholds ===
ZOMBIE_THRESHOLD_MULTIPLIER = 2.0
ZOMBIE_CRITICAL_PERCENTILE = 75

# === Seller-Deal Fit ===
SELLER_FIT_MIN_DEALS = 5

# === Account Health ===
ACCOUNT_HEALTH_MIN_DEALS = 3
ACCOUNT_HEALTH_NEUTRAL = 0.5

# === Recurrent Loss ===
RECURRENT_LOSS_THRESHOLD = 2

# === Close Value stats (from Won deals) ===
CLOSE_VALUE_MAX = 30288.0
CLOSE_VALUE_MEDIAN = 1117.0
CLOSE_VALUE_P75 = 4430.0
CLOSE_VALUE_P25 = 518.0
CLOSE_VALUE_MEAN = 2360.9

# === Deal stages ===
ACTIVE_STAGES = {'Prospecting', 'Engaging'}
CLOSED_STAGES = {'Won', 'Lost'}
ALL_STAGES = {'Prospecting', 'Engaging', 'Won', 'Lost'}

# === Normalization constants ===
NORMALIZATION_MAX_VALUE = 30288.0  # For log normalization of value component
