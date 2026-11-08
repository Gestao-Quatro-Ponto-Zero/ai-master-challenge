"""Features point-in-time. A MESMA função serve ao treino, à pontuação em lote e ao /score/what-if.

Regra de ouro: para uma data T, só entram deals fechados até T. Nenhuma feature usa close_date ou
duração do próprio deal (seria vazamento).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import RECENT_DAYS, SHRINK_K

DEFAULT_BASE_RATE = 0.6


def open_snapshot(df: pd.DataFrame, T: pd.Timestamp) -> pd.DataFrame:
    """Deals engajados em T e ainda não fechados (Engaging). Prospecting não tem engage_date."""
    m = df["engage_date"].notna() & (df["engage_date"] <= T) & (df["close_date"].isna() | (df["close_date"] > T))
    snap = df.loc[m].copy()
    snap["snapshot"] = T
    snap["age_days"] = (T - snap["engage_date"]).dt.days
    return snap


def _wins_n(df: pd.DataFrame, key: str) -> dict[str, list[float]]:
    g = df.groupby(key)["won"].agg(["sum", "count"])
    return {str(k): [float(r["sum"]), float(r["count"])] for k, r in g.iterrows()}


def build_history_tables(df: pd.DataFrame, T: pd.Timestamp, snap: pd.DataFrame | None = None) -> dict:
    """Tabelas de taxas históricas (só deals fechados até T) + dicionários de apoio para o what-if."""
    hist = df[df["won"].notna() & (df["close_date"] <= T)]
    base = float(hist["won"].mean()) if len(hist) else DEFAULT_BASE_RATE
    recent = hist[hist["close_date"] > T - pd.Timedelta(days=RECENT_DAYS)]

    pair = hist.assign(_k=hist["sales_agent"] + "||" + hist["product"])
    load = snap.groupby("sales_agent").size().to_dict() if snap is not None else {}

    agents = df.drop_duplicates("sales_agent")[["sales_agent", "manager", "regional_office"]]
    products = df.drop_duplicates("product")[["product", "series", "price"]]
    return {
        "as_of": T.date().isoformat(),
        "shrink_k": SHRINK_K,
        "base_wr": base,
        "product": _wins_n(hist, "product"),
        "agent": _wins_n(hist, "sales_agent"),
        "agent_product": _wins_n(pair, "_k"),
        "recent": _wins_n(recent, "sales_agent"),
        "load": {str(k): int(v) for k, v in load.items()},
        "agents": {r.sales_agent: {"manager": r.manager, "regional_office": r.regional_office}
                   for r in agents.itertuples()},
        "products": {r.product: {"series": r.series, "price": float(r.price)} for r in products.itertuples()},
    }


def _lookup(table: dict, keys) -> tuple[np.ndarray, np.ndarray]:
    arr = np.array([table.get(k, (0.0, 0.0)) for k in keys], dtype=float).reshape(-1, 2)
    return arr[:, 0], arr[:, 1]


def _shrink(wins, n, prior, k):
    return (wins + k * prior) / (n + k)


def apply_tables(snap: pd.DataFrame, tables: dict) -> pd.DataFrame:
    """Acrescenta as features históricas a um conjunto de deals (colunas: sales_agent, product)."""
    k, base = tables["shrink_k"], tables["base_wr"]
    out = snap.copy()
    agents, products = out["sales_agent"].astype(str), out["product"].astype(str)

    pw, pn = _lookup(tables["product"], products)
    aw, an = _lookup(tables["agent"], agents)
    apw, apn = _lookup(tables["agent_product"], agents + "||" + products)
    rw, rn = _lookup(tables["recent"], agents)

    agent_wr = _shrink(aw, an, base, k)
    out["base_wr"] = base
    out["product_wr"] = _shrink(pw, pn, base, k)
    out["agent_wr"] = agent_wr
    out["agent_n"] = an
    out["agent_product_wr"] = _shrink(apw, apn, agent_wr, k)
    out["agent_recent_wr"] = _shrink(rw, rn, agent_wr, k)
    out["agent_load"] = [tables["load"].get(a, 0) for a in agents]
    return out


def add_history_features(snap: pd.DataFrame, df: pd.DataFrame, T: pd.Timestamp) -> pd.DataFrame:
    return apply_tables(snap, build_history_tables(df, T, snap))


def what_if_row(tables: dict, product: str, seller: str, age_days: int) -> pd.DataFrame:
    """Uma linha de features para um deal hipotético, usando as tabelas do modelo ativo."""
    prod, agent = tables["products"][product], tables["agents"][seller]
    row = pd.DataFrame([{
        "sales_agent": seller, "product": product, "series": prod["series"], "price": prod["price"],
        "manager": agent["manager"], "regional_office": agent["regional_office"], "age_days": int(age_days),
    }])
    return apply_tables(row, tables)
