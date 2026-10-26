"""
Behavioral, Anti-Leakage Mutation & Invariance Test Suite.

Designed so every test name corresponds to a concrete regression detector:
1. Mutation-based temporal anti-leakage (corrupting post-cutoff outcomes must not alter past scores).
2. Separation of CRM missing-account hygiene from statistical win probability (snapshot-leakage guard).
3. Row-permutation invariance by `opportunity_id`.
4. Exact numerical parity between `score_single_deal_simulation` (UI Sandbox) and batch `score_engaging_deals`.
5. Functional salesperson overrides reordering the operational queue while preserving `p_win_90d` and `ev_90d`.
6. Dual-regime backtest integrity and neutral tie-breaking.
7. Schema sanitization (`GTXPro`, `technolgy`), regional funnel audit, and empty-history fallback.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data_loader import (
    build_enriched_pipeline,
    load_raw_tables,
    normalize_product_name,
)
from src.survival_and_scoring import (
    EmpiricalHorizonScorer,
    apply_rep_overrides,
    compute_age_stage_distribution,
    score_single_deal_simulation,
)
from src.explainability import enrich_with_explainability
from src.backtest import (
    calculate_auc_score,
    calculate_brier_score,
    calculate_lift_at_k,
    run_conditional_resolved_evaluation,
    run_multi_cutoff_queue_evaluation,
    run_prospective_queue_backtest,
)


@pytest.fixture(scope="session")
def loaded_pipeline():
    df, audit = build_enriched_pipeline()
    return df, audit


# --- 1. Schema Integrity & Empirical CRM Audit Tests ---


def test_gtxpro_foreign_key_normalization():
    raw_names = pd.Series(["GTXPro", "GTX Pro", "GTX Plus Basic", "GTXPlusBasic"])
    normalized = normalize_product_name(raw_names)
    assert "GTXPro" not in normalized.values
    assert normalized.iloc[0] == "GTX Pro"
    assert normalized.iloc[3] == "GTX Plus Basic"


def test_schema_anomalies_and_regional_funnel_audit(loaded_pipeline):
    df, audit = loaded_pipeline
    sectors = df[df["sector"].notnull()]["sector"].unique()
    assert "technolgy" not in sectors
    assert "technology" in sectors
    assert audit["gtxpro_foreign_key_fixed"] == 1480

    # Closing-time schema artifact: 0 closed deals lack account, vs 1,088 Engaging & 337 Prospecting
    assert audit["closed_missing_account_count"] == 0
    assert audit["missing_account_engaging"] == 1088
    assert audit["missing_account_prospecting"] == 337

    # Regional funnel asymmetry: 100% of Prospecting deals belong to Central; 30 active + 5 zero-deal agents
    assert audit["prospecting_central_share_pct"] == 100.0
    assert audit["active_agents_count"] == 30
    assert len(audit["inactive_agents_in_teams"]) == 5


# --- 2. True Mutation-Based Anti-Leakage & Snapshot-Leakage Guard Tests ---


def test_mutating_future_outcomes_never_changes_past_predictions():
    """
    Corrupts ALL post-cutoff outcomes (flipping Won <-> Lost, multiplying close_value by 100x,
    and injecting synthetic future deals) and asserts bit-for-bit identical predictions at cutoff.
    """
    t_cut = pd.Timestamp("2017-08-31")
    raw_clean = load_raw_tables()

    df_clean, _ = build_enriched_pipeline(
        as_of_date=t_cut, tables_override=raw_clean
    )
    scorer_clean = EmpiricalHorizonScorer().fit(df_clean, as_of_date=t_cut)
    open_clean = df_clean[
        df_clean["engage_date"].notnull()
        & (df_clean["engage_date"] <= t_cut)
        & ((df_clean["close_date"] > t_cut) | df_clean["close_date"].isnull())
    ].copy()
    scored_clean = (
        scorer_clean.score_engaging_deals(open_clean)
        .sort_values("opportunity_id")
        .reset_index(drop=True)
    )

    # Sabotage future records in a deep copy of raw tables
    sabotaged_pip = raw_clean["pipeline"].copy()
    future_close_mask = sabotaged_pip["close_date"].notnull() & (
        sabotaged_pip["close_date"] > t_cut
    )
    assert future_close_mask.sum() > 1500

    sabotaged_pip.loc[future_close_mask, "deal_stage"] = np.where(
        sabotaged_pip.loc[future_close_mask, "deal_stage"] == "Won", "Lost", "Won"
    )
    sabotaged_pip.loc[future_close_mask, "close_value"] = (
        sabotaged_pip.loc[future_close_mask, "close_value"].fillna(500.0) * 100.0
    )

    # Inject synthetic post-cutoff deals
    extra_future = sabotaged_pip.head(30).copy()
    extra_future["opportunity_id"] = [f"FUT-{i:03d}" for i in range(30)]
    extra_future["engage_date"] = pd.Timestamp("2017-10-05")
    extra_future["close_date"] = pd.Timestamp("2017-11-15")
    extra_future["deal_stage"] = "Won"
    extra_future["close_value"] = 999999.0
    sabotaged_pip = pd.concat([sabotaged_pip, extra_future], ignore_index=True)

    raw_sabotaged = {
        "pipeline": sabotaged_pip,
        "accounts": raw_clean["accounts"].copy(),
        "products": raw_clean["products"].copy(),
        "teams": raw_clean["teams"].copy(),
    }

    df_sab, _ = build_enriched_pipeline(
        as_of_date=t_cut, tables_override=raw_sabotaged
    )
    scorer_sab = EmpiricalHorizonScorer().fit(df_sab, as_of_date=t_cut)
    open_sab = df_sab[
        df_sab["engage_date"].notnull()
        & (df_sab["engage_date"] <= t_cut)
        & ((df_sab["close_date"] > t_cut) | df_sab["close_date"].isnull())
    ].copy()
    scored_sab = (
        scorer_sab.score_engaging_deals(open_sab)
        .sort_values("opportunity_id")
        .reset_index(drop=True)
    )

    assert list(scored_clean["opportunity_id"]) == list(scored_sab["opportunity_id"])
    for col in ["cycle_days", "expected_won_value", "p_age_90d", "p_win_90d", "ev_90d"]:
        assert np.allclose(
            scored_clean[col].values, scored_sab[col].values, atol=1e-12
        ), f"Future leakage detected in column {col}!"


def test_missing_account_separated_from_win_probability(loaded_pipeline):
    """
    Verifies that removing `account` flags a CRM hygiene task WITHOUT distorting `p_win_90d` or `ev_90d`.
    """
    df, _ = loaded_pipeline
    scorer = EmpiricalHorizonScorer().fit(df)

    linked_sample = (
        df[(df["deal_stage"] == "Engaging") & df["has_account"]].head(50).copy()
    )
    unlinked_clone = linked_sample.copy()
    unlinked_clone["account"] = np.nan
    unlinked_clone["has_account"] = False
    unlinked_clone["account_display"] = "⚠️ Conta Não Vinculada (CRM Gap)"
    unlinked_clone["crm_hygiene_status"] = "⚠️ Sem Conta (Enriquecer CRM)"

    s_linked = scorer.score_engaging_deals(linked_sample).sort_values("opportunity_id")
    s_unlinked = scorer.score_engaging_deals(unlinked_clone).sort_values(
        "opportunity_id"
    )

    assert np.allclose(s_linked["p_win_90d"].values, s_unlinked["p_win_90d"].values, atol=1e-12)
    assert np.allclose(s_linked["ev_90d"].values, s_unlinked["ev_90d"].values, atol=1e-12)
    assert (s_linked["crm_hygiene_status"] == "✅ Conta Vinculada").all()
    assert (s_unlinked["crm_hygiene_status"] == "⚠️ Sem Conta (Enriquecer CRM)").all()


# --- 3. Row-Permutation Invariance & Two-Path Simulator Parity Tests ---


def test_row_permutation_invariance_by_opportunity_id(loaded_pipeline):
    """Shuffling input rows must produce identical scores and exact identical ranking order."""
    df, _ = loaded_pipeline
    scorer = EmpiricalHorizonScorer().fit(df)
    engaging = df[df["deal_stage"] == "Engaging"].copy()
    shuffled = engaging.sample(frac=1.0, random_state=2026).copy()

    res_orig = scorer.score_engaging_deals(engaging)
    res_shuf = scorer.score_engaging_deals(shuffled)

    assert list(res_orig["opportunity_id"]) == list(res_shuf["opportunity_id"])
    assert np.allclose(res_orig["ev_90d"].values, res_shuf["ev_90d"].values, atol=1e-12)
    assert np.allclose(res_orig["p_win_90d"].values, res_shuf["p_win_90d"].values, atol=1e-12)
    assert list(res_orig["action_tier"]) == list(res_shuf["action_tier"])


def test_simulator_and_batch_scorer_exact_parity(loaded_pipeline):
    """
    Compares batch `score_engaging_deals` against single-deal `score_single_deal_simulation`
    across 20 real Engaging deals of diverse products, ages, and account states.
    """
    df, _ = loaded_pipeline
    scorer = EmpiricalHorizonScorer().fit(df)
    sample_deals = (
        df[df["deal_stage"] == "Engaging"]
        .iloc[::75]
        .head(20)
        .copy()
    )
    batch_scored = scorer.score_engaging_deals(sample_deals).set_index("opportunity_id")

    for _, raw_row in sample_deals.iterrows():
        opp_id = str(raw_row["opportunity_id"])
        sim_row = score_single_deal_simulation(
            scorer=scorer,
            sales_agent=str(raw_row["sales_agent"]),
            product=str(raw_row["product"]),
            has_account=bool(raw_row["has_account"]),
            cycle_days=float(raw_row["cycle_days"]),
            expected_won_value=float(raw_row["expected_won_value"]),
            opportunity_id=opp_id,
            account_name=str(raw_row["account"]) if raw_row["has_account"] else None,
        )
        b_row = batch_scored.loc[opp_id]
        assert np.isclose(sim_row["p_win_90d"], b_row["p_win_90d"], atol=1e-9)
        assert np.isclose(sim_row["ev_90d"], b_row["ev_90d"], atol=1e-9)
        assert sim_row["action_tier"] == b_row["action_tier"]
        assert sim_row["crm_hygiene_status"] == b_row["crm_hygiene_status"]


# --- 4. Functional Rep Override & Queue Behavior Tests ---


def test_rep_override_reorders_queue_without_altering_statistical_estimate(loaded_pipeline):
    """
    Verifies that salesperson overrides (`promote`, `pause`, `archive`) actually move deals
    in the operational ranking while preserving `p_win_90d` and `ev_90d` untouched.
    """
    df, _ = loaded_pipeline
    scorer = EmpiricalHorizonScorer().fit(df)
    engaging = df[df["deal_stage"] == "Engaging"].head(40).copy()

    base_scored = scorer.score_engaging_deals(engaging)
    top_id = str(base_scored.iloc[0]["opportunity_id"])
    bottom_id = str(base_scored.iloc[-1]["opportunity_id"])

    overrides = {
        bottom_id: {"disposition": "promote", "reason": "Minuta aprovada pelo CFO"},
        top_id: {"disposition": "archive", "reason": "Cliente fechou com concorrente"},
    }
    overridden = scorer.score_engaging_deals(engaging, overrides=overrides)

    # Promoted deal moves to #1; archived deal moves to the very end
    assert str(overridden.iloc[0]["opportunity_id"]) == bottom_id
    assert overridden.iloc[0]["operational_rank_group"] == 0
    assert "Override" in str(overridden.iloc[0]["action_tier"])

    assert str(overridden.iloc[-1]["opportunity_id"]) == top_id
    assert overridden.iloc[-1]["operational_rank_group"] == 3

    # Statistical estimates must remain bit-for-bit identical!
    b_idx = base_scored.set_index("opportunity_id")
    o_idx = overridden.set_index("opportunity_id")
    assert np.allclose(b_idx["p_win_90d"].values, o_idx.loc[b_idx.index, "p_win_90d"].values, atol=1e-12)
    assert np.allclose(b_idx["ev_90d"].values, o_idx.loc[b_idx.index, "ev_90d"].values, atol=1e-12)


# --- 5. Age Curve Continuity, Empty History Fallback & Prospecting Triage ---


def test_age_curve_continuity_and_stale_decay(loaded_pipeline):
    df, _ = loaded_pipeline
    scorer = EmpiricalHorizonScorer().fit(df)
    ages = pd.Series(np.arange(0.0, 180.0, 1.0))
    probs = scorer.predict_age_90d_prob(ages)

    # Day-to-day step must be continuous (no sudden >3pp jump in 24h)
    diffs = np.abs(np.diff(probs.values))
    assert diffs.max() < 0.03

    # Active window (~45d) must clearly exceed >150d stale backlog
    assert probs.iloc[45] > 0.35
    assert probs.iloc[165] < 0.05


def test_empty_history_fallback():
    t_early = pd.Timestamp("2016-01-01")
    df, _ = build_enriched_pipeline(as_of_date=t_early)
    scorer = EmpiricalHorizonScorer().fit(df, as_of_date=t_early)
    assert scorer.fitted_snapshot_count_ == 0
    assert df["expected_won_value"].notnull().all()
    assert (df["expected_won_value"] > 0).all()


def test_prospecting_deterministic_triage_and_explainability(loaded_pipeline):
    df, _ = loaded_pipeline
    scorer = EmpiricalHorizonScorer().fit(df)

    engaging = df[df["deal_stage"] == "Engaging"].head(15).copy()
    prospecting = df[df["deal_stage"] == "Prospecting"].copy()

    scored_prosp = scorer.score_prospecting_deals(prospecting)
    assert len(scored_prosp) == 500
    # Linked accounts come strictly before unlinked accounts in operational triage
    first_unlinked_idx = scored_prosp.index[~scored_prosp["has_account"]][0]
    last_linked_idx = scored_prosp.index[scored_prosp["has_account"]][-1]
    assert last_linked_idx < first_unlinked_idx

    enriched = enrich_with_explainability(scorer.score_engaging_deals(engaging))
    for col in ["driver_1", "driver_2", "driver_3", "recommended_next_step", "sla_recommendation"]:
        assert (enriched[col].str.len() > 10).all()

    dist = compute_age_stage_distribution(df, pd.Timestamp("2017-12-31"))
    assert "open_unclosed_share" in dist.columns
    assert float(dist.loc[dist["age_threshold_days"] == 180, "open_unclosed_share"].iloc[0]) == 1.0


# --- 6. Metric Functions & Dual-Regime Backtest Integrity ---


def test_metric_functions():
    assert calculate_auc_score(np.array([1, 1, 0, 0]), np.array([0.9, 0.8, 0.2, 0.1])) == 1.0
    assert calculate_auc_score(np.array([1, 1, 0, 0]), np.array([0.1, 0.2, 0.8, 0.9])) == 0.0
    assert calculate_brier_score(np.array([1, 0, 1, 0]), np.array([0.5, 0.5, 0.5, 0.5])) == 0.25
    lift, prec, pos = calculate_lift_at_k(
        np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0]),
        np.array([90, 80, 70, 60, 50, 40, 30, 20, 10, 5]),
        k_pct=0.20,
    )
    assert prec == 1.0 and pos == 2 and round(lift, 2) == 3.33


def test_dual_regime_backtest_honesty_and_alignment():
    queue_reports = run_multi_cutoff_queue_evaluation()
    assert [r.open_queue_count for r in queue_reports] == [2257, 2265, 2409]

    for rep in queue_reports:
        ev_share = rep.strategies["ev_90d_full"]["rev_20_share_pct"]
        price_share = rep.strategies["nominal_price"]["rev_20_share_pct"]
        fresh_share = rep.strategies["freshness"]["rev_20_share_pct"]
        assert ev_share > price_share
        assert ev_share > fresh_share
        assert ev_share >= 58.0

    cond = run_conditional_resolved_evaluation(split_date=pd.Timestamp("2017-06-30"))
    assert cond.open_total_at_split == 1686
    assert cond.resolved_deal_count == 970
    assert cond.censored_excluded_count == 716
    # Conditional resolved subset honestly reflects flat static-CRM discrimination (~0.48 - 0.53)
    assert 0.45 <= cond.strategies["ev_90d_full"]["auc"] <= 0.55
    assert 0.45 <= cond.strategies["agent_closed_wr"]["auc"] <= 0.55


def test_streamlit_ui_renders_all_tabs_cleanly():
    """Executes the full Streamlit application headlessly via AppTest to catch UI/schema drift."""
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    app_path = str(Path(__file__).resolve().parent.parent / "app.py")
    at = AppTest.from_file(app_path, default_timeout=30)
    at.run()
    assert not at.exception, f"Streamlit UI raised exception: {at.exception}"
    assert len(at.tabs) == 4
    assert len(at.metric) >= 10
    assert len(at.dataframe) >= 2

