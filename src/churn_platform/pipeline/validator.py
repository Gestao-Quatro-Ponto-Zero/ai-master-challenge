"""SPEC-2 REQ-2-002/003: Schema validation + Data Quality Report."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

TYPE_MAP = {
    "string": "object",
    "integer": "int64",
    "float": "float64",
    "boolean": "bool",
    "date": "object",
    "datetime": "object",
}


class ValidationError(Exception):
    """Erro de validação de schema."""


def validate_schema(
    df: pd.DataFrame,
    schema: dict[str, Any],
    source_name: str,
) -> None:
    required = schema.get("required", [])
    for col in required:
        if col not in df.columns:
            raise ValidationError(f"[{source_name}] Coluna obrigatória ausente: {col}")

    types = schema.get("types", {})
    for col, expected_type in types.items():
        if col in df.columns:
            pandas_type = TYPE_MAP.get(expected_type, "object")
            actual_dtype = str(df[col].dtype)
            if actual_dtype != pandas_type and not (
                expected_type in ("date", "datetime") and "datetime" in actual_dtype
            ):
                logger.debug(
                    "  Tipagem: %s esperado=%s, atual=%s (não crítico)",
                    col, expected_type, actual_dtype,
                )

    constraints = schema.get("constraints", {})
    for col, rules in constraints.items():
        if col not in df.columns:
            continue
        if "min" in rules:
            if df[col].dtype in ("int64", "float64") and df[col].min() < rules["min"]:
                n_bad = (df[col] < rules["min"]).sum()
                raise ValidationError(
                    f"[{source_name}] {col}: {n_bad} valores abaixo do mínimo {rules['min']}"
                )
        if "in" in rules:
            bad = df[col].dropna().isin(rules["in"]) == False
            if bad.any():
                invalid = df[col][bad].unique()
                logger.warning(
                    "[%s] %s: valores fora do esperado: %s",
                    source_name, col, invalid,
                )

    logger.info("  ✓ Schema OK")


def generate_dqr(
    sources: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    report = {}
    for name, df in sources.items():
        src_name = name.split("/")[-1] if "/" in name else name
        col_stats = {}
        for col in df.columns:
            stats = {
                "dtype": str(df[col].dtype),
                "nulls": int(df[col].isna().sum()),
                "null_rate": round(float(df[col].isna().mean()), 3),
                "unique": int(df[col].nunique()),
            }
            if df[col].dtype in ("int64", "float64"):
                stats["min"] = float(df[col].min()) if df[col].count() > 0 else None
                stats["max"] = float(df[col].max()) if df[col].count() > 0 else None
                stats["mean"] = round(float(df[col].mean()), 2) if df[col].count() > 0 else None
            col_stats[col] = stats
        report[src_name] = {
            "rows": len(df),
            "cols": len(df.columns),
            "columns": col_stats,
        }
    return report


def run(
    sources: dict[str, pd.DataFrame],
    schemas: dict[str, Any],
    output_dir: str = "output",
) -> dict[str, Any]:
    logger.info("=== Validação de dados ===")
    import json, os

    for name, df in sources.items():
        src_key = name.split("/")[-1].replace(".csv", "").replace(".json", "").replace(".parquet", "")
        schema = schemas.get(src_key, {})
        if schema:
            logger.info("Validando schema: %s", src_key)
            validate_schema(df, schema, src_key)

    dqr = generate_dqr(sources)
    os.makedirs(output_dir, exist_ok=True)
    dqr_path = os.path.join(output_dir, "dqr.json")
    with open(dqr_path, "w") as f:
        json.dump(dqr, f, indent=2, default=str)
    logger.info("DQR salvo em %s", dqr_path)

    return dqr
