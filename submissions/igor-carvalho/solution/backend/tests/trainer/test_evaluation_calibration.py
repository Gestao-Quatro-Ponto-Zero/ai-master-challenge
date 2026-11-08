import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from lead_core.calibration import apply_calibration
from lead_trainer.calibration import fit_calibration
from lead_trainer.evaluation import backtest, bootstrap_auc_ci, lift_at, quality_gate, revenue_capture
from lead_trainer.repository import CsvDealRepository


def test_lift_and_capture_basics():
    y = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    assert lift_at(y, np.linspace(1, 0, 10), 0.2) == pytest.approx(5.0)
    assert lift_at(y, np.linspace(0, 1, 10), 0.2) == pytest.approx(0.0)
    realized = np.array([100.0, 0, 0, 0, 0])
    assert revenue_capture(np.array([5, 4, 3, 2, 1.0]), realized, 0.2) == pytest.approx(1.0)
    assert np.isnan(revenue_capture(np.arange(5.0), np.zeros(5)))


def test_bootstrap_ci_contains_point_estimate():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 800)
    p = y * 0.2 + rng.random(800)
    lo, hi = bootstrap_auc_ci(y, p, n_boot=200)
    assert lo < roc_auc_score(y, p) < hi


# ------------------------------------------------------------------ calibração
def test_calibration_shrinks_toward_base_and_is_monotone():
    cal = {"alpha": 0.25, "center": 0.6, "base": 0.62}
    p = np.linspace(0.1, 0.9, 50)
    out = apply_calibration(p, cal)
    assert (np.diff(out) > 0).all()
    assert out.max() - out.min() < p.max() - p.min()
    assert out.min() >= 0.01 and out.max() <= 0.99


def test_fit_calibration_shift_matches_observed_rate():
    rng = np.random.default_rng(1)
    p = rng.uniform(0.05, 0.4, 3000)
    y = (rng.random(3000) < 0.10).astype(float)                    # taxa real bem abaixo da média prevista
    cal = fit_calibration(y, p, base_rate=0.10)
    assert cal["method"] == "level_shift" and cal["shift"] < 0
    assert apply_calibration(p, cal).mean() == pytest.approx(y.mean(), abs=0.005)


def test_fit_calibration_keeps_ranking_and_slope():
    p = np.linspace(0.05, 0.6, 400)
    y = (np.random.default_rng(3).random(400) < 0.2).astype(float)
    out = apply_calibration(p, fit_calibration(y, p, base_rate=0.2))
    assert (np.diff(out) > 0).all()


def test_fit_calibration_not_useful_when_level_is_unpredictable():
    rng = np.random.default_rng(4)
    p = np.clip(0.15 + rng.normal(0, 0.05, 2000), 0.01, 0.9)
    y = np.r_[(rng.random(1000) < 0.30), (rng.random(1000) < 0.05)].astype(float)   # taxa muda entre as metades
    cal = fit_calibration(y, p, base_rate=0.15)
    assert cal["evaluated"] == "out_of_sample" and cal["useful"] is False


def test_fit_calibration_marks_useful_when_signal_exists():
    rng = np.random.default_rng(2)
    p = rng.uniform(0.05, 0.9, 6000)
    y = (rng.random(6000) < p).astype(float)
    cal = fit_calibration(y, p, base_rate=0.05)                      # taxa base de treino defasada
    assert cal["useful"] is True and abs(cal["shift"]) < 0.3


def test_small_validation_is_evaluated_in_sample():
    rng = np.random.default_rng(5)
    p = rng.uniform(0.1, 0.5, 100)
    cal = fit_calibration((rng.random(100) < 0.2).astype(float), p, base_rate=0.2)
    assert cal["evaluated"] == "in_sample"


# ------------------------------------------------------------------ portão de qualidade
@pytest.mark.parametrize("cand,active,ok", [
    ({"auc": 0.55, "auc_ci95": [0.52, 0.57]}, None, True),
    ({"auc": 0.51, "auc_ci95": [0.49, 0.53]}, None, False),                       # não supera o acaso
    ({"auc": 0.55, "auc_ci95": [0.52, 0.57]}, {"auc": 0.558}, True),             # dentro da tolerância
    ({"auc": 0.54, "auc_ci95": [0.52, 0.57]}, {"auc": 0.56}, False),              # pior que o ativo
    ({"auc": 0.60, "auc_ci95": [0.55, 0.65], "revenue_capture_top20": 0.30,
      "revenue_capture_price_only_top20": 0.35}, None, False),                    # não bate "só preço"
    ({"auc": 0.50, "auc_ci95": [0.52, 0.57], "protocol": "won_30d.v1"},
     {"auc": 0.70, "protocol": "legacy"}, True),                                  # protocolos diferentes: não compara
    ({"auc": None, "auc_ci95": None}, None, False),
])
def test_quality_gate(cand, active, ok):
    passed, reason = quality_gate(cand, active)
    assert passed is ok and reason


def test_backtest_on_synthetic_data(synthetic_dir):
    df = CsvDealRepository(synthetic_dir).load()
    bt = backtest(df, [pd.Timestamp("2017-07-01"), pd.Timestamp("2017-09-15")])
    assert len(bt["per_snapshot"]) == 2
    assert 0.3 < bt["auc"] < 1.0 and bt["auc_ci95"][0] < bt["auc"] < bt["auc_ci95"][1]
    assert bt["n_test"] == sum(m["n_test"] for m in bt["per_snapshot"])


def test_backtest_skips_snapshots_without_data(synthetic_dir):
    df = CsvDealRepository(synthetic_dir).load()
    bt = backtest(df, [pd.Timestamp("2016-10-05")])      # antes de existir treino
    assert bt["auc"] is None and bt["per_snapshot"] == []
