"""Tests for aggregate-only deterministic Phase 4 reporting."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from run_survival_analysis import JSON_NAMES, REPORT_NAMES, validate_inputs  # noqa: E402
from survival_reporting import render_reports, write_json  # noqa: E402


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_json_writer_is_idempotent() -> None:
    path = ROOT / ".venv" / "phase4-survival-writer-test.json"
    payload = {"b": 2, "a": [1, 3]}
    write_json(path, payload); first = _hash(path)
    write_json(path, payload); second = _hash(path)
    assert first == second
    path.unlink(missing_ok=True)


def test_phase4_jsons_are_aggregate_and_without_pii() -> None:
    for name in JSON_NAMES:
        text = (ROOT / "artifacts" / name).read_text(encoding="utf-8").lower()
        assert '"account_id"' not in text
        assert "account_name" not in text
        assert "feedback_text" not in text


def test_reports_reconcile_with_renderer_and_required_sections() -> None:
    payloads = {name: json.loads((ROOT / "artifacts" / name).read_text(encoding="utf-8")) for name in JSON_NAMES}
    rendered = render_reports(payloads)
    assert set(rendered) == set(REPORT_NAMES)
    assert rendered["survival-analysis.md"] == (ROOT / "reports" / "survival-analysis.md").read_text(encoding="utf-8")
    for section in ("## 1. Objetivo", "## 6. Kaplan–Meier", "## 9. Landmarks", "## 12. Sensibilidade", "## 15. Limitações"):
        assert section in rendered["survival-analysis.md"]


def test_input_hashes_and_mandatory_figures() -> None:
    assert validate_inputs()["all_hashes_match"] is True
    expected = {
        "kaplan-meier-overall.png", "kaplan-meier-quality-populations.png",
        "kaplan-meier-selected-groups.png", "cumulative-hazard-overall.png",
        "landmark-survival-comparison.png", "rmst-comparison.png",
    }
    actual = {path.name for path in (ROOT / "reports" / "figures").glob("*.png")}
    # Later governed phases may add figures; Phase 4 assets must remain present.
    assert expected.issubset(actual)
