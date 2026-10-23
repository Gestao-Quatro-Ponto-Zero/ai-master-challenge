from pathlib import Path

from ravenlake import pipeline, sources

HEADERS = {
    "accounts": "account_id,account_name",
    "subscriptions": "subscription_id,account_id",
    "feature_usage": "usage_id,subscription_id",
    "support_tickets": "ticket_id,account_id",
    "churn_events": "churn_event_id,account_id",
}


def test_from_local_reads_all_datasets(tmp_path: Path) -> None:
    for dataset, header in HEADERS.items():
        (tmp_path / sources.file_name(dataset)).write_text(f"{header}\nX-1,A-1\n")

    snapshot = sources.from_local(tmp_path)

    assert snapshot.source == "local"
    assert set(snapshot.files) == set(sources.DATASETS)
    assert snapshot.files["accounts"].startswith(b"account_id")


def test_sha256_is_stable() -> None:
    assert pipeline.sha256(b"abc") == pipeline.sha256(b"abc")
    assert pipeline.sha256(b"abc") != pipeline.sha256(b"abd")
