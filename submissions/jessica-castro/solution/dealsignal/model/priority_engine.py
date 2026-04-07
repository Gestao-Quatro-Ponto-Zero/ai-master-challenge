"""Revenue Priority Engine — combines win probability, deal value, and health."""
from __future__ import annotations
import pandas as pd

from config.constants import HEALTH_MULTIPLIER as _HEALTH_MULTIPLIER


def compute_priority(df: pd.DataFrame) -> pd.DataFrame:
    """Compute priority_score and priority_tier for each deal."""
    df = df.copy()

    multiplier = (
        df.get("deal_health_status", pd.Series("Atenção", index=df.index))
        .map(_HEALTH_MULTIPLIER)
        .fillna(0.90)
    )

    win_prob  = df.get("win_probability",  pd.Series(0.5, index=df.index))
    eff_value = df.get("effective_value",   pd.Series(0.0, index=df.index))

    df["priority_score"] = (win_prob * eff_value * multiplier).round(2)

    p33 = df["priority_score"].quantile(0.33)
    p66 = df["priority_score"].quantile(0.66)

    df["priority_tier"] = pd.cut(
        df["priority_score"],
        bins=[-0.01, p33, p66, float("inf")],
        labels=["Baixa prioridade", "Média prioridade", "Alta prioridade"],
    ).astype(str)

    return df
