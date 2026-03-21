"""Fixtures partilhadas: modo demo para contratos API que assumem `demo-opportunities.json`."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _demo_dataset_for_api_contract_tests(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Testes em `test_api_contract.py` exigem IDs/regiões do snapshot demo (determinístico)."""
    if request.path.name != "test_api_contract.py":
        return
    monkeypatch.setenv("LEAD_SCORER_DATA_SOURCE_MODE", "demo_dataset")
