"""Canonical metric implementations from the metric registry."""

from __future__ import annotations


def engagement_total(likes: int, shares: int, comments: int) -> int:
    """Return unweighted observable interactions."""
    values = (likes, shares, comments)
    if any(value < 0 for value in values):
        raise ValueError("interaction counts must be non-negative")
    return sum(values)


def safe_rate(numerator: float, denominator: float) -> float:
    """Return a rate while failing closed on a non-positive denominator."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return numerator / denominator
