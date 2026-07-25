from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class EfficiencyScenario:
    volume: int
    eligible_share: float
    adoption: float
    manual_minutes: float
    assisted_minutes: float
    safe_success_rate: float


@dataclass(frozen=True)
class EfficiencyResult:
    adopted_cases: float
    manual_hours: float
    assisted_hours: float
    rework_hours: float
    net_hours_released: float
    time_reduction_rate: float

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_efficiency(scenario: EfficiencyScenario) -> EfficiencyResult:
    if scenario.volume < 0:
        raise ValueError("Volume não pode ser negativo.")
    for name in ("eligible_share", "adoption", "safe_success_rate"):
        value = getattr(scenario, name)
        if not 0 <= value <= 1:
            raise ValueError(f"{name} deve estar entre 0 e 1.")
    if scenario.manual_minutes <= 0:
        raise ValueError("Tempo manual deve ser maior que zero.")
    if scenario.assisted_minutes < 0:
        raise ValueError("Tempo assistido não pode ser negativo.")

    adopted_cases = scenario.volume * scenario.eligible_share * scenario.adoption
    manual_hours = adopted_cases * scenario.manual_minutes / 60
    assisted_hours = adopted_cases * scenario.assisted_minutes / 60
    rework_hours = (
        adopted_cases
        * (1 - scenario.safe_success_rate)
        * scenario.manual_minutes
        / 60
    )
    total_assisted_hours = assisted_hours + rework_hours
    net_hours = manual_hours - total_assisted_hours
    reduction = net_hours / manual_hours if manual_hours else 0.0

    return EfficiencyResult(
        adopted_cases=adopted_cases,
        manual_hours=manual_hours,
        assisted_hours=assisted_hours,
        rework_hours=rework_hours,
        net_hours_released=net_hours,
        time_reduction_rate=reduction,
    )
