"""Reprodução da ausência de sinal preditivo por atributo — Requirement
"Reprodução da ausência de sinal preditivo por atributo".

Separação temporal treino/teste sobre os negócios fechados; AUC isolada por
atributo firmográfico (usando a taxa de ganho do próprio atributo, calculada
só no treino, como a pontuação preditiva — o jeito mais direto de testar se
uma categoria isolada carrega sinal) e AUC do conjunto combinado (gradient
boosting sobre todos os atributos juntos).

NÃO usa `close_value`, `close_date` nem duração de ciclo como atributo —
são resultado, não entrada disponível no momento da pontuação.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ISOLATED_ATTRIBUTES = [
    ("sales_agent", "vendedor"),
    ("account", "conta"),
    ("sector", "setor"),
    ("regional_office", "escritório regional"),
]

FEATURE_COLUMNS = ["sales_agent", "product", "account", "sector", "regional_office"]


@dataclass(frozen=True)
class SplitDatasets:
    train: pd.DataFrame
    test: pd.DataFrame
    cutoff_date: pd.Timestamp


def chronological_split(closed: pd.DataFrame, test_fraction: float = 0.2) -> SplitDatasets:
    ordered = closed.sort_values("engage_date")
    cutoff_idx = int(len(ordered) * (1 - test_fraction))
    cutoff_date = ordered.iloc[cutoff_idx]["engage_date"]
    train = ordered[ordered["engage_date"] < cutoff_date]
    test = ordered[ordered["engage_date"] >= cutoff_date]
    return SplitDatasets(train=train, test=test, cutoff_date=cutoff_date)


def _isolated_attribute_auc(train: pd.DataFrame, test: pd.DataFrame, column: str) -> float | None:
    train_sub = train.dropna(subset=[column])
    test_sub = test.dropna(subset=[column])
    if train_sub.empty or test_sub.empty:
        return None

    global_rate = (train_sub["deal_stage"] == "Won").mean()
    rate_by_group = train_sub.groupby(column)["deal_stage"].apply(
        lambda s: (s == "Won").mean()
    )

    y_true = (test_sub["deal_stage"] == "Won").astype(int).to_numpy()
    y_score = test_sub[column].map(rate_by_group).fillna(global_rate).to_numpy()

    if len(np.unique(y_true)) < 2:
        return None
    return float(roc_auc_score(y_true, y_score))


def isolated_aucs(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, float | None]:
    """Task 6.1/6.2 — AUC isolada para vendedor, conta, setor, escritório."""
    return {
        label: _isolated_attribute_auc(train, test, column)
        for column, label in ISOLATED_ATTRIBUTES
    }


def combined_auc(train: pd.DataFrame, test: pd.DataFrame, seed: int = 20260819) -> float:
    """AUC do conjunto combinado — gradient boosting sobre todos os
    atributos firmográficos juntos (one-hot via categorias nativas do
    HistGradientBoostingClassifier, sem close_value/close_date/ciclo)."""
    train_sub = train.dropna(subset=FEATURE_COLUMNS)
    test_sub = test.dropna(subset=FEATURE_COLUMNS)

    x_train = train_sub[FEATURE_COLUMNS].astype("category")
    x_test = test_sub[FEATURE_COLUMNS].astype("category")
    y_train = (train_sub["deal_stage"] == "Won").astype(int)
    y_test = (test_sub["deal_stage"] == "Won").astype(int)

    model = HistGradientBoostingClassifier(
        categorical_features="from_dtype", random_state=seed
    )
    model.fit(x_train, y_train)
    y_score = model.predict_proba(x_test)[:, 1]
    return float(roc_auc_score(y_test, y_score))
