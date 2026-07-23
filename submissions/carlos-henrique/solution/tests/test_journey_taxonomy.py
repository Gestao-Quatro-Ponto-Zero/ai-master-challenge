import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from journey_taxonomy import classify_journeys


def _record(population):
    dates = list(pd.to_datetime(["2024-01-01", "2024-02-01", "2024-02-10", "2024-02-11"]))
    return {"account_id": "a", "journey_scope": "FULL_OBSERVED_JOURNEY", "quality_population": population, "_tokens": ["SUBSCRIPTION_START", "CHURN", "REACTIVATION", "FEATURE"], "_dates": dates}


def test_taxonomy_is_deterministic_and_has_one_primary():
    features = pd.DataFrame({"account_id": ["a"], "feature_event_count_30d": [0], "active_days_30d": [0], "max_mrr": [3000], "quality_coverage_ratio": [1.0]})
    first = classify_journeys([_record("MAIN"), _record("STRICT")], features)
    second = classify_journeys([_record("MAIN"), _record("STRICT")], features)
    pd.testing.assert_frame_equal(first, second)
    assert first["primary_journey_class"].notna().all()
    assert set(first["stability_status"]) == {"ROBUST"}


def test_taxonomy_contains_no_prediction_or_action():
    features = pd.DataFrame({"account_id": ["a"], "feature_event_count_30d": [0], "active_days_30d": [0], "max_mrr": [3000], "quality_coverage_ratio": [1.0]})
    result = classify_journeys([_record("MAIN")], features).iloc[0]
    assert "NOT_AN_INDIVIDUAL_SCORE" in json.loads(result["limitations"])
    assert result["primary_journey_class"] == "RECOVERY_JOURNEY"
