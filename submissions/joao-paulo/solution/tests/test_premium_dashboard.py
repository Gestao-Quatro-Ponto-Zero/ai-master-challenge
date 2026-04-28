from __future__ import annotations

import json
from pathlib import Path
import shutil
from uuid import uuid4

import pandas as pd

from churn_diagnosis.presentation.generate_executive_dashboard import generate_dashboard


def _build_reconciliation(account_360: pd.DataFrame) -> pd.DataFrame:
    churn_flag = pd.to_numeric(account_360.get("churn_flag", 0), errors="coerce").fillna(0).astype(int)
    had_churn_event = pd.to_numeric(account_360.get("had_churn_event", 0), errors="coerce").fillna(0).astype(int)
    reactivation_events = pd.to_numeric(account_360.get("reactivation_events", 0), errors="coerce").fillna(0)
    active_subscriptions = pd.to_numeric(account_360.get("active_subscriptions", 0), errors="coerce").fillna(0)
    return pd.DataFrame(
        [
            {
                "metric_key": "total_accounts",
                "metric_label": "Total de contas monitoradas",
                "metric_category": "métrica operacional atual",
                "metric_value": int(len(account_360)),
                "definition": "Snapshot atual.",
                "recommended_usage": "base operacional",
            },
            {
                "metric_key": "accounts_churn_flag_true",
                "metric_label": "Contas com churn_flag = true",
                "metric_category": "métrica cadastral",
                "metric_value": int(churn_flag.sum()),
                "definition": "Cadastro.",
                "recommended_usage": "narrativa executiva",
            },
            {
                "metric_key": "accounts_with_churn_event",
                "metric_label": "Contas com churn_event",
                "metric_category": "métrica observada por eventos",
                "metric_value": int(had_churn_event.gt(0).sum()),
                "definition": "Eventos históricos.",
                "recommended_usage": "histórico",
            },
            {
                "metric_key": "accounts_with_churn_flag_true_and_no_event",
                "metric_label": "Churn cadastral sem evento",
                "metric_category": "métrica cadastral",
                "metric_value": int((churn_flag.eq(1) & had_churn_event.eq(0)).sum()),
                "definition": "Divergência 1.",
                "recommended_usage": "governança",
            },
            {
                "metric_key": "accounts_with_event_and_churn_flag_false",
                "metric_label": "Evento sem churn cadastral",
                "metric_category": "métrica observada por eventos",
                "metric_value": int((had_churn_event.eq(1) & churn_flag.eq(0)).sum()),
                "definition": "Divergência 2.",
                "recommended_usage": "governança",
            },
            {
                "metric_key": "accounts_reactivated",
                "metric_label": "Contas reativadas",
                "metric_category": "métrica observada por eventos",
                "metric_value": int(reactivation_events.gt(0).sum()),
                "definition": "Reativação.",
                "recommended_usage": "histórico",
            },
            {
                "metric_key": "accounts_currently_active_after_reactivation",
                "metric_label": "Ativas após reativação",
                "metric_category": "métrica operacional atual",
                "metric_value": int((reactivation_events.gt(0) & active_subscriptions.gt(0)).sum()),
                "definition": "Reativadas e ativas.",
                "recommended_usage": "operação",
            },
        ]
    )


def _write_dashboard_inputs(
    target_dir: Path,
    account_360: pd.DataFrame,
    drivers: pd.DataFrame,
    metrics: dict,
    reconciliation: pd.DataFrame | None = None,
) -> None:
    stable_accounts = account_360.sort_values("account_id").reset_index(drop=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    account_360.to_csv(target_dir / "account_360.csv", index=False)
    drivers.to_csv(target_dir / "churn_risk_drivers.csv", index=False)
    (reconciliation if reconciliation is not None else _build_reconciliation(account_360)).to_csv(
        target_dir / "churn_reconciliation.csv",
        index=False,
    )
    pd.DataFrame(
        [
            {
                "feature": "usage_drop_ratio",
                "feature_label": "Queda recente de uso",
                "importance": 0.28,
                "transformed_features": 1,
                "normalized_importance": 0.28,
                "avg_signed_impact": 0.082,
                "avg_abs_impact": 0.090,
                "median_abs_impact": 0.080,
                "accounts_raising_risk": 2,
                "accounts_reducing_risk": 1,
                "sample_size": max(len(account_360), 1),
                "raising_share": 0.67,
                "portfolio_direction": "elevates_risk",
                "impact_statement": "Queda recente de uso tende a elevar risco no portfólio.",
            },
            {
                "feature": "auto_renew_flag",
                "feature_label": "Auto-renovação",
                "importance": 0.19,
                "transformed_features": 1,
                "normalized_importance": 0.19,
                "avg_signed_impact": -0.041,
                "avg_abs_impact": 0.050,
                "median_abs_impact": 0.050,
                "accounts_raising_risk": 1,
                "accounts_reducing_risk": 2,
                "sample_size": max(len(account_360), 1),
                "raising_share": 0.33,
                "portfolio_direction": "reduces_risk",
                "impact_statement": "Auto-renovação atua mais como fator protetivo.",
            },
        ]
    ).to_csv(target_dir / "model_global_explainability.csv", index=False)
    pd.DataFrame(
        [
            {
                "account_id": stable_accounts.iloc[0]["account_id"],
                "rank": 1,
                "feature": "usage_drop_ratio",
                "feature_label": "Queda recente de uso",
                "feature_value": "0.550",
                "baseline_value": "0.120",
                "local_impact": 0.083,
                "abs_local_impact": 0.083,
                "impact_direction": "raises_risk",
                "explanation_text": "Queda recente de uso eleva o risco da conta.",
            }
        ]
    ).to_csv(target_dir / "account_model_explanations.csv", index=False)
    (target_dir / "model_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def test_generate_dashboard_is_deterministic_and_preserves_inputs():
    account_360 = pd.DataFrame(
        [
            {
                "account_id": "A-2",
                "account_name": "Bravo Corp",
                "industry": "HealthTech",
                "current_mrr": 2000,
                "mrr_at_risk": 2000,
                "health_score": 80,
                "risk_level": "critical",
                "primary_driver": "usage_stale",
                "recommended_action": "Action B",
                "current_churn_probability": 0.90,
                "latest_plan": "Pro",
                "churn_flag": 1,
                "had_churn_event": 1,
                "reactivation_events": 1,
                "active_subscriptions": 1,
            },
            {
                "account_id": "A-1",
                "account_name": "Alpha Corp",
                "industry": "FinTech",
                "current_mrr": 2000,
                "mrr_at_risk": 2000,
                "health_score": 80,
                "risk_level": "critical",
                "primary_driver": "recent_usage_drop",
                "recommended_action": "Action A",
                "current_churn_probability": 0.90,
                "latest_plan": "Pro",
                "churn_flag": 0,
                "had_churn_event": 1,
                "reactivation_events": 0,
                "active_subscriptions": 1,
            },
            {
                "account_id": "A-3",
                "account_name": "Charlie Corp",
                "industry": "EdTech",
                "current_mrr": 500,
                "mrr_at_risk": 0,
                "health_score": 15,
                "risk_level": "low",
                "primary_driver": "healthy",
                "recommended_action": "Action C",
                "current_churn_probability": 0.10,
                "latest_plan": "Basic",
                "churn_flag": 1,
                "had_churn_event": 0,
                "reactivation_events": 0,
                "active_subscriptions": 0,
            },
        ]
    )
    drivers = pd.DataFrame(
        [
            {
                "account_id": "A-2",
                "triggered_specification": "usage_stale",
                "weight": 18,
                "evidence_metric": 40,
            },
            {
                "account_id": "A-1",
                "triggered_specification": "recent_usage_drop",
                "weight": 22,
                "evidence_metric": 0.55,
            },
            {
                "account_id": "A-2",
                "triggered_specification": "recent_usage_drop",
                "weight": 22,
                "evidence_metric": 0.65,
            },
            {
                "account_id": "A-1",
                "triggered_specification": "usage_stale",
                "weight": 18,
                "evidence_metric": 35,
            },
        ]
    )
    metrics = {"roc_auc": 0.9123, "average_precision": 0.8345}

    root = Path("tests") / f".tmp_dashboard_{uuid4().hex}"
    base_dir = root / "base"
    shuffled_dir = root / "shuffled"

    try:
        _write_dashboard_inputs(base_dir, account_360, drivers, metrics)
        _write_dashboard_inputs(
            shuffled_dir,
            account_360.sample(frac=1, random_state=7).reset_index(drop=True),
            drivers.sample(frac=1, random_state=11).reset_index(drop=True),
            metrics,
        )

        before_inputs = {
            name: (base_dir / name).read_bytes()
            for name in [
                "account_360.csv",
                "churn_risk_drivers.csv",
                "churn_reconciliation.csv",
                "model_global_explainability.csv",
                "account_model_explanations.csv",
                "model_metrics.json",
            ]
        }

        first_target = generate_dashboard(base_dir)
        second_target = generate_dashboard(base_dir)
        shuffled_target = generate_dashboard(shuffled_dir)

        first_html = first_target.read_text(encoding="utf-8")
        second_html = second_target.read_text(encoding="utf-8")
        shuffled_html = shuffled_target.read_text(encoding="utf-8")

        assert first_html == second_html
        assert first_html == shuffled_html
        assert "Cockpit Executivo de Receita" in first_html
        assert "Resumo para decisão" in first_html
        assert "Decisão agora" in first_html
        assert "Fila executiva de hoje" in first_html
        assert "Reconciliação formal de churn" in first_html
        assert "Explicabilidade global do modelo" in first_html
        assert "Explicabilidade por conta" in first_html
        assert "https://cdn.plot.ly" not in first_html
        assert "fonts.googleapis.com" not in first_html
        assert "fonts.gstatic.com" not in first_html
        assert "script src=" not in first_html.lower()

        after_inputs = {
            name: (base_dir / name).read_bytes()
            for name in [
                "account_360.csv",
                "churn_risk_drivers.csv",
                "churn_reconciliation.csv",
                "model_global_explainability.csv",
                "account_model_explanations.csv",
                "model_metrics.json",
            ]
        }
        assert before_inputs == after_inputs
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_generate_dashboard_handles_empty_driver_file_with_schema():
    account_360 = pd.DataFrame(
        [
            {
                "account_id": "A-1",
                "account_name": "Alpha Corp",
                "industry": "FinTech",
                "current_mrr": 1500,
                "mrr_at_risk": 0,
                "health_score": 12,
                "risk_level": "low",
                "primary_driver": "healthy",
                "recommended_action": "Keep monitoring",
                "current_churn_probability": 0.11,
                "latest_plan": "Pro",
                "churn_flag": 0,
                "had_churn_event": 0,
                "reactivation_events": 0,
                "active_subscriptions": 1,
            }
        ]
    )
    drivers = pd.DataFrame(
        columns=[
            "account_id",
            "health_score",
            "risk_level",
            "triggered_specification",
            "weight",
            "evidence_metric",
            "interpretation",
        ]
    )
    metrics = {"roc_auc": 0.8123, "average_precision": 0.6345}

    root = Path("tests") / f".tmp_dashboard_empty_{uuid4().hex}"
    try:
        _write_dashboard_inputs(root, account_360, drivers, metrics)
        target = generate_dashboard(root)
        html = target.read_text(encoding="utf-8")
        assert "Cockpit Executivo de Receita" in html
        assert "Resumo para decisão" in html
        assert "churn_reconciliation.csv" in html
        assert "https://cdn.plot.ly" not in html
    finally:
        shutil.rmtree(root, ignore_errors=True)
