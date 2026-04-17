from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import joblib
import numpy as np
import pandas as pd

from churn_diagnosis.domain.services import HealthScoreService
from churn_diagnosis.infrastructure.loaders import DataBundle
from churn_diagnosis.ml.config import ChurnPredictionConfig
from churn_diagnosis.ml.dataset_builder import (
    build_current_scoring_dataset,
    build_point_in_time_dataset,
)
from churn_diagnosis.ml.explainability import (
    build_account_explainability,
    build_global_explainability,
)
from churn_diagnosis.ml.feature_engineering import resolve_current_snapshot_date
from churn_diagnosis.ml.trainer import build_current_scoring_frame, evaluate_models


@dataclass
class RunArtifacts:
    account_360: pd.DataFrame
    customer_health: pd.DataFrame
    churn_risk_drivers: pd.DataFrame
    churn_reconciliation: pd.DataFrame
    model_metrics: dict[str, Any]
    model: Any
    current_churn_scoring: pd.DataFrame
    account_model_explanations: pd.DataFrame
    model_global_explainability: pd.DataFrame
    point_in_time_training_dataset: pd.DataFrame
    model_comparison: pd.DataFrame
    feature_importance: pd.DataFrame


def build_churn_reconciliation(account_360: pd.DataFrame) -> pd.DataFrame:
    churn_flag = pd.to_numeric(account_360.get("churn_flag", 0), errors="coerce").fillna(0).astype(int)
    had_churn_event = pd.to_numeric(account_360.get("had_churn_event", 0), errors="coerce").fillna(0).astype(int)
    reactivation_events = pd.to_numeric(account_360.get("reactivation_events", 0), errors="coerce").fillna(0)
    active_subscriptions = pd.to_numeric(account_360.get("active_subscriptions", 0), errors="coerce").fillna(0)

    metrics = [
        {
            "metric_key": "total_accounts",
            "metric_label": "Total de contas monitoradas",
            "metric_category": "métrica operacional atual",
            "metric_value": int(len(account_360)),
            "definition": "Total de contas presentes no snapshot atual usado pelo account_360.",
            "recommended_usage": "base operacional e denominador dos demais KPIs",
        },
        {
            "metric_key": "accounts_churn_flag_true",
            "metric_label": "Contas com churn_flag = true",
            "metric_category": "métrica cadastral",
            "metric_value": int(churn_flag.sum()),
            "definition": "Contas marcadas como churn na tabela cadastral de accounts.",
            "recommended_usage": "narrativa executiva e KPI oficial consolidado",
        },
        {
            "metric_key": "accounts_with_churn_event",
            "metric_label": "Contas com pelo menos um churn_event",
            "metric_category": "métrica observada por eventos",
            "metric_value": int(had_churn_event.gt(0).sum()),
            "definition": "Contas que tiveram pelo menos um evento de churn registrado na trilha histórica.",
            "recommended_usage": "histórico de jornada e análise de reincidência",
        },
        {
            "metric_key": "accounts_with_churn_flag_true_and_no_event",
            "metric_label": "Contas com churn_flag = true e sem churn_event",
            "metric_category": "métrica cadastral",
            "metric_value": int((churn_flag.eq(1) & had_churn_event.eq(0)).sum()),
            "definition": "Divergência onde o cadastro indica churn, mas a trilha de eventos não registra ocorrência.",
            "recommended_usage": "governança de dado e reconciliação cadastral",
        },
        {
            "metric_key": "accounts_with_event_and_churn_flag_false",
            "metric_label": "Contas com churn_event e churn_flag = false",
            "metric_category": "métrica observada por eventos",
            "metric_value": int((had_churn_event.eq(1) & churn_flag.eq(0)).sum()),
            "definition": "Divergência onde a trilha de eventos mostra churn histórico, mas o cadastro atual não marca churn.",
            "recommended_usage": "análise histórica, reativação e qualidade de integração",
        },
        {
            "metric_key": "accounts_reactivated",
            "metric_label": "Contas com reativação registrada",
            "metric_category": "métrica observada por eventos",
            "metric_value": int(reactivation_events.gt(0).sum()),
            "definition": "Contas com pelo menos um evento de reativação ao longo da jornada.",
            "recommended_usage": "histórico de recuperação e ciclos de churn",
        },
        {
            "metric_key": "accounts_currently_active_after_reactivation",
            "metric_label": "Contas ativas hoje após reativação",
            "metric_category": "métrica operacional atual",
            "metric_value": int((reactivation_events.gt(0) & active_subscriptions.gt(0)).sum()),
            "definition": "Contas que já reativaram em algum momento e continuam ativas no snapshot atual.",
            "recommended_usage": "operação atual e retenção preventiva de contas reincidentes",
        },
    ]
    return pd.DataFrame(metrics)


class BuildAccount360UseCase:
    def execute(self, data: DataBundle) -> pd.DataFrame:
        accounts = data.accounts.copy()
        subs = data.subscriptions.copy()
        usage = data.feature_usage.copy()
        tickets = data.support_tickets.copy()
        churn = data.churn_events.copy()

        usage = usage.merge(
            subs[["subscription_id", "account_id", "start_date", "end_date"]],
            on="subscription_id",
            how="left",
            validate="many_to_one",
        )

        snapshot_date = resolve_current_snapshot_date(data)

        subs_sorted = subs.sort_values(["account_id", "start_date", "subscription_id"]).copy()
        subs_sorted["is_active_at_snapshot"] = (
            (subs_sorted["start_date"] <= snapshot_date)
            & (
                subs_sorted["end_date"].isna()
                | (subs_sorted["end_date"] >= snapshot_date)
            )
        )

        latest_subs = (
            subs_sorted.groupby("account_id", as_index=False)
            .agg(
                subscriptions_count=("subscription_id", "count"),
                latest_plan=("plan_tier", "last"),
                latest_subscription_start=("start_date", "max"),
                latest_subscription_end=("end_date", "max"),
                upgrade_count=("upgrade_flag", "sum"),
                downgrade_count=("downgrade_flag", "sum"),
                churned_subscriptions=("churn_flag", "sum"),
            )
        )

        active_subs = subs_sorted.loc[subs_sorted["is_active_at_snapshot"]].copy()
        if active_subs.empty:
            active_sub_features = subs_sorted[["account_id"]].drop_duplicates().assign(
                current_mrr=0.0,
                current_arr=0.0,
                active_subscriptions=0,
                is_current_trial=False,
                current_billing_frequency="none",
                auto_renew_flag=False,
            )
        else:
            billing_mix = (
                active_subs.groupby("account_id")["billing_frequency"]
                .agg(
                    lambda s: "mixed"
                    if s.dropna().nunique() > 1
                    else (s.dropna().iloc[-1] if not s.dropna().empty else "none")
                )
                .reset_index(name="current_billing_frequency")
            )
            active_sub_features = (
                active_subs.groupby("account_id", as_index=False)
                .agg(
                    current_mrr=("mrr_amount", "sum"),
                    current_arr=("arr_amount", "sum"),
                    active_subscriptions=("subscription_id", "count"),
                    is_current_trial=("is_trial", "max"),
                    auto_renew_flag=("auto_renew_flag", "max"),
                )
                .merge(billing_mix, on="account_id", how="left", validate="one_to_one")
            )

        usage_base = usage.groupby("account_id", as_index=False).agg(
            usage_events=("usage_id", "count"),
            total_usage_count=("usage_count", "sum"),
            total_usage_duration_secs=("usage_duration_secs", "sum"),
            total_errors=("error_count", "sum"),
            distinct_features=("feature_name", "nunique"),
            beta_events=("is_beta_feature", "sum"),
            last_usage_date=("usage_date", "max"),
            first_usage_date=("usage_date", "min"),
        )

        usage["days_from_snapshot"] = (snapshot_date - usage["usage_date"]).dt.days

        usage_30 = (
            usage[usage["days_from_snapshot"] <= 30]
            .groupby("account_id", as_index=False)
            .agg(
                usage_count_30d=("usage_count", "sum"),
                errors_30d=("error_count", "sum"),
                usage_events_30d=("usage_id", "count"),
                features_30d=("feature_name", "nunique"),
                beta_events_30d=("is_beta_feature", "sum"),
            )
        )

        usage_prev_30 = (
            usage[(usage["days_from_snapshot"] > 30) & (usage["days_from_snapshot"] <= 60)]
            .groupby("account_id", as_index=False)
            .agg(
                usage_count_prev_30d=("usage_count", "sum"),
                errors_prev_30d=("error_count", "sum"),
                usage_events_prev_30d=("usage_id", "count"),
            )
        )

        ticket_features = tickets.groupby("account_id", as_index=False).agg(
            ticket_count=("ticket_id", "count"),
            avg_resolution_hours=("resolution_time_hours", "mean"),
            max_resolution_hours=("resolution_time_hours", "max"),
            avg_first_response_min=("first_response_time_minutes", "mean"),
            avg_satisfaction=("satisfaction_score", "mean"),
            escalation_count=("escalation_flag", "sum"),
            high_tickets=("priority", lambda s: int((s == "high").sum())),
            urgent_tickets=("priority", lambda s: int((s == "urgent").sum())),
            last_ticket_at=("submitted_at", "max"),
        )

        churn_features = churn.groupby("account_id", as_index=False).agg(
            churn_events=("churn_event_id", "count"),
            last_churn_date=("churn_date", "max"),
            total_refund_amount=("refund_amount_usd", "sum"),
            pricing_churns=("reason_code", lambda s: int((s == "pricing").sum())),
            support_churns=("reason_code", lambda s: int((s == "support").sum())),
            feature_churns=("reason_code", lambda s: int((s == "features").sum())),
            reactivation_events=("is_reactivation", "sum"),
            preceding_upgrade_events=("preceding_upgrade_flag", "sum"),
            preceding_downgrade_events=("preceding_downgrade_flag", "sum"),
        )

        if churn.empty:
            churn_state = accounts[["account_id"]].copy()
            churn_state["observed_churn_flag"] = 0
            churn_state["had_churn_event"] = 0
            churn_state["last_churn_was_reactivation"] = 0
        else:
            churn_sorted = churn.sort_values(["account_id", "churn_date", "churn_event_id"]).copy()
            last_events = churn_sorted.groupby("account_id", as_index=False).tail(1).copy()
            churn_state = last_events[["account_id", "is_reactivation"]].rename(
                columns={"is_reactivation": "last_churn_was_reactivation"}
            )
            churn_state["last_churn_was_reactivation"] = churn_state["last_churn_was_reactivation"].fillna(False).astype(int)
            churn_state["had_churn_event"] = 1
            churn_state["observed_churn_flag"] = (1 - churn_state["last_churn_was_reactivation"]).astype(int)

        df = (
            accounts.merge(latest_subs, on="account_id", how="left", validate="one_to_one")
            .merge(active_sub_features, on="account_id", how="left", validate="one_to_one")
            .merge(usage_base, on="account_id", how="left", validate="one_to_one")
            .merge(usage_30, on="account_id", how="left", validate="one_to_one")
            .merge(usage_prev_30, on="account_id", how="left", validate="one_to_one")
            .merge(ticket_features, on="account_id", how="left", validate="one_to_one")
            .merge(churn_features, on="account_id", how="left", validate="one_to_one")
            .merge(churn_state, on="account_id", how="left", validate="one_to_one")
        )

        fill_zero_cols = [
            "current_mrr",
            "current_arr",
            "usage_events",
            "total_usage_count",
            "total_usage_duration_secs",
            "total_errors",
            "distinct_features",
            "beta_events",
            "usage_count_30d",
            "errors_30d",
            "usage_events_30d",
            "features_30d",
            "beta_events_30d",
            "usage_count_prev_30d",
            "errors_prev_30d",
            "usage_events_prev_30d",
            "ticket_count",
            "escalation_count",
            "high_tickets",
            "urgent_tickets",
            "churn_events",
            "total_refund_amount",
            "pricing_churns",
            "support_churns",
            "feature_churns",
            "reactivation_events",
            "preceding_upgrade_events",
            "preceding_downgrade_events",
            "upgrade_count",
            "downgrade_count",
            "active_subscriptions",
            "churned_subscriptions",
            "subscriptions_count",
            "observed_churn_flag",
            "had_churn_event",
            "last_churn_was_reactivation",
        ]

        for col in fill_zero_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        bool_defaults = {
            "is_current_trial": False,
            "auto_renew_flag": False,
        }
        for col, default in bool_defaults.items():
            if col in df.columns:
                df[col] = df[col].fillna(default).astype(bool)

        object_defaults = {
            "current_billing_frequency": "none",
        }
        for col, default in object_defaults.items():
            if col in df.columns:
                df[col] = df[col].fillna(default)

        df["days_since_last_usage"] = (
            (snapshot_date - df["last_usage_date"]).dt.days.fillna(9999).astype(int)
        )
        df["days_since_last_ticket"] = (
            (snapshot_date - df["last_ticket_at"]).dt.days.fillna(9999).astype(int)
        )
        df["days_since_signup"] = (snapshot_date - df["signup_date"]).dt.days.astype(int)

        df["usage_drop_ratio"] = np.where(
            df["usage_count_prev_30d"] > 0,
            (df["usage_count_prev_30d"] - df["usage_count_30d"]) / df["usage_count_prev_30d"],
            0.0,
        )
        df["error_rate_30d"] = np.where(
            df["usage_count_30d"] > 0,
            df["errors_30d"] / df["usage_count_30d"],
            0.0,
        )
        df["avg_usage_per_event_30d"] = np.where(
            df["usage_events_30d"] > 0,
            df["usage_count_30d"] / df["usage_events_30d"],
            0.0,
        )
        df["avg_duration_per_event"] = np.where(
            df["usage_events"] > 0,
            df["total_usage_duration_secs"] / df["usage_events"],
            0.0,
        )
        df["escalation_rate"] = np.where(
            df["ticket_count"] > 0,
            df["escalation_count"] / df["ticket_count"],
            0.0,
        )
        df["urgent_ticket_rate"] = np.where(
            df["ticket_count"] > 0,
            df["urgent_tickets"] / df["ticket_count"],
            0.0,
        )

        df["support_burden_index"] = (
            (df["avg_first_response_min"].fillna(0) / 60.0) * 0.3
            + df["avg_resolution_hours"].fillna(0) * 0.5
            + df["escalation_rate"] * 10 * 0.2
        )

        df["revenue_band"] = pd.cut(
            df["current_mrr"].fillna(0),
            bins=[-1, 500, 1500, 4000, np.inf],
            labels=["low", "mid", "high", "strategic"],
        ).astype("object")

        df["usage_health_band"] = pd.cut(
            df["usage_count_30d"].fillna(0),
            bins=[-1, 20, 100, 250, np.inf],
            labels=["very_low", "low", "medium", "high"],
        ).astype("object")

        df["is_logo_churned"] = (df["active_subscriptions"] == 0).astype(int)
        df["snapshot_date"] = snapshot_date

        return df


class ScoreAccountsUseCase:
    def __init__(self, service: HealthScoreService | None = None) -> None:
        self.service = service or HealthScoreService()

    def execute(self, account_360: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        health_rows: list[dict[str, Any]] = []
        driver_rows: list[dict[str, Any]] = []

        for _, row in account_360.iterrows():
            health = self.service.evaluate(row)
            health_rows.append(health.as_record())

            for signal in health.signals:
                driver_rows.append(
                    {
                        "account_id": health.account_id,
                        "health_score": health.health_score,
                        "risk_level": health.risk_level,
                        "triggered_specification": signal.name,
                        "weight": signal.weight,
                        "evidence_metric": signal.evidence,
                        "interpretation": signal.interpretation,
                    }
                )

        customer_health = pd.DataFrame(health_rows)
        churn_risk_drivers = pd.DataFrame(driver_rows)
        return customer_health, churn_risk_drivers


class TrainClassifierUseCase:
    def __init__(self, config: ChurnPredictionConfig | None = None) -> None:
        self.config = config or ChurnPredictionConfig()

    def execute(
        self,
        data: DataBundle,
    ) -> tuple[Any, dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        dataset, leakage_report = build_point_in_time_dataset(
            data=data,
            config=self.config,
        )
        evaluation = evaluate_models(dataset=dataset, config=self.config)
        current_scoring_dataset, current_snapshot_date = build_current_scoring_dataset(
            data=data,
        )
        current_scoring = build_current_scoring_frame(
            model=evaluation["best_model"],
            feature_columns=evaluation["feature_columns"],
            scoring_dataset=current_scoring_dataset,
            threshold=evaluation["best_threshold"],
            scored_at=current_snapshot_date,
        )
        account_model_explanations, current_scoring_explainability, current_scoring_feature_effects = build_account_explainability(
            model=evaluation["best_model"],
            scoring_dataset=current_scoring_dataset,
            feature_columns=evaluation["feature_columns"],
            reference_dataset=dataset.reindex(columns=evaluation["feature_columns"]),
            top_k=3,
        )
        current_scoring = current_scoring.merge(
            current_scoring_explainability,
            on="account_id",
            how="left",
            validate="one_to_one",
        )
        model_global_explainability = build_global_explainability(
            aggregated_feature_importance=evaluation["feature_importance"],
            all_local_impacts=current_scoring_feature_effects,
            top_k=12,
        )

        metrics = {
            "roc_auc": float(evaluation["test_metrics"]["roc_auc"]),
            "average_precision": float(evaluation["test_metrics"]["pr_auc"]),
            "best_model_name": evaluation["best_model_name"],
            "best_selection_score": float(evaluation["best_selection_score"]),
            "best_threshold": float(evaluation["best_threshold"]),
            "threshold_strategy": evaluation["threshold_strategy"],
            "oof_metrics": evaluation["oof_metrics"],
            "random_validation_metrics": evaluation["random_validation_metrics"],
            "temporal_validation_metrics": evaluation["temporal_validation_metrics"],
            "validation_gap_summary": evaluation["validation_gap_summary"],
            "target_definition": "target=1 when a non-reactivation churn happens within 30 days after snapshot_date",
            "training_dataset_strategy": "multi_snapshot_per_account_temporal_horizon",
            "dataset_rows": int(dataset.shape[0]),
            "dataset_columns": int(dataset.shape[1]),
            "positive_rate": float(dataset["target_churn_30d"].mean()),
            "leakage_report": leakage_report.__dict__,
            "current_scoring": {
                "rows": int(current_scoring.shape[0]),
                "scored_at": str(pd.Timestamp(current_snapshot_date).isoformat()),
                "output_columns": current_scoring.columns.tolist(),
            },
            "explainability_strategy": {
                "global": "aggregated raw feature importance + average local impact on current portfolio",
                "local": "per-account probability impact after replacing each feature with the training baseline profile",
                "dependencies": "no additional heavy dependencies",
            },
            "top_global_drivers": model_global_explainability.head(5).to_dict(orient="records"),
            "comparison": evaluation["comparison"].to_dict(orient="records"),
            "train_val_metrics": evaluation["train_val_metrics"],
            "test_metrics": evaluation["test_metrics"],
            "robustness": evaluation["robustness"],
        }

        return (
            evaluation["best_model"],
            metrics,
            current_scoring,
            dataset,
            evaluation["comparison"],
            evaluation["feature_importance"],
            account_model_explanations,
            model_global_explainability,
        )


class BuildSolutionUseCase:
    def __init__(self) -> None:
        self.account_360_builder = BuildAccount360UseCase()
        self.scorer = ScoreAccountsUseCase()
        self.trainer = TrainClassifierUseCase()

    def execute(self, data: DataBundle) -> RunArtifacts:
        account_360 = self.account_360_builder.execute(data)
        customer_health, churn_risk_drivers = self.scorer.execute(account_360)
        (
            model,
            metrics,
            current_churn_scoring,
            point_in_time_training_dataset,
            model_comparison,
            feature_importance,
            account_model_explanations,
            model_global_explainability,
        ) = self.trainer.execute(data)

        account_360 = account_360.merge(
            customer_health,
            on="account_id",
            how="left",
            validate="one_to_one",
        )
        account_360 = account_360.merge(
            current_churn_scoring,
            on="account_id",
            how="left",
            validate="one_to_one",
        )

        account_360["priority_segment"] = np.select(
            [
                (account_360["risk_level"].isin(["critical", "high"])) & (account_360["current_mrr"] >= 2000),
                (account_360["risk_level"].isin(["critical", "high"])) & (account_360["current_mrr"] < 2000),
                (account_360["risk_level"] == "medium") & (account_360["current_mrr"] >= 2000),
            ],
            [
                "save_now_strategic",
                "save_now_volume",
                "watch_strategic",
            ],
            default="healthy_or_expand",
        )

        churn_reconciliation = build_churn_reconciliation(account_360)

        return RunArtifacts(
            account_360=account_360,
            customer_health=customer_health,
            churn_risk_drivers=churn_risk_drivers,
            churn_reconciliation=churn_reconciliation,
            model_metrics=metrics,
            model=model,
            current_churn_scoring=current_churn_scoring,
            account_model_explanations=account_model_explanations,
            model_global_explainability=model_global_explainability,
            point_in_time_training_dataset=point_in_time_training_dataset,
            model_comparison=model_comparison,
            feature_importance=feature_importance,
        )

    @staticmethod
    def save_model(model: Any, path: str) -> None:
        joblib.dump(model, path)
