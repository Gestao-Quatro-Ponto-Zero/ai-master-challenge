"""
Parsimonious Empirical 90-Day Horizon Scorer & Operational Queue Triage.

Design principles following adversarial & methodological review:
1. Explicit Decision & Horizon: Ranks active `Engaging` deals by Expected 90-Day Revenue
   (`ev_90d = p_win_90d * expected_won_value`) to answer: "Which open opportunities in the
   queue today maximize realized Won revenue over the next 90 days?"
2. Strict Separation of Statistical Estimation vs. Operational Heuristics:
   - Statistical Estimate (`p_win_90d`): Learned strictly from historical weekly point-in-time
     snapshots whose 90-day outcome windows completed on or before `as_of_date`, combined with
     Empirical Bayes shrinkage on historical agent conversion. Zero arbitrary penalties.
   - CRM Hygiene (`crm_hygiene_status`): Missing `account` (0% in closed deals vs 68.5% in
     Engaging) may reflect closing-time updates; it triggers an enrichment task without
     altering `p_win_90d` (preventing snapshot leakage and unjustified 50% penalties).
   - Operational Triage Buckets (`action_tier`) & Functional Rep Overrides (`operational_rank_group`):
     Explicitly documented workflow rules and human overrides that reorder the operational queue
     while leaving `p_win_90d` and `ev_90d` untouched and auditable.
3. Prospecting Queue (`500` pre-contact deals in Central without `engage_date`):
   Explicitly treated as an operational triage rule (readiness + historical product ticket),
   not a probabilistic model, because pre-contact transitions are unrecorded in the CRM export.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


AGE_BIN_EDGES: List[float] = [-1.0, 14.0, 30.0, 60.0, 90.0, 115.0, 140.0, 10000.0]
AGE_BIN_CENTERS: List[float] = [7.0, 22.0, 45.0, 75.0, 102.5, 127.5, 165.0]


@dataclass
class HorizonScoringParameters:
    """Explicit parameters for the Empirical 90-Day Horizon Scorer."""

    horizon_days: int = 90
    snapshot_stride_days: int = 7
    prior_strength_age: float = 20.0
    prior_strength_agent: float = 50.0
    default_median_cycle_days: float = 57.0
    default_p95_cycle_days: float = 116.0


class EmpiricalHorizonScorer:
    """
    Point-in-time 90-Day Horizon Scorer for `Engaging` deals and deterministic
    operational triage for `Prospecting` leads.
    """

    def __init__(self, params: Optional[HorizonScoringParameters] = None) -> None:
        self.params = params or HorizonScoringParameters()
        self.global_closed_win_rate_: float = 0.6315
        self.global_90d_win_rate_: float = 0.35
        self.age_bin_centers_: np.ndarray = np.array(AGE_BIN_CENTERS, dtype=float)
        self.age_bin_probs_: np.ndarray = np.array(
            [0.38, 0.39, 0.42, 0.42, 0.30, 0.08, 0.01], dtype=float
        )
        self.agent_closed_win_rates_: Dict[str, float] = {}
        self.agent_skill_ratios_: Dict[str, float] = {}
        self.product_median_cycle_: Dict[str, float] = {}
        self.product_p95_cycle_: Dict[str, float] = {}
        self.fitted_snapshot_count_: int = 0
        self.is_fitted_: bool = False

    def fit(
        self, df: pd.DataFrame, as_of_date: Optional[pd.Timestamp] = None
    ) -> "EmpiricalHorizonScorer":
        """
        Fits the 90-day empirical age curve and agent Empirical Bayes ratios using
        ONLY events observable on or before `as_of_date` (zero future leakage).
        """
        work = df.copy()
        cutoff = (
            pd.Timestamp(as_of_date)
            if as_of_date is not None
            else pd.Timestamp("2017-12-31")
        )

        # Strictly censor any event occurring after `cutoff`
        engaged_obs = work[
            work["engage_date"].notnull() & (work["engage_date"] <= cutoff)
        ].copy()

        closed_known_mask = (
            engaged_obs["deal_stage"].isin(["Won", "Lost"])
            & engaged_obs["close_date"].notnull()
            & (engaged_obs["close_date"] <= cutoff)
        )
        closed = engaged_obs[closed_known_mask].copy()

        if len(closed) == 0:
            self.fitted_snapshot_count_ = 0
            self.is_fitted_ = True
            return self

        closed["is_won"] = (closed["deal_stage"] == "Won").astype(float)
        self.global_closed_win_rate_ = float(closed["is_won"].mean())

        # 1. Empirical Bayes conditional agent skill ratio on known closed deals
        m_ag = self.params.prior_strength_agent
        ag_stats = closed.groupby("sales_agent")["is_won"].agg(["count", "mean"])
        smoothed_ag = (
            ag_stats["count"] * ag_stats["mean"] + m_ag * self.global_closed_win_rate_
        ) / (ag_stats["count"] + m_ag)
        self.agent_closed_win_rates_ = smoothed_ag.to_dict()
        if self.global_closed_win_rate_ > 0:
            self.agent_skill_ratios_ = (
                smoothed_ag / self.global_closed_win_rate_
            ).to_dict()

        # 2. Product-specific Won cycle duration thresholds (median & P95) for operational buckets
        won = closed[closed["deal_stage"] == "Won"].copy()
        if len(won) > 0:
            won["cycle"] = (
                (won["close_date"] - won["engage_date"]).dt.days.clip(lower=1)
            )
            self.product_median_cycle_ = (
                won.groupby("product")["cycle"].median().to_dict()
            )
            self.product_p95_cycle_ = (
                won.groupby("product")["cycle"].quantile(0.95).to_dict()
            )

        # 3. Empirical 90-day conversion curve from completed historical snapshots s <= cutoff - H
        engaged_obs["known_stage"] = np.where(
            closed_known_mask, engaged_obs["deal_stage"], "Engaging"
        )
        engaged_obs["known_close_date"] = engaged_obs["close_date"].where(
            closed_known_mask, pd.NaT
        )

        first_close = closed["close_date"].min()
        h_delta = pd.Timedelta(days=self.params.horizon_days)
        last_valid_snapshot = cutoff - h_delta

        if pd.notnull(first_close) and last_valid_snapshot >= first_close:
            snap_dates = pd.date_range(
                first_close,
                last_valid_snapshot,
                freq=f"{self.params.snapshot_stride_days}D",
            )
            snaps = []
            for s in snap_dates:
                open_s = engaged_obs[
                    (engaged_obs["engage_date"] <= s)
                    & (
                        engaged_obs["known_close_date"].isnull()
                        | (engaged_obs["known_close_date"] > s)
                    )
                ].copy()
                if len(open_s) == 0:
                    continue
                open_s["age"] = (s - open_s["engage_date"]).dt.days.astype(float)
                open_s["won_in_h"] = (
                    (open_s["known_stage"] == "Won")
                    & (open_s["known_close_date"] > s)
                    & (open_s["known_close_date"] <= s + h_delta)
                ).astype(float)
                snaps.append(open_s[["age", "won_in_h"]])

            if len(snaps) > 0:
                hist = pd.concat(snaps, ignore_index=True)
                self.fitted_snapshot_count_ = len(snap_dates)
                self.global_90d_win_rate_ = float(hist["won_in_h"].mean())
                hist["age_bin"] = pd.cut(hist["age"], bins=AGE_BIN_EDGES)
                b_stats = hist.groupby("age_bin", observed=False)["won_in_h"].agg(
                    ["count", "mean"]
                )
                m_age = self.params.prior_strength_age
                b_means = b_stats["mean"].fillna(0.0)
                b_probs = (
                    b_stats["count"] * b_means + m_age * self.global_90d_win_rate_
                ) / (b_stats["count"] + m_age)
                # For bins with zero historical observations in very short histories, keep prior
                self.age_bin_probs_ = b_probs.values.astype(float)

        self.is_fitted_ = True
        return self

    def predict_age_90d_prob(self, age_days: pd.Series) -> pd.Series:
        """
        Evaluates continuous piecewise-linear empirical 90-day conversion rate by deal age.
        Excludes account/sector fields to prevent snapshot leakage.
        """
        age_vals = age_days.fillna(0.0).clip(lower=0.0).astype(float).values
        probs = np.interp(age_vals, self.age_bin_centers_, self.age_bin_probs_)
        return pd.Series(np.clip(probs, 0.001, 0.95), index=age_days.index)

    def score_engaging_deals(
        self,
        df: pd.DataFrame,
        overrides: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> pd.DataFrame:
        """
        Scores `Engaging` opportunities producing:
        - `p_age_90d`: Base empirical 90-day win rate for the deal's current age
        - `p_win_90d`: Empirical 90-day win probability (`p_age_90d * agent_skill_ratio`)
        - `ev_90d`: Expected 90-Day Revenue in USD (`p_win_90d * expected_won_value`)
        - `is_stale_p95`: Operational hygiene flag (`cycle_days > product_p95_cycle`)
        - `statistical_tier`: Triage tier prior to human override
        - `action_tier`: Final operational tier (incorporating any active rep override)
        - `operational_rank_group`: 0=Promoted, 1=Standard Queue, 2=Paused, 3=Archived
        """
        if not self.is_fitted_:
            self.fit(df)

        out = df.copy()
        age = out["cycle_days"].fillna(0.0).clip(lower=0.0).astype(float)

        if "has_account" not in out.columns:
            out["has_account"] = out["account"].notnull() & (
                out["account"].astype(str).str.strip() != ""
            )
        if "crm_hygiene_status" not in out.columns:
            out["crm_hygiene_status"] = np.where(
                out["has_account"],
                "✅ Conta Vinculada",
                "⚠️ Sem Conta (Enriquecer CRM)",
            )

        p_age = self.predict_age_90d_prob(age)
        ag_ratio = (
            out["sales_agent"].map(self.agent_skill_ratios_).fillna(1.0).astype(float)
        )

        # H1 — Arthur autorizou a simplificação após as auditorias dos agentes;
        # implementação assistida por IA. Não reintroduzir pesos EV/dia/enterprise
        # sem avaliação comparativa. Origem e limites: PROCESS_LOG.md, mapa H1–H5.
        out["p_age_90d"] = p_age.round(4)
        out["p_win_90d"] = np.clip(p_age * ag_ratio, 0.001, 0.95).round(4)
        out["ev_90d"] = (out["p_win_90d"] * out["expected_won_value"]).round(2)

        prod_med = (
            out["product"]
            .map(self.product_median_cycle_)
            .fillna(self.params.default_median_cycle_days)
        )
        prod_p95 = (
            out["product"]
            .map(self.product_p95_cycle_)
            .fillna(self.params.default_p95_cycle_days)
        )

        out["product_median_cycle"] = prod_med.round(1)
        out["product_p95_cycle"] = prod_p95.round(1)
        out["is_stale_p95"] = age > prod_p95

        # Explicit operational triage tiers (clearly distinguished from statistical p_win_90d)
        conditions = [
            out["is_stale_p95"],
            age > prod_med,
        ]
        choices = [
            "🧹 Higienizar (>P95 Ciclo)",
            "🛠️ Revisar Gargalo (>Mediana)",
        ]
        out["statistical_tier"] = np.select(
            conditions, choices, default="🚀 Priorizar (Janela Ativa)"
        )

        out = apply_rep_overrides(out, overrides)

        return out.sort_values(
            ["operational_rank_group", "ev_90d", "p_win_90d", "opportunity_id"],
            ascending=[True, False, False, True],
        ).reset_index(drop=True)

    def score_prospecting_deals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Deterministic operational triage for the 500 `Prospecting` leads (all in Central)
        that lack `engage_date`. Explicitly non-probabilistic because pre-engagement
        disqualifications are not recorded in the historical CRM snapshot.
        """
        if not self.is_fitted_:
            self.fit(df)

        out = df.copy()
        if "has_account" not in out.columns:
            out["has_account"] = out["account"].notnull() & (
                out["account"].astype(str).str.strip() != ""
            )
        if "crm_hygiene_status" not in out.columns:
            out["crm_hygiene_status"] = np.where(
                out["has_account"],
                "✅ Conta Vinculada",
                "⚠️ Sem Conta (Enriquecer CRM)",
            )

        out["agent_hist_win_rate"] = (
            out["sales_agent"]
            .map(self.agent_closed_win_rates_)
            .fillna(self.global_closed_win_rate_)
            .round(4)
        )

        out["sdr_triage_lane"] = np.where(
            out["has_account"],
            "1. Pronto p/ 1º Contato (Conta Vinculada)",
            "2. Enriquecer Cadastro antes do Contato",
        )
        out["sdr_playbook"] = np.where(
            ~out["has_account"],
            "🔍 Mapear Conta/Decisor no CRM antes da abordagem (24h)",
            np.where(
                out["expected_won_value"] >= 3000.0,
                "📞 Abordagem Consultiva Direta (Ticket Alto)",
                "⚡ Cadência Padrão de Qualificação (Ticket Volume)",
            ),
        )

        return out.sort_values(
            [
                "has_account",
                "expected_won_value",
                "agent_hist_win_rate",
                "opportunity_id",
            ],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)


def apply_rep_overrides(
    scored_df: pd.DataFrame,
    overrides: Optional[Dict[str, Dict[str, str]]] = None,
) -> pd.DataFrame:
    """
    Applies active salesperson/manager overrides to operational queue placement
    WITHOUT altering the underlying statistical estimates (`p_win_90d`, `ev_90d`).
    """
    out = scored_df.copy()
    # H5 — Arthur revisou e ajustou o comportamento do override durante a
    # implementação no Codex. A intervenção muda a fila, não a estimativa estatística.
    # Atribuição e teste correspondente: PROCESS_LOG.md, mapa H1–H5.
    out["override_disposition"] = "none"
    out["override_reason"] = ""
    out["operational_rank_group"] = 1
    out["action_tier"] = out["statistical_tier"]

    if not overrides:
        return out

    disp_map = {}
    reason_map = {}
    for opp_id, payload in overrides.items():
        disp = str(payload.get("disposition", "none")).strip().lower()
        if disp in {"promote", "pause", "archive"}:
            disp_map[opp_id] = disp
            reason_map[opp_id] = str(payload.get("reason", ""))

    if not disp_map:
        return out

    mapped_disp = out["opportunity_id"].map(disp_map).fillna("none")
    out["override_disposition"] = mapped_disp
    out["override_reason"] = out["opportunity_id"].map(reason_map).fillna("")

    out["operational_rank_group"] = np.select(
        [
            mapped_disp == "promote",
            mapped_disp == "pause",
            mapped_disp == "archive",
        ],
        [0, 2, 3],
        default=1,
    )
    out["action_tier"] = np.select(
        [
            mapped_disp == "promote",
            mapped_disp == "pause",
            mapped_disp == "archive",
        ],
        [
            "⬆️ Priorizado Manualmente (Override)",
            "⏸️ Pausado em Campo (Override)",
            "🗑️ Desqualificado em Campo (Override)",
        ],
        default=out["statistical_tier"],
    )
    return out


def score_single_deal_simulation(
    scorer: EmpiricalHorizonScorer,
    sales_agent: str,
    product: str,
    has_account: bool,
    cycle_days: float,
    expected_won_value: float,
    opportunity_id: str = "SIM-001",
    account_name: Optional[str] = None,
) -> pd.Series:
    """
    Canonical single-deal scoring entry point shared between the Streamlit Sandbox
    and batch parity unit tests. Calls `scorer.score_engaging_deals` directly so
    there is zero duplicate math.
    """
    acc_val = (
        account_name if (has_account and account_name) else ("Conta Simulada" if has_account else np.nan)
    )
    acc_disp = str(acc_val) if has_account else "⚠️ Conta Não Vinculada (CRM Gap)"
    sim_df = pd.DataFrame(
        [
            {
                "opportunity_id": opportunity_id,
                "sales_agent": sales_agent,
                "product": product,
                "has_account": bool(has_account),
                "account": acc_val,
                "account_display": acc_disp,
                "crm_hygiene_status": (
                    "✅ Conta Vinculada"
                    if has_account
                    else "⚠️ Sem Conta (Enriquecer CRM)"
                ),
                "cycle_days": float(cycle_days),
                "expected_won_value": float(expected_won_value),
                "deal_stage": "Engaging",
            }
        ]
    )
    return scorer.score_engaging_deals(sim_df).iloc[0]


def compute_age_stage_distribution(
    df: pd.DataFrame, snapshot_date: pd.Timestamp
) -> pd.DataFrame:
    """
    Computes empirical stage proportions across observed duration thresholds.
    Explicitly descriptive proportions (not a Kaplan-Meier product-limit estimator).
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
                "deals_at_or_above_age": total,
                "won_count": won,
                "lost_count": lost,
                "still_engaging_open": still_open,
                "closed_only_win_rate": (
                    round(won / closed_total, 4) if closed_total > 0 else 0.0
                ),
                "unconditional_won_share": round(won / total, 4),
                "open_unclosed_share": round(still_open / total, 4),
            }
        )
    return pd.DataFrame(rows)


# Backwards-compatible alias for clean imports
SurvivalLeadScorer = EmpiricalHorizonScorer
