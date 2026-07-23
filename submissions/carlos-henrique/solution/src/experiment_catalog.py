"""Versioned candidate-intervention catalog; descriptions never execute delivery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {
    "intervention_id", "name", "target_queue", "description", "mechanism_hypothesis",
    "delivery_channel", "operational_owner", "required_capabilities", "required_data",
    "eligibility_requirements", "exclusion_conditions", "ethical_considerations",
    "operational_risks", "contamination_risks", "cost_category", "reversibility",
    "requires_approval", "prohibited_uses", "version",
}
FORBIDDEN_EXECUTION_FIELDS = {"delivered_at", "contact_status", "treatment_result", "uplift", "effect"}


def validate_catalog(payload: dict[str, Any]) -> dict[str, Any]:
    interventions = payload.get("interventions", [])
    if payload.get("execution_policy") != "DESIGN_ONLY_NO_DELIVERY" or len(interventions) != 10:
        raise ValueError("Catalog must contain ten design-only candidate interventions.")
    ids = []
    for item in interventions:
        missing = REQUIRED_FIELDS - set(item)
        if missing: raise ValueError(f"{item.get('intervention_id')} missing {sorted(missing)}")
        if FORBIDDEN_EXECUTION_FIELDS & set(item): raise ValueError("Execution or result field in catalog.")
        if not item["requires_approval"]: raise ValueError("All interventions require approval.")
        ids.append(item["intervention_id"])
    if len(ids) != len(set(ids)): raise ValueError("Duplicate intervention IDs.")
    return {"catalog_version": payload["catalog_version"], "intervention_count": len(ids), "design_only": True}


def load_catalog(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_catalog(payload)
    return payload


def catalog_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validate_catalog(payload)
    return {item["intervention_id"]: item for item in payload["interventions"]}
