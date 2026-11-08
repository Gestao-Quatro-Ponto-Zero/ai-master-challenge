"""Comportamento do modelo de receita esperada em 30 dias (alvo, features, limiares, calibração, pipeline)."""
import json

import numpy as np
import pandas as pd
import pytest

from lead_core.bands import displayed_score, duration_thresholds
from lead_core.bundle import SCORED_FILE
from lead_core.calibration import apply_calibration
from lead_core.constants import HORIZON_DAYS
from lead_core.features import apply_tables, build_history_tables
from lead_trainer.evaluation import rolling_snapshots
from lead_trainer.repository import CsvDealRepository
from lead_trainer.training import build_test, build_train, fit_gbm

T = pd.Timestamp("2017-09-15")
THR = {"stale_days": 104, "review_days": 127, "focus_score": 80, "follow_up_score": 40}


@pytest.fixture(scope="module")
def df(synthetic_dir):
    return CsvDealRepository(synthetic_dir).load()


# ------------------------------------------------------------------ alvo
def test_stalled_open_deals_count_as_zero(df):
    test = build_test(df, T)
    still_open_after = test[test["close_date"].isna() | (test["close_date"] > T + pd.Timedelta(days=HORIZON_DAYS))]
    assert len(still_open_after) > 0 and (still_open_after["won_30d"] == 0).all()


def test_label_is_won_inside_horizon_only(df):
    t = build_test(df, T)
    inside = (t["close_date"] <= T + pd.Timedelta(days=HORIZON_DAYS)) & (t["won"] == 1)
    assert (t["won_30d"] == inside.astype(int)).all()
    assert (t.loc[t["won_30d"] == 1, "realized_30d"] == t.loc[t["won_30d"] == 1, "close_value"]).all()


def test_train_set_ignores_what_happens_after_T(df):
    base = build_train(df, T)
    changed = df.copy()
    m = changed["close_date"] > T
    changed.loc[m, "won"] = 1.0 - changed.loc[m, "won"]
    changed.loc[m, "close_date"] = changed.loc[m, "close_date"] + pd.Timedelta(days=200)
    again = build_train(changed, T)
    pd.testing.assert_frame_equal(base[["age_days", "age_vs_cycle", "won_30d"]], again[["age_days", "age_vs_cycle", "won_30d"]])


def test_train_includes_deals_that_never_closed(df):
    train = build_train(df, T)
    assert len(train) > len(df[df["won"].notna()])           # fotos repetidas + abertos que seguem parados


# ------------------------------------------------------------------ feature age_vs_cycle
def test_age_vs_cycle_uses_p99_of_closed_cycle(df):
    tables = build_history_tables(df, T)
    assert tables["cycle_p99"] > 0
    t = build_test(df, T)
    assert (t["age_vs_cycle"] * tables["cycle_p99"]).sub(t["age_days"]).abs().max() < 1e-6


def test_legacy_tables_without_cycle_still_apply(df):
    tables = {k: v for k, v in build_history_tables(df, T).items() if k != "cycle_p99"}
    snap = build_test(df, T).drop(columns=["age_vs_cycle"])
    out = apply_tables(snap, tables)
    assert out["age_vs_cycle"].isna().all()


def test_fit_gbm_uses_enough_trees(df):
    fitted = fit_gbm(build_train(df, T))
    assert fitted.best_iteration >= 50 and fitted.validation_p.min() >= 0


# ------------------------------------------------------------------ limiares e faixas
def test_review_and_stale_are_quantiles_not_extremes():
    durations = list(range(1, 101)) + [2000]
    t = duration_thresholds(durations)
    assert t["stale_days"] < t["review_days"] < 200


def test_stale_score_never_reaches_high_priority():
    assert displayed_score("stale_risk", 97, THR) == 79
    assert displayed_score("stale_risk", 30, THR) == 30
    assert displayed_score("review", 97, THR) is None
    assert displayed_score("focus", 97, THR) == 97


# ------------------------------------------------------------------ calibração (aplicação)
def test_level_shift_is_monotone_and_moves_level():
    p = np.linspace(0.02, 0.6, 30)
    down = apply_calibration(p, {"method": "level_shift", "shift": -1.0})
    assert (np.diff(down) > 0).all() and down.mean() < p.mean()
    assert np.allclose(apply_calibration(p, {"method": "level_shift", "shift": 0.0}), p, atol=1e-6)


def test_legacy_shrink_artifacts_still_load():
    out = apply_calibration([0.7], {"method": "shrink_to_base", "alpha": 0.5, "center": 0.5, "base": 0.5})
    assert out[0] == pytest.approx(0.6)


# ------------------------------------------------------------------ pipeline
def _card(trained):
    v = trained["result"]["version"]
    return json.loads((trained["artifact_dir"] / f"v{v}" / "model_card.json").read_text())


def test_model_card_describes_30d_target(trained):
    c = _card(trained)
    assert c["target"] == "won_within_30d" and c["horizon_days"] == 30
    assert c["calibration"]["method"] == "level_shift" and "useful" in c["calibration"]
    assert c["backtest"]["protocol"] == "won_30d.v1"
    assert "age_vs_cycle" in c["features"]["num"] if isinstance(c["features"], dict) else "age_vs_cycle" in c["features"]


def test_scored_stale_never_high_and_zombies_have_no_score(trained):
    v = trained["result"]["version"]
    s = pd.read_parquet(trained["artifact_dir"] / f"v{v}" / SCORED_FILE)
    assert (s.loc[s["band"] == "stale_risk", "score"] <= 79).all()
    assert s.loc[s["band"] == "review", "score"].isna().all()
    assert (s["band"][s["score"] >= 80] == "focus").all()


def test_prospecting_has_expected_value_but_no_score(trained):
    v = trained["result"]["version"]
    s = pd.read_parquet(trained["artifact_dir"] / f"v{v}" / SCORED_FILE)
    p = s[s["band"] == "prospecting"]
    if len(p):
        assert p["score"].isna().all() and p["expected_value"].notna().all() and p["age_days"].isna().all()


def test_zombies_are_less_likely_than_live_deals(trained):
    v = trained["result"]["version"]
    s = pd.read_parquet(trained["artifact_dir"] / f"v{v}" / SCORED_FILE)
    z, live = s[s["band"] == "review"], s[s["band"].isin(["focus", "follow_up", "low"])]
    if len(z) and len(live):
        assert z["p_win"].mean() < live["p_win"].mean()


# ------------------------------------------------------------------ backtest móvel
def test_rolling_snapshots_end_at_reference_minus_horizon():
    snaps = rolling_snapshots(pd.Timestamp("2017-12-31"))
    assert len(snaps) == 4 and snaps[-1] == pd.Timestamp("2017-12-01")
    assert all((b - a).days == 14 for a, b in zip(snaps, snaps[1:]))
