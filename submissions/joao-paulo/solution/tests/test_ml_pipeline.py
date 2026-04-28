from pathlib import Path

import pandas as pd

from churn_diagnosis.application.use_cases import BuildSolutionUseCase, TrainClassifierUseCase
from churn_diagnosis.infrastructure.loaders import CsvDataLoader
from churn_diagnosis.ml import trainer
from churn_diagnosis.ml.config import ChurnPredictionConfig
from churn_diagnosis.ml.dataset_builder import (
    build_current_scoring_dataset,
    build_point_in_time_dataset,
)

DATA_DIR = Path("data")


def test_point_in_time_dataset_has_binary_target():
    bundle = CsvDataLoader(DATA_DIR).load()
    dataset, _ = build_point_in_time_dataset(bundle, ChurnPredictionConfig())
    assert "target_churn_30d" in dataset.columns
    assert dataset["target_churn_30d"].nunique() == 2
    assert dataset["snapshot_date"].nunique() > 1
    assert (dataset.groupby("account_id").size() > 1).any()


def test_feature_matrix_excludes_leaky_columns():
    bundle = CsvDataLoader(DATA_DIR).load()
    dataset, _ = build_point_in_time_dataset(bundle, ChurnPredictionConfig())
    X, _, _, _ = trainer.build_feature_matrix(dataset)

    forbidden = {
        "snapshot_id",
        "account_id",
        "account_name",
        "signup_date",
        "first_future_churn_date",
        "snapshot_date",
        "churn_flag",
        "target_churn_30d",
        "is_logo_churned",
    }
    assert forbidden.isdisjoint(set(X.columns))


def test_train_classifier_returns_ranked_artifacts():
    bundle = CsvDataLoader(DATA_DIR).load()
    (
        model,
        metrics,
        current_scoring_frame,
        dataset,
        comparison,
        feature_importance,
        account_model_explanations,
        model_global_explainability,
    ) = (
        TrainClassifierUseCase(ChurnPredictionConfig(cv_folds=2)).execute(bundle)
    )

    assert model is not None
    assert metrics["best_model_name"] in {
        "logistic_regression",
        "random_forest",
        "xgboost",
    }
    assert "best_selection_score" in metrics
    assert metrics["threshold_strategy"]["source"] == "out_of_fold_train_val_grouped_by_account"
    assert metrics["threshold_strategy"]["optimized_metric"] == "f1"
    assert 0.1 <= metrics["best_threshold"] <= 0.9
    assert metrics["oof_metrics"]["threshold"] == metrics["best_threshold"]
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert 0.0 <= metrics["average_precision"] <= 1.0
    assert {"roc_auc", "pr_auc", "precision", "recall", "f1", "sample_size"}.issubset(
        metrics["random_validation_metrics"]
    )
    assert {"roc_auc", "pr_auc", "precision", "recall", "f1", "sample_size", "train_end_date", "validation_start_date"}.issubset(
        metrics["temporal_validation_metrics"]
    )
    assert "relevant_gap" in metrics["validation_gap_summary"]
    assert not current_scoring_frame.empty
    assert {
        "account_id",
        "current_churn_probability",
        "current_risk_band",
        "scored_at",
    }.issubset(current_scoring_frame.columns)
    assert "snapshot_date" not in current_scoring_frame.columns
    assert not dataset.empty
    assert not comparison.empty
    assert not feature_importance.empty
    assert not account_model_explanations.empty
    assert not model_global_explainability.empty
    assert {"xgboost", "logistic_regression", "random_forest"}.issubset(
        set(comparison["model"])
    )
    assert "selection_score" in comparison.columns
    assert {"oof_f1", "oof_pr_auc", "train_val_f1"}.issubset(comparison.columns)
    assert comparison["selection_score"].is_monotonic_decreasing
    assert {"feature", "feature_label", "importance", "normalized_importance"}.issubset(feature_importance.columns)
    assert {"account_id", "rank", "feature_label", "local_impact", "explanation_text"}.issubset(account_model_explanations.columns)
    assert {"feature_label", "portfolio_direction", "impact_statement"}.issubset(model_global_explainability.columns)
    assert "explainability_strategy" in metrics
    assert "top_global_drivers" in metrics


def test_current_scoring_dataset_matches_training_feature_schema():
    bundle = CsvDataLoader(DATA_DIR).load()
    training_dataset, _ = build_point_in_time_dataset(bundle, ChurnPredictionConfig())
    current_scoring_dataset, _ = build_current_scoring_dataset(bundle)

    X_train, _, _, _ = trainer.build_feature_matrix(training_dataset)

    missing_columns = set(X_train.columns).difference(current_scoring_dataset.columns)
    assert not missing_columns
    assert list(current_scoring_dataset.reindex(columns=X_train.columns).columns) == list(X_train.columns)


def test_current_scoring_dataset_uses_only_current_snapshot():
    bundle = CsvDataLoader(DATA_DIR).load()
    training_dataset, _ = build_point_in_time_dataset(bundle, ChurnPredictionConfig())
    current_scoring_dataset, current_snapshot_date = build_current_scoring_dataset(bundle)

    assert current_scoring_dataset["snapshot_date"].nunique() == 1
    assert current_scoring_dataset["snapshot_date"].eq(current_snapshot_date).all()
    assert training_dataset["snapshot_date"].nunique() > current_scoring_dataset["snapshot_date"].nunique()
    assert training_dataset["snapshot_date"].max() < current_snapshot_date


def test_training_dataset_targets_only_future_churn_events():
    bundle = CsvDataLoader(DATA_DIR).load()
    dataset, leakage_report = build_point_in_time_dataset(bundle, ChurnPredictionConfig())

    positives = dataset.loc[dataset["target_churn_30d"].eq(1)].copy()
    assert not positives.empty
    assert leakage_report.target_uses_only_future_churn is True
    assert leakage_report.multiple_snapshots_per_account is True
    assert leakage_report.features_within_snapshot_boundary is True
    assert (positives["first_future_churn_date"] > positives["snapshot_date"]).all()
    assert (
        positives["first_future_churn_date"]
        <= positives["snapshot_date"] + pd.Timedelta(days=30)
    ).all()


def test_temporal_validation_split_respects_chronology():
    bundle = CsvDataLoader(DATA_DIR).load()
    dataset, _ = build_point_in_time_dataset(bundle, ChurnPredictionConfig())
    split = trainer.build_temporal_validation_split(dataset, validation_fraction=0.20)

    train_dates = pd.to_datetime(dataset.loc[split["train_mask"], "snapshot_date"])
    validation_dates = pd.to_datetime(dataset.loc[split["validation_mask"], "snapshot_date"])

    assert not train_dates.empty
    assert not validation_dates.empty
    assert train_dates.max() < validation_dates.min()


def test_build_solution_use_case_exposes_training_outputs():
    bundle = CsvDataLoader(DATA_DIR).load()
    artifacts = BuildSolutionUseCase().execute(bundle)

    assert not artifacts.point_in_time_training_dataset.empty
    assert not artifacts.current_churn_scoring.empty
    assert not artifacts.model_comparison.empty
    assert not artifacts.feature_importance.empty
    assert not artifacts.churn_reconciliation.empty
    assert not artifacts.account_model_explanations.empty
    assert not artifacts.model_global_explainability.empty
    assert artifacts.account_360["current_churn_probability"].notna().all()
    assert "current_primary_model_driver_label" in artifacts.account_360.columns
    assert "current_model_explanation" in artifacts.account_360.columns
    assert "snapshot_date_x" not in artifacts.account_360.columns
    assert "snapshot_date_y" not in artifacts.account_360.columns
    assert artifacts.model_metrics["threshold_strategy"]["source"] == "out_of_fold_train_val_grouped_by_account"
    assert artifacts.model_metrics["oof_metrics"]["threshold"] == artifacts.model_metrics["best_threshold"]
    assert "random_validation_metrics" in artifacts.model_metrics
    assert "temporal_validation_metrics" in artifacts.model_metrics
    assert "validation_gap_summary" in artifacts.model_metrics
    assert artifacts.model_metrics["best_model_name"] == artifacts.model_comparison.iloc[0]["model"]
    assert "explainability_strategy" in artifacts.model_metrics
    assert {
        "total_accounts",
        "accounts_churn_flag_true",
        "accounts_with_churn_event",
        "accounts_currently_active_after_reactivation",
    }.issubset(set(artifacts.churn_reconciliation["metric_key"]))
