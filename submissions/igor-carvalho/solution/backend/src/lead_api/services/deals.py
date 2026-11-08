"""Consulta de deals pontuados: escopo, filtros, ordenação e paginação (regra de negócio fora dos routers)."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from lead_core.constants import BANDS, PRIORITY_LEVELS, STAGES, VIEWS

from ..errors import deal_not_found
from ..presenters import detail_dict, summary_dict
from ..security import Principal
from ..store import LoadedModel

SORT_COLUMNS = {"score": "score", "expected_value": "expected_value", "age_days": "age_days"}


@dataclass
class DealFilters:
    seller: str | None = None
    manager: str | None = None
    office: str | None = None
    stage: str | None = None
    band: str | None = None
    product: str | None = None
    min_score: int | None = None
    max_score: int | None = None
    priority: str | None = None     # high | medium | low (faixas em constants.PRIORITY_LEVELS)
    view: str | None = None         # aba: focus | decide | follow | prospecting | review | all | ev
    q: str | None = None
    page: int = 1
    page_size: int = 50
    sort: str | None = None         # padrão: o da visão (ev -> expected_value) ou score
    order: str = "desc"


def scoped(model: LoadedModel, user: Principal) -> pd.DataFrame:
    df = model.deals
    return df if user.sellers is None else df[df["seller"].isin(user.sellers)]


def probability_allowed(flag: bool, model: LoadedModel) -> bool:
    """A chance em % aparece quando G4_SHOW_PROBABILITY está ligada. A calibração (model card) não a esconde:
    o front avisa quando ela ainda não é calibrada (meta.calibration_useful)."""
    return bool(flag)


class DealQueryService:
    def __init__(self, show_probability: bool):
        self.show_probability = show_probability

    def list(self, model: LoadedModel, user: Principal, f: DealFilters) -> dict:
        df = self._filter(scoped(model, user), f)
        col = SORT_COLUMNS[f.sort or (VIEWS[f.view]['sort'] if f.view else 'score')]
        df = df.sort_values([col, "expected_value"], ascending=[f.order == "asc", False], na_position="last",
                            kind="stable")
        start = (f.page - 1) * f.page_size
        page = df.iloc[start:start + f.page_size]
        return {"items": [summary_dict(r, probability_allowed(self.show_probability, model)) for _, r in page.iterrows()],
                "page": f.page, "page_size": f.page_size, "total": int(len(df))}

    @staticmethod
    def _filter(df: pd.DataFrame, f: DealFilters) -> pd.DataFrame:
        if f.view is not None:
            df = df[df["band"].isin(VIEWS[f.view]["bands"])]
        elif f.band is None:                        # padrão: sem zumbis e sem prospecting (viram abas)
            df = df[~df["band"].isin(["review", "prospecting"])]
        if f.band is not None:
            df = df[df["band"] == f.band]
        for column, value in (("seller", f.seller), ("manager", f.manager), ("office", f.office),
                              ("stage", f.stage), ("product", f.product)):
            if value is not None:
                df = df[df[column] == value]
        low, high = f.min_score, f.max_score
        if f.priority is not None:
            _, _, p_min, p_max = next(level for level in PRIORITY_LEVELS if level[0] == f.priority)
            low, high = max(low or 0, p_min), min(high if high is not None else 100, p_max)
        if low is not None:
            df = df[df["score"].notna() & (df["score"] >= low)]
        if high is not None:
            df = df[df["score"].notna() & (df["score"] <= high)]
        if f.q:
            needle = f.q.strip().lower()
            hit = (df["opportunity_id"].str.lower().str.contains(needle, regex=False)
                   | df["account"].fillna("").str.lower().str.contains(needle, regex=False))
            df = df[hit]
        return df

    def get(self, model: LoadedModel, user: Principal, opportunity_id: str) -> dict:
        df = scoped(model, user)
        if opportunity_id not in df.index:
            raise deal_not_found()
        return detail_dict(df.loc[opportunity_id], model.bundle, probability_allowed(self.show_probability, model))

    @staticmethod
    def filters(model: LoadedModel, user: Principal) -> dict:
        df = scoped(model, user)
        return {
            "sellers": sorted(df["seller"].unique()), "managers": sorted(df["manager"].unique()),
            "offices": sorted(df["office"].unique()), "products": sorted(df["product"].unique()),
            "stages": list(STAGES), "bands": list(BANDS),
        }
