"""Cross-component reconciliation: dashboard aggregation must agree with the
EDA/inference evidence pack, since both read the same contract-approved dataset
independently. A divergence here means two components drifted apart, not that
either number is individually wrong.
"""

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest
from dashboard.data import kpis, load_data, performance_by

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "social_media_dataset.csv"
PROCESSED = ROOT / "data" / "processed" / "posts_analytical.csv"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_raw_dataset_hash_matches_source_contract() -> None:
    contract = (ROOT / "docs" / "contracts" / "source-data.md").read_text(encoding="utf-8")
    assert _sha256(RAW).upper() in contract.upper()


def test_processed_row_count_reconciles_with_raw() -> None:
    raw_rows = sum(1 for _ in RAW.open("r", encoding="utf-8")) - 1
    processed = pd.read_csv(PROCESSED)
    assert len(processed) == raw_rows
    assert processed["id"].is_unique
    assert processed["content_id"].is_unique


def test_dashboard_overall_kpis_reconcile_with_eda_evidence() -> None:
    evidence = json.loads(
        (ROOT / "outputs" / "evidence" / "eda-evidence-records.json").read_text(encoding="utf-8")
    )
    overview = pd.read_csv(ROOT / "outputs" / "tables" / "EDA-OVERVIEW.csv").set_index("metric")[
        "value"
    ]

    summary = kpis(load_data())
    assert summary["posts"] == int(overview["rows"])
    assert summary["sponsored_share"] == pytest.approx(float(overview["sponsored_share"]))
    assert summary["engagement_mean"] == pytest.approx(
        evidence["EDA-BASE-001"]["estimate"]["mean"], abs=1e-8
    )


def test_dashboard_platform_breakdown_reconciles_with_eda_table() -> None:
    eda_platform = pd.read_csv(ROOT / "outputs" / "tables" / "EDA-BY-PLATFORM.csv").set_index(
        "platform"
    )
    dashboard_platform = performance_by(load_data(), "platform").set_index("platform")

    assert dashboard_platform["n"].sum() == eda_platform["n"].sum()
    for platform in eda_platform.index:
        assert dashboard_platform.loc[platform, "n"] == eda_platform.loc[platform, "n"]
        assert dashboard_platform.loc[platform, "engagement_mean"] == pytest.approx(
            eda_platform.loc[platform, "engagement_mean"], abs=1e-8
        )
