from __future__ import annotations

from typing import Iterable

import pandas as pd

from .entities import AccountHealth, RiskSignal
from .specifications import Specification, risk_specifications


class HealthScoreService:
    def __init__(self, specs: Iterable[Specification] | None = None) -> None:
        self.specs = list(specs or risk_specifications())

    def evaluate(self, row: pd.Series) -> AccountHealth:
        ranked_signals: list[tuple[int, int, RiskSignal]] = []

        for idx, spec in enumerate(self.specs):
            if spec.is_satisfied_by(row):
                ranked_signals.append(
                    (
                        -spec.weight,
                        idx,
                        RiskSignal(
                        name=spec.name,
                        weight=spec.weight,
                        evidence=spec.evidence(row),
                        interpretation=spec.interpretation(row),
                        ),
                    )
                )

        ranked_signals.sort(key=lambda item: (item[0], item[1]))
        signals = [signal for _, _, signal in ranked_signals]

        base_score = sum(signal.weight for signal in signals)
        revenue_modifier = self._revenue_modifier(row)
        score = min(100, base_score + revenue_modifier)

        risk_level = self._risk_band(score)
        primary_driver = signals[0].name if signals else "healthy"
        secondary_driver = signals[1].name if len(signals) > 1 else "healthy"
        mrr_at_risk = float(row.get("current_mrr", 0) or 0) if risk_level in {"high", "critical"} else 0.0
        action = self._recommend_action(risk_level, primary_driver)

        return AccountHealth(
            account_id=str(row["account_id"]),
            health_score=score,
            risk_level=risk_level,
            mrr_at_risk=mrr_at_risk,
            primary_driver=primary_driver,
            secondary_driver=secondary_driver,
            recommended_action=action,
            signals=signals,
        )

    @staticmethod
    def _revenue_modifier(row: pd.Series) -> int:
        mrr = float(row.get("current_mrr", 0) or 0)
        if mrr >= 4000:
            return 10
        if mrr >= 2000:
            return 6
        if mrr >= 1000:
            return 3
        return 0

    @staticmethod
    def _risk_band(score: int) -> str:
        if score >= 75:
            return "critical"
        if score >= 55:
            return "high"
        if score >= 30:
            return "medium"
        return "low"

    @staticmethod
    def _recommend_action(risk_level: str, primary_driver: str) -> str:
        if risk_level == "critical":
            if primary_driver in {"recent_downgrade", "no_auto_renew"}:
                return "CS + Revenue: abordagem comercial imediata para revisar plano, renovacao e novo risco de downgrade."
            if primary_driver in {"poor_support_experience", "high_escalation_load"}:
                return "CS + Support: abrir plano de recuperacao com SLA executivo e revisar a jornada de suporte."
            return "CS: abrir playbook de retencao nas proximas 24h com contato humano e revisao de adocao."
        if risk_level == "high":
            return "CS: priorizar contato nesta semana e revisar adocao, erros e uso recente."
        if risk_level == "medium":
            return "Automacao de nurture e monitoramento quinzenal com foco em ativacao."
        return "Manter acompanhamento padrao e avaliar potencial de expansao."
