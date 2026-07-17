from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def test_core_eda_outputs_exist_and_reconcile() -> None:
    platform = pd.read_csv(ROOT / "outputs" / "tables" / "EDA-BY-PLATFORM.csv")
    assert platform["n"].sum() == 52_214
    assert set(platform["platform"]) == {"Bilibili", "Instagram", "RedNote", "TikTok", "YouTube"}


def test_sponsor_segment_table_has_both_comparison_arms() -> None:
    sponsor = pd.read_csv(ROOT / "outputs" / "tables" / "EDA-SPONSOR-CRUDE-SEGMENTS.csv")
    assert sponsor["n_organic"].notna().all()
    assert sponsor["n_sponsored"].notna().all()
