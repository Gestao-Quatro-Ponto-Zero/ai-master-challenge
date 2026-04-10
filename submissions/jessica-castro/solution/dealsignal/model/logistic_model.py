import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import cross_val_score

from utils.logger import get_logger

logger = get_logger(__name__)


class DealScoringModel:
    def __init__(self, Cs=None, cv: int = 5):
        self.Cs = Cs or [0.01, 0.1, 1.0, 10.0]
        self.cv = cv
        self._base_model: LogisticRegressionCV = None
        self._model: CalibratedClassifierCV = None

    def fit(self, X_woe: pd.DataFrame, y: pd.Series) -> "DealScoringModel":
        self._base_model = LogisticRegressionCV(
            Cs=self.Cs,
            cv=self.cv,
            scoring="roc_auc",
            class_weight="balanced",
            solver="lbfgs",
            max_iter=1000,
            random_state=42,
            n_jobs=-1,
        )
        self._base_model.fit(X_woe, y)
        best_C = self._base_model.C_[0]
        logger.info("Best regularization C: %.4f", best_C)

        # Cross-validated AUC before calibration
        cv_auc = cross_val_score(
            self._base_model, X_woe, y, cv=self.cv, scoring="roc_auc", n_jobs=-1
        ).mean()
        logger.info("Cross-validated AUC-ROC: %.4f", cv_auc)
        self.cv_auc_ = cv_auc

        # Calibrate with sigmoid (Platt) + proper CV to avoid overfitting
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import FunctionTransformer
        base_lr = LogisticRegression(
            C=best_C,
            class_weight="balanced",
            solver="lbfgs",
            max_iter=1000,
            random_state=42,
        )
        self._model = CalibratedClassifierCV(
            base_lr, method="sigmoid", cv=self.cv
        )
        self._model.fit(X_woe, y)
        logger.info("Model calibration complete")
        return self

    def predict_proba(self, X_woe: pd.DataFrame) -> np.ndarray:
        return self._model.predict_proba(X_woe)[:, 1]

    def evaluate(self, X_woe: pd.DataFrame, y: pd.Series) -> dict:
        proba = self.predict_proba(X_woe)
        preds = (proba >= 0.5).astype(int)
        return {
            "auc": roc_auc_score(y, proba),
            "accuracy": accuracy_score(y, preds),
            "precision": precision_score(y, preds, zero_division=0),
            "recall": recall_score(y, preds, zero_division=0),
            "f1": f1_score(y, preds, zero_division=0),
        }

    @property
    def coefficients(self) -> np.ndarray:
        return self._base_model.coef_[0]

    @property
    def feature_names(self):
        return self._base_model.feature_names_in_
