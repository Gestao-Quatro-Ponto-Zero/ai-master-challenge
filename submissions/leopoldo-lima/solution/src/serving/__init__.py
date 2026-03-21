"""Camada de serving: oportunidades canónicas a partir dos CSVs oficiais (CRP-REAL-02)."""

from src.serving.models import ServingOpportunity
from src.serving.opportunity_pipeline import (
    build_serving_opportunities,
    clear_serving_cache,
)

__all__ = ["ServingOpportunity", "build_serving_opportunities", "clear_serving_cache"]
