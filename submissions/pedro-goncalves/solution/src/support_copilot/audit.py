from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def build_record(
    *,
    pii_counts: dict[str, int],
    prediction: dict,
    decision: dict,
    mode: str,
    threshold: float,
    kill_switch: bool,
    model_sha256: str,
    policy_version: str,
    taxonomy_version: str,
    app_version: str,
    memory_lesson_ids: list[str] | None = None,
    memory_schema_version: str | None = None,
) -> dict:
    return {
        "decision_id": str(uuid4()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_text_stored": False,
        "text_fingerprint_stored": False,
        "patterns_masked": any(pii_counts.values()),
        "masked_pattern_counts": pii_counts,
        "versions": {
            "model_sha256": model_sha256,
            "policy": policy_version,
            "taxonomy": taxonomy_version,
            "app": app_version,
        },
        "prediction": prediction,
        "policy": {
            "mode": mode,
            "threshold": threshold,
            "kill_switch": kill_switch,
        },
        "decision": decision,
        "memory": {
            "matched_lesson_ids": memory_lesson_ids or [],
            "schema_version": memory_schema_version,
        },
        "retention": "Runtime owner must define and enforce retention before production.",
    }


def append_record(path: str | Path, record: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as output:
        output.write(json.dumps(record, ensure_ascii=False) + "\n")
