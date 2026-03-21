from __future__ import annotations

import os
from typing import Protocol

from src.api.contracts import (
    DashboardFilterOptionsResponse,
    DashboardKpisResponse,
    OpportunitiesListResponse,
    OpportunityDetailResponse,
)


class OpportunityRepositoryLike(Protocol):
    def list_opportunities(
        self,
        region: str | None = None,
        manager: str | None = None,
        deal_stage: str | None = None,
        q: str | None = None,
        sort_by: str = "score",
        sort_order: str = "desc",
        limit: int = 20,
        page: int | None = None,
        page_size: int | None = None,
    ) -> OpportunitiesListResponse: ...

    def get_opportunity(self, opportunity_id: str) -> OpportunityDetailResponse: ...
    def get_dashboard_kpis(self) -> DashboardKpisResponse: ...
    def get_dashboard_filter_options(self) -> DashboardFilterOptionsResponse: ...


def create_opportunity_repository(mode: str | None = None) -> OpportunityRepositoryLike:
    runtime_mode = (mode or os.environ.get("LEAD_SCORER_REPOSITORY_MODE", "api")).strip().lower()

    if runtime_mode == "api":
        from src.infrastructure.http.api_client import ApiClient, ApiClientConfig
        from src.infrastructure.repositories.api_opportunity_repository import (
            ApiOpportunityRepository,
        )

        client = ApiClient(ApiClientConfig.from_env())
        return ApiOpportunityRepository(client=client)
    if runtime_mode == "mock":
        from src.infrastructure.repositories.mock_opportunity_repository import (
            MockOpportunityRepository,
        )

        return MockOpportunityRepository()
    raise ValueError("Invalid LEAD_SCORER_REPOSITORY_MODE. Use 'mock' or 'api'.")
