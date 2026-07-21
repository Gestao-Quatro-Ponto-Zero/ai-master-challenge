"""Tests for deterministic graph artifacts, reports, and figures."""

import hashlib
import json
import sys
from pathlib import Path

import matplotlib.image as mpimg

SOLUTION = Path(__file__).parents[1]
SRC = SOLUTION / "src"
sys.path.insert(0, str(SRC))

from graph_reporting import write_json  # noqa: E402


def test_json_writer_is_deterministic(tmp_path: Path) -> None:
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    payload = {"z": [2, 1], "a": {"value": 3}}
    write_json(first, payload)
    write_json(second, payload)
    assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()
    assert list(json.loads(first.read_text(encoding="utf-8"))) == ["a", "z"]


def test_reports_have_exact_contract_and_governed_language() -> None:
    report_dir = SOLUTION / "reports"
    expected = {"journeygraph.md", "graph-methodology.md", "graph-schema.md", "graph-validation.md", "neo4j-guide.md"}
    for name in expected:
        assert (report_dir / name).is_file()
    main = (report_dir / "journeygraph.md").read_text(encoding="utf-8")
    assert "## 1. Executive Summary" in main
    assert "## 20. Prepara" in main
    assert "centralidade" in main.lower() and "estrutural" in main.lower()
    assert "MRR" in main and "associado" in main.lower()
    lowered = "\n".join((report_dir / name).read_text(encoding="utf-8").lower() for name in expected)
    for forbidden in ('"account_id":', '"account_name":', '"email":', '"feedback_text":'):
        assert forbidden not in lowered


def test_six_aggregate_figures_are_valid_pngs() -> None:
    figure_dir = SOLUTION / "reports" / "figures"
    names = {
        "journeygraph-overview.png", "journeygraph-event-transitions.png",
        "journeygraph-churn-paths.png", "journeygraph-reactivation-paths.png",
        "journeygraph-quality-layer.png", "journeygraph-taxonomy.png",
    }
    for name in names:
        path = figure_dir / name
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        image = mpimg.imread(path)
        assert image.shape[0] >= 600 and image.shape[1] >= 900
