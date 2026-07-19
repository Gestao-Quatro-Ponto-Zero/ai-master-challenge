# -*- coding: utf-8 -*-
"""Testes da FASE 3 — contratos e sanidade matemática do modelo de ROI."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_prep import TICKETS_PER_YEAR, build_dataset1
from src.roi_model import (
    BUSINESS_SCENARIOS,
    DEFLECTION_BY_TYPE,
    SOLUTION_IMPL_COST_BRL,
    break_even_deflection,
    roi_business_scenario,
    roi_scenario,
    sensitivity_tornado,
    workload_by_segment,
)


@pytest.fixture(scope="module")
def d1():
    return build_dataset1()


def test_hours_year_matches_manual_formula(d1):
    r = roi_scenario(d1, "base")
    manual = (d1["est_handle_minutes"].sum() / 60) * (TICKETS_PER_YEAR / len(d1))
    assert r.hours_year == pytest.approx(manual, rel=1e-9)


def test_no_double_counting_full_deflection_kills_assist(d1):
    full = roi_scenario(d1, "base", deflection_by_type={t: 1.0 for t in DEFLECTION_BY_TYPE})
    assert full.assist_hours == pytest.approx(0.0, abs=1e-9)
    assert full.hours_saved == pytest.approx(full.hours_year, rel=1e-9)


def test_combined_less_than_sum_of_isolated_levers(d1):
    # prova de não-dupla-contagem: combinado < deflexão isolada + assistência isolada
    combined = roi_scenario(d1, "base")
    defl_only = roi_scenario(d1, "base", assist_reduction=0.0)
    assist_only = roi_scenario(d1, "base",
                               deflection_by_type={t: 0.0 for t in DEFLECTION_BY_TYPE})
    assert combined.hours_saved < defl_only.hours_saved + assist_only.hours_saved
    assert combined.hours_saved == pytest.approx(
        defl_only.hours_saved
        + assist_only.hours_saved * (1 - defl_only.deflected_hours / defl_only.hours_year),
        rel=1e-9,
    )


def test_savings_never_exceed_baseline_cost(d1):
    for s in ["low", "base", "high"]:
        r = roi_scenario(d1, s)
        assert r.hours_saved <= r.hours_year
        assert r.gross_savings_brl <= r.cost_year_brl


def test_zero_levers_save_nothing_and_cost_money(d1):
    r = roi_scenario(d1, "base",
                     deflection_by_type={t: 0.0 for t in DEFLECTION_BY_TYPE},
                     assist_reduction=0.0)
    assert r.hours_saved == pytest.approx(0.0, abs=1e-9)
    assert r.net_savings_year1_brl < 0
    assert r.payback_months == float("inf")  # sem economia, payback nunca chega


def test_ramp_up_only_affects_year1_not_steady(d1):
    lo = roi_scenario(d1, "base", ramp_up_year1=0.5)
    hi = roi_scenario(d1, "base", ramp_up_year1=0.8)
    assert lo.savings_year1_brl < hi.savings_year1_brl
    assert lo.net_savings_steady_brl == pytest.approx(hi.net_savings_steady_brl, rel=1e-12)


def test_steady_state_better_than_year1(d1):
    r = roi_scenario(d1, "base")
    assert r.net_savings_steady_brl > r.net_savings_year1_brl
    assert r.roi_steady > r.roi_year1


def test_internal_implementation_has_zero_incremental_cost_and_immediate_payback(d1):
    assert set(SOLUTION_IMPL_COST_BRL.values()) == {0.0}
    for name in BUSINESS_SCENARIOS:
        r = roi_business_scenario(d1, name)
        assert r.solution_cost_year1_brl == pytest.approx(r.run_cost_year_brl)
        expected = 0.0 if r.net_savings_year1_brl > 0 else float("inf")
        assert r.payback_months == expected


def test_volume_override_scales_linearly(d1):
    r1 = roi_scenario(d1, "base", tickets_year=30_000)
    r2 = roi_scenario(d1, "base", tickets_year=60_000)
    assert r2.hours_year == pytest.approx(2 * r1.hours_year, rel=1e-9)
    assert r2.gross_savings_brl == pytest.approx(2 * r1.gross_savings_brl, rel=1e-9)


def test_unknown_override_raises(d1):
    with pytest.raises(ValueError, match="overrides desconhecidos"):
        roi_scenario(d1, "base", tickets_per_year=30_000)  # nome antigo do kwarg


def test_business_scenarios_are_coherent_and_ordered(d1):
    cons = roi_business_scenario(d1, "conservador")
    base = roi_business_scenario(d1, "base")
    otim = roi_business_scenario(d1, "otimista")
    assert cons.net_savings_year1_brl < base.net_savings_year1_brl < otim.net_savings_year1_brl
    # conservador pareia economia-low com custo-high (≠ roi_scenario('low'))
    all_low = roi_scenario(d1, "low")
    assert cons.solution_cost_year1_brl > all_low.solution_cost_year1_brl
    assert set(BUSINESS_SCENARIOS) == {"conservador", "base", "otimista"}


def test_break_even_deflection_closes_the_model(d1):
    x = break_even_deflection(d1)
    assert 0 < x < 1
    r = roi_scenario(d1, "base",
                     deflection_by_type={t: x for t in DEFLECTION_BY_TYPE},
                     assist_reduction=0.0)
    assert r.net_savings_year1_brl == pytest.approx(0.0, abs=1.0)  # fecha em ~R$0


def test_workload_by_segment_totals(d1):
    w = workload_by_segment(d1)
    assert w["tickets_year"].sum() == pytest.approx(TICKETS_PER_YEAR, rel=1e-9)
    r = roi_scenario(d1, "base")
    assert w["hours_year"].sum() == pytest.approx(r.hours_year, rel=1e-6)


def test_tornado_has_all_premises_positive_amplitude(d1):
    t = sensitivity_tornado(d1)
    assert len(t) == 7
    assert "Custo de implantação" not in set(t["premissa"])
    assert (t["amplitude"] > 0).all()
    assert t["net_base"].nunique() == 1
