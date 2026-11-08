"""Traduz contribuições do LightGBM (log-odds) em motivos legíveis em pt-BR. Sempre "associação, não causa"."""
from __future__ import annotations

from typing import Callable

import numpy as np

DISCLAIMER = "Associações no histórico; não são causas."


def _pct(v: float) -> str:
    return f"{float(v) * 100:.0f}%"


# feature -> (código exibido, função que monta o texto a partir do valor)
CATALOG: dict[str, tuple[str, Callable]] = {
    "price": ("price", lambda v: "Ticket do produto: US$ " + f"{float(v):,.0f}".replace(",", ".")),
    "agent_wr": ("agent_wr", lambda v: f"Taxa de vitória do vendedor: {_pct(v)}"),
    "agent_n": ("agent_n", lambda v: f"Experiência do vendedor: {int(v)} deals fechados"),
    "product_wr": ("product_wr", lambda v: f"Taxa de vitória do produto: {_pct(v)}"),
    "agent_product_wr": ("agent_product_wr", lambda v: f"Histórico do vendedor com este produto: {_pct(v)}"),
    "agent_recent_wr": ("agent_recent_wr", lambda v: f"Desempenho recente do vendedor (90 dias): {_pct(v)}"),
    "agent_load": ("agent_load", lambda v: f"Deals abertos do vendedor: {int(v)}"),
    "age_days": ("age_band", lambda v: f"Tempo no funil: {int(v)} dias"),
    "product": ("product", lambda v: f"Produto: {v}"),
    "series": ("series", lambda v: f"Série do produto: {v}"),
    "sales_agent": ("sales_agent", lambda v: f"Perfil do vendedor: {v}"),
    "manager": ("manager", lambda v: f"Time do manager: {v}"),
    "regional_office": ("regional_office", lambda v: f"Escritório: {v}"),
}


def build_reasons(features: list[str], values: list, contribs: np.ndarray, min_abs: float = 1e-9) -> list[dict]:
    """Motivos ordenados por impacto (normalizado: soma 1). Contribuições nulas são ignoradas."""
    total = float(np.abs(contribs).sum())
    items = []
    for feat, val, c in zip(features, values, contribs):
        if abs(c) < min_abs or total == 0:
            continue
        code, fmt = CATALOG.get(feat, (feat, lambda v: f"{feat}: {v}"))
        items.append({
            "code": code,
            "label": fmt(val),
            "value": str(val),
            "direction": "positive" if c > 0 else "negative",
            "impact": round(abs(float(c)) / total, 4),
        })
    return sorted(items, key=lambda r: -r["impact"])
