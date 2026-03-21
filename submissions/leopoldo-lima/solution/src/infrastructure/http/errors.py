from __future__ import annotations


class ApiClientError(Exception):
    """Base integration error raised by API client."""


class ApiClientTimeoutError(ApiClientError):
    """Raised when request exceeds configured timeout."""


class ApiClientResponseError(ApiClientError):
    """Raised for non-2xx responses from upstream API."""

    def __init__(self, status_code: int, detail: str, request_id: str | None = None) -> None:
        super().__init__(f"HTTP {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail
        self.request_id = request_id


class ApiClientNotFoundError(ApiClientResponseError):
    """Raised for 404 responses from upstream API."""


class ApiClientValidationError(ApiClientResponseError):
    """Raised for 422 responses from upstream API."""


class ApiClientServerError(ApiClientResponseError):
    """Raised for 5xx responses from upstream API."""
