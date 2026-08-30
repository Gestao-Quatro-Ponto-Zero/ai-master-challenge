"""Conversão DataFrame -> registros JSON-seguros (NaN/NaT -> None)."""

from __future__ import annotations

import pandas as pd


def clean_value(value):
    """Converte NaN/NaT (pandas) para None — JSON e Pydantic não aceitam NaN."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def df_to_records(df: pd.DataFrame) -> list[dict]:
    return [{k: clean_value(v) for k, v in row.items()} for row in df.to_dict(orient="records")]
