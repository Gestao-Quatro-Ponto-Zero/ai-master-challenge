from pathlib import Path

import pandas as pd

from churn_diagnosis.application.use_cases import BuildAccount360UseCase, build_churn_reconciliation
from churn_diagnosis.infrastructure.loaders import DataBundle
from churn_diagnosis.infrastructure.loaders import CsvDataLoader


def test_account_360_has_expected_keys():
    loader = CsvDataLoader(Path(__file__).resolve().parents[1] / "data")
    data = loader.load()
    df = BuildAccount360UseCase().execute(data)
    assert len(df) == 500
    assert df["account_id"].nunique() == 500
    expected_columns = {
        "account_id",
        "current_mrr",
        "usage_drop_ratio",
        "error_rate_30d",
        "escalation_rate",
        "snapshot_date",
    }
    assert expected_columns.issubset(df.columns)


def test_account_360_current_state_uses_active_subscriptions():
    bundle = DataBundle(
        accounts=pd.DataFrame(
            [
                {
                    "account_id": "A-1",
                    "account_name": "Alpha",
                    "industry": "FinTech",
                    "country": "US",
                    "signup_date": pd.Timestamp("2024-01-01"),
                    "referral_source": "partner",
                    "plan_tier": "Basic",
                    "seats": 10,
                    "is_trial": False,
                    "churn_flag": True,
                },
                {
                    "account_id": "A-2",
                    "account_name": "Beta",
                    "industry": "HealthTech",
                    "country": "BR",
                    "signup_date": pd.Timestamp("2024-01-10"),
                    "referral_source": "web",
                    "plan_tier": "Starter",
                    "seats": 4,
                    "is_trial": False,
                    "churn_flag": False,
                },
            ]
        ),
        subscriptions=pd.DataFrame(
            [
                {
                    "subscription_id": "S-1",
                    "account_id": "A-1",
                    "start_date": pd.Timestamp("2024-01-01"),
                    "end_date": pd.Timestamp("2024-02-01"),
                    "plan_tier": "Basic",
                    "seats": 5,
                    "mrr_amount": 100,
                    "arr_amount": 1200,
                    "is_trial": False,
                    "upgrade_flag": False,
                    "downgrade_flag": False,
                    "churn_flag": True,
                    "billing_frequency": "monthly",
                    "auto_renew_flag": True,
                },
                {
                    "subscription_id": "S-2",
                    "account_id": "A-1",
                    "start_date": pd.Timestamp("2024-02-10"),
                    "end_date": pd.Timestamp("2024-04-30"),
                    "plan_tier": "Pro",
                    "seats": 8,
                    "mrr_amount": 200,
                    "arr_amount": 2400,
                    "is_trial": False,
                    "upgrade_flag": True,
                    "downgrade_flag": False,
                    "churn_flag": False,
                    "billing_frequency": "monthly",
                    "auto_renew_flag": False,
                },
                {
                    "subscription_id": "S-3",
                    "account_id": "A-1",
                    "start_date": pd.Timestamp("2024-03-01"),
                    "end_date": pd.NaT,
                    "plan_tier": "Enterprise",
                    "seats": 12,
                    "mrr_amount": 300,
                    "arr_amount": 3600,
                    "is_trial": False,
                    "upgrade_flag": True,
                    "downgrade_flag": False,
                    "churn_flag": False,
                    "billing_frequency": "annual",
                    "auto_renew_flag": True,
                },
                {
                    "subscription_id": "S-4",
                    "account_id": "A-2",
                    "start_date": pd.Timestamp("2024-01-15"),
                    "end_date": pd.Timestamp("2024-02-20"),
                    "plan_tier": "Starter",
                    "seats": 4,
                    "mrr_amount": 50,
                    "arr_amount": 600,
                    "is_trial": False,
                    "upgrade_flag": False,
                    "downgrade_flag": False,
                    "churn_flag": True,
                    "billing_frequency": "monthly",
                    "auto_renew_flag": False,
                },
            ]
        ),
        feature_usage=pd.DataFrame(
            [
                {
                    "usage_id": "U-1",
                    "subscription_id": "S-2",
                    "usage_date": pd.Timestamp("2024-03-10"),
                    "feature_name": "automation",
                    "usage_count": 10,
                    "usage_duration_secs": 100,
                    "error_count": 0,
                    "is_beta_feature": False,
                },
                {
                    "usage_id": "U-2",
                    "subscription_id": "S-3",
                    "usage_date": pd.Timestamp("2024-03-12"),
                    "feature_name": "billing",
                    "usage_count": 5,
                    "usage_duration_secs": 50,
                    "error_count": 1,
                    "is_beta_feature": False,
                },
                {
                    "usage_id": "U-3",
                    "subscription_id": "S-4",
                    "usage_date": pd.Timestamp("2024-02-10"),
                    "feature_name": "reports",
                    "usage_count": 2,
                    "usage_duration_secs": 20,
                    "error_count": 0,
                    "is_beta_feature": False,
                },
            ]
        ),
        support_tickets=pd.DataFrame(
            [
                {
                    "ticket_id": "T-1",
                    "account_id": "A-1",
                    "submitted_at": pd.Timestamp("2024-03-15"),
                    "closed_at": pd.Timestamp("2024-03-15 03:00:00"),
                    "priority": "low",
                    "resolution_time_hours": 3.0,
                    "first_response_time_minutes": 20.0,
                    "satisfaction_score": 4.5,
                    "escalation_flag": False,
                },
                {
                    "ticket_id": "T-2",
                    "account_id": "A-2",
                    "submitted_at": pd.Timestamp("2024-02-05"),
                    "closed_at": pd.Timestamp("2024-02-05 02:00:00"),
                    "priority": "medium",
                    "resolution_time_hours": 2.0,
                    "first_response_time_minutes": 15.0,
                    "satisfaction_score": 4.0,
                    "escalation_flag": False,
                },
            ]
        ),
        churn_events=pd.DataFrame(
            [
                {
                    "churn_event_id": "C-1",
                    "account_id": "A-1",
                    "churn_date": pd.Timestamp("2024-02-01"),
                    "reason_code": "pricing",
                    "refund_amount_usd": 0.0,
                    "feedback_text": "too expensive",
                    "preceding_upgrade_flag": False,
                    "preceding_downgrade_flag": False,
                    "is_reactivation": False,
                },
                {
                    "churn_event_id": "C-2",
                    "account_id": "A-2",
                    "churn_date": pd.Timestamp("2024-02-20"),
                    "reason_code": "support",
                    "refund_amount_usd": 10.0,
                    "feedback_text": "slow support",
                    "preceding_upgrade_flag": False,
                    "preceding_downgrade_flag": False,
                    "is_reactivation": False,
                },
            ]
        ),
    )

    df = BuildAccount360UseCase().execute(bundle).set_index("account_id")

    assert df.loc["A-1", "current_mrr"] == 500
    assert df.loc["A-1", "current_arr"] == 6000
    assert df.loc["A-1", "active_subscriptions"] == 2
    assert df.loc["A-1", "latest_plan"] == "Enterprise"
    assert df.loc["A-1", "current_billing_frequency"] == "mixed"
    assert bool(df.loc["A-1", "auto_renew_flag"]) is True
    assert df.loc["A-1", "is_logo_churned"] == 0

    assert df.loc["A-2", "current_mrr"] == 0
    assert df.loc["A-2", "current_arr"] == 0
    assert df.loc["A-2", "active_subscriptions"] == 0
    assert df.loc["A-2", "latest_plan"] == "Starter"
    assert df.loc["A-2", "is_logo_churned"] == 1


def test_account_360_current_revenue_matches_active_subscriptions_in_real_data():
    loader = CsvDataLoader(Path(__file__).resolve().parents[1] / "data")
    data = loader.load()
    df = BuildAccount360UseCase().execute(data)

    scoped = data.subscriptions.merge(df[["account_id", "snapshot_date"]], on="account_id", how="inner")
    active = scoped[
        (scoped["start_date"] <= scoped["snapshot_date"])
        & (scoped["end_date"].isna() | (scoped["end_date"] >= scoped["snapshot_date"]))
    ].copy()
    expected = active.groupby("account_id", as_index=False).agg(
        expected_current_mrr=("mrr_amount", "sum"),
        expected_current_arr=("arr_amount", "sum"),
        expected_active_subscriptions=("subscription_id", "count"),
    )

    merged = df.merge(expected, on="account_id", how="left")
    for column in ["expected_current_mrr", "expected_current_arr", "expected_active_subscriptions"]:
        merged[column] = merged[column].fillna(0)

    assert merged["current_mrr"].round(6).equals(merged["expected_current_mrr"].round(6))
    assert merged["current_arr"].round(6).equals(merged["expected_current_arr"].round(6))
    assert merged["active_subscriptions"].astype(float).round(6).equals(merged["expected_active_subscriptions"].astype(float).round(6))
    assert merged["is_logo_churned"].equals((merged["active_subscriptions"] == 0).astype(int))


def test_churn_reconciliation_counts_divergent_definitions():
    account_360 = pd.DataFrame(
        [
            {
                "account_id": "A-1",
                "churn_flag": 1,
                "had_churn_event": 1,
                "reactivation_events": 1,
                "active_subscriptions": 1,
            },
            {
                "account_id": "A-2",
                "churn_flag": 1,
                "had_churn_event": 0,
                "reactivation_events": 0,
                "active_subscriptions": 0,
            },
            {
                "account_id": "A-3",
                "churn_flag": 0,
                "had_churn_event": 1,
                "reactivation_events": 0,
                "active_subscriptions": 1,
            },
        ]
    )

    reconciliation = build_churn_reconciliation(account_360).set_index("metric_key")

    assert reconciliation.loc["total_accounts", "metric_value"] == 3
    assert reconciliation.loc["accounts_churn_flag_true", "metric_value"] == 2
    assert reconciliation.loc["accounts_with_churn_event", "metric_value"] == 2
    assert reconciliation.loc["accounts_with_churn_flag_true_and_no_event", "metric_value"] == 1
    assert reconciliation.loc["accounts_with_event_and_churn_flag_false", "metric_value"] == 1
    assert reconciliation.loc["accounts_reactivated", "metric_value"] == 1
    assert reconciliation.loc["accounts_currently_active_after_reactivation", "metric_value"] == 1
    assert reconciliation.loc["accounts_churn_flag_true", "metric_category"] == "métrica cadastral"
    assert reconciliation.loc["accounts_with_churn_event", "metric_category"] == "métrica observada por eventos"
    assert reconciliation.loc["accounts_currently_active_after_reactivation", "metric_category"] == "métrica operacional atual"
