"""Tests for the read-only RavenStack source-audit pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest


SOLUTION_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SOLUTION_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from data_audit import (  # noqa: E402
    audit_key,
    calculate_match_rate,
    classify_leakage,
    compute_sha256,
    count_chronology_violations,
    detect_orphans,
    ensure_no_raw_text,
    measure_join_inflation,
    parse_datetime_series,
    profile_dataframe,
    run_consistency_audit,
    sanitize_value,
)
from data_loader import (  # noqa: E402
    OFFICIAL_FILES,
    DataLoadError,
    load_csv,
    validate_all_present,
)


def test_five_official_files_are_present() -> None:
    paths = validate_all_present()
    assert set(paths) == set(OFFICIAL_FILES)
    assert all(path.is_file() for path in paths.values())


def test_loader_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(DataLoadError, match="missing"):
        load_csv("accounts", raw_data_dir=tmp_path)


def test_sha256_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_bytes(b"abc")
    expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert compute_sha256(source) == expected
    assert compute_sha256(source) == compute_sha256(source)


def test_minimum_profile_contains_required_shape() -> None:
    frame = pd.DataFrame({"entity_id": ["a", "b"], "value": [1, 2]})
    profile = profile_dataframe("example", frame)
    assert profile["records"] == 2
    assert profile["column_count"] == 2
    assert profile["columns"] == ["entity_id", "value"]
    assert "column_profiles" in profile
    assert "candidate_keys" in profile


def test_duration_measures_are_not_classified_as_timestamps() -> None:
    frame = pd.DataFrame(
        {
            "submitted_at": ["2025-01-01"],
            "resolution_time_hours": [12.5],
            "first_response_time_minutes": [30],
        }
    )
    profile = profile_dataframe("support_tickets", frame)
    assert set(profile["temporal_columns"]) == {"submitted_at"}


def test_duplicate_key_is_detected() -> None:
    frame = pd.DataFrame({"entity_id": ["a", "a", "b"]})
    result = audit_key(frame, "entity_id")
    assert result["duplicate_excess_rows"] == 1
    assert result["duplicate_affected_rows"] == 2
    assert result["status"] == "INVALID"


def test_null_key_is_detected() -> None:
    frame = pd.DataFrame({"entity_id": ["a", None, "b"]})
    result = audit_key(frame, "entity_id")
    assert result["null_rows"] == 1
    assert result["status"] == "INVALID"


def test_orphans_are_detected_without_exposing_values() -> None:
    parent = pd.Series(["a", "b"])
    child = pd.Series(["a", "c", "c"])
    result = detect_orphans(parent, child)
    assert result == {"orphan_rows": 2, "orphan_unique_values": 1}
    assert "c" not in json.dumps(result)


def test_match_rate_uses_non_null_child_rows() -> None:
    parent = pd.Series(["a", "b"])
    child = pd.Series(["a", "b", "c", None])
    assert calculate_match_rate(parent, child) == pytest.approx(2 / 3)


def test_join_inflation_is_detected() -> None:
    parent = pd.DataFrame({"account_id": ["a", "b"]})
    child = pd.DataFrame({"account_id": ["a", "a", "b"]})
    result = measure_join_inflation(parent, "account_id", child, "account_id")
    assert result["rows_before"] == 2
    assert result["rows_after"] == 3
    assert result["multiplier"] == 1.5
    assert result["one_to_many_expansion"] is True


def test_valid_and_invalid_dates_are_parsed() -> None:
    parsed = parse_datetime_series(pd.Series(["2025-01-01", "not-a-date", None]))
    assert parsed.notna().sum() == 1
    assert parsed.isna().sum() == 2


def test_impossible_chronology_is_detected() -> None:
    frame = pd.DataFrame(
        {
            "start_date": ["2025-01-02", "2025-01-01"],
            "end_date": ["2025-01-01", "2025-01-03"],
        }
    )
    assert count_chronology_violations(frame, "start_date", "end_date") == 1


def test_leakage_classification() -> None:
    explicit = classify_leakage("accounts", "churn_flag")
    temporal = classify_leakage("feature_usage", "usage_date")
    safe = classify_leakage("accounts", "industry")
    assert explicit["risk"] == "EXPLICIT"
    assert temporal["risk"] == "TEMPORAL"
    assert safe["risk"] == "NONE_IDENTIFIED"


def test_text_and_identifier_samples_are_sanitized() -> None:
    assert sanitize_value("customer@example.com", "feedback") == "[TEXT_REDACTED:length=20]"
    assert sanitize_value("1234567890", "account_id") == "1234...7890"
    assert sanitize_value("https://example.com", "category") == "[URL_REDACTED]"


def test_raw_free_text_is_absent_from_artifact_payload() -> None:
    payload = {"text": "[TEXT_REDACTED:length=17]", "count": 1}
    assert ensure_no_raw_text(payload, ["private feedback"])
    assert not ensure_no_raw_text({"text": "private feedback"}, ["private feedback"])


def test_profiling_is_idempotent() -> None:
    frame = pd.DataFrame(
        {
            "entity_id": ["a", "b"],
            "event_date": ["2025-01-01", "2025-01-02"],
            "value": [1, 2],
        }
    )
    first = profile_dataframe("example", frame)
    second = profile_dataframe("example", frame)
    assert first == second


def test_cross_table_target_consistency_is_detected() -> None:
    frames = {
        "accounts": pd.DataFrame(
            {"account_id": ["a", "b"], "churn_flag": [False, True]}
        ),
        "subscriptions": pd.DataFrame(
            {
                "churn_flag": [False],
                "end_date": [None],
                "arr_amount": [120],
                "mrr_amount": [10],
            }
        ),
        "feature_usage": pd.DataFrame(
            {
                "usage_id": ["u", "u"],
                "subscription_id": ["s", "s"],
                "usage_date": ["2025-01-01", "2025-01-01"],
                "feature_name": ["f", "f"],
            }
        ),
        "support_tickets": pd.DataFrame(
            {
                "submitted_at": ["2025-01-01"],
                "closed_at": ["2025-01-01 01:00:00"],
                "resolution_time_hours": [1.0],
                "satisfaction_score": [5.0],
            }
        ),
        "churn_events": pd.DataFrame({"account_id": ["a"]}),
    }
    checks = {
        item["check"]: item for item in run_consistency_audit(frames)["checks"]
    }
    assert checks["account_churn_flag_false_with_churn_event"]["occurrence_count"] == 1
    assert checks["account_churn_flag_true_without_churn_event"]["occurrence_count"] == 1
    assert checks["usage_id_duplicate_excess_rows"]["occurrence_count"] == 1
