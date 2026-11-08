"""Score de um deal hipotético: aplica o modelo JÁ treinado. Não treina nada."""
from __future__ import annotations

from lead_core.bands import priority_level
from lead_core.features import what_if_row

from ..errors import ApiError
from ..presenters import _none
from ..store import LoadedModel
from .deals import probability_allowed


class WhatIfService:
    def __init__(self, show_probability: bool):
        self.show_probability = show_probability

    def score(self, model: LoadedModel, product: str, seller: str, age_days: int) -> dict:
        tables = model.bundle.tables
        problems = []
        if product not in tables["products"]:
            problems.append({"field": "product", "message": f"Produto desconhecido: {product}"})
        if seller not in tables["agents"]:
            problems.append({"field": "seller", "message": f"Vendedor desconhecido: {seller}"})
        if problems:
            raise ApiError(422, "VALIDATION_ERROR", "Dados de entrada inválidos.", problems)

        feats = what_if_row(tables, product, seller, age_days)
        out = model.bundle.score(feats).iloc[0]
        score = _none(out["score"])
        return {
            "score": None if score is None else int(score),
            "band": out["band"], "priority_level": priority_level(None if score is None else int(score)),
            "expected_value": round(float(out["expected_value"]), 2),
            "p_win": round(float(out["p_win"]), 4) if probability_allowed(self.show_probability, model) else None,
            "reasons": out["reasons"][:3], "model_version": model.bundle.version,
        }
