"""Regras de negócio do score, cobertas por muitos casos (unidade pura, sem treino)."""
import itertools

import numpy as np
import pytest

from lead_api.presenters import confidence_reason
from lead_core.bands import assign_band, duration_thresholds, priority_level, score_from_ev
from lead_core.calibration import apply_calibration
from lead_core.constants import (
    BANDS, FOCUS_SCORE, FOLLOW_UP_SCORE, LOW_CONFIDENCE_AGENT_N, PRIORITY_LEVELS, SUGGESTED_ACTIONS, VIEW_OF_BAND, VIEWS,
)
from lead_core.persistence import users_from_tables
from lead_core.reasons import build_reasons
from lead_trainer.evaluation import quality_gate

THR = {"stale_days": 104, "review_days": 138, "focus_score": 80, "follow_up_score": 40}


# ----------------------------------------------------------------------------- faixas (matriz completa)
def oracle(stage, age, score):
    """Implementação independente da regra, escrita como tabela de decisão."""
    if stage == "Prospecting":
        return "prospecting"
    if age > 138:
        return "review"
    if age > 104:
        return "stale_risk"
    return "focus" if score >= 80 else "follow_up" if score >= 40 else "low"


@pytest.mark.parametrize("age,score", list(itertools.product([0, 1, 40, 103, 104, 105, 137, 138, 139, 400],
                                                              [0, 1, 39, 40, 41, 79, 80, 81, 99, 100])))
def test_band_matrix_engaging(age, score):
    assert assign_band("Engaging", age, score, THR) == oracle("Engaging", age, score)


@pytest.mark.parametrize("age,score", [(None, None), (0, 100), (500, 0), (60, 60)])
def test_prospecting_ignores_age_and_score(age, score):
    assert assign_band("Prospecting", age, score, THR) == "prospecting"


@pytest.mark.parametrize("thr,age,score,band", [
    ({"stale_days": 30, "review_days": 60}, 31, 99, "stale_risk"),      # limiares vêm do model card
    ({"stale_days": 30, "review_days": 60}, 61, 99, "review"),
    ({"stale_days": 30, "review_days": 60, "focus_score": 90}, 10, 85, "follow_up"),
    ({"stale_days": 30, "review_days": 60, "follow_up_score": 10}, 10, 15, "follow_up"),
])
def test_band_uses_thresholds_from_model_card(thr, age, score, band):
    assert assign_band("Engaging", age, score, thr) == band


def test_engaging_without_score_is_low():
    assert assign_band("Engaging", 30, None, THR) == "low"


# ----------------------------------------------------------------------------- prioridade
@pytest.mark.parametrize("score,level", [(None, None), (0, "Baixa"), (39, "Baixa"), (40, "Média"), (79, "Média"),
                                         (80, "Alta"), (100, "Alta")])
def test_priority_level_boundaries(score, level):
    assert priority_level(score) == level


def test_priority_levels_cover_0_to_100_without_gaps_or_overlap():
    covered = [s for _, _, lo, hi in PRIORITY_LEVELS for s in range(lo, hi + 1)]
    assert sorted(covered) == list(range(0, 101))
    assert {(k, label) for k, label, *_ in PRIORITY_LEVELS} == {("high", "Alta"), ("medium", "Média"), ("low", "Baixa")}


@pytest.mark.parametrize("score", range(0, 101, 5))
def test_priority_function_matches_published_levels(score):
    label = next(lbl for _, lbl, lo, hi in PRIORITY_LEVELS if lo <= score <= hi)
    assert priority_level(score) == label


def test_priority_thresholds_equal_band_thresholds():
    assert (FOCUS_SCORE, FOLLOW_UP_SCORE) == (80, 40)


# ----------------------------------------------------------------------------- visões (abas)
def test_every_band_belongs_to_exactly_one_tab():
    tabs = ["focus", "decide", "follow", "prospecting", "review"]
    for band in BANDS:
        assert [t for t in tabs if band in VIEWS[t]["bands"]] == [VIEW_OF_BAND[band]]


def test_all_view_covers_every_band_and_ev_excludes_review():
    assert set(VIEWS["all"]["bands"]) == set(BANDS)
    assert "review" not in VIEWS["ev"]["bands"] and VIEWS["ev"]["sort"] == "expected_value"


def test_every_band_has_a_suggested_action():
    assert set(SUGGESTED_ACTIONS) == set(BANDS) and all(SUGGESTED_ACTIONS.values())


# ----------------------------------------------------------------------------- confiança
@pytest.mark.parametrize("confidence,stage,expected", [
    ("medium", "Engaging", None), ("high", "Engaging", None), ("medium", "Prospecting", None),
    ("low", "Prospecting", "o deal ainda não tem histórico"),
    ("low", "Engaging", f"o vendedor tem menos de {LOW_CONFIDENCE_AGENT_N} deals fechados"),
])
def test_confidence_reason(confidence, stage, expected):
    assert confidence_reason(confidence, stage) == expected


# ----------------------------------------------------------------------------- score por percentil
def test_score_is_percentile_of_reference():
    ref = np.arange(1.0, 101.0)                       # 100 valores: 1..100
    assert score_from_ev(np.array([0.5, 1, 50, 100, 1000]), ref).tolist() == [0, 1, 50, 100, 100]


@pytest.mark.parametrize("ev", [-5.0, 0.0])
def test_score_of_non_positive_value_is_zero_when_reference_positive(ev):
    assert score_from_ev(np.array([ev]), np.array([1.0, 2.0, 3.0]))[0] == 0


def test_score_with_ties_in_reference_is_stable():
    ref = np.array([5.0] * 10)
    assert score_from_ev(np.array([4.9, 5.0, 5.1]), ref).tolist() == [0, 100, 100]


def test_score_is_integer_between_0_and_100():
    s = score_from_ev(np.random.default_rng(1).uniform(0, 9000, 300), np.sort(np.random.default_rng(2).uniform(0, 5000, 200)))
    assert s.dtype.kind == "i" and s.min() >= 0 and s.max() <= 100


# ----------------------------------------------------------------------------- limiares de duração
@pytest.mark.parametrize("durations,p50,stale,review", [
    ([10], 10, 10, 10), ([1, 2, 3, 4, 5], 3, 5, 5), ([50] * 20, 50, 50, 50), ([], 0, 0, 0),
    ([1.5, 2.5], 2, 2, 2),
])
def test_duration_thresholds_cases(durations, p50, stale, review):
    t = duration_thresholds(durations)
    assert (t["typical_p50"], t["stale_days"], t["review_days"]) == (p50, stale, review)


def test_review_threshold_is_p99_not_the_maximum():
    base = list(range(1, 101))
    assert duration_thresholds(base)["review_days"] == 99
    # um único fechamento muito tardio (limpeza de carteira) não pode empurrar o limiar de zumbi
    assert duration_thresholds(base + [900])["review_days"] < 150


# ----------------------------------------------------------------------------- calibração
@pytest.mark.parametrize("alpha,base,center,p,expected", [
    (1.0, 0.5, 0.5, 0.5, 0.5), (1.0, 0.4, 0.5, 0.7, 0.6), (0.5, 0.5, 0.5, 0.9, 0.7), (0.1, 0.4, 0.5, 0.9, 0.44),
    (0.25, 0.3, 0.5, 0.1, 0.2), (0.75, 0.5, 0.4, 0.4, 0.5),
])
def test_calibration_formula(alpha, base, center, p, expected):
    got = apply_calibration([p], {"alpha": alpha, "center": center, "base": base})[0]
    assert got == pytest.approx(expected)


@pytest.mark.parametrize("p", [0.0, 1.0, -2.0, 3.0])
def test_calibration_is_clipped_to_probability_range(p):
    out = apply_calibration([p], {"alpha": 1.0, "center": 0.5, "base": 0.5})[0]
    assert 0.01 <= out <= 0.99


def test_calibration_preserves_ranking():
    p = np.linspace(0.05, 0.95, 50)
    out = apply_calibration(p, {"alpha": 0.1, "center": 0.5, "base": 0.4})
    assert (np.diff(out) > 0).all()


# ----------------------------------------------------------------------------- portão de qualidade
@pytest.mark.parametrize("cand,active,ok", [
    ({"auc": None, "auc_ci95": None}, None, False),                            # sem backtest
    ({"auc": 0.55, "auc_ci95": [0.52, 0.58]}, None, True),                    # primeira versão
    ({"auc": 0.55, "auc_ci95": [0.50, 0.58]}, None, False),                   # IC encosta em 0,5
    ({"auc": 0.55, "auc_ci95": [0.499, 0.58]}, None, False),
    ({"auc": 0.55, "auc_ci95": [0.501, 0.58]}, None, True),
    ({"auc": 0.541, "auc_ci95": [0.52, 0.57]}, {"auc": 0.55}, True),          # piora dentro da tolerância (0,01)
    ({"auc": 0.539, "auc_ci95": [0.52, 0.57]}, {"auc": 0.55}, False),         # piora além da tolerância
    ({"auc": 0.60, "auc_ci95": [0.55, 0.65]}, {"auc": 0.55}, True),           # melhora
    ({"auc": 0.56, "auc_ci95": [0.52, 0.6]}, {"auc": None}, True),            # ativo sem métrica
])
def test_quality_gate_cases(cand, active, ok):
    assert quality_gate(cand, active)[0] is ok


def test_quality_gate_explains_rejection():
    assert "acaso" in quality_gate({"auc": 0.52, "auc_ci95": [0.49, 0.55]}, None)[1]
    assert "pior" in quality_gate({"auc": 0.50, "auc_ci95": [0.51, 0.55]}, {"auc": 0.56})[1]


# ----------------------------------------------------------------------------- motivos
def test_reasons_are_normalised_sorted_and_signed():
    r = build_reasons(["a", "b", "c"], [1, 2, 3], np.array([0.2, -0.6, 0.2]))
    assert [x["code"] for x in r][0] == "b" and r[0]["direction"] == "negative"
    assert sum(x["impact"] for x in r) == pytest.approx(1.0, abs=1e-3)
    assert {x["direction"] for x in r} == {"positive", "negative"}


def test_reasons_skip_zero_contributions_and_handle_all_zero():
    assert [x["code"] for x in build_reasons(["a", "b"], [1, 2], np.array([0.0, 0.5]))] == ["b"]
    assert build_reasons(["a"], [1], np.array([0.0])) == []


# ----------------------------------------------------------------------------- usuários
TABLES = {"agents": {"Ana Souza": {"manager": "Rui Lima", "regional_office": "West"},
                     "Bia Cruz": {"manager": "Rui Lima", "regional_office": "West"},
                     "Zé D'Ávila": {"manager": "Eva Reis", "regional_office": "East"}}}


def test_users_from_tables_roles_and_keys():
    rows = {u["user_key"]: u for u in users_from_tables(TABLES, "t")}
    assert set(rows) == {"revops", "ana-souza", "bia-cruz", "ze-d-avila", "rui-lima", "eva-reis"}
    assert rows["revops"]["role"] == "revops" and rows["rui-lima"]["role"] == "manager"
    assert rows["ana-souza"]["role"] == "seller" and rows["ana-souza"]["manager"] == "Rui Lima"
    assert rows["eva-reis"]["regional_office"] == "East" and rows["rui-lima"]["manager"] is None


def test_users_from_empty_tables_has_only_admin():
    assert [u["user_key"] for u in users_from_tables(None)] == ["revops"]
