import app

def test_reconciliation_unique_ids():
    rows=app.reconciled_historical_rows()
    ids=[r['opportunity_id'] for r in rows]
    assert len(ids)==len(set(ids))

def test_reconciliation_closures():
    with app.DB_LOCK, app.connect() as db:
        closures=[dict(r) for r in db.execute('SELECT * FROM deal_closures')]
    rows={r['opportunity_id']:r for r in app.reconciled_historical_rows()}
    for c in closures:
        if c['opportunity_id'] in rows:
            assert rows[c['opportunity_id']]['deal_stage']==c['outcome']
            assert rows[c['opportunity_id']]['closure_source']=='operational_sqlite'
