"""Reusable, privacy-preserving quality checks for RavenStack source data."""

from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
URL_PATTERN = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)
DATE_NAME_PATTERN = re.compile(
    r"(?:^|_)(?:date|datetime|timestamp|at)$", re.IGNORECASE
)
TEXT_NAME_PATTERN = re.compile(
    r"(?:account_name|feedback|description|subject|comment|text|reason_details?)",
    re.IGNORECASE,
)
ID_NAME_PATTERN = re.compile(r"(?:^|_)id$", re.IGNORECASE)
SENTINEL_STRINGS = {"", "unknown", "n/a", "na", "null", "none", "-1", "999", "9999"}


def compute_sha256(path: Path | str, chunk_size: int = 1024 * 1024) -> str:
    """Calculate a deterministic SHA-256 digest without loading the file at once."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_physical_lines(path: Path | str, chunk_size: int = 1024 * 1024) -> int:
    """Count physical lines while remaining agnostic to logical CSV records."""

    line_breaks = 0
    last_byte = b""
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            line_breaks += chunk.count(b"\n")
            last_byte = chunk[-1:]
    return line_breaks + int(bool(last_byte) and last_byte != b"\n")


def mask_identifier(value: object) -> str:
    """Partially mask a technical identifier for safe diagnostics."""

    text = str(value)
    if len(text) <= 8:
        return "***"
    return f"{text[:4]}...{text[-4:]}"


def sanitize_value(value: object, column: str = "") -> object:
    """Sanitize a scalar without reproducing free text or personal identifiers."""

    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return None
    if isinstance(value, (bool, int, float, np.integer, np.floating)):
        return value.item() if hasattr(value, "item") else value

    text = str(value)
    if ID_NAME_PATTERN.search(column):
        return mask_identifier(text)
    if TEXT_NAME_PATTERN.search(column):
        return f"[TEXT_REDACTED:length={len(text)}]"
    sanitized = EMAIL_PATTERN.sub("[EMAIL_REDACTED]", text)
    sanitized = PHONE_PATTERN.sub("[PHONE_REDACTED]", sanitized)
    sanitized = URL_PATTERN.sub("[URL_REDACTED]", sanitized)
    return sanitized[:80]


def sanitized_samples(series: pd.Series, column: str, limit: int = 3) -> list[object]:
    """Return bounded, de-duplicated samples after applying sanitization."""

    samples: list[object] = []
    seen: set[str] = set()
    for value in series.dropna():
        safe = sanitize_value(value, column)
        marker = repr(safe)
        if marker not in seen:
            samples.append(safe)
            seen.add(marker)
        if len(samples) >= limit:
            break
    return samples


def cardinality_class(series: pd.Series) -> str:
    """Classify observed cardinality at the current snapshot grain."""

    rows = len(series)
    unique = int(series.nunique(dropna=True))
    if rows == 0:
        return "EMPTY"
    if unique <= 1:
        return "CONSTANT"
    if unique == rows and not series.isna().any():
        return "UNIQUE"
    ratio = unique / rows
    if ratio <= 0.01:
        return "LOW"
    if ratio <= 0.10:
        return "MEDIUM"
    return "HIGH"


def audit_key(frame: pd.DataFrame, columns: str | Sequence[str]) -> dict[str, object]:
    """Assess completeness and uniqueness of a candidate key."""

    key_columns = [columns] if isinstance(columns, str) else list(columns)
    missing_columns = [column for column in key_columns if column not in frame.columns]
    if missing_columns:
        return {
            "columns": key_columns,
            "status": "INVALID",
            "missing_columns": missing_columns,
        }

    key_frame = frame[key_columns]
    null_rows = int(key_frame.isna().any(axis=1).sum())
    duplicate_affected_rows = int(key_frame.duplicated(keep=False).sum())
    duplicate_excess_rows = int(key_frame.duplicated(keep="first").sum())
    unique_non_null = int(key_frame.dropna().drop_duplicates().shape[0])
    complete_and_unique = null_rows == 0 and duplicate_excess_rows == 0
    return {
        "columns": key_columns,
        "rows": int(len(frame)),
        "null_rows": null_rows,
        "unique_non_null_values": unique_non_null,
        "duplicate_affected_rows": duplicate_affected_rows,
        "duplicate_excess_rows": duplicate_excess_rows,
        "complete_and_unique_in_snapshot": complete_and_unique,
        "status": "CANDIDATE" if complete_and_unique else "INVALID",
        "stability_note": "Cross-snapshot stability requires source governance evidence.",
    }


def parse_datetime_series(series: pd.Series) -> pd.Series:
    """Parse a temporal series explicitly and retain invalid values as NaT."""

    return pd.to_datetime(series, errors="coerce", utc=True, format="mixed")


def audit_temporal_column(series: pd.Series, column: str) -> dict[str, object]:
    """Profile validity, range, timezone evidence, and granularity of a date field."""

    non_null = series.dropna()
    parsed = parse_datetime_series(series)
    invalid = int(non_null.shape[0] - parsed.notna().sum())
    text = non_null.astype(str)
    date_only_share = float(text.str.fullmatch(r"\d{4}-\d{2}-\d{2}").mean()) if len(text) else 0.0
    timezone_share = (
        float(text.str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", regex=True).mean())
        if len(text)
        else 0.0
    )
    now = pd.Timestamp.now(tz="UTC")
    plausible_start = pd.Timestamp("2000-01-01", tz="UTC")
    minimum = parsed.min()
    maximum = parsed.max()
    return {
        "column": column,
        "non_null": int(non_null.shape[0]),
        "missing_count": int(series.isna().sum()),
        "missing_rate": round(float(series.isna().mean()), 6),
        "invalid_count": invalid,
        "invalid_rate_non_null": round(invalid / len(non_null), 6) if len(non_null) else 0.0,
        "minimum": minimum.isoformat() if pd.notna(minimum) else None,
        "maximum": maximum.isoformat() if pd.notna(maximum) else None,
        "future_suspect_count": int((parsed > now).sum()),
        "pre_2000_suspect_count": int((parsed < plausible_start).sum()),
        "predominant_format": "YYYY-MM-DD" if date_only_share >= 0.8 else "DATETIME_OR_MIXED",
        "timezone": "EXPLICIT_OFFSET_OR_UTC" if timezone_share >= 0.8 else "NOT_DECLARED",
        "granularity": "DATE" if date_only_share >= 0.8 else "DATETIME",
    }


def classify_leakage(table: str, column: str) -> dict[str, str]:
    """Classify pre-outcome feature risk without removing any source column."""

    lowered = column.lower()
    explicit = {
        "churn_flag",
        "churn_date",
        "reason_code",
        "refund_amount_usd",
        "feedback_text",
        "is_reactivation",
        "churn_event_id",
        "preceding_upgrade_flag",
        "preceding_downgrade_flag",
    }
    proxy = {"end_date"}
    temporal = {
        "usage_date",
        "submitted_at",
        "closed_at",
        "start_date",
        "signup_date",
    }
    support_post_interaction = {
        "closed_at",
        "resolution_time_hours",
        "first_response_time_minutes",
        "satisfaction_score",
        "escalation_flag",
    }

    if table == "churn_events" and lowered != "account_id":
        risk = "EXPLICIT"
        reason = "The field belongs to the outcome event and is unavailable before churn."
    elif lowered in explicit:
        risk = "EXPLICIT"
        reason = "The field directly encodes the outcome or cancellation-time information."
    elif lowered in proxy:
        risk = "PROXY"
        reason = "Population or value may directly encode termination state."
    elif lowered in temporal or (
        table == "support_tickets" and lowered in support_post_interaction
    ):
        risk = "TEMPORAL"
        reason = "Safe use requires an explicit as-of cutoff before the prediction time."
    else:
        risk = "NONE_IDENTIFIED"
        reason = "No direct structural leakage signal was identified; temporal validation still applies."

    return {
        "risk": risk,
        "reason": reason,
        "allowed_use": "Audit, reconciliation, and retrospective description.",
        "prohibited_use": (
            "Pre-churn predictive feature without cutoff controls."
            if risk != "NONE_IDENTIFIED"
            else "No blanket prohibition; use remains subject to feature-time validation."
        ),
        "decision": "VALIDATED_WITH_WARNINGS" if risk != "NONE_IDENTIFIED" else "VALIDATED",
    }


def text_privacy_profile(series: pd.Series) -> dict[str, object]:
    """Measure privacy patterns with regex and aggregate counts only."""

    text = series.dropna().astype(str)
    lengths = text.str.len()
    stripped = text.str.strip()
    return {
        "non_null_count": int(len(text)),
        "missing_count": int(series.isna().sum()),
        "missing_rate": round(float(series.isna().mean()), 6),
        "average_length": round(float(lengths.mean()), 3) if len(lengths) else 0.0,
        "maximum_length": int(lengths.max()) if len(lengths) else 0,
        "empty_or_whitespace_count": int(stripped.eq("").sum()),
        "possible_email_count": int(text.str.contains(EMAIL_PATTERN, regex=True).sum()),
        "possible_phone_count": int(text.str.contains(PHONE_PATTERN, regex=True).sum()),
        "possible_url_count": int(text.str.contains(URL_PATTERN, regex=True).sum()),
        "raw_text_included": False,
    }


def _json_number(value: object) -> int | float | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        numeric = float(value)
        return numeric if math.isfinite(numeric) else None
    return None


def profile_dataframe(
    table: str,
    frame: pd.DataFrame,
    *,
    file_name: str | None = None,
    file_metadata: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build a deterministic structural profile without exposing raw free text."""

    rows = len(frame)
    column_profiles: dict[str, dict[str, object]] = {}
    constant_columns: list[str] = []
    near_constant_columns: list[str] = []
    temporal_columns: dict[str, dict[str, object]] = {}
    text_columns: dict[str, dict[str, object]] = {}
    negative_values: dict[str, int] = {}

    for column in frame.columns:
        series = frame[column]
        missing_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))
        non_null_count = int(series.notna().sum())
        empty_count = 0
        whitespace_count = 0
        sentinel_count = 0
        inconsistent_id_count = 0

        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            text = series.dropna().astype(str)
            stripped = text.str.strip()
            empty_count = int(stripped.eq("").sum())
            whitespace_count = int(text.ne(stripped).sum())
            sentinel_count = int(stripped.str.lower().isin(SENTINEL_STRINGS).sum())
            if ID_NAME_PATTERN.search(str(column)):
                inconsistent_id_count = int(
                    (~stripped.str.fullmatch(r"[A-Za-z0-9_-]+", na=False)).sum()
                    + text.ne(stripped).sum()
                )
        elif pd.api.types.is_numeric_dtype(series):
            sentinel_count = int(series.isin([-1, 999, 9999]).sum())
            negative_values[str(column)] = int((series < 0).sum())

        if unique_count <= 1:
            constant_columns.append(str(column))
        elif non_null_count and int(series.value_counts(dropna=True).iloc[0]) / non_null_count >= 0.95:
            near_constant_columns.append(str(column))

        profile = {
            "dtype_inferred": str(series.dtype),
            "missing_count": missing_count,
            "missing_rate": round(missing_count / rows, 6) if rows else 0.0,
            "non_null_count": non_null_count,
            "unique_count": unique_count,
            "unique_rate": round(unique_count / rows, 6) if rows else 0.0,
            "cardinality": cardinality_class(series),
            "empty_string_count": empty_count,
            "leading_or_trailing_space_count": whitespace_count,
            "possible_inconsistent_id_count": inconsistent_id_count,
            "possible_sentinel_count": sentinel_count,
            "sanitized_samples": sanitized_samples(series, str(column)),
        }

        if pd.api.types.is_numeric_dtype(series):
            profile["minimum"] = _json_number(series.min())
            profile["maximum"] = _json_number(series.max())
            profile["negative_count"] = negative_values[str(column)]

        if DATE_NAME_PATTERN.search(str(column)):
            temporal_columns[str(column)] = audit_temporal_column(series, str(column))
        if TEXT_NAME_PATTERN.search(str(column)):
            text_columns[str(column)] = text_privacy_profile(series)

        column_profiles[str(column)] = profile

    candidate_keys = {
        str(column): audit_key(frame, str(column))
        for column in frame.columns
        if ID_NAME_PATTERN.search(str(column))
    }

    composite_candidates: dict[str, dict[str, object]] = {}
    if table == "feature_usage" and {
        "subscription_id",
        "usage_date",
        "feature_name",
    }.issubset(frame.columns):
        columns = ["subscription_id", "usage_date", "feature_name"]
        composite_candidates["subscription_id+usage_date+feature_name"] = audit_key(
            frame, columns
        )

    payload: dict[str, object] = {
        "table": table,
        "file_name": file_name,
        "records": int(rows),
        "column_count": int(len(frame.columns)),
        "columns": [str(column) for column in frame.columns],
        "dtypes_inferred": {str(column): str(dtype) for column, dtype in frame.dtypes.items()},
        "exact_duplicate_rows": int(frame.duplicated().sum()),
        "constant_columns": sorted(constant_columns),
        "near_constant_columns": sorted(near_constant_columns),
        "candidate_keys": candidate_keys,
        "candidate_composite_keys": composite_candidates,
        "temporal_columns": temporal_columns,
        "text_privacy": text_columns,
        "negative_numeric_values": negative_values,
        "column_profiles": column_profiles,
        "quality_observations": [],
    }
    if file_metadata:
        payload["file_metadata"] = dict(file_metadata)

    observations: list[str] = []
    if payload["exact_duplicate_rows"]:
        observations.append("Exact duplicate rows detected.")
    invalid_keys = [name for name, result in candidate_keys.items() if result["status"] == "INVALID"]
    if invalid_keys:
        observations.append("Non-unique or incomplete technical identifiers: " + ", ".join(invalid_keys))
    if any(column["invalid_count"] for column in temporal_columns.values()):
        observations.append("At least one candidate temporal field contains invalid values.")
    if any(profile["possible_email_count"] or profile["possible_phone_count"] for profile in text_columns.values()):
        observations.append("Text fields contain patterns requiring privacy controls.")
    payload["quality_observations"] = observations
    return payload


def detect_orphans(parent: pd.Series, child: pd.Series) -> dict[str, int]:
    """Count child keys that do not match a non-null parent key."""

    parent_values = set(parent.dropna().astype(str))
    child_text = child.dropna().astype(str)
    orphan_mask = ~child_text.isin(parent_values)
    return {
        "orphan_rows": int(orphan_mask.sum()),
        "orphan_unique_values": int(child_text[orphan_mask].nunique()),
    }


def calculate_match_rate(parent: pd.Series, child: pd.Series) -> float:
    """Calculate referential match coverage over non-null child rows."""

    parent_values = set(parent.dropna().astype(str))
    child_text = child.dropna().astype(str)
    if child_text.empty:
        return 1.0
    return float(child_text.isin(parent_values).mean())


def audit_relationship(
    parent_table: str,
    parent_frame: pd.DataFrame,
    parent_column: str,
    child_table: str,
    child_frame: pd.DataFrame,
    child_column: str,
) -> dict[str, object]:
    """Audit a parent-to-child relation and its observed join shape."""

    if parent_column not in parent_frame or child_column not in child_frame:
        return {
            "source_table": parent_table,
            "source_column": parent_column,
            "target_table": child_table,
            "target_column": child_column,
            "status": "INVALID",
            "observation": "Required relationship column is missing.",
        }

    parent = parent_frame[parent_column]
    child = child_frame[child_column]
    parent_non_null = parent.dropna().astype(str)
    child_non_null = child.dropna().astype(str)
    parent_values = set(parent_non_null)
    child_values = set(child_non_null)
    matching_values = len(parent_values.intersection(child_values))
    orphan = detect_orphans(parent, child)
    match_rate = calculate_match_rate(parent, child)
    parent_unique = parent_non_null.nunique() == len(parent_non_null)
    child_unique = child_non_null.nunique() == len(child_non_null)
    parent_index = pd.Index(parent_non_null.drop_duplicates())
    children_per_parent = child_non_null.value_counts().reindex(parent_index, fill_value=0)


    if parent_unique and child_unique:
        cardinality = "ONE_TO_ONE"
    elif parent_unique and not child_unique:
        cardinality = "ONE_TO_MANY"
    elif not parent_unique and child_unique:
        cardinality = "MANY_TO_ONE"
    else:
        cardinality = "MANY_TO_MANY"

    if orphan["orphan_rows"]:
        status = "VALIDATED_WITH_WARNINGS"
        observation = "Child rows without a parent require investigation before integration."
    elif cardinality in {"ONE_TO_MANY", "MANY_TO_MANY"}:
        status = "UNSAFE_WITHOUT_AGGREGATION"
        observation = "Referential coverage is complete, but a raw join expands the parent grain."
    else:
        status = "VALIDATED"
        observation = "Referential coverage and observed cardinality are compatible with a direct join."

    return {
        "source_table": parent_table,
        "source_column": parent_column,
        "target_table": child_table,
        "target_column": child_column,
        "records_in_source": int(len(parent_frame)),
        "unique_values_in_source": int(parent_non_null.nunique()),
        "records_in_target": int(len(child_frame)),
        "unique_values_in_target": int(child_non_null.nunique()),
        "matching_values": int(matching_values),
        "orphan_values": int(orphan["orphan_unique_values"]),
        "orphan_rows": int(orphan["orphan_rows"]),
        "null_target_keys": int(child.isna().sum()),
        "match_rate": round(match_rate, 6),
        "observed_cardinality": cardinality,
        "children_per_source_minimum": int(children_per_parent.min()),
        "children_per_source_median": round(float(children_per_parent.median()), 6),
        "children_per_source_mean": round(float(children_per_parent.mean()), 6),
        "children_per_source_maximum": int(children_per_parent.max()),
        "source_values_without_children": int((children_per_parent == 0).sum()),
        "inflation_risk": "HIGH" if cardinality in {"ONE_TO_MANY", "MANY_TO_MANY"} else "LOW",
        "status": status,
        "observation": observation,
    }


def measure_join_inflation(
    parent_frame: pd.DataFrame,
    parent_key: str,
    child_frame: pd.DataFrame,
    child_key: str,
    *,
    label: str = "",
) -> dict[str, object]:
    """Simulate a bounded left join using only keys and report expansion."""

    left = parent_frame[[parent_key]].copy()
    right = child_frame[[child_key]].copy()
    joined = left.merge(right, how="left", left_on=parent_key, right_on=child_key)
    before_rows = len(left)
    after_rows = len(joined)
    multiplier = after_rows / before_rows if before_rows else 0.0
    source_unique_before = int(left[parent_key].nunique(dropna=True))
    source_unique_after = int(joined[parent_key].nunique(dropna=True))
    parent_duplicates = bool(left[parent_key].duplicated().any())
    child_duplicates = bool(right[child_key].duplicated().any())
    return {
        "join": label or f"{parent_key}->{child_key}",
        "grain_before": f"one row per {parent_key} as supplied",
        "rows_before": int(before_rows),
        "rows_after": int(after_rows),
        "multiplier": round(multiplier, 6),
        "unique_source_entities_before": source_unique_before,
        "unique_source_entities_after": source_unique_after,
        "unique_source_entities_preserved": source_unique_before == source_unique_after,
        "many_to_many_risk": bool(parent_duplicates and child_duplicates),
        "one_to_many_expansion": bool((not parent_duplicates) and child_duplicates),
        "recommended_strategy": (
            "Aggregate child events to the intended as-of grain before joining."
            if multiplier > 1.0
            else "Direct join is structurally safe at the observed snapshot grain."
        ),
    }


def count_chronology_violations(
    frame: pd.DataFrame, earlier_column: str, later_column: str
) -> int:
    """Count rows where a later event occurs before its required predecessor."""

    earlier = parse_datetime_series(frame[earlier_column])
    later = parse_datetime_series(frame[later_column])
    return int((later.notna() & earlier.notna() & (later < earlier)).sum())


def _temporal_check(
    check: str,
    count: int,
    classification: str,
    interpretation: str,
) -> dict[str, object]:
    return {
        "check": check,
        "occurrence_count": int(count),
        "classification": classification,
        "interpretation": interpretation,
    }


def run_temporal_audit(frames: Mapping[str, pd.DataFrame]) -> dict[str, object]:
    """Run cross-table temporal checks without building a consolidated event log."""

    accounts = frames["accounts"]
    subscriptions = frames["subscriptions"]
    usage = frames["feature_usage"]
    tickets = frames["support_tickets"]
    churn = frames["churn_events"]

    columns: dict[str, dict[str, object]] = {}
    for table, frame in frames.items():
        for column in frame.columns:
            if DATE_NAME_PATTERN.search(str(column)):
                columns[f"{table}.{column}"] = audit_temporal_column(frame[column], str(column))

    a = accounts[["account_id", "signup_date"]].copy()
    a["signup_ts"] = parse_datetime_series(a["signup_date"])
    s = subscriptions[["subscription_id", "account_id", "start_date", "end_date"]].copy()
    s["start_ts"] = parse_datetime_series(s["start_date"])
    s["end_ts"] = parse_datetime_series(s["end_date"])
    u = usage[["subscription_id", "usage_date"]].copy()
    u["usage_ts"] = parse_datetime_series(u["usage_date"])
    t = tickets[["account_id", "submitted_at", "closed_at"]].copy()
    t["submitted_ts"] = parse_datetime_series(t["submitted_at"])
    t["closed_ts"] = parse_datetime_series(t["closed_at"])
    c = churn[["account_id", "churn_date"]].copy()
    c["churn_ts"] = parse_datetime_series(c["churn_date"])

    checks: list[dict[str, object]] = []

    subscription_account = s.merge(a[["account_id", "signup_ts"]], on="account_id", how="left")
    checks.append(
        _temporal_check(
            "subscription_before_account_signup",
            int((subscription_account["start_ts"] < subscription_account["signup_ts"]).sum()),
            "CONFIRMED_ERROR",
            "Subscription start must not precede account creation.",
        )
    )
    checks.append(
        _temporal_check(
            "subscription_end_before_start",
            int((s["end_ts"].notna() & (s["end_ts"] < s["start_ts"])).sum()),
            "CONFIRMED_ERROR",
            "A subscription end before its start is chronologically impossible.",
        )
    )

    usage_subscription = u.merge(
        s[["subscription_id", "start_ts", "end_ts"]], on="subscription_id", how="left"
    )
    checks.append(
        _temporal_check(
            "usage_before_subscription_start",
            int((usage_subscription["usage_ts"] < usage_subscription["start_ts"]).sum()),
            "CONFIRMED_ERROR",
            "Usage before subscription start cannot enter the event log without remediation.",
        )
    )
    checks.append(
        _temporal_check(
            "usage_after_subscription_end",
            int(
                (
                    usage_subscription["end_ts"].notna()
                    & (usage_subscription["usage_ts"] > usage_subscription["end_ts"])
                ).sum()
            ),
            "SUSPICIOUS_OCCURRENCE",
            "May reflect late events, wrong assignment, or an invalid subscription window.",
        )
    )

    ticket_account = t.merge(a[["account_id", "signup_ts"]], on="account_id", how="left")
    checks.append(
        _temporal_check(
            "ticket_before_account_signup",
            int((ticket_account["submitted_ts"] < ticket_account["signup_ts"]).sum()),
            "CONFIRMED_ERROR",
            "Ticket submission must not precede account creation.",
        )
    )
    checks.append(
        _temporal_check(
            "ticket_closed_before_submitted",
            int((t["closed_ts"] < t["submitted_ts"]).sum()),
            "CONFIRMED_ERROR",
            "Ticket close must not precede submission.",
        )
    )

    churn_account = c.merge(a[["account_id", "signup_ts"]], on="account_id", how="left")
    checks.append(
        _temporal_check(
            "churn_before_account_signup",
            int((churn_account["churn_ts"] < churn_account["signup_ts"]).sum()),
            "CONFIRMED_ERROR",
            "Churn must not precede account creation.",
        )
    )

    first_start = s.groupby("account_id", dropna=False)["start_ts"].min()
    churn_first_start = c.join(first_start, on="account_id")
    checks.append(
        _temporal_check(
            "churn_before_first_subscription",
            int((churn_first_start["churn_ts"] < churn_first_start["start_ts"]).sum()),
            "CONFIRMED_ERROR",
            "Churn before the first subscription lacks a valid subscription lifecycle.",
        )
    )

    active_match_count = 0
    churn_without_any_subscription = 0
    churn_after_all_subscription_ends = 0
    for account_id, churn_ts in c[["account_id", "churn_ts"]].itertuples(index=False):
        account_subscriptions = s[s["account_id"] == account_id]
        if account_subscriptions.empty:
            churn_without_any_subscription += 1
            continue
        active = (
            (account_subscriptions["start_ts"] <= churn_ts)
            & (account_subscriptions["end_ts"].isna() | (account_subscriptions["end_ts"] >= churn_ts))
        )
        active_match_count += int(active.any())
        all_ended = account_subscriptions["end_ts"].notna().all() and (
            account_subscriptions["end_ts"] < churn_ts
        ).all()
        churn_after_all_subscription_ends += int(all_ended)
    checks.append(
        _temporal_check(
            "churn_without_active_subscription",
            int(len(c) - active_match_count),
            "SUSPICIOUS_OCCURRENCE",
            "Requires lifecycle rules for multiple subscriptions before event-log construction.",
        )
    )
    checks.append(
        _temporal_check(
            "churn_without_any_subscription",
            churn_without_any_subscription,
            "CONFIRMED_ERROR",
            "A churn event without any subscription cannot be placed in a subscription lifecycle.",
        )
    )
    checks.append(
        _temporal_check(
            "churn_after_all_subscription_ends",
            churn_after_all_subscription_ends,
            "SUSPICIOUS_OCCURRENCE",
            "May reflect delayed churn registration or an incomplete subscription history.",
        )
    )

    first_churn = c.groupby("account_id", dropna=False)["churn_ts"].min()
    ticket_churn = t.join(first_churn, on="account_id")
    checks.append(
        _temporal_check(
            "ticket_after_first_churn",
            int(
                (
                    ticket_churn["churn_ts"].notna()
                    & (ticket_churn["submitted_ts"] > ticket_churn["churn_ts"])
                ).sum()
            ),
            "POSSIBLE_BEHAVIOR",
            "May be post-cancellation support, delayed entry, reactivation, or another subscription.",
        )
    )

    subscription_churn = s.join(first_churn, on="account_id")
    subscriptions_after_churn = int(
        (
            subscription_churn["churn_ts"].notna()
            & (subscription_churn["start_ts"] > subscription_churn["churn_ts"])
        ).sum()
    )
    checks.append(
        _temporal_check(
            "subscription_started_after_prior_churn",
            subscriptions_after_churn,
            "POSSIBLE_BEHAVIOR",
            "Supports a reactivation hypothesis but does not define reactivation by itself.",
        )
    )
    checks.append(
        _temporal_check(
            "open_subscription_on_churned_account",
            int((subscription_churn["churn_ts"].notna() & subscription_churn["end_ts"].isna()).sum()),
            "SUSPICIOUS_OCCURRENCE",
            "May represent parallel subscriptions, reactivation, or incomplete closure fields.",
        )
    )

    simultaneous = {
        "feature_usage_same_subscription_date": int(
            usage.duplicated(["subscription_id", "usage_date"], keep=False).sum()
        ),
        "support_tickets_same_account_timestamp": int(
            tickets.duplicated(["account_id", "submitted_at"], keep=False).sum()
        ),
        "churn_events_same_account_date": int(
            churn.duplicated(["account_id", "churn_date"], keep=False).sum()
        ),
    }

    churn_counts = churn.groupby("account_id").size()
    account_ids = set(accounts["account_id"].astype(str))
    accounts_with_churn = set(churn_counts.index.astype(str))
    recurrence = {
        "accounts_with_zero_churn_events": int(len(account_ids - accounts_with_churn)),
        "accounts_with_one_churn_event": int((churn_counts == 1).sum()),
        "accounts_with_multiple_churn_events": int((churn_counts > 1).sum()),
        "maximum_churn_events_per_account": int(churn_counts.max()) if len(churn_counts) else 0,
        "explicit_reactivation_events": (
            int(churn["is_reactivation"].fillna(False).astype(bool).sum())
            if "is_reactivation" in churn
            else 0
        ),
        "subscriptions_started_after_prior_churn": subscriptions_after_churn,
        "reactivation_classification": (
            "EXPLICIT" if "is_reactivation" in churn.columns else "INFERABLE"
        ),
        "final_rule_status": "DECISION_PENDING_PHASE_2",
    }

    accounts_with_usage = set(
        subscriptions.loc[
            subscriptions["subscription_id"].isin(set(usage["subscription_id"])), "account_id"
        ].astype(str)
    )
    accounts_with_ticket = set(tickets["account_id"].astype(str))
    accounts_with_any_activity = accounts_with_usage | accounts_with_ticket | accounts_with_churn
    recurrence["accounts_without_usage_ticket_or_churn"] = int(
        len(account_ids - accounts_with_any_activity)
    )

    denominators = {
        "subscription_before_account_signup": len(s),
        "subscription_end_before_start": int(s["end_ts"].notna().sum()),
        "usage_before_subscription_start": len(u),
        "usage_after_subscription_end": len(u),
        "ticket_before_account_signup": len(t),
        "ticket_closed_before_submitted": len(t),
        "churn_before_account_signup": len(c),
        "churn_before_first_subscription": len(c),
        "churn_without_active_subscription": len(c),
        "churn_without_any_subscription": len(c),
        "churn_after_all_subscription_ends": len(c),
        "ticket_after_first_churn": int(ticket_churn["churn_ts"].notna().sum()),
        "subscription_started_after_prior_churn": int(
            subscription_churn["churn_ts"].notna().sum()
        ),
        "open_subscription_on_churned_account": int(
            subscription_churn["churn_ts"].notna().sum()
        ),
    }
    for check in checks:
        evaluated = int(denominators[check["check"]])
        check["evaluated_records"] = evaluated
        check["occurrence_rate"] = round(
            check["occurrence_count"] / evaluated, 6
        ) if evaluated else 0.0

    return {
        "temporal_columns": columns,
        "cross_table_checks": checks,
        "simultaneous_event_rows": simultaneous,
        "churn_recurrence_and_reactivation": recurrence,
    }


def run_consistency_audit(frames: Mapping[str, pd.DataFrame]) -> dict[str, object]:
    """Audit stable cross-field rules and target consistency using aggregate counts."""

    accounts = frames["accounts"]
    subscriptions = frames["subscriptions"]
    usage = frames["feature_usage"]
    tickets = frames["support_tickets"]
    churn = frames["churn_events"]
    checks: list[dict[str, object]] = []

    def add_check(
        check: str,
        count: int,
        evaluated: int,
        severity: str,
        interpretation: str,
    ) -> None:
        checks.append(
            {
                "check": check,
                "occurrence_count": int(count),
                "evaluated_records": int(evaluated),
                "occurrence_rate": round(count / evaluated, 6) if evaluated else 0.0,
                "severity": severity,
                "status": "PASS" if count == 0 else "WARNING",
                "interpretation": interpretation,
            }
        )

    churn_accounts = set(churn["account_id"].dropna().astype(str))
    account_has_churn_event = accounts["account_id"].astype(str).isin(churn_accounts)
    account_churn_flag = accounts["churn_flag"].fillna(False).astype(bool)
    add_check(
        "account_churn_flag_false_with_churn_event",
        int((~account_churn_flag & account_has_churn_event).sum()),
        len(accounts),
        "HIGH",
        "The account-level snapshot flag conflicts with the churn event table.",
    )
    add_check(
        "account_churn_flag_true_without_churn_event",
        int((account_churn_flag & ~account_has_churn_event).sum()),
        len(accounts),
        "HIGH",
        "The account-level target flag lacks a corresponding churn event.",
    )

    subscription_churn_flag = subscriptions["churn_flag"].fillna(False).astype(bool)
    add_check(
        "subscription_churn_true_without_end_date",
        int((subscription_churn_flag & subscriptions["end_date"].isna()).sum()),
        len(subscriptions),
        "HIGH",
        "A churned subscription is expected to have a termination date.",
    )
    add_check(
        "subscription_churn_false_with_end_date",
        int((~subscription_churn_flag & subscriptions["end_date"].notna()).sum()),
        len(subscriptions),
        "HIGH",
        "An ended subscription conflicts with a false churn flag in this schema.",
    )
    add_check(
        "arr_not_equal_to_mrr_times_twelve",
        int((subscriptions["arr_amount"] != subscriptions["mrr_amount"] * 12).sum()),
        len(subscriptions),
        "MEDIUM",
        "ARR and MRR require a documented reconciliation rule before financial use.",
    )

    submitted = parse_datetime_series(tickets["submitted_at"])
    closed = parse_datetime_series(tickets["closed_at"])
    calculated_resolution = (closed - submitted).dt.total_seconds() / 3600
    resolution_mismatch = (
        calculated_resolution.notna()
        & tickets["resolution_time_hours"].notna()
        & ((calculated_resolution - tickets["resolution_time_hours"]).abs() > 0.001)
    )
    add_check(
        "ticket_resolution_hours_mismatch",
        int(resolution_mismatch.sum()),
        len(tickets),
        "MEDIUM",
        "Stored resolution duration should reconcile with submitted and closed timestamps.",
    )
    satisfaction = tickets["satisfaction_score"].dropna()
    add_check(
        "satisfaction_score_outside_1_to_5",
        int((~satisfaction.between(1, 5)).sum()),
        len(satisfaction),
        "HIGH",
        "Non-null satisfaction scores must remain in the documented 1-to-5 domain.",
    )

    add_check(
        "usage_id_duplicate_excess_rows",
        int(usage.duplicated(["usage_id"]).sum()),
        len(usage),
        "HIGH",
        "The supplied usage identifier is not a unique event key.",
    )
    add_check(
        "usage_business_composite_duplicate_excess_rows",
        int(usage.duplicated(["subscription_id", "usage_date", "feature_name"]).sum()),
        len(usage),
        "HIGH",
        "The tested subscription-date-feature composite is also not unique.",
    )

    numeric_frames = [frame.select_dtypes(include="number") for frame in frames.values()]
    negative_count = sum(int((frame < 0).sum().sum()) for frame in numeric_frames)
    numeric_cells = sum(int(frame.size) for frame in numeric_frames)
    add_check(
        "negative_numeric_values",
        negative_count,
        numeric_cells,
        "MEDIUM",
        "Negative values require domain-specific justification before analytical use.",
    )
    return {"checks": checks}


def build_schema_map(
    frames: Mapping[str, pd.DataFrame],
    profiles: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """Build an evidence-based schema map with candidate roles and risks."""

    tables: dict[str, list[dict[str, object]]] = {}
    for table, frame in frames.items():
        rows: list[dict[str, object]] = []
        key_profiles = profiles[table]["candidate_keys"]
        for column in frame.columns:
            name = str(column)
            is_key = bool(ID_NAME_PATTERN.search(name))
            is_temporal = bool(DATE_NAME_PATTERN.search(name))
            is_text = bool(TEXT_NAME_PATTERN.search(name))
            if is_key:
                role = "TECHNICAL_IDENTIFIER"
            elif is_temporal:
                role = "TEMPORAL_FIELD"
            elif is_text:
                role = "TEXT_OR_LABEL"
            elif pd.api.types.is_numeric_dtype(frame[column]):
                role = "NUMERIC_MEASURE"
            else:
                role = "CATEGORICAL_ATTRIBUTE"
            leakage = classify_leakage(table, name)
            key_status = key_profiles.get(name, {}).get("status") if is_key else None
            rows.append(
                {
                    "column": name,
                    "dtype_inferred": str(frame[column].dtype),
                    "candidate_role": role,
                    "candidate_key": key_status,
                    "temporal_field": is_temporal,
                    "text_field": is_text,
                    "leakage_risk": leakage["risk"],
                    "validation_status": (
                        "CANDIDATE"
                        if is_key or is_temporal
                        else leakage["decision"]
                    ),
                }
            )
        tables[table] = rows
    return {"tables": tables}


def build_raw_manifest(
    source_paths: Mapping[str, Path],
    load_metadata: Mapping[str, Mapping[str, object]],
    records: Mapping[str, int],
    *,
    relative_to: Path,
) -> dict[str, object]:
    """Build a deterministic manifest for raw, read-only inputs."""

    files: list[dict[str, object]] = []
    for table in sorted(source_paths):
        path = source_paths[table]
        stat = path.stat()
        metadata = load_metadata[table]
        files.append(
            {
                "table": table,
                "file": path.name,
                "relative_path": path.relative_to(relative_to).as_posix(),
                "bytes": int(stat.st_size),
                "sha256": compute_sha256(path),
                "modified_at_utc": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
                "encoding": metadata["encoding"],
                "delimiter": metadata["delimiter"],
                "physical_lines": count_physical_lines(path),
                "records_loaded": int(records[table]),
            }
        )
    return {"files": files}


def ensure_no_raw_text(payload: object, forbidden_values: Iterable[str]) -> bool:
    """Return True when no provided free-text value occurs in a serialized payload."""

    serialized = repr(payload)
    return not any(value and value in serialized for value in forbidden_values)
