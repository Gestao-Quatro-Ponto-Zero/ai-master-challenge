from __future__ import annotations

import numpy as np
import pandas as pd

from churn_diagnosis.infrastructure.loaders import DataBundle

SNAPSHOT_KEY = "snapshot_id"


def resolve_current_snapshot_date(data: DataBundle) -> pd.Timestamp:
    subscriptions = data.subscriptions
    feature_usage = data.feature_usage
    support_tickets = data.support_tickets
    churn_events = data.churn_events
    accounts = data.accounts

    snapshot_candidates = [
        feature_usage["usage_date"].max() if not feature_usage.empty else pd.NaT,
        support_tickets["submitted_at"].max() if not support_tickets.empty else pd.NaT,
        churn_events["churn_date"].max() if not churn_events.empty else pd.NaT,
        subscriptions["start_date"].max() if not subscriptions.empty else pd.NaT,
        accounts["signup_date"].max() if not accounts.empty else pd.NaT,
    ]
    valid_candidates = [ts for ts in snapshot_candidates if pd.notna(ts)]
    if not valid_candidates:
        return pd.Timestamp.utcnow().normalize()
    return (max(valid_candidates) + pd.Timedelta(days=1)).normalize()


def ensure_snapshot_key(snapshots: pd.DataFrame) -> pd.DataFrame:
    snapshot_frame = snapshots.copy()
    snapshot_frame["snapshot_date"] = pd.to_datetime(snapshot_frame["snapshot_date"])
    if SNAPSHOT_KEY not in snapshot_frame.columns:
        snapshot_frame[SNAPSHOT_KEY] = np.arange(len(snapshot_frame), dtype=int)
    return snapshot_frame


def _usage_window_columns(window: int) -> list[str]:
    return [
        SNAPSHOT_KEY,
        "account_id",
        f"usage_events_{window}d",
        f"distinct_features_{window}d",
        f"total_usage_count_{window}d",
        f"total_usage_duration_secs_{window}d",
        f"total_error_count_{window}d",
        f"beta_feature_events_{window}d",
        f"avg_usage_count_{window}d",
        f"avg_usage_duration_secs_{window}d",
        f"avg_error_count_{window}d",
        f"error_per_usage_{window}d",
    ]


def _ticket_window_columns(window: int) -> list[str]:
    return [
        SNAPSHOT_KEY,
        "account_id",
        f"tickets_{window}d",
        f"avg_resolution_time_hours_{window}d",
        f"avg_first_response_time_minutes_{window}d",
        f"avg_satisfaction_score_{window}d",
        f"escalated_tickets_{window}d",
        f"urgent_tickets_{window}d",
        f"high_or_urgent_tickets_{window}d",
        f"ticket_escalation_rate_{window}d",
        f"ticket_urgency_rate_{window}d",
    ]


def _usage_window(df: pd.DataFrame, window: int) -> pd.DataFrame:
    scoped = df[df["days_to_snapshot"].between(0, window)]
    if scoped.empty:
        return pd.DataFrame(columns=_usage_window_columns(window))

    grouped = scoped.groupby([SNAPSHOT_KEY, "account_id"]).agg(
        **{
            f"usage_events_{window}d": ("usage_id", "count"),
            f"distinct_features_{window}d": ("feature_name", "nunique"),
            f"total_usage_count_{window}d": ("usage_count", "sum"),
            f"total_usage_duration_secs_{window}d": ("usage_duration_secs", "sum"),
            f"total_error_count_{window}d": ("error_count", "sum"),
            f"beta_feature_events_{window}d": ("is_beta_feature", "sum"),
            f"avg_usage_count_{window}d": ("usage_count", "mean"),
            f"avg_usage_duration_secs_{window}d": ("usage_duration_secs", "mean"),
            f"avg_error_count_{window}d": ("error_count", "mean"),
        }
    ).reset_index()

    grouped[f"error_per_usage_{window}d"] = (
        grouped[f"total_error_count_{window}d"]
        / grouped[f"total_usage_count_{window}d"].clip(lower=1)
    )
    return grouped


def _ticket_window(df: pd.DataFrame, window: int) -> pd.DataFrame:
    scoped = df[df["days_to_snapshot"].between(0, window)]
    if scoped.empty:
        return pd.DataFrame(columns=_ticket_window_columns(window))

    grouped = scoped.groupby([SNAPSHOT_KEY, "account_id"]).agg(
        **{
            f"tickets_{window}d": ("ticket_id", "count"),
            f"avg_resolution_time_hours_{window}d": ("resolution_time_hours", "mean"),
            f"avg_first_response_time_minutes_{window}d": (
                "first_response_time_minutes",
                "mean",
            ),
            f"avg_satisfaction_score_{window}d": ("satisfaction_score", "mean"),
            f"escalated_tickets_{window}d": ("escalation_flag", "sum"),
            f"urgent_tickets_{window}d": ("priority", lambda s: (s == "urgent").sum()),
            f"high_or_urgent_tickets_{window}d": (
                "priority",
                lambda s: s.isin(["high", "urgent"]).sum(),
            ),
        }
    ).reset_index()

    grouped[f"ticket_escalation_rate_{window}d"] = (
        grouped[f"escalated_tickets_{window}d"]
        / grouped[f"tickets_{window}d"].clip(lower=1)
    )
    grouped[f"ticket_urgency_rate_{window}d"] = (
        grouped[f"high_or_urgent_tickets_{window}d"]
        / grouped[f"tickets_{window}d"].clip(lower=1)
    )
    return grouped


def build_snapshot_feature_frame(
    data: DataBundle,
    snapshots: pd.DataFrame,
) -> pd.DataFrame:
    accounts = data.accounts.copy()
    subscriptions = data.subscriptions.copy()
    feature_usage = data.feature_usage.copy()
    support_tickets = data.support_tickets.copy()

    snapshot_frame = ensure_snapshot_key(snapshots)

    base = snapshot_frame.merge(
        accounts,
        on="account_id",
        how="left",
        validate="many_to_one",
    )
    base["account_age_days"] = (
        base["snapshot_date"] - base["signup_date"]
    ).dt.days.clip(lower=0)

    subscriptions_pt = subscriptions.merge(
        base[[SNAPSHOT_KEY, "account_id", "snapshot_date"]],
        on="account_id",
        how="inner",
    )
    subscriptions_pt = subscriptions_pt[
        subscriptions_pt["start_date"] <= subscriptions_pt["snapshot_date"]
    ].copy()

    subscriptions_pt["is_active_at_snapshot"] = (
        subscriptions_pt["end_date"].isna()
        | (subscriptions_pt["end_date"] >= subscriptions_pt["snapshot_date"])
    )
    subscriptions_pt["ended_before_snapshot"] = (
        subscriptions_pt["end_date"].notna()
        & (subscriptions_pt["end_date"] < subscriptions_pt["snapshot_date"])
    )

    subscriptions_agg = subscriptions_pt.groupby([SNAPSHOT_KEY, "account_id"]).agg(
        sub_count=("subscription_id", "nunique"),
        active_subscriptions=("is_active_at_snapshot", "sum"),
        ended_subscriptions=("ended_before_snapshot", "sum"),
        total_mrr=("mrr_amount", "sum"),
        avg_mrr=("mrr_amount", "mean"),
        max_mrr=("mrr_amount", "max"),
        total_arr=("arr_amount", "sum"),
        total_seats_subs=("seats", "sum"),
        avg_seats_subs=("seats", "mean"),
        upgrade_events=("upgrade_flag", "sum"),
        downgrade_events=("downgrade_flag", "sum"),
        annual_subscriptions=("billing_frequency", lambda s: (s == "annual").sum()),
        monthly_subscriptions=("billing_frequency", lambda s: (s == "monthly").sum()),
        auto_renew_subscriptions=("auto_renew_flag", "sum"),
        trial_subscriptions=("is_trial", "sum"),
    ).reset_index()

    usage_pt = (
        feature_usage.merge(
            subscriptions[["subscription_id", "account_id"]],
            on="subscription_id",
            how="left",
        )
        .merge(base[[SNAPSHOT_KEY, "account_id", "snapshot_date"]], on="account_id", how="inner")
    )
    usage_pt = usage_pt[usage_pt["usage_date"] <= usage_pt["snapshot_date"]].copy()
    if not usage_pt.empty and (usage_pt["usage_date"] > usage_pt["snapshot_date"]).any():
        raise ValueError("Usage features include rows after snapshot_date.")
    usage_pt["days_to_snapshot"] = (
        usage_pt["snapshot_date"] - usage_pt["usage_date"]
    ).dt.days

    usage_30 = _usage_window(usage_pt, 30)
    usage_90 = _usage_window(usage_pt, 90)

    usage_recency = usage_pt.groupby([SNAPSHOT_KEY, "account_id"]).agg(
        last_usage_date=("usage_date", "max"),
        first_usage_date=("usage_date", "min"),
    ).reset_index()
    usage_recency = usage_recency.merge(
        base[[SNAPSHOT_KEY, "account_id", "snapshot_date"]],
        on=[SNAPSHOT_KEY, "account_id"],
        how="left",
        validate="one_to_one",
    )
    usage_recency["days_since_last_usage"] = (
        usage_recency["snapshot_date"] - usage_recency["last_usage_date"]
    ).dt.days
    usage_recency["days_since_first_usage"] = (
        usage_recency["snapshot_date"] - usage_recency["first_usage_date"]
    ).dt.days
    usage_recency = usage_recency[
        [SNAPSHOT_KEY, "account_id", "days_since_last_usage", "days_since_first_usage"]
    ]

    tickets_pt = support_tickets.merge(
        base[[SNAPSHOT_KEY, "account_id", "snapshot_date"]],
        on="account_id",
        how="inner",
    )
    tickets_pt = tickets_pt[
        tickets_pt["submitted_at"].dt.normalize() <= tickets_pt["snapshot_date"]
    ].copy()
    if not tickets_pt.empty and (tickets_pt["submitted_at"].dt.normalize() > tickets_pt["snapshot_date"]).any():
        raise ValueError("Ticket features include rows after snapshot_date.")
    tickets_pt["days_to_snapshot"] = (
        tickets_pt["snapshot_date"] - tickets_pt["submitted_at"].dt.normalize()
    ).dt.days

    tickets_30 = _ticket_window(tickets_pt, 30)
    tickets_90 = _ticket_window(tickets_pt, 90)

    ticket_recency = tickets_pt.groupby([SNAPSHOT_KEY, "account_id"]).agg(
        last_ticket_date=("submitted_at", "max")
    ).reset_index()
    ticket_recency = ticket_recency.merge(
        base[[SNAPSHOT_KEY, "account_id", "snapshot_date"]],
        on=[SNAPSHOT_KEY, "account_id"],
        how="left",
        validate="one_to_one",
    )
    ticket_recency["days_since_last_ticket"] = (
        ticket_recency["snapshot_date"] - ticket_recency["last_ticket_date"].dt.normalize()
    ).dt.days
    ticket_recency = ticket_recency[[SNAPSHOT_KEY, "account_id", "days_since_last_ticket"]]

    dataset = (
        base.merge(subscriptions_agg, on=[SNAPSHOT_KEY, "account_id"], how="left")
        .merge(usage_30, on=[SNAPSHOT_KEY, "account_id"], how="left")
        .merge(usage_90, on=[SNAPSHOT_KEY, "account_id"], how="left")
        .merge(usage_recency, on=[SNAPSHOT_KEY, "account_id"], how="left")
        .merge(tickets_30, on=[SNAPSHOT_KEY, "account_id"], how="left")
        .merge(tickets_90, on=[SNAPSHOT_KEY, "account_id"], how="left")
        .merge(ticket_recency, on=[SNAPSHOT_KEY, "account_id"], how="left")
    )

    protected_cols = {
        SNAPSHOT_KEY,
        "account_id",
        "account_name",
        "industry",
        "country",
        "referral_source",
        "plan_tier",
        "signup_date",
        "first_churn_date",
        "snapshot_date",
    }

    for col in dataset.columns:
        if col not in protected_cols and dataset[col].dtype.kind in "biufc":
            dataset[col] = dataset[col].fillna(0)

    dataset["trial_ratio"] = dataset["trial_subscriptions"] / dataset["sub_count"].clip(lower=1)
    dataset["annual_ratio"] = dataset["annual_subscriptions"] / dataset["sub_count"].clip(lower=1)
    dataset["monthly_ratio"] = dataset["monthly_subscriptions"] / dataset["sub_count"].clip(lower=1)
    dataset["auto_renew_ratio"] = dataset["auto_renew_subscriptions"] / dataset["sub_count"].clip(lower=1)
    dataset["downgrade_to_upgrade_ratio"] = dataset["downgrade_events"] / dataset["upgrade_events"].clip(lower=1)

    dataset["support_burden_index_30d"] = (
        dataset["avg_resolution_time_hours_30d"] * 0.5
        + dataset["avg_first_response_time_minutes_30d"] / 60 * 0.3
        + dataset["ticket_escalation_rate_30d"] * 10 * 0.2
    )

    dataset["support_burden_index_90d"] = (
        dataset["avg_resolution_time_hours_90d"] * 0.5
        + dataset["avg_first_response_time_minutes_90d"] / 60 * 0.3
        + dataset["ticket_escalation_rate_90d"] * 10 * 0.2
    )

    dataset["usage_intensity_30d"] = dataset["total_usage_count_30d"] / dataset["total_seats_subs"].clip(lower=1)
    dataset["usage_intensity_90d"] = dataset["total_usage_count_90d"] / dataset["total_seats_subs"].clip(lower=1)

    dataset["usage_drop_ratio_30_to_90"] = np.where(
        dataset["total_usage_count_90d"] > 0,
        1 - (
            dataset["total_usage_count_30d"]
            / dataset["total_usage_count_90d"].clip(lower=1)
        ),
        0.0,
    )

    dataset["error_acceleration_30_to_90"] = np.where(
        dataset["total_error_count_90d"] > 0,
        dataset["total_error_count_30d"]
        / dataset["total_error_count_90d"].clip(lower=1),
        0.0,
    )

    return dataset.sort_values(["account_id", "snapshot_date", SNAPSHOT_KEY]).reset_index(drop=True)
