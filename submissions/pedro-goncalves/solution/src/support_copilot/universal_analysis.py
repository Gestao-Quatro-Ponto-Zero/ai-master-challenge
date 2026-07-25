from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd


VALID_ROLES = (
    "Identificador",
    "Texto",
    "Data",
    "Categoria",
    "Métrica",
    "Contexto",
)


@dataclass(frozen=True)
class TableSummary:
    name: str
    rows: int
    columns: int
    completeness: float
    exact_duplicate_rows: int
    duplicate_identifier_rows: int | None
    text_columns: tuple[str, ...]
    date_columns: tuple[str, ...]
    category_columns: tuple[str, ...]
    metric_columns: tuple[str, ...]
    quality_score: float


def read_spreadsheet(
    source: str | Path | BinaryIO | BytesIO,
    *,
    filename: str,
) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if hasattr(source, "seek"):
        source.seek(0)
    if suffix == ".csv":
        return pd.read_csv(source)
    if suffix in {".xlsx", ".xlsm"}:
        return pd.read_excel(source, engine="openpyxl")
    raise ValueError("Formato não suportado. Use CSV ou XLSX.")


def infer_role(column: str, series: pd.Series) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", column.lower()).strip()
    if re.search(r"\b(id|identifier|ticket id|protocolo|codigo|code)\b", normalized):
        return "Identificador"
    if re.search(
        r"\b(description|document|message|mensagem|descricao|texto|comentario)\b",
        normalized,
    ):
        return "Texto"
    if re.search(r"\b(date|data|time|timestamp|created|updated|resolved)\b", normalized):
        return "Data"
    if pd.api.types.is_numeric_dtype(series):
        return "Métrica"
    unique_share = series.nunique(dropna=True) / max(len(series), 1)
    if unique_share <= 0.20:
        return "Categoria"
    return "Contexto"


def profile_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for order, column in enumerate(frame.columns, start=1):
        series = frame[column]
        rows.append(
            {
                "Usar": True,
                "Ordem": order,
                "Coluna": str(column),
                "Papel sugerido": infer_role(str(column), series),
                "Papel validado": infer_role(str(column), series),
                "Tipo": str(series.dtype),
                "Preenchimento": round(float(series.notna().mean()), 4),
                "Valores distintos": int(series.nunique(dropna=True)),
            }
        )
    return pd.DataFrame(rows)


def validate_schema(schema: pd.DataFrame, available_columns: list[str]) -> pd.DataFrame:
    required = {"Usar", "Ordem", "Coluna", "Papel validado"}
    missing = required.difference(schema.columns)
    if missing:
        raise ValueError(f"Configuração sem campos obrigatórios: {sorted(missing)}")

    selected = schema[schema["Usar"].astype(bool)].copy()
    if selected.empty:
        raise ValueError("Mantenha pelo menos uma coluna.")
    unknown = set(selected["Coluna"]).difference(available_columns)
    if unknown:
        raise ValueError(f"Colunas desconhecidas: {sorted(unknown)}")
    invalid_roles = set(selected["Papel validado"]).difference(VALID_ROLES)
    if invalid_roles:
        raise ValueError(f"Papéis inválidos: {sorted(invalid_roles)}")

    selected["Ordem"] = pd.to_numeric(selected["Ordem"], errors="coerce")
    if selected["Ordem"].isna().any():
        raise ValueError("Toda coluna mantida precisa de uma ordem numérica.")
    if selected["Ordem"].duplicated().any():
        raise ValueError("Cada coluna mantida precisa de uma ordem diferente.")
    return selected.sort_values(["Ordem", "Coluna"]).reset_index(drop=True)


def apply_schema(frame: pd.DataFrame, schema: pd.DataFrame) -> pd.DataFrame:
    validated = validate_schema(schema, list(frame.columns))
    return frame[validated["Coluna"].tolist()].copy()


def summarize_table(
    frame: pd.DataFrame,
    schema: pd.DataFrame,
    *,
    name: str,
) -> TableSummary:
    validated = validate_schema(schema, list(frame.columns))
    prepared = apply_schema(frame, validated)
    completeness = float(prepared.notna().mean().mean()) if not prepared.empty else 0.0
    exact_duplicates = int(prepared.duplicated().sum())

    identifier_columns = validated.loc[
        validated["Papel validado"].eq("Identificador"), "Coluna"
    ].tolist()
    duplicate_identifiers = None
    if identifier_columns:
        duplicate_identifiers = int(
            prepared.duplicated(subset=identifier_columns).sum()
        )

    def role_columns(role: str) -> tuple[str, ...]:
        return tuple(
            validated.loc[
                validated["Papel validado"].eq(role), "Coluna"
            ].tolist()
        )

    duplicate_rate = exact_duplicates / max(len(prepared), 1)
    identifier_penalty = (
        0.0
        if duplicate_identifiers is None
        else duplicate_identifiers / max(len(prepared), 1)
    )
    role_coverage = min(
        1.0,
        len(set(validated["Papel validado"])) / 4,
    )
    quality_score = 100 * (
        0.50 * completeness
        + 0.25 * (1 - duplicate_rate)
        + 0.15 * (1 - identifier_penalty)
        + 0.10 * role_coverage
    )

    return TableSummary(
        name=name,
        rows=len(prepared),
        columns=len(prepared.columns),
        completeness=completeness,
        exact_duplicate_rows=exact_duplicates,
        duplicate_identifier_rows=duplicate_identifiers,
        text_columns=role_columns("Texto"),
        date_columns=role_columns("Data"),
        category_columns=role_columns("Categoria"),
        metric_columns=role_columns("Métrica"),
        quality_score=round(quality_score, 1),
    )


def category_distribution(
    frame: pd.DataFrame,
    column: str,
    *,
    limit: int = 10,
) -> pd.DataFrame:
    counts = (
        frame[column]
        .fillna("Não informado")
        .astype(str)
        .value_counts(dropna=False)
        .head(limit)
        .rename_axis("Categoria")
        .reset_index(name="Registros")
    )
    counts["Participação"] = counts["Registros"] / max(len(frame), 1)
    return counts


def compare_summaries(
    first: TableSummary,
    second: TableSummary,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Planilha": first.name,
                "Linhas": first.rows,
                "Colunas": first.columns,
                "Preenchimento": first.completeness,
                "Duplicatas exatas": first.exact_duplicate_rows,
                "IDs repetidos": first.duplicate_identifier_rows,
                "Qualidade": first.quality_score,
            },
            {
                "Planilha": second.name,
                "Linhas": second.rows,
                "Colunas": second.columns,
                "Preenchimento": second.completeness,
                "Duplicatas exatas": second.exact_duplicate_rows,
                "IDs repetidos": second.duplicate_identifier_rows,
                "Qualidade": second.quality_score,
            },
        ]
    )
