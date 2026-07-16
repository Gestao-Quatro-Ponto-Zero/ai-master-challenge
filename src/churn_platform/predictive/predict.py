"""SPEC-6.2: Predição de churn para contas ativas."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from .train import (
    CAT_FEATURES,
    HEALTH_FEATURES,
    NUM_FEATURES,
    engineer_features,
    load_model,
    prepare_xy,
)

logger = logging.getLogger(__name__)


def predict_churn(
    df: pd.DataFrame,
    output_dir: str = "output/models",
) -> pd.DataFrame:
    logger.info("=== Predição de Churn ===")

    model, scaler, label_encoders = load_model(output_dir)
    df_feat = engineer_features(df)

    for col in HEALTH_FEATURES:
        if col in df.columns and col not in df_feat.columns:
            df_feat[col] = df[col].fillna(50)

    X, _ = prepare_xy(df_feat)

    for c in CAT_FEATURES:
        le = label_encoders.get(c)
        if le:
            X[c] = X[c].map(lambda v: le.transform([v])[0] if v in le.classes_ else -1).astype(int)

    features = list(model.feature_names_in_)
    for f in features:
        if f not in X.columns:
            X[f] = 0

    X = X[features]

    num_cols = [c for c in features if c not in CAT_FEATURES]
    if scaler:
        X[num_cols] = scaler.transform(X[num_cols])

    y_prob = model.predict_proba(X)[:, 1]

    result = df[["account_id", "account_name", "industry", "mrr_amount", "churn_flag"]].copy()
    result["churn_probability"] = np.round(y_prob, 4)

    def risk_label(p: float) -> str:
        if p >= 0.5:
            return "High"
        elif p >= 0.3:
            return "Medium"
        elif p >= 0.15:
            return "Low"
        return "Minimal"

    result["churn_risk_label"] = result["churn_probability"].apply(risk_label)

    active = result[result["churn_flag"] == False].sort_values("churn_probability", ascending=False)
    n_high = (active["churn_probability"] >= 0.5).sum()
    n_med = ((active["churn_probability"] >= 0.3) & (active["churn_probability"] < 0.5)).sum()
    logger.info("  Ativas: %d high, %d medium, %d low/minimal", n_high, n_med, len(active) - n_high - n_med)

    return result
