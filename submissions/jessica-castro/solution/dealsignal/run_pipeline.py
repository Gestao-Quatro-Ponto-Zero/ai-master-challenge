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

import pandas as pd

from enrichment.digital_enrichment import run_enrichment
from features.feature_engineering import FEATURE_COLS_V2 as FEATURE_COLS, build_features
from features.feature_store import save_features
from model.feature_selection_iv import select_features_by_iv
from model.health_engine   import compute_deal_health
from model.logistic_model import DealScoringModel
from model.priority_engine import compute_priority
from model.rating_engine import score_pipeline
from model.woe_transformer import WoETransformer
from utils.cache import artifact_exists, load_artifact, save_artifact
from utils.explainability import add_explanations_to_scored_df
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
    "woe": ARTIFACTS_DIR / "woe_transformer.pkl",
    "model": ARTIFACTS_DIR / "model.pkl",
    "feature_cols": ARTIFACTS_DIR / "feature_cols.pkl",
    "metadata": ARTIFACTS_DIR / "metadata.json",
}


def load_raw_data() -> tuple:
    logger.info("Loading raw CSV files...")
    accounts = pd.read_csv(PATHS["accounts"])
    products = pd.read_csv(PATHS["products"])
    pipeline = pd.read_csv(PATHS["pipeline"])
    teams = pd.read_csv(PATHS["teams"])
    logger.info(
        "Loaded: accounts=%d, products=%d, pipeline=%d, teams=%d",
        len(accounts), len(products), len(pipeline), len(teams),
    )
    return accounts, products, pipeline, teams


def main(force_enrich: bool = False, force_train: bool = False) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Load raw data
    accounts, products, pipeline, teams = load_raw_data()

    # Step 2: Enrichment
    enriched = run_enrichment(accounts, str(PATHS["enriched"]), force=force_enrich)

    # Step 3: Feature engineering
    logger.info("Building feature matrix...")
    feature_df, target = build_features(pipeline, accounts, products, teams, enriched)
    save_features(feature_df, str(PATHS["features"]))

    # Step 4: Train / score split
    train_mask = target.notna()
    score_mask = ~train_mask

    X_all = feature_df[FEATURE_COLS].copy()
    y_train = target[train_mask].astype(int)
    X_train = X_all[train_mask]
    X_score = X_all[score_mask]
    open_deals = feature_df[score_mask].copy()

    logger.info("Train size: %d, Score size: %d", len(X_train), len(X_score))

    # Step 5: Train WoE + Model (or load from cache)
    if not force_train and artifact_exists(str(PATHS["woe"])):
        logger.info("Loading cached model artifacts...")
        woe = load_artifact(str(PATHS["woe"]))
        model = load_artifact(str(PATHS["model"]))
        selected_features = load_artifact(str(PATHS["feature_cols"]))
    else:
        logger.info("Fitting WoE transformer...")
        woe = WoETransformer(n_bins=10)
        woe.fit(X_train, y_train)

        logger.info("Selecting features by IV...")
        selected_features = select_features_by_iv(woe.iv_scores_, threshold=0.02)

        if not selected_features:
            logger.warning("No features passed IV threshold — using all features")
            selected_features = FEATURE_COLS

        X_train_woe = woe.transform(X_train[selected_features])

        logger.info("Training Logistic Regression model...")
        model = DealScoringModel()
        model.fit(X_train_woe, y_train)

        metrics = model.evaluate(X_train_woe, y_train)
        logger.info("Train metrics: %s", metrics)

        # Save artifacts
        save_artifact(woe, str(PATHS["woe"]))
        save_artifact(model, str(PATHS["model"]))
        save_artifact(selected_features, str(PATHS["feature_cols"]))

        metadata = {
            "cv_auc": round(model.cv_auc_, 4),
            "train_auc": round(metrics["auc"], 4),
            "n_features": len(selected_features),
            "selected_features": selected_features,
            "n_train": int(len(X_train)),
            "n_score": int(len(X_score)),
        }
        with open(PATHS["metadata"], "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info("Saved model artifacts to %s", ARTIFACTS_DIR)

    # Step 6: Score open deals
    logger.info("Scoring %d open deals...", len(open_deals))
    scored, X_score_woe = score_pipeline(
        open_deals, woe, model, selected_features
    )

    # Step 7: Add explainability
    logger.info("Computing feature contributions...")
    scored = add_explanations_to_scored_df(
        scored, X_score_woe, model.coefficients, selected_features
    )

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
