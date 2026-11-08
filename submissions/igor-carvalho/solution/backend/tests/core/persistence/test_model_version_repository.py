import pytest
from sqlalchemy.exc import IntegrityError

from lead_core.persistence import ModelVersionRepository


def register(repo, version, trained_at="2026-11-01T00:00:00Z"):
    repo.register(version, "gbm", trained_at, "2017-12-31", f"/a/v{version}", {"auc": 0.55, "auc_ci95": [0.52, 0.58]})


def test_model_version_lifecycle(database):
    repo = ModelVersionRepository(database)
    register(repo, "2026.11.1")
    register(repo, "2026.11.2", "2026-11-02T00:00:00Z")
    assert repo.get("2026.11.1")["status"] == "candidate" and repo.active() is None

    repo.promote("2026.11.1")
    assert repo.active()["version"] == "2026.11.1" and repo.active()["metrics"]["auc"] == 0.55
    repo.promote("2026.11.2")                                  # troca: a anterior é aposentada
    assert repo.get("2026.11.1")["status"] == "retired" and repo.active()["version"] == "2026.11.2"
    assert sum(v["status"] == "active" for v in repo.list()) == 1
    assert repo.get("2026.11.2")["promoted_at"]


def test_model_version_reject_and_repromote_clears_reason(database):
    repo = ModelVersionRepository(database)
    register(repo, "1")
    repo.reject("1", "AUC pior")
    assert repo.get("1")["status"] == "rejected" and repo.get("1")["reject_reason"] == "AUC pior"
    repo.promote("1")
    assert repo.get("1")["reject_reason"] is None and repo.active()["version"] == "1"


def test_promote_unknown_version_fails_without_retiring_active(database):
    repo = ModelVersionRepository(database)
    register(repo, "1")
    repo.promote("1")
    with pytest.raises(KeyError):
        repo.promote("999")
    assert repo.active()["version"] == "1"


def test_duplicate_version_is_rejected(database):
    repo = ModelVersionRepository(database)
    register(repo, "1")
    with pytest.raises(IntegrityError):
        register(repo, "1")


def test_list_is_newest_first_and_prefix_search(database):
    repo = ModelVersionRepository(database)
    register(repo, "2026.10.1", "2026-10-01T00:00:00Z")
    register(repo, "2026.11.1", "2026-11-01T00:00:00Z")
    register(repo, "2026.11.2", "2026-11-02T00:00:00Z")
    assert [v["version"] for v in repo.list()] == ["2026.11.2", "2026.11.1", "2026.10.1"]
    assert sorted(repo.versions_with_prefix("2026.11.")) == ["2026.11.1", "2026.11.2"]
    assert repo.get("nada") is None
