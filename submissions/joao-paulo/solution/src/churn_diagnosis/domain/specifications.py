from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd


class SpecificationEvaluationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Specification:
    name: str
    weight: int
    message: str
    predicate: Callable[[pd.Series], bool]
    evidence_field: str

    def is_satisfied_by(self, row: pd.Series) -> bool:
        try:
            return bool(self.predicate(row))
        except Exception as exc:
            raise SpecificationEvaluationError(
                f"Failed to evaluate specification '{self.name}'"
            ) from exc

    def evidence(self, row: pd.Series):
        return row.get(self.evidence_field)

    def interpretation(self, row: pd.Series) -> str:
        return self.message


def risk_specifications() -> list[Specification]:
    return [
        Specification(
            name="recent_usage_drop",
            weight=22,
            message="Queda relevante de uso nos ultimos 30 dias.",
            predicate=lambda r: (r.get("usage_drop_ratio", 0) or 0) >= 0.35,
            evidence_field="usage_drop_ratio",
        ),
        Specification(
            name="usage_stale",
            weight=18,
            message="Conta com recencia de uso ruim.",
            predicate=lambda r: (r.get("days_since_last_usage", 9999) or 9999) >= 30,
            evidence_field="days_since_last_usage",
        ),
        Specification(
            name="high_error_rate",
            weight=15,
            message="Taxa de erro elevada no uso recente.",
            predicate=lambda r: (r.get("error_rate_30d", 0) or 0) >= 0.08,
            evidence_field="error_rate_30d",
        ),
        Specification(
            name="low_feature_adoption",
            weight=12,
            message="Baixa adocao funcional do produto.",
            predicate=lambda r: (r.get("distinct_features", 0) or 0) <= 8,
            evidence_field="distinct_features",
        ),
        Specification(
            name="poor_support_experience",
            weight=18,
            message="Experiencia de suporte abaixo do ideal.",
            predicate=lambda r: (
                (r.get("avg_first_response_min", 0) or 0) >= 180
                or (r.get("avg_resolution_hours", 0) or 0) >= 48
                or ((r.get("avg_satisfaction", 5) or 5) <= 2.5)
            ),
            evidence_field="avg_first_response_min",
        ),
        Specification(
            name="high_escalation_load",
            weight=10,
            message="Volume elevado de escalacoes.",
            predicate=lambda r: (r.get("escalation_rate", 0) or 0) >= 0.30,
            evidence_field="escalation_rate",
        ),
        Specification(
            name="recent_downgrade",
            weight=20,
            message="Historico comercial recente indica downgrade.",
            predicate=lambda r: (r.get("downgrade_count", 0) or 0) >= 1,
            evidence_field="downgrade_count",
        ),
        Specification(
            name="no_auto_renew",
            weight=8,
            message="Conta sem auto renew habilitado.",
            predicate=lambda r: not bool(r.get("auto_renew_flag", False)),
            evidence_field="auto_renew_flag",
        ),
        Specification(
            name="trial_fragility",
            weight=8,
            message="Conta em trial ou com fragilidade de conversao.",
            predicate=lambda r: bool(r.get("is_current_trial", False)) or bool(r.get("is_trial", False)),
            evidence_field="is_current_trial",
        ),
        Specification(
            name="reactivation_risk",
            weight=10,
            message="Conta com historico de reativacao e risco estrutural de recorrencia.",
            predicate=lambda r: (r.get("reactivation_events", 0) or 0) >= 1,
            evidence_field="reactivation_events",
        ),
    ]


def opportunity_specifications() -> list[Specification]:
    return [
        Specification(
            name="healthy_expansion_candidate",
            weight=0,
            message="Conta saudavel, com bom engajamento e receita relevante.",
            predicate=lambda r: (
                (r.get("usage_drop_ratio", 0) or 0) < 0.05
                and (r.get("days_since_last_usage", 9999) or 9999) <= 10
                and (r.get("avg_satisfaction", 0) or 0) >= 4
                and (r.get("current_mrr", 0) or 0) >= 1500
            ),
            evidence_field="current_mrr",
        )
    ]
