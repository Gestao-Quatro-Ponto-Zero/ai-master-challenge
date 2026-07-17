import pytest
from dashboard.decision import break_even, experiment_copy


def test_break_even_translates_cost_into_minimum_incremental_result() -> None:
    result = break_even(10_000, 250, 100_000)
    assert result["incremental_conversions"] == 40
    assert result["incremental_rate"] == pytest.approx(0.0004)
    assert result["required_margin"] == pytest.approx(10_000)


def test_break_even_rejects_invalid_business_inputs() -> None:
    with pytest.raises(ValueError):
        break_even(1_000, 0, 10_000)


def test_experiment_copy_maps_objective_to_metric_and_guardrail() -> None:
    result = experiment_copy("Conversão")
    assert result["metric"] == "margem incremental"
    assert "CAC" in result["guardrail"]
