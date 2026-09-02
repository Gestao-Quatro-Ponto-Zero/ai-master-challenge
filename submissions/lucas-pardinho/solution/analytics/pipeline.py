#!/usr/bin/env python3
"""Valida os CSVs do CRM e gera os artefatos consumidos pelo G4 Focus.

O pipeline usa somente a biblioteca padrao do Python. A probabilidade operacional
e estimada por um modelo empirico suavizado, treinado em snapshots semanais de
oportunidades encerradas e avaliado em um holdout temporal por oportunidade.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping, Sequence


SNAPSHOT_DATE = date(2017, 12, 31)
MODEL_VERSION = "1.0.0"
WEEK_DAYS = 7
PREDICTION_HORIZON_DAYS = 60
AGE_PRIOR_STRENGTH = 30.0
CELL_PRIOR_STRENGTH = 15.0

EXPECTED_SCHEMAS: dict[str, list[str]] = {
    "accounts.csv": [
        "account",
        "sector",
        "year_established",
        "revenue",
        "employees",
        "office_location",
        "subsidiary_of",
    ],
    "metadata.csv": ["Table", "Field", "Description"],
    "products.csv": ["product", "series", "sales_price"],
    "sales_pipeline.csv": [
        "opportunity_id",
        "sales_agent",
        "product",
        "account",
        "deal_stage",
        "engage_date",
        "close_date",
        "close_value",
    ],
    "sales_teams.csv": ["sales_agent", "manager", "regional_office"],
}

EXPECTED_STAGES = {"Prospecting", "Engaging", "Won", "Lost"}
QUEUE_ORDER = {
    "Foco agora": 0,
    "Acelerar": 1,
    "Nutrir": 2,
    "Resgatar ou desqualificar": 3,
    "Qualificar": 4,
}


class DataValidationError(RuntimeError):
    """Indica que os dados de entrada nao atendem ao contrato esperado."""


def parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_float(value: str) -> float | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def canonical_product(value: str) -> str:
    return "GTX Pro" if value == "GTXPro" else value


def display_sector(value: str) -> str:
    return "technology" if value == "technolgy" else value


def display_location(value: str) -> str:
    return "Philippines" if value == "Philipines" else value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tables(data_dir: Path) -> dict[str, list[dict[str, str]]]:
    tables: dict[str, list[dict[str, str]]] = {}
    missing = [name for name in EXPECTED_SCHEMAS if not (data_dir / name).is_file()]
    if missing:
        raise DataValidationError(
            "Arquivos obrigatorios ausentes: " + ", ".join(sorted(missing))
        )

    for filename, expected_fields in EXPECTED_SCHEMAS.items():
        with (data_dir / filename).open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames != expected_fields:
                raise DataValidationError(
                    f"Schema invalido em {filename}: esperado {expected_fields}, "
                    f"recebido {reader.fieldnames}"
                )
            tables[filename] = [dict(row) for row in reader]
    return tables


def duplicate_values(rows: Sequence[Mapping[str, str]], field: str) -> list[str]:
    counts = Counter((row.get(field) or "").strip() for row in rows)
    return sorted(value for value, count in counts.items() if value and count > 1)


def rounded(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requer pelo menos um valor")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def validate_tables(
    tables: Mapping[str, list[dict[str, str]]],
    data_dir: Path,
    snapshot_date: date,
) -> dict[str, Any]:
    accounts = tables["accounts.csv"]
    products = tables["products.csv"]
    pipeline = tables["sales_pipeline.csv"]
    teams = tables["sales_teams.csv"]
    metadata = tables["metadata.csv"]

    errors: list[str] = []
    warnings: list[str] = []

    key_specs = [
        ("accounts.csv", accounts, "account"),
        ("products.csv", products, "product"),
        ("sales_pipeline.csv", pipeline, "opportunity_id"),
        ("sales_teams.csv", teams, "sales_agent"),
    ]
    uniqueness: dict[str, Any] = {}
    for filename, rows, field in key_specs:
        blank_count = sum(not (row.get(field) or "").strip() for row in rows)
        duplicates = duplicate_values(rows, field)
        uniqueness[field] = {
            "file": filename,
            "blankCount": blank_count,
            "duplicateCount": len(duplicates),
            "valid": blank_count == 0 and not duplicates,
        }
        if blank_count:
            errors.append(f"{filename}.{field} possui {blank_count} chaves vazias")
        if duplicates:
            errors.append(
                f"{filename}.{field} possui {len(duplicates)} chaves duplicadas"
            )

    account_keys = {row["account"] for row in accounts}
    product_keys = {row["product"] for row in products}
    agent_keys = {row["sales_agent"] for row in teams}

    orphan_agents = sorted(
        {row["sales_agent"] for row in pipeline if row["sales_agent"] not in agent_keys}
    )
    orphan_products = sorted(
        {
            canonical_product(row["product"])
            for row in pipeline
            if canonical_product(row["product"]) not in product_keys
        }
    )
    nonblank_accounts = [row["account"] for row in pipeline if row["account"]]
    orphan_accounts = sorted(
        {account for account in nonblank_accounts if account not in account_keys}
    )
    missing_accounts = sum(not row["account"] for row in pipeline)

    if orphan_agents:
        errors.append(f"{len(orphan_agents)} vendedores nao encontrados em sales_teams")
    if orphan_products:
        errors.append(f"{len(orphan_products)} produtos nao encontrados no catalogo")
    if orphan_accounts:
        errors.append(f"{len(orphan_accounts)} contas preenchidas nao encontradas")
    if missing_accounts:
        warnings.append(
            f"{missing_accounts} oportunidades sem conta; ausencia aceita e sinalizada"
        )

    invalid_stages = sorted(
        {row["deal_stage"] for row in pipeline if row["deal_stage"] not in EXPECTED_STAGES}
    )
    if invalid_stages:
        errors.append("Estagios inesperados: " + ", ".join(invalid_stages))

    date_violations = Counter()
    numeric_violations = Counter()
    stage_counts = Counter(row["deal_stage"] for row in pipeline)
    for row in pipeline:
        stage = row["deal_stage"]
        engage = parse_date(row["engage_date"])
        close = parse_date(row["close_date"])
        close_value = parse_float(row["close_value"])

        if row["engage_date"] and engage is None:
            date_violations["invalidEngageDate"] += 1
        if row["close_date"] and close is None:
            date_violations["invalidCloseDate"] += 1
        if engage and engage > snapshot_date:
            date_violations["engageAfterSnapshot"] += 1
        if close and close > snapshot_date:
            date_violations["closeAfterSnapshot"] += 1
        if engage and close and close < engage:
            date_violations["closeBeforeEngage"] += 1

        if stage == "Prospecting" and (engage or close or row["close_value"]):
            date_violations["prospectingUnexpectedTimeline"] += 1
        if stage == "Engaging" and (not engage or close or row["close_value"]):
            date_violations["engagingInvalidTimeline"] += 1
        if stage in {"Won", "Lost"} and (not engage or not close):
            date_violations["closedMissingTimeline"] += 1
        if stage == "Lost" and close_value != 0:
            numeric_violations["lostCloseValueNotZero"] += 1
        if stage == "Won" and (close_value is None or close_value <= 0):
            numeric_violations["wonCloseValueNotPositive"] += 1

    for name, count in {**date_violations, **numeric_violations}.items():
        if count:
            errors.append(f"{name}: {count} registros")

    invalid_prices = sum(
        parse_float(row["sales_price"]) is None
        or (parse_float(row["sales_price"]) or 0) <= 0
        for row in products
    )
    if invalid_prices:
        errors.append(f"products.csv possui {invalid_prices} precos invalidos")

    expected_metadata_fields = {
        (table.removesuffix(".csv"), field)
        for table, fields in EXPECTED_SCHEMAS.items()
        if table != "metadata.csv"
        for field in fields
    }
    actual_metadata_fields = {(row["Table"], row["Field"]) for row in metadata}
    missing_metadata = sorted(expected_metadata_fields - actual_metadata_fields)
    if missing_metadata:
        errors.append(f"metadata.csv nao descreve {len(missing_metadata)} campos")

    raw_gtxpro = sum(row["product"] == "GTXPro" for row in pipeline)
    sector_fixes = sum(row["sector"] == "technolgy" for row in accounts)
    location_fixes = sum(row["office_location"] == "Philipines" for row in accounts)

    gtk_count = sum(canonical_product(row["product"]) == "GTK 500" for row in pipeline)
    if gtk_count < 50:
        warnings.append(
            f"GTK 500 tem apenas {gtk_count} oportunidades; previsoes recebem baixa confianca"
        )

    report = {
        "snapshotDate": snapshot_date.isoformat(),
        "source": {
            "name": "CRM Sales Predictive Analytics",
            "license": "CC0-1.0",
            "url": "https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics",
            "files": {
                filename: {
                    "rows": len(tables[filename]),
                    "sha256": sha256_file(data_dir / filename),
                }
                for filename in sorted(EXPECTED_SCHEMAS)
            },
        },
        "validationPassed": not errors,
        "errors": errors,
        "warnings": warnings,
        "rowCounts": {filename: len(rows) for filename, rows in sorted(tables.items())},
        "stageCounts": dict(sorted(stage_counts.items())),
        "schemas": {name: fields for name, fields in sorted(EXPECTED_SCHEMAS.items())},
        "uniqueness": uniqueness,
        "referentialIntegrity": {
            "unknownSalesAgents": len(orphan_agents),
            "unknownProductsAfterNormalization": len(orphan_products),
            "unknownNonblankAccounts": len(orphan_accounts),
            "missingAccountsAccepted": missing_accounts,
        },
        "timelineRules": {
            "violations": dict(sorted(date_violations.items())),
            "closedDealsUseCloseFieldsOnly": True,
        },
        "transformations": [
            {
                "file": "sales_pipeline.csv",
                "field": "product",
                "from": "GTXPro",
                "to": "GTX Pro",
                "count": raw_gtxpro,
                "purpose": "canonical_join_repair",
            },
            {
                "file": "accounts.csv",
                "field": "sector",
                "from": "technolgy",
                "to": "technology",
                "count": sector_fixes,
                "purpose": "display_only",
            },
            {
                "file": "accounts.csv",
                "field": "office_location",
                "from": "Philipines",
                "to": "Philippines",
                "count": location_fixes,
                "purpose": "display_only",
            },
        ],
        "modelReadiness": {
            "closedDeals": stage_counts["Won"] + stage_counts["Lost"],
            "openEngagingDeals": stage_counts["Engaging"],
            "openProspectingDeals": stage_counts["Prospecting"],
            "lowSupportProducts": ["GTK 500"] if gtk_count < 50 else [],
        },
    }
    return report


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_normalized_tables(
    tables: Mapping[str, list[dict[str, str]]], normalized_dir: Path
) -> None:
    normalized_dir.mkdir(parents=True, exist_ok=True)
    for filename, rows in tables.items():
        normalized_rows: list[dict[str, str]] = []
        for original in rows:
            row = dict(original)
            if filename == "sales_pipeline.csv":
                row["product"] = canonical_product(row["product"])
            elif filename == "accounts.csv":
                row["sector"] = display_sector(row["sector"])
                row["office_location"] = display_location(row["office_location"])
            normalized_rows.append(row)
        write_csv(normalized_dir / filename, EXPECTED_SCHEMAS[filename], normalized_rows)


def age_bucket(age_days: int) -> str:
    if age_days <= 30:
        return "0-30"
    if age_days <= 60:
        return "31-60"
    if age_days <= 90:
        return "61-90"
    if age_days <= 120:
        return "91-120"
    if age_days <= 138:
        return "121-138"
    return "139+"


def build_weekly_snapshots(
    rows: Sequence[Mapping[str, str]], snapshot_date: date = SNAPSHOT_DATE
) -> list[dict[str, Any]]:
    """Reconstrui janelas com desfecho observavel sem assumir que aberto = perdido.

    Deals encerrados podem contribuir ate o instante anterior ao fechamento, pois o
    evento final e conhecido. Deals ainda Engaging contribuem apenas quando a janela
    inteira de 60 dias terminou ate ``snapshot_date``; nesses pontos, sabemos que nao
    houve Won no horizonte. Prospecting nao tem data de engajamento e fica de fora.
    """
    snapshots: list[dict[str, Any]] = []
    for row in rows:
        if row["deal_stage"] not in {"Won", "Lost", "Engaging"}:
            continue
        engage = parse_date(row["engage_date"])
        close = parse_date(row["close_date"])
        if not engage:
            continue
        if row["deal_stage"] in {"Won", "Lost"}:
            if not close:
                continue
            duration = (close - engage).days
            if duration <= 0:
                continue
            ages = list(range(0, duration, WEEK_DAYS))
            outcome_type = "closed"
        else:
            last_fully_observed_age = (
                snapshot_date - timedelta(days=PREDICTION_HORIZON_DAYS) - engage
            ).days
            if last_fully_observed_age < 0:
                continue
            ages = list(range(0, last_fully_observed_age + 1, WEEK_DAYS))
            duration = None
            outcome_type = "censored_open_observed_window"
        if not ages:
            ages = [0]
        weight = 1.0 / len(ages)
        for age in ages:
            days_to_close = duration - age if duration is not None else None
            snapshots.append(
                {
                    "opportunityId": row["opportunity_id"],
                    "engageDate": engage,
                    "product": canonical_product(row["product"]),
                    "ageDays": age,
                    "ageBucket": age_bucket(age),
                    "label": int(
                        row["deal_stage"] == "Won"
                        and days_to_close is not None
                        and 0 < days_to_close <= PREDICTION_HORIZON_DAYS
                    ),
                    "weight": weight,
                    "observationType": outcome_type,
                }
            )
    return snapshots


def fit_empirical_model(snapshots: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total_weight = sum(float(row["weight"]) for row in snapshots)
    positive_weight = sum(
        float(row["weight"]) * int(row["label"]) for row in snapshots
    )
    if total_weight <= 0:
        raise DataValidationError("Nao ha snapshots historicos validos para treinar o modelo")
    overall = positive_weight / total_weight

    age_totals: defaultdict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    cell_totals: defaultdict[tuple[str, str], list[float]] = defaultdict(
        lambda: [0.0, 0.0]
    )
    for row in snapshots:
        weight = float(row["weight"])
        positive = weight * int(row["label"])
        bucket = str(row["ageBucket"])
        product = str(row["product"])
        age_totals[bucket][0] += positive
        age_totals[bucket][1] += weight
        cell_totals[(product, bucket)][0] += positive
        cell_totals[(product, bucket)][1] += weight

    age_rates: dict[str, dict[str, float]] = {}
    for bucket, (positive, support) in sorted(age_totals.items()):
        rate = (positive + AGE_PRIOR_STRENGTH * overall) / (
            support + AGE_PRIOR_STRENGTH
        )
        age_rates[bucket] = {
            "rate": rounded(rate, 8),
            "effectiveSupport": rounded(support, 4),
        }

    cells: dict[str, dict[str, float]] = {}
    for (product, bucket), (positive, support) in sorted(cell_totals.items()):
        parent_rate = age_rates[bucket]["rate"]
        rate = (positive + CELL_PRIOR_STRENGTH * parent_rate) / (
            support + CELL_PRIOR_STRENGTH
        )
        cells[f"{product}|{bucket}"] = {
            "rate": rounded(rate, 8),
            "effectiveSupport": rounded(support, 4),
        }

    return {
        "overallRate": rounded(overall, 8),
        "effectiveTrainingDeals": rounded(total_weight, 2),
        "ageRates": age_rates,
        "cells": cells,
    }


def predict_empirical(
    model: Mapping[str, Any], product: str, age_days: int
) -> tuple[float, float]:
    bucket = age_bucket(age_days)
    if model.get("selectedStrategy") == "constant_training_rate":
        return float(model["overallRate"]), float(model["effectiveTrainingDeals"])
    cell = model["cells"].get(f"{product}|{bucket}")
    if cell:
        return float(cell["rate"]), float(cell["effectiveSupport"])
    age_stats = model["ageRates"].get(bucket)
    if age_stats:
        return float(age_stats["rate"]), float(age_stats["effectiveSupport"])
    return float(model["overallRate"]), 0.0


def temporal_split(
    modeling_rows: Sequence[Mapping[str, str]], train_fraction: float = 0.8
) -> tuple[list[Mapping[str, str]], list[Mapping[str, str]], date]:
    dated = sorted(
        ((parse_date(row["engage_date"]), row) for row in modeling_rows),
        key=lambda item: (item[0] or date.min, item[1]["opportunity_id"]),
    )
    if len(dated) < 10:
        raise DataValidationError("Amostra insuficiente para holdout temporal")
    raw_index = max(1, min(len(dated) - 2, math.floor(len(dated) * train_fraction) - 1))
    cutoff = dated[raw_index][0]
    if cutoff is None:
        raise DataValidationError("Datas de engajamento insuficientes para split temporal")
    train = [row for engage, row in dated if engage and engage <= cutoff]
    holdout = [row for engage, row in dated if engage and engage > cutoff]
    if not holdout:
        raise DataValidationError("Holdout temporal ficou vazio")
    return train, holdout, cutoff


def select_evaluation_snapshots(
    snapshots: Sequence[Mapping[str, Any]], target_age: int = 30
) -> list[dict[str, Any]]:
    grouped: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in snapshots:
        grouped[str(row["opportunityId"])].append(row)
    selected: list[dict[str, Any]] = []
    for opportunity_id in sorted(grouped):
        choice = min(
            grouped[opportunity_id],
            key=lambda row: (abs(int(row["ageDays"]) - target_age), -int(row["ageDays"])),
        )
        selected.append({**choice, "weight": 1.0})
    return selected


def brier_score(labels: Sequence[int], predictions: Sequence[float]) -> float:
    return sum((prediction - label) ** 2 for label, prediction in zip(labels, predictions)) / len(labels)


def average_precision(labels: Sequence[int], predictions: Sequence[float]) -> float:
    ranked = sorted(
        zip(predictions, labels, range(len(labels))),
        key=lambda item: (-item[0], item[2]),
    )
    positives = sum(labels)
    if positives == 0:
        return 0.0
    true_positives = 0
    precision_sum = 0.0
    for index, (_, label, _) in enumerate(ranked, start=1):
        if label:
            true_positives += 1
            precision_sum += true_positives / index
    return precision_sum / positives


def precision_at_k(
    labels: Sequence[int], predictions: Sequence[float], k: int = 20
) -> float:
    k = min(k, len(labels))
    ranked = sorted(
        zip(predictions, labels, range(len(labels))),
        key=lambda item: (-item[0], item[2]),
    )[:k]
    return sum(label for _, label, _ in ranked) / k if k else 0.0


def evaluate_models(
    train_rows: Sequence[Mapping[str, str]],
    holdout_rows: Sequence[Mapping[str, str]],
    snapshot_date: date = SNAPSHOT_DATE,
) -> tuple[dict[str, Any], dict[str, Any]]:
    train_snapshots = build_weekly_snapshots(train_rows, snapshot_date)
    holdout_snapshots = build_weekly_snapshots(holdout_rows, snapshot_date)
    model = fit_empirical_model(train_snapshots)
    evaluation_rows = select_evaluation_snapshots(holdout_snapshots)
    labels = [int(row["label"]) for row in evaluation_rows]
    empirical_predictions = [
        predict_empirical(model, str(row["product"]), int(row["ageDays"]))[0]
        for row in evaluation_rows
    ]
    baseline_predictions = [float(model["overallRate"])] * len(evaluation_rows)

    def metrics(predictions: Sequence[float]) -> dict[str, float]:
        return {
            "brier": rounded(brier_score(labels, predictions), 5),
            "averagePrecision": rounded(average_precision(labels, predictions), 5),
            "precisionAt20": rounded(precision_at_k(labels, predictions, 20), 5),
        }

    baseline_metrics = metrics(baseline_predictions)
    empirical_metrics = metrics(empirical_predictions)
    empirical_selected = (
        empirical_metrics["brier"] <= baseline_metrics["brier"] * 1.02
        and empirical_metrics["averagePrecision"]
        >= baseline_metrics["averagePrecision"] - 0.005
        and (
            empirical_metrics["precisionAt20"] > baseline_metrics["precisionAt20"]
            or empirical_metrics["averagePrecision"]
            > baseline_metrics["averagePrecision"] + 0.005
            or empirical_metrics["brier"] < baseline_metrics["brier"] - 0.002
        )
    )
    comparison = {
        "evaluationUnit": "one_snapshot_per_holdout_opportunity_nearest_day_30",
        "holdoutObservations": len(evaluation_rows),
        "positiveRate": rounded(sum(labels) / len(labels), 5),
        "baseline": {
            "name": "constant_training_rate",
            **baseline_metrics,
        },
        "empiricalModel": {
            "name": "bayesian_smoothed_product_age",
            **empirical_metrics,
        },
        "selected": (
            "bayesian_smoothed_product_age" if empirical_selected else "constant_training_rate"
        ),
        "selectionRule": (
            "Escolher o modelo segmentado somente quando preserva calibracao e ranking "
            "do baseline no holdout temporal. O score operacional conserva idade e valor "
            "mesmo se a probabilidade constante vencer."
        ),
    }
    return model, comparison


def confidence_for_prediction(product: str, age_days: int, support: float) -> str:
    if age_days > 138 or product == "GTK 500":
        return "low"
    if support >= 50:
        return "high"
    if support >= 15:
        return "medium"
    return "low"


def actionability_score(age_days: int, duration_stats: Mapping[str, float]) -> float:
    p25 = float(duration_stats["p25"])
    p75 = float(duration_stats["p75"])
    maximum = float(duration_stats["max"])
    if age_days > maximum:
        return 0.05
    if age_days <= p25:
        return 0.55 + (0.45 * age_days / max(p25, 1.0))
    if age_days <= p75:
        return 1.0
    return max(0.25, 1.0 - 0.75 * ((age_days - p75) / max(maximum - p75, 1.0)))


def value_percentiles(products: Sequence[Mapping[str, str]]) -> dict[str, float]:
    ordered = sorted(
        (float(row["sales_price"]), row["product"]) for row in products
    )
    if len(ordered) == 1:
        return {ordered[0][1]: 1.0}
    return {
        product: index / (len(ordered) - 1)
        for index, (_, product) in enumerate(ordered)
    }


def account_details(row: Mapping[str, str] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "sector": display_sector(row["sector"]),
        "yearEstablished": int(row["year_established"]),
        "revenueMillions": float(row["revenue"]),
        "employees": int(row["employees"]),
        "officeLocation": display_location(row["office_location"]),
        "subsidiaryOf": row["subsidiary_of"] or None,
    }


def build_open_opportunities(
    tables: Mapping[str, list[dict[str, str]]],
    model: Mapping[str, Any],
    duration_stats: Mapping[str, float],
    snapshot_date: date,
) -> list[dict[str, Any]]:
    pipeline = tables["sales_pipeline.csv"]
    products = tables["products.csv"]
    teams = tables["sales_teams.csv"]
    accounts = tables["accounts.csv"]
    products_by_name = {row["product"]: row for row in products}
    teams_by_agent = {row["sales_agent"]: row for row in teams}
    accounts_by_name = {row["account"]: row for row in accounts}
    value_percentile_by_product = value_percentiles(products)
    overall_rate = float(model["overallRate"])

    opportunities: list[dict[str, Any]] = []
    for raw in pipeline:
        stage = raw["deal_stage"]
        if stage not in {"Engaging", "Prospecting"}:
            continue
        product_raw = raw["product"]
        product = canonical_product(product_raw)
        product_row = products_by_name[product]
        team = teams_by_agent[raw["sales_agent"]]
        engage = parse_date(raw["engage_date"])
        age_days = (snapshot_date - engage).days if engage else None
        price = float(product_row["sales_price"])
        value_factor = value_percentile_by_product[product]
        quality_flags: list[str] = []
        if not raw["account"]:
            quality_flags.append("missing_account")
        if product_raw != product:
            quality_flags.append("product_name_normalized")

        if stage == "Engaging":
            assert age_days is not None
            probability, support = predict_empirical(model, product, age_days)
            actionability = actionability_score(age_days, duration_stats)
            priority = 100 * (
                0.65 * probability + 0.20 * actionability + 0.15 * value_factor
            )
            confidence = confidence_for_prediction(product, age_days, support)
            if age_days > int(duration_stats["max"]):
                quality_flags.append("outside_historical_cycle")
            if product == "GTK 500":
                quality_flags.append("low_product_support")

            reasons: list[str] = []
            if age_days > int(duration_stats["max"]):
                reasons.append(
                    f"Ha {age_days} dias em Engaging; o maior ciclo historico encerrado foi "
                    f"de {int(duration_stats['max'])} dias."
                )
                reasons.append(
                    "A fila de resgate sinaliza falta de proximo passo, nao menor chance "
                    "causal de vitoria eventual."
                )
            elif probability >= overall_rate + 0.04:
                reasons.append("Conversao estimada acima da media historica comparavel.")
            elif probability <= overall_rate - 0.04:
                reasons.append("Conversao estimada abaixo da media historica comparavel.")
            else:
                reasons.append("Conversao estimada proxima da media historica comparavel.")
            if actionability >= 0.8:
                reasons.append("Deal esta na janela historica mais acionavel do ciclo.")
            elif age_days <= int(duration_stats["max"]):
                reasons.append("Timing do ciclo reduz a urgencia relativa desta oportunidade.")
            if value_factor >= 0.75:
                reasons.append("Produto esta no quartil superior de valor de catalogo.")
            elif value_factor <= 0.25:
                reasons.append("Valor potencial baixo em relacao ao catalogo.")

            opportunity = {
                "opportunityId": raw["opportunity_id"],
                "salesAgent": raw["sales_agent"],
                "manager": team["manager"],
                "regionalOffice": team["regional_office"],
                "product": product,
                "productRaw": product_raw,
                "productSeries": product_row["series"],
                "account": raw["account"] or None,
                "accountDetails": account_details(accounts_by_name.get(raw["account"])),
                "dealStage": stage,
                "engageDate": engage.isoformat(),
                "ageDays": age_days,
                "estimatedValue": int(price),
                "probability": rounded(probability, 4),
                "priorityScore": rounded(priority, 1),
                "qualificationScore": None,
                "scoreBreakdown": {
                    "conversion": rounded(probability * 100, 1),
                    "actionability": rounded(actionability * 100, 1),
                    "valuePotential": rounded(value_factor * 100, 1),
                    "weightedContribution": {
                        "conversion": rounded(65 * probability, 1),
                        "actionability": rounded(20 * actionability, 1),
                        "value": rounded(15 * value_factor, 1),
                    },
                },
                "queue": None,
                "confidence": confidence,
                "reasons": reasons,
                "dataQualityFlags": quality_flags,
                "nextAction": None,
                "rankGlobal": None,
                "rankByAgent": None,
            }
        else:
            account_factor = 1.0 if raw["account"] else 0.0
            qualification = 100 * (0.60 * account_factor + 0.40 * value_factor)
            reasons = [
                (
                    "Conta identificada; ja e possivel validar perfil e interlocutores."
                    if raw["account"]
                    else "Conta ainda nao identificada; completar esse dado e o primeiro passo."
                ),
                (
                    "Produto esta no quartil superior de valor potencial."
                    if value_factor >= 0.75
                    else "Valor potencial vem do preco de catalogo, ainda sem validacao comercial."
                ),
            ]
            opportunity = {
                "opportunityId": raw["opportunity_id"],
                "salesAgent": raw["sales_agent"],
                "manager": team["manager"],
                "regionalOffice": team["regional_office"],
                "product": product,
                "productRaw": product_raw,
                "productSeries": product_row["series"],
                "account": raw["account"] or None,
                "accountDetails": account_details(accounts_by_name.get(raw["account"])),
                "dealStage": stage,
                "engageDate": None,
                "ageDays": None,
                "estimatedValue": int(price),
                "probability": None,
                "priorityScore": None,
                "qualificationScore": rounded(qualification, 1),
                "scoreBreakdown": {
                    "accountCompleteness": rounded(account_factor * 100, 1),
                    "valuePotential": rounded(value_factor * 100, 1),
                    "weightedContribution": {
                        "account": rounded(60 * account_factor, 1),
                        "value": rounded(40 * value_factor, 1),
                    },
                },
                "queue": "Qualificar",
                "confidence": "high" if raw["account"] else "medium",
                "reasons": reasons,
                "dataQualityFlags": quality_flags,
                "nextAction": (
                    "Validar fit, interlocutor e criterio de compra antes de engajar."
                    if raw["account"]
                    else "Identificar a conta e completar o contexto minimo de qualificacao."
                ),
                "rankGlobal": None,
                "rankByAgent": None,
            }
        opportunities.append(opportunity)

    engaging_by_agent: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for opportunity in opportunities:
        if opportunity["dealStage"] == "Engaging" and opportunity["ageDays"] <= int(
            duration_stats["max"]
        ):
            engaging_by_agent[opportunity["salesAgent"]].append(opportunity)
    focus_ids: set[str] = set()
    for agent_opportunities in engaging_by_agent.values():
        ranked = sorted(
            agent_opportunities,
            key=lambda row: (-row["priorityScore"], row["opportunityId"]),
        )
        focus_ids.update(row["opportunityId"] for row in ranked[:10])

    for opportunity in opportunities:
        if opportunity["dealStage"] != "Engaging":
            continue
        age_days = int(opportunity["ageDays"])
        if age_days > int(duration_stats["max"]):
            queue = "Resgatar ou desqualificar"
            next_action = (
                "Fazer uma ultima tentativa com prazo; sem sinal concreto, encerrar ou reciclar."
            )
        elif opportunity["opportunityId"] in focus_ids:
            queue = "Foco agora"
            next_action = "Contatar hoje, confirmar necessidade e registrar o proximo passo com data."
        elif age_days > int(duration_stats["p75"]):
            queue = "Acelerar"
            next_action = "Revisar bloqueios e combinar uma acao objetiva para esta semana."
        else:
            queue = "Nutrir"
            next_action = "Manter cadencia e agendar o proximo follow-up antes de o deal esfriar."
        opportunity["queue"] = queue
        opportunity["nextAction"] = next_action

    for stage, score_field in (("Engaging", "priorityScore"), ("Prospecting", "qualificationScore")):
        stage_rows = [row for row in opportunities if row["dealStage"] == stage]
        global_ranked = sorted(
            stage_rows,
            key=lambda row: (-float(row[score_field]), row["opportunityId"]),
        )
        for rank, row in enumerate(global_ranked, start=1):
            row["rankGlobal"] = rank
        by_agent: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in stage_rows:
            by_agent[row["salesAgent"]].append(row)
        for agent_rows in by_agent.values():
            ranked = sorted(
                agent_rows,
                key=lambda row: (-float(row[score_field]), row["opportunityId"]),
            )
            for rank, row in enumerate(ranked, start=1):
                row["rankByAgent"] = rank

    opportunities.sort(
        key=lambda row: (
            QUEUE_ORDER[row["queue"]],
            -float(row["priorityScore"] or row["qualificationScore"] or 0),
            row["opportunityId"],
        )
    )
    return opportunities


def duration_statistics(pipeline: Sequence[Mapping[str, str]]) -> dict[str, float]:
    durations: list[int] = []
    won_durations: list[int] = []
    for row in pipeline:
        if row["deal_stage"] not in {"Won", "Lost"}:
            continue
        engage = parse_date(row["engage_date"])
        close = parse_date(row["close_date"])
        if not engage or not close:
            continue
        duration = (close - engage).days
        durations.append(duration)
        if row["deal_stage"] == "Won":
            won_durations.append(duration)
    return {
        "p25": rounded(quantile(durations, 0.25), 1),
        "median": rounded(median(durations), 1),
        "p75": rounded(quantile(durations, 0.75), 1),
        "p90": rounded(quantile(durations, 0.90), 1),
        "p95": rounded(quantile(durations, 0.95), 1),
        "max": rounded(max(durations), 1),
        "wonMedian": rounded(median(won_durations), 1),
    }


def summarize_opportunity(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: row[key]
        for key in (
            "opportunityId",
            "salesAgent",
            "manager",
            "regionalOffice",
            "product",
            "account",
            "dealStage",
            "ageDays",
            "estimatedValue",
            "probability",
            "priorityScore",
            "qualificationScore",
            "queue",
            "confidence",
            "nextAction",
        )
    }


def build_dashboard(opportunities: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    engaging = [row for row in opportunities if row["dealStage"] == "Engaging"]
    prospecting = [row for row in opportunities if row["dealStage"] == "Prospecting"]

    def group_metrics(field: str) -> list[dict[str, Any]]:
        groups: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for row in opportunities:
            groups[str(row[field])].append(row)
        return [
            {
                "name": name,
                "openOpportunities": len(rows),
                "engaging": sum(row["dealStage"] == "Engaging" for row in rows),
                "prospecting": sum(row["dealStage"] == "Prospecting" for row in rows),
                "focusNow": sum(row["queue"] == "Foco agora" for row in rows),
                "stale": sum(
                    row["queue"] == "Resgatar ou desqualificar" for row in rows
                ),
                "estimatedConversions": rounded(
                    sum(
                        float(row["probability"] or 0)
                        for row in rows
                        if "outside_historical_cycle" not in row["dataQualityFlags"]
                    ),
                    1,
                ),
                "pipelineValue": int(sum(int(row["estimatedValue"]) for row in rows)),
            }
            for name, rows in sorted(groups.items())
        ]

    queue_metrics = []
    for queue, _ in sorted(QUEUE_ORDER.items(), key=lambda item: item[1]):
        rows = [row for row in opportunities if row["queue"] == queue]
        queue_metrics.append(
            {
                "queue": queue,
                "count": len(rows),
                "pipelineValue": int(sum(int(row["estimatedValue"]) for row in rows)),
                "estimatedConversions": rounded(
                    sum(
                        float(row["probability"] or 0)
                        for row in rows
                        if "outside_historical_cycle" not in row["dataQualityFlags"]
                    ),
                    1,
                ),
            }
        )

    return {
        "snapshotDate": SNAPSHOT_DATE.isoformat(),
        "generatedFor": "G4 Focus",
        "summary": {
            "openOpportunities": len(opportunities),
            "engaging": len(engaging),
            "prospecting": len(prospecting),
            "focusNow": sum(row["queue"] == "Foco agora" for row in opportunities),
            "stale": sum(
                row["queue"] == "Resgatar ou desqualificar" for row in opportunities
            ),
            "pipelineValue": int(sum(int(row["estimatedValue"]) for row in opportunities)),
            "engagingPipelineValue": int(
                sum(int(row["estimatedValue"]) for row in engaging)
            ),
            "weightedPipelineValue": int(
                round(
                    sum(
                        int(row["estimatedValue"]) * float(row["probability"])
                        for row in engaging
                        if "outside_historical_cycle" not in row["dataQualityFlags"]
                    )
                )
            ),
            "estimatedConversionsNext60Days": rounded(
                sum(
                    float(row["probability"])
                    for row in engaging
                    if "outside_historical_cycle" not in row["dataQualityFlags"]
                ),
                1,
            ),
            "estimatedConversionsExcludeOutOfSupport": True,
            "outOfClosedCycleSupport": sum(
                "outside_historical_cycle" in row["dataQualityFlags"] for row in engaging
            ),
            "missingAccount": sum(row["account"] is None for row in opportunities),
        },
        "queues": queue_metrics,
        "byRegion": group_metrics("regionalOffice"),
        "byManager": group_metrics("manager"),
        "byAgent": group_metrics("salesAgent"),
        "topOpportunities": [summarize_opportunity(row) for row in engaging[:10]],
    }


def build_model_report(
    pipeline: Sequence[Mapping[str, str]],
    modeling_rows: Sequence[Mapping[str, str]],
    final_model: Mapping[str, Any],
    comparison: Mapping[str, Any],
    cutoff: date,
    train_count: int,
    holdout_count: int,
    duration_stats: Mapping[str, float],
) -> dict[str, Any]:
    closed = [row for row in pipeline if row["deal_stage"] in {"Won", "Lost"}]
    product_outcomes: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in closed:
        product_outcomes[canonical_product(row["product"])][row["deal_stage"]] += 1
    product_stats = []
    for product, counts in sorted(product_outcomes.items()):
        total = counts["Won"] + counts["Lost"]
        product_stats.append(
            {
                "product": product,
                "closedDeals": total,
                "won": counts["Won"],
                "lost": counts["Lost"],
                "historicalWinRate": rounded(counts["Won"] / total, 4),
            }
        )

    q4_start = date(2017, 10, 1)
    before_q4 = [
        row
        for row in closed
        if parse_date(row["close_date"]) and parse_date(row["close_date"]) < q4_start
    ]
    q4 = [
        row
        for row in closed
        if parse_date(row["close_date"]) and parse_date(row["close_date"]) >= q4_start
    ]

    def outcome_period(rows: Sequence[Mapping[str, str]]) -> dict[str, Any]:
        wins = sum(row["deal_stage"] == "Won" for row in rows)
        return {
            "closedDeals": len(rows),
            "won": wins,
            "winRate": rounded(wins / len(rows), 4) if rows else None,
        }

    all_snapshots = build_weekly_snapshots(modeling_rows)
    censored_snapshots = sum(
        row["observationType"] == "censored_open_observed_window"
        for row in all_snapshots
    )
    censored_opportunities = sum(
        row["deal_stage"] == "Engaging"
        and parse_date(row["engage_date"]) is not None
        and (
            SNAPSHOT_DATE
            - timedelta(days=PREDICTION_HORIZON_DAYS)
            - parse_date(row["engage_date"])
        ).days
        >= 0
        for row in modeling_rows
    )

    return {
        "snapshotDate": SNAPSHOT_DATE.isoformat(),
        "modelVersion": MODEL_VERSION,
        "status": "operational_conservative_model",
        "predictionTarget": "P(Won nos proximos 60 dias | oportunidade ainda em Engaging)",
        "selectedProbabilityModel": comparison["selected"],
        "runtimeDecision": {
            "scikitLearnAvailable": False,
            "approach": "evaluated_smoothed_empirical_with_baseline_guardrail",
            "reason": (
                "O runtime validado nao oferece scikit-learn. Foi adotado um estimador "
                "empirico deterministico, auditavel e sem dependencias externas."
            ),
        },
        "training": {
            "closedOpportunities": len(closed),
            "censoredOpenOpportunitiesWithObservedHorizon": censored_opportunities,
            "weeklySnapshots": len(all_snapshots),
            "censoredOpenSnapshots": censored_snapshots,
            "temporalSplit": {
                "trainEngageDateThrough": cutoff.isoformat(),
                "trainOpportunities": train_count,
                "holdoutOpportunities": holdout_count,
                "opportunityIsolation": True,
            },
            "snapshotWeighting": "cada oportunidade soma peso 1, independentemente da duracao",
            "ageBucketsDays": ["0-30", "31-60", "61-90", "91-120", "121-138", "139+"],
            "smoothing": {
                "agePriorStrength": AGE_PRIOR_STRENGTH,
                "productAgePriorStrength": CELL_PRIOR_STRENGTH,
                "noArbitraryStaleConstant": True,
            },
        },
        "features": {
            "candidateUsed": [
                "product_normalized",
                "pipeline_age_bucket_at_prediction_time",
            ],
            "selectedProbabilityFeatures": (
                ["global_observed_target_rate"]
                if comparison["selected"] == "constant_training_rate"
                else ["product_normalized", "pipeline_age_bucket_at_prediction_time"]
            ),
            "excludedToPreventLeakage": [
                "deal_stage_final",
                "close_date",
                "close_value",
                "opportunity_id",
                "account_and_firmographics",
                "sales_agent_manager_region",
            ],
            "policy": (
                "Nenhum campo conhecido apenas depois do desfecho entra na predicao. "
                "Identidade de conta e equipe e exibida, mas nao altera a probabilidade."
            ),
        },
        "evaluation": comparison,
        "outcomeDrift": {
            "before2017Q4": outcome_period(before_q4),
            "from2017Q4": outcome_period(q4),
            "interpretation": (
                "A taxa de Won caiu no Q4. A probabilidade e um apoio conservador, "
                "nao uma verdade permanente; requer recalibracao em producao."
            ),
        },
        "finalModel": final_model,
        "historicalCycleDays": duration_stats,
        "historicalProductOutcomes": product_stats,
        "priorityScore": {
            "appliesTo": "Engaging",
            "formula": "100 * (0.65 * probability + 0.20 * actionability + 0.15 * value_percentile)",
            "components": {
                "probability": "estimativa empirica suavizada por produto e idade",
                "actionability": "janela derivada dos quartis do ciclo historico",
                "valuePercentile": "percentil do preco de catalogo; nunca close_value",
            },
        },
        "qualificationScore": {
            "appliesTo": "Prospecting",
            "formula": "100 * (0.60 * account_identified + 0.40 * catalog_value_percentile)",
            "probabilitySuppressed": True,
        },
        "queueRules": [
            {
                "queue": "Foco agora",
                "rule": "Top 10 por vendedor entre Engaging com idade ate o maximo historico",
            },
            {
                "queue": "Acelerar",
                "rule": "Demais Engaging acima do p75 e ate o maximo historico",
            },
            {"queue": "Nutrir", "rule": "Demais Engaging ate o p75 historico"},
            {
                "queue": "Resgatar ou desqualificar",
                "rule": "Engaging acima do maximo historico de ciclo encerrado",
            },
            {"queue": "Qualificar", "rule": "Todas as oportunidades Prospecting"},
        ],
        "limitations": [
            "O dataset e um snapshot historico sem eventos de atividade, canal, contato ou proximo passo.",
            "O target e reconstruido a partir de snapshots semanais, nao observado nativamente no CRM.",
            "A probabilidade de deals acima de 138 dias e conservadora e tem baixa confianca.",
            "Idade alta nao e interpretada como causa de perda: a fila de resgate e uma regra operacional de actionability.",
            "O preco de catalogo aproxima potencial; desconto e quantidade nao estao disponiveis.",
            "Antes de uso real, o modelo deve ser recalibrado com dados atuais e monitorado por coorte.",
        ],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as target:
        json.dump(payload, target, ensure_ascii=False, indent=2, sort_keys=False)
        target.write("\n")


def run_pipeline(
    data_dir: Path,
    normalized_dir: Path,
    output_dir: Path,
    snapshot_date: date = SNAPSHOT_DATE,
) -> dict[str, Any]:
    tables = read_tables(data_dir)
    quality_report = validate_tables(tables, data_dir, snapshot_date)
    if not quality_report["validationPassed"]:
        raise DataValidationError("; ".join(quality_report["errors"]))

    write_normalized_tables(tables, normalized_dir)
    pipeline = tables["sales_pipeline.csv"]
    modeling_rows = [
        row for row in pipeline if row["deal_stage"] in {"Won", "Lost", "Engaging"}
    ]
    train, holdout, cutoff = temporal_split(modeling_rows)
    _, comparison = evaluate_models(train, holdout, snapshot_date)
    final_model = fit_empirical_model(
        build_weekly_snapshots(modeling_rows, snapshot_date)
    )
    final_model["selectedStrategy"] = comparison["selected"]
    durations = duration_statistics(pipeline)
    opportunities = build_open_opportunities(
        tables, final_model, durations, snapshot_date
    )
    dashboard = build_dashboard(opportunities)
    model_report = build_model_report(
        pipeline,
        modeling_rows,
        final_model,
        comparison,
        cutoff,
        len(train),
        len(holdout),
        durations,
    )

    write_json(output_dir / "opportunities.json", opportunities)
    write_json(output_dir / "dashboard.json", dashboard)
    write_json(output_dir / "model-report.json", model_report)
    write_json(output_dir / "data-quality.json", quality_report)
    return {
        "opportunities": opportunities,
        "dashboard": dashboard,
        "modelReport": model_report,
        "dataQuality": quality_report,
    }


def default_solution_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    solution_dir = default_solution_dir()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=solution_dir / "data" / "raw",
        help="Diretorio contendo os cinco CSVs brutos",
    )
    parser.add_argument(
        "--normalized-dir",
        type=Path,
        default=solution_dir / "data" / "normalized",
        help="Diretorio de saida dos CSVs normalizados",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=solution_dir / "generated",
        help="Diretorio dos JSONs consumidos pela aplicacao",
    )
    parser.add_argument(
        "--snapshot-date",
        type=lambda value: datetime.strptime(value, "%Y-%m-%d").date(),
        default=SNAPSHOT_DATE,
        help="Data de corte no formato YYYY-MM-DD (default: 2017-12-31)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_pipeline(
        data_dir=args.data_dir.resolve(),
        normalized_dir=args.normalized_dir.resolve(),
        output_dir=args.output_dir.resolve(),
        snapshot_date=args.snapshot_date,
    )
    summary = result["dashboard"]["summary"]
    print(
        "Pipeline concluido: "
        f"{summary['openOpportunities']} oportunidades abertas, "
        f"{summary['focusNow']} em Foco agora, "
        f"{summary['stale']} para resgate."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
