from pathlib import Path

import pytest

from src.data_loader import DatasetNotFoundError, get_data_dir, validate_data_dir

REQUIRED = ("accounts.csv", "products.csv", "sales_pipeline.csv", "sales_teams.csv")


def test_validate_data_dir_accepts_complete_directory(tmp_path: Path):
    for filename in REQUIRED:
        (tmp_path / filename).write_text("header\n", encoding="utf-8")
    assert validate_data_dir(tmp_path) == tmp_path.resolve()


def test_validate_data_dir_rejects_incomplete_directory(tmp_path: Path):
    (tmp_path / "accounts.csv").write_text("account\n", encoding="utf-8")
    with pytest.raises(DatasetNotFoundError):
        validate_data_dir(tmp_path)


def test_environment_variable_has_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    for filename in REQUIRED:
        (tmp_path / filename).write_text("header\n", encoding="utf-8")
    monkeypatch.setenv("CRM_DATA_DIR", str(tmp_path))
    assert get_data_dir() == tmp_path.resolve()
