"""Conversão DataFrame -> registros JSON-seguros (NaN/NaT -> None)."""

from __future__ import annotations

import pandas as pd


def _clean(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def df_to_records(df: pd.DataFrame) -> list[dict]:
    return [{k: _clean(v) for k, v in row.items()} for row in df.to_dict(orient="records")]
