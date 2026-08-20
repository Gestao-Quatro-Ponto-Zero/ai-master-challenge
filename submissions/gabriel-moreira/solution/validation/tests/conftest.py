from pathlib import Path

import pytest
from scoring.pipeline import load_and_score
from scoring.repository import load_dataset

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return DATA_DIR


@pytest.fixture(scope="session")
def dataset(data_dir):
    return load_dataset(data_dir)


@pytest.fixture(scope="session")
def scored_pipeline(data_dir):
    return load_and_score(str(data_dir))
