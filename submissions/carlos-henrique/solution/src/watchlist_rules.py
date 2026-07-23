"""Versioned deterministic rule engine for the governed intervention watchlist."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


QUEUES = (
    "DATA_QUALITY_REVIEW", "HIGH_MRR_LOW_ENGAGEMENT_REVIEW",
    "RECENT_CHURN_REVIEW", "RECURRING_CHURN_REVIEW", "REACTIVATION_REVIEW",
    "SUPPORT_JOURNEY_REVIEW", "ADOPTION_REVIEW",
)

REQUIRED_RULE_FIELDS = {
    "rule_id", "rule_name", "queue", "description", "enabled", "population",
    "reference_window_days", "required_conditions", "optional_conditions",
    "exclusion_conditions", "minimum_quality_coverage", "allowed_stability",
    "minimum_support", "minimum_group_size", "materiality_definition",
    "urgency_definition", "confidence_policy", "human_owner",
    "authorized_investigation", "prohibited_actions", "version",
}

OPERATORS = {"eq", "ne", "lt", "lte", "gt", "gte", "in", "not_in", "is_null", "not_null"}


def load_rule_config(path: Path) -> dict[str, Any]:
    """Load and validate a local JSON rule configuration."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_rule_config(payload)
    return payload


def validate_rule_config(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload.get("config_version"), str) or not payload.get("rules"):
        raise ValueError("Rule configuration requires config_version and rules.")
    ids: list[str] = []
    for rule in payload["rules"]:
        missing = REQUIRED_RULE_FIELDS - set(rule)
        if missing:
            raise ValueError(f"Rule {rule.get('rule_id')} missing fields: {sorted(missing)}")
        if rule["queue"] not in QUEUES:
            raise ValueError(f"Unknown queue: {rule['queue']}")
        if not str(rule["rule_id"]).startswith("W"):
            raise ValueError("Rule IDs must use the W namespace.")
        ids.append(rule["rule_id"])
        for group in ("required_conditions", "optional_conditions", "exclusion_conditions"):
            for condition in rule[group]:
                if set(condition) != {"field", "operator", "value"}:
                    raise ValueError(f"Invalid condition shape in {rule['rule_id']}")
                if condition["operator"] not in OPERATORS:
                    raise ValueError(f"Invalid operator in {rule['rule_id']}")
                if condition["field"] in {"account_name", "email", "feedback_text"}:
                    raise ValueError("Rules cannot depend on PII or free text.")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate rule IDs.")
    return {"rule_count": len(ids), "enabled_count": sum(bool(rule["enabled"]) for rule in payload["rules"])}


def _condition_mask(frame: pd.DataFrame, condition: dict[str, Any]) -> pd.Series:
    field, operator, value = condition["field"], condition["operator"], condition["value"]
    if field not in frame:
        raise KeyError(f"Unknown rule field: {field}")
    series = frame[field]
    if operator == "eq": return series.eq(value)
    if operator == "ne": return series.ne(value)
    if operator == "lt": return series.lt(value)
    if operator == "lte": return series.le(value)
    if operator == "gt": return series.gt(value)
    if operator == "gte": return series.ge(value)
    if operator == "in": return series.isin(value)
    if operator == "not_in": return ~series.isin(value)
    if operator == "is_null": return series.isna() if value else series.notna()
    if operator == "not_null": return series.notna() if value else series.isna()
    raise ValueError(operator)


def conditions_mask(frame: pd.DataFrame, conditions: Iterable[dict[str, Any]], *, require_all: bool = True) -> pd.Series:
    masks = [_condition_mask(frame, condition).fillna(False) for condition in conditions]
    if not masks:
        return pd.Series(True if require_all else False, index=frame.index, dtype=bool)
    result = masks[0]
    for mask in masks[1:]:
        result = result & mask if require_all else result | mask
    return result


def apply_rules(features: pd.DataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Apply each rule independently and preserve every promoted trigger."""
    validate_rule_config(config)
    trigger_frames: list[pd.DataFrame] = []
    executions: list[dict[str, Any]] = []
    denominator = int(features["account_id"].nunique())
    for rule in config["rules"]:
        if not rule["enabled"]:
            executions.append({"rule_id": rule["rule_id"], "status": "DISABLED", "candidate_accounts": 0, "promoted_accounts": 0, "population_denominator": denominator, "population_share": 0.0})
            continue
        required = conditions_mask(features, rule["required_conditions"])
        excluded = conditions_mask(features, rule["exclusion_conditions"], require_all=False)
        quality = features["quality_coverage_ratio"].ge(float(rule["minimum_quality_coverage"]))
        stability = features["stability_status"].isin(rule["allowed_stability"])
        mask = required & ~excluded & quality & stability
        candidates = features.loc[mask].copy()
        candidate_count = int(candidates["account_id"].nunique())
        share = candidate_count / denominator if denominator else 0.0
        minimum = max(int(rule["minimum_support"]), int(rule["minimum_group_size"]))
        status = "PROMOTED"
        promote = candidate_count >= minimum
        if not promote:
            status = "INSUFFICIENT_GROUP_SUPPORT"
        elif share > 0.70 and rule["queue"] != "DATA_QUALITY_REVIEW":
            status = "BROAD_RULE_NOT_PROMOTED"
            promote = False
        elif share > 0.70:
            status = "BROAD_RULE_EXCEPTION_DATA_QUALITY"
        elif share > 0.40:
            status = "BROAD_RULE_REVIEW_REQUIRED"
        if promote:
            candidates["watchlist_rule_id"] = rule["rule_id"]
            candidates["rule_name"] = rule["rule_name"]
            candidates["queue"] = rule["queue"]
            candidates["rule_version"] = rule["version"]
            candidates["human_owner"] = rule["human_owner"]
            candidates["authorized_investigation"] = rule["authorized_investigation"]
            candidates["prohibited_actions"] = json.dumps(rule["prohibited_actions"], separators=(",", ":"), sort_keys=True)
            candidates["reference_window_days"] = rule["reference_window_days"]
            candidates["rule_group_size"] = candidate_count
            candidates["population_denominator"] = denominator
            candidates["rule_population_share"] = share
            candidates["broad_rule_status"] = status if status.startswith("BROAD") else "NOT_BROAD"
            trigger_frames.append(candidates)
        executions.append({
            "rule_id": rule["rule_id"], "rule_name": rule["rule_name"], "queue": rule["queue"],
            "status": status, "candidate_accounts": candidate_count,
            "promoted_accounts": candidate_count if promote else 0,
            "population_denominator": denominator, "population_share": share,
            "minimum_group_size": minimum, "version": rule["version"],
        })
    if not trigger_frames:
        return features.iloc[0:0].copy(), executions
    triggers = pd.concat(trigger_frames, ignore_index=True)
    return triggers.sort_values(["account_key", "queue", "watchlist_rule_id"]).reset_index(drop=True), executions
