"""
Strict Out-of-Time Temporal Backtest & Baseline Benchmark Engine.

Implements the killer validation required by the G4 hiring challenge:
1. Strict Out-of-Time split (train up to 2017-06-30, test on deals closed afterwards).
2. Probabilistic Calibration assessment via Brier Score and Reliability Diagram bins.
3. Discrimination assessment via Area Under the ROC Curve (AUC-ROC).
4. Lift@K metrics (Top 10%, Top 20%, Top 30%) and Captured Revenue ($).
5. Head-to-head comparison against 3 common naive baselines:
   - Baseline 1: Deal Nominal Price (sales_price)
   - Baseline 2: Pure Aging (-cycle_days)
   - Baseline 3: Sales Agent Historical Win Rate
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.data_loader import build_enriched_pipeline
from src.survival_and_scoring import SurvivalLeadScorer


def calculate_brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Computes mean squared error between probability forecasts and true binary outcomes."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_prob, dtype=float)
    return float(np.mean((y_p - y_t) ** 2))


def calculate_auc_score(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """
    Computes ROC AUC score using the Wilcoxon / Mann-Whitney U rank statistic.
    Completely autonomous (works with or without scikit-learn).
    """
    y_t = np.asarray(y_true)
    y_s = np.asarray(y_score)
    pos = y_s[y_t == 1]
    neg = y_s[y_t == 0]
    n_pos = len(pos)
    n_neg = len(neg)
    if n_pos == 0 or n_neg == 0:
        return 0.5
    ranks = pd.Series(y_s).rank().values
    sum_ranks_pos = float(np.sum(ranks[y_t == 1]))
    u = sum_ranks_pos - (n_pos * (n_pos + 1)) / 2.0
    return float(u / (n_pos * n_neg))


def calculate_lift_at_k(y_true: np.ndarray, y_score: np.ndarray, k_pct: float = 0.20) -> Tuple[float, float, int]:
    """
    Calculates Lift and Precision in the Top K percent of highest-ranked deals.
    Lift = (Precision @ Top K) / (Global Base Win Rate)
    """
    y_t = np.asarray(y_true)
    y_s = np.asarray(y_score)
    n = len(y_t)
    if n == 0:
        return 1.0, 0.0, 0
    k_count = max(1, int(np.ceil(n * k_pct)))
    top_indices = np.argsort(y_s)[::-1][:k_count]
    top_positives = int(np.sum(y_t[top_indices]))
    precision_at_k = float(top_positives / k_count)
    base_rate = float(np.mean(y_t))
    lift = float(precision_at_k / base_rate) if base_rate > 0 else 1.0
    return lift, precision_at_k, top_positives


def calculate_reliability_diagram_bins(
    y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 5
) -> List[Dict[str, float]]:
    """Calculates observed vs predicted win rates across probability quintiles."""
    df_eval = pd.DataFrame({"true": y_true, "prob": y_prob})
    df_eval["bin"] = pd.qcut(df_eval["prob"], q=n_bins, duplicates="drop")

    bins_summary = []
    for b_label, group in df_eval.groupby("bin", observed=True):
        bins_summary.append(
            {
                "bin_range": str(b_label),
                "deal_count": int(len(group)),
                "predicted_prob_mean": round(float(group["prob"].mean()), 4),
                "observed_win_rate": round(float(group["true"].mean()), 4),
                "calibration_gap": round(float(group["prob"].mean() - group["true"].mean()), 4),
            }
        )
    return bins_summary


@dataclass
class BacktestReport:
    """Consolidated results of the Out-of-Time Backtest."""

    split_date: str
    train_deal_count: int
    train_win_rate: float
    test_deal_count: int
    test_win_rate: float
    model_metrics: Dict[str, float]
    baseline_value_metrics: Dict[str, float]
    baseline_aging_metrics: Dict[str, float]
    baseline_agent_metrics: Dict[str, float]
    calibration_bins: List[Dict[str, float]]
    captured_revenue_top20_usd: float

    def to_markdown_table(self) -> str:
        """Renders an executive markdown comparison table."""
        lines = [
            "| Estratégia / Modelo | AUC-ROC | Brier Score | Lift @ Top 10% | Lift @ Top 20% | Precisão @ Top 20% |",
            "| :--- | :---: | :---: | :---: | :---: | :---: |",
            f"| **🎯 RevOps Survival Engine (Nosso)** | **{self.model_metrics['auc']:.4f}** | **{self.model_metrics['brier']:.4f}** | **{self.model_metrics['lift_10']:.2f}x** | **{self.model_metrics['lift_20']:.2f}x** | **{self.model_metrics['prec_20']*100:.1f}%** |",
            f"| Baseline 1: Valor Nominal (sales_price) | {self.baseline_value_metrics['auc']:.4f} | N/A | {self.baseline_value_metrics['lift_10']:.2f}x | {self.baseline_value_metrics['lift_20']:.2f}x | {self.baseline_value_metrics['prec_20']*100:.1f}% |",
            f"| Baseline 2: Aging (-cycle_days) | {self.baseline_aging_metrics['auc']:.4f} | N/A | {self.baseline_aging_metrics['lift_10']:.2f}x | {self.baseline_aging_metrics['lift_20']:.2f}x | {self.baseline_aging_metrics['prec_20']*100:.1f}% |",
            f"| Baseline 3: Média do Vendedor | {self.baseline_agent_metrics['auc']:.4f} | {self.baseline_agent_metrics['brier']:.4f} | {self.baseline_agent_metrics['lift_10']:.2f}x | {self.baseline_agent_metrics['lift_20']:.2f}x | {self.baseline_agent_metrics['prec_20']*100:.1f}% |",
        ]
        return "\n".join(lines)


def run_temporal_backtest(
    data_dir: Optional[Path] = None,
    split_date: pd.Timestamp = pd.Timestamp("2017-06-30"),
) -> BacktestReport:
    """
    Executes the full Out-of-Time backtest:
    - Trains strictly on closed deals <= split_date
    - Evaluates on closed deals > split_date
    - Benchmarks against 3 baselines
    """
    df, _ = build_enriched_pipeline(data_dir=data_dir, as_of_date=split_date)
    closed = df[df["deal_stage"].isin(["Won", "Lost"]) & df["close_date"].notnull()].copy()

    train = closed[closed["close_date"] <= split_date].copy()
    test = closed[closed["close_date"] > split_date].copy()

    scorer = SurvivalLeadScorer()
    scorer.fit(df, as_of_date=split_date)

    scored_test = scorer.score_engaging_deals(test)
    y_true = (scored_test["deal_stage"] == "Won").astype(int).values

    # 1. Model metrics (AUC evaluates calibrated probability, Lift evaluates commercial ranking)
    m_auc = calculate_auc_score(y_true, scored_test["p_win"].values)
    m_brier = calculate_brier_score(y_true, scored_test["p_win"].values)
    m_lift10, m_p10, _ = calculate_lift_at_k(y_true, scored_test["priority_score"].values, 0.10)
    m_lift20, m_p20, m_won20 = calculate_lift_at_k(y_true, scored_test["priority_score"].values, 0.20)

    # Top 20% captured real won revenue
    top20_cutoff = int(np.ceil(len(scored_test) * 0.20))
    top20_df = scored_test.iloc[:top20_cutoff]
    captured_rev = float(top20_df[top20_df["deal_stage"] == "Won"]["close_value"].sum())

    # 2. Baseline 1: Nominal value
    b1_scores = test["sales_price"].values
    b1_auc = calculate_auc_score(y_true, b1_scores)
    b1_lift10, _, _ = calculate_lift_at_k(y_true, b1_scores, 0.10)
    b1_lift20, b1_p20, _ = calculate_lift_at_k(y_true, b1_scores, 0.20)

    # 3. Baseline 2: Pure aging (-cycle_days)
    b2_scores = -test["cycle_days"].fillna(999.0).values
    b2_auc = calculate_auc_score(y_true, b2_scores)
    b2_lift10, _, _ = calculate_lift_at_k(y_true, b2_scores, 0.10)
    b2_lift20, b2_p20, _ = calculate_lift_at_k(y_true, b2_scores, 0.20)

    # 4. Baseline 3: Agent historical win rate
    agent_priors = test["sales_agent"].map(scorer.agent_win_rates_).fillna(scorer.global_win_rate_).values
    b3_auc = calculate_auc_score(y_true, agent_priors)
    b3_brier = calculate_brier_score(y_true, agent_priors)
    b3_lift10, _, _ = calculate_lift_at_k(y_true, agent_priors, 0.10)
    b3_lift20, b3_p20, _ = calculate_lift_at_k(y_true, agent_priors, 0.20)

    # 5. Reliability calibration bins
    calib_bins = calculate_reliability_diagram_bins(y_true, scored_test["p_win"].values, n_bins=5)

    return BacktestReport(
        split_date=str(split_date.date()),
        train_deal_count=len(train),
        train_win_rate=round(float((train["deal_stage"] == "Won").mean()), 4),
        test_deal_count=len(test),
        test_win_rate=round(float((test["deal_stage"] == "Won").mean()), 4),
        model_metrics={
            "auc": round(m_auc, 4),
            "brier": round(m_brier, 4),
            "lift_10": round(m_lift10, 2),
            "lift_20": round(m_lift20, 2),
            "prec_20": round(m_p20, 4),
        },
        baseline_value_metrics={
            "auc": round(b1_auc, 4),
            "lift_10": round(b1_lift10, 2),
            "lift_20": round(b1_lift20, 2),
            "prec_20": round(b1_p20, 4),
        },
        baseline_aging_metrics={
            "auc": round(b2_auc, 4),
            "lift_10": round(b2_lift10, 2),
            "lift_20": round(b2_lift20, 2),
            "prec_20": round(b2_p20, 4),
        },
        baseline_agent_metrics={
            "auc": round(b3_auc, 4),
            "brier": round(b3_brier, 4),
            "lift_10": round(b3_lift10, 2),
            "lift_20": round(b3_lift20, 2),
            "prec_20": round(b3_p20, 4),
        },
        calibration_bins=calib_bins,
        captured_revenue_top20_usd=round(captured_rev, 2),
    )


if __name__ == "__main__":
    report = run_temporal_backtest()
    try:
        print(report.to_markdown_table())
    except UnicodeEncodeError:
        print(report.to_markdown_table().encode("ascii", errors="replace").decode("ascii"))
    
    # Save artifacts
    artifacts_dir = Path(__file__).resolve().parent.parent / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    with open(artifacts_dir / "backtest_report.md", "w", encoding="utf-8") as f:
        f.write("# Relatório de Backtest Out-of-Time\n\n")
        f.write(report.to_markdown_table())
        f.write(f"\n\n**Receita Real Capturada no Top 20%:** ${report.captured_revenue_top20_usd:,.2f} USD\n")
    print(f"\n[OK] Artefato salvo com sucesso em: {artifacts_dir / 'backtest_report.md'}")


