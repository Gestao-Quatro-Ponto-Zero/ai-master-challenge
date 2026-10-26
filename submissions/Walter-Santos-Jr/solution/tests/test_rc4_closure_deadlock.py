"""Regression: closing a deal must not reacquire DB_LOCK while already held."""
from pathlib import Path


def test_close_deal_does_not_nest_nonreentrant_lock():
    code = (Path(__file__).resolve().parents[1] / 'app.py').read_text(encoding='utf-8')
    closure = code.split('def close_deal(', 1)[1].split('\ndef sync_jobs(', 1)[0]
    assert 'with DB_LOCK, connect() as db:' in closure
    assert 'with DB_LOCK:' not in closure
    assert "db.execute('BEGIN IMMEDIATE')" in closure
