from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class RiskSignal:
    name: str
    weight: int
    evidence: float | int | str
    interpretation: str


@dataclass(frozen=True)
class AccountHealth:
    account_id: str
    health_score: int
    risk_level: str
    mrr_at_risk: float
    primary_driver: str
    secondary_driver: str
    recommended_action: str
    signals: List[RiskSignal]

    def as_record(self) -> Dict[str, object]:
        return {
            "account_id": self.account_id,
            "health_score": self.health_score,
            "risk_level": self.risk_level,
            "mrr_at_risk": round(self.mrr_at_risk, 2),
            "primary_driver": self.primary_driver,
            "secondary_driver": self.secondary_driver,
            "recommended_action": self.recommended_action,
        }
