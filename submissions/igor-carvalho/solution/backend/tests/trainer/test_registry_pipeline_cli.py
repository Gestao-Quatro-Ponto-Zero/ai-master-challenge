import json
from datetime import datetime, timezone

import pandas as pd
import pytest

from lead_core.bundle import SCORED_FILE
from lead_core.db import session
from lead_trainer import cli
from lead_trainer.pipeline import run_training
from lead_trainer.registry import ModelRegistry
from tests.conftest import make_config

CONTRACT_COLUMNS = {"opportunity_id", "seller", "manager", "office", "stage", "product", "series", "account",
                    "account_missing", "list_price", "engage_date", "age_days", "p_win_raw", "p_win", "expected_value",
                    "score", "band", "confidence", "flags", "reasons"}


# ------------------------------------------------------------------ registro
def test_versions_increment_within_month(tmp_path):
    reg = ModelRegistry(tmp_path / "a", tmp_path / "db.sqlite")
    now = datetime(2026, 11, 7, tzinfo=timezone.utc)
    assert reg.next_version(now) == "2026.11.1"
    reg.register("2026.11.1", "gbm", "t", "2017-12-31", {"auc": 0.55})
    reg.version_dir("2026.11.1").mkdir(parents=True)
    assert reg.next_version(now) == "2026.11.2"
    assert reg.next_version(datetime(2026, 12, 1, tzinfo=timezone.utc)) == "2026.12.1"


def test_promote_keeps_single_active_and_supports_rollback(tmp_path):
    reg = ModelRegistry(tmp_path / "a", tmp_path / "db.sqlite")
    for v in ("2026.11.1", "2026.11.2"):
        reg.version_dir(v).mkdir(parents=True)
        reg.register(v, "gbm", "t", "r", {"auc": 0.55})
    reg.promote("2026.11.1")
    reg.promote("2026.11.2")
    assert reg.current_version() == "2026.11.2"
    assert [r["status"] for r in reg.list() if r["status"] == "active"] == ["active"]
    reg.promote("2026.11.1")                       # rollback
    assert reg.current_version() == "2026.11.1" and reg.active()["version"] == "2026.11.1"


def test_promote_unknown_version_fails(tmp_path):
    reg = ModelRegistry(tmp_path / "a", tmp_path / "db.sqlite")
    with pytest.raises(FileNotFoundError):
        reg.promote("9.9.9")
    reg.version_dir("9.9.9").mkdir(parents=True)
    with pytest.raises(KeyError):
        reg.promote("9.9.9")


# ------------------------------------------------------------------ pipeline completo
def test_pipeline_writes_all_artifacts(trained):
    version = trained["result"]["version"]
    folder = trained["artifact_dir"] / f"v{version}"
    for name in ("model.txt", "features.json", "calibration.json", "history_tables.json", "score_reference.json",
                 "model_card.json", SCORED_FILE):
        assert (folder / name).exists(), name
    assert (trained["artifact_dir"] / "CURRENT").read_text() == version
    assert trained["result"]["status"] == "active"


def test_scored_deals_columns_and_invariants(trained):
    version = trained["result"]["version"]
    s = pd.read_parquet(trained["artifact_dir"] / f"v{version}" / SCORED_FILE)
    assert CONTRACT_COLUMNS <= set(s.columns)
    assert s["opportunity_id"].is_unique
    assert set(s["stage"]) == {"Engaging", "Prospecting"}
    assert (s[s["stage"] == "Prospecting"]["band"] == "prospecting").all()
    assert s[s["band"].isin(["review", "prospecting"])]["score"].isna().all()
    live = s[~s["band"].isin(["review", "prospecting"])]
    assert live["score"].between(0, 100).all()
    thr = json.loads((trained["artifact_dir"] / f"v{version}" / "model_card.json").read_text())["thresholds"]
    assert (s[s["band"] == "review"]["age_days"] > thr["review_days"]).all()
    assert (s[s["band"] == "focus"]["age_days"] <= thr["stale_days"]).all()
    assert (s[s["band"] == "focus"]["score"] >= 80).all()


def test_model_card_contract(trained):
    version = trained["result"]["version"]
    card = json.loads((trained["artifact_dir"] / f"v{version}" / "model_card.json").read_text())
    assert {"version", "engine", "trained_at", "reference_date", "features", "excludes", "backtest", "thresholds",
            "calibration", "limitations"} <= set(card)
    assert "close_date" in card["excludes"] and "close_value" in card["excludes"]
    assert card["reference_date"] == "2017-12-31"
    assert set(card["thresholds"]) >= {"focus_score", "follow_up_score", "stale_days", "review_days"}


def test_registry_row_matches_artifacts(trained):
    reg = ModelRegistry(trained["artifact_dir"], trained["db_path"])
    row = reg.active()
    assert row["version"] == trained["result"]["version"] and row["status"] == "active"
    assert "auc" in row["metrics"]


def test_training_is_deterministic(synthetic_dir, tmp_path):
    outs = []
    for i in range(2):
        cfg = make_config(tmp_path / str(i), synthetic_dir, skip_backtest=True)
        res = run_training(cfg)
        outs.append(pd.read_parquet(cfg.artifact_dir / f"v{res['version']}" / SCORED_FILE))
    pd.testing.assert_frame_equal(outs[0], outs[1])


def test_second_run_creates_new_version_and_retires_old(synthetic_dir, tmp_path):
    cfg = make_config(tmp_path, synthetic_dir, skip_backtest=True)
    first, second = run_training(cfg), run_training(cfg)
    assert (first["version"], second["version"]) == ("2026.11.1", "2026.11.2")
    reg = ModelRegistry(cfg.artifact_dir, cfg.db_path)
    status = {r["version"]: r["status"] for r in reg.list()}
    assert status == {"2026.11.1": "retired", "2026.11.2": "active"}


def test_gate_rejection_keeps_previous_model(synthetic_dir, tmp_path, monkeypatch):
    cfg = make_config(tmp_path, synthetic_dir, skip_backtest=True)
    first = run_training(cfg)
    weak = {"per_snapshot": [], "auc": 0.50, "auc_ci95": [0.47, 0.53]}
    monkeypatch.setattr("lead_trainer.pipeline.backtest", lambda df, snaps: weak)
    cfg2 = make_config(tmp_path, synthetic_dir, skip_backtest=False, force_promote=False)
    second = run_training(cfg2)

    assert second["status"] == "rejected" and "acaso" in second["reason"]
    reg = ModelRegistry(cfg.artifact_dir, cfg.db_path)
    assert reg.current_version() == first["version"]
    assert {r["version"]: r["status"] for r in reg.list()}[second["version"]] == "rejected"


def test_skip_backtest_without_force_does_not_promote(synthetic_dir, tmp_path):
    cfg = make_config(tmp_path, synthetic_dir, skip_backtest=True, force_promote=False)
    res = run_training(cfg)
    assert res["status"] == "rejected"
    assert ModelRegistry(cfg.artifact_dir, cfg.db_path).current_version() is None


def test_explicit_reference_date_is_respected(synthetic_dir, tmp_path):
    cfg = make_config(tmp_path, synthetic_dir, skip_backtest=True, reference_date="2017-10-31")
    res = run_training(cfg)
    s = pd.read_parquet(cfg.artifact_dir / f"v{res['version']}" / SCORED_FILE)
    assert s["age_days"].max() <= 400 and res["open_deals_scored"] == len(s)
    card = json.loads((cfg.artifact_dir / f"v{res['version']}" / "model_card.json").read_text())
    assert card["reference_date"] == "2017-10-31"


# ------------------------------------------------------------------ CLI
def test_cli_train_list_promote(synthetic_dir, tmp_path, capsys):
    base = ["--data-dir", str(synthetic_dir), "--artifact-dir", str(tmp_path / "a"), "--db", str(tmp_path / "d.db")]
    assert cli.main(base + ["train", "--skip-backtest", "--force"]) == 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["status"] == "active"

    assert cli.main(base + ["train", "--skip-backtest", "--force"]) == 0
    capsys.readouterr()
    assert cli.main(base + ["list"]) == 0
    listing = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert [r["version"] for r in listing] == ["2026.11.2", "2026.11.1"] or len(listing) == 2

    assert cli.main(base + ["promote", listing[-1]["version"]]) == 0
    assert ModelRegistry(tmp_path / "a", tmp_path / "d.db").current_version() == listing[-1]["version"]


def test_cli_evaluate_does_not_write(synthetic_dir, tmp_path, capsys):
    base = ["--data-dir", str(synthetic_dir), "--artifact-dir", str(tmp_path / "a"), "--db", str(tmp_path / "d.db")]
    assert cli.main(base + ["evaluate", "--snapshots", "2017-07-01,2017-09-15"]) == 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["auc"] is not None
    assert not (tmp_path / "a").exists()
