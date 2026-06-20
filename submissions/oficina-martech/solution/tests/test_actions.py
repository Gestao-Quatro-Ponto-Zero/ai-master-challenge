"""Testes da camada de ação (audit log de decisões do vendedor). Banco temporário."""
import sqlite3
from pathlib import Path

import pytest

from scoring.actions import (
    log_action, load_action_state, discarded_ids, contacted_today_ids, action_log,
)

MIGRATION = Path(__file__).resolve().parent.parent / "db" / "migrations" / "0003_actions.sql"


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test.db"
    with sqlite3.connect(db) as c:
        c.executescript(MIGRATION.read_text(encoding="utf-8"))
    return db


def test_log_e_estado_roundtrip(tmp_db):
    log_action("OPP1", "contacted", "Anna", db_path=tmp_db)
    assert load_action_state(tmp_db) == {"OPP1": "contacted"}


def test_ultima_acao_vence(tmp_db):
    """Event sourcing: o estado é a ÚLTIMA ação — descartar e reativar funciona."""
    log_action("OPP1", "discarded", "Anna", db_path=tmp_db)
    assert "OPP1" in discarded_ids(tmp_db)
    log_action("OPP1", "reactivated", "Anna", db_path=tmp_db)
    assert "OPP1" not in discarded_ids(tmp_db)


def test_contacted_today(tmp_db):
    log_action("OPP1", "contacted", "Anna", db_path=tmp_db)
    log_action("OPP2", "discarded", "Bob", db_path=tmp_db)
    assert contacted_today_ids(tmp_db) == {"OPP1"}


def test_acao_invalida_rejeitada(tmp_db):
    with pytest.raises(ValueError):
        log_action("OPP1", "deleted", "Anna", db_path=tmp_db)


def test_action_log_auditoria(tmp_db):
    log_action("OPP1", "contacted", "Anna", note="ligou às 9h", db_path=tmp_db)
    log_action("OPP2", "discarded", "Bob", db_path=tmp_db)
    log = action_log(tmp_db)
    assert len(log) == 2
    assert log[0][2] == "discarded"          # mais recente primeiro
    assert log[1][4] == "ligou às 9h"        # nota preservada