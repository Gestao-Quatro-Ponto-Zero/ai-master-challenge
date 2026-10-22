import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_reports_loaded_real_source_data():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "analysis": "loaded", "data": "source-csv"}


def test_analysis_exposes_unknown_metrics_and_real_counts():
    response = client.get("/api/analysis")
    assert response.status_code == 200
    data = response.json()
    assert data["record_counts"] == {
        "accounts": 500,
        "subscriptions": 5000,
        "usage": 25000,
        "tickets": 2000,
        "churn_events": 600,
    }
    assert data["metrics"]["logo_churn_rate"]["status"] == "UNKNOWN"
    assert data["metrics"]["gross_revenue_churn"]["value"] is None
    assert data["data_quality"]["event_accounts"] == 352
    assert len(data["monthly"]) == 24
    quality = data["data_quality"]
    assert quality["usage_duplicate_ids"] == 21
    assert quality["usage_rows_in_duplicate_id_groups"] == 42
    assert quality["usage_duplicate_excess_rows"] == 21


def test_business_investigation_has_label_cohorts_segments_and_unknown_revenue():
    response = client.get("/api/business-investigation")
    assert response.status_code == 200
    data = response.json()
    assert data["labels"]["account_positive_counts"] == {
        "account_flag": 110,
        "any_event": 352,
        "nonreactivation_event": 339,
        "subscription_flag_account": 312,
    }
    assert data["cohorts"]["status"] == "NOT_IDENTIFIABLE"
    assert data["cohorts"]["retention_heatmap"] is None
    assert data["cohorts"]["first_subscription_start_rows"]
    assert data["revenue"]["current_mrr_lost_revenue_grr_nrr_ltv_exposure"] is None
    assert data["usage"]["concentration"]["valid_interval_usage_rows"] == 5568
    assert data["usage"]["concentration"]["duplicate_usage_id_groups"] == 21
    assert len(data["account_investigation_candidates"]) == 30


def test_historical_churn_endpoint_exposes_conditional_date_reconstruction():
    response = client.get("/api/historical-churn")
    assert response.status_code == 200
    data = response.json()
    assert data["snapshots"]["2023-01-01"]["active_accounts"] == 0
    assert data["snapshots"]["2024-01-01"]["active_accounts"] == 191
    assert data["annual"]["2023"]["classical_logo_churn_rate_gross_exit"] is None
    assert data["annual"]["2024"]["classical_logo_churn_rate_gross_exit"] == 0
    assert data["annual"]["2024"]["opening_accounts_with_nonreactivation_event"] == 103
    assert data["annual"]["2024"]["opening_subscriptions_not_active_at_year_end"] == 66
    assert data["annual"]["2024"]["opening_subscriptions_with_churn_flag"] == 66
    assert data["annual"]["2024"]["movement_equation"]["residual"] == 0
    assert data["cohorts"]["status"] == "CONDITIONAL_DATE_RECONSTRUCTION"
    assert data["data_quality"]["invalid_nonpositive_subscription_intervals"] == 13
    assert len(data["monthly"]) == 24
    assert [row["month"] for row in data["monthly"] if row["gross_logo_exits_any_interval_gap"]] == ["2023-11", "2024-03", "2024-04", "2024-09"]


def test_g4_customer_churn_endpoint_keeps_primary_kpi_unknown_and_exposes_conditional_evidence():
    response = client.get("/api/g4-customer-churn")
    assert response.status_code == 200
    data = response.json()
    assert data["primary_customer_churn"]["classification"] == "C — CUSTOMER CHURN NOT IDENTIFIABLE"
    assert data["primary_customer_churn"]["value"] is None
    assert data["annual"]["2023"]["opening_active_accounts"] == 0
    assert data["annual"]["2024"]["opening_active_accounts"] == 191
    assert data["annual"]["2024"]["conditional_gross_date_churn_rate"] == 0
    assert data["annual"]["2024"]["opening_accounts_with_nonreactivation_event"] == 103
    assert data["annual"]["2024"]["nonreactivation_event_rows_with_active_subscription"] == 443
    assert data["reconciliation"]["movement_bridge"]["residual"] == 0
    assert len(data["cohorts"]["rows"]) == 300
    assert len(data["quarterly"]) == 8
    assert data["segments"]
    assert data["account_review_candidates"]
    assert "/api/g4-customer-churn" in client.get("/openapi.json").json()["paths"]


def test_contract_churn_endpoint_reconciles_subscription_and_account_grains():
    response = client.get("/api/contract-churn")
    assert response.status_code == 200
    data = response.json()
    counts = data["revalidation"]
    assert (counts["opening_accounts"], counts["opening_subscription_ids"]) == (191, 655)
    assert counts["subscription_rows_ended_before_2025_boundary"] == 66
    assert counts["distinct_accounts_in_66"] == 57
    assert counts["ended_subscriptions_with_another_active_at_end"] == 66
    assert counts["opening_accounts_with_any_2024_coverage_gap"] == 0
    assert counts["ended_accounts_active_at_2025_boundary"] == 57
    assert counts["events_with_any_active_subscription"] == 443
    assert counts["distinct_accounts_among_events_with_active_subscription"] == 302
    assert counts["events_with_multiple_active_subscriptions"] == 395
    assert data["reactivation_summary"]["event_rows"] == 55
    assert data["reactivation_summary"]["rows_with_active_subscription_on_event_date"] == 51
    assert data["reactivation_summary"]["rows_after_any_same_account_subscription_end"] == 20
    assert data["reactivation_summary"]["rows_with_later_same_account_subscription_start"] == 45
    assert data["reactivation_summary"]["distinct_accounts_in_2024_opening_base"] == 14
    assert counts["conflicting_events_near_same_account_end"]["within_30_days"] == 104
    assert len(data["ended_subscriptions"]) == 66
    assert len(data["conflicting_events"]) == 443
    assert all("subscription_id" in row for row in data["ended_subscriptions"])
    assert all("event_subscription_link" in row for row in data["conflicting_events"])
    assert data["financial_descriptives"]["sum_mrr_rows_not_current_revenue"] == 93159


def test_daily_portfolio_churn_exposes_plan_proxy_and_all_period_aggregations():
    response = client.get("/api/daily-portfolio-churn")
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["plan_identity"] == "PLAN-LEVEL PROXY"
    assert data["metadata"]["actual_product_identity"] == "NOT_IDENTIFIABLE"
    assert data["metadata"]["interval_rule"] == "[start_date, end_date); null end_date is right-censored through observation_end"
    assert data["metadata"]["observation_start"] == "2023-01-01"
    assert data["metadata"]["observation_end"] == "2024-12-31"
    assert data["metadata"]["earliest_subscription_start"] == "2023-01-09"
    assert len(data["daily"]) == 731
    assert {"WEEKLY", "MONTHLY", "QUARTERLY", "SEMIANNUAL", "ANNUAL"}.issubset(data["periods"])
    assert data["summary"]["invalid_intervals"] == 13
    assert data["summary"]["plan_relation_loss_events"] == 62
    assert data["summary"]["customer_churn_events"] == 8
    assert data["reconciliation"]["daily_plan_bridge_failures"] == []
    assert data["reconciliation"]["daily_customer_bridge_failures"] == []
    assert data["event_reconciliation"]["event_rows"] == 600
    assert data["event_reconciliation"]["ambiguous_account_only_linkage"] is True
    assert data["financial_metrics"]["status"] == "UNKNOWN"
    moments = data["key_moments"]["moments"]
    rate_peak = next(row for row in moments if row["type"] == "RATE_PEAK")
    volume_peak = next(row for row in moments if row["type"] == "LOSS_VOLUME_PEAK")
    october = next(row for row in moments if row["type"] == "RATE_PEAK" and row["month"] == "2024-10")
    december = next(row for row in moments if row["type"] == "LOSS_VOLUME_PEAK" and row["month"] == "2024-12")
    assert rate_peak["month"] == "2024-10"
    assert october["numerator"] == 9 and october["denominator"] == 1073
    assert october["value"] == pytest.approx(0.83877, abs=0.00001)
    assert volume_peak["month"] == "2024-12"
    assert december["numerator"] == 11
    assert december["comparison"]["opening_cohort_losses"] == 5
    assert december["comparison"]["opening_denominator"] == 1279
    assert data["key_moments"]["months_analyzed"] == 24
    assert "/api/daily-portfolio-churn" in client.get("/openapi.json").json()["paths"]


def test_event_contract_does_not_invent_subscription_foreign_keys():
    response = client.get("/api/contract-churn")
    assert response.status_code == 200
    row = response.json()["conflicting_events"][0]
    assert "subscription_id" not in row
    assert row["event_subscription_link"].startswith("UNKNOWN:")


def test_key_moment_selector_excludes_undefined_rates_and_retains_ties():
    from key_moments import build_key_moments

    periods = []
    for month, opening, lost, gross in [
        ("2023-01", 0, 0, 0),
        ("2023-02", 10, 2, 2),
        ("2023-03", 20, 4, 4),
        ("2023-04", 10, 2, 2),
    ]:
        periods.append({
            "period": month,
            "opening_plan_relations": opening,
            "opening_relations_lost_any_time": lost,
            "opening_cohort_churn_any_pct": lost / opening * 100 if opening else None,
            "gross_plan_relation_loss_events": gross,
            "opening_relations_lost_at_close": lost,
            "opening_customers": 0,
            "opening_customers_lost_any_time": 0,
            "opening_customers_lost_at_close": 0,
            "gross_customer_churn_events": 0,
            "new_customers": 0,
            "new_plan_relationships": 0,
            "customer_reactivations": 0,
            "plan_reactivations": 0,
            "portfolio_contraction_events": 0,
            "possible_downgrade_candidates": 0,
            "plan_segments": [],
            "account_segments": {},
        })
    result = build_key_moments({"periods": {"MONTHLY": periods}, "movements": []})
    peaks = [row for row in result["moments"] if row["type"] == "RATE_PEAK"]
    assert [row["month"] for row in peaks] == ["2023-02", "2023-03", "2023-04"]
    assert all(row["denominator"] > 0 for row in peaks)
    assert all("2023-01" not in row["month"] for row in peaks)


def test_support_comparison_preserves_ticket_denominators_and_caveats():
    response = client.get("/api/analysis")
    assert response.status_code == 200
    groups = {row["group"]: row for row in response.json()["support_comparison"]}
    assert groups["accounts_with_any_event"]["first_response_n"] == groups["accounts_with_any_event"]["ticket_rows"]
    assert groups["accounts_with_any_event"]["resolution_n"] == groups["accounts_with_any_event"]["ticket_rows"]
    assert groups["accounts_with_any_event"]["escalation_n"] == groups["accounts_with_any_event"]["ticket_rows"]
    assert groups["accounts_without_event"]["accounts"] > 0
    event_group = groups["accounts_with_any_event"]
    no_event_group = groups["accounts_without_event"]
    assert (event_group["satisfaction_n"], event_group["satisfaction_missing"]) == (815, 580)
    assert event_group["satisfaction_mean"] == 3.9804
    assert (no_event_group["satisfaction_n"], no_event_group["satisfaction_missing"]) == (360, 245)
    assert no_event_group["satisfaction_mean"] == 3.9833


def test_reconciliation_accounts_are_not_risk_scores():
    response = client.get("/api/accounts/reconciliation?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["returned"] == 5
    assert "not an account risk score" in data["accounts"][0]["interpretation"].lower()
    assert "not a revenue exposure" in data["warning"]


def test_scenario_is_explicitly_hypothetical_and_calculates_assumptions():
    response = client.post(
        "/api/scenarios/retention",
        json={
            "eligible_accounts": 100,
            "operational_capacity": 50,
            "budget": 2500,
            "cost_per_contact": 100,
            "assumed_effectiveness": 0.1,
            "assumed_monthly_value_per_retained_account": 500,
            "retention_horizon_months": 3,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HYPOTHETICAL"
    assert data["selected_accounts"] == 25
    assert data["currency_unit"] == "user-supplied units"
    assert data["hypothetical_incremental_retained_accounts"] == 2.5
    assert data["intervention_cost"] == 2500
    assert data["hypothetical_retained_value"] == 3750
    assert data["hypothetical_net_value"] == 1250
    assert data["sensitivity"]["low_net_value"] == -1562.5
    assert data["scenario_cases"]["conservative"]["expected_participants"] == 12.5
    assert data["scenario_cases"]["conservative"]["hypothetical_incremental_retained_accounts"] == 0.625
    assert data["scenario_cases"]["base"]["hypothetical_net_value"] == 1250
    assert any("incremental percentage-point" in item for item in data["limitations"])


def test_scenario_requires_user_supplied_value_for_value_estimate():
    response = client.post(
        "/api/scenarios/retention",
        json={
            "eligible_accounts": 50,
            "operational_capacity": 10,
            "budget": 1000,
            "cost_per_contact": 100,
            "assumed_effectiveness": 0.1,
            "assumed_monthly_value_per_retained_account": 0,
            "retention_horizon_months": 6,
        },
    )
    assert response.status_code == 200
    assert response.json()["hypothetical_retained_value"] is None
    assert response.json()["hypothetical_net_value"] is None


def test_invalid_scenario_is_rejected():
    response = client.post(
        "/api/scenarios/retention",
        json={
            "eligible_accounts": 501,
            "operational_capacity": 10,
            "budget": -1,
            "cost_per_contact": 100,
            "assumed_effectiveness": 1.5,
            "assumed_monthly_value_per_retained_account": 500,
            "retention_horizon_months": 6,
        },
    )
    assert response.status_code == 422


def test_scenario_uptake_and_three_cases_are_explicit():
    response = client.post(
        "/api/scenarios/retention",
        json={
            "eligible_accounts": 20,
            "operational_capacity": 20,
            "budget": 2000,
            "cost_per_contact": 100,
            "assumed_uptake_pct": 0.5,
            "assumed_effectiveness": 0.1,
            "assumed_monthly_value_per_retained_account": 500,
            "retention_horizon_months": 3,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["selected_accounts"] == 20
    assert data["expected_participants"] == 10
    assert data["hypothetical_incremental_retained_accounts"] == 1
    assert data["hypothetical_retained_value"] == 1500
    assert data["hypothetical_net_value"] == -500
    assert set(data["scenario_cases"]) == {"conservative", "base", "optimistic"}
    assert data["scenario_cases"]["conservative"]["assumed_uptake_pct"] == 25
    assert data["scenario_cases"]["base"]["expected_participants"] == 10
    assert data["scenario_cases"]["optimistic"]["assumed_incremental_lift_pct_points"] == 15
    assert any("not confidence intervals" in item for item in data["limitations"])


def _monthly_lab_payload(month="2024-01"):
    row = next(item for item in client.get("/api/daily-portfolio-churn").json()["periods"]["MONTHLY"] if item["period"] == month)
    return {
        "month": month,
        "opening_customers": row["opening_customers"],
        "new_customers": row["new_customers"],
        "customer_loss_events": row["gross_customer_churn_events"],
        "customer_reactivations": row["customer_reactivations"],
        "opening_customer_loss_any": row["opening_customers_lost_any_time"],
        "opening_customer_loss_at_close": row["opening_customers_lost_at_close"],
        "portfolio_expansions": row["portfolio_expansion_events"],
        "portfolio_contractions": row["portfolio_contraction_events"],
        "possible_upgrades": row["possible_upgrade_candidates"],
        "possible_downgrades": row["possible_downgrade_candidates"],
        "assumed_customer_monthly_value": 300,
        "assumed_acquisition_cost_per_customer": 20,
        "assumed_retention_cost_per_account": 15,
        "assumed_uptake_pct": 0.5,
        "assumed_incremental_retention_lift_pct": 0.1,
        "horizon_months": 6,
        "plans": [{
            "plan_tier": plan["plan_tier"],
            "opening_relations": plan["opening_relations"],
            "new_relations": plan["new_relations"],
            "loss_events": plan["gross_loss_events"],
            "reactivations": plan["reactivations"],
            "opening_cohort_loss_any": plan["opening_relations_lost_any_time"],
            "opening_cohort_loss_at_close": plan["opening_relations_lost_at_close"],
            "assumed_monthly_value": 100,
        } for plan in row["plan_segments"]],
    }


def test_monthly_lab_keeps_observed_baseline_and_calculates_scenario_separately():
    payload = _monthly_lab_payload()
    response = client.post("/api/monthly-lab/scenario", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    observed = data["observed_baseline"]
    scenario = data["scenario"]
    assert data["status"] == "SCENARIO_ONLY"
    assert data["evidence_classification"].startswith("HYPOTHETICAL_USER_ASSUMPTIONS")
    actual = next(row for row in client.get("/api/daily-portfolio-churn").json()["periods"]["MONTHLY"] if row["period"] == "2024-01")
    assert observed["closing_plan_relations"] == actual["closing_plan_relations"]
    assert scenario["closing_plan_relations"] == scenario["opening_plan_relations"] + scenario["new_plan_relationships"] + scenario["plan_reactivations"] - scenario["plan_loss_events"]
    assert scenario["closing_customers"] == scenario["opening_customers"] + scenario["new_customers"] + scenario["customer_reactivations"] - scenario["customer_loss_events"]
    assert scenario["financial_model_status"] == "USER_ASSUMPTIONS_ONLY"
    assert scenario["scenario_cases"]["base"]["modeled_net_contribution"] is not None
    assert data["comparison"]["monthly_modeled_run_rate_vs_observed"].startswith("NOT_COMPARABLE")
    assert data["comparison"]["plan_closing_base_delta_pct"] == 0
    assert data["comparison"]["customer_loss_events_delta_pct"] == 0


def test_monthly_lab_rejects_impossible_counts_and_edited_observed_opening():
    payload = _monthly_lab_payload()
    payload["plans"][0]["loss_events"] = 100000
    assert client.post("/api/monthly-lab/scenario", json=payload).status_code == 422
    payload = _monthly_lab_payload()
    payload["opening_customers"] += 1
    assert client.post("/api/monthly-lab/scenario", json=payload).status_code == 422


def test_monthly_lab_rejects_month_outside_observation():
    payload = _monthly_lab_payload()
    payload["month"] = "2025-01"
    response = client.post("/api/monthly-lab/scenario", json=payload)
    assert response.status_code == 404


def test_monthly_lab_keeps_zero_opening_denominator_undefined():
    response = client.post("/api/monthly-lab/scenario", json=_monthly_lab_payload("2023-01"))
    assert response.status_code == 200, response.text
    scenario = response.json()["scenario"]
    assert scenario["customer_cohort_gross_loss_rate_pct"] is None
    assert scenario["plan_cohort_gross_loss_rate_pct"] is None
    assert response.json()["comparison"]["customer_loss_events_delta_pct"] is None
    assert response.json()["comparison"]["plan_loss_events_delta_pct"] is None


def test_monthly_lab_accepts_unmodified_baselines_for_every_observed_month():
    rows = client.get("/api/daily-portfolio-churn").json()["periods"]["MONTHLY"]
    assert len(rows) == 24
    for row in rows:
        response = client.post("/api/monthly-lab/scenario", json=_monthly_lab_payload(row["period"]))
        assert response.status_code == 200, f"{row['period']}: {response.text}"


def test_transition_audit_exposes_flags_without_promoting_them_to_migrations():
    response = client.get("/api/transition-audit")
    assert response.status_code == 200
    data = response.json()
    assert data["explicit_flags"]["upgrade_flag_rows"] == 529
    assert data["explicit_flags"]["downgrade_flag_rows"] == 218
    assert data["explicit_flags"]["rows_with_both_flags"] == 23
    assert data["classification_counts"]["confirmed"] == 0
    assert data["classification_counts"]["possible_upgrade_pairs_30d"] == 52
    assert data["classification_counts"]["possible_downgrade_pairs_30d"] == 51
