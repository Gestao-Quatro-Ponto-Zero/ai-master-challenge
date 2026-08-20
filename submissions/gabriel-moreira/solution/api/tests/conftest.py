import os
from pathlib import Path

import pytest
from scoring.repository import load_dataset

DATA_DIR = Path(__file__).resolve().parents[3] / "data"

os.environ.setdefault("LEAD_SCORER_DATA_DIR", str(DATA_DIR))
os.environ.setdefault("LEAD_SCORER_EXPORT_PATH", "/tmp/lead_scorer_test_export.csv")


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return DATA_DIR


@pytest.fixture(scope="session")
def dataset(data_dir):
    return load_dataset(data_dir)


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as test_client:
        yield test_client


def token_for(client, name: str) -> str:
    resp = client.post("/identify", json={"name": name})
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


def auth_headers(client, name: str) -> dict:
    return {"Authorization": f"Bearer {token_for(client, name)}"}
