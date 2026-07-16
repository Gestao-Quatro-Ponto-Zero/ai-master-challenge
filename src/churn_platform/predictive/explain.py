"""SPEC-6.3: SHAP explainability para predições de churn."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shap

from .train import (
    CAT_FEATURES,
    HEALTH_FEATURES,
    NUM_FEATURES,
    engineer_features,
    load_model,
    prepare_xy,
)

logger = logging.getLogger(__name__)


def explain_model(
    df: pd.DataFrame,
    output_dir: str = "output/models",
    top_n: int = 50,
) -> dict[str, Any]:
    logger.info("=== SHAP Explanation ===")

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

    X_model = X

    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_model)

    global_importance = {}
    for i, feat in enumerate(features):
        global_importance[feat] = float(np.abs(shap_values.values[:, i]).mean())

    global_ranked = sorted(global_importance.items(), key=lambda x: -x[1])

    account_explanations = []
    for idx in range(min(top_n, len(df))):
        account_id = df.iloc[idx]["account_id"]
        shap_row = shap_values.values[idx]

        feat_contrib = [(features[i], float(shap_row[i])) for i in range(len(features))]
        feat_contrib.sort(key=lambda x: -abs(x[1]))

        top_risk = [{"feature": f, "contribution": round(c, 4)} for f, c in feat_contrib[:5] if c > 0]
        top_protect = [{"feature": f, "contribution": round(c, 4)} for f, c in feat_contrib[:5] if c < 0]

        account_explanations.append({
            "account_id": account_id,
            "churn_probability": round(float(model.predict_proba(X_model.iloc[[idx]])[:, 1][0]), 4),
            "top_risk_factors": top_risk[:3],
            "top_protective_factors": top_protect[:3],
        })

    result = {
        "global_feature_importance": [{"feature": f, "mean_abs_shap": round(v, 4)} for f, v in global_ranked],
        "accounts": account_explanations,
    }

    out = Path(output_dir)
    with open(out / "shap_explanations.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    logger.info("  Top features: %s", [f for f, _ in global_ranked[:5]])

    return result
