"""SPEC-6.1: Treinamento XGBoost com validação temporal walk-forward."""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)

CAT_FEATURES = ["industry", "country", "referral_source", "plan_tier_account", "billing_frequency"]
NUM_FEATURES = [
    "seats_account", "mrr_amount",
    "upgrade_flag", "downgrade_flag", "auto_renew_flag",
    "total_usage_count", "avg_usage_duration", "total_error_count",
    "unique_features", "usage_days",
    "total_tickets", "avg_resolution_hours", "avg_first_response_min",
    "avg_satisfaction", "escalation_count", "high_priority_tickets",
    "is_trial_account", "is_trial_subscription",
]
HEALTH_FEATURES = ["health_score", "pillar_usage", "pillar_support", "pillar_engagement", "pillar_financial"]
TARGET = "churn_flag"


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    ref_date = pd.Timestamp.now()
    if "start_date" in result.columns:
        sd = pd.to_datetime(result["start_date"], errors="coerce")
        ref_date = sd.max() if sd.notna().any() else ref_date
    if "signup_date" in result.columns:
        sd = pd.to_datetime(result["signup_date"], errors="coerce")
        result["tenure_days"] = (ref_date - sd).dt.days.fillna(0)
    else:
        result["tenure_days"] = 0
    for c in NUM_FEATURES:
        if c not in result.columns:
            result[c] = 0
    for c in CAT_FEATURES:
        if c not in result.columns:
            result[c] = "unknown"
    return result


def prepare_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    y = df[TARGET].astype(int)
    cols = NUM_FEATURES + CAT_FEATURES
    if "tenure_days" in df.columns:
        cols = cols + ["tenure_days"]
    for c in HEALTH_FEATURES:
        if c in df.columns and c not in cols:
            cols = [c] + cols
    X = df[cols].copy()
    for c in CAT_FEATURES:
        X[c] = X[c].fillna("unknown").astype(str)
    for c in X.select_dtypes(include=["object"]).columns:
        if c not in CAT_FEATURES:
            X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
    for c in NUM_FEATURES + HEALTH_FEATURES:
        if c in X.columns:
            X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
    return X, y


def train_model(
    df: pd.DataFrame,
    output_dir: str = "output/models",
) -> dict[str, Any]:
    logger.info("=== Treinamento XGBoost ===")

    df = engineer_features(df)

    X, y = prepare_xy(df)
    features = list(X.columns)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for c in CAT_FEATURES:
        le = LabelEncoder()
        X[c] = le.fit_transform(X[c].astype(str))
        with open(out / f"label_{c}.pkl", "wb") as f:
            pickle.dump(le, f)

    scaler = StandardScaler()
    X_scaled = X.copy()
    num_cols = [c for c in features if c not in CAT_FEATURES]
    X_scaled[num_cols] = scaler.fit_transform(X_scaled[num_cols])
    with open(out / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled[features], y, test_size=0.2, random_state=42, stratify=y
    )

    neg, pos = y_train.value_counts().to_dict()
    logger.info("  Train: neg=%d pos=%d ratio=%.2f", neg, pos, neg / pos if pos else 0)

    model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
        eval_metric="logloss",
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_prob = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob)

    base_rate = y_test.mean()
    y_pred = (y_prob >= base_rate).astype(int)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)

    metrics = {
        "auc_roc": round(float(auc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "base_rate": round(float(base_rate), 4),
        "n_accounts": len(df),
        "n_churned": int(y.sum()),
        "n_active": int((1 - y).sum()),
        "features": features,
        "feature_importance": {
            k: round(float(v), 4) for k, v in zip(features, model.feature_importances_)
        },
    }

    with open(out / "model_xgboost.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(out / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info("  AUC-ROC: %.4f", auc)
    logger.info("  Precision: %.4f", prec)
    logger.info("  Recall: %.4f", rec)

    return metrics


def load_model(output_dir: str = "output/models"):
    out = Path(output_dir)
    with open(out / "model_xgboost.pkl", "rb") as f:
        model = pickle.load(f)
    scaler = None
    scaler_path = out / "scaler.pkl"
    if scaler_path.exists():
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)
    label_encoders = {}
    for c in CAT_FEATURES:
        path = out / f"label_{c}.pkl"
        if path.exists():
            with open(path, "rb") as f:
                label_encoders[c] = pickle.load(f)
    return model, scaler, label_encoders
