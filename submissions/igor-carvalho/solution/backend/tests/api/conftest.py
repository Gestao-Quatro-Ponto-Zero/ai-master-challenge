from __future__ import annotations

import shutil

import pytest
from fastapi.testclient import TestClient

from lead_api.main import create_app
from lead_api.settings import Settings

SECRET = "teste-" + "x" * 40


class FakeRunner:
    """Não executa o treino: só registra o pedido (o job fica 'queued' até o teste marcá-lo)."""

    def __init__(self):
        self.started: list[str] = []

    def start(self, job_id: str) -> None:
        self.started.append(job_id)


def make_settings(artifact_dir, db_path, **kw) -> Settings:
    return Settings(artifact_dir=artifact_dir, db_path=db_path, jwt_secret=SECRET, **kw)


def login(client: TestClient, user_key: str) -> dict:
    r = client.post("/api/v1/auth/login", json={"user_key": user_key})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def ro_client(trained, tmp_path_factory):
    """Cliente somente-leitura compartilhado pelo módulo (não grava feedback/jobs)."""
    tmp = tmp_path_factory.mktemp("ro")
    shutil.copytree(trained["artifact_dir"], tmp / "artifacts")
    shutil.copy(trained["db_path"], tmp / "app.db")
    with TestClient(create_app(make_settings(tmp / "artifacts", tmp / "app.db"), FakeRunner())) as c:
        yield c


@pytest.fixture()
def rw_client(trained_copy):
    runner = FakeRunner()
    settings = make_settings(trained_copy["artifact_dir"], trained_copy["db_path"])
    with TestClient(create_app(settings, runner)) as c:
        c.runner, c.paths, c.settings = runner, trained_copy, settings
        yield c


@pytest.fixture(scope="module")
def seller(ro_client):
    return login(ro_client, "agent-1")


@pytest.fixture(scope="module")
def manager(ro_client):
    return login(ro_client, "mgr-a")


@pytest.fixture(scope="module")
def revops(ro_client):
    return login(ro_client, "revops")
