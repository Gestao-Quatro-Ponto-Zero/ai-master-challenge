"""Camada de ação — registra e consulta decisões do vendedor sobre deals.

Audit log persistente em SQLite (tabela deal_actions, migration 0003):
- 'contacted'  : vendedor agiu no deal hoje -> some do brief, ganha check na lista
- 'discarded'  : vendedor descartou -> sai das listas (reversível com 'reactivated')

O estado efetivo de cada deal é a ÚLTIMA ação registrada (event sourcing simples).
db_path opcional para testes com banco temporário.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

from .data import DB_PATH


def _conn(db_path: Path | str | None = None):
    return sqlite3.connect(db_path or DB_PATH)


def log_action(opportunity_id: str, action: str, actor: str,
               note: str | None = None, db_path=None) -> None:
    """Registra uma ação do vendedor sobre um deal (append-only)."""
    if action not in ("contacted", "discarded", "reactivated"):
        raise ValueError(f"ação inválida: {action}")
    with _conn(db_path) as c:
        c.execute(
            "INSERT INTO deal_actions(opportunity_id, action, actor, note) VALUES (?,?,?,?)",
            (opportunity_id, action, actor, note),
        )


def load_action_state(db_path=None) -> dict[str, str]:
    """Última ação por deal: {opportunity_id: 'contacted'|'discarded'|'reactivated'}."""
    with _conn(db_path) as c:
        rows = c.execute(
            "SELECT opportunity_id, action FROM deal_actions a "
            "WHERE a.id = (SELECT MAX(id) FROM deal_actions WHERE opportunity_id = a.opportunity_id)"
        ).fetchall()
    return {opp: act for opp, act in rows}


def discarded_ids(db_path=None) -> set[str]:
    """Deals cuja última ação foi 'discarded' (fora das listas até reativar)."""
    return {opp for opp, act in load_action_state(db_path).items() if act == "discarded"}


def contacted_today_ids(db_path=None) -> set[str]:
    """Deals contatados HOJE (última ação 'contacted' com data de hoje)."""
    with _conn(db_path) as c:
        rows = c.execute(
            "SELECT opportunity_id, action, date(created_at) = date('now') AS today "
            "FROM deal_actions a "
            "WHERE a.id = (SELECT MAX(id) FROM deal_actions WHERE opportunity_id = a.opportunity_id)"
        ).fetchall()
    return {opp for opp, act, today in rows if act == "contacted" and today}


def action_log(db_path=None, limit: int = 50) -> list[tuple]:
    """Histórico recente (auditoria): [(quando, deal, ação, ator, nota)]."""
    with _conn(db_path) as c:
        return c.execute(
            "SELECT created_at, opportunity_id, action, actor, COALESCE(note,'') "
            "FROM deal_actions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
