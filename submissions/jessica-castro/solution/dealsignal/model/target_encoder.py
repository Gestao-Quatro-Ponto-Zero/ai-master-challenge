"""
DealSignal — Target Encoder for categorical features.

Learns smoothed win rates per category (and per pair/triple of categories)
from training data, then applies the learned mappings to new data.

All encodings use Bayesian smoothing:
    smoothed_rate = (n * group_rate + m * global_rate) / (n + m)
"""

from __future__ import annotations

from typing import List, Tuple

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

SMOOTHING_PRIOR = 10


def _smoothed_rates(
    keys: pd.Series, y: pd.Series, global_rate: float, m: int
) -> dict:
    """Compute Bayesian-smoothed target rates per group."""
    tmp = pd.DataFrame({"key": keys.values, "y": y.values})
    agg = tmp.groupby("key")["y"].agg(["mean", "count"])
    agg["smoothed"] = (agg["count"] * agg["mean"] + m * global_rate) / (
        agg["count"] + m
    )
    return agg["smoothed"].to_dict()


class DealSignalTargetEncoder:
    """Fit/transform target encoder for categorical columns and their interactions.

    Parameters
    ----------
    single_cols : list of column names to target-encode individually.
    pair_cols   : list of (col1, col2) tuples to encode as pairs.
    triple_cols : list of (col1, col2, col3) tuples to encode as triples.
    m           : Bayesian smoothing strength (default 10).
    """

    def __init__(
        self,
        single_cols: List[str] | None = None,
        pair_cols: List[Tuple[str, str]] | None = None,
        triple_cols: List[Tuple[str, str, str]] | None = None,
        m: int = SMOOTHING_PRIOR,
    ):
        self.single_cols = single_cols or []
        self.pair_cols = pair_cols or []
        self.triple_cols = triple_cols or []
        self.m = m
        self.global_rate_: float = 0.5
        self.mappings_: dict[str, dict] = {}
        self.feature_names_: List[str] = []

    def fit(self, df: pd.DataFrame, y: pd.Series) -> "DealSignalTargetEncoder":
        """Learn target-encoded mappings from training data."""
        self.global_rate_ = float(y.mean())
        self.mappings_ = {}
        self.feature_names_ = []
        m = self.m

        df = df.copy()
        for col in self._all_raw_cols():
            if col in df.columns:
                df[col] = df[col].fillna("Unknown").astype(str)

        # Reset y index to align with df
        y_aligned = y.values

        # Singles
        for col in self.single_cols:
            if col not in df.columns:
                continue
            feat_name = f"te_{col}"
            self.mappings_[feat_name] = _smoothed_rates(
                df[col].reset_index(drop=True),
                pd.Series(y_aligned),
                self.global_rate_,
                m,
            )
            self.feature_names_.append(feat_name)

        # Pairs
        for c1, c2 in self.pair_cols:
            if c1 not in df.columns or c2 not in df.columns:
                continue
            feat_name = f"te_{c1}_{c2}"
            combo = (df[c1] + "|" + df[c2]).reset_index(drop=True)
            self.mappings_[feat_name] = _smoothed_rates(
                combo, pd.Series(y_aligned), self.global_rate_, m
            )
            self.feature_names_.append(feat_name)

        # Triples (use slightly higher smoothing for sparser groups)
        m_triple = max(m, 15)
        for c1, c2, c3 in self.triple_cols:
            if not all(c in df.columns for c in [c1, c2, c3]):
                continue
            feat_name = f"te_{c1}_{c2}_{c3}"
            combo = (df[c1] + "|" + df[c2] + "|" + df[c3]).reset_index(drop=True)
            self.mappings_[feat_name] = _smoothed_rates(
                combo, pd.Series(y_aligned), self.global_rate_, m_triple
            )
            self.feature_names_.append(feat_name)

        logger.info(
            "TargetEncoder fit: %d singles, %d pairs, %d triples → %d features",
            len(self.single_cols),
            len(self.pair_cols),
            len(self.triple_cols),
            len(self.feature_names_),
        )
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply learned mappings to produce target-encoded feature matrix."""
        df = df.copy()
        for col in self._all_raw_cols():
            if col in df.columns:
                df[col] = df[col].fillna("Unknown").astype(str)

        result = pd.DataFrame(index=df.index)

        for col in self.single_cols:
            feat_name = f"te_{col}"
            if feat_name in self.mappings_ and col in df.columns:
                result[feat_name] = df[col].map(self.mappings_[feat_name]).fillna(
                    self.global_rate_
                )
            else:
                result[feat_name] = self.global_rate_

        for c1, c2 in self.pair_cols:
            feat_name = f"te_{c1}_{c2}"
            if feat_name in self.mappings_ and c1 in df.columns and c2 in df.columns:
                combo = df[c1] + "|" + df[c2]
                result[feat_name] = combo.map(self.mappings_[feat_name]).fillna(
                    self.global_rate_
                )
            else:
                result[feat_name] = self.global_rate_

        for c1, c2, c3 in self.triple_cols:
            feat_name = f"te_{c1}_{c2}_{c3}"
            if (
                feat_name in self.mappings_
                and all(c in df.columns for c in [c1, c2, c3])
            ):
                combo = df[c1] + "|" + df[c2] + "|" + df[c3]
                result[feat_name] = combo.map(self.mappings_[feat_name]).fillna(
                    self.global_rate_
                )
            else:
                result[feat_name] = self.global_rate_

        return result

    def _all_raw_cols(self) -> set:
        cols = set(self.single_cols)
        for c1, c2 in self.pair_cols:
            cols.update([c1, c2])
        for c1, c2, c3 in self.triple_cols:
            cols.update([c1, c2, c3])
        return cols


# ── Default configuration used by the production pipeline ───────────────────

DEFAULT_SINGLE_COLS = [
    "product",
    "sales_agent",
    "city",
    "country",
    "lead_source",
    "lead_origin",
    "contact_role",
    "lead_quality",
    "lead_tag",
    "last_activity_type",
    "last_notable_activity",
    "office",
    "manager",
]

DEFAULT_PAIR_COLS = [
    ("sales_agent", "product"),
    ("lead_tag", "sales_agent"),
    ("lead_tag", "product"),
    ("lead_tag", "city"),
    ("lead_tag", "lead_source"),
    ("lead_tag", "manager"),
    ("lead_tag", "last_activity_type"),
    ("city", "manager"),
    ("product", "city"),
    ("lead_source", "manager"),
    ("product", "lead_source"),
]

DEFAULT_TRIPLE_COLS = [
    ("lead_tag", "sales_agent", "product"),
    ("lead_tag", "sales_agent", "city"),
    ("lead_tag", "sales_agent", "lead_source"),
    ("lead_tag", "product", "city"),
    ("lead_tag", "product", "lead_source"),
    ("lead_tag", "city", "lead_source"),
    ("lead_tag", "manager", "product"),
]
