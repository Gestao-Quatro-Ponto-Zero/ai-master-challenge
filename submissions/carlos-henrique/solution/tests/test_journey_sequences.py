import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from journey_sequences import build_account_journeys, collapse_consecutive, same_day_dependency


def _events():
    types = ["ACCOUNT_CREATED", "SUBSCRIPTION_STARTED", "FEATURE_USED", "FEATURE_USED", "CHURN_RECORDED", "REACTIVATION_RECORDED", "FEATURE_USED", "CHURN_RECORDED"]
    times = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-03", "2024-02-01", "2024-02-10", "2024-02-11", "2024-03-01"])
    return pd.DataFrame({"event_id": [f"e{i}" for i in range(8)], "account_id": ["a"] * 8, "event_time": times, "event_type": types, "event_order_on_same_day": range(1, 9), "quality_status": ["VALID"] * 8, "is_quarantined": [False] * 8})


def test_collapse_and_same_day_dependency():
    dates = list(pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"]))
    tokens, kept_dates = collapse_consecutive(["FEATURE", "FEATURE", "CHURN"], dates)
    assert tokens == ["FEATURE", "CHURN"]
    assert same_day_dependency(["FEATURE", "SUPPORT_OPEN"], dates[:2]) == "PARTIAL"
    assert len(kept_dates) == 2


def test_scopes_are_bounded_and_unique():
    features = pd.DataFrame({"account_id": ["a"], "primary_outcome": ["REACTIVATED_THEN_CHURNED_AGAIN"], "quality_coverage_ratio": [1.0]})
    built = build_account_journeys(_events(), features, observation_end="2024-04-30")
    assert not built.dataset.duplicated(["account_id", "journey_scope", "quality_population"]).any()
    pre = built.dataset.set_index("journey_scope").loc["PRE_FIRST_CHURN"]
    assert json.loads(pre["collapsed_sequence"])[-1] == "CHURN"
    post = built.dataset.set_index("journey_scope").loc["POST_REACTIVATION"]
    assert json.loads(post["collapsed_sequence"])[0] == "REACTIVATION"
    between = built.dataset.set_index("journey_scope").loc["BETWEEN_RECURRING_CHURNS"]
    assert json.loads(between["collapsed_sequence"])[0] == "CHURN"


def test_quarantine_never_enters_sequence():
    events = _events()
    events.loc[len(events)] = ["q", "a", pd.Timestamp("2024-01-04"), "SUPPORT_TICKET_OPENED", 1, "VALID", True]
    features = pd.DataFrame({"account_id": ["a"], "primary_outcome": ["REACTIVATED_THEN_CHURNED_AGAIN"], "quality_coverage_ratio": [1.0]})
    full = build_account_journeys(events, features, observation_end="2024-04-30").dataset.query("journey_scope == 'FULL_OBSERVED_JOURNEY'").iloc[0]
    assert "SUPPORT_OPEN" not in full["collapsed_sequence"]
