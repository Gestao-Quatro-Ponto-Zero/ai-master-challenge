#!/usr/bin/env python3
"""Create a simple historical ranking benchmark for the Lead Scorer logic.

This is not a calibrated forecast validation. It is a lightweight sanity check:
using only older closed opportunities to build historical rates, rank newer
closed opportunities by simple strategies and compare top-k win/revenue capture.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

PRIOR_WEIGHT = 25
CUTS = [0.10, 0.20, 0.30]


def bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def smoothed_rate(won: float, total: float, global_rate: float) -> float:
    return float((won + PRIOR_WEIGHT * global_rate) / (total + PRIOR_WEIGHT))


def minmax(series: pd.Series) -> pd.Series:
    values = series.astype(float)
    low = float(values.min())
    high = float(values.max())
    if high == low:
        return pd.Series(50.0, index=series.index)
    return ((values - low) / (high - low) * 100).clip(0, 100)


def account_quality(row: pd.Series) -> float:
    if not bool_value(row.get("account_known")):
        return 22.0

    score = 62.0
    if row.get("revenue_band") == "over_3b":
        score += 16
    elif row.get("revenue_band") == "1_5b_to_3b":
        score += 12
    elif row.get("revenue_band") == "500m_to_1_5b":
        score += 7

    if row.get("employee_band") == "over_10k":
        score += 12
    elif row.get("employee_band") == "2k_to_10k":
        score += 8
    elif row.get("employee_band") == "500_to_2k":
        score += 4

    age = row.get("account_age_years_as_of_snapshot")
    if not pd.isna(age):
        if float(age) >= 25:
            score += 6
        elif float(age) >= 10:
            score += 3

    return float(max(0, min(100, score)))


def rate_lookup(train: pd.DataFrame, key: str, global_rate: float) -> tuple[dict[str, float], dict[str, int]]:
    grouped = train.groupby(key).agg(won=("is_won", "sum"), total=("opportunity_id", "size")).reset_index()
    grouped["rate"] = grouped.apply(lambda row: smoothed_rate(row["won"], row["total"], global_rate), axis=1)
    return (
        grouped.set_index(key)["rate"].to_dict(),
        grouped.set_index(key)["total"].astype(int).to_dict(),
    )


def build_scores(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    out = test.copy()
    global_rate = float(train["is_won"].mean())

    seller_rate, seller_support = rate_lookup(train, "sales_agent_id", global_rate)
    product_rate, _ = rate_lookup(train, "product_id", global_rate)
    sector_rate, _ = rate_lookup(train[train["sector"].notna()], "sector", global_rate)

    out["seller_rate_score"] = out["sales_agent_id"].map(seller_rate).fillna(global_rate) * 100
    out["product_rate_score"] = out["product_id"].map(product_rate).fillna(global_rate) * 100
    out["sector_rate_score"] = out["sector"].map(sector_rate).fillna(global_rate) * 100
    out["account_quality_score"] = out.apply(account_quality, axis=1)
    out["value_score"] = minmax(np.log1p(out["estimated_deal_value"].fillna(0)))
    out["seller_support"] = out["sales_agent_id"].map(seller_support).fillna(0).astype(int)
    out["confidence_score"] = np.select(
        [
            out["account_known"].map(bool_value) & (out["seller_support"] >= 100),
            out["account_known"].map(bool_value) & (out["seller_support"] >= 50),
        ],
        [90, 72],
        default=45,
    )

    # V1-compatible ranking: explainable priority, not probability.
    out["v1_compatible_score"] = (
        out["value_score"] * 0.25
        + out["seller_rate_score"] * 0.25
        + out["product_rate_score"] * 0.20
        + out["sector_rate_score"] * 0.10
        + out["account_quality_score"] * 0.15
        + out["confidence_score"] * 0.05
    ).round(1)

    out["value_only"] = out["value_score"]
    out["seller_win_rate_baseline"] = out["seller_rate_score"]
    out["product_win_rate_baseline"] = out["product_rate_score"]
    return out


def evaluate_strategy(test: pd.DataFrame, strategy: str, cut: float) -> dict[str, object]:
    ordered = test.sort_values(strategy, ascending=False)
    top_n = max(1, int(round(len(ordered) * cut)))
    top = ordered.head(top_n)
    overall_win_rate = float(test["is_won"].mean())
    top_win_rate = float(top["is_won"].mean())
    total_won_revenue = float(test["close_value"].sum())
    top_won_revenue = float(top["close_value"].sum())

    return {
        "strategy": strategy,
        "top_cut": pct(cut),
        "top_n": top_n,
        "top_win_rate": round(top_win_rate, 4),
        "lift_vs_overall_win_rate": round(top_win_rate / overall_win_rate, 3) if overall_win_rate else 0,
        "won_revenue_capture": round(top_won_revenue / total_won_revenue, 4) if total_won_revenue else 0,
        "avg_score_top": round(float(top[strategy].mean()), 2),
    }


def markdown_table(df: pd.DataFrame) -> str:
    display = df.copy()
    for col in ["top_win_rate", "won_revenue_capture"]:
        display[col] = display[col].map(lambda value: pct(float(value)))
    display["lift_vs_overall_win_rate"] = display["lift_vs_overall_win_rate"].map(lambda value: f"{float(value):.2f}x")
    header = "| " + " | ".join(display.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(display.columns)) + " |"
    rows = ["| " + " | ".join(map(str, row)) + " |" for row in display.to_numpy()]
    return "\n".join([header, separator, *rows])


def write_report(results: pd.DataFrame, metadata: dict[str, object]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    top10 = results[results["top_cut"] == "10.0%"].sort_values("lift_vs_overall_win_rate", ascending=False)
    top20 = results[results["top_cut"] == "20.0%"].sort_values("lift_vs_overall_win_rate", ascending=False)
    v1_top10 = results[(results["strategy"] == "v1_compatible_score") & (results["top_cut"] == "10.0%")].iloc[0]
    value_top10 = results[(results["strategy"] == "value_only") & (results["top_cut"] == "10.0%")].iloc[0]
    v1_top20 = results[(results["strategy"] == "v1_compatible_score") & (results["top_cut"] == "20.0%")].iloc[0]
    value_top20 = results[(results["strategy"] == "value_only") & (results["top_cut"] == "20.0%")].iloc[0]
    report = [
        "# Score Benchmark",
        "",
        "Este benchmark e um sanity check historico, nao uma prova de forecast calibrado.",
        "",
        "Metodologia:",
        "",
        "- usa oportunidades fechadas com `engage_date` conhecido;",
        "- divide o historico por tempo: 70% mais antigo para construir taxas e 30% mais recente para testar ranking;",
        "- compara uma heuristica compativel com o score V1 contra baselines simples;",
        "- mede win rate no topo da lista, lift contra a media e captura de receita ganha.",
        "",
        "## Metadata",
        "",
        "```json",
        json.dumps(metadata, indent=2, ensure_ascii=False),
        "```",
        "",
        "## Resultado principal - Top 10%",
        "",
        markdown_table(top10),
        "",
        "## Resultado principal - Top 20%",
        "",
        markdown_table(top20),
        "",
        "## Todos os cortes",
        "",
        markdown_table(results.sort_values(["top_cut", "strategy"])),
        "",
        "## Leitura pratica",
        "",
        f"- No top 10%, o score V1 teve win rate de {pct(float(v1_top10['top_win_rate']))}, contra {pct(float(value_top10['top_win_rate']))} do baseline por valor.",
        f"- No top 20%, o baseline por valor capturou {pct(float(value_top20['won_revenue_capture']))} da receita ganha, contra {pct(float(v1_top20['won_revenue_capture']))} do score V1.",
        "- Leitura honesta: valor puro e um baseline forte para captura de receita historica; o score V1 nao deve ser vendido como maximizador puro de receita.",
        "- A utilidade do V1 esta em priorizacao operacional com explicabilidade, fit vendedor-oportunidade, saneamento de dados e governanca de remanejamento.",
        "- Como nao ha snapshots reais, este teste deve ser tratado como evidencia direcional para o desafio, nao como validacao de modelo em producao.",
    ]
    (REPORTS_DIR / "score_benchmark.md").write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    enriched = pd.read_csv(PROCESSED_DIR / "opportunities_enriched.csv", parse_dates=["engage_date"])
    closed = enriched[
        (enriched["is_closed"].map(bool_value))
        & enriched["engage_date"].notna()
        & enriched["sales_agent_id"].notna()
        & enriched["product_id"].notna()
    ].copy()
    closed = closed.sort_values("engage_date").reset_index(drop=True)
    split_idx = int(len(closed) * 0.70)
    train = closed.iloc[:split_idx].copy()
    test = closed.iloc[split_idx:].copy()

    scored = build_scores(train, test)
    strategies = [
        "v1_compatible_score",
        "value_only",
        "seller_win_rate_baseline",
        "product_win_rate_baseline",
    ]
    rows = [evaluate_strategy(scored, strategy, cut) for strategy in strategies for cut in CUTS]
    results = pd.DataFrame(rows)

    metadata = {
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "test_overall_win_rate": round(float(test["is_won"].mean()), 4),
        "test_total_won_revenue": round(float(test["close_value"].sum()), 2),
        "split": "70% earliest engage_date train / 30% latest engage_date test",
    }

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(PROCESSED_DIR / "score_benchmark.csv", index=False)
    write_report(results, metadata)
    print(json.dumps({"metadata": metadata, "rows": len(results)}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
