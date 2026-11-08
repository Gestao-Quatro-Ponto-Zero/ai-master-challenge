
from lead_core import db as raw

from .conftest import TABLES


def test_seed_creates_admin_sellers_and_managers(users):
    assert users.count() == 3
    assert users.get_active("revops")["role"] == "revops"
    assert users.get_active("ana-souza")["manager"] == "Rui Lima" and users.get_active("rui-lima")["role"] == "manager"


def test_seed_is_idempotent(users):
    assert users.seed_from_tables(TABLES) == 0 and users.count() == 3


def test_add_missing_only_inserts_new(users):
    rows = [{"user_key": "ana-souza", "full_name": "x", "role": "seller", "created_at": "t"},
            {"user_key": "novo", "full_name": "Novo", "role": "seller", "created_at": "t"}]
    assert users.add_missing(rows) == 1 and users.get_active("ana-souza")["full_name"] == "Ana Souza"
    assert users.add_missing([]) == 0


def test_inactive_and_unknown_users_are_not_returned(database, users):
    with raw.session(database.path) as conn:
        conn.execute("UPDATE users SET is_active = 0 WHERE user_key = 'ana-souza'")
    assert users.get_active("ana-souza") is None and users.get_active("ninguem") is None


def test_users_are_returned_as_plain_dicts(users):
    assert isinstance(users.get_active("revops"), dict)
