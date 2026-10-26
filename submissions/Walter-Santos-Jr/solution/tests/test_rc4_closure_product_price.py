import app
from pathlib import Path

def test_catalog_fields_from_original_opportunity():
    deal=next(r for r in app.ROWS if r['deal_stage'] in ('Engaging','Prospecting'))
    assert isinstance(deal['sales_price'],float)
    assert deal['product_normalized']

def test_sales_action_state_exposes_reference_fields():
    deal=next(r for r in app.ROWS if r['deal_stage'] in ('Engaging','Prospecting') and app.quality_gate(r)['eligible'])
    state=app.sales_action_state(deal['opportunity_id'])
    assert state['product']==deal['product_normalized']
    assert state['catalog_price']==deal['sales_price']
    assert state['quantity'] is None
    assert state['currency'] is None

def test_closure_ui_keeps_transaction_value_separate():
    js=(Path(__file__).resolve().parents[1]/'static'/'app.js').read_text()
    assert 'closure-commercial-summary' in js
    assert 'name="close_value"' in js
    assert 'd.catalog_price' in js
