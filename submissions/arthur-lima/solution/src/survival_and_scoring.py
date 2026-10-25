"""
Survival-Calibrated Win Probability & Expected Revenue Velocity Engine.

Addresses the 4 core statistical pitfalls identified in the Red Team Review:
1. Right-Censoring & Survivorship Bias: Replaces naive 'score=0 after 138d' with a smooth
   logistic/exponential survival decay curve calibrated on point-in-time cohorts, plus an
   auditable 'Zombie Suspect' flag (>P95 cohort cycle age).
2. CRM Account-Linkage Signal: Incorporates the empirical discovery that deals with a linked
   CRM account convert at ~52% in point-in-time snapshots vs <5% for unlinked orphan deals.
3. 486x Price Dispersion ($55 to $26,768): Computes true Expected Value (EV = P_win * Value),
   Expected Revenue Velocity (EV / Expected Remaining Days), and a normalized hybrid priority
   score (0-100) that balances conversion momentum with financial yield.
4. Separate Scoring Architecture for SDR Queue (500 Prospecting deals without engage_date).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


@dataclass
class ScoringParameters:
    """Calibrated hyperparameters for the RevOps Survival & Velocity Engine."""

    golden_window_days: float = 57.0      # Median time-to-win in historical closed deals
    zombie_p95_days: float = 118.0        # 95th percentile of Won cycle duration
    hard_horizon_days: float = 138.0      # Maximum observed Won cycle in historical window
    decay_lambda: float = 0.022           # Smooth continuous decay rate after median cycle
    unlinked_account_penalty: float = 0.50  # Operational discount for orphan deals needing enrichment
    prior_strength: float = 15.0          # Empirical Bayes shrinkage strength for agent/product win rates
    max_ev_day_ref: float = 1000.0        # Canonical fixed reference for EV/day log normalization
    max_ev_abs_ref: float = 20000.0       # Canonical fixed reference for EV absolute log normalization


class SurvivalLeadScorer:
    """
    Point-in-time calibrated Lead Scorer separating Engaging Deals (Closers)
    from Prospecting Deals (SDRs).
    """

    def __init__(self, params: ScoringParameters | None = None) -> None:
        self.params = params or ScoringParameters()
        self.global_win_rate_: float = 0.6315
        self.agent_win_rates_: Dict[str, float] = {}
        self.product_win_rates_: Dict[str, float] = {}
        self.product_median_cycle_: Dict[str, float] = {}
        self.product_p95_cycle_: Dict[str, float] = {}
        self.account_win_rates_: Dict[str, float] = {}
        self.is_fitted_: bool = False

    def fit(self, df: pd.DataFrame, as_of_date: pd.Timestamp | None = None) -> "SurvivalLeadScorer":
        """
        Fits Empirical Bayes priors for sales_agent, product, and account strictly on deals
        closed on or before `as_of_date` (zero temporal leakage).
        """
        work = df.copy()
        if as_of_date is not None:
            closed = work[
                work["deal_stage"].isin(["Won", "Lost"])
                & work["close_date"].notnull()
                & (work["close_date"] <= as_of_date)
            ].copy()
        else:
            closed = work[work["deal_stage"].isin(["Won", "Lost"])].copy()

        if len(closed) == 0:
            self.is_fitted_ = True
            return self

        closed["is_won"] = (closed["deal_stage"] == "Won").astype(float)
        self.global_win_rate_ = float(closed["is_won"].mean())
        m = self.params.prior_strength

        # 1. Empirical Bayes smoothed Win Rate per Sales Agent
        agent_stats = closed.groupby("sales_agent")["is_won"].agg(["count", "mean"])
        self.agent_win_rates_ = (
            (agent_stats["count"] * agent_stats["mean"] + m * self.global_win_rate_)
            / (agent_stats["count"] + m)
        ).to_dict()

        # 2. Empirical Bayes smoothed Win Rate per Product
        prod_stats = closed.groupby("product")["is_won"].agg(["count", "mean"])
        self.product_win_rates_ = (
            (prod_stats["count"] * prod_stats["mean"] + m * self.global_win_rate_)
            / (prod_stats["count"] + m)
        ).to_dict()

        # 3. Empirical Bayes smoothed Win Rate per Account (for known accounts)
        acc_closed = closed[closed["account"].notnull()]
        if len(acc_closed) > 0:
            acc_stats = acc_closed.groupby("account")["is_won"].agg(["count", "mean"])
            self.account_win_rates_ = (
                (acc_stats["count"] * acc_stats["mean"] + 8.0 * self.global_win_rate_)
                / (acc_stats["count"] + 8.0)
            ).to_dict()

        # 4. Product-specific cycle duration median & P95 on Won deals
        won = closed[closed["deal_stage"] == "Won"].copy()
        if len(won) > 0:
            won["cycle_days"] = (won["close_date"] - won["engage_date"]).dt.days.clip(lower=1)
            self.product_median_cycle_ = won.groupby("product")["cycle_days"].median().to_dict()
            self.product_p95_cycle_ = won.groupby("product")["cycle_days"].quantile(0.95).to_dict()

        self.is_fitted_ = True
        return self

    def compute_aging_survival_factor(self, age_days: pd.Series, product: pd.Series) -> pd.Series:
        """
        Continuous empirical cycle factor S(age | product):
        - Early phase (0 to 14d): Unqualified deals drop out early; factor rises smoothly from ~0.88 to ~1.00.
        - Maturation peak (~40 to 60d): Active engagement converts at highest observed rate (~1.06).
        - Stagnation decay (age > product median): Smooth exponential decay without abrupt cliff,
          floored at 0.50 so enterprise deals remain auditable.
        """
        age = age_days.fillna(30.0).clip(lower=0.0)
        med = product.map(self.product_median_cycle_).fillna(self.params.golden_window_days)

        # Smooth continuous ramp from 0.88 up to ~1.06 around 45-50 days
        ramp = 0.88 + 0.18 * (1.0 - np.exp(-age / 18.0))

        # Smooth continuous decay only for excess days beyond the product median cycle
        excess_age = np.maximum(0.0, age - med)
        decay = np.exp(-self.params.decay_lambda * excess_age)

        combined = np.clip(ramp * decay, 0.50, 1.15)
        return pd.Series(combined, index=age_days.index)

    def score_engaging_deals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Scores active `Engaging` deals (Closer Pipeline) producing:
        - `p_win`: Calibrated win probability [0.01, 0.95]
        - `expected_value`: Monetary Expected Value ($ = p_win * expected_won_value)
        - `expected_days_remaining`: Estimated days left to close
        - `ev_per_day`: Expected Revenue Velocity ($/day)
        - `aging_risk_score`: Continuous 0-100 stagnation index
        - `priority_score`: 0-100 operational ranking score
        - `action_tier`: Prescriptive commercial bucket (🚀 Acelerar Fechamento, 🛠️ Intervenção de Resgate, 🧹 Higienizar / Auditar Zombie)
        """
        if not self.is_fitted_:
            self.fit(df)

        out = df.copy()
        age = out["cycle_days"].fillna(0.0).clip(lower=0.0)

        p_agent = out["sales_agent"].map(self.agent_win_rates_).fillna(self.global_win_rate_)
        p_prod = out["product"].map(self.product_win_rates_).fillna(self.global_win_rate_)
        p_acc = out["account"].map(self.account_win_rates_).fillna(self.global_win_rate_)

        # Base propensity combining agent skill and product conversion around global mean
        account_adj = np.where(
            out["has_account"],
            np.clip(p_acc / self.global_win_rate_, 0.92, 1.08),
            self.params.unlinked_account_penalty,
        )
        base_p = p_agent * (p_prod / self.global_win_rate_) * account_adj


        # Enterprise / parent company slight structural boost when account is linked
        enterprise_boost = np.where(out["has_account"] & out["is_enterprise_account"], 1.04, 1.00)

        survival_factor = self.compute_aging_survival_factor(age, out["product"])
        out["survival_factor"] = survival_factor.round(4)

        raw_p = base_p * enterprise_boost * survival_factor
        out["p_win"] = np.clip(raw_p, 0.015, 0.94).round(4)

        # Cohort thresholds per product
        prod_med = out["product"].map(self.product_median_cycle_).fillna(self.params.golden_window_days)
        prod_p95 = out["product"].map(self.product_p95_cycle_).fillna(self.params.zombie_p95_days)

        out["is_zombie_suspect"] = age > prod_p95
        out["aging_risk_score"] = np.clip(
            100.0 * (1.0 - np.exp(-0.018 * age)), 0.0, 100.0
        ).round(1)

        # Smooth continuous estimate of remaining cycle days without discrete jumps at median
        rem_before = np.maximum(0.0, prod_med - age)
        ext_after = 0.25 * np.maximum(0.0, age - prod_med)
        out["expected_days_remaining"] = (10.0 + rem_before + ext_after).round(1)

        # Monetary Expected Value ($) & Expected Revenue Velocity ($/day)
        out["expected_value"] = (out["p_win"] * out["expected_won_value"]).round(2)
        out["ev_per_day"] = (out["expected_value"] / out["expected_days_remaining"]).round(2)

        # Operational Priority Score (0-100) using fixed canonical ceilings to guarantee stability
        ev_day_norm = np.log1p(out["ev_per_day"]) / np.log1p(self.params.max_ev_day_ref)
        ev_abs_norm = np.log1p(out["expected_value"]) / np.log1p(self.params.max_ev_abs_ref)

        priority_raw = 100.0 * (
            0.50 * out["p_win"]
            + 0.30 * np.clip(ev_day_norm, 0.0, 1.0)
            + 0.20 * np.clip(ev_abs_norm, 0.0, 1.0)
        )
        out["priority_score"] = np.clip(priority_raw, 1.0, 99.5).round(1)

        # 3 Operational Action Tiers with strict cohort boundary definitions
        conditions = [
            out["is_zombie_suspect"],
            (age > prod_med) | (out["p_win"] < 0.30),
        ]
        choices = [
            "🧹 Higienizar / Auditar Zombie",
            "🛠️ Intervenção de Resgate",
        ]
        out["action_tier"] = np.select(
            conditions, choices, default="🚀 Acelerar Fechamento"
        )

        return out.sort_values(["priority_score", "ev_per_day"], ascending=[False, False])

    def score_prospecting_deals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Scores the 500 `Prospecting` deals (SDR Queue) that have no `engage_date` yet.
        Ranks by Account-Product-Agent ICP Fit and Expected First-Touch Yield.
        """
        if not self.is_fitted_:
            self.fit(df)

        out = df.copy()
        p_agent = out["sales_agent"].map(self.agent_win_rates_).fillna(self.global_win_rate_)
        p_prod = out["product"].map(self.product_win_rates_).fillna(self.global_win_rate_)
        p_acc = out["account"].map(self.account_win_rates_).fillna(self.global_win_rate_)

        icp_multiplier = np.where(
            out["has_account"],
            np.where(out["is_enterprise_account"], 1.12, 1.02),
            0.68,  # Unlinked lead requires SDR enrichment before qualification
        )

        out["p_win_icp"] = np.clip(
            self.global_win_rate_
            * (p_agent / self.global_win_rate_)
            * (p_prod / self.global_win_rate_)
            * (p_acc / self.global_win_rate_)
            * icp_multiplier,
            0.10,
            0.88,
        ).round(4)

        out["expected_value_icp"] = (out["p_win_icp"] * out["expected_won_value"]).round(2)
        ev_norm = np.log1p(out["expected_value_icp"]) / np.log1p(
            max(float(out["expected_value_icp"].max()), 100.0)
        )

        out["sdr_fit_score"] = np.clip(
            100.0 * (0.55 * out["p_win_icp"] + 0.45 * ev_norm),
            5.0,
            99.0,
        ).round(1)

        out["sdr_playbook"] = np.where(
            ~out["has_account"],
            "🔍 Enriquecer Conta no CRM + Qualificar ICP (24h)",
            np.where(
                out["expected_won_value"] >= 3000,
                "🔥 Outbound Executivo Multi-Thread (Ligar Hoje)",
                "⚡ Cadência Rápida Inbound + Demo Express",
            ),
        )

        return out.sort_values(["sdr_fit_score", "expected_value_icp"], ascending=[False, False])


def compute_empirical_survival_curve(df: pd.DataFrame, snapshot_date: pd.Timestamp) -> pd.DataFrame:
    """
    Computes the empirical survival and conversion table across cycle age thresholds
    to prove right-censoring at 138 days vs naive closed-only win rate.
    """
    engaged = df[df["engage_date"].notnull()].copy()
    engaged["obs_days"] = (
        engaged["close_date"].fillna(snapshot_date) - engaged["engage_date"]
    ).dt.days.clip(lower=0)

    thresholds: List[int] = [0, 7, 14, 30, 45, 57, 75, 90, 105, 120, 138, 180, 240]
    rows = []
    for t in thresholds:
        sub = engaged[engaged["obs_days"] >= t]
        total = len(sub)
        if total == 0:
            continue
        won = int((sub["deal_stage"] == "Won").sum())
        lost = int((sub["deal_stage"] == "Lost").sum())
        still_open = int((sub["deal_stage"] == "Engaging").sum())
        closed_total = won + lost
        rows.append(
            {
                "age_threshold_days": t,
                "deals_surviving": total,
                "won_count": won,
                "lost_count": lost,
                "still_engaging_censored": still_open,
                "naive_closed_only_win_rate": round(won / closed_total, 4) if closed_total > 0 else 0.0,
                "true_unconditional_win_rate": round(won / total, 4),
                "censoring_rate": round(still_open / total, 4),
            }
        )
    return pd.DataFrame(rows)
