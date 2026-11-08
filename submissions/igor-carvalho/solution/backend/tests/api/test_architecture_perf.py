"""Garantias de arquitetura: a API não treina, não importa o treinador e não altera o esquema."""
import ast
import re
import time
from pathlib import Path

import lightgbm as lgb
import pytest

from lead_core.db import SCHEMA_FILE, session
from tests.api.conftest import login

API = "/api/v1"
SRC = Path(__file__).resolve().parents[2] / "src"


def test_api_package_never_imports_trainer():
    for path in (SRC / "lead_api").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                    [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            assert not any(n.startswith("lead_trainer") for n in names), f"{path} importa lead_trainer"


def test_core_never_imports_api_or_trainer():
    for path in (SRC / "lead_core").rglob("*.py"):
        assert not re.search(r"^\s*(from|import)\s+lead_(api|trainer)", path.read_text(), re.M), path


def test_requests_never_train(ro_client, seller, revops, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("a API tentou treinar durante uma requisição")
    monkeypatch.setattr(lgb, "train", boom)
    monkeypatch.setattr(lgb.LGBMClassifier, "fit", boom)
    assert ro_client.get(f"{API}/deals", headers=seller).status_code == 200
    assert ro_client.post(f"{API}/score/what-if", headers=seller,
                          json={"product": "Prod Pro", "seller": "Agent 1", "age_days": 20}).status_code == 200
    assert ro_client.get(f"{API}/summary", headers=revops).status_code == 200
    assert ro_client.post(f"{API}/admin/refresh", headers=revops).status_code == 200


def test_api_does_not_alter_schema(rw_client):
    h = login(rw_client, "agent-1")
    rw_client.get(f"{API}/deals", headers=h)
    with session(rw_client.paths["db_path"]) as conn:
        tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    declared = set(re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", SCHEMA_FILE.read_text()))
    assert tables == declared


def test_scores_come_from_artifacts_not_database(rw_client):
    with session(rw_client.paths["db_path"]) as conn:
        cols = {r["name"] for t in ("users", "deal_feedback", "model_versions", "jobs")
                for r in conn.execute(f"PRAGMA table_info({t})")}
    assert "score" not in cols and "p_win" not in cols       # só score_at_feedback (cópia histórica)


def p95(values):
    return sorted(values)[int(len(values) * 0.95) - 1]


@pytest.mark.perf
def test_latency_budget(ro_client, seller):
    body = {"product": "Prod Pro", "seller": "Agent 1", "age_days": 30}
    what_if, listing = [], []
    for _ in range(60):
        t = time.perf_counter(); ro_client.post(f"{API}/score/what-if", headers=seller, json=body); what_if.append(time.perf_counter() - t)
        t = time.perf_counter(); ro_client.get(f"{API}/deals?page_size=50", headers=seller); listing.append(time.perf_counter() - t)
    assert p95(what_if) <= 0.150, f"what-if p95 {p95(what_if)*1000:.0f} ms"
    assert p95(listing) <= 0.300, f"/deals p95 {p95(listing)*1000:.0f} ms"
