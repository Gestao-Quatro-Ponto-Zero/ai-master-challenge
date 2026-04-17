from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    StratifiedGroupKFold,
    cross_val_predict,
    cross_validate,
)
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from .config import ChurnPredictionConfig
from .explainability import aggregate_transformed_feature_importance
from .preprocessing import build_feature_matrix, build_preprocessors

VALIDATION_METRICS = [
    "accuracy",
    "precision",
    "recall",
    "f1",
    "roc_auc",
    "average_precision",
]


def compute_selection_score(
    cv_pr_auc_mean: float,
    val_pr_auc: float,
    overfit_gap_f1: float,
) -> float:
    return (
        cv_pr_auc_mean * 0.65
        + val_pr_auc * 0.35
        - max(overfit_gap_f1, 0.0) * 0.20
    )


def compute_metrics(y_true, y_proba, threshold: float) -> dict:
    pred = (y_proba >= threshold).astype(int)
    return {
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "pr_auc": float(average_precision_score(y_true, y_proba)),
        "threshold": float(threshold),
        "confusion_matrix": confusion_matrix(y_true, pred).tolist(),
    }


def tune_threshold(y_true, y_proba) -> dict:
    best = {"threshold": 0.5, "precision": 0.0, "recall": 0.0, "f1": -1.0}
    best_rank = (-1.0, -1.0, -1.0, float("-inf"))

    for threshold in np.arange(0.10, 0.91, 0.01):
        pred = (y_proba >= threshold).astype(int)
        precision = precision_score(y_true, pred, zero_division=0)
        recall = recall_score(y_true, pred, zero_division=0)
        f1 = f1_score(y_true, pred, zero_division=0)
        rank = (
            float(f1),
            float(precision),
            float(recall),
            -abs(float(threshold) - 0.5),
        )

        if rank > best_rank:
            best_rank = rank
            best = {
                "threshold": float(round(threshold, 2)),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
            }

    return best


def resolve_cv_folds(y: pd.Series, requested_folds: int) -> int:
    min_class_count = int(y.value_counts().min()) if not y.empty else 2
    return max(2, min(requested_folds, min_class_count))


def build_models(
    numeric_columns: list[str],
    categorical_columns: list[str],
    config: ChurnPredictionConfig,
):
    linear_prep, tree_prep = build_preprocessors(
        numeric_columns,
        categorical_columns,
        config,
    )

    return {
        "logistic_regression": Pipeline(
            [
                (
                    "prep",
                    linear_prep,
                ),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        random_state=config.random_state,
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("prep", tree_prep),
                (
                    "clf",
                    RandomForestClassifier(
                        n_estimators=400,
                        max_depth=8,
                        min_samples_leaf=4,
                        class_weight="balanced_subsample",
                        random_state=config.random_state,
                    ),
                ),
            ]
        ),
        "xgboost": Pipeline(
            [
                ("prep", tree_prep),
                (
                    "clf",
                    XGBClassifier(
                        n_estimators=250,
                        max_depth=3,
                        learning_rate=0.05,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        reg_alpha=0.4,
                        reg_lambda=3.0,
                        min_child_weight=4,
                        gamma=0.2,
                        objective="binary:logistic",
                        eval_metric="logloss",
                        random_state=config.random_state,
                        tree_method="hist",
                        n_jobs=1,
                        verbosity=0,
                    ),
                ),
            ]
        ),
    }


def probability_to_risk_band(probability: float, threshold: float) -> str:
    critical_floor = max(0.80, threshold + 0.20)
    medium_floor = max(0.20, threshold * 0.60)

    if probability >= critical_floor:
        return "critical"
    if probability >= threshold:
        return "high"
    if probability >= medium_floor:
        return "medium"
    return "low"


def build_temporal_validation_split(
    dataset: pd.DataFrame,
    validation_fraction: float,
) -> dict[str, object]:
    snapshot_dates = pd.to_datetime(dataset["snapshot_date"]).dt.normalize()
    ordered_dates = sorted(snapshot_dates.dropna().unique())
    if len(ordered_dates) < 2:
        raise ValueError("Temporal validation requires at least two distinct snapshot dates.")

    default_validation_dates = max(1, int(round(len(ordered_dates) * validation_fraction)))
    start_idx = max(1, len(ordered_dates) - default_validation_dates)

    for split_idx in range(start_idx, 0, -1):
        validation_start = ordered_dates[split_idx]
        train_mask = snapshot_dates < validation_start
        validation_mask = snapshot_dates >= validation_start

        if train_mask.sum() == 0 or validation_mask.sum() == 0:
            continue

        y_train = dataset.loc[train_mask, "target_churn_30d"]
        y_validation = dataset.loc[validation_mask, "target_churn_30d"]
        if y_train.nunique() < 2 or y_validation.nunique() < 2:
            continue

        return {
            "train_mask": train_mask.to_numpy(),
            "validation_mask": validation_mask.to_numpy(),
            "train_end_date": pd.Timestamp(snapshot_dates.loc[train_mask].max()),
            "validation_start_date": pd.Timestamp(snapshot_dates.loc[validation_mask].min()),
        }

    raise ValueError("Unable to build a valid temporal validation split with both classes present.")


def evaluate_temporal_validation(
    dataset: pd.DataFrame,
    feature_columns: list[str],
    best_model_name: str,
    config: ChurnPredictionConfig,
) -> dict[str, object]:
    temporal_split = build_temporal_validation_split(dataset, config.test_size)
    train_mask = temporal_split["train_mask"]
    validation_mask = temporal_split["validation_mask"]

    X = dataset.reindex(columns=feature_columns)
    y = dataset["target_churn_30d"].astype(int)
    groups = dataset["account_id"].astype(str)

    X_train = X.loc[train_mask].copy()
    y_train = y.loc[train_mask].copy()
    groups_train = groups.loc[train_mask].copy()
    X_validation = X.loc[validation_mask].copy()
    y_validation = y.loc[validation_mask].copy()

    temporal_model = build_models(
        numeric_columns=X_train.select_dtypes(include=["number", "bool"]).columns.tolist(),
        categorical_columns=[c for c in X_train.columns if c not in X_train.select_dtypes(include=["number", "bool"]).columns.tolist()],
        config=config,
    )[best_model_name]

    cv = StratifiedGroupKFold(
        n_splits=resolve_cv_folds(y_train, config.cv_folds),
        shuffle=True,
        random_state=config.random_state,
    )
    temporal_oof_proba = cross_val_predict(
        temporal_model,
        X_train,
        y_train,
        cv=cv,
        method="predict_proba",
        groups=groups_train,
        n_jobs=1,
    )[:, 1]
    threshold = tune_threshold(y_train, temporal_oof_proba)["threshold"]

    temporal_model.fit(X_train, y_train)
    validation_proba = temporal_model.predict_proba(X_validation)[:, 1]
    metrics = compute_metrics(y_validation, validation_proba, threshold)
    metrics.update(
        {
            "sample_size": int(validation_mask.sum()),
            "train_sample_size": int(train_mask.sum()),
            "train_end_date": str(pd.Timestamp(temporal_split["train_end_date"]).date()),
            "validation_start_date": str(pd.Timestamp(temporal_split["validation_start_date"]).date()),
        }
    )
    return metrics


def build_validation_gap_summary(
    random_metrics: dict[str, object],
    temporal_metrics: dict[str, object],
) -> dict[str, object]:
    monitored_metrics = ["roc_auc", "pr_auc", "precision", "recall", "f1"]
    deltas = {
        metric: float(temporal_metrics[metric]) - float(random_metrics[metric])
        for metric in monitored_metrics
    }
    relevant_gap = any(abs(delta) >= 0.05 for delta in deltas.values())
    if not relevant_gap:
        note = "Random and temporal validation are broadly aligned."
    elif deltas["pr_auc"] < -0.05 or deltas["roc_auc"] < -0.05 or deltas["f1"] < -0.05:
        note = "Temporal validation is materially worse than random validation, suggesting the random split is more optimistic."
    else:
        note = "Temporal validation differs materially from random validation and should be reviewed before presenting model quality."

    return {
        "relevant_gap": bool(relevant_gap),
        "deltas": deltas,
        "note": note,
    }


def build_current_scoring_frame(
    model,
    feature_columns: list[str],
    scoring_dataset: pd.DataFrame,
    threshold: float,
    scored_at: pd.Timestamp,
) -> pd.DataFrame:
    scoring_X = scoring_dataset.reindex(columns=feature_columns)
    probabilities = model.predict_proba(scoring_X)[:, 1]

    scoring_frame = scoring_dataset[["account_id"]].copy()
    scoring_frame["current_churn_probability"] = probabilities
    scoring_frame["current_decision_threshold"] = float(threshold)
    scoring_frame["current_predicted_churn_30d"] = (
        scoring_frame["current_churn_probability"] >= threshold
    ).astype(int)
    scoring_frame["current_risk_band"] = scoring_frame["current_churn_probability"].map(
        lambda value: probability_to_risk_band(float(value), float(threshold))
    )
    scoring_frame["scored_at"] = pd.Timestamp(scored_at)
    return scoring_frame


def evaluate_models(
    dataset: pd.DataFrame,
    config: ChurnPredictionConfig,
):
    X, y, numeric_columns, categorical_columns = build_feature_matrix(dataset)
    groups = dataset["account_id"].astype(str)

    holdout_cv = StratifiedGroupKFold(
        n_splits=max(2, int(round(1 / config.test_size))),
        shuffle=True,
        random_state=config.random_state,
    )
    train_val_idx, test_idx = next(holdout_cv.split(X, y, groups))

    X_train_val = X.iloc[train_val_idx].copy()
    X_test = X.iloc[test_idx].copy()
    y_train_val = y.iloc[train_val_idx].copy()
    y_test = y.iloc[test_idx].copy()
    groups_train_val = groups.iloc[train_val_idx].copy()

    models = build_models(numeric_columns, categorical_columns, config)
    cv = StratifiedGroupKFold(
        n_splits=resolve_cv_folds(y_train_val, config.cv_folds),
        shuffle=True,
        random_state=config.random_state,
    )

    comparison_rows = []
    artifacts = {}
    best_name = None
    best_score = -1.0
    best_rank_key: tuple[float, float, float, float] | None = None

    for model_name, pipeline in models.items():
        cv_scores = cross_validate(
            pipeline,
            X_train_val,
            y_train_val,
            cv=cv,
            scoring=VALIDATION_METRICS,
            groups=groups_train_val,
            return_train_score=True,
            n_jobs=1,
        )

        oof_proba = cross_val_predict(
            pipeline,
            X_train_val,
            y_train_val,
            cv=cv,
            method="predict_proba",
            groups=groups_train_val,
            n_jobs=1,
        )[:, 1]
        threshold_details = tune_threshold(y_train_val, oof_proba)
        threshold = threshold_details["threshold"]
        oof_metrics = compute_metrics(y_train_val, oof_proba, threshold)

        pipeline.fit(X_train_val, y_train_val)
        train_val_proba = pipeline.predict_proba(X_train_val)[:, 1]
        train_val_metrics = compute_metrics(y_train_val, train_val_proba, threshold)

        artifacts[model_name] = {
            "pipeline": pipeline,
            "threshold": threshold,
            "threshold_details": threshold_details,
            "cv": {
                metric: float(np.mean(values))
                for metric, values in cv_scores.items()
                if "time" not in metric
            },
            "oof_metrics": oof_metrics,
            "train_val_metrics": train_val_metrics,
            "overfit_gap_f1": float(train_val_metrics["f1"] - oof_metrics["f1"]),
            "underfit_flag": bool(
                train_val_metrics["f1"] < 0.65 and oof_metrics["f1"] < 0.65
            ),
        }
        selection_score = compute_selection_score(
            cv_pr_auc_mean=artifacts[model_name]["cv"]["test_average_precision"],
            val_pr_auc=oof_metrics["pr_auc"],
            overfit_gap_f1=artifacts[model_name]["overfit_gap_f1"],
        )
        artifacts[model_name]["selection_score"] = selection_score

        comparison_rows.append(
            {
                "model": model_name,
                "cv_accuracy_mean": artifacts[model_name]["cv"]["test_accuracy"],
                "cv_precision_mean": artifacts[model_name]["cv"]["test_precision"],
                "cv_recall_mean": artifacts[model_name]["cv"]["test_recall"],
                "cv_f1_mean": artifacts[model_name]["cv"]["test_f1"],
                "cv_roc_auc_mean": artifacts[model_name]["cv"]["test_roc_auc"],
                "cv_pr_auc_mean": artifacts[model_name]["cv"]["test_average_precision"],
                "oof_f1": oof_metrics["f1"],
                "oof_pr_auc": oof_metrics["pr_auc"],
                "train_val_f1": train_val_metrics["f1"],
                "threshold": threshold,
                "overfit_gap_f1": artifacts[model_name]["overfit_gap_f1"],
                "underfit_flag": artifacts[model_name]["underfit_flag"],
                "selection_score": selection_score,
            }
        )

        rank_key = (
            selection_score,
            artifacts[model_name]["cv"]["test_average_precision"],
            oof_metrics["pr_auc"],
            -artifacts[model_name]["overfit_gap_f1"],
        )
        if best_rank_key is None or rank_key > best_rank_key:
            best_name = model_name
            best_rank_key = rank_key
            best_score = selection_score

    evaluation_model = artifacts[best_name]["pipeline"]
    best_threshold = artifacts[best_name]["threshold"]
    test_proba = evaluation_model.predict_proba(X_test)[:, 1]
    train_val_metrics = artifacts[best_name]["train_val_metrics"]
    oof_metrics = artifacts[best_name]["oof_metrics"]
    test_metrics = compute_metrics(y_test, test_proba, best_threshold)
    test_metrics.update(
        {
            "sample_size": int(len(y_test)),
            "train_sample_size": int(len(y_train_val)),
        }
    )

    temporal_validation_metrics = evaluate_temporal_validation(
        dataset=dataset,
        feature_columns=X.columns.tolist(),
        best_model_name=best_name,
        config=config,
    )
    validation_gap_summary = build_validation_gap_summary(
        random_metrics=test_metrics,
        temporal_metrics=temporal_validation_metrics,
    )

    deployment_models = build_models(numeric_columns, categorical_columns, config)
    best_model = deployment_models[best_name]
    best_model.fit(X, y)

    preprocessor = best_model.named_steps["prep"]
    estimator = best_model.named_steps["clf"]
    feature_names = preprocessor.get_feature_names_out()

    if hasattr(estimator, "feature_importances_"):
        importances = estimator.feature_importances_
    else:
        importances = np.abs(estimator.coef_[0])

    feature_importance = aggregate_transformed_feature_importance(
        transformed_feature_names=feature_names,
        importances=np.asarray(importances),
        original_feature_columns=X.columns.tolist(),
    )

    return {
        "comparison": pd.DataFrame(comparison_rows)
        .sort_values(
            ["selection_score", "cv_pr_auc_mean", "oof_pr_auc", "overfit_gap_f1"],
            ascending=[False, False, False, True],
        )
        .reset_index(drop=True),
        "artifacts": artifacts,
        "best_model_name": best_name,
        "best_model": best_model,
        "best_threshold": best_threshold,
        "best_selection_score": best_score,
        "feature_columns": X.columns.tolist(),
        "threshold_strategy": {
            "source": "out_of_fold_train_val_grouped_by_account",
            "optimized_metric": "f1",
            "cv_folds": int(config.cv_folds),
        },
        "random_validation_metrics": test_metrics,
        "temporal_validation_metrics": temporal_validation_metrics,
        "validation_gap_summary": validation_gap_summary,
        "oof_metrics": oof_metrics,
        "train_val_metrics": train_val_metrics,
        "test_metrics": test_metrics,
        "robustness": {
            "train_val_vs_oof_f1_gap": float(
                train_val_metrics["f1"] - oof_metrics["f1"]
            ),
            "oof_vs_test_f1_gap": float(
                oof_metrics["f1"] - test_metrics["f1"]
            ),
            "train_val_vs_test_f1_gap": float(
                train_val_metrics["f1"] - test_metrics["f1"]
            ),
            "oof_vs_test_pr_auc_gap": float(
                oof_metrics["pr_auc"] - test_metrics["pr_auc"]
            ),
            "train_val_vs_test_pr_auc_gap": float(
                train_val_metrics["pr_auc"] - test_metrics["pr_auc"]
            ),
            "train_val_vs_test_roc_auc_gap": float(
                train_val_metrics["roc_auc"] - test_metrics["roc_auc"]
            ),
        },
        "feature_importance": feature_importance,
    }
