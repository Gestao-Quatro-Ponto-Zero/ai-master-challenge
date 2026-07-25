from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CapacityScenario:
    total_tickets: int
    eligible_share: float
    adoption: float
    minutes_saved_per_eligible_ticket: float
    safe_success_rate: float
    review_minutes_per_routed_ticket: float
    rework_minutes_per_adopted_ticket: float = 0.0
    loaded_cost_per_hour: float = 0.0
    solution_cost_for_period: float = 0.0


@dataclass(frozen=True)
class CapacityResult:
    eligible_tickets: float
    adopted_tickets: float
    gross_hours_released: float
    review_hours_added: float
    rework_hours_added: float
    net_hours_released: float
    gross_value: float | None
    net_value: float | None

    def to_dict(self) -> dict:
        return asdict(self)


REFERENCE_SCENARIOS = (
    (
        "Conservador",
        CapacityScenario(30_000, 0.10, 0.30, 3, 0.85, 1.5, 0.5),
    ),
    (
        "Base",
        CapacityScenario(30_000, 0.25, 0.50, 5, 0.90, 1.0, 0.5),
    ),
    (
        "Expansão",
        CapacityScenario(30_000, 0.40, 0.70, 7, 0.95, 0.5, 0.25),
    ),
)


def calculate_capacity(scenario: CapacityScenario) -> CapacityResult:
    eligible = scenario.total_tickets * scenario.eligible_share
    adopted = eligible * scenario.adoption
    gross_hours = (
        adopted
        * scenario.minutes_saved_per_eligible_ticket
        * scenario.safe_success_rate
        / 60
    )
    review_hours = adopted * scenario.review_minutes_per_routed_ticket / 60
    rework_hours = adopted * scenario.rework_minutes_per_adopted_ticket / 60
    net_hours = gross_hours - review_hours - rework_hours

    if scenario.loaded_cost_per_hour > 0:
        gross_value = net_hours * scenario.loaded_cost_per_hour
        net_value = gross_value - scenario.solution_cost_for_period
    else:
        gross_value = None
        net_value = None

    return CapacityResult(
        eligible_tickets=eligible,
        adopted_tickets=adopted,
        gross_hours_released=gross_hours,
        review_hours_added=review_hours,
        rework_hours_added=rework_hours,
        net_hours_released=net_hours,
        gross_value=gross_value,
        net_value=net_value,
    )
