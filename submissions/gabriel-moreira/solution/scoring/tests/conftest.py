from pathlib import Path

import pytest

from scoring import load_dataset
from scoring.pipeline import build_scoring_context, load_and_score

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return DATA_DIR


@pytest.fixture(scope="session")
def dataset(data_dir):
    return load_dataset(data_dir)


@pytest.fixture(scope="session")
def ctx(dataset):
    return build_scoring_context(dataset)


@pytest.fixture(scope="session")
def scored_pipeline(data_dir):
    return load_and_score(str(data_dir))
