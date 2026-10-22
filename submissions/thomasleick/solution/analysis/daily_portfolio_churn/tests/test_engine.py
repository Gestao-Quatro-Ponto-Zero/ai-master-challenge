from datetime import date
from pathlib import Path

from daily_portfolio_churn.engine import _classify_plan_transitions, aggregate_periods, analyze, build_ledger, write_outputs


def row(sub_id: str, account: str, plan: str, start: str, end: str = "") -> dict[str, str]:
    return {"subscription_id": sub_id, "account_id": account, "plan_tier": plan, "start_date": start, "end_date": end}


def test_required_multi_product_portfolio_example():
    ledger = build_ledger([
        row("a-alpha", "A", "Alfa", "2024-01-01", "2024-01-02"),
        row("a-beta", "A", "Beta", "2024-01-01"),
        row("b-beta", "B", "Beta", "2024-01-01", "2024-01-02"),
        row("a-gamma", "A", "Gama", "2024-01-02"),
        row("c-alpha", "C", "Alfa", "2024-01-02"),
    ], date(2024, 1, 1), date(2024, 1, 3))
    day = {entry["date"]: entry for entry in ledger["daily"]}["2024-01-02"]
    assert day["opening_plan_relations"] == 3
    assert day["plan_relation_losses"] == 2
    assert day["daily_plan_churn_rate_pct"] == 2 / 3 * 100
    assert day["customer_churn"] == 1
    assert day["daily_customer_churn_rate_pct"] == 50
    assert day["new_customers"] == 1
    assert day["new_plan_relationships"] == 2
    assert day["retained_plan_relationships"] == 1
    assert day["closing_plan_relations"] == 3


def test_contiguous_renewal_and_overlapping_rows_are_one_relation():
    ledger = build_ledger([
        row("r1", "A", "Basic", "2024-01-01", "2024-02-01"),
        row("r2", "A", "Basic", "2024-02-01", "2024-03-01"),
        row("r3", "A", "Basic", "2024-01-15", "2024-02-15"),
    ], date(2024, 1, 1), date(2024, 3, 2))
    assert len(ledger["intervals"]) == 1
    by_date = {row["date"]: row for row in ledger["daily"]}
    assert by_date["2024-02-01"]["plan_relation_losses"] == 0
    assert by_date["2024-03-01"]["plan_relation_losses"] == 1
    assert sum(row["new_plan_relationships"] for row in ledger["daily"]) == 1


def test_gap_is_loss_then_reactivation():
    ledger = build_ledger([
        row("r1", "A", "Pro", "2024-01-01", "2024-01-03"),
        row("r2", "A", "Pro", "2024-01-05"),
    ], date(2024, 1, 1), date(2024, 1, 6))
    by_date = {row["date"]: row for row in ledger["daily"]}
    assert by_date["2024-01-03"]["plan_relation_losses"] == 1
    assert by_date["2024-01-05"]["plan_relation_reactivations"] == 1
    assert by_date["2024-01-05"]["customer_reactivations"] == 1


def test_same_day_plan_swap_is_two_distinct_movements_without_customer_churn():
    ledger = build_ledger([
        row("old", "A", "Basic", "2024-01-01", "2024-02-01"),
        row("new", "A", "Pro", "2024-02-01"),
    ], date(2024, 1, 1), date(2024, 2, 2))
    day = {row["date"]: row for row in ledger["daily"]}["2024-02-01"]
    assert day["plan_relation_losses"] == 1
    assert day["new_plan_relationships"] == 1
    assert day["customer_churn"] == 0


def test_period_aggregation_uses_opening_cohort_and_not_daily_rate_average():
    ledger = build_ledger([
        row("a", "A", "Basic", "2024-01-01", "2024-01-15"),
        row("b", "B", "Basic", "2024-01-01"),
        row("c", "C", "Pro", "2024-01-10"),
    ], date(2024, 1, 1), date(2024, 2, 1))
    month = aggregate_periods(ledger, ("MONTHLY",))["MONTHLY"][0]
    assert month["opening_plan_relations"] == 0
    assert month["gross_plan_relation_loss_events"] == 1
    assert month["closing_plan_relations"] == 2
    # The January period starts before any observed start; its empty opening base is undefined.
    assert month["opening_cohort_churn_at_close_pct"] is None


def test_empty_opening_population_has_undefined_daily_rate():
    ledger = build_ledger([row("a", "A", "Basic", "2024-01-01")], date(2024, 1, 1), date(2024, 1, 1))
    assert ledger["daily"][0]["daily_plan_churn_rate_pct"] is None
    assert ledger["daily"][0]["daily_customer_churn_rate_pct"] is None


def test_same_date_start_is_a_daily_acquisition_and_present_in_calendar_close():
    ledger = build_ledger([row("jan-one", "A", "Basic", "2024-01-01")], date(2023, 12, 31), date(2024, 1, 1))
    transition = {item["date"]: item for item in ledger["daily"]}["2024-01-01"]
    assert transition["opening_customers"] == 0
    assert transition["new_customers"] == 1
    assert transition["closing_customers"] == 1
    assert ledger["active_snapshots"][date(2024, 1, 1)] == {("A", "Basic")}


def test_nonpositive_interval_is_preserved_as_invalid_not_counted_as_churn():
    ledger = build_ledger([row("bad", "A", "Pro", "2024-01-02", "2024-01-02")], date(2024, 1, 1), date(2024, 1, 3))
    assert len(ledger["invalid_intervals"]) == 1
    assert ledger["invalid_intervals"][0]["subscription_id"] == "bad"
    assert sum(day["plan_relation_losses"] for day in ledger["daily"]) == 0


def test_last_open_interval_is_right_censored_not_churned():
    ledger = build_ledger([row("a", "A", "Basic", "2024-01-01")], date(2024, 1, 1), date(2024, 1, 3))
    assert sum(row["plan_relation_losses"] for row in ledger["daily"]) == 0
    assert ledger["intervals"][0]["right_censored"] is True


def test_possible_downgrade_uses_explicitly_unverified_tier_order():
    subscriptions = [
        row("pro", "D", "Pro", "2024-01-01", "2024-01-10"),
        row("basic", "D", "Basic", "2024-01-10"),
    ]
    ledger = build_ledger(subscriptions, date(2024, 1, 1), date(2024, 2, 10))
    transitions = _classify_plan_transitions(ledger, subscriptions)
    assert transitions["classification"] == "POSSIBLE_ONLY"
    assert transitions["windows_days"]["0"]["possible_downgrade_pairs"] == 1
    assert transitions["candidate_transitions"][0]["transition_timing"] == "NEW_PLAN_START_SAME_DAY_AS_LOSS"
    assert "not verified" in transitions["plan_order_evidence"]


def test_possible_upgrade_and_window_sensitivity_are_separate_from_revenue():
    subscriptions = [
        row("basic", "E", "Basic", "2024-01-01", "2024-01-10"),
        row("enterprise", "E", "Enterprise", "2024-01-17"),
    ]
    ledger = build_ledger(subscriptions, date(2024, 1, 1), date(2024, 2, 1))
    transitions = _classify_plan_transitions(ledger, subscriptions)
    assert transitions["windows_days"]["1"]["possible_upgrade_pairs"] == 0
    assert transitions["windows_days"]["7"]["possible_upgrade_pairs"] == 1
    assert transitions["windows_days"]["30"]["possible_upgrade_pairs"] == 1


def test_period_bridges_close_and_aggregate_from_daily_moves():
    ledger = build_ledger([
        row("a1", "A", "Basic", "2024-01-01", "2024-01-03"),
        row("a2", "A", "Pro", "2024-01-01"),
        row("b1", "B", "Basic", "2024-01-01", "2024-01-04"),
        row("b2", "B", "Basic", "2024-01-06"),
    ], date(2024, 1, 1), date(2024, 2, 1))
    for day in ledger["daily"]:
        assert day["opening_plan_relations"] - day["plan_relation_losses"] + day["new_plan_relationships"] + day["plan_relation_reactivations"] == day["closing_plan_relations"]
        assert day["opening_customers"] + day["new_customers"] + day["customer_reactivations"] - day["customer_churn"] == day["closing_customers"]
    aggregate = aggregate_periods(ledger)
    for granularity in aggregate.values():
        assert all(row["plan_relation_bridge_residual"] == 0 for row in granularity)
        assert all(row["customer_bridge_residual"] == 0 for row in granularity)
    assert sum(row["gross_plan_relation_loss_events"] for row in aggregate["MONTHLY"]) == sum(row["gross_plan_relation_loss_events"] for row in aggregate["ANNUAL"])


def test_monthly_plan_segments_reconcile_to_daily_ledger():
    ledger = build_ledger([
        row("b1", "A", "Basic", "2024-01-01", "2024-02-01"),
        row("p1", "B", "Pro", "2024-01-01"),
        row("b2", "A", "Basic", "2024-02-01"),
        row("e1", "C", "Enterprise", "2024-02-01"),
    ], date(2024, 1, 1), date(2024, 2, 3))
    months = aggregate_periods(ledger, ("MONTHLY",))["MONTHLY"]
    jan, feb = months
    assert jan["period"] == "2024-01"
    assert sum(p["opening_relations"] for p in jan["plan_segments"]) == jan["opening_plan_relations"]
    assert sum(p["gross_loss_events"] for p in jan["plan_segments"]) == jan["gross_plan_relation_loss_events"]
    assert sum(p["closing_relations"] for p in jan["plan_segments"]) == jan["closing_plan_relations"]
    assert feb["plan_relation_bridge_residual"] == 0
    basic = next(p for p in feb["plan_segments"] if p["plan_tier"] == "Basic")
    assert basic["gross_loss_events"] == 0  # Adjacent renewal was consolidated.


def test_real_monthly_series_carries_event_exposure_and_plan_segments():
    data_dir = Path(__file__).resolve().parents[3] / "data" / "raw"
    result = analyze(data_dir)
    months = result["periods"]["MONTHLY"]
    assert len(months) == 24
    assert months[0]["period"] == "2023-01"
    assert months[-1]["period"] == "2024-12"
    assert months[0]["recorded_events_per_opening_customer_pct"] is None
    assert months[11]["recorded_event_rows"] == 16
    assert months[12]["recorded_nonreactivation_event_rows"] + months[12]["recorded_reactivation_event_rows"] == months[12]["recorded_event_rows"]
    assert result["annual_monthly_summary"]["2023"]["gross_plan_loss_events"] == 6
    assert result["annual_monthly_summary"]["2024"]["gross_plan_loss_events"] == 56
    assert result["annual_monthly_summary"]["2023"]["opening_plan_relation_months"] == 1406
    assert result["annual_monthly_summary"]["2024"]["opening_plan_relation_months"] == 9414
    assert result["reconciliation"]["daily_plan_bridge_failures"] == []
    assert result["reconciliation"]["daily_customer_bridge_failures"] == []
    for month in months:
        for dimension in ("industry", "country", "referral_source"):
            groups = month["account_segments"][dimension]
            assert sum(group["opening_customers"] for group in groups) == month["opening_customers"]
            assert sum(group["closing_customers"] for group in groups) == month["closing_customers"]
            assert sum(group["opening_plan_relations"] for group in groups) == month["opening_plan_relations"]
            assert sum(group["closing_plan_relations"] for group in groups) == month["closing_plan_relations"]


def test_monthly_account_segment_output_is_written(tmp_path):
    data_dir = Path(__file__).resolve().parents[3] / "data" / "raw"
    write_outputs(data_dir, tmp_path)
    output = tmp_path / "monthly-account-segment-summary.csv"
    assert output.exists()
    assert output.read_text(encoding="utf-8").startswith("period,dimension,segment,")
