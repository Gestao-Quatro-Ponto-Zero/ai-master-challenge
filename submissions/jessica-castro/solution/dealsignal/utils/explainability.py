from typing import List, Tuple

import numpy as np
import pandas as pd


def compute_deal_contributions(
    woe_row: pd.Series,
    coefficients: np.ndarray,
    feature_names: List[str],
) -> dict:
    contributions = {
        feat: float(woe_row[feat]) * float(coefficients[i])
        for i, feat in enumerate(feature_names)
    }
    sorted_contribs = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    top_positive = [(f, v) for f, v in sorted_contribs if v > 0][:3]
    top_negative = [(f, v) for f, v in reversed(sorted_contribs) if v < 0][:3]
    return {"top_positive": top_positive, "top_negative": top_negative}


def format_explanation(contributions: dict) -> str:
    parts = []
    for feat, val in contributions["top_positive"]:
        parts.append(f"+{feat}({val:+.2f})")
    for feat, val in contributions["top_negative"]:
        parts.append(f"-{feat}({val:+.2f})")
    return ", ".join(parts) if parts else "—"


def add_explanations_to_scored_df(
    scored_df: pd.DataFrame,
    X_woe: pd.DataFrame,
    coefficients: np.ndarray,
    feature_names: List[str],
) -> pd.DataFrame:
    scored_df = scored_df.copy()
    explanations = []
    for idx in scored_df.index:
        if idx in X_woe.index:
            contribs = compute_deal_contributions(
                X_woe.loc[idx], coefficients, feature_names
            )
            explanations.append(format_explanation(contribs))
        else:
            explanations.append("—")
    scored_df["top_contributing_factors"] = explanations
    return scored_df
