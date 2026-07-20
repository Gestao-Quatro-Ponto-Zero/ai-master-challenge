"""Tests for evidence, sensitivity and principal-finding gates."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from finding_engine import sensitivity_status, validate_finding  # noqa: E402


def _finding() -> dict:
    return {
        "finding_id": "F", "title": "t", "statement": "s", "evidence": {"n": 20},
        "population": "p", "metric": "m", "comparison": "c", "sample_size": 20,
        "effect_size": 0.2, "confidence_level": "MEDIUM", "limitations": "l",
        "business_relevance": "b", "recommended_investigation": "r", "sensitivity_status": "ROBUST",
    }


def test_finding_without_evidence_is_rejected() -> None:
    finding = _finding()
    finding["evidence"] = {}
    with pytest.raises(ValueError, match="evidence"):
        validate_finding(finding)


def test_unstable_finding_is_not_eligible() -> None:
    finding = _finding()
    finding["sensitivity_status"] = "UNSTABLE"
    with pytest.raises(ValueError, match="UNSTABLE"):
        validate_finding(finding)


def test_sensitivity_thresholds() -> None:
    assert sensitivity_status(1.0, 0.95) == "ROBUST"
    assert sensitivity_status(1.0, 0.8) == "SENSITIVE"
    assert sensitivity_status(1.0, 0.5) == "UNSTABLE"

def test_real_findings_are_evidenced_stable_and_private() -> None:
    import json
    import re

    artifacts = ROOT / "artifacts"
    reports = ROOT / "reports"
    payload = json.loads((artifacts / "executive_findings.json").read_text(encoding="utf-8"))
    assert payload["finding_count"] <= 10
    for finding in payload["findings"]:
        validate_finding(finding)
        assert finding["sensitivity_status"] != "UNSTABLE"
        assert finding["sample_size"] > 0
    public_paths = (
        list(artifacts.glob("*diagnostics.json"))
        + [artifacts / "diagnostic_summary.json", artifacts / "journey_summary.json", artifacts / "executive_findings.json", artifacts / "sensitivity_analysis.json"]
        + list(reports.glob("*-diagnostic.md"))
        + [reports / "data-health.md"]
    )
    public_text = "\n".join(path.read_text(encoding="utf-8") for path in public_paths)
    assert "C:\\" not in public_text
    assert not re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", public_text, re.I)
    assert not re.search(r"\b(causou|provocou|levou ao churn|determinou)\b", public_text, re.I)


def test_real_sensitivity_and_reconciliation_are_explicit() -> None:
    import json

    sensitivity = json.loads((ROOT / "artifacts" / "sensitivity_analysis.json").read_text(encoding="utf-8"))
    summary = json.loads((ROOT / "artifacts" / "diagnostic_summary.json").read_text(encoding="utf-8"))
    statuses = {item["classification"] for item in sensitivity["comparisons"]}
    assert statuses <= {"ROBUST", "SENSITIVE", "UNSTABLE"}
    assert summary["input_validation"]["reconciliation_unexplained_difference"] == 0
