import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from lead_api.main import create_app
from lead_api.services.jobs import SubprocessJobRunner
from lead_core.persistence import Database, JobRepository
from lead_core.db import session
from tests.api.conftest import FakeRunner, login, make_settings

API = "/api/v1"
BODY = {"product": "Prod Pro", "seller": "Agent 1", "age_days": 30}


# ------------------------------------------------------------------ what-if
def test_what_if_ok(ro_client, seller):
    r = ro_client.post(f"{API}/score/what-if", headers=seller, json=BODY)
    out = r.json()
    assert r.status_code == 200 and 0 <= out["score"] <= 100 and out["model_version"]
    assert out["band"] in {"focus", "follow_up", "low"} and out["expected_value"] > 0 and out["reasons"]


def test_what_if_is_deterministic_and_age_sensitive(ro_client, seller):
    a = ro_client.post(f"{API}/score/what-if", headers=seller, json=BODY).json()
    b = ro_client.post(f"{API}/score/what-if", headers=seller, json=BODY).json()
    assert a == b
    old = ro_client.post(f"{API}/score/what-if", headers=seller, json={**BODY, "age_days": 120}).json()
    zombie = ro_client.post(f"{API}/score/what-if", headers=seller, json={**BODY, "age_days": 300}).json()
    assert old["band"] == "stale_risk" and zombie["band"] == "review" and zombie["score"] is None


def test_what_if_matches_scored_deal(ro_client, revops):
    """Mesmo vendedor/produto/idade no what-if e no lote dão o mesmo score (mesma lógica de features)."""
    deal = ro_client.get(f"{API}/deals", headers=revops, params={"page_size": 5}).json()["items"][2]
    wi = ro_client.post(f"{API}/score/what-if", headers=revops, json={
        "product": deal["product"], "seller": deal["seller"], "age_days": deal["age_days"]}).json()
    assert wi["score"] == deal["score"] and wi["expected_value"] == pytest.approx(deal["expected_value"], abs=0.01)


@pytest.mark.parametrize("body,field", [
    ({**BODY, "product": "Inexistente"}, "product"), ({**BODY, "seller": "Ninguém"}, "seller")])
def test_what_if_unknown_entities(ro_client, seller, body, field):
    r = ro_client.post(f"{API}/score/what-if", headers=seller, json=body)
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert r.json()["error"]["details"][0]["field"] == field


@pytest.mark.parametrize("age", [-1, 401, "dez"])
def test_what_if_age_validation(ro_client, seller, age):
    assert ro_client.post(f"{API}/score/what-if", headers=seller, json={**BODY, "age_days": age}).status_code == 422


def test_rate_limit_on_what_if(trained_copy):
    settings = make_settings(trained_copy["artifact_dir"], trained_copy["db_path"], rate_limit_per_minute=3)
    with TestClient(create_app(settings)) as c:
        h = login(c, "agent-1")
        codes = [c.post(f"{API}/score/what-if", headers=h, json=BODY).status_code for _ in range(5)]
        assert codes == [200, 200, 200, 429, 429]
        assert c.post(f"{API}/score/what-if", headers=h, json=BODY).json()["error"]["code"] == "RATE_LIMITED"
        assert c.post(f"{API}/score/what-if", headers=login(c, "agent-2"), json=BODY).status_code == 200  # por usuário


# ------------------------------------------------------------------ feedback
def own_deal(client, headers):
    return client.get(f"{API}/deals", headers=headers).json()["items"][0]


def test_feedback_roundtrip_persists_in_sqlite(rw_client):
    h = login(rw_client, "agent-1")
    deal = own_deal(rw_client, h)
    r = rw_client.post(f"{API}/deals/{deal['opportunity_id']}/feedback", headers=h,
                       json={"action": "disagree", "comment": "Cliente pediu para esperar o próximo trimestre."})
    assert r.status_code == 201 and r.json()["id"] == 1

    hist = rw_client.get(f"{API}/deals/{deal['opportunity_id']}/feedback", headers=h).json()["items"]
    assert hist[0]["action"] == "disagree" and hist[0]["user_key"] == "agent-1"
    with session(rw_client.paths["db_path"]) as conn:
        row = conn.execute("SELECT * FROM deal_feedback").fetchone()
    assert row["score_at_feedback"] == deal["score"] and row["band_at_feedback"] == deal["band"] and row["model_version"]


@pytest.mark.parametrize("payload", [{"action": "talvez"}, {}, {"action": "worked", "comment": "x" * 281}])
def test_feedback_validation(rw_client, payload):
    h = login(rw_client, "agent-1")
    r = rw_client.post(f"{API}/deals/{own_deal(rw_client, h)['opportunity_id']}/feedback", headers=h, json=payload)
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_feedback_out_of_scope_is_404(rw_client):
    other = login(rw_client, "agent-5")
    deal_id = own_deal(rw_client, other)["opportunity_id"]
    h = login(rw_client, "agent-1")
    assert rw_client.post(f"{API}/deals/{deal_id}/feedback", headers=h, json={"action": "ignore"}).status_code == 404
    assert rw_client.get(f"{API}/deals/{deal_id}/feedback", headers=h).status_code == 404


def test_feedback_history_is_newest_first(rw_client):
    h = login(rw_client, "agent-1")
    did = own_deal(rw_client, h)["opportunity_id"]
    for a in ("worked", "ignore", "disagree"):
        rw_client.post(f"{API}/deals/{did}/feedback", headers=h, json={"action": a})
    assert [i["action"] for i in rw_client.get(f"{API}/deals/{did}/feedback", headers=h).json()["items"]] == ["disagree", "ignore", "worked"]


# ------------------------------------------------------------------ admin
@pytest.mark.parametrize("method,path", [("post", "/admin/refresh"), ("post", "/admin/retrain"), ("get", "/admin/jobs/x")])
def test_admin_requires_revops(ro_client, seller, manager, method, path):
    for h in (seller, manager):
        r = getattr(ro_client, method)(API + path, headers=h)
        assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN_ROLE"


def test_retrain_creates_job_and_blocks_second(rw_client):
    h = login(rw_client, "revops")
    r = rw_client.post(f"{API}/admin/retrain", headers=h)
    assert r.status_code == 202 and r.json()["status"] == "queued"
    assert rw_client.runner.started == [r.json()["job_id"]]

    again = rw_client.post(f"{API}/admin/retrain", headers=h)
    assert again.status_code == 409 and again.json()["error"]["code"] == "JOB_ALREADY_RUNNING"

    job = rw_client.get(f"{API}/admin/jobs/{r.json()['job_id']}", headers=h).json()
    assert job["status"] == "queued" and job["kind"] == "retrain"
    JobRepository(Database(rw_client.paths["db_path"])).mark(r.json()["job_id"], "succeeded", result={"ok": 1})
    assert rw_client.post(f"{API}/admin/retrain", headers=h).status_code == 202      # liberado depois de terminar


def test_job_not_found(rw_client):
    r = rw_client.get(f"{API}/admin/jobs/nada", headers=login(rw_client, "revops"))
    assert r.status_code == 404 and r.json()["error"]["code"] == "JOB_NOT_FOUND"


def test_refresh_picks_up_a_promoted_version(trained_copy, synthetic_dir):
    from lead_trainer.pipeline import run_training
    from tests.conftest import make_config
    cfg = make_config(trained_copy["tmp"], synthetic_dir, artifact_dir=trained_copy["artifact_dir"],
                      db_path=trained_copy["db_path"], skip_backtest=True)
    with TestClient(create_app(make_settings(cfg.artifact_dir, cfg.db_path), FakeRunner())) as c:
        h = login(c, "revops")
        before = c.get(f"{API}/meta", headers=h).json()["model_version"]
        new = run_training(cfg)["version"]                      # outro processo promove uma versão nova
        assert c.get(f"{API}/meta", headers=h).json()["model_version"] == before   # a API ainda serve a antiga
        r = c.post(f"{API}/admin/refresh", headers=h)
        assert r.status_code == 200 and r.json()["model_version"] == new
        assert c.get(f"{API}/meta", headers=h).json()["model_version"] == new


def test_subprocess_runner_success_and_failure(trained_copy):
    settings = make_settings(trained_copy["artifact_dir"], trained_copy["db_path"])
    with TestClient(create_app(settings, FakeRunner())) as c:
        store, jobs = c.app.state.container.store, JobRepository(Database(settings.db_path))
        ok = subprocess.CompletedProcess([], 0, stdout='log...\n{"version": "9.9.9", "status": "active"}\n', stderr="")
        bad = subprocess.CompletedProcess([], 1, stdout="", stderr="boom")

        for proc, expected in ((ok, "succeeded"), (bad, "failed")):
            runner = SubprocessJobRunner(settings, store, jobs, runner=lambda *a, _p=proc, **k: _p)
            job_id = jobs.create("retrain", "revops")
            runner._execute(job_id)
            job = jobs.get(job_id)
            assert job["status"] == expected and job["finished_at"]
        assert job["error"] == "boom"


def test_runner_command_calls_trainer_module(trained_copy):
    settings = make_settings(trained_copy["artifact_dir"], trained_copy["db_path"])
    cmd = SubprocessJobRunner(settings, None, None).command()
    assert cmd[:3] == [sys.executable, "-m", "lead_trainer"] and cmd[-1] == "train"
    assert str(settings.artifact_dir) in cmd and str(settings.db_path) in cmd


# ------------------------------------------------------------------ health / meta / model
def test_health_and_meta_and_model(ro_client, seller):
    assert ro_client.get(f"{API}/health/live").json() == {"status": "ok"}
    assert ro_client.get(f"{API}/health/ready").json()["status"] == "ok"
    meta = ro_client.get(f"{API}/meta", headers=seller).json()
    assert meta["reference_date"] == "2017-12-31" and meta["show_probability"] is False
    card = ro_client.get(f"{API}/model", headers=seller).json()
    assert card["engine"] == "gbm" and "close_date" in card["excludes"] and card["limitations"]


def test_not_ready_without_model(tmp_path):
    settings = make_settings(tmp_path / "empty", tmp_path / "app.db")
    with TestClient(create_app(settings)) as c:
        assert c.get(f"{API}/health/live").status_code == 200
        r = c.get(f"{API}/health/ready")
        assert r.status_code == 503 and r.json()["error"]["code"] == "MODEL_NOT_READY"
        h = login(c, "revops")                                   # admin existe mesmo sem modelo
        assert c.get(f"{API}/deals", headers=h).json()["error"]["code"] == "MODEL_NOT_READY"
        assert c.post(f"{API}/admin/refresh", headers=h).status_code == 503
