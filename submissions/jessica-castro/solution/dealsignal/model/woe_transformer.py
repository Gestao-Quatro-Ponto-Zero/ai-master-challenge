from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from config.constants import WOE_CAP, WOE_MIN_BIN_SIZE
from utils.logger import get_logger

logger = get_logger(__name__)

EPSILON = 1e-6


class WoETransformer(BaseEstimator, TransformerMixin):
    def __init__(self, n_bins: int = 10, min_bin_size: float = WOE_MIN_BIN_SIZE, woe_cap: float = WOE_CAP):
        self.n_bins = n_bins
        self.min_bin_size = min_bin_size
        self.woe_cap = woe_cap

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "WoETransformer":
        self.feature_names_in_ = list(X.columns)
        self.bins_: Dict[str, pd.IntervalIndex] = {}
        self.woe_maps_: Dict[str, Dict] = {}
        self.iv_scores_: Dict[str, float] = {}

        total_events = max((y == 1).sum(), EPSILON)
        total_non_events = max((y == 0).sum(), EPSILON)

        for col in X.columns:
            series = X[col].copy()

            # Skip constant features
            if series.nunique() <= 1:
                self.woe_maps_[col] = {}
                self.iv_scores_[col] = 0.0
                logger.debug("Skipping constant feature: %s", col)
                continue

            try:
                binned, bins = pd.qcut(
                    series,
                    q=self.n_bins,
                    retbins=True,
                    duplicates="drop",
                )
            except Exception:
                try:
                    binned, bins = pd.cut(
                        series,
                        bins=min(series.nunique(), self.n_bins),
                        retbins=True,
                        include_lowest=True,
                    )
                except Exception as e:
                    logger.warning("Cannot bin feature %s: %s", col, e)
                    self.woe_maps_[col] = {}
                    self.iv_scores_[col] = 0.0
                    continue

            self.bins_[col] = bins
            temp = pd.DataFrame({"bin": binned, "target": y})
            stats = (
                temp.groupby("bin", observed=True)["target"]
                .agg(events=lambda x: (x == 1).sum(), non_events=lambda x: (x == 0).sum())
                .reset_index()
            )

            stats["event_rate"] = (stats["events"] + EPSILON) / total_events
            stats["non_event_rate"] = (stats["non_events"] + EPSILON) / total_non_events
            stats["woe"] = np.log(stats["event_rate"] / stats["non_event_rate"]).clip(-self.woe_cap, self.woe_cap)
            stats["iv_contrib"] = (stats["event_rate"] - stats["non_event_rate"]) * stats["woe"]

            self.woe_maps_[col] = dict(zip(stats["bin"], stats["woe"]))
            self.iv_scores_[col] = float(stats["iv_contrib"].sum())

        logger.info(
            "WoE fit complete. Top features by IV: %s",
            sorted(self.iv_scores_.items(), key=lambda x: -x[1])[:5],
        )
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        result = pd.DataFrame(index=X.index)
        for col in self.feature_names_in_:
            if col not in X.columns or not self.woe_maps_.get(col):
                result[col] = 0.0
                continue

            series = X[col].copy()
            bins = self.bins_.get(col)
            if bins is None:
                result[col] = 0.0
                continue

            # Track out-of-training-range values before clipping — they get WoE=0 (neutral)
            out_of_range = (series < bins[0]) | (series > bins[-1])

            # Clip to training range for binning
            series_clipped = series.clip(lower=bins[0], upper=bins[-1])

            # Assign bins
            binned = pd.cut(
                series_clipped,
                bins=bins,
                include_lowest=True,
                labels=False,
            )

            # Build numeric → interval mapping
            bin_intervals = list(self.woe_maps_[col].keys())
            woe_values = np.zeros(len(series))
            for i, interval in enumerate(bin_intervals):
                mask = binned == i
                woe_values[mask] = self.woe_maps_[col][interval]

            # Neutral WoE for out-of-range values (no extrapolation)
            woe_values[out_of_range] = 0.0

            result[col] = woe_values
        return result

    def get_feature_contributions(
        self,
        X_woe: pd.DataFrame,
        coefficients: np.ndarray,
    ) -> pd.DataFrame:
        contrib = X_woe.copy()
        for i, col in enumerate(X_woe.columns):
            contrib[col] = X_woe[col] * coefficients[i]
        return contrib
