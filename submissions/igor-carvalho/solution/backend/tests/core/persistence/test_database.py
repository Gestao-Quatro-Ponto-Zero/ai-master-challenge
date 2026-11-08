"""Database: esquema congelado, pragmas, rollback e acesso concorrente ao mesmo arquivo."""
import pytest

from lead_core import db as raw
from lead_core.persistence import Database, UserRepository

from .conftest import TABLES


def test_orm_does_not_create_or_alter_tables(database):
    with raw.session(database.path) as conn:
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    assert names == {"schema_info", "users", "deal_feedback", "model_versions", "jobs"}
    assert raw.schema_sha256() == raw.SCHEMA_HASH_FILE.read_text().strip()


def test_pragmas_are_applied_on_every_connection(database):
    with database.session() as s:
        assert s.connection().exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        assert s.connection().exec_driver_sql("PRAGMA journal_mode").scalar().lower() == "wal"


def test_session_rolls_back_on_error(database):
    users = UserRepository(database)
    with pytest.raises(RuntimeError):
        with database.session() as s:
            s.connection().exec_driver_sql("INSERT INTO users (user_key, full_name, role, created_at) VALUES ('x','X','seller','t')")
            raise RuntimeError("boom")
    assert users.get_active("x") is None


def test_two_database_handles_see_the_same_data(tmp_path):
    a, b = Database(tmp_path / "s.db"), Database(tmp_path / "s.db")
    UserRepository(a).seed_from_tables(TABLES)
    assert UserRepository(b).get_active("ana-souza") is not None
