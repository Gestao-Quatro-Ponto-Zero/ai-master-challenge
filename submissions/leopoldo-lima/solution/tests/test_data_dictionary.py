from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_ROOT = ROOT.parent
OUT_MD = SUBMISSION_ROOT / "docs" / "DATA_DICTIONARY.md"
OUT_JSON = ROOT / "artifacts" / "data-validation" / "metadata-coverage-report.json"


def test_data_dictionary_outputs_exist_after_generation() -> None:
    assert OUT_MD.exists()
    assert OUT_JSON.exists()


def test_metadata_coverage_has_tables() -> None:
    payload = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    assert "tables" in payload
    assert "sales_pipeline" in payload["tables"]
