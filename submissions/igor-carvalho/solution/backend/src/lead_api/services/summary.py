"""KPIs agregados dentro do escopo do usuário. Valor esperado NÃO conta deals a revisar (zumbis)."""
from __future__ import annotations

import pandas as pd

from lead_core.constants import VIEWS

from ..errors import ApiError
from ..security import Principal
from ..store import LoadedModel
from .deals import scoped

GROUP_COLUMNS = {"seller": "seller", "manager": "manager", "office": "office"}


def _kpis(df: pd.DataFrame) -> dict:
    live = df[df["band"] != "review"]
    counts = df["band"].value_counts()
    return {
        "open_deals": int(len(df)), "expected_value": round(float(live["expected_value"].sum()), 2),
        "focus": int(counts.get("focus", 0)), "stale_risk": int(counts.get("stale_risk", 0)),
        "review": int(counts.get("review", 0)), "prospecting": int(counts.get("prospecting", 0)),
    }


def _views(df: pd.DataFrame) -> dict:
    """Contagem e valor esperado por visão (aba). Zumbis não contam valor esperado."""
    out = {}
    for key, view in VIEWS.items():
        part = df[df["band"].isin(view["bands"])]
        live = part[part["band"] != "review"]
        out[key] = {"count": int(len(part)), "expected_value": round(float(live["expected_value"].sum()), 2)}
    return out


def _funnel(df: pd.DataFrame, thresholds: dict) -> dict:
    """Heatmap do funil: produto x tempo no funil. Faixas de dias vêm dos limiares do modelo.

    Prospecting não entra (não tem data). Valor esperado não conta deals a revisar, como nos KPIs."""
    p50, stale, review = (int(thresholds[k]) for k in ("typical_p50", "stale_days", "review_days"))
    edges = [(0, p50), (p50 + 1, stale), (stale + 1, review), (review + 1, None)]
    labels = [f"até {p50} d", f"{p50 + 1}–{stale} d", f"{stale + 1}–{review} d", f"mais de {review} d"]
    columns = [{"key": f"d{i}", "label": label, "min_days": lo, "max_days": hi}
               for i, (label, (lo, hi)) in enumerate(zip(labels, edges))]
    aged = df[df["age_days"].notna() & (df["band"] != "prospecting")]
    rows = []
    for product, part in aged.groupby("product"):
        cells = []
        for lo, hi in edges:
            cell = part[(part["age_days"] >= lo) & (part["age_days"] <= hi if hi is not None else True)]
            live = cell[cell["band"] != "review"]
            cells.append({"count": int(len(cell)), "expected_value": round(float(live["expected_value"].sum()), 2)})
        rows.append({"product": product, "count": sum(c["count"] for c in cells),
                     "expected_value": round(sum(c["expected_value"] for c in cells), 2), "cells": cells})
    rows.sort(key=lambda r: (-r["expected_value"], r["product"]))
    return {"columns": columns, "rows": rows}


class SummaryService:
    def summarize(self, model: LoadedModel, user: Principal, group_by: str) -> dict:
        if group_by not in GROUP_COLUMNS:
            raise ApiError(422, "VALIDATION_ERROR", "group_by inválido.", [{"field": "group_by", "allowed": list(GROUP_COLUMNS)}])
        df = scoped(model, user)
        groups = []
        for key, part in df.groupby(GROUP_COLUMNS[group_by]):
            k = _kpis(part)
            groups.append({"key": key, "open_deals": k["open_deals"], "expected_value": k["expected_value"],
                           "review_share": round(k["review"] / k["open_deals"], 4) if k["open_deals"] else 0.0,
                           "focus": k["focus"]})
        groups.sort(key=lambda g: -g["expected_value"])
        return {"reference_date": model.bundle.card["reference_date"], "totals": _kpis(df), "views": _views(df),
                "funnel": _funnel(df, model.bundle.card["thresholds"]), "groups": groups}
