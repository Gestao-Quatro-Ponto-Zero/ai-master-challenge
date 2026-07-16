"""
Lead scoring engine — heuristic scoring with explainability.

Features (weights calibrated from EDA):
  - deal_stage (30%): Won=100, Engaging=70, Prospecting=30, Lost=0
  - time_in_stage (15%): Engaging deals gain score over time (max 365d), then decay
  - seller_win_rate (15%): historical close rate of the assigned seller
  - sector_win_rate (15%): historical close rate for the account's sector
  - product_price (10%): normalized by product catalog range
  - account_revenue (15%): normalized by accounts dataset range

All features normalize to 0–100 sub-scores before weighting.
Score range: 0–100.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoreConfig:
    """Single source of truth for scoring weights and thresholds."""
    stage_weights: dict = None
    weight_deal_stage: float = 0.30
    weight_time_in_stage: float = 0.15
    weight_seller_win_rate: float = 0.15
    weight_sector_win_rate: float = 0.15
    weight_product_price: float = 0.10
    weight_account_revenue: float = 0.15
    max_days_for_upside: int = 365
    decay_after_days: int = 730
    min_deals_for_seller_wr: int = 5

    def __post_init__(self):
        if self.stage_weights is None:
            self.stage_weights = {
                "Won": 100,
                "Engaging": 70,
                "Prospecting": 30,
                "Lost": 0,
            }


class Scorer:
    """Lead scorer with explainable breakdown."""

    def __init__(self, config: Optional[ScoreConfig] = None):
        self.config = config or ScoreConfig()
        self._seller_win_rates: dict = {}
        self._sector_win_rates: dict = {}
        self._revenue_min: float = 0
        self._revenue_max: float = 1
        self._price_min: float = 0
        self._price_max: float = 1
        self._time_prob_buckets: dict = {}
        self._time_bin_edges = [0, 7, 14, 30, 60, 90, 120, 9999]
        self._time_bin_labels = ["0-7d", "8-14d", "15-30d", "31-60d", "61-90d", "91-120d", "120d+"]
        self._manager_avg_wr: float = 0.5
        self._fitted = False

    def fit(self, pipeline: pd.DataFrame, accounts: pd.DataFrame,
            products: pd.DataFrame, teams: pd.DataFrame) -> "Scorer":
        """Compute historical stats from closed deals for scoring."""
        merged = pipeline.merge(accounts, on="account", how="left")
        merged = merged.merge(products, on="product", how="left")
        merged = merged.merge(teams, on="sales_agent", how="left")

        # Normalization ranges
        self._revenue_min = accounts["revenue"].min()
        self._revenue_max = accounts["revenue"].max()
        self._price_min = products["sales_price"].min()
        self._price_max = products["sales_price"].max()

        # Seller win rates
        closed = merged[merged["deal_stage"].isin(["Won", "Lost"])].copy()
        if len(closed) > 0:
            seller_stats = closed.groupby("sales_agent")["deal_stage"].agg(
                total="count",
                won=lambda x: (x == "Won").sum(),
            )
            seller_stats["wr"] = seller_stats["won"] / seller_stats["total"].clip(lower=1)
            for agent, row in seller_stats.iterrows():
                if row["total"] >= self.config.min_deals_for_seller_wr:
                    self._seller_win_rates[agent] = row["wr"]

            # Manager average win rate as fallback for sellers with few deals
            merged_with_manager = closed.copy()
            mgr_wr = merged_with_manager.groupby("manager")["deal_stage"].apply(
                lambda x: (x == "Won").mean()
            )
            for agent in merged["sales_agent"].unique():
                if agent not in self._seller_win_rates:
                    row = teams[teams["sales_agent"] == agent]
                    if len(row) > 0:
                        mgr = row.iloc[0]["manager"]
                        self._seller_win_rates[agent] = float(mgr_wr.get(mgr, 0.5))

            # Sector win rates
            self._sector_win_rates = dict(
                closed.groupby("sector")["deal_stage"]
                .apply(lambda x: (x == "Won").mean())
                .round(4)
            )

        # Time-based win probability from historical deal durations
        closed_with_dates = pipeline[
            pipeline["deal_stage"].isin(["Won", "Lost"])
        ].copy()
        closed_with_dates["engage_date"] = pd.to_datetime(
            closed_with_dates["engage_date"], errors="coerce"
        )
        closed_with_dates["close_date"] = pd.to_datetime(
            closed_with_dates["close_date"], errors="coerce"
        )
        closed_with_dates["days"] = (
            closed_with_dates["close_date"] - closed_with_dates["engage_date"]
        ).dt.days.dropna()
        if len(closed_with_dates) > 0:
            closed_with_dates["bucket"] = pd.cut(
                closed_with_dates["days"],
                bins=self._time_bin_edges,
                labels=self._time_bin_labels,
                right=True,
            )
            bucket_wr = (
                closed_with_dates.groupby("bucket", observed=True)["deal_stage"]
                .apply(lambda x: (x == "Won").mean())
            )
            self._time_prob_buckets = bucket_wr.to_dict()
        self._fitted = True
        return self

    def _normalize(self, value: float, vmin: float, vmax: float) -> float:
        if vmax <= vmin:
            return 0.5
        return (value - vmin) / (vmax - vmin)

    def _score_stage(self, stage: str) -> float:
        return float(self.config.stage_weights.get(stage, 0))

    def _score_time_in_stage(self, days_in_stage: Optional[float]) -> float:
        """
        Engaging deals: time invested indicates momentum.
        Peaks around max_days_for_upside, then decays.
        """
        if days_in_stage is None or pd.isna(days_in_stage):
            return 50  # neutral for Prospecting (no dates)
        d = max(0, days_in_stage)
        if d <= self.config.max_days_for_upside:
            return (d / self.config.max_days_for_upside) * 100
        if d >= self.config.decay_after_days:
            return 0
        # Linear decay from peak to 0
        decay_span = self.config.decay_after_days - self.config.max_days_for_upside
        fraction = (d - self.config.max_days_for_upside) / decay_span
        return 100 * (1 - fraction)

    def _score_seller_win_rate(self, agent: str) -> float:
        wr = self._seller_win_rates.get(agent, 0.5)
        return wr * 100

    def _score_sector_win_rate(self, sector: Optional[str]) -> float:
        if pd.isna(sector) or sector is None:
            return 50
        wr = self._sector_win_rates.get(sector, 0.5)
        return wr * 100

    def _score_product_price(self, price: Optional[float]) -> float:
        if pd.isna(price) or price is None:
            return 50
        return self._normalize(price, self._price_min, self._price_max) * 100

    def _score_account_revenue(self, revenue: Optional[float]) -> float:
        if pd.isna(revenue) or revenue is None:
            return 50
        return self._normalize(revenue, self._revenue_min, self._revenue_max) * 100

    def predict_win_prob(self, days_in_stage: Optional[float]) -> float:
        """Return win probability (0.0–1.0) based on historical time buckets."""
        if days_in_stage is None or pd.isna(days_in_stage) or days_in_stage < 0:
            return self._time_prob_buckets.get(self._time_bin_labels[0], 0.5)
        for i in range(len(self._time_bin_edges) - 1):
            if self._time_bin_edges[i] <= days_in_stage <= self._time_bin_edges[i + 1]:
                return self._time_prob_buckets.get(self._time_bin_labels[i], 0.5)
        return 0.5

    def _data_available(self, sector, revenue, price) -> dict:
        """Check which account-dependent features have data."""
        return {
            "sector_win_rate": sector is not None and not (isinstance(sector, float) and pd.isna(sector)),
            "account_revenue": revenue is not None and not (isinstance(revenue, float) and pd.isna(revenue)),
            "product_price": price is not None and not (isinstance(price, float) and pd.isna(price)),
        }

    def score_one(self, stage: str, days_in_stage: Optional[float],
                  agent: str, sector: Optional[str],
                  price: Optional[float], revenue: Optional[float]) -> dict:
        """Score a single deal and return breakdown.

        Features without available data get weight = 0.
        Freed weight is redistributed proportionally to features that have data.
        """
        if stage == "Won":
            return {"score": 100, "breakdown": {"deal_stage": 100},
                    "weights": {"deal_stage": 1.0}, "total": 100}
        if stage == "Lost":
            return {"score": 0, "breakdown": {"deal_stage": 0},
                    "weights": {"deal_stage": 1.0}, "total": 0}

        sub_scores = {
            "deal_stage": self._score_stage(stage),
            "time_in_stage": self._score_time_in_stage(days_in_stage),
            "seller_win_rate": self._score_seller_win_rate(agent),
            "sector_win_rate": self._score_sector_win_rate(sector),
            "product_price": self._score_product_price(price),
            "account_revenue": self._score_account_revenue(revenue),
        }

        base_weights = {
            "deal_stage": self.config.weight_deal_stage,
            "time_in_stage": self.config.weight_time_in_stage,
            "seller_win_rate": self.config.weight_seller_win_rate,
            "sector_win_rate": self.config.weight_sector_win_rate,
            "product_price": self.config.weight_product_price,
            "account_revenue": self.config.weight_account_revenue,
        }

        # Always-available features (stage, time, seller) always count
        always_available = {"deal_stage", "time_in_stage", "seller_win_rate"}

        # Check data availability for account-dependent features
        data_ok = self._data_available(sector, revenue, price)

        # Build active weights: handle data-dependent features that also need process-aware logic
        # Time in stage for Prospecting: days=0, sub_score=0 -> weight stays because stage IS known
        # Sector/revenue/price without data -> weight = 0
        active_weights = {}
        freed_weight = 0.0
        for k, w in base_weights.items():
            if k in always_available:
                active_weights[k] = w
            elif data_ok.get(k, False):
                active_weights[k] = w
            else:
                active_weights[k] = 0.0
                freed_weight += w

        # Redistribute freed weight proportionally among active features
        if freed_weight > 0 and active_weights:
            active_total = sum(active_weights.values())
            if active_total > 0:
                for k in active_weights:
                    active_weights[k] += freed_weight * (active_weights[k] / active_total)

        score = sum(sub_scores[k] * active_weights[k] for k in active_weights)
        return {
            "score": round(score, 1),
            "breakdown": sub_scores,
            "weights": active_weights,
            "total": round(score, 1),
        }

    def score_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score all open deals in a merged dataframe. Returns copy with score columns."""
        result = df.copy()

        # Compute days_in_stage for open deals
        ref_date = pd.Timestamp("2017-07-01")  # reference for historical data
        engage = pd.to_datetime(result["engage_date"], errors="coerce")
        close = pd.to_datetime(result["close_date"], errors="coerce")
        result["days_in_stage"] = np.where(
            result["deal_stage"] == "Prospecting",
            0,
            (close.fillna(ref_date) - engage).dt.days.fillna(0).clip(lower=0)
        )

        scores = result.apply(
            lambda row: self.score_one(
                stage=row["deal_stage"],
                days_in_stage=row["days_in_stage"],
                agent=row["sales_agent"],
                sector=row.get("sector", None),
                price=row.get("sales_price", None),
                revenue=row.get("revenue", None),
            ),
            axis=1,
            result_type="expand",
        )
        result["score"] = scores["score"]
        result["score_breakdown"] = scores["breakdown"]
        result["score_weights"] = scores["weights"]

        # Win probability from time-in-stage
        result["win_prob"] = result["days_in_stage"].apply(self.predict_win_prob)

        return result
