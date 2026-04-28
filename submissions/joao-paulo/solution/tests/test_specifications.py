import pandas as pd
import pytest

from churn_diagnosis.domain.specifications import Specification, SpecificationEvaluationError, risk_specifications


def test_recent_usage_drop_spec_triggers():
    row = pd.Series({
        "usage_drop_ratio": 0.60,
        "days_since_last_usage": 45,
        "error_rate_30d": 0.12,
        "distinct_features": 4,
        "avg_first_response_min": 240,
        "avg_resolution_hours": 60,
        "avg_satisfaction": 2.0,
        "escalation_rate": 0.5,
        "downgrade_count": 1,
        "auto_renew_flag": False,
        "is_current_trial": False,
        "is_trial": False,
        "reactivation_events": 1,
    })
    names = [spec.name for spec in risk_specifications() if spec.is_satisfied_by(row)]
    assert "recent_usage_drop" in names
    assert "usage_stale" in names
    assert "high_error_rate" in names
    assert "recent_downgrade" in names


def test_healthy_row_triggers_nothing_major():
    row = pd.Series({
        "usage_drop_ratio": 0.0,
        "days_since_last_usage": 3,
        "error_rate_30d": 0.01,
        "distinct_features": 20,
        "avg_first_response_min": 30,
        "avg_resolution_hours": 8,
        "avg_satisfaction": 4.8,
        "escalation_rate": 0.0,
        "downgrade_count": 0,
        "auto_renew_flag": True,
        "is_current_trial": False,
        "is_trial": False,
        "reactivation_events": 0,
    })
    names = [spec.name for spec in risk_specifications() if spec.is_satisfied_by(row)]
    assert "recent_usage_drop" not in names
    assert "usage_stale" not in names
    assert "poor_support_experience" not in names


def test_specification_raises_contextual_error_on_predicate_failure():
    spec = Specification(
        name="broken_spec",
        weight=10,
        message="Broken.",
        predicate=lambda r: r["missing_column"] > 0,
        evidence_field="missing_column",
    )

    with pytest.raises(SpecificationEvaluationError, match="broken_spec"):
        spec.is_satisfied_by(pd.Series({"account_id": "A-1"}))
