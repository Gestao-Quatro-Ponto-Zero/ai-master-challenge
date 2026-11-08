import pytest

from lead_core.persistence import JobAlreadyRunning, JobRepository


def test_job_lifecycle(database, users):
    repo = JobRepository(database)
    job_id = repo.create("retrain", "revops", {"x": 1})
    assert repo.get(job_id)["status"] == "queued" and repo.get(job_id)["started_at"] is None
    repo.mark(job_id, "running")
    assert repo.get(job_id)["status"] == "running" and repo.get(job_id)["started_at"]
    repo.mark(job_id, "succeeded", result={"version": "9"})
    job = repo.get(job_id)
    assert job["result"] == {"version": "9"} and job["finished_at"] and job["error"] is None


def test_only_one_retrain_in_flight_then_released(database, users):
    repo = JobRepository(database)
    first = repo.create("retrain", "revops")
    with pytest.raises(JobAlreadyRunning):
        repo.create("retrain", "revops")
    repo.mark(first, "running")
    with pytest.raises(JobAlreadyRunning):
        repo.create("retrain", "revops")
    repo.mark(first, "failed", error="boom")
    assert repo.get(first)["error"] == "boom"
    repo.create("retrain", "revops")                           # liberado depois de terminar


def test_refresh_jobs_are_not_limited(database, users):
    repo = JobRepository(database)
    assert repo.create("refresh", "revops") != repo.create("refresh", "revops")


def test_unknown_job_is_none(database):
    assert JobRepository(database).get("nada") is None
