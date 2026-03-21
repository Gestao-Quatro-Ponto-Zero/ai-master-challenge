from __future__ import annotations

from dataclasses import dataclass

from src.api.contracts import (
    DashboardFilterOptionsResponse,
    DashboardKpisResponse,
    OpportunitiesListResponse,
    OpportunityDetailResponse,
)
from src.infrastructure.http.api_client import ApiClient
from src.infrastructure.http.errors import ApiClientError


class OpportunityRepositoryError(Exception):
    """Base repository error."""


class OpportunityNotFoundError(OpportunityRepositoryError):
    """Raised when opportunity ID is not found."""


@dataclass
class ApiOpportunityRepository:
    client: ApiClient

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
    ) -> OpportunitiesListResponse:
        try:
            return self.client.list_opportunities(
                region=region,
                manager=manager,
                deal_stage=deal_stage,
                q=q,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                page=page,
                page_size=page_size,
            )
        except ApiClientError as exc:
            raise OpportunityRepositoryError("Failed to list opportunities.") from exc

    def get_opportunity(self, opportunity_id: str) -> OpportunityDetailResponse:
        try:
            return self.client.get_opportunity(opportunity_id)
        except ApiClientError as exc:
            if getattr(exc, "status_code", None) == 404:
                raise OpportunityNotFoundError(
                    f"Opportunity '{opportunity_id}' not found."
                ) from exc
            raise OpportunityRepositoryError("Failed to fetch opportunity detail.") from exc

    def get_dashboard_kpis(self) -> DashboardKpisResponse:
        try:
            return self.client.get_dashboard_kpis()
        except ApiClientError as exc:
            raise OpportunityRepositoryError("Failed to fetch dashboard KPIs.") from exc

    def get_dashboard_filter_options(self) -> DashboardFilterOptionsResponse:
        try:
            return self.client.get_dashboard_filter_options()
        except ApiClientError as exc:
            raise OpportunityRepositoryError("Failed to fetch dashboard filters.") from exc
