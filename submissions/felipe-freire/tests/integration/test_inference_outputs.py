import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def test_sponsorship_record_has_effect_interval_and_limitations() -> None:
    path = ROOT / "outputs" / "evidence" / "inference-evidence-records.json"
    record = json.loads(path.read_text(encoding="utf-8"))["INF-SPON-001"]
    assert record["status"] == "VALIDATED"
    assert record["result"]["ci95_low"] < record["result"]["estimate"]
    assert record["result"]["ci95_high"] > record["result"]["estimate"]
    assert record["limitations"]


def test_propensity_has_common_support() -> None:
    frame = pd.read_csv(ROOT / "outputs" / "tables" / "INF-PROPENSITY-DIAGNOSTICS.csv")
    assert frame["propensity"].between(0.1, 0.9).mean() > 0.99
