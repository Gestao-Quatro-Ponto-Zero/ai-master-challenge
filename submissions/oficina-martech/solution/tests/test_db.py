"""Testes da camada de dados (rodam se o banco estiver seedado)."""
import sqlite3
from pathlib import Path
import pytest

DB = Path(__file__).resolve().parent.parent / "db" / "foco.db"
pytestmark = pytest.mark.skipif(not DB.exists(), reason="rode make seed antes")


def _q(sql):
    with sqlite3.connect(DB) as c:
        return c.execute(sql).fetchone()


def test_seed_counts():
    assert _q("SELECT COUNT(*) FROM sales_pipeline")[0] == 8800
    assert _q("SELECT COUNT(*) FROM sales_teams")[0] == 35


def test_fix_gtxpro_aplicado():
    # higiene: não deve sobrar 'GTXPro' (foi normalizado para 'GTX Pro')
    assert _q("SELECT COUNT(*) FROM sales_pipeline WHERE product='GTXPro'")[0] == 0
    assert _q("SELECT COUNT(*) FROM sales_pipeline WHERE product='GTX Pro'")[0] > 0


def test_fk_integridade_produtos():
    # todo produto do pipeline existe no catálogo
    orphans = _q(
        "SELECT COUNT(*) FROM sales_pipeline p "
        "LEFT JOIN products pr ON pr.product=p.product WHERE pr.product IS NULL"
    )[0]
    assert orphans == 0
