"""Tests for temporal quarantine, duplicate policy, and churn attribution."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


SOLUTION_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SOLUTION_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from event_rules import QUALITY_QUARANTINED, QUALITY_WARNING, classify_quality  # noqa: E402
from temporal_quality import (  # noqa: E402
    account_event_flags,
    annotate_usage_duplicates,
    assign_churn_subscription,
    subscription_event_flags,
    ticket_event_flags,
    usage_event_flags,
)


SIGNUP = {"A1": pd.Timestamp("2024-01-01")}
SUBSCRIPTIONS = pd.DataFrame(
    [
        ["S1", "A1", "2024-01-02", "2024-01-10"],
        ["S2", "A1", "2024-01-05", None],
    ],
    columns=["subscription_id", "account_id", "start_date", "end_date"],
)
SUBSCRIPTION_LOOKUP = {
    str(row["subscription_id"]): row.to_dict() for _, row in SUBSCRIPTIONS.iterrows()
}


def test_invalid_timestamp_is_quarantined() -> None:
    flags = account_event_flags("A1", "not-a-date", SIGNUP)
    assert "INVALID_TIMESTAMP" in flags
    assert classify_quality(flags) == QUALITY_QUARANTINED


def test_pre_account_event_is_quarantined() -> None:
    flags = account_event_flags("A1", "2023-12-31", SIGNUP)
    assert flags == {"PRE_ACCOUNT_EVENT"}
    assert classify_quality(flags) == QUALITY_QUARANTINED


def test_pre_and_post_subscription_usage_are_quarantined() -> None:
    pre = usage_event_flags(
        account_id="A1", subscription_id="S1", event_time="2024-01-01",
        account_signup=SIGNUP, subscriptions_by_id=SUBSCRIPTION_LOOKUP,
    )
    post = usage_event_flags(
        account_id="A1", subscription_id="S1", event_time="2024-01-11",
        account_signup=SIGNUP, subscriptions_by_id=SUBSCRIPTION_LOOKUP,
    )
    assert "PRE_SUBSCRIPTION_USAGE" in pre
    assert "POST_SUBSCRIPTION_USAGE" in post
    assert classify_quality(pre) == QUALITY_QUARANTINED
    assert classify_quality(post) == QUALITY_QUARANTINED


def test_end_before_start_is_quarantined() -> None:
    flags = subscription_event_flags(
        account_id="A1", subscription_id="S1", event_time="2024-01-01",
        start_time="2024-01-02", end_time="2024-01-01",
        event_type="SUBSCRIPTION_ENDED", account_signup=SIGNUP,
    )
    assert "END_BEFORE_START" in flags
    assert classify_quality(flags) == QUALITY_QUARANTINED


def test_close_before_open_is_quarantined() -> None:
    flags = ticket_event_flags(
        account_id="A1", event_time="2024-01-02", opened_time="2024-01-03",
        event_type="SUPPORT_TICKET_CLOSED", account_signup=SIGNUP,
    )
    assert "CLOSE_BEFORE_OPEN" in flags
    assert classify_quality(flags) == QUALITY_QUARANTINED


def test_exact_active_churn_assignment_is_the_only_direct_link() -> None:
    assignment = assign_churn_subscription(SUBSCRIPTIONS.iloc[[0]], "A1", "2024-01-05")
    assert assignment.status == "EXACT_ACTIVE_MATCH"
    assert assignment.candidate_subscription_id == "S1"


def test_multiple_active_subscriptions_remain_ambiguous() -> None:
    assignment = assign_churn_subscription(SUBSCRIPTIONS, "A1", "2024-01-06")
    assert assignment.status == "MULTIPLE_ACTIVE_CANDIDATES"
    assert assignment.candidate_subscription_id is None
    assert assignment.active_candidate_count == 2


def test_churn_without_active_subscription_does_not_invent_link() -> None:
    assignment = assign_churn_subscription(SUBSCRIPTIONS.iloc[[0]], "A1", "2024-01-11")
    assert assignment.status == "SINGLE_PRIOR_SUBSCRIPTION"
    assert assignment.candidate_subscription_id is None


def test_duplicate_policy_distinguishes_exact_source_and_candidate() -> None:
    frame = pd.DataFrame(
        [
            ["U1", "S1", "2024-01-03", "F", 1],
            ["U1", "S1", "2024-01-04", "G", 2],
            ["U3", "S1", "2024-01-03", "F", 3],
            ["U3", "S1", "2024-01-03", "F", 3],
        ],
        columns=["usage_id", "subscription_id", "usage_date", "feature_name", "usage_count"],
    )
    annotated, summary = annotate_usage_duplicates(frame)
    assert summary["exact_duplicate_rows_removed"] == 1
    assert summary["duplicate_source_id_rows"] == 4
    assert summary["duplicate_candidate_key_rows"] == 3
    assert bool(annotated.iloc[-1]["_drop_exact_duplicate"])


def test_supported_warning_does_not_quarantine() -> None:
    assert classify_quality({"DUPLICATE_SOURCE_ID"}) == QUALITY_WARNING
