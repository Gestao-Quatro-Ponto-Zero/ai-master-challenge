"""Account-domain features."""
from __future__ import annotations
from typing import Optional

import numpy as np
import pandas as pd


def compute_account_features(
    df: pd.DataFrame,
    reference_date: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """Add account-domain features to df.

    Assumes enriched_accounts columns (revenue, employees, year_established,
    digital_maturity_index) are already merged upstream.

    Parameters
    ----------
    df             : DataFrame with enriched account columns already joined
    reference_date : Date to use for company_age computation. Defaults to
                     pd.Timestamp.now(). Pass dataset_end from build_features()
                     to ensure reproducible results across execution dates.
    """
    df = df.copy()
    if reference_date is None:
        reference_date = pd.Timestamp.now()

    if "revenue" in df.columns and "employees" in df.columns:
        df["revenue_per_employee"] = df["revenue"] / df["employees"].replace(0, np.nan)
    else:
        df["revenue_per_employee"] = np.nan

    if "year_established" in df.columns:
        df["company_age"] = (
            reference_date
            - pd.to_datetime(df["year_established"], format="%Y", errors="coerce")
        ).dt.days / 365.25
    if "company_age" not in df.columns:
        df["company_age"] = np.nan

    df["company_age_score"] = df["company_age"].rank(pct=True) if "company_age" in df.columns else 0.5

    df["account_size_percentile"] = (
        df["revenue"].rank(pct=True) if "revenue" in df.columns else 0.5
    )

    if "opportunity_id" in df.columns and "account" in df.columns:
        df["account_deal_volume"] = df.groupby("account")["opportunity_id"].transform("count")
    else:
        df["account_deal_volume"] = 1

    return df
