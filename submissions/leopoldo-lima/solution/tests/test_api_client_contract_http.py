from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from src.infrastructure.http.api_client import ApiClient, ApiClientConfig
from src.infrastructure.http.errors import (
    ApiClientNotFoundError,
    ApiClientServerError,
    ApiClientTimeoutError,
    ApiClientValidationError,
)


@pytest.fixture
def api_client() -> ApiClient:
    return ApiClient(ApiClientConfig(base_url="http://test"))


def test_contract_list_opportunities_happy_path(
    api_client: ApiClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        method="GET",
        url="http://test/api/opportunities?region=Core&sort_by=score&sort_order=desc&limit=20",
        json={
            "total": 1,
            "items": [
                {
                    "id": "OPP-001",
                    "title": "Enterprise expansion",
                    "seller": "Ana",
                    "manager": "Marcos",
                    "region": "Core",
                    "deal_stage": "Engaging",
                    "amount": 1000.0,
                    "score": 77,
                    "priority_band": "high",
                    "next_action": "ligar hoje",
                    "nextBestAction": "ligar hoje",
                }
            ],
        },
    )

    result = api_client.list_opportunities(region="Core", limit=20)
    assert result.total == 1
    assert result.items[0].id == "OPP-001"
    assert result.items[0].priority_band == "high"


def test_contract_detail_404_maps_to_not_found(
    api_client: ApiClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        method="GET",
        url="http://test/api/opportunities/NOPE",
        status_code=404,
        json={"detail": "Opportunity not found"},
        headers={"x-request-id": "req-404"},
    )

    with pytest.raises(ApiClientNotFoundError) as exc:
        api_client.get_opportunity("NOPE")
    assert exc.value.request_id == "req-404"


def test_contract_validation_422_maps_to_validation_error(
    api_client: ApiClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        method="GET",
        url="http://test/api/opportunities?sort_by=invalid&sort_order=desc&limit=20",
        status_code=422,
        json={"detail": "Invalid query"},
    )
    with pytest.raises(ApiClientValidationError):
        api_client.list_opportunities(sort_by="invalid")


def test_contract_500_maps_to_server_error(api_client: ApiClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="http://test/api/dashboard/kpis",
        status_code=500,
        json={"detail": "Internal server error"},
    )
    with pytest.raises(ApiClientServerError):
        api_client.get_dashboard_kpis()


def test_contract_timeout_maps_to_timeout_error(
    api_client: ApiClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_exception(httpx.ReadTimeout("timeout"))
    with pytest.raises(ApiClientTimeoutError):
        api_client.get_dashboard_filter_options()
