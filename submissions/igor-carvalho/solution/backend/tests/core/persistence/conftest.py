import pytest

from lead_core.persistence import Database, UserRepository

TABLES = {"agents": {"Ana Souza": {"manager": "Rui Lima", "regional_office": "West"}}}


@pytest.fixture()
def database(tmp_path):
    return Database(tmp_path / "t.db")


@pytest.fixture()
def users(database):
    repo = UserRepository(database)
    repo.seed_from_tables(TABLES)
    return repo
