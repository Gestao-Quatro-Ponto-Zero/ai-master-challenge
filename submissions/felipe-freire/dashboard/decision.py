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


def experiment_copy(objective: str, language: str = "pt") -> dict[str, str]:
    """Translate a marketing objective into a primary metric and safety guardrail."""
    mapping_pt = {
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
    if objective not in mapping_pt:
        raise ValueError(f"unsupported objective: {objective}")
    translations = {
        "es": {
            "Alcance": ("alcance único incremental", "frecuencia y costo por persona alcanzada"),
            "Compartilhamento": (
                "tasa incremental de compartidos",
                "comentarios negativos y tasa de unfollow",
            ),
            "Conversa": (
                "comentarios cualificados incrementales",
                "sentimiento negativo y tiempo de moderación",
            ),
            "Conversão": ("margen incremental", "CAC, reembolsos y frecuencia"),
        },
        "en": {
            "Alcance": ("incremental unique reach", "frequency and cost per person reached"),
            "Compartilhamento": ("incremental share rate", "negative comments and unfollow rate"),
            "Conversa": (
                "incremental qualified comments",
                "negative sentiment and moderation time",
            ),
            "Conversão": ("incremental margin", "CAC, refunds, and frequency"),
        },
    }
    if language in translations:
        metric, guardrail = translations[language][objective]
        return {"metric": metric, "guardrail": guardrail}
    return mapping_pt[objective]
