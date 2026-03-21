from __future__ import annotations

import httpx
import pytest

from src.infrastructure.http.api_client import ApiClient, ApiClientConfig
from src.infrastructure.http.errors import (
    ApiClientNotFoundError,
    ApiClientResponseError,
    ApiClientServerError,
    ApiClientTimeoutError,
    ApiClientValidationError,
)


def test_api_client_list_and_detail_success() -> None:
    captured_query = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_query
        if request.url.path == "/api/opportunities":
            captured_query = request.url.query.decode()
            return httpx.Response(
                200,
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
                            "amount": 10.0,
                            "score": 60,
                            "priority_band": "medium",
                            "next_action": "ligar",
                            "nextBestAction": "ligar",
                        }
                    ],
                },
            )
        if request.url.path == "/api/opportunities/OPP-001":
            return httpx.Response(
                200,
                json={
                    "id": "OPP-001",
                    "title": "Enterprise expansion",
                    "seller": "Ana",
                    "manager": "Marcos",
                    "region": "Core",
                    "deal_stage": "Engaging",
                    "amount": 10.0,
                    "scoreExplanation": {
                        "score": 60,
                        "priority_band": "medium",
                        "positive_factors": [],
                        "negative_factors": [],
                        "risk_flags": [],
                        "next_action": "ligar",
                    },
                },
            )
        return httpx.Response(404, json={"detail": "not found"})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="http://test")
    api_client = ApiClient(ApiClientConfig(base_url="http://test"), client=client)

    listing = api_client.list_opportunities(limit=10)
    assert listing.total == 1
    assert listing.items[0].id == "OPP-001"
    assert captured_query == "sort_by=score&sort_order=desc&limit=10"
    detail = api_client.get_opportunity("OPP-001")
    assert detail.id == "OPP-001"


def test_api_client_list_serializes_filters_with_stable_order() -> None:
    captured_query = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_query
        captured_query = request.url.query.decode()
        return httpx.Response(200, json={"total": 0, "items": []})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="http://test")
    api_client = ApiClient(ApiClientConfig(base_url="http://test"), client=client)

    api_client.list_opportunities(
        region="Core",
        manager="Marcos Silva",
        deal_stage="Engaging",
        q="enterprise plus",
        sort_by="title",
        sort_order="asc",
        limit=25,
        page=2,
        page_size=10,
    )
    expected_query = (
        "region=Core&manager=Marcos+Silva&deal_stage=Engaging&q=enterprise+plus"
        "&sort_by=title&sort_order=asc&limit=25&page=2&page_size=10"
    )
    assert captured_query == expected_query


def test_api_client_response_error() -> None:
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(404, json={"detail": "Opportunity not found"})
    )
    client = httpx.Client(transport=transport, base_url="http://test")
    api_client = ApiClient(ApiClientConfig(base_url="http://test"), client=client)

    with pytest.raises(ApiClientResponseError) as exc_info:
        api_client.get_opportunity("NOPE")
    assert exc_info.value.status_code == 404


def test_api_client_maps_404_to_specific_exception_with_request_id() -> None:
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(
            404,
            json={"detail": "Opportunity not found"},
            headers={"x-request-id": "req-404"},
        )
    )
    client = httpx.Client(transport=transport, base_url="http://test")
    api_client = ApiClient(ApiClientConfig(base_url="http://test"), client=client)

    with pytest.raises(ApiClientNotFoundError) as exc_info:
        api_client.get_opportunity("NOPE")
    assert exc_info.value.status_code == 404
    assert exc_info.value.request_id == "req-404"


def test_api_client_maps_422_and_500_to_specific_exceptions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/invalid"):
            return httpx.Response(422, json={"detail": "Invalid filter"})
        return httpx.Response(500, json={"detail": "Internal server error"})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="http://test")
    api_client = ApiClient(ApiClientConfig(base_url="http://test"), client=client)

    with pytest.raises(ApiClientValidationError):
        api_client.get_opportunity("invalid")
    with pytest.raises(ApiClientServerError):
        api_client.get_opportunity("boom")


def test_api_client_timeout_error() -> None:
    def raise_timeout(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("boom")

    transport = httpx.MockTransport(raise_timeout)
    client = httpx.Client(transport=transport, base_url="http://test")
    api_client = ApiClient(ApiClientConfig(base_url="http://test"), client=client)

    with pytest.raises(ApiClientTimeoutError):
        api_client.list_opportunities()
