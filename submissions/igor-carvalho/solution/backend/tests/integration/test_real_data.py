"""Roda o pipeline completo no dataset REAL e confere os números aprovados nos notebooks (marcado slow)."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from lead_core.bundle import SCORED_FILE
from lead_trainer.pipeline import TrainConfig, run_training

DATA = Path(__file__).resolve().parents[2] / "data"
pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def real(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("real")
    cfg = TrainConfig(DATA, tmp / "art", tmp / "app.db", clock=lambda: datetime(2026, 11, 7, tzinfo=timezone.utc))
    result = run_training(cfg)
    folder = cfg.artifact_dir / f"v{result['version']}"
    return result, json.loads((folder / "model_card.json").read_text()), pd.read_parquet(folder / SCORED_FILE)


def test_backtest_beats_chance_and_price_only(real):
    result, card, _ = real
    assert result["status"] == "active"                       # passou no portão de qualidade
    bt = card["backtest"]
    assert bt["protocol"] == "won_30d.v1" and bt["horizon_days"] == 30
    assert 0.62 <= bt["auc"] <= 0.72 and bt["auc_ci95"][0] > 0.5
    assert bt["revenue_capture_top20"] > bt["revenue_capture_price_only_top20"]


def test_thresholds_are_quantiles(real):
    thr = real[1]["thresholds"]
    assert (thr["stale_days"], thr["review_days"]) == (104, 127)


def test_pipeline_counts(real):
    s = real[2]
    assert len(s) == 2089 and (s["stage"] == "Prospecting").sum() == 500
    assert (s["band"] == "review").sum() == 1346


def test_no_stalled_deal_in_focus(real):
    s = real[2]
    assert (s["score"] >= 80).sum() > 0
    assert (s.loc[s["band"] == "stale_risk", "score"] <= 79).all()
    assert (s.loc[s["score"] >= 80, "age_days"] <= real[1]["thresholds"]["stale_days"]).all()


def test_calibration_card_is_honest(real):
    cal = real[1]["calibration"]
    assert cal["method"] == "level_shift" and cal["evaluated"] == "out_of_sample"
    assert cal["useful"] == (cal["brier_calibrated"] < cal["brier_constant"])
