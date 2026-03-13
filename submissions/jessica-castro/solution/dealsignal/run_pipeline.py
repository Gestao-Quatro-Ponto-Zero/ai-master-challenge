"""
DealSignal - Pipeline Orchestrator

Usage:
    python run_pipeline.py
    python run_pipeline.py --force-enrich
    python run_pipeline.py --force-train
    python run_pipeline.py --log-level DEBUG
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path so modules resolve correctly
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler

from enrichment.digital_enrichment import run_enrichment
from features.feature_columns import FEATURE_COLS_V2 as FEATURE_COLS
from features.feature_engineering import build_features
from features.feature_store import save_features
from features.interaction_features import FEATURE_COLS_V3, add_v3_features
from model.health_engine import compute_deal_health
from model.priority_engine import compute_priority
from model.rating_engine import assign_rating, compute_expected_revenue
from model.target_encoder import (
    DealSignalTargetEncoder,
    DEFAULT_SINGLE_COLS,
    DEFAULT_PAIR_COLS,
    DEFAULT_TRIPLE_COLS,
)
from utils.cache import artifact_exists, load_artifact, save_artifact
from utils.logger import get_logger

logger = get_logger("run_pipeline")

# Paths
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
ARTIFACTS_DIR = ROOT / "model" / "artifacts"

PATHS = {
    "accounts": DATA_DIR / "accounts.csv",
    "products": DATA_DIR / "products.csv",
    "pipeline": DATA_DIR / "sales_pipeline.csv",
    "teams": DATA_DIR / "sales_teams.csv",
    "enriched": DATA_DIR / "enriched_accounts.csv",
    "results": DATA_DIR / "results.csv",
    "features": DATA_DIR / "features.parquet",
    "target_encoder": ARTIFACTS_DIR / "target_encoder.pkl",
    "scaler": ARTIFACTS_DIR / "scaler.pkl",
    "model": ARTIFACTS_DIR / "model.pkl",
    "feature_cols": ARTIFACTS_DIR / "feature_cols.pkl",
    "metadata": ARTIFACTS_DIR / "metadata.json",
}

# V3 + V4 numeric features used alongside target-encoded features
V3_V4_NUMERIC_COLS = [
    c
    for c in (
        FEATURE_COLS_V3
        + [
            "lead_source_wr",
            "lead_origin_wr",
            "contact_role_wr",
            "last_activity_type_wr",
            "lead_quality_score",
            "activity_count",
            "page_views_per_visit",
            "has_activity",
            "last_activity_is_positive",
            "lead_tag_wr",
            "country_wr",
            "is_india",
        ]
    )
]
# Deduplicate while preserving order
V3_V4_NUMERIC_COLS = list(dict.fromkeys(V3_V4_NUMERIC_COLS))


def load_raw_data() -> tuple:
    logger.info("Loading raw CSV files...")
    accounts = pd.read_csv(PATHS["accounts"])
    products = pd.read_csv(PATHS["products"])
    pipeline = pd.read_csv(PATHS["pipeline"])
    teams = pd.read_csv(PATHS["teams"])
    logger.info(
        "Loaded: accounts=%d, products=%d, pipeline=%d, teams=%d",
        len(accounts),
        len(products),
        len(pipeline),
        len(teams),
    )
    return accounts, products, pipeline, teams


def _build_feature_matrix(
    feature_df: pd.DataFrame,
    te: DealSignalTargetEncoder,
    numeric_cols: list[str],
) -> pd.DataFrame:
    """Combine numeric features + target-encoded features into a single matrix."""
    available_numeric = [c for c in numeric_cols if c in feature_df.columns]
    X_numeric = feature_df[available_numeric].copy()
    X_te = te.transform(feature_df)
    X = pd.concat([X_numeric, X_te], axis=1)
    X = X.fillna(X.median())
    return X


def main(force_enrich: bool = False, force_train: bool = False) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Load raw data
    accounts, products, pipeline, teams = load_raw_data()

    # Step 2: Enrichment
    enriched = run_enrichment(accounts, str(PATHS["enriched"]), force=force_enrich)

    # Step 3: Feature engineering (V2 + V4 lead/geo)
    logger.info("Building feature matrix...")
    feature_df, target = build_features(pipeline, accounts, products, teams, enriched)
    save_features(feature_df, str(PATHS["features"]))

    # Step 3b: Add V3 interaction features
    train_mask = target.notna()
    feature_df = add_v3_features(feature_df, train_mask)

    # Step 4: Train / score split
    score_mask = ~train_mask
    y_train = target[train_mask].astype(int)

    # If there are no open (unlabelled) deals, score ALL deals for dashboard display.
    if score_mask.sum() == 0:
        logger.warning(
            "No open deals found in the pipeline — scoring all %d deals (in-sample) "
            "for dashboard display.",
            len(feature_df),
        )
        score_mask = pd.Series(True, index=train_mask.index)

    open_deals = feature_df[score_mask].copy()
    logger.info("Train size: %d, Score size: %d", train_mask.sum(), score_mask.sum())

    # Step 5: Train Target Encoder + Scaler + Model (or load from cache)
    if not force_train and artifact_exists(str(PATHS["target_encoder"])):
        logger.info("Loading cached model artifacts...")
        te = load_artifact(str(PATHS["target_encoder"]))
        scaler = load_artifact(str(PATHS["scaler"]))
        model = load_artifact(str(PATHS["model"]))
        selected_features = load_artifact(str(PATHS["feature_cols"]))
    else:
        # 5a: Fit target encoder on training data
        logger.info("Fitting target encoder...")
        te = DealSignalTargetEncoder(
            single_cols=DEFAULT_SINGLE_COLS,
            pair_cols=DEFAULT_PAIR_COLS,
            triple_cols=DEFAULT_TRIPLE_COLS,
            m=10,
        )
        te.fit(feature_df[train_mask], y_train)

        # 5b: Build combined feature matrix for training
        X_train = _build_feature_matrix(
            feature_df[train_mask], te, V3_V4_NUMERIC_COLS
        )
        all_feature_cols = list(X_train.columns)

        # 5c: Scale features
        scaler = StandardScaler()
        X_train_scaled = pd.DataFrame(
            scaler.fit_transform(X_train),
            columns=all_feature_cols,
            index=X_train.index,
        )

        # 5d: L1 feature selection
        logger.info("L1 feature selection from %d features...", len(all_feature_cols))
        lr_l1 = LogisticRegression(
            C=0.03,
            penalty="l1",
            solver="saga",
            class_weight="balanced",
            max_iter=15000,
            random_state=42,
        )
        lr_l1.fit(X_train_scaled, y_train)
        coefs = np.abs(lr_l1.coef_[0])
        selected_features = [
            all_feature_cols[i] for i in range(len(all_feature_cols)) if coefs[i] > 0
        ]
        logger.info("Selected %d / %d features via L1", len(selected_features), len(all_feature_cols))

        # 5e: Train final model on selected features
        X_train_sel = X_train_scaled[selected_features]

        logger.info("Training Logistic Regression on %d features...", len(selected_features))
        model = LogisticRegression(
            C=0.5,
            class_weight="balanced",
            max_iter=10000,
            random_state=42,
        )
        model.fit(X_train_sel, y_train)

        # 5f: OOF Cross-validated AUC
        # Build OOF target-encoded features (each row encoded using other folds)
        # then evaluate LR on those features. This matches production behavior
        # where TE is fit on all historical data before scoring new deals.
        from sklearn.metrics import roc_auc_score
        from sklearn.model_selection import KFold

        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        kf_te = KFold(n_splits=5, shuffle=True, random_state=42)
        train_df_for_cv = feature_df[train_mask]

        # Step 1: Build OOF target-encoded features
        oof_te_features = pd.DataFrame(index=train_df_for_cv.index)
        for te_fold_train_idx, te_fold_val_idx in kf_te.split(train_df_for_cv):
            fold_train = train_df_for_cv.iloc[te_fold_train_idx]
            fold_val = train_df_for_cv.iloc[te_fold_val_idx]
            fold_y = y_train.iloc[te_fold_train_idx]

            fold_te = DealSignalTargetEncoder(
                single_cols=DEFAULT_SINGLE_COLS,
                pair_cols=DEFAULT_PAIR_COLS,
                triple_cols=DEFAULT_TRIPLE_COLS,
                m=10,
            )
            fold_te.fit(fold_train, fold_y)
            fold_encoded = fold_te.transform(fold_val)
            oof_te_features = oof_te_features.combine_first(fold_encoded)

        # Combine OOF TE with numeric features
        avail_numeric = [c for c in V3_V4_NUMERIC_COLS if c in train_df_for_cv.columns]
        X_oof = pd.concat([train_df_for_cv[avail_numeric], oof_te_features], axis=1)
        X_oof = X_oof.fillna(X_oof.median())
        X_oof_s = pd.DataFrame(
            StandardScaler().fit_transform(X_oof),
            columns=X_oof.columns, index=X_oof.index,
        )

        # Step 2: CV on OOF features using selected_features
        avail_sel = [f for f in selected_features if f in X_oof_s.columns]
        cv_scores = cross_val_score(
            LogisticRegression(C=0.5, class_weight="balanced", max_iter=10000, random_state=42),
            X_oof_s[avail_sel], y_train, cv=cv, scoring="roc_auc", n_jobs=-1,
        )
        cv_auc = float(cv_scores.mean())
        cv_auc_std = float(cv_scores.std())
        logger.info("OOF CV AUC-ROC: %.4f ± %.4f", cv_auc, cv_auc_std)

        # 5g: Save artifacts
        save_artifact(te, str(PATHS["target_encoder"]))
        save_artifact(scaler, str(PATHS["scaler"]))
        save_artifact(model, str(PATHS["model"]))
        save_artifact(selected_features, str(PATHS["feature_cols"]))

        metadata = {
            "cv_auc": round(cv_auc, 4),
            "cv_auc_std": round(cv_auc_std, 4),
            "n_features_total": len(all_feature_cols),
            "n_features_selected": len(selected_features),
            "selected_features": selected_features,
            "n_train": int(train_mask.sum()),
            "n_score": int(score_mask.sum()),
            "model_type": "LogisticRegression + TargetEncoder + L1",
        }
        with open(PATHS["metadata"], "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info("Saved model artifacts to %s", ARTIFACTS_DIR)

    # Step 6: Score open deals
    logger.info("Scoring %d open deals...", len(open_deals))
    X_score = _build_feature_matrix(open_deals, te, V3_V4_NUMERIC_COLS)
    X_score_scaled = pd.DataFrame(
        scaler.transform(X_score),
        columns=X_score.columns,
        index=X_score.index,
    )
    X_score_sel = X_score_scaled[selected_features]

    proba = model.predict_proba(X_score_sel)[:, 1]
    scored = open_deals.copy()
    scored["win_probability"] = proba
    scored["deal_rating"] = scored["win_probability"].apply(assign_rating)
    scored["expected_revenue"] = scored.apply(
        lambda r: compute_expected_revenue(r["win_probability"], r["effective_value"]),
        axis=1,
    )

    logger.info(
        "Scored %d deals. Rating distribution:\n%s",
        len(scored),
        scored["deal_rating"].value_counts().to_string(),
    )

    # Step 7: Add explainability (feature contributions)
    logger.info("Computing feature contributions...")
    coefficients = model.coef_[0]
    explanations = []
    for idx in scored.index:
        if idx in X_score_sel.index:
            row = X_score_sel.loc[idx]
            contribs = {feat: float(row[feat]) * float(coefficients[i])
                        for i, feat in enumerate(selected_features)}
            sorted_c = sorted(contribs.items(), key=lambda x: x[1], reverse=True)
            top_pos = [(f, v) for f, v in sorted_c if v > 0][:3]
            top_neg = [(f, v) for f, v in reversed(sorted_c) if v < 0][:3]
            parts = [f"+{f}({v:+.2f})" for f, v in top_pos]
            parts += [f"-{f}({v:+.2f})" for f, v in top_neg]
            explanations.append(", ".join(parts) if parts else "—")
        else:
            explanations.append("—")
    scored["top_contributing_factors"] = explanations

    # ── V2: Deal Health Engine + Priority Engine ───────────────────────────
    scored = compute_deal_health(scored)
    scored = compute_priority(scored)

    # Step 8: Save results
    output_cols = [
        "opportunity_id", "account", "product", "sales_agent",
        "manager", "office", "deal_stage", "engage_date", "close_date",
        "effective_value", "win_probability", "deal_rating",
        "expected_revenue", "top_contributing_factors",
        # Feature columns used by the UI for engine scores and signals
        "agent_win_rate", "product_win_rate",
        "days_since_engage", "pipeline_velocity",
        "digital_maturity_index",
        "deal_health_score", "deal_health_status",
        "priority_score", "priority_tier",
        "seller_win_rate", "seller_rank_percentile", "seller_pipeline_load",
        "is_stale_flag", "deal_age_percentile",
        "product_rank_percentile",
    ]
    available_cols = [c for c in output_cols if c in scored.columns]
    results = scored[available_cols].sort_values("expected_revenue", ascending=False)
    results.to_csv(PATHS["results"], index=False)
    logger.info("Results saved to %s (%d deals)", PATHS["results"], len(results))

    # Summary
    top10 = results.head(10)
    logger.info("\n=== TOP 10 DEALS TO PRIORITIZE ===")
    for _, row in top10.iterrows():
        logger.info(
            "  [%s] %s | %s | Agent: %s | ExpRev: $%.0f | Prob: %.1f%%",
            row.get("deal_rating", "?"),
            row.get("account", "?"),
            row.get("product", "?"),
            row.get("sales_agent", "?"),
            row.get("expected_revenue", 0),
            row.get("win_probability", 0) * 100,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DealSignal Pipeline")
    parser.add_argument("--force-enrich", action="store_true", help="Re-run enrichment")
    parser.add_argument("--force-train", action="store_true", help="Re-train model")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING"],
        help="Logging level",
    )
    args = parser.parse_args()

    import os
    os.environ["LOG_LEVEL"] = args.log_level

    main(force_enrich=args.force_enrich, force_train=args.force_train)
