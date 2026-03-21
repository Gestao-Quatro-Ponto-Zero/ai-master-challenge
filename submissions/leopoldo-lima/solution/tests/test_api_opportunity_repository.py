from __future__ import annotations

import pytest

from src.api.contracts import (
    DashboardFilterOptionsResponse,
    DashboardKpisResponse,
    OpportunitiesListResponse,
    OpportunityDetailResponse,
    ScoreExplanationResponse,
)
from src.infrastructure.http.errors import ApiClientResponseError
from src.infrastructure.repositories.api_opportunity_repository import (
    ApiOpportunityRepository,
    OpportunityNotFoundError,
    OpportunityRepositoryError,
)


class FakeClient:
    def list_opportunities(self, **_kwargs) -> OpportunitiesListResponse:  # type: ignore[no-untyped-def]
        return OpportunitiesListResponse(total=0, items=[])

    def get_opportunity(self, _opportunity_id: str) -> OpportunityDetailResponse:
        return OpportunityDetailResponse(
            id="OPP-001",
            title="Deal",
            seller="Ana",
            manager="Marcos",
            region="Core",
            deal_stage="Engaging",
            amount=100.0,
            scoreExplanation=ScoreExplanationResponse(
                score=70,
                priority_band="medium",
                positive_factors=[],
                negative_factors=[],
                risk_flags=[],
                next_action="ligar",
            ),
        )

    def get_dashboard_kpis(self) -> DashboardKpisResponse:
        return DashboardKpisResponse(
            total_opportunities=1,
            open_opportunities=1,
            won_opportunities=0,
            lost_opportunities=0,
            avg_score=70.0,
        )

    def get_dashboard_filter_options(self) -> DashboardFilterOptionsResponse:
        return DashboardFilterOptionsResponse(
            regional_offices=["Core"],
            managers=["Marcos"],
            deal_stages=["Engaging"],
            regions=["Core"],
        )


def test_repository_happy_path() -> None:
    repo = ApiOpportunityRepository(client=FakeClient())  # type: ignore[arg-type]
    assert repo.list_opportunities().total == 0
    assert repo.get_opportunity("OPP-001").id == "OPP-001"
    assert repo.get_dashboard_kpis().avg_score == 70.0
    fo = repo.get_dashboard_filter_options()
    assert fo.regions == ["Core"]
    assert fo.regional_offices == ["Core"]


class NotFoundClient(FakeClient):
    def get_opportunity(self, _opportunity_id: str) -> OpportunityDetailResponse:
        raise ApiClientResponseError(404, "Opportunity not found")


def test_repository_maps_404_to_domain_error() -> None:
    repo = ApiOpportunityRepository(client=NotFoundClient())  # type: ignore[arg-type]
    with pytest.raises(OpportunityNotFoundError):
        repo.get_opportunity("NOPE")


class GenericErrorClient(FakeClient):
    def list_opportunities(self, **_kwargs) -> OpportunitiesListResponse:  # type: ignore[no-untyped-def]
        raise ApiClientResponseError(500, "boom")


def test_repository_maps_api_error_to_repository_error() -> None:
    repo = ApiOpportunityRepository(client=GenericErrorClient())  # type: ignore[arg-type]
    with pytest.raises(OpportunityRepositoryError):
        repo.list_opportunities()
