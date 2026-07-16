"""Business-facing decision helpers for experiment planning."""

from __future__ import annotations

import math


def break_even(
    campaign_cost: float, margin_per_conversion: float, eligible_people: int
) -> dict[str, float | int]:
    """Calculate the minimum incremental result required to recover campaign cost."""
    if campaign_cost < 0 or margin_per_conversion <= 0 or eligible_people <= 0:
        raise ValueError("cost must be non-negative; margin and audience must be positive")
    conversions = math.ceil(campaign_cost / margin_per_conversion)
    rate = conversions / eligible_people
    return {
        "incremental_conversions": conversions,
        "incremental_rate": rate,
        "required_margin": conversions * margin_per_conversion,
    }


def experiment_copy(objective: str) -> dict[str, str]:
    """Translate a marketing objective into a primary metric and safety guardrail."""
    mapping = {
        "Alcance": {
            "metric": "alcance único incremental",
            "guardrail": "frequência e custo por pessoa alcançada",
        },
        "Compartilhamento": {
            "metric": "share rate incremental",
            "guardrail": "comentários negativos e unfollow rate",
        },
        "Conversa": {
            "metric": "comentários qualificados incrementais",
            "guardrail": "sentimento negativo e tempo de moderação",
        },
        "Conversão": {
            "metric": "margem incremental",
            "guardrail": "CAC, reembolso e frequência",
        },
    }
    if objective not in mapping:
        raise ValueError(f"unsupported objective: {objective}")
    return mapping[objective]
