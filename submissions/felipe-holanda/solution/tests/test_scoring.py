import numpy as np
import pandas as pd
import pytest

from lead_scorer import load, reference_date, score_pipeline
from lead_scorer.scoring import (HORIZON_DAYS, LANE_FOCUS, LANE_PROSPECT, LANE_REVIEW, TIMING_POINTS,
                                 VALUE_POINTS, build_curves, split_at, value_points)


def _deal(i, stage, engage=None, close=None, value=0, price=1000, agent="A"):
    return dict(opportunity_id=f"D{i}", sales_agent=agent, manager="M", regional_office="R",
                product="P", sales_price=price, account=None, sector=None, deal_stage=stage,
                engage_date=pd.Timestamp(engage) if engage else pd.NaT,
                close_date=pd.Timestamp(close) if close else pd.NaT, close_value=value)


@pytest.fixture(scope="module")
def real():
    deals, _ = load()
    return deals


def test_data_quality_fixes_applied(real):
    assert "GTXPro" not in set(real["product"])
    assert real["sales_price"].notna().all()


def test_reference_date_is_last_crm_event(real):
    assert reference_date(real) == pd.Timestamp("2017-12-31")


def test_split_does_not_leak_future():
    deals = pd.DataFrame([
        _deal(1, "Won", "2017-01-01", "2017-02-01", 900),
        _deal(2, "Lost", "2017-01-10", "2017-03-15"),  # ainda aberto em 01/03
    ])
    closed, open_ = split_at(deals, "2017-03-01")
    assert list(closed["opportunity_id"]) == ["D1"]
    assert list(open_["opportunity_id"]) == ["D2"]
    assert open_.iloc[0]["age_days"] == (pd.Timestamp("2017-03-01") - pd.Timestamp("2017-01-10")).days


def test_ripeness_counts_open_deals_as_not_closed():
    # 40 deals ganhos em exatamente 10 dias
    closed = pd.DataFrame({"cycle_days": [10] * 40, "won": [1] * 40})
    only_closed = build_curves(closed)
    with_stuck = build_curves(closed, open_ages=[200] * 40)  # 40 deals empacados há 200 dias
    assert only_closed.ripeness[0] == pytest.approx(1.0)
    assert with_stuck.ripeness[0] == pytest.approx(0.5)


def test_value_points_are_log_scaled():
    pts = value_points([55, 550, 26768], 55, 26768)
    assert pts[0] == 0 and pts[2] == VALUE_POINTS
    assert 20 < pts[1] < 25  # 10x o menor preço ~ 37% da escala log


def test_lanes_and_score_bounds(real):
    scored, curves = score_pipeline(real, reference_date(real))
    assert scored["score"].between(0, VALUE_POINTS + TIMING_POINTS).all()
    review = scored[scored["lane"] == LANE_REVIEW]
    assert (review["age_days"] > curves.max_cycle).all()
    assert (scored.loc[scored["lane"] == LANE_PROSPECT, "stage"] == "Prospecting").all()
    focus = scored[scored["lane"] == LANE_FOCUS]
    assert (focus["age_days"] <= curves.max_cycle).all()
    assert focus["score"].is_monotonic_decreasing


def test_every_deal_explains_itself(real):
    scored, _ = score_pipeline(real, reference_date(real))
    assert scored["reasons"].map(len).min() >= 2
    assert scored["action"].notna().all()


def test_same_value_ripe_deal_beats_stale_deal(real):
    scored, curves = score_pipeline(real, reference_date(real))
    focus = scored[(scored["lane"] == LANE_FOCUS) & (scored["product"] == "GTX Pro")]
    peak = focus.loc[(focus["age_days"] - curves.peak_age).abs().idxmin()]
    late = focus.loc[focus["age_days"].idxmax()]
    assert peak["score"] > late["score"]


def test_backtest_beats_value_only(real):
    from lead_scorer.backtest import run_backtest, summarize
    s = summarize(run_backtest(real))
    assert s.loc["Lead Scorer (valor + momento)", "revenue_captured"] > s.loc["Só valor de lista", "revenue_captured"]
    assert s.loc["Lead Scorer (valor + momento)", "hit_rate"] > s.loc["Só valor de lista", "hit_rate"]
    assert HORIZON_DAYS == 30 and np.isfinite(s.values).all()


def test_build_payload_has_proof_and_health_without_future(real):
    from lead_scorer.build import build_payload
    from lead_scorer.data import load as load_all
    deals, teams = load_all()
    payload = build_payload(deals, teams, "2017-09-30")
    # só segundas-feiras cujo mês seguinte já aconteceu até a data de corte
    assert all(s["asOf"] <= "2017-08-31" for s in payload["timeTravel"])
    assert payload["health"][-1]["date"] == "2017-09-30"
    first = payload["timeTravel"][0]
    assert set(first["compare"]) == {"Lead Scorer (valor + momento)", "Só valor de lista", "Aleatório"}
    assert {r[8] for r in first["rows"]} <= {"won30", "won_later", "lost", "open"}


def test_naive_forecast_ignores_age_and_overstates(real):
    from lead_scorer.build import pipeline_health
    last = pipeline_health(real, reference_date(real))[-1]
    assert last["naiveForecast"] > 10 * last["ageAwareForecast"]
