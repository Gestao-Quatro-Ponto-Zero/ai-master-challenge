from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class DataBundle:
    accounts: pd.DataFrame
    subscriptions: pd.DataFrame
    feature_usage: pd.DataFrame
    support_tickets: pd.DataFrame
    churn_events: pd.DataFrame


class CsvDataLoader:
    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)

    def load(self) -> DataBundle:
        return DataBundle(
            accounts=pd.read_csv(self.data_dir / "ravenstack_accounts.csv", parse_dates=["signup_date"]),
            subscriptions=pd.read_csv(self.data_dir / "ravenstack_subscriptions.csv", parse_dates=["start_date", "end_date"]),
            feature_usage=pd.read_csv(self.data_dir / "ravenstack_feature_usage.csv", parse_dates=["usage_date"]),
            support_tickets=pd.read_csv(self.data_dir / "ravenstack_support_tickets.csv", parse_dates=["submitted_at", "closed_at"]),
            churn_events=pd.read_csv(self.data_dir / "ravenstack_churn_events.csv", parse_dates=["churn_date"]),
        )
