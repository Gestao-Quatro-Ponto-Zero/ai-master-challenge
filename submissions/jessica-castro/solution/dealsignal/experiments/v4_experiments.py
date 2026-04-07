"""DealSignal V4 — Lead/Engagement Feature Experiments
=====================================================

Tests the impact of adding lead, engagement, and geographic features
(from previously unused pipeline columns) to the existing V2/V3 feature sets.

Experiments:
  1. V2 baseline (WoE + IV) — reference
  2. V2 + V4 lead/geo features + LR
  3. V3 + V4 lead/geo features + LR
  4. V3 + V4 + GradientBoosting (tuned)
  5. Ablation: contribution of each new feature group
  6. Feature importance ranking

Usage:
    cd solution/dealsignal
    python -m experiments.v4_experiments
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

EXPERIMENTS_DIR = Path(__file__).parent
ROOT = EXPERIMENTS_DIR.parent
sys.path.insert(0, str(ROOT))

from features.feature_engineering import build_features
from features.feature_columns import (
    FEATURE_COLS_V2,
    FEATURE_COLS_V4,
    FEATURE_COLS_V4_LEAD,
    FEATURE_COLS_V4_GEO,
)
from features.interaction_features import (
    FEATURE_COLS_V3,
    add_v3_features,
)
from model.feature_selection_iv import select_features_by_iv
from model.woe_transformer import WoETransformer

DATA_DIR = ROOT / "data"
OUTPUT_DIR = EXPERIMENTS_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

CV_FOLDS = 5
RANDOM_STATE = 42


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def cv_auc(X, y, estimator, n_splits=CV_FOLDS):
    X_clean = X.fillna(X.median())
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_validate(
        estimator, X_clean, y, cv=cv,
        scoring={"auc": "roc_auc", "ap": "average_precision"},
        n_jobs=-1, error_score="raise",
    )
    return {
        "cv_auc_mean": scores["test_auc"].mean(),
        "cv_auc_std":  scores["test_auc"].std(),
        "cv_ap_mean":  scores["test_ap"].mean(),
        "cv_ap_std":   scores["test_ap"].std(),
    }


def make_lr():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(C=1.0, class_weight="balanced",
                                   max_iter=1000, random_state=RANDOM_STATE)),
    ])


def make_rf():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=300, max_depth=7,
                                       class_weight="balanced",
                                       random_state=RANDOM_STATE, n_jobs=-1)),
    ])


def make_gbm():
    return GradientBoostingClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.05,
        min_samples_leaf=20, subsample=0.8,
        random_state=RANDOM_STATE,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Data loading
# ═══════════════════════════════════════════════════════════════════════════════

def load_data():
    print("▶ Carregando dados e construindo features V2 + V4 (lead/geo)...")
    accounts = pd.read_csv(DATA_DIR / "accounts.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")
    pipeline = pd.read_csv(DATA_DIR / "sales_pipeline.csv")
    teams = pd.read_csv(DATA_DIR / "sales_teams.csv")
    enriched = pd.read_csv(DATA_DIR / "enriched_accounts.csv")

    # build_features now includes lead + geo features (V4)
    feature_df, target = build_features(pipeline, accounts, products, teams, enriched)

    train_mask = target.notna()

    # Add V3 interaction features
    feature_df = add_v3_features(feature_df, train_mask)

    y_train = target[train_mask].astype(int)

    # V4 = V2 + lead + geo (already computed by build_features)
    FEATURE_COLS_V4_FULL = FEATURE_COLS_V4  # V2 + lead + geo

    # V3+V4 = V3 interaction features + V4 lead/geo features
    FEATURE_COLS_V3_V4 = list(dict.fromkeys(FEATURE_COLS_V3 + FEATURE_COLS_V4_LEAD + FEATURE_COLS_V4_GEO))

    print(f"   Train: {train_mask.sum():,} | V2: {len(FEATURE_COLS_V2)} | "
          f"V4: {len(FEATURE_COLS_V4_FULL)} | V3+V4: {len(FEATURE_COLS_V3_V4)}")

    return feature_df, y_train, train_mask, FEATURE_COLS_V4_FULL, FEATURE_COLS_V3_V4


# ═══════════════════════════════════════════════════════════════════════════════
# Experiments
# ═══════════════════════════════════════════════════════════════════════════════

def run_experiments():
    feature_df, y_train, train_mask, V4_COLS, V3_V4_COLS = load_data()
    X_train_full = feature_df[train_mask].copy()

    results = []

    # ── 1. Baseline: V2 + WoE + IV (production) ────────────────────────────
    print("\n═══ 1. Baseline V2 (WoE + IV) ═══")
    X_v2 = X_train_full[FEATURE_COLS_V2].copy()
    woe = WoETransformer(n_bins=10)
    woe.fit(X_v2, y_train)
    selected = select_features_by_iv(woe.iv_scores_, threshold=0.02)
    if not selected:
        selected = FEATURE_COLS_V2
    X_woe = woe.transform(X_v2[selected])
    scores = cv_auc(X_woe, y_train, LogisticRegression(C=1.0, class_weight="balanced",
                                                         max_iter=1000, random_state=RANDOM_STATE))
    print(f"   AUC={scores['cv_auc_mean']:.4f} ± {scores['cv_auc_std']:.4f}  "
          f"AP={scores['cv_ap_mean']:.4f}  ({len(selected)} features via IV)")
    results.append({"experimento": "1. Baseline V2 (WoE+IV)", "features": len(selected),
                    "modelo": "LR+WoE", **scores})

    # ── 2. V2 + lead/geo (V4) + LR ─────────────────────────────────────────
    print("\n═══ 2. V4 (V2 + lead/geo) + LR ═══")
    X_v4 = X_train_full[V4_COLS].copy()
    scores = cv_auc(X_v4, y_train, make_lr())
    print(f"   AUC={scores['cv_auc_mean']:.4f} ± {scores['cv_auc_std']:.4f}  "
          f"AP={scores['cv_ap_mean']:.4f}  ({len(V4_COLS)} features)")
    results.append({"experimento": "2. V4 (V2+lead/geo) + LR", "features": len(V4_COLS),
                    "modelo": "LR", **scores})

    # ── 3. V3 + V4 (all features) + LR ─────────────────────────────────────
    print("\n═══ 3. V3+V4 (all features) + LR ═══")
    available_v3v4 = [c for c in V3_V4_COLS if c in X_train_full.columns]
    X_v3v4 = X_train_full[available_v3v4].copy()
    scores = cv_auc(X_v3v4, y_train, make_lr())
    print(f"   AUC={scores['cv_auc_mean']:.4f} ± {scores['cv_auc_std']:.4f}  "
          f"AP={scores['cv_ap_mean']:.4f}  ({len(available_v3v4)} features)")
    results.append({"experimento": "3. V3+V4 + LR", "features": len(available_v3v4),
                    "modelo": "LR", **scores})

    # ── 4. V3+V4 + RandomForest ─────────────────────────────────────────────
    print("\n═══ 4. V3+V4 + RandomForest ═══")
    scores = cv_auc(X_v3v4, y_train, make_rf())
    print(f"   AUC={scores['cv_auc_mean']:.4f} ± {scores['cv_auc_std']:.4f}  "
          f"AP={scores['cv_ap_mean']:.4f}")
    results.append({"experimento": "4. V3+V4 + RF", "features": len(available_v3v4),
                    "modelo": "RandomForest", **scores})

    # ── 5. V3+V4 + GradientBoosting ────────────────────────────────────────
    print("\n═══ 5. V3+V4 + GradientBoosting ═══")
    scores = cv_auc(X_v3v4, y_train, make_gbm())
    print(f"   AUC={scores['cv_auc_mean']:.4f} ± {scores['cv_auc_std']:.4f}  "
          f"AP={scores['cv_ap_mean']:.4f}")
    results.append({"experimento": "5. V3+V4 + GBM", "features": len(available_v3v4),
                    "modelo": "GBM", **scores})

    # ── 6. V3+V4 + GBM tuned (GridSearch) ──────────────────────────────────
    print("\n═══ 6. V3+V4 + GBM (tuned) ═══")
    X_clean = X_v3v4.fillna(X_v3v4.median())
    param_grid = {
        "n_estimators": [200, 400],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.01, 0.05, 0.1],
        "min_samples_leaf": [10, 30],
    }
    gs = GridSearchCV(
        GradientBoostingClassifier(subsample=0.8, random_state=RANDOM_STATE),
        param_grid,
        cv=StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE),
        scoring="roc_auc",
        n_jobs=-1,
        verbose=0,
    )
    gs.fit(X_clean, y_train)
    best_auc = gs.best_score_
    print(f"   Best AUC={best_auc:.4f}  params={gs.best_params_}")
    results.append({"experimento": "6. V3+V4 + GBM (tuned)", "features": len(available_v3v4),
                    "modelo": "GBM-tuned",
                    "cv_auc_mean": best_auc, "cv_auc_std": 0.0,
                    "cv_ap_mean": 0.0, "cv_ap_std": 0.0})

    # ── 7. V4-only lead features + LR (ablation) ───────────────────────────
    print("\n═══ 7. Ablation — apenas V4 lead features ═══")
    avail_lead = [c for c in FEATURE_COLS_V4_LEAD if c in X_train_full.columns]
    if avail_lead:
        X_lead = X_train_full[avail_lead].copy()
        scores = cv_auc(X_lead, y_train, make_lr())
        print(f"   Lead only: AUC={scores['cv_auc_mean']:.4f} ± {scores['cv_auc_std']:.4f}  "
              f"({len(avail_lead)} features)")
        results.append({"experimento": "7a. Lead features only", "features": len(avail_lead),
                        "modelo": "LR", **scores})

    avail_geo = [c for c in FEATURE_COLS_V4_GEO if c in X_train_full.columns]
    if avail_geo:
        X_geo = X_train_full[avail_geo].copy()
        scores = cv_auc(X_geo, y_train, make_lr())
        print(f"   Geo only:  AUC={scores['cv_auc_mean']:.4f} ± {scores['cv_auc_std']:.4f}  "
              f"({len(avail_geo)} features)")
        results.append({"experimento": "7b. Geo features only", "features": len(avail_geo),
                        "modelo": "LR", **scores})

    # ── 8. Feature importance (RF on V3+V4) ─────────────────────────────────
    print("\n═══ 8. Feature importance (RF on V3+V4) ═══")
    rf = RandomForestClassifier(n_estimators=500, max_depth=7, class_weight="balanced",
                                random_state=RANDOM_STATE, n_jobs=-1)
    rf.fit(X_clean, y_train)
    importance = pd.DataFrame({
        "feature": available_v3v4,
        "importance": rf.feature_importances_,
    }).sort_values("importance", ascending=False)
    importance.to_csv(OUTPUT_DIR / "v4_feature_importance.csv", index=False)
    print("   Top 15 features:")
    for _, row in importance.head(15).iterrows():
        bar = "█" * int(row["importance"] * 100)
        print(f"   {row['feature']:<35s}  {row['importance']:.4f}  {bar}")

    # ── Save comparison ─────────────────────────────────────────────────────
    comparison = pd.DataFrame(results)
    comparison.to_csv(OUTPUT_DIR / "v4_comparison_table.csv", index=False)
    print("\n═══ RESUMO ═══")
    print(comparison[["experimento", "features", "modelo", "cv_auc_mean", "cv_auc_std"]].to_string(index=False))

    best = comparison.loc[comparison["cv_auc_mean"].idxmax()]
    print(f"\n✦ Melhor: {best['experimento']} → AUC {best['cv_auc_mean']:.4f}")
    print(f"  Delta vs baseline: {best['cv_auc_mean'] - results[0]['cv_auc_mean']:+.4f}")

    return comparison


if __name__ == "__main__":
    run_experiments()
