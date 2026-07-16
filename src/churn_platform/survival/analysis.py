"""SPEC-7: Survival Analysis — Kaplan-Meier + Cox Proportional Hazards.

Requisitos:
- REQ-7-001: KM estimator por segmento (industry, plan, billing, country)
- REQ-7-002: CoxPH model com hazard ratios
- REQ-7-003: Predição de tempo até churn por conta
- REQ-7-004: Concordance index > 0.70
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.utils import concordance_index
from matplotlib.colors import to_rgba

matplotlib.use("Agg")

logger = logging.getLogger(__name__)

SEGMENTS = ["industry", "plan_tier_account", "billing_frequency", "country"]
COLORS = ["#d4a84b", "#ef4444", "#22c55e", "#06b6d4", "#f97316", "#8b5cf6", "#ec4899"]
REFERENCE_DATE = pd.Timestamp("2025-01-01")


def prepare_survival_data(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["signup_date"] = pd.to_datetime(result["signup_date"], errors="coerce")
    result["start_date"] = pd.to_datetime(result["start_date"], errors="coerce")

    events = pd.read_csv("submissions/rodolfo/data/ravenstack_churn_events.csv")
    events["churn_date"] = pd.to_datetime(events["churn_date"], errors="coerce")
    churn_dates = events.groupby("account_id")["churn_date"].max().to_dict()

    result["churn_date"] = result["account_id"].map(churn_dates)

    censored = result["churn_flag"] == False
    result.loc[censored, "churn_date"] = REFERENCE_DATE

    result["signup_date"] = result["signup_date"].fillna(REFERENCE_DATE - pd.Timedelta(days=365))
    result["churn_date"] = result["churn_date"].fillna(REFERENCE_DATE)

    result["tenure_days"] = (result["churn_date"] - result["signup_date"]).dt.days.clip(1).astype(int)

    result["tenure_months"] = (result["tenure_days"] / 30.44).round(1)
    result["event_observed"] = result["churn_flag"].astype(int)

    logger.info(
        "Survival data: %s accounts, %s events, tenure 0-%s days",
        len(result), result["event_observed"].sum(), int(result["tenure_days"].max()),
    )
    return result


def plot_km_curves(
    data: pd.DataFrame,
    output_dir: str = "output",
) -> list[str]:
    paths = []
    kmf = KaplanMeierFitter()

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Curvas de Sobrevivência Kaplan-Meier", fontsize=16, fontweight="bold", color="#1a1a1a", y=0.98)

    for idx, segment in enumerate(SEGMENTS):
        ax = axes[idx // 2][idx % 2]
        categories = data[segment].value_counts().index[:6]

        for i, cat in enumerate(categories):
            mask = data[segment] == cat
            if mask.sum() < 5:
                continue
            kmf.fit(
                data.loc[mask, "tenure_days"],
                event_observed=data.loc[mask, "event_observed"],
                label=f"{cat} (n={mask.sum()})",
            )
            kmf.plot_survival_function(
                ax=ax,
                color=COLORS[i % len(COLORS)],
                linewidth=2,
                ci_show=True,
                ci_alpha=0.12,
            )

        ax.set_title(segment.replace("_", " ").title(), fontsize=13, fontweight="bold")
        ax.set_xlabel("Dias desde cadastro", fontsize=10)
        ax.set_ylabel("Probabilidade de Sobrevivência", fontsize=10)
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=8, loc="lower left")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = Path(output_dir) / "survival_km_curves.png"
    fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    paths.append(str(path))
    logger.info("KM curves saved: %s", path)

    fig2, ax2 = plt.subplots(figsize=(14, 6))
    fig2.suptitle("Sobrevivência Global — Kaplan-Meier", fontsize=16, fontweight="bold", color="#1a1a1a")

    kmf.fit(data["tenure_days"], event_observed=data["event_observed"], label="Geral")
    ax2 = kmf.plot_survival_function(ax=ax2, color="#d4a84b", linewidth=3, ci_show=True, ci_alpha=0.15)
    ax2 = plt.gca()

    surv_col = kmf.survival_function_.columns[0]
    for p in [0.25, 0.5, 0.75]:
        surv = kmf.survival_function_[surv_col]
        idx_closest = (surv - p).abs().idxmin()
        ax2.axvline(x=idx_closest, color="#888", linestyle="--", linewidth=0.8, alpha=0.5)
        ax2.text(idx_closest + 10, p - 0.05, f"{int(idx_closest)}d", fontsize=9, color="#888")

    ax2.set_xlabel("Dias desde cadastro", fontsize=12)
    ax2.set_ylabel("Probabilidade de Sobrevivência", fontsize=12)
    ax2.set_ylim(0, 1.05)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    path2 = Path(output_dir) / "survival_global_km.png"
    fig2.savefig(str(path2), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig2)
    paths.append(str(path2))
    logger.info("Global KM saved: %s", path2)

    return paths


def fit_coxph(data: pd.DataFrame) -> dict[str, Any]:
    numeric_cols = [
        "seats_account", "mrr_amount", "upgrade_flag", "downgrade_flag",
        "total_usage_count", "total_error_count", "unique_features", "usage_days",
        "total_tickets", "avg_resolution_hours", "avg_first_response_min",
        "avg_satisfaction", "escalation_count", "high_priority_tickets",
        "is_trial_account", "is_trial_subscription",
    ]

    df_cox = data[numeric_cols + ["tenure_days", "event_observed"]].copy()
    df_cox = df_cox.fillna(0)

    for col in numeric_cols:
        if col not in df_cox.columns:
            df_cox[col] = 0

    df_cox = df_cox.replace([np.inf, -np.inf], 0)
    df_cox = df_cox.dropna()

    if len(df_cox) < 100:
        logger.warning("Too few rows after cleaning: %s", len(df_cox))

    cph = CoxPHFitter(penalizer=0.1)
    cph.fit(df_cox, duration_col="tenure_days", event_col="event_observed", show_progress=False)

    summary = cph.summary.copy()
    hazard_ratios = {}
    for idx in summary.index:
        hazard_ratios[str(idx)] = {
            "hr": round(float(summary.loc[idx, "exp(coef)"]), 4),
            "hr_lower_ci": round(float(summary.loc[idx, "exp(coef) lower 95%"]), 4),
            "hr_upper_ci": round(float(summary.loc[idx, "exp(coef) upper 95%"]), 4),
            "p_value": float(summary.loc[idx, "p"]),
            "significant": bool(summary.loc[idx, "p"] < 0.05),
        }

    c_index = concordance_index(
        df_cox["tenure_days"],
        -cph.predict_partial_hazard(df_cox),
        df_cox["event_observed"],
    )

    result = {
        "concordance_index": round(float(c_index), 4),
        "n_accounts": len(df_cox),
        "n_events": int(df_cox["event_observed"].sum()),
        "hazard_ratios": hazard_ratios,
        "features_tested": len(numeric_cols),
        "features_significant": sum(1 for v in hazard_ratios.values() if v["significant"]),
    }

    logger.info("CoxPH: C-index=%.4f, %s significant features", c_index, result["features_significant"])

    top_features = sorted(hazard_ratios.items(), key=lambda x: -abs(x[1]["hr"] - 1))[:5]
    for feat, hr in top_features:
        direction = "↑ risco" if hr["hr"] > 1 else "↓ risco"
        logger.info("  %s: HR=%.2f (%s, p=%.4f)", feat, hr["hr"], direction, hr["p_value"])

    return result


def plot_coxph_results(
    hazard_ratios: dict[str, Any],
    output_dir: str = "output",
) -> str:
    significant = {k: v for k, v in hazard_ratios.items() if v["significant"]}
    if not significant:
        significant = hazard_ratios

    items = sorted(significant.items(), key=lambda x: abs(x[1]["hr"] - 1))[-12:]
    features = [i[0].replace("_", " ").title() for i in items]
    hrs = [i[1]["hr"] for i in items]
    lower = [i[1]["hr_lower_ci"] for i in items]
    upper = [i[1]["hr_upper_ci"] for i in items]
    colors = ["#ef4444" if h > 1 else "#22c55e" for h in hrs]

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.suptitle("Hazard Ratios — Cox Proportional Hazards", fontsize=16, fontweight="bold", y=0.96)

    y_pos = range(len(features))
    ax.barh(y_pos, hrs, xerr=[np.array(hrs) - np.array(lower), np.array(upper) - np.array(hrs)],
            color=colors, alpha=0.8, capsize=3, height=0.6)

    ax.axvline(x=1, color="#333", linestyle="--", linewidth=1, alpha=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(features, fontsize=10)
    ax.set_xlabel("Hazard Ratio (exp(coef))", fontsize=12)
    ax.set_xlim(0, max(upper) * 1.15)

    ax.text(0.98, 0.02, "↑ risco →", transform=ax.transAxes, ha="right", fontsize=10, color="#ef4444", fontweight="bold")
    ax.grid(True, alpha=0.3, axis="x")

    plt.tight_layout()
    path = Path(output_dir) / "survival_coxph.png"
    fig.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info("CoxPH plot saved: %s", path)
    return str(path)


def predict_survival(
    data: pd.DataFrame,
    kmf: KaplanMeierFitter,
    cph: CoxPHFitter | None = None,
) -> pd.DataFrame:
    result = data[["account_id"]].copy()
    surv_col = kmf.survival_function_.columns[0]
    surv_series = kmf.survival_function_[surv_col]

    def surv_at(t: int) -> float:
        idx = (surv_series.index.values - t).argmin()
        return float(surv_series.iloc[idx])

    result["survival_90d"] = surv_at(90)
    result["survival_180d"] = surv_at(180)
    result["survival_365d"] = surv_at(365)
    median_idx = (surv_series.values - 0.5).argmin()
    result["expected_tenure_days"] = int(surv_series.index[median_idx])

    return result


def run_survival_analysis(
    df: pd.DataFrame,
    output_dir: str = "output",
) -> dict[str, Any]:
    logger.info("=== Survival Analysis ===")

    data = prepare_survival_data(df)

    km_paths = plot_km_curves(data, output_dir)

    coxph_results = fit_coxph(data)

    coxph_path = plot_coxph_results(coxph_results["hazard_ratios"], output_dir)

    predictions = predict_survival(data, KaplanMeierFitter().fit(data["tenure_days"], event_observed=data["event_observed"]))

    pred_path = Path(output_dir) / "survival_predictions.parquet"
    predictions.to_parquet(pred_path, index=False)

    result = {
        "concordance_index": coxph_results["concordance_index"],
        "n_accounts": coxph_results["n_accounts"],
        "n_events": coxph_results["n_events"],
        "significant_features": coxph_results["features_significant"],
        "features_tested": coxph_results["features_tested"],
        "hazard_ratios": coxph_results["hazard_ratios"],
        "outputs": {
            "km_curves": km_paths,
            "coxph_plot": coxph_path,
            "predictions": str(pred_path),
        },
    }

    with open(Path(output_dir) / "survival_results.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    logger.info("=== Survival Analysis concluída ===")
    return result
