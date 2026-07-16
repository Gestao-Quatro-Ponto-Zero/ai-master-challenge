"""SPEC-6: Modelagem Preditiva — XGBoost com SHAP explainability."""

from .train import train_model
from .predict import predict_churn
from .explain import explain_model

__all__ = ["train_model", "predict_churn", "explain_model"]
