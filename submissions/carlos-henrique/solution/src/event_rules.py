"""Canonical event types, ordering, quality flags, and deterministic identities."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Final, Iterable, Mapping

import pandas as pd


SCHEMA_VERSION: Final[str] = "2.0.0"
RULES_VERSION: Final[str] = "phase2-v1"
TIMEZONE_POLICY: Final[str] = "NAIVE_SOURCE_TIME"

QUALITY_VALID: Final[str] = "VALID"
QUALITY_WARNING: Final[str] = "VALID_WITH_WARNING"
QUALITY_QUARANTINED: Final[str] = "QUARANTINED"

DERIVATION_SOURCE: Final[str] = "SOURCE"
DERIVATION_DERIVED: Final[str] = "DERIVED"

EVENT_ORDER: Final[Mapping[str, int]] = {
    "ACCOUNT_CREATED": 1,
    "SUBSCRIPTION_STARTED": 2,
    "FEATURE_USED": 3,
    "SUPPORT_TICKET_OPENED": 4,
    "SUPPORT_TICKET_CLOSED": 5,
    "CHURN_RECORDED": 6,
    "REACTIVATION_RECORDED": 7,
    "SUBSCRIPTION_ENDED": 8,
}

QUALITY_FLAGS: Final[tuple[str, ...]] = (
    "MISSING_REQUIRED_ID",
    "INVALID_TIMESTAMP",
    "PRE_ACCOUNT_EVENT",
    "PRE_SUBSCRIPTION_USAGE",
    "POST_SUBSCRIPTION_USAGE",
    "END_BEFORE_START",
    "CLOSE_BEFORE_OPEN",
    "DUPLICATE_SOURCE_ID",
    "DUPLICATE_CANDIDATE_KEY",
    "EXACT_DUPLICATE",
    "MULTIPLE_ACTIVE_SUBSCRIPTIONS",
    "CHURN_WITHOUT_ACTIVE_SUBSCRIPTION",
    "CHURN_BEFORE_FIRST_SUBSCRIPTION",
    "POST_CHURN_EVENT",
    "OPEN_SUBSCRIPTION_AFTER_CHURN",
    "AMBIGUOUS_CHURN_SUBSCRIPTION",
    "REACTIVATION_WITHOUT_PRIOR_CHURN",
    "SAME_DAY_ORDER_ASSIGNED",
)

FATAL_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "MISSING_REQUIRED_ID",
        "INVALID_TIMESTAMP",
        "PRE_ACCOUNT_EVENT",
        "PRE_SUBSCRIPTION_USAGE",
        "POST_SUBSCRIPTION_USAGE",
        "END_BEFORE_START",
        "CLOSE_BEFORE_OPEN",
        "CHURN_BEFORE_FIRST_SUBSCRIPTION",
        "REACTIVATION_WITHOUT_PRIOR_CHURN",
    }
)

WARNING_FLAGS: Final[frozenset[str]] = frozenset(QUALITY_FLAGS) - FATAL_FLAGS - {
    "EXACT_DUPLICATE"
}

DUPLICATE_EXACT: Final[str] = "EXACT_DUPLICATE"
DUPLICATE_SOURCE_ID: Final[str] = "DUPLICATE_SOURCE_ID"
DUPLICATE_CANDIDATE_KEY: Final[str] = "DUPLICATE_CANDIDATE_KEY"
DUPLICATE_LEGITIMATE_REPEAT: Final[str] = "LEGITIMATE_REPEAT_EVENT"


@dataclass(frozen=True)
class EventDefinition:
    """Governed metadata for one event type."""

    name: str
    description: str
    source: str
    timestamp_field: str
    entity: str
    fields_used: tuple[str, ...]
    derivation_type: str
    leakage_risk: str
    allowed_use: str
    prohibited_use: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["fields_used"] = list(self.fields_used)
        return payload


EVENT_DEFINITIONS: Final[tuple[EventDefinition, ...]] = (
    EventDefinition(
        "ACCOUNT_CREATED",
        "Account creation observed at source signup date.",
        "accounts",
        "signup_date",
        "ACCOUNT",
        ("account_id", "signup_date"),
        DERIVATION_SOURCE,
        "LOW",
        "Journey anchoring and temporal validation.",
        "Do not enrich with account_name or snapshot churn_flag.",
    ),
    EventDefinition(
        "SUBSCRIPTION_STARTED",
        "Subscription episode start observed in the subscription source.",
        "subscriptions",
        "start_date",
        "SUBSCRIPTION",
        ("subscription_id", "account_id", "start_date", "plan_tier", "mrr_amount"),
        DERIVATION_SOURCE,
        "MEDIUM",
        "Episode construction and as-of journey ordering.",
        "Do not infer upgrade, downgrade, or churn from snapshot flags.",
    ),
    EventDefinition(
        "SUBSCRIPTION_ENDED",
        "Subscription end observed when a source end date exists.",
        "subscriptions",
        "end_date",
        "SUBSCRIPTION",
        ("subscription_id", "account_id", "end_date", "plan_tier"),
        DERIVATION_SOURCE,
        "HIGH_PROXY",
        "Outcome chronology after the end timestamp.",
        "Do not use as a pre-outcome feature without an as-of cutoff.",
    ),
    EventDefinition(
        "FEATURE_USED",
        "Feature usage record preserved at source grain.",
        "feature_usage",
        "usage_date",
        "SUBSCRIPTION",
        ("usage_id", "subscription_id", "usage_date", "feature_name", "usage_count"),
        DERIVATION_SOURCE,
        "TEMPORAL",
        "Usage sequencing after temporal-quality filtering.",
        "Do not use quarantined usage or collapse duplicate IDs silently.",
    ),
    EventDefinition(
        "SUPPORT_TICKET_OPENED",
        "Support ticket submission observed in the source.",
        "support_tickets",
        "submitted_at",
        "ACCOUNT",
        ("ticket_id", "account_id", "submitted_at", "priority"),
        DERIVATION_SOURCE,
        "TEMPORAL",
        "Support interaction sequencing after account creation.",
        "Do not attach response, satisfaction, or closure facts before available.",
    ),
    EventDefinition(
        "SUPPORT_TICKET_CLOSED",
        "Support ticket closure observed when a close timestamp exists.",
        "support_tickets",
        "closed_at",
        "ACCOUNT",
        ("ticket_id", "account_id", "closed_at", "satisfaction_score", "escalation_flag"),
        DERIVATION_SOURCE,
        "POST_INTERACTION",
        "Post-closure journey analysis with an as-of cutoff.",
        "Do not expose closure attributes before closed_at.",
    ),
    EventDefinition(
        "CHURN_RECORDED",
        "Explicit non-reactivation churn occurrence at account grain.",
        "churn_events",
        "churn_date",
        "ACCOUNT",
        ("churn_event_id", "account_id", "churn_date", "is_reactivation"),
        DERIVATION_SOURCE,
        "OUTCOME",
        "Outcome sequencing and recurrent-churn analysis.",
        "Do not use reason, refund, feedback, or the event itself before outcome.",
    ),
    EventDefinition(
        "REACTIVATION_RECORDED",
        "Explicit source-marked reactivation retained as a distinct account event.",
        "churn_events",
        "churn_date",
        "ACCOUNT",
        ("churn_event_id", "account_id", "churn_date", "is_reactivation"),
        DERIVATION_SOURCE,
        "OUTCOME_HISTORY",
        "Return-cycle reconstruction after a prior churn.",
        "Do not infer an unobserved subscription or erase prior churn.",
    ),
)


def event_dictionary() -> dict[str, object]:
    """Return deterministic, JSON-ready event governance metadata."""

    return {
        "schema_version": SCHEMA_VERSION,
        "rules_version": RULES_VERSION,
        "event_types": [definition.to_dict() for definition in EVENT_DEFINITIONS],
        "same_day_order": dict(EVENT_ORDER),
        "timezone_policy": TIMEZONE_POLICY,
    }


def normalize_scalar(value: object) -> str:
    """Normalize stable scalar inputs for deterministic hashes."""

    if value is None or pd.isna(value):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return str(value).strip()


def deterministic_id(prefix: str, *parts: object) -> str:
    """Create a stable SHA-256 identity without exposing raw composite values."""

    serialized = json.dumps(
        [normalize_scalar(part) for part in parts],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:32]}"


def event_id_for(
    *,
    source_table: str,
    source_record_id: object,
    source_row_number: int,
    event_type: str,
    event_time: object,
) -> str:
    """Create an event identity stable across repeated builds."""

    return deterministic_id(
        "evt",
        source_table,
        source_record_id,
        source_row_number,
        event_type,
        event_time,
    )


def episode_id_for(account_id: object, subscription_id: object) -> str:
    """Create a stable episode identity for a source subscription."""

    return deterministic_id("ep", account_id, subscription_id)


def serialize_flags(flags: Iterable[str]) -> str:
    """Serialize supported quality flags in deterministic order."""

    allowed = set(QUALITY_FLAGS)
    normalized = sorted({flag for flag in flags if flag in allowed})
    return "|".join(normalized)


def classify_quality(flags: Iterable[str]) -> str:
    """Map a set of flags to the canonical quality status."""

    normalized = set(flags)
    if normalized & FATAL_FLAGS:
        return QUALITY_QUARANTINED
    if normalized & WARNING_FLAGS:
        return QUALITY_WARNING
    return QUALITY_VALID


def event_order(event_type: str) -> int:
    """Return the non-causal technical tie-break order."""

    if event_type not in EVENT_ORDER:
        raise ValueError(f"Unsupported event type: {event_type}")
    return EVENT_ORDER[event_type]
