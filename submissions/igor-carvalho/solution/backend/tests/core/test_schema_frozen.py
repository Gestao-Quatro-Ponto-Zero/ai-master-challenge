"""O esquema SQLite v1 é imutável: qualquer mudança no arquivo quebra este teste (só com pedido explícito)."""
import sqlite3

import pytest

from lead_core import db

EXPECTED_TABLES = {"schema_info", "users", "deal_feedback", "model_versions", "jobs"}


def test_schema_file_hash_is_frozen():
    assert db.schema_sha256() == db.SCHEMA_HASH_FILE.read_text().strip(), (
        "schema_v1.sql foi alterado. O esquema é congelado: só mude com pedido explícito do dono do projeto.")


def test_init_creates_expected_tables(tmp_path):
    db.init_db(tmp_path / "a.db")
    with db.session(tmp_path / "a.db") as conn:
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        assert names == EXPECTED_TABLES
        assert conn.execute("SELECT version FROM schema_info").fetchone()[0] == 1


def test_init_is_idempotent_and_does_not_touch_data(tmp_path):
    p = tmp_path / "a.db"
    db.init_db(p)
    from lead_core.persistence import Database, UserRepository
    UserRepository(Database(p)).seed_from_tables(None)
    db.init_db(p)
    with db.session(p) as conn:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1


@pytest.fixture()
def conn(tmp_path):
    p = tmp_path / "c.db"
    db.init_db(p)
    c = db.connect(p)
    c.execute("INSERT INTO users (user_key, full_name, role, created_at) VALUES ('u', 'U', 'seller', 'x')")
    yield c
    c.close()


def test_feedback_action_is_constrained(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO deal_feedback (opportunity_id, user_key, action, created_at) VALUES ('d','u','bogus','x')")


def test_feedback_comment_max_280(conn):
    ok = "x" * 280
    conn.execute("INSERT INTO deal_feedback (opportunity_id, user_key, action, comment, created_at) VALUES ('d','u','worked',?,'x')", (ok,))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO deal_feedback (opportunity_id, user_key, action, comment, created_at) VALUES ('d','u','worked',?,'x')", (ok + "x",))


def test_feedback_requires_existing_user(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO deal_feedback (opportunity_id, user_key, action, created_at) VALUES ('d','ghost','worked','x')")


def test_only_one_active_model(conn):
    ins = "INSERT INTO model_versions (version, engine, trained_at, reference_date, artifact_path, metrics_json, status) VALUES (?,?,?,?,?,?,?)"
    conn.execute(ins, ("1", "gbm", "t", "r", "p", "{}", "active"))
    conn.execute(ins, ("2", "gbm", "t", "r", "p", "{}", "retired"))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(ins, ("3", "gbm", "t", "r", "p", "{}", "active"))


def test_only_one_retrain_job_in_flight(conn):
    ins = "INSERT INTO jobs (job_id, kind, status, created_at) VALUES (?,?,?,'x')"
    conn.execute(ins, ("a", "retrain", "running"))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(ins, ("b", "retrain", "queued"))
    conn.execute("UPDATE jobs SET status='succeeded' WHERE job_id='a'")
    conn.execute(ins, ("c", "retrain", "queued"))   # liberado depois que o anterior termina


def test_slugify():
    assert db.slugify("Dustin Brinkmann") == "dustin-brinkmann"
    assert db.slugify("Zane Levy") == "zane-levy"
    assert db.slugify("José  D'Ávila") == "jose-d-avila"
