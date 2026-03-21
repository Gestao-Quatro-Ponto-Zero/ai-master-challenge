from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from src.api.contracts import (
    DashboardFilterOptionsResponse,
    DashboardKpisResponse,
    OpportunitiesListResponse,
    OpportunityDetailResponse,
)
from src.infrastructure.http.errors import (
    ApiClientNotFoundError,
    ApiClientResponseError,
    ApiClientServerError,
    ApiClientTimeoutError,
    ApiClientValidationError,
)
from src.infrastructure.http.filter_params import OpportunityListFilters, filters_to_query_params


@dataclass(frozen=True)
class ApiClientConfig:
    base_url: str
    timeout_seconds: float = 5.0
    auth_token: str | None = None
    correlation_id: str | None = None

    @classmethod
    def from_env(cls) -> "ApiClientConfig":
        return cls(
            base_url=os.environ.get("LEAD_SCORER_API_BASE_URL", "http://127.0.0.1:8787"),
            timeout_seconds=float(os.environ.get("LEAD_SCORER_API_TIMEOUT_SECONDS", "5")),
            auth_token=os.environ.get("LEAD_SCORER_API_AUTH_TOKEN"),
            correlation_id=os.environ.get("LEAD_SCORER_API_CORRELATION_ID"),
        )


class ApiClient:
    def __init__(self, config: ApiClientConfig, client: httpx.Client | None = None) -> None:
        headers: dict[str, str] = {}
        if config.auth_token:
            headers["Authorization"] = f"Bearer {config.auth_token}"
        if config.correlation_id:
            headers["x-request-id"] = config.correlation_id

        self._config = config
        self._owned_client = client is None
        self._client = client or httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            headers=headers,
        )

    def close(self) -> None:
        if self._owned_client:
            self._client.close()

    def __enter__(self) -> "ApiClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.close()

    def _get(self, path: str, params: dict[str, str | int] | None = None) -> dict:
        try:
            response = self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise ApiClientTimeoutError("Request timed out.") from exc

        request_id = response.headers.get("x-request-id")
        if response.status_code >= 400:
            detail = "Unexpected API error."
            payload = response.json() if response.text else {}
            if isinstance(payload, dict) and isinstance(payload.get("detail"), str):
                detail = payload["detail"]
            if response.status_code == 404:
                raise ApiClientNotFoundError(response.status_code, detail, request_id=request_id)
            if response.status_code == 422:
                raise ApiClientValidationError(response.status_code, detail, request_id=request_id)
            if response.status_code >= 500:
                raise ApiClientServerError(response.status_code, detail, request_id=request_id)
            raise ApiClientResponseError(response.status_code, detail, request_id=request_id)

        payload = response.json()
        if not isinstance(payload, dict):
            raise ApiClientResponseError(
                response.status_code,
                "Invalid JSON payload shape.",
                request_id=request_id,
            )
        return payload

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
        params = filters_to_query_params(
            OpportunityListFilters(
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
        )
        payload = self._get("/api/opportunities", params=params)
        return OpportunitiesListResponse.model_validate(payload)

    def get_opportunity(self, opportunity_id: str) -> OpportunityDetailResponse:
        payload = self._get(f"/api/opportunities/{opportunity_id}")
        return OpportunityDetailResponse.model_validate(payload)

    def get_dashboard_kpis(self) -> DashboardKpisResponse:
        payload = self._get("/api/dashboard/kpis")
        return DashboardKpisResponse.model_validate(payload)

    def get_dashboard_filter_options(self) -> DashboardFilterOptionsResponse:
        payload = self._get("/api/dashboard/filter-options")
        return DashboardFilterOptionsResponse.model_validate(payload)
