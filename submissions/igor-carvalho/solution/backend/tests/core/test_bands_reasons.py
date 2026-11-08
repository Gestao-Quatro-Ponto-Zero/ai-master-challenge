import numpy as np
import pytest

from lead_core.bands import assign_band, duration_thresholds, priority_level, score_from_ev
from lead_core.reasons import build_reasons

THR = {"stale_days": 104, "review_days": 138, "focus_score": 80, "follow_up_score": 40}


def test_duration_thresholds():
    t = duration_thresholds(list(range(1, 139)))
    assert t["review_days"] == 137 and t["stale_days"] == 124 and t["typical_p50"] == 70   # P99, não o máximo
    assert duration_thresholds([])["review_days"] == 0


@pytest.mark.parametrize("stage,age,score,band", [
    ("Prospecting", None, None, "prospecting"),
    ("Engaging", 139, 99, "review"),          # zumbi vence qualquer score
    ("Engaging", 138, 99, "stale_risk"),
    ("Engaging", 105, 99, "stale_risk"),      # esfriando vence "foco"
    ("Engaging", 104, 80, "focus"),
    ("Engaging", 50, 79, "follow_up"),
    ("Engaging", 50, 40, "follow_up"),
    ("Engaging", 50, 39, "low"),
])
def test_assign_band(stage, age, score, band):
    assert assign_band(stage, age, score, THR) == band


def test_score_from_ev_is_monotone_and_bounded():
    ref = np.sort(np.random.default_rng(0).uniform(100, 5000, 500))
    ev = np.linspace(0, 6000, 200)
    s = score_from_ev(ev, ref)
    assert s.min() == 0 and s.max() == 100
    assert (np.diff(s) >= 0).all()
    assert score_from_ev(np.array([ref[-1]]), ref)[0] == 100


def test_score_from_ev_empty_reference():
    assert score_from_ev(np.array([1.0, 2.0]), np.array([])).tolist() == [0, 0]


@pytest.mark.parametrize("score,level", [(None, None), (100, "Alta"), (80, "Alta"), (79, "Média"), (40, "Média"), (39, "Baixa"), (0, "Baixa")])
def test_priority_level(score, level):
    assert priority_level(score) == level


def test_reasons_sorted_normalized_and_labeled():
    feats = ["price", "agent_wr", "age_days", "agent_n"]
    vals = [4821.0, 0.62, 129, 90]
    r = build_reasons(feats, vals, np.array([0.1, -0.3, 0.2, 0.0]))
    assert [x["code"] for x in r] == ["agent_wr", "age_band", "price"]       # zero é descartado
    assert sum(x["impact"] for x in r) == pytest.approx(1.0, abs=1e-3)
    assert r[0]["direction"] == "negative" and r[1]["direction"] == "positive"
    assert r[1]["label"] == "Tempo no funil: 129 dias"
    assert r[2]["label"] == "Ticket do produto: US$ 4.821"


def test_reasons_all_zero_returns_empty():
    assert build_reasons(["price"], [1.0], np.array([0.0])) == []
