"""Validate evaluator-facing documentation against the frozen dashboard snapshot."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SUBMISSION_ROOT = Path(__file__).resolve().parents[2]
SOLUTION_ROOT = SUBMISSION_ROOT / "solution"
DATA_DIR = SOLUTION_ROOT / "app" / "public" / "data"
REPORTS_DIR = SOLUTION_ROOT / "reports"
README = SUBMISSION_ROOT / "README.md"
ARCHITECTURE = SUBMISSION_ROOT / "docs" / "architecture.md"
APP_README = SOLUTION_ROOT / "app" / "README.md"
MATRIX = REPORTS_DIR / "metric-consistency-matrix.md"
DOCUMENTS = (README, ARCHITECTURE, APP_README, MATRIX)
CUTOFF = "2024-12-31T19:00:00"
SCREENSHOTS = (
    "01-executive-overview.png",
    "02-data-quality.png",
    "03-journey-explorer.png",
    "04-journeygraph.png",
    "05-watchlist.png",
    "06-experiment-lab.png",
    "07-governance.png",
)


def load_json(name: str) -> dict[str, Any]:
    with (DATA_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def inventory_digest(paths: list[Path]) -> str:
    rows = []
    for path in sorted(paths, key=lambda item: item.name):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{path.name}:{digest}")
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def validate_links(document: Path, errors: list[str]) -> int:
    text = document.read_text(encoding="utf-8")
    links = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text)
    checked = 0
    for link in links:
        if link.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = link.split("#", maxsplit=1)[0]
        if not target:
            continue
        checked += 1
        if not (document.parent / target).resolve().exists():
            errors.append(f"broken link in {document.relative_to(SUBMISSION_ROOT)}: {link}")
    return checked


def expect_equal(errors: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        errors.append(f"{label}: expected {expected!r}, found {actual!r}")


def main() -> int:
    errors: list[str] = []
    for document in DOCUMENTS:
        if not document.exists():
            errors.append(f"missing document: {document.relative_to(SUBMISSION_ROOT)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    overview = load_json("overview.json")
    quality = load_json("quality.json")
    journeys = load_json("journey_index.json")
    watchlist = load_json("watchlist_summary.json")
    experiments = load_json("experiment_registry.json")
    metadata = load_json("metadata.json")

    metrics = {item["label"]: item["value"] for item in overview["metrics"]}
    expected_metrics = {
        "Accounts": 500,
        "Events processed": 35_586,
        "Usable events": 13_927,
        "Journeys": 4_221,
        "Promotable patterns": 435,
        "Promotable transitions": 43,
        "Review queues": 7,
        "Experiment designs": 8,
    }
    for label, expected in expected_metrics.items():
        expect_equal(errors, f"overview metric {label}", metrics.get(label), expected)

    quality_by_status = {item["status"]: item["events"] for item in quality["distribution"]}
    expect_equal(errors, "quarantined records", quality_by_status.get("QUARANTINED"), 21_659)
    expect_equal(errors, "journey accounts", journeys.get("accounts"), 500)
    expect_equal(errors, "journey count", journeys.get("journeys"), 4_221)
    expect_equal(errors, "watchlist items", watchlist.get("items"), 1_609)
    expect_equal(errors, "watchlist unique accounts", watchlist.get("unique_accounts"), 500)
    expect_equal(errors, "watchlist queues", len(watchlist.get("queues", [])), 7)

    statuses = Counter(item["status"] for item in experiments["experiments"])
    expect_equal(errors, "experiment count", len(experiments["experiments"]), 8)
    expect_equal(errors, "READY_FOR_REVIEW", statuses["READY_FOR_REVIEW"], 1)
    expect_equal(errors, "PILOT_ONLY", statuses["PILOT_ONLY"], 1)
    expect_equal(errors, "UNDERPOWERED", statuses["UNDERPOWERED"], 4)
    expect_equal(errors, "NOT_FEASIBLE", statuses["NOT_FEASIBLE"], 2)

    json_paths = sorted(DATA_DIR.glob("*.json"))
    expect_equal(errors, "dashboard JSON count", len(json_paths), 15)
    for path in json_paths:
        payload = load_json(path.name)
        observed_cutoff = payload.get("cutoff", payload.get("data_cutoff"))
        if path.name == "demo_story.json":
            expect_equal(errors, "global cutoff for demo_story.json", metadata["data_cutoff"], CUTOFF)
        else:
            expect_equal(errors, f"cutoff in {path.name}", observed_cutoff, CUTOFF)
    expect_equal(errors, "metadata validation output_count", metadata["validation"]["output_count"], 15)

    readme = README.read_text(encoding="utf-8")
    required_headings = (
        "## Executive Summary",
        "## The Problem",
        "## The Solution",
        "## Key Results",
        "## Product Walkthrough",
        "## Governed by Design",
        "## Architecture",
        "## Quick Start",
    )
    for heading in required_headings:
        if heading not in readme:
            errors.append(f"README missing heading: {heading}")

    quick_start = "\n".join(
        (
            "cd submissions/carlos-henrique/solution/app",
            "npm ci",
            "npm run build:data",
            "npm run dev",
        )
    )
    if quick_start not in readme:
        errors.append("README Quick Start does not match the validated npm workflow")
    if quick_start not in APP_README.read_text(encoding="utf-8"):
        errors.append("app README does not contain the validated npm workflow")

    matrix = MATRIX.read_text(encoding="utf-8")
    if "| FAIL |" in matrix or "| BLOCKED |" in matrix:
        errors.append("metric consistency matrix contains a non-PASS result")
    if "be5d2d2edcc6992de678b5ef0d7d18d16ce39f423421ec5f6805aaebc664b61b" not in matrix:
        errors.append("metric consistency matrix is missing the validated inventory digest")

    for screenshot in SCREENSHOTS:
        if not (REPORTS_DIR / "screenshots" / screenshot).is_file():
            errors.append(f"missing screenshot: {screenshot}")

    checked_links = sum(validate_links(document, errors) for document in DOCUMENTS)
    for document in DOCUMENTS:
        for line_number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), 1):
            if line.rstrip() != line:
                errors.append(
                    f"trailing whitespace: {document.relative_to(SUBMISSION_ROOT)}:{line_number}"
                )

    result = {
        "cutoff": CUTOFF,
        "documents": len(DOCUMENTS),
        "inventory_sha256": inventory_digest(json_paths),
        "json_files": len(json_paths),
        "links_checked": checked_links,
        "metrics_checked": 15,
        "screenshots": len(SCREENSHOTS),
        "status": "PASS" if not errors else "BLOCKED",
    }
    print(json.dumps(result, indent=2, sort_keys=True))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
