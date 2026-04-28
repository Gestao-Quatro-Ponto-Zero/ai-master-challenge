from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

from .config import ChurnPredictionConfig


class QuantileClipper:
    def __init__(self, lower_q: float = 0.01, upper_q: float = 0.99):
        self.lower_q = lower_q
        self.upper_q = upper_q

    def fit(self, X, y=None):
        frame = pd.DataFrame(X)
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}
        for col in frame.columns:
            s = pd.to_numeric(frame[col], errors="coerce")
            self.lower_bounds_[col] = s.quantile(self.lower_q)
            self.upper_bounds_[col] = s.quantile(self.upper_q)
        return self

    def transform(self, X):
        frame = pd.DataFrame(X).copy()
        for col in frame.columns:
            s = pd.to_numeric(frame[col], errors="coerce")
            lo = self.lower_bounds_.get(col)
            hi = self.upper_bounds_.get(col)
            frame[col] = s.clip(lower=lo, upper=hi)
        return frame

    def get_feature_names_out(self, input_features=None):
        return input_features


def build_feature_matrix(dataset: pd.DataFrame):
    forbidden = {
        "snapshot_id",
        "account_id",
        "account_name",
        "signup_date",
        "first_churn_date",
        "first_future_churn_date",
        "snapshot_date",
        "churn_flag",
        "target_churn_30d",
        "is_logo_churned",
    }

    feature_cols = [c for c in dataset.columns if c not in forbidden]
    X = dataset[feature_cols].copy()
    y = dataset["target_churn_30d"].astype(int).copy()

    numeric_columns = X.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_columns = [c for c in X.columns if c not in numeric_columns]

    return X, y, numeric_columns, categorical_columns


def build_preprocessors(
    numeric_columns: list[str],
    categorical_columns: list[str],
    config: ChurnPredictionConfig,
):
    numeric_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "clipper",
                QuantileClipper(
                    lower_q=config.outlier_lower_quantile,
                    upper_q=config.outlier_upper_quantile,
                ),
            ),
            ("scaler", RobustScaler()),
        ]
    )

    categorical_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    linear_prep = ColumnTransformer(
        [
            ("num", numeric_pipe, numeric_columns),
            ("cat", categorical_pipe, categorical_columns),
        ]
    )

    tree_prep = ColumnTransformer(
        [
            (
                "num",
                Pipeline([("imputer", SimpleImputer(strategy="median"))]),
                numeric_columns,
            ),
            ("cat", categorical_pipe, categorical_columns),
        ]
    )

    return linear_prep, tree_prep
