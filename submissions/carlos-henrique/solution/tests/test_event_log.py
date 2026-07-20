"""Tests for canonical event generation, provenance, reconciliation, and privacy."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
import pytest


SOLUTION_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SOLUTION_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from event_log import EVENT_COLUMNS, build_event_log  # noqa: E402
from event_rules import event_dictionary, event_id_for  # noqa: E402


def _frames() -> dict[str, pd.DataFrame]:
    accounts = pd.DataFrame(
        [
            ["A1", "Private Alpha", "SaaS", "BR", "2024-01-01", "web", "pro", 10, False, False],
            ["A2", "Private Beta", "Retail", "BR", "2024-01-01", "partner", "basic", 5, False, False],
        ],
        columns=[
            "account_id", "account_name", "industry", "country", "signup_date",
            "referral_source", "plan_tier", "seats", "is_trial", "churn_flag",
        ],
    )
    subscriptions = pd.DataFrame(
        [
            ["S1", "A1", "2024-01-02", "2024-01-10", "pro", 10, 100.0, 1200.0, False, False, False, False, "monthly", True],
            ["S2", "A1", "2024-01-05", None, "pro", 12, 120.0, 1440.0, False, False, False, False, "monthly", True],
            ["S3", "A2", "2024-02-01", None, "basic", 5, 50.0, 600.0, False, False, False, False, "monthly", True],
        ],
        columns=[
            "subscription_id", "account_id", "start_date", "end_date", "plan_tier",
            "seats", "mrr_amount", "arr_amount", "is_trial", "upgrade_flag",
            "downgrade_flag", "churn_flag", "billing_frequency", "auto_renew_flag",
        ],
    )
    usage = pd.DataFrame(
        [
            ["U1", "S1", "2024-01-03", "analytics", 1, 30, 0, False],
            ["U1", "S1", "2024-01-04", "export", 2, 50, 0, False],
            ["U3", "S1", "2024-01-03", "analytics", 3, 60, 0, False],
            ["U4", "S1", "2024-01-01", "search", 1, 10, 0, False],
            ["U5", "S1", "2024-01-11", "search", 1, 10, 0, False],
        ],
        columns=[
            "usage_id", "subscription_id", "usage_date", "feature_name", "usage_count",
            "usage_duration_secs", "error_count", "is_beta_feature",
        ],
    )
    tickets = pd.DataFrame(
        [
            ["T1", "A1", "2024-01-03", "2024-01-04 10:00:00", 34.0, "HIGH", 15, 4.0, False],
            ["T2", "A2", "2023-12-31", "2024-01-02 10:00:00", 58.0, "LOW", 30, 3.0, True],
        ],
        columns=[
            "ticket_id", "account_id", "submitted_at", "closed_at", "resolution_time_hours",
            "priority", "first_response_time_minutes", "satisfaction_score", "escalation_flag",
        ],
    )
    churn = pd.DataFrame(
        [
            ["C1", "A1", "2024-01-06", "PRICE", 0.0, False, False, False, "private feedback"],
            ["C2", "A1", "2024-01-08", "RETURN", 0.0, False, False, True, "private feedback"],
            ["C3", "A1", "2024-01-09", "OTHER", 0.0, False, False, False, "private feedback"],
        ],
        columns=[
            "churn_event_id", "account_id", "churn_date", "reason_code", "refund_amount_usd",
            "preceding_upgrade_flag", "preceding_downgrade_flag", "is_reactivation", "feedback_text",
        ],
    )
    return {
        "accounts": accounts,
        "subscriptions": subscriptions,
        "feature_usage": usage,
        "support_tickets": tickets,
        "churn_events": churn,
    }


@pytest.fixture(scope="module")
def result():
    return build_event_log(_frames())


def test_event_id_is_deterministic_and_row_sensitive() -> None:
    kwargs = {
        "source_table": "feature_usage",
        "source_record_id": "U1",
        "source_row_number": 2,
        "event_type": "FEATURE_USED",
        "event_time": pd.Timestamp("2024-01-03"),
    }
    assert event_id_for(**kwargs) == event_id_for(**kwargs)
    assert event_id_for(**kwargs) != event_id_for(**{**kwargs, "source_row_number": 3})


def test_event_log_has_canonical_schema_and_provenance(result) -> None:
    combined = pd.concat([result.event_log, result.quarantined_events])
    assert list(result.event_log.columns) == EVENT_COLUMNS
    assert combined["event_id"].is_unique
    assert combined["source_record_id"].notna().all()
    assert combined["source_row_number"].ge(2).all()
    assert combined["derivation_rule"].str.len().gt(0).all()


def test_source_event_generation_is_reconciled(result) -> None:
    assert result.reconciliation["events_by_type"] == {
        "ACCOUNT_CREATED": 2,
        "CHURN_RECORDED": 2,
        "FEATURE_USED": 5,
        "REACTIVATION_RECORDED": 1,
        "SUBSCRIPTION_ENDED": 1,
        "SUBSCRIPTION_STARTED": 3,
        "SUPPORT_TICKET_CLOSED": 2,
        "SUPPORT_TICKET_OPENED": 2,
    }
    assert result.reconciliation["totals"]["events_generated"] == 18
    assert result.reconciliation["totals"]["unexplained_difference"] == 0


def test_free_text_and_snapshot_leakage_are_absent(result) -> None:
    forbidden = {
        "account_name", "feedback_text", "reason_code", "refund_amount_usd",
        "churn_flag", "upgrade_flag", "downgrade_flag",
    }
    combined = pd.concat([result.event_log, result.quarantined_events])
    assert forbidden.isdisjoint(combined.columns)
    serialized = combined.to_json(date_format="iso", orient="records")
    assert "Private Alpha" not in serialized
    assert "private feedback" not in serialized


def test_duplicate_source_and_candidate_keys_are_preserved_with_flags(result) -> None:
    combined = pd.concat([result.event_log, result.quarantined_events])
    usage = combined.loc[combined["event_type"].eq("FEATURE_USED")]
    assert len(usage) == 5
    assert usage["quality_flags"].str.contains("DUPLICATE_SOURCE_ID", regex=False).sum() == 2
    assert usage["quality_flags"].str.contains("DUPLICATE_CANDIDATE_KEY", regex=False).sum() == 2


def test_churn_recurrence_and_reactivation_are_not_collapsed(result) -> None:
    combined = pd.concat([result.event_log, result.quarantined_events])
    churn = combined.loc[combined["event_type"].eq("CHURN_RECORDED")].sort_values("event_time")
    reactivation = combined.loc[combined["event_type"].eq("REACTIVATION_RECORDED")]
    assert churn["churn_sequence_number"].tolist() == [1, 2]
    assert churn.iloc[1]["days_since_previous_churn"] == 3
    assert len(reactivation) == 1
    assert reactivation.iloc[0]["days_since_previous_churn"] == 2


def test_same_day_order_uses_documented_noncausal_tie_break(result) -> None:
    combined = pd.concat([result.event_log, result.quarantined_events])
    same_day = combined.loc[
        combined["account_id"].eq("A1")
        & combined["event_time"].dt.normalize().eq(pd.Timestamp("2024-01-03"))
    ].sort_values("event_order_on_same_day")
    assert same_day["event_type"].tolist() == [
        "FEATURE_USED", "FEATURE_USED", "SUPPORT_TICKET_OPENED"
    ]
    assert same_day["quality_flags"].str.contains("SAME_DAY_ORDER_ASSIGNED", regex=False).all()


def test_open_and_overlapping_subscription_episodes_are_preserved(result) -> None:
    episodes = result.subscription_episodes.set_index("subscription_id")
    assert episodes.loc["S2", "episode_status"] == "OPEN"
    assert bool(episodes.loc["S1", "has_overlap"])
    assert bool(episodes.loc["S2", "has_overlap"])
    assert episodes.loc["S1", "episode_id"] != episodes.loc["S2", "episode_id"]


def test_repeated_in_memory_build_is_idempotent() -> None:
    first = build_event_log(_frames())
    second = build_event_log(_frames())
    assert first.event_log["event_id"].tolist() == second.event_log["event_id"].tolist()
    assert first.quarantined_events["event_id"].tolist() == second.quarantined_events["event_id"].tolist()
    assert first.reconciliation == second.reconciliation


def test_dictionary_contains_only_implemented_source_events() -> None:
    dictionary = event_dictionary()
    names = {item["name"] for item in dictionary["event_types"]}
    assert names == {
        "ACCOUNT_CREATED", "SUBSCRIPTION_STARTED", "SUBSCRIPTION_ENDED", "FEATURE_USED",
        "SUPPORT_TICKET_OPENED", "SUPPORT_TICKET_CLOSED", "CHURN_RECORDED",
        "REACTIVATION_RECORDED",
    }
    assert all(item["derivation_type"] == "SOURCE" for item in dictionary["event_types"])


def test_real_outputs_have_no_free_text_or_pii_patterns() -> None:
    processed = SOLUTION_ROOT / "data" / "processed"
    paths = [
        processed / "event_log.parquet",
        processed / "quarantined_events.parquet",
        processed / "subscription_episodes.parquet",
    ]
    assert all(path.is_file() for path in paths)
    email = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
    forbidden_columns = {"account_name", "feedback_text", "reason_code"}
    for path in paths:
        frame = pd.read_parquet(path)
        assert forbidden_columns.isdisjoint(frame.columns)
        for column in frame.select_dtypes(include=["object", "string"]).columns:
            assert not frame[column].dropna().astype(str).str.contains(email).any()
    manifest_text = (SOLUTION_ROOT / "artifacts" / "event_log_manifest.json").read_text(encoding="utf-8")
    assert "C:\\" not in manifest_text
    json.loads(manifest_text)
