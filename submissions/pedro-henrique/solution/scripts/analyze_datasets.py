"""Analisa datasets do challenge e gera `public/insights.json`.

Uso:
  python scripts/analyze_datasets.py
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEPS_ERROR: str | None = None

try:
    import numpy as np
    import pandas as pd
    from sklearn.cluster import KMeans
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder

    ANALYSIS_DEPS_READY = True
except ModuleNotFoundError as exc:
    DEPS_ERROR = str(exc)
    ANALYSIS_DEPS_READY = False


def normalize_name(value: str) -> str:
    raw = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    raw = raw.lower().strip()
    raw = re.sub(r"[^a-z0-9]+", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()


def find_column(df: pd.DataFrame, keyword_groups: list[list[str]]) -> str | None:
    normalized_map = {normalize_name(col): col for col in df.columns}
    normalized_keys = list(normalized_map.keys())

    for group in keyword_groups:
        for candidate in normalized_keys:
            if all(keyword in candidate for keyword in group):
                return normalized_map[candidate]

    return None


def choose_csv(dataset_path: Path) -> Path:
    csvs = list(dataset_path.rglob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {dataset_path}")
    return max(csvs, key=lambda item: item.stat().st_size)


def maybe_find_local_dataset_csvs() -> tuple[Path, Path] | None:
    data_dir = Path("data")
    if not data_dir.exists():
        return None

    csvs = sorted(data_dir.rglob("*.csv"), key=lambda item: item.stat().st_size, reverse=True)
    if len(csvs) < 2:
        return None

    return csvs[0], csvs[1]


def min_valid_count(total_rows: int) -> int:
    return max(30, int(total_rows * 0.08))


def parse_duration_hours(value: Any) -> float | None:
    text = clean_text(value).lower().replace(",", ".")
    if text in {"", "nan", "none", "nat"}:
        return None

    if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return float(text)

    if re.fullmatch(r"\d{1,3}:\d{1,2}(?::\d{1,2})?", text):
        parts = [float(item) for item in text.split(":")]
        if len(parts) == 2:
            hours, minutes = parts
            seconds = 0.0
        else:
            hours, minutes, seconds = parts
        return hours + (minutes / 60.0) + (seconds / 3600.0)

    units = re.findall(r"(-?\d+(?:\.\d+)?)\s*(days?|d|hours?|hrs?|h|minutes?|mins?|m)\b", text)
    if not units:
        return None

    total_hours = 0.0
    for raw_number, unit in units:
        number = float(raw_number)
        if unit.startswith("d"):
            total_hours += number * 24.0
        elif unit.startswith("h"):
            total_hours += number
        else:
            total_hours += number / 60.0

    return total_hours


def derive_resolution_hours(df: pd.DataFrame, cols: dict[str, str | None]) -> pd.Series:
    empty = pd.Series(np.nan, index=df.index, dtype="float64")
    resolution_col = cols.get("resolution_hours")
    if not resolution_col or resolution_col not in df.columns:
        return empty

    threshold = min_valid_count(len(df))
    numeric = pd.to_numeric(df[resolution_col], errors="coerce")
    if int(numeric.notna().sum()) >= threshold:
        return numeric.astype(float)

    parsed_duration = pd.to_numeric(df[resolution_col].map(parse_duration_hours), errors="coerce")
    if int(parsed_duration.notna().sum()) >= threshold:
        return parsed_duration.astype(float)

    first_response_col = cols.get("first_response")
    if first_response_col and first_response_col in df.columns:
        resolved_at = pd.to_datetime(df[resolution_col], errors="coerce")
        first_response_at = pd.to_datetime(df[first_response_col], errors="coerce")
        diff_hours = (resolved_at - first_response_at).dt.total_seconds() / 3600.0

        # Ajuste simples para inconsistências de virada de dia em dados sintéticos.
        diff_hours = diff_hours.where(diff_hours >= 0, diff_hours + 24)
        diff_hours = diff_hours.where((diff_hours >= 0) & (diff_hours <= 24 * 14), np.nan)
        if int(diff_hours.notna().sum()) >= threshold:
            return diff_hours.astype(float)

    return empty


def import_kagglehub_compat():
    try:
        from kagglesdk import kaggle_env  # type: ignore

        if not hasattr(kaggle_env, "get_web_endpoint") and hasattr(kaggle_env, "get_endpoint"):
            kaggle_env.get_web_endpoint = kaggle_env.get_endpoint  # type: ignore[attr-defined]

        import kagglehub  # type: ignore

        return kagglehub
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Falha ao carregar kagglehub/kagglesdk: {exc}") from exc


def find_dataset_csvs() -> tuple[Path, Path]:
    if not ANALYSIS_DEPS_READY:
        raise RuntimeError(DEPS_ERROR or "Dependencias de analise nao instaladas")

    local_csvs = maybe_find_local_dataset_csvs()
    if local_csvs:
        return local_csvs

    kagglehub = import_kagglehub_compat()
    ds1_path = Path(kagglehub.dataset_download("suraj520/customer-support-ticket-dataset"))
    ds2_path = Path(kagglehub.dataset_download("adisongoh/it-service-ticket-classification-dataset"))
    return choose_csv(ds1_path), choose_csv(ds2_path)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text


def extract_support_columns(df: pd.DataFrame) -> dict[str, str | None]:
    return {
        "status": find_column(df, [["status"]]),
        "channel": find_column(df, [["channel"]]),
        "ticket_type": find_column(df, [["ticket", "type"]]) or find_column(df, [["type"]]),
        "priority": find_column(df, [["priority"]]),
        "first_response": find_column(df, [["first", "response"]]),
        "resolution_hours": find_column(df, [["time", "resolution"]]) or find_column(df, [["resolution", "time"]]),
        "description": find_column(df, [["ticket", "description"]]) or find_column(df, [["description"]]),
        "resolution": find_column(df, [["resolution"]]),
        "csat": find_column(df, [["customer", "satisfaction"]])
        or find_column(df, [["satisfaction"]])
        or find_column(df, [["csat"]]),
    }


def normalize_status_bucket(value: Any) -> str:
    normalized = normalize_name(clean_text(value))
    if "pending" in normalized:
        return "pending"
    if "open" in normalized:
        return "open"
    if "close" in normalized:
        return "closed"
    if "resolve" in normalized:
        return "resolved"
    if "deflect" in normalized:
        return "deflected"
    return "other"


def compute_ticket_status_summary(df: pd.DataFrame, cols: dict[str, str | None]) -> dict[str, Any]:
    status_col = cols.get("status")
    if not status_col or status_col not in df.columns:
        return {
            "total_tickets": int(len(df)),
            "open_tickets": 0,
            "pending_tickets": 0,
            "closed_tickets": 0,
            "resolved_tickets": 0,
            "resolved_definition": "tickets fechados com CSAT >= 4",
        }

    status_bucket = df[status_col].astype(str).map(normalize_status_bucket)

    open_tickets = int((status_bucket == "open").sum())
    pending_tickets = int((status_bucket == "pending").sum())
    closed_tickets = int((status_bucket == "closed").sum())

    csat_col = cols.get("csat")
    if csat_col and csat_col in df.columns:
        csat = pd.to_numeric(df[csat_col], errors="coerce")
        resolved_tickets = int(((status_bucket == "closed") & (csat >= 4)).sum())
    else:
        resolved_tickets = closed_tickets

    return {
        "total_tickets": int(len(df)),
        "open_tickets": open_tickets,
        "pending_tickets": pending_tickets,
        "closed_tickets": closed_tickets,
        "resolved_tickets": resolved_tickets,
        "resolved_definition": "tickets fechados com CSAT >= 4",
    }


def compute_channel_bottlenecks(df: pd.DataFrame, cols: dict[str, str | None]) -> list[dict[str, Any]]:
    if not cols["resolution_hours"]:
        return []

    local = df.copy()
    local["resolution_hours"] = derive_resolution_hours(local, cols)
    local = local.dropna(subset=["resolution_hours"])

    if cols["channel"] and cols["channel"] in local.columns:
        local["channel"] = local[cols["channel"]].astype(str)
    else:
        local["channel"] = "Unknown"

    grouped = (
        local.groupby("channel", dropna=False)["resolution_hours"]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
    grouped = grouped[grouped["count"] >= 5]
    grouped = grouped.sort_values("mean", ascending=False).head(8)

    return [
        {
            "channel": str(row.channel),
            "avg_resolution_hours": round(float(row.mean), 2),
            "median_resolution_hours": round(float(row.median), 2),
            "ticket_volume": int(row.count),
        }
        for row in grouped.itertuples(index=False)
    ]


def compute_ticket_type_analysis(df: pd.DataFrame, cols: dict[str, str | None]) -> list[dict[str, Any]]:
    if not cols["ticket_type"]:
        return []

    local = df.copy()
    local["ticket_type"] = local[cols["ticket_type"]].astype(str)
    local["resolution_hours"] = derive_resolution_hours(local, cols)

    grouped = (
        local.groupby("ticket_type", dropna=False)
        .agg(
            ticket_volume=("ticket_type", "size"),
            avg_resolution_hours=("resolution_hours", "mean"),
        )
        .reset_index()
    )
    grouped = grouped.sort_values("ticket_volume", ascending=False).head(8)

    total = max(int(grouped["ticket_volume"].sum()), 1)
    return [
        {
            "ticket_type": str(row.ticket_type),
            "ticket_volume": int(row.ticket_volume),
            "share_pct": round((float(row.ticket_volume) / total) * 100, 1),
            "avg_resolution_hours": round(float(0.0 if pd.isna(row.avg_resolution_hours) else row.avg_resolution_hours), 2),
        }
        for row in grouped.itertuples(index=False)
    ]


def compute_customer_satisfaction_summary(df: pd.DataFrame, cols: dict[str, str | None]) -> dict[str, Any]:
    total_tickets = int(len(df))
    empty = {
        "positive_count": 0,
        "neutral_count": 0,
        "negative_count": 0,
        "unrated_count": total_tickets,
        "positive_pct": 0.0,
        "neutral_pct": 0.0,
        "negative_pct": 0.0,
        "unrated_pct": 100.0,
        "sample_size": 0,
        "total_tickets": total_tickets,
    }

    if not cols["csat"]:
        return empty

    ratings = pd.to_numeric(df[cols["csat"]], errors="coerce")
    rated_mask = ratings.notna()
    rated_ratings = ratings[rated_mask]
    sample_size = int(rated_mask.sum())

    if sample_size == 0:
        return empty

    positive_count = int((rated_ratings >= 4).sum())
    neutral_count = int((rated_ratings == 3).sum())
    negative_count = int((rated_ratings <= 2).sum())
    unrated_count = total_tickets - sample_size

    return {
        "positive_count": positive_count,
        "neutral_count": neutral_count,
        "negative_count": negative_count,
        "unrated_count": unrated_count,
        "positive_pct": round((positive_count / total_tickets) * 100, 1),
        "neutral_pct": round((neutral_count / total_tickets) * 100, 1),
        "negative_pct": round((negative_count / total_tickets) * 100, 1),
        "unrated_pct": round((unrated_count / total_tickets) * 100, 1),
        "sample_size": sample_size,
        "total_tickets": total_tickets,
    }


def build_calculation_rationale() -> list[dict[str, str]]:
    return [
        {
            "metrica": "Tickets abertos",
            "racional": "Contagem de registros cujo status indica atendimento aberto.",
        },
        {
            "metrica": "Tickets pendentes",
            "racional": "Contagem de registros cujo status indica pendência de resposta.",
        },
        {
            "metrica": "Tickets fechados",
            "racional": "Contagem de registros cujo status indica fechamento do ticket.",
        },
        {
            "metrica": "Tickets resolvidos",
            "racional": "Subset dos tickets fechados com avaliação de satisfação maior ou igual a 4.",
        },
        {
            "metrica": "Gargalo por canal",
            "racional": "Tempo médio de resolução por canal, em horas, ordenado do maior para o menor.",
        },
        {
            "metrica": "Análise por tipo de ticket",
            "racional": "Volume e participação percentual de cada tipo de ticket, com tempo médio de resolução.",
        },
        {
            "metrica": "Satisfação do cliente",
            "racional": "Positivo = CSAT >= 4, Neutro = CSAT = 3, Negativo = CSAT <= 2.",
        },
    ]


def compute_flow_bottlenecks(df: pd.DataFrame, cols: dict[str, str | None]) -> list[dict[str, Any]]:
    if not cols["resolution_hours"]:
        return []

    local = df.copy()
    local["resolution_hours"] = derive_resolution_hours(local, cols)
    local = local.dropna(subset=["resolution_hours"])

    local["channel"] = local[cols["channel"]].astype(str) if cols["channel"] else "Unknown"
    local["ticket_type"] = local[cols["ticket_type"]].astype(str) if cols["ticket_type"] else "Unknown"
    local["priority"] = local[cols["priority"]].astype(str) if cols["priority"] else "Unknown"

    grouped = (
        local.groupby(["channel", "ticket_type", "priority"], dropna=False)["resolution_hours"]
        .agg(["mean", "count"])
        .reset_index()
    )
    grouped = grouped[grouped["count"] >= 5]
    grouped = grouped.sort_values("mean", ascending=False).head(10)

    return [
        {
            "segment": f"{row.channel} | {row.ticket_type} | {row.priority}",
            "avg_resolution_hours": round(float(row.mean), 2),
            "sample_size": int(row.count),
        }
        for row in grouped.itertuples(index=False)
    ]


def compute_csat_drivers(df: pd.DataFrame, cols: dict[str, str | None]) -> list[dict[str, Any]]:
    if not cols["csat"]:
        return []

    local = df.copy()
    target = pd.to_numeric(local[cols["csat"]], errors="coerce")
    local = local.assign(csat=target).dropna(subset=["csat"])

    if len(local) < 30:
        return []

    derived_resolution = derive_resolution_hours(local, cols)
    if int(derived_resolution.notna().sum()) >= min_valid_count(len(local)):
        local["derived_resolution_hours"] = derived_resolution

    numerical_candidates = []
    for col in local.columns:
        if col in {cols["csat"], "csat"}:
            continue
        normalized_col = normalize_name(col)
        if any(token in normalized_col for token in (" ticket id", " id", "email", "date")):
            continue
        series = pd.to_numeric(local[col], errors="coerce")
        if series.notna().sum() > max(20, int(0.15 * len(local))):
            local[col] = series
            numerical_candidates.append(col)

    categorical_candidates = []
    for alias in ("channel", "ticket_type", "priority"):
        source_col = cols.get(alias)
        if source_col and source_col in local.columns:
            categorical_candidates.append(source_col)

    feature_cols = list(dict.fromkeys(numerical_candidates[:6] + categorical_candidates))
    if not feature_cols:
        return []

    model_input = local[feature_cols].copy()
    y = local["csat"].copy()

    numeric_cols = [col for col in feature_cols if pd.api.types.is_numeric_dtype(model_input[col])]
    cat_cols = [col for col in feature_cols if col not in numeric_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                    ]
                ),
                numeric_cols,
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                cat_cols,
            ),
        ]
    )

    model = Pipeline(
        [
            ("prep", preprocessor),
            ("rf", RandomForestRegressor(n_estimators=220, random_state=42, n_jobs=-1)),
        ]
    )

    model.fit(model_input, y)

    importances = model.named_steps["rf"].feature_importances_
    names = model.named_steps["prep"].get_feature_names_out()
    grouped_importance: dict[str, float] = {}

    for name, value in zip(names, importances):
        base = name.split("__", 1)[-1].split("_", 1)[0]
        grouped_importance[base] = grouped_importance.get(base, 0.0) + float(value)

    driver_rows: list[dict[str, Any]] = []
    for feature_name, importance in grouped_importance.items():
        source_name = next((col for col in feature_cols if normalize_name(col).startswith(normalize_name(feature_name))), feature_name)
        corr = 0.0
        if source_name in numeric_cols:
            series = pd.to_numeric(local[source_name], errors="coerce")
            corr_value = series.corr(y)
            corr = float(0.0 if pd.isna(corr_value) else corr_value)

        signed_impact = float(np.sign(corr) * importance if corr != 0 else importance)
        driver_rows.append(
            {
                "feature": str(source_name),
                "impact": round(signed_impact, 4),
                "importance": round(float(importance), 4),
                "correlation": round(corr, 4),
            }
        )

    driver_rows.sort(key=lambda item: abs(item["impact"]), reverse=True)
    return driver_rows[:8]


def compute_waste(df: pd.DataFrame, cols: dict[str, str | None], hourly_cost_brl: float) -> dict[str, Any]:
    if not cols["resolution_hours"]:
        return {"recoverable_hours": 0.0, "recoverable_brl": 0.0}

    local = df.copy()
    local["resolution_hours"] = derive_resolution_hours(local, cols)
    local = local.dropna(subset=["resolution_hours"])

    if cols["channel"]:
        local["channel"] = local[cols["channel"]].astype(str)
    else:
        local["channel"] = "Unknown"

    if cols["ticket_type"]:
        local["ticket_type"] = local[cols["ticket_type"]].astype(str)
    else:
        local["ticket_type"] = "Unknown"

    medians = local.groupby(["channel", "ticket_type"])["resolution_hours"].transform("median")
    local["excess"] = np.maximum(local["resolution_hours"] - medians, 0)
    total_excess_hours = float(local["excess"].sum())
    recoverable_hours = round(total_excess_hours, 2)
    recoverable_brl = round(recoverable_hours * hourly_cost_brl, 2)

    return {
        "recoverable_hours": recoverable_hours,
        "recoverable_brl": recoverable_brl,
        "hourly_cost_brl": hourly_cost_brl,
    }


def compute_automation_patterns(df: pd.DataFrame, cols: dict[str, str | None], hourly_cost_brl: float) -> list[dict[str, Any]]:
    if not cols["description"]:
        return []

    descriptions = (
        df[cols["description"]]
        .astype(str)
        .map(clean_text)
        .replace("", np.nan)
        .dropna()
    )
    descriptions = descriptions.head(8000)

    if len(descriptions) < 100:
        return []

    vectorizer = TfidfVectorizer(max_features=3000, stop_words="english")
    matrix = vectorizer.fit_transform(descriptions)

    k = 10
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = kmeans.fit_predict(matrix)

    frame = pd.DataFrame({"description": descriptions.values, "cluster": labels})
    counts = frame["cluster"].value_counts().sort_values(ascending=False)

    patterns: list[dict[str, Any]] = []
    for cluster_id, volume in counts.head(10).items():
        examples = frame[frame["cluster"] == cluster_id]["description"].head(3).tolist()
        exemplar = max(examples, key=len) if examples else f"Cluster {cluster_id}"
        estimated_savings = round(float(volume) * 0.35 * hourly_cost_brl, 2)
        patterns.append(
            {
                "pattern": exemplar[:120],
                "volume": int(volume),
                "estimated_savings_brl": estimated_savings,
            }
        )

    return patterns


def compute_category_volume(df: pd.DataFrame) -> list[dict[str, Any]]:
    col = find_column(df, [["topic", "group"]]) or find_column(df, [["category"]]) or find_column(df, [["label"]])
    if not col:
        return []

    counts = df[col].astype(str).value_counts().head(10)
    return [
        {"category": str(index), "volume": int(value)}
        for index, value in counts.items()
    ]


def run_analysis(hourly_cost_brl: float) -> dict[str, Any]:
    if not ANALYSIS_DEPS_READY:
        raise RuntimeError(DEPS_ERROR or "Dependencias de analise nao instaladas")

    dataset1_csv, dataset2_csv = find_dataset_csvs()
    support_df = pd.read_csv(dataset1_csv)
    it_df = pd.read_csv(dataset2_csv)

    cols = extract_support_columns(support_df)

    status_summary = compute_ticket_status_summary(support_df, cols)
    channel_bottlenecks = compute_channel_bottlenecks(support_df, cols)
    ticket_type_analysis = compute_ticket_type_analysis(support_df, cols)
    customer_satisfaction = compute_customer_satisfaction_summary(support_df, cols)
    flow = compute_flow_bottlenecks(support_df, cols)
    csat = compute_csat_drivers(support_df, cols)
    waste = compute_waste(support_df, cols, hourly_cost_brl)
    patterns = compute_automation_patterns(support_df, cols, hourly_cost_brl)
    categories = compute_category_volume(it_df)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": "kaggle_datasets_real_analysis",
        "dataset_files": {
            "support_dataset_csv": str(dataset1_csv),
            "it_dataset_csv": str(dataset2_csv),
        },
        "ticket_status_summary": status_summary,
        "channel_bottlenecks": channel_bottlenecks,
        "ticket_type_analysis": ticket_type_analysis,
        "customer_satisfaction": customer_satisfaction,
        "calculation_rationale": build_calculation_rationale(),
        "flow_bottlenecks": flow,
        "csat_drivers": csat,
        "waste_estimation": waste,
        "automation_patterns": patterns,
        "it_category_volume": categories,
    }


def fallback_snapshot(hourly_cost_brl: float) -> dict[str, Any]:
    recoverable_hours = 184.0
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": "fallback_sample_snapshot",
        "ticket_status_summary": {
            "total_tickets": 690,
            "open_tickets": 430,
            "pending_tickets": 50,
            "closed_tickets": 210,
            "resolved_tickets": 200,
            "resolved_definition": "tickets fechados com CSAT >= 4",
        },
        "channel_bottlenecks": [
            {"channel": "Email", "avg_resolution_hours": 12.4, "median_resolution_hours": 11.2, "ticket_volume": 220},
            {"channel": "Phone", "avg_resolution_hours": 10.8, "median_resolution_hours": 9.6, "ticket_volume": 184},
        ],
        "ticket_type_analysis": [
            {"ticket_type": "Technical issue", "ticket_volume": 240, "share_pct": 34.8, "avg_resolution_hours": 11.6},
            {"ticket_type": "Billing inquiry", "ticket_volume": 190, "share_pct": 27.5, "avg_resolution_hours": 9.4},
        ],
        "customer_satisfaction": {
            "positive_count": 140,
            "neutral_count": 20,
            "negative_count": 40,
            "positive_pct": 70.0,
            "neutral_pct": 10.0,
            "negative_pct": 20.0,
            "sample_size": 200,
        },
        "calculation_rationale": build_calculation_rationale(),
        "flow_bottlenecks": [
            {"segment": "Email | Access | High", "avg_resolution_hours": 12.4, "sample_size": 220},
            {"segment": "Phone | Network | Critical", "avg_resolution_hours": 10.8, "sample_size": 184},
        ],
        "csat_drivers": [
            {"feature": "Time to Resolution", "impact": -0.72, "importance": 0.36, "correlation": -0.72},
            {"feature": "Ticket Priority", "impact": 0.58, "importance": 0.29, "correlation": 0.31},
        ],
        "waste_estimation": {
            "recoverable_hours": recoverable_hours,
            "recoverable_brl": round(recoverable_hours * hourly_cost_brl, 2),
            "hourly_cost_brl": hourly_cost_brl,
        },
        "automation_patterns": [
            {"pattern": "Reset de senha sem sucesso", "volume": 220, "estimated_savings_brl": 1650},
            {"pattern": "Erro de VPN", "volume": 180, "estimated_savings_brl": 1440},
        ],
        "it_category_volume": [],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera insights do dashboard admin a partir dos datasets")
    parser.add_argument(
        "--hourly-cost",
        type=float,
        default=35.0,
        help="Custo hora-agente em BRL para cálculo de desperdício",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path("public/insights.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        insights = run_analysis(hourly_cost_brl=args.hourly_cost)
        print("Analise real dos datasets concluida com sucesso.")
    except Exception as exc:  # noqa: BLE001
        print(f"Falha ao rodar analise real ({exc}). Gerando snapshot de fallback.")
        insights = fallback_snapshot(hourly_cost_brl=args.hourly_cost)

    output_path.write_text(json.dumps(insights, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Insights gerado em: {output_path.resolve()}")


if __name__ == "__main__":
    main()
