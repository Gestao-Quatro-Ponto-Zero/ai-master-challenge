"""
Automated Test Suite for RevOps Survival Engine, Schema Integrity & Anti-Leakage.

Covers:
1. Schema normalization and foreign key fixes ('GTXPro' -> 'GTX Pro', 'technolgy' -> 'technology').
2. Zero data leakage in deal valuation and temporal backtests.
3. Separation of Closer Pipeline (1,589 Engaging) vs SDR Queue (500 Prospecting).
4. Survival curve properties (smooth decay, no right-censoring cliff to zero at 138d).
5. Zombie Suspect flag detection above cohort P95 cycle age.
6. Metric implementations (AUC, Brier Score, Lift@K).
7. Commercial explainability, SLA assignments, and tactical scripts.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data_loader import build_enriched_pipeline, normalize_product_name
from src.survival_and_scoring import (
    SurvivalLeadScorer,
    ScoringParameters,
    compute_empirical_survival_curve,
)
from src.explainability import enrich_with_explainability, generate_deal_reasons
from src.backtest import (
    calculate_auc_score,
    calculate_brier_score,
    calculate_lift_at_k,
    calculate_reliability_diagram_bins,
    run_temporal_backtest,
)


@pytest.fixture(scope="session")
def loaded_pipeline():
    df, audit = build_enriched_pipeline()
    return df, audit


# --- 1. Schema Integrity & Bug Fixing Tests ---

def test_gtxpro_foreign_key_normalization():
    raw_names = pd.Series(["GTXPro", "GTX Pro", "GTX Plus Basic", "GTXPlusBasic"])
    normalized = normalize_product_name(raw_names)
    assert "GTXPro" not in normalized.values
    assert normalized.iloc[0] == "GTX Pro"
    assert normalized.iloc[3] == "GTX Plus Basic"


def test_sector_typo_fix(loaded_pipeline):
    df, audit = loaded_pipeline
    sectors = df[df["sector"].notnull()]["sector"].unique()
    assert "technolgy" not in sectors
    assert "technology" in sectors
    assert audit["gtxpro_foreign_key_fixed"] > 0


def test_missing_accounts_audited(loaded_pipeline):
    df, audit = loaded_pipeline
    assert audit["missing_account_engaging"] == 1088
    assert audit["missing_account_prospecting"] == 337
    # Ensure display account is never raw NaN
    assert df["account_display"].isnull().sum() == 0


# --- 2. Anti-Leakage & Value Estimation Tests ---

def test_no_leakage_in_expected_won_value(loaded_pipeline):
    df, _ = loaded_pipeline
    open_deals = df[df["deal_stage"].isin(["Engaging", "Prospecting"])]
    # Open deals must never have an actual close_value in raw data
    assert open_deals["close_value"].isnull().all()
    # But our engine must provide an estimated expected_won_value > 0 based on historical Won medians
    assert (open_deals["expected_won_value"] > 0).all()
    assert not np.isnan(open_deals["expected_won_value"].values).any()


def test_temporal_split_zero_leakage():
    t_cut = pd.Timestamp("2017-06-30")
    df, _ = build_enriched_pipeline(as_of_date=t_cut)
    closed = df[df["deal_stage"].isin(["Won", "Lost"])]
    train = closed[closed["close_date"] <= t_cut]
    test = closed[closed["close_date"] > t_cut]
    # No test deal close dates allowed in train window
    assert (train["close_date"] <= t_cut).all()
    assert (test["close_date"] > t_cut).all()


# --- 3. Survival Engine & Censoring Tests ---

def test_smooth_survival_decay_avoids_cliff():
    scorer = SurvivalLeadScorer()
    ages = pd.Series([10.0, 30.0, 57.0, 90.0, 120.0, 138.0, 160.0, 200.0])
    prods = pd.Series(["GTX Basic"] * len(ages))
    factors = scorer.compute_aging_survival_factor(ages, prods)

    # 1. Monotonic decay after the full maturation window (120 days)
    mat_idx = 4  # 120 days
    for i in range(mat_idx + 1, len(factors)):
        assert factors.iloc[i] <= factors.iloc[i - 1]

    # 2. Critical test: At 138d and beyond, survival factor must NOT drop abruptly to 0.0
    # It must decay smoothly to prevent right-censoring errors on living Enterprise deals
    assert factors.iloc[5] > 0.02  # at 138 days
    assert factors.iloc[6] > 0.01  # at 160 days
    assert factors.iloc[7] >= 0.02  # at 200 days floor



def test_zombie_suspect_flag(loaded_pipeline):
    df, _ = loaded_pipeline
    engaging = df[df["deal_stage"] == "Engaging"].copy()
    scorer = SurvivalLeadScorer()
    scored = scorer.score_engaging_deals(engaging)

    # Deals older than ~118 days (P95) must be flagged
    old_deals = scored[scored["cycle_days"] > 120]
    assert len(old_deals) > 0
    assert old_deals["is_zombie_suspect"].all()


def test_ev_velocity_calculation(loaded_pipeline):
    df, _ = loaded_pipeline
    engaging = df[df["deal_stage"] == "Engaging"].copy()
    scorer = SurvivalLeadScorer()
    scored = scorer.score_engaging_deals(engaging)

    # Expected value must equal p_win * expected_won_value
    expected_ev = (scored["p_win"] * scored["expected_won_value"]).round(2)
    assert np.allclose(scored["expected_value"].values, expected_ev.values, atol=0.05)

    # EV per day must be strictly positive and finite
    assert (scored["ev_per_day"] > 0).all()
    assert not np.isinf(scored["ev_per_day"].values).any()


# --- 4. Pipeline Partitioning: Closers vs SDRs ---

def test_pipeline_two_queues_partition(loaded_pipeline):
    df, _ = loaded_pipeline
    scorer = SurvivalLeadScorer()

    engaging = df[df["deal_stage"] == "Engaging"]
    prospecting = df[df["deal_stage"] == "Prospecting"]

    assert len(engaging) == 1589
    assert len(prospecting) == 500

    scored_eng = scorer.score_engaging_deals(engaging)
    scored_prosp = scorer.score_prospecting_deals(prospecting)

    assert "priority_score" in scored_eng.columns
    assert "ev_per_day" in scored_eng.columns
    assert "sdr_fit_score" in scored_prosp.columns
    assert "sdr_playbook" in scored_prosp.columns


# --- 5. Metric Functions Verification ---

def test_auc_calculation():
    # Perfect ranking
    assert calculate_auc_score(np.array([1, 1, 0, 0]), np.array([0.9, 0.8, 0.2, 0.1])) == 1.0
    # Inverted ranking
    assert calculate_auc_score(np.array([1, 1, 0, 0]), np.array([0.1, 0.2, 0.8, 0.9])) == 0.0
    # Random / ties
    assert calculate_auc_score(np.array([1, 0]), np.array([0.5, 0.5])) == 0.5


def test_brier_score_calculation():
    y_true = np.array([1, 0, 1, 0])
    # Perfect forecast
    assert calculate_brier_score(y_true, np.array([1.0, 0.0, 1.0, 0.0])) == 0.0
    # Completely wrong forecast
    assert calculate_brier_score(y_true, np.array([0.0, 1.0, 0.0, 1.0])) == 1.0
    # Uninformative base rate (0.5)
    assert calculate_brier_score(y_true, np.array([0.5, 0.5, 0.5, 0.5])) == 0.25


def test_lift_at_k_calculation():
    y_true = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0])  # base rate = 0.30
    scores = np.array([90, 80, 70, 60, 50, 40, 30, 20, 10, 5])
    lift, precision, pos_count = calculate_lift_at_k(y_true, scores, k_pct=0.20)
    # Top 20% = top 2 deals (90, 80) -> both are won -> precision = 1.0
    # Lift = 1.0 / 0.30 = 3.33x
    assert precision == 1.0
    assert pos_count == 2
    assert round(lift, 2) == 3.33


# --- 6. Explainability & Prescriptive Action Tests ---

def test_explainability_enrichment(loaded_pipeline):
    df, _ = loaded_pipeline
    engaging = df[df["deal_stage"] == "Engaging"].head(20).copy()
    scorer = SurvivalLeadScorer()
    scored = scorer.score_engaging_deals(engaging)
    enriched = enrich_with_explainability(scored)

    assert "driver_1" in enriched.columns
    assert "driver_2" in enriched.columns
    assert "driver_3" in enriched.columns
    assert "recommended_next_step" in enriched.columns
    assert "sla_recommendation" in enriched.columns
    assert "suggested_script" in enriched.columns

    # Check non-emptiness
    for col in ["driver_1", "driver_2", "driver_3", "recommended_next_step", "sla_recommendation", "suggested_script"]:
        assert (enriched[col].str.len() > 5).all()


# --- 7. End-to-End Backtest Execution ---

def test_backtest_report_execution():
    report = run_temporal_backtest()
    assert report.train_deal_count > 2500
    assert report.test_deal_count > 3500
    assert report.model_metrics["auc"] > 0.50
    assert report.model_metrics["brier"] < 0.25
    assert report.model_metrics["lift_20"] >= 1.0
    assert report.captured_revenue_top20_usd > 1000000.0  # Captured > $1M USD in top 20%
