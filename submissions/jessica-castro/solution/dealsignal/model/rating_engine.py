from typing import List

import pandas as pd

from config.constants import RATING_THRESHOLDS
from utils.logger import get_logger

logger = get_logger(__name__)


def assign_rating(win_probability: float) -> str:
    for threshold, rating in RATING_THRESHOLDS:
        if win_probability >= threshold:
            return rating
    return "CCC"


def compute_expected_revenue(win_probability: float, effective_value: float) -> float:
    return round(win_probability * effective_value, 2)


def score_pipeline(
    open_deals_df: pd.DataFrame,
    woe_transformer,
    model,
    feature_cols: List[str],
) -> pd.DataFrame:
    df = open_deals_df.copy()
    X = df[feature_cols].copy()
    X_woe = woe_transformer.transform(X)

    proba = model.predict_proba(X_woe)
    df["win_probability"] = proba
    df["deal_rating"] = df["win_probability"].apply(assign_rating)
    df["expected_revenue"] = df.apply(
        lambda r: compute_expected_revenue(r["win_probability"], r["effective_value"]),
        axis=1,
    )

    logger.info(
        "Scored %d open deals. Rating distribution:\n%s",
        len(df),
        df["deal_rating"].value_counts().to_string(),
    )
    return df, X_woe
