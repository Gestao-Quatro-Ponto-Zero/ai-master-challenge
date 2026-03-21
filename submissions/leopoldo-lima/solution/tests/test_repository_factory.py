from __future__ import annotations

import sys

import pytest

from src.infrastructure.repositories.api_opportunity_repository import ApiOpportunityRepository
from src.infrastructure.repositories.mock_opportunity_repository import MockOpportunityRepository
from src.infrastructure.repositories.repository_factory import create_opportunity_repository


def test_factory_returns_api_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEAD_SCORER_REPOSITORY_MODE", raising=False)
    repo = create_opportunity_repository()
    assert isinstance(repo, ApiOpportunityRepository)


def test_factory_returns_api_when_flag_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEAD_SCORER_REPOSITORY_MODE", "api")
    repo = create_opportunity_repository()
    assert isinstance(repo, ApiOpportunityRepository)


def test_factory_returns_mock_when_flag_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEAD_SCORER_REPOSITORY_MODE", "mock")
    repo = create_opportunity_repository()
    assert isinstance(repo, MockOpportunityRepository)


def test_factory_api_mode_does_not_import_mock_module() -> None:
    sys.modules.pop("src.infrastructure.repositories.mock_opportunity_repository", None)
    create_opportunity_repository(mode="api")
    assert "src.infrastructure.repositories.mock_opportunity_repository" not in sys.modules


def test_factory_rejects_invalid_mode() -> None:
    with pytest.raises(ValueError):
        create_opportunity_repository(mode="invalid")
