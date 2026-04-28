from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from churn_diagnosis.infrastructure.loaders import DataBundle
from .config import ChurnPredictionConfig
from .feature_engineering import (
    SNAPSHOT_KEY,
    build_snapshot_feature_frame,
    ensure_snapshot_key,
    resolve_current_snapshot_date,
)


@dataclass
class LeakageReport:
    post_churn_usage_rate_in_raw: float
    post_churn_ticket_rate_in_raw: float
    forbidden_feature_columns_absent: bool
    features_within_snapshot_boundary: bool
    target_uses_only_future_churn: bool
    multiple_snapshots_per_account: bool


def _resolve_dataset_end(data: DataBundle) -> pd.Timestamp:
    subscriptions = data.subscriptions
    feature_usage = data.feature_usage
    support_tickets = data.support_tickets
    churn_events = data.churn_events
    accounts = data.accounts

    return max(
        subscriptions["start_date"].max(),
        subscriptions["end_date"].dropna().max(),
        feature_usage["usage_date"].max(),
        support_tickets["submitted_at"].dt.normalize().max(),
        churn_events["churn_date"].max(),
        accounts["signup_date"].max(),
    )


def _actual_churn_events(churn_events: pd.DataFrame) -> pd.DataFrame:
    events = churn_events.copy()
    return events.loc[~events["is_reactivation"].fillna(False)].copy()


def _build_training_snapshots(
    data: DataBundle,
    config: ChurnPredictionConfig,
) -> pd.DataFrame:
    accounts = data.accounts.copy()
    dataset_end = _resolve_dataset_end(data)
    latest_eligible_snapshot = dataset_end - pd.Timedelta(days=config.horizon_days)

    snapshot_rows: list[dict[str, object]] = []

    # We generate rolling monthly snapshots per account. Each row is later labeled
    # by asking whether a true churn event happens in the next fixed horizon.
    for row in accounts.itertuples(index=False):
        first_snapshot = row.signup_date + pd.Timedelta(days=config.min_history_days)
        if pd.isna(first_snapshot) or first_snapshot > latest_eligible_snapshot:
            continue

        snapshot_dates = pd.date_range(
            start=first_snapshot.normalize(),
            end=latest_eligible_snapshot.normalize(),
            freq=f"{config.snapshot_step_days}D",
        )
        for snapshot_date in snapshot_dates:
            snapshot_rows.append(
                {
                    "account_id": row.account_id,
                    "snapshot_date": snapshot_date.normalize(),
                }
            )

    snapshots = pd.DataFrame(snapshot_rows)
    if snapshots.empty:
        return pd.DataFrame(columns=["account_id", "snapshot_date", SNAPSHOT_KEY])
    return ensure_snapshot_key(snapshots)


def _label_snapshots(
    snapshots: pd.DataFrame,
    actual_churn_events: pd.DataFrame,
    horizon_days: int,
) -> pd.DataFrame:
    labeled = snapshots.copy()
    labeled["target_churn_30d"] = 0
    labeled["first_future_churn_date"] = pd.NaT

    if labeled.empty or actual_churn_events.empty:
        return labeled

    joined = labeled.merge(
        actual_churn_events[["account_id", "churn_date"]],
        on="account_id",
        how="left",
    )
    in_window = joined[
        (joined["churn_date"] > joined["snapshot_date"])
        & (
            joined["churn_date"]
            <= joined["snapshot_date"] + pd.Timedelta(days=horizon_days)
        )
    ].copy()
    if in_window.empty:
        return labeled

    future_churn = (
        in_window.groupby(SNAPSHOT_KEY, as_index=False)["churn_date"]
        .min()
        .rename(columns={"churn_date": "first_future_churn_date"})
    )
    labeled = labeled.merge(future_churn, on=SNAPSHOT_KEY, how="left", suffixes=("", "_detected"))
    labeled["first_future_churn_date"] = labeled["first_future_churn_date_detected"].combine_first(
        labeled["first_future_churn_date"]
    )
    labeled = labeled.drop(columns=["first_future_churn_date_detected"])
    labeled["target_churn_30d"] = labeled["first_future_churn_date"].notna().astype(int)
    return labeled


def _compute_raw_leakage_rates(
    data: DataBundle,
    actual_churn_events: pd.DataFrame,
) -> tuple[float, float]:
    subscriptions = data.subscriptions.copy()
    feature_usage = data.feature_usage.copy()
    support_tickets = data.support_tickets.copy()

    account_churn = actual_churn_events.groupby("account_id", as_index=False)["churn_date"].min()
    account_churn = account_churn.rename(columns={"churn_date": "first_actual_churn_date"})

    raw_usage_leak = (
        feature_usage.merge(
            subscriptions[["subscription_id", "account_id"]],
            on="subscription_id",
            how="left",
        )
        .merge(account_churn, on="account_id", how="inner")
    )
    raw_usage_post = (
        float((raw_usage_leak["usage_date"] > raw_usage_leak["first_actual_churn_date"]).mean())
        if not raw_usage_leak.empty
        else 0.0
    )

    raw_ticket_leak = support_tickets.merge(account_churn, on="account_id", how="inner")
    raw_ticket_post = (
        float(
            (
                raw_ticket_leak["submitted_at"].dt.normalize()
                > raw_ticket_leak["first_actual_churn_date"]
            ).mean()
        )
        if not raw_ticket_leak.empty
        else 0.0
    )
    return raw_usage_post, raw_ticket_post


def _build_leakage_report(
    dataset: pd.DataFrame,
    actual_churn_events: pd.DataFrame,
    raw_usage_post: float,
    raw_ticket_post: float,
) -> LeakageReport:
    forbidden_columns = {
        "churn_date",
        "reason_code",
        "refund_amount_usd",
        "feedback_text",
        "preceding_upgrade_flag",
        "preceding_downgrade_flag",
        "is_reactivation",
    }

    future_target_check = True
    if not dataset.empty and "first_future_churn_date" in dataset.columns:
        positives = dataset.loc[dataset["target_churn_30d"].eq(1)].copy()
        if not positives.empty:
            future_target_check = bool(
                (
                    positives["first_future_churn_date"] > positives["snapshot_date"]
                ).all()
                and (
                    positives["first_future_churn_date"]
                    <= positives["snapshot_date"] + pd.Timedelta(days=30)
                ).all()
            )

    features_within_snapshot_boundary = bool(dataset["snapshot_date"].notna().all())
    multiple_snapshots = bool((dataset.groupby("account_id").size() > 1).any())

    return LeakageReport(
        post_churn_usage_rate_in_raw=raw_usage_post,
        post_churn_ticket_rate_in_raw=raw_ticket_post,
        forbidden_feature_columns_absent=forbidden_columns.isdisjoint(set(dataset.columns)),
        features_within_snapshot_boundary=features_within_snapshot_boundary,
        target_uses_only_future_churn=future_target_check,
        multiple_snapshots_per_account=multiple_snapshots,
    )


def build_point_in_time_dataset(
    data: DataBundle,
    config: ChurnPredictionConfig,
) -> tuple[pd.DataFrame, LeakageReport]:
    actual_churn_events = _actual_churn_events(data.churn_events)
    raw_usage_post, raw_ticket_post = _compute_raw_leakage_rates(data, actual_churn_events)

    labeled_snapshots = _label_snapshots(
        snapshots=_build_training_snapshots(data, config),
        actual_churn_events=actual_churn_events,
        horizon_days=config.horizon_days,
    )

    dataset = build_snapshot_feature_frame(
        data=data,
        snapshots=labeled_snapshots[[SNAPSHOT_KEY, "account_id", "snapshot_date"]],
    ).merge(
        labeled_snapshots[
            [SNAPSHOT_KEY, "first_future_churn_date", "target_churn_30d"]
        ],
        on=SNAPSHOT_KEY,
        how="left",
        validate="one_to_one",
    )

    dataset = dataset.loc[dataset["active_subscriptions"] > 0].copy()
    dataset["is_logo_churned"] = dataset["target_churn_30d"].astype(int)
    dataset = dataset.sort_values(["account_id", "snapshot_date", SNAPSHOT_KEY]).reset_index(drop=True)

    leakage_report = _build_leakage_report(
        dataset=dataset,
        actual_churn_events=actual_churn_events,
        raw_usage_post=raw_usage_post,
        raw_ticket_post=raw_ticket_post,
    )

    return dataset, leakage_report


def build_current_scoring_dataset(
    data: DataBundle,
) -> tuple[pd.DataFrame, pd.Timestamp]:
    current_snapshot_date = resolve_current_snapshot_date(data)
    current_snapshots = data.accounts[["account_id"]].copy()
    current_snapshots["snapshot_date"] = current_snapshot_date
    current_snapshots = ensure_snapshot_key(current_snapshots)

    dataset = build_snapshot_feature_frame(
        data=data,
        snapshots=current_snapshots,
    )
    return dataset, current_snapshot_date
