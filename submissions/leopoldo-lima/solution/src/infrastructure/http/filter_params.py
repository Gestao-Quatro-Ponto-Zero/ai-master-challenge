from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass


@dataclass(frozen=True)
class OpportunityListFilters:
    region: str | None = None
    manager: str | None = None
    deal_stage: str | None = None
    q: str | None = None
    sort_by: str = "score"
    sort_order: str = "desc"
    limit: int = 20
    page: int | None = None
    page_size: int | None = None


def filters_to_query_params(filters: OpportunityListFilters) -> OrderedDict[str, str | int]:
    params: OrderedDict[str, str | int] = OrderedDict()
    if filters.region:
        params["region"] = filters.region
    if filters.manager:
        params["manager"] = filters.manager
    if filters.deal_stage:
        params["deal_stage"] = filters.deal_stage
    if filters.q:
        params["q"] = filters.q.strip()
    params["sort_by"] = filters.sort_by
    params["sort_order"] = filters.sort_order
    params["limit"] = filters.limit
    if filters.page is not None:
        params["page"] = filters.page
    if filters.page_size is not None:
        params["page_size"] = filters.page_size
    return params
