"""
Dual-Regime Out-of-Time Backtest & Ablation Engine.

Directly addresses the core methodological distinction in CRM pipeline evaluation:
1. Primary Operational Evaluation — Full Open Queue at Cutoff (90-Day Horizon, Uncensored):
   Evaluates ALL `Engaging` deals available in the salesperson's queue on cutoff date `T`
   (using strictly features immutable/known on `T`, excluding `account` to prevent snapshot leakage)
   against realized `Won` outcomes and revenue in `(T, T + 90 days]`.
   Evaluated across 3 rolling cutoffs (`2017-07-31`, `2017-08-31`, `2017-09-30`), both globally
   and within each individual salesperson's queue (Top 20% per rep), including an ablation of
   `P_90d(age only)` vs `P_90d(age, agent)`.
2. Diagnostic Conditional Evaluation — Resolved-Only Subset (`Won` vs `Lost`):
   Evaluates the subpopulation of open deals at cutoff `T` (`2017-06-30`, `N = 970`) that
   eventually closed as `Won` or `Lost` (excluding the 716 deals that remained open).
   Demonstrates transparently that once abandoned backlog is filtered out via future outcome
   conditioning, static CRM fields have near-random discrimination (AUC ~0.50–0.51).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import build_enriched_pipeline
from src.survival_and_scoring import EmpiricalHorizonScorer


def calculate_brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Computes mean squared error between probability forecasts and binary outcomes."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_prob, dtype=float)
    return float(np.mean((y_p - y_t) ** 2))


def calculate_auc_score(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Computes ROC AUC score using the Wilcoxon / Mann-Whitney U rank statistic."""
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


def calculate_lift_at_k(
    y_true: np.ndarray, y_score: np.ndarray, k_pct: float = 0.20
) -> Tuple[float, float, int]:
    """Calculates Lift and Precision in the Top K percent of highest-ranked deals."""
    y_t = np.asarray(y_true)
    y_s = np.asarray(y_score)
    n = len(y_t)
    if n == 0:
        return 1.0, 0.0, 0
    k_count = max(1, int(np.ceil(n * k_pct)))
    # Deterministic tie-breaking via stable mergesort on reversed array or explicit argsort
    order = np.lexsort((np.arange(n), -y_s))
    top_indices = order[:k_count]
    top_positives = int(np.sum(y_t[top_indices]))
    precision_at_k = float(top_positives / k_count)
    base_rate = float(np.mean(y_t))
    lift = float(precision_at_k / base_rate) if base_rate > 0 else 1.0
    return lift, precision_at_k, top_positives


def calculate_top_k_revenue(
    realized_rev: np.ndarray, y_score: np.ndarray, k_pct: float = 0.20
) -> Tuple[float, float]:
    """Calculates realized revenue ($) and share (%) captured in the Top K% of deals."""
    rev = np.asarray(realized_rev, dtype=float)
    y_s = np.asarray(y_score, dtype=float)
    n = len(rev)
    if n == 0 or rev.sum() <= 0:
        return 0.0, 0.0
    k_count = max(1, int(np.ceil(n * k_pct)))
    order = np.lexsort((np.arange(n), -y_s))
    captured = float(rev[order[:k_count]].sum())
    share_pct = float(captured / rev.sum() * 100.0)
    return round(captured, 2), round(share_pct, 2)


def calculate_within_rep_top_k(
    queue_df: pd.DataFrame, score_col: str, k_pct: float = 0.20
) -> Dict[str, float]:
    """
    Evaluates the operational decision where each individual salesperson works
    the Top K% of THEIR OWN open queue on cutoff day.
    """
    total_rev = float(queue_df["realized_rev_90d"].sum())
    sorted_q = queue_df.sort_values(
        [score_col, "opportunity_id"], ascending=[False, True]
    )
    picked_parts = []
    for _, grp in sorted_q.groupby("sales_agent", sort=False):
        k_rep = max(1, int(np.ceil(len(grp) * k_pct)))
        picked_parts.append(grp.iloc[:k_rep])
    picked = pd.concat(picked_parts, ignore_index=True)
    cap_rev = float(picked["realized_rev_90d"].sum())
    return {
        "selected_deals": int(len(picked)),
        "win_rate_pct": round(float(picked["won_90d"].mean() * 100.0), 1),
        "captured_rev_usd": round(cap_rev, 2),
        "captured_rev_share_pct": (
            round(cap_rev / total_rev * 100.0, 1) if total_rev > 0 else 0.0
        ),
    }


def calculate_reliability_diagram_bins(
    y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 5
) -> List[Dict[str, float]]:
    """Calculates observed vs predicted win rates across probability quantiles."""
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
                "calibration_gap": round(
                    float(group["prob"].mean() - group["true"].mean()), 4
                ),
            }
        )
    return bins_summary


@dataclass
class QueueHorizonCutoffReport:
    """Results for a single cutoff date on the Full Open Queue (+90d Horizon)."""

    split_date: str
    horizon_days: int
    train_closed_count: int
    open_queue_count: int
    base_win_rate_90d: float
    total_realized_rev_90d_usd: float
    strategies: Dict[str, Dict[str, float]]
    within_rep_top20: Dict[str, Dict[str, float]]
    calibration_bins: List[Dict[str, float]]

    def to_markdown_table(self) -> str:
        lines = [
            f"**Corte `{self.split_date}` — Fila Aberta Completa (`N = {self.open_queue_count:,}`, Horizonte +{self.horizon_days}d, Taxa Base = {self.base_win_rate_90d*100:.1f}%, Receita Total 90d = US$ {self.total_realized_rev_90d_usd:,.0f})**",
            "",
            "| Estratégia de Priorização | AUC (P) | Brier | Lift @ Top 20% | Precisão @ Top 20% | Receita Capturada Top 20% (Global) | % Receita Total |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
        order = [
            ("ev_90d_full", "🎯 **EV_90d = P_90d(idade, vendedor) × Ticket**"),
            ("ev_90d_age_only", "🔬 Ablação: EV_90d (apenas idade × Ticket)"),
            ("nominal_price", "Baseline 1: Preço Nominal (`sales_price`)"),
            ("freshness", "Baseline 2: Frescor (`-idade` no corte)"),
            ("agent_closed_wr", "Baseline 3: Win Rate Fechado do Vendedor"),
        ]
        for key, label in order:
            m = self.strategies[key]
            brier_str = f"{m['brier']:.4f}" if m.get("brier") is not None else "N/A"
            lines.append(
                f"| {label} | {m['auc_prob']:.4f} | {brier_str} | {m['lift_20']:.2f}x | "
                f"{m['prec_20']*100:.1f}% | US$ {m['rev_20_usd']:,.0f} | **{m['rev_20_share_pct']:.1f}%** |"
            )
        return "\n".join(lines)


@dataclass
class ConditionalResolvedReport:
    """Diagnostic evaluation on the Resolved-Only subpopulation (`Won` vs `Lost`)."""

    split_date: str
    open_total_at_split: int
    censored_excluded_count: int
    resolved_deal_count: int
    resolved_win_rate: float
    strategies: Dict[str, Dict[str, float]]

    def to_markdown_table(self) -> str:
        lines = [
            f"**Diagnóstico Condicional — Subpopulação Resolvida em `{self.split_date}` (`N = {self.resolved_deal_count}` resolvidos; `{self.censored_excluded_count}` não-fechados removidos)**",
            "",
            "| Estratégia (Subconjunto `Won` vs `Lost`) | AUC-ROC | Brier | Lift @ Top 20% | Precisão @ Top 20% |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]
        order = [
            ("ev_90d_full", "Motor EV_90d / P_90d(idade, vendedor)"),
            ("nominal_price", "Baseline 1: Preço Nominal (`sales_price`)"),
            ("freshness", "Baseline 2: Frescor (`-idade` no corte)"),
            ("agent_closed_wr", "Baseline 3: Win Rate Fechado do Vendedor"),
        ]
        for key, label in order:
            m = self.strategies[key]
            brier_str = f"{m['brier']:.4f}" if m.get("brier") is not None else "N/A"
            lines.append(
                f"| {label} | {m['auc']:.4f} | {brier_str} | {m['lift_20']:.2f}x | {m['prec_20']*100:.1f}% |"
            )
        return "\n".join(lines)


def run_prospective_queue_backtest(
    data_dir: Optional[Path] = None,
    split_date: pd.Timestamp = pd.Timestamp("2017-08-31"),
    horizon_days: int = 90,
) -> QueueHorizonCutoffReport:
    """
    Evaluates the full open `Engaging` queue available at `split_date` over `(split_date, split_date + horizon_days]`.
    Uses zero future outcome filtering and zero `account` snapshot leakage.
    """
    df, _ = build_enriched_pipeline(data_dir=data_dir, as_of_date=split_date)

    train_closed = df[
        df["deal_stage"].isin(["Won", "Lost"])
        & df["close_date"].notnull()
        & (df["close_date"] <= split_date)
    ].copy()

    scorer = EmpiricalHorizonScorer()
    scorer.fit(df, as_of_date=split_date)

    # Full open queue on split_date (no filtering on future stage!)
    open_queue = df[
        df["engage_date"].notnull()
        & (df["engage_date"] <= split_date)
        & ((df["close_date"] > split_date) | df["close_date"].isnull())
    ].copy()
    open_queue["cycle_days"] = (split_date - open_queue["engage_date"]).dt.days.astype(
        float
    )

    scored_q = (
        scorer.score_engaging_deals(open_queue)
        .sort_values("opportunity_id", ascending=True)
        .reset_index(drop=True)
    )
    h_end = split_date + pd.Timedelta(days=horizon_days)

    scored_q["won_90d"] = (
        (scored_q["deal_stage"] == "Won")
        & scored_q["close_date"].notnull()
        & (scored_q["close_date"] > split_date)
        & (scored_q["close_date"] <= h_end)
    ).astype(int)
    scored_q["realized_rev_90d"] = np.where(
        scored_q["won_90d"] == 1, scored_q["close_value"].fillna(0.0), 0.0
    )

    # Ablation & baseline columns strictly aligned on `scored_q`
    scored_q["ev_90d_age_only"] = (
        scored_q["p_age_90d"] * scored_q["expected_won_value"]
    ).round(2)
    scored_q["freshness_score"] = -scored_q["cycle_days"].values
    scored_q["agent_closed_wr"] = (
        scored_q["sales_agent"]
        .map(scorer.agent_closed_win_rates_)
        .fillna(scorer.global_closed_win_rate_)
        .astype(float)
    )

    y_true = scored_q["won_90d"].values
    real_rev = scored_q["realized_rev_90d"].values

    def eval_strategy(prob_vec: np.ndarray, rank_vec: np.ndarray, has_brier: bool):
        auc_p = calculate_auc_score(y_true, prob_vec)
        brier = round(calculate_brier_score(y_true, prob_vec), 4) if has_brier else None
        lift20, prec20, _ = calculate_lift_at_k(y_true, rank_vec, 0.20)
        rev20, share20 = calculate_top_k_revenue(real_rev, rank_vec, 0.20)
        return {
            "auc_prob": round(auc_p, 4),
            "brier": brier,
            "lift_20": round(lift20, 2),
            "prec_20": round(prec20, 4),
            "rev_20_usd": rev20,
            "rev_20_share_pct": share20,
        }

    strategies = {
        "ev_90d_full": eval_strategy(
            scored_q["p_win_90d"].values, scored_q["ev_90d"].values, True
        ),
        "ev_90d_age_only": eval_strategy(
            scored_q["p_age_90d"].values, scored_q["ev_90d_age_only"].values, True
        ),
        "nominal_price": eval_strategy(
            scored_q["sales_price"].values, scored_q["sales_price"].values, False
        ),
        "freshness": eval_strategy(
            scored_q["freshness_score"].values,
            scored_q["freshness_score"].values,
            False,
        ),
        "agent_closed_wr": eval_strategy(
            scored_q["agent_closed_wr"].values,
            scored_q["agent_closed_wr"].values,
            True,
        ),
    }

    within_rep = {
        "ev_90d_full": calculate_within_rep_top_k(scored_q, "ev_90d", 0.20),
        "nominal_price": calculate_within_rep_top_k(scored_q, "sales_price", 0.20),
        "freshness": calculate_within_rep_top_k(scored_q, "freshness_score", 0.20),
    }

    calib_bins = calculate_reliability_diagram_bins(
        y_true, scored_q["p_win_90d"].values, n_bins=5
    )

    return QueueHorizonCutoffReport(
        split_date=str(split_date.date()),
        horizon_days=horizon_days,
        train_closed_count=len(train_closed),
        open_queue_count=len(scored_q),
        base_win_rate_90d=round(float(y_true.mean()), 4),
        total_realized_rev_90d_usd=round(float(real_rev.sum()), 2),
        strategies=strategies,
        within_rep_top20=within_rep,
        calibration_bins=calib_bins,
    )


def run_multi_cutoff_queue_evaluation(
    data_dir: Optional[Path] = None,
    cutoffs: Sequence[str] = ("2017-07-31", "2017-08-31", "2017-09-30"),
    horizon_days: int = 90,
) -> List[QueueHorizonCutoffReport]:
    """Runs the 90-day open-queue evaluation across multiple independent monthly cutoffs."""
    return [
        run_prospective_queue_backtest(
            data_dir=data_dir,
            split_date=pd.Timestamp(c),
            horizon_days=horizon_days,
        )
        for c in cutoffs
    ]


def run_conditional_resolved_evaluation(
    data_dir: Optional[Path] = None,
    split_date: pd.Timestamp = pd.Timestamp("2017-06-30"),
) -> ConditionalResolvedReport:
    """
    Diagnostic evaluation on the subpopulation of open deals at `split_date` that
    eventually resolved as `Won` or `Lost` (excluding deals that stayed in `Engaging`).
    Illustrates why static CRM features have AUC ~0.50-0.51 once abandoned deals are removed.
    """
    df, _ = build_enriched_pipeline(data_dir=data_dir, as_of_date=split_date)
    scorer = EmpiricalHorizonScorer()
    scorer.fit(df, as_of_date=split_date)

    open_cohort = df[
        df["engage_date"].notnull()
        & (df["engage_date"] <= split_date)
        & ((df["close_date"] > split_date) | df["close_date"].isnull())
    ].copy()
    open_cohort["cycle_days"] = (split_date - open_cohort["engage_date"]).dt.days.astype(
        float
    )

    resolved = open_cohort[open_cohort["deal_stage"].isin(["Won", "Lost"])].copy()
    censored_count = int(len(open_cohort) - len(resolved))

    scored_res = (
        scorer.score_engaging_deals(resolved)
        .sort_values("opportunity_id", ascending=True)
        .reset_index(drop=True)
    )
    y_true = (scored_res["deal_stage"] == "Won").astype(int).values

    ag_wr = (
        scored_res["sales_agent"]
        .map(scorer.agent_closed_win_rates_)
        .fillna(scorer.global_closed_win_rate_)
        .astype(float)
        .values
    )
    fresh = -scored_res["cycle_days"].values
    price = scored_res["sales_price"].values

    def eval_cond(score_vec: np.ndarray, prob_vec: Optional[np.ndarray] = None):
        auc_v = calculate_auc_score(y_true, score_vec)
        lift20, prec20, _ = calculate_lift_at_k(y_true, score_vec, 0.20)
        # Note: p_win_90d estimates unconditional 90d conversion (~38%), whereas conditional
        # Won/(Won+Lost) base rate is ~62.8%, so Brier on conditional subset is only meaningful
        # for conditional estimators like agent_closed_wr.
        brier_v = (
            round(calculate_brier_score(y_true, prob_vec), 4)
            if prob_vec is not None
            else None
        )
        return {
            "auc": round(auc_v, 4),
            "brier": brier_v,
            "lift_20": round(lift20, 2),
            "prec_20": round(prec20, 4),
        }

    strategies = {
        "ev_90d_full": eval_cond(scored_res["ev_90d"].values, None),
        "nominal_price": eval_cond(price, None),
        "freshness": eval_cond(fresh, None),
        "agent_closed_wr": eval_cond(ag_wr, ag_wr),
    }

    return ConditionalResolvedReport(
        split_date=str(split_date.date()),
        open_total_at_split=len(open_cohort),
        censored_excluded_count=censored_count,
        resolved_deal_count=len(resolved),
        resolved_win_rate=round(float(y_true.mean()), 4),
        strategies=strategies,
    )


def generate_full_backtest_markdown(data_dir: Optional[Path] = None) -> str:
    """Generates the complete dual-regime backtest report in Markdown."""
    queue_reports = run_multi_cutoff_queue_evaluation(data_dir=data_dir)
    cond_report = run_conditional_resolved_evaluation(data_dir=data_dir)

    sections = [
        "# Relatório de Validação Out-of-Time (Dois Regimes + Ablação)\n",
        "## 1. Avaliação Operacional Primária — Fila Aberta Completa no Corte (Horizonte +90 Dias, Sem Censura)\n",
        "> **Pergunta avaliada:** *Diante de todas as oportunidades abertas em `Engaging` na data de corte (sem filtrar pelo futuro e sem usar `account`), quais priorizar hoje para maximizar a receita fechada (`Won`) nos próximos 90 dias?*\n",
    ]
    for rep in queue_reports:
        sections.append(rep.to_markdown_table())
        wr = rep.within_rep_top20
        sections.append(
            f"\n*Seleção Intra-Vendedor (Top 20% dentro da carteira de cada rep em `{rep.split_date}`):* "
            f"**EV_90d** captura **US$ {wr['ev_90d_full']['captured_rev_usd']:,.0f} ({wr['ev_90d_full']['captured_rev_share_pct']:.1f}%)** "
            f"vs Preço Nominal US$ {wr['nominal_price']['captured_rev_usd']:,.0f} ({wr['nominal_price']['captured_rev_share_pct']:.1f}%) "
            f"e Frescor US$ {wr['freshness']['captured_rev_usd']:,.0f} ({wr['freshness']['captured_rev_share_pct']:.1f}%).\n"
        )

    sections.append(
        "\n## 2. Diagnóstico de Limite Estrutural — Subpopulação Condicional Resolvida (`Won` vs `Lost`)\n"
    )
    sections.append(
        "> **Limitação demonstrada:** Quando removemos post-hoc os 716 negócios que permaneceram abertos sem fechar e avaliamos apenas os 970 resolvidos (`Won` vs `Lost`), todos os preditores estáticos do CRM ficam próximos do acaso (AUC ~0,49–0,51). Ou seja: o ganho empírico do motor vem de separar oportunidades vivas do backlog estagnado e ponderá-las pelo ticket mediano — não de prever quem ganha uma negociação ativa sem telemetria de interações.\n"
    )
    sections.append(cond_report.to_markdown_table() + "\n")
    return "\n".join(sections)


if __name__ == "__main__":
    md = generate_full_backtest_markdown()
    try:
        print(md)
    except UnicodeEncodeError:
        print(md.encode("ascii", errors="replace").decode("ascii"))

    artifacts_dir = Path(__file__).resolve().parent.parent / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    with open(artifacts_dir / "backtest_report.md", "w", encoding="utf-8") as f:
        f.write(md)
    print(f"\n[OK] Relatório salvo em: {artifacts_dir / 'backtest_report.md'}")
