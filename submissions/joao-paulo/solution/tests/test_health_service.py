import pandas as pd

from churn_diagnosis.domain.services import HealthScoreService


def test_health_score_high_risk_for_compound_signals():
    service = HealthScoreService()
    row = pd.Series({
        "account_id": "A-1",
        "usage_drop_ratio": 0.5,
        "days_since_last_usage": 40,
        "error_rate_30d": 0.09,
        "distinct_features": 5,
        "avg_first_response_min": 300,
        "avg_resolution_hours": 70,
        "avg_satisfaction": 2.2,
        "escalation_rate": 0.4,
        "downgrade_count": 2,
        "auto_renew_flag": False,
        "is_current_trial": False,
        "is_trial": False,
        "reactivation_events": 1,
        "current_mrr": 4500,
    })
    result = service.evaluate(row)
    assert result.risk_level in {"critical", "high"}
    assert result.health_score >= 75
    assert result.mrr_at_risk == 4500


def test_health_score_low_for_healthy_account():
    service = HealthScoreService()
    row = pd.Series({
        "account_id": "A-2",
        "usage_drop_ratio": 0.0,
        "days_since_last_usage": 2,
        "error_rate_30d": 0.01,
        "distinct_features": 18,
        "avg_first_response_min": 20,
        "avg_resolution_hours": 5,
        "avg_satisfaction": 4.5,
        "escalation_rate": 0.0,
        "downgrade_count": 0,
        "auto_renew_flag": True,
        "is_current_trial": False,
        "is_trial": False,
        "reactivation_events": 0,
        "current_mrr": 2000,
    })
    result = service.evaluate(row)
    assert result.risk_level == "low"
    assert result.health_score < 30


def test_primary_driver_prefers_highest_weight_signal():
    service = HealthScoreService()
    row = pd.Series({
        "account_id": "A-3",
        "usage_drop_ratio": 0.5,
        "days_since_last_usage": 10,
        "error_rate_30d": 0.0,
        "distinct_features": 15,
        "avg_first_response_min": 20,
        "avg_resolution_hours": 5,
        "avg_satisfaction": 4.5,
        "escalation_rate": 0.0,
        "downgrade_count": 1,
        "auto_renew_flag": True,
        "is_current_trial": False,
        "is_trial": False,
        "reactivation_events": 0,
        "current_mrr": 1500,
    })
    result = service.evaluate(row)
    assert result.primary_driver == "recent_usage_drop"
    assert result.secondary_driver == "recent_downgrade"
