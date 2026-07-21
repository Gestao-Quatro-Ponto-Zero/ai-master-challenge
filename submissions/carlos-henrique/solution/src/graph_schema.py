"""Governed JourneyGraph labels, relationships, properties, and identifiers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


PUBLIC_NAMESPACE_SALT = "ai-master-challenge::carlos-henrique::journeygraph::v1"

NODE_LABELS = (
    "Account", "Journey", "EventInstance", "EventType", "Pattern", "Outcome",
    "Taxonomy", "QualityProfile", "Finding", "Investigation",
)

RELATIONSHIP_TYPES = (
    "HAS_JOURNEY", "HAS_EVENT", "OF_TYPE", "NEXT_EVENT", "CLASSIFIED_AS",
    "ASSOCIATED_WITH_OUTCOME", "HAS_QUALITY_PROFILE", "MATCHES_PATTERN",
    "CONTAINS_EVENT_TYPE", "OBSERVED_BEFORE", "OBSERVED_AFTER", "ASSOCIATED_WITH",
    "SUPPORTED_BY", "RECOMMENDS_INVESTIGATION", "TRANSITIONS_TO",
)

FORBIDDEN_CAUSAL_TERMS = (
    "CAUSES", "CAUSE", "LEADS_TO", "RESULTS_IN", "PREVENTS", "DRIVES",
    "DETERMINES", "TRIGGERS_CHURN", "SAVES_REVENUE", "REVENUE_LOST",
    "REVENUE_SAVED", "PREVENTABLE_REVENUE",
)

FORBIDDEN_PII_PROPERTIES = (
    "account_id", "account_name", "email", "feedback", "feedback_text",
    "source_event_id", "source_record_id", "subscription_id",
)

EVENT_TYPES = (
    "ACCOUNT", "SUBSCRIPTION_START", "SUBSCRIPTION_END", "FEATURE",
    "SUPPORT_OPEN", "SUPPORT_CLOSE", "CHURN", "REACTIVATION",
)

OUTCOMES = (
    "NO_CHURN_OBSERVED", "SINGLE_CHURN", "RECURRING_CHURN", "REACTIVATED",
    "REACTIVATED_THEN_CHURNED_AGAIN", "CHURNED_NOT_REACTIVATED",
)

INVESTIGATIONS = (
    "REVIEW_DATA_QUALITY", "VALIDATE_SUBSCRIPTION_OVERLAP",
    "INVESTIGATE_PRODUCT_ADOPTION", "REVIEW_SUPPORT_JOURNEY",
    "VALIDATE_REACTIVATION_PATH", "REVIEW_HIGH_MRR_LOW_USAGE",
    "VALIDATE_PATTERN_IN_NEW_COHORT",
)

NODE_SCHEMAS: dict[str, tuple[str, ...]] = {
    "Account": ("account_key", "primary_outcome", "mrr_band", "associated_mrr", "quality_population", "quality_coverage_ratio", "journey_count", "event_count", "taxonomy_class", "is_anonymized"),
    "Journey": ("journey_key", "journey_scope", "quality_population", "journey_start", "journey_end", "raw_length", "collapsed_length", "distinct_event_types", "observed_days", "same_day_order_dependency", "contains_churn", "contains_reactivation", "quality_coverage_ratio", "stability_status", "journey_length_band"),
    "EventInstance": ("event_instance_key", "event_type", "event_time", "event_position", "same_day_order", "quality_status", "source_table", "journey_scope", "is_warning", "is_endpoint_event"),
    "EventType": ("event_type",),
    "Pattern": ("pattern_key", "pattern_family_key", "pattern", "pattern_type", "pattern_length", "journey_scope", "outcome_context", "quality_population", "account_support", "denominator_accounts", "relative_support", "confidence", "lift", "coverage", "leverage", "discriminative_ratio", "principal_support", "strict_support", "stability_status", "same_day_dependency", "small_sample", "exposure_control", "is_promotable", "associated_mrr", "median_mrr", "mean_mrr", "mrr_account_count"),
    "Outcome": ("outcome", "associated_mrr", "median_mrr", "mean_mrr", "mrr_account_count"),
    "Taxonomy": ("taxonomy_id", "name", "definition", "associated_mrr", "median_mrr", "mean_mrr", "mrr_account_count"),
    "QualityProfile": ("quality_profile_key", "population", "stability_status", "same_day_dependency", "small_sample", "warning_dependency_ratio_band", "coverage_band", "confidence_level", "limitations_count"),
    "Finding": ("finding_id", "title", "confidence_level", "stability_status", "business_relevance", "recommended_investigation", "is_causal"),
    "Investigation": ("investigation_type", "is_automatic", "requires_human_review"),
}

EDGE_SCHEMAS: dict[str, tuple[str, ...]] = {
    "TRANSITIONS_TO": ("journey_scope", "outcome", "account_support", "transition_count", "denominator_accounts", "relative_support", "source_conditional_probability", "lift", "principal_support", "strict_support", "stability_status", "same_day_dependency", "small_sample", "is_promotable", "associated_mrr", "median_mrr", "mean_mrr", "mrr_account_count"),
    "NEXT_EVENT": ("event_position", "elapsed_days", "same_day", "journey_scope"),
}


def stable_key(namespace: str, *parts: object, length: int = 16) -> str:
    """Create a deterministic namespaced public key with no reversible mapping."""
    payload = "|".join([PUBLIC_NAMESPACE_SALT, namespace, *(str(part) for part in parts)])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]
    return f"{namespace}_{digest}"


def simple_value(value: Any) -> str | int | float | bool:
    """Coerce values to GraphML-safe primitives; serialize collections stably."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return 0.0 if value != value else value
    if isinstance(value, (list, tuple, dict, set)):
        serializable = sorted(value) if isinstance(value, set) else value
        return json.dumps(serializable, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return str(value)


def graph_schema_artifact() -> dict[str, Any]:
    return {
        "schema_version": "6.0.0",
        "identifier_policy": {
            "algorithm": "SHA256_TRUNCATED_16",
            "salt": PUBLIC_NAMESPACE_SALT,
            "purpose": "PUBLIC_NON_SECRET_NAMESPACING",
            "reverse_mapping_versioned": False,
        },
        "node_labels": list(NODE_LABELS),
        "relationship_types": list(RELATIONSHIP_TYPES),
        "node_schemas": {key: list(value) for key, value in NODE_SCHEMAS.items()},
        "edge_schemas": {key: list(value) for key, value in EDGE_SCHEMAS.items()},
        "forbidden_causal_terms": list(FORBIDDEN_CAUSAL_TERMS),
        "forbidden_pii_properties": list(FORBIDDEN_PII_PROPERTIES),
        "graphml_value_types": ["string", "integer", "float", "boolean"],
    }
