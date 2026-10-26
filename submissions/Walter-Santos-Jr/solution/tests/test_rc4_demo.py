import app

def test_rc4_historical_filters():
    all_deals=app.historical_conversion()
    melvin=app.historical_conversion({'manager':'Melvin Marxen'})
    assert melvin['won']+melvin['lost'] <= all_deals['won']+all_deals['lost']
    assert melvin['won']+melvin['lost'] > 0
    assert app.historical_conversion({'sales_agent':'__unknown__'})['won']==0

def test_rc4_persona_scopes():
    h=app.Handler.__new__(app.Handler)
    manager={'role':'MANAGER','manager':'Melvin Marxen'}
    seller={'role':'SELLER','seller':'Darcel Schlecht'}
    assert h.scoped_args({'manager':'other'},manager)['manager']=='Melvin Marxen'
    assert h.scoped_args({'sales_agent':'other'},seller)['sales_agent']=='Darcel Schlecht'
    assert not h.authorized('/api/quality/metrics','GET',seller)
    assert not h.authorized('/api/opportunities/X/reassign','POST',seller)
    assert h.authorized('/api/opportunities/X/reassign','POST',manager)
    assert not h.authorized('/api/dashboard','GET',None)

def test_rc4_seller_deal_scope():
    h=app.Handler.__new__(app.Handler)
    seller={'role':'SELLER','seller':'Darcel Schlecht'}
    own=next(r['opportunity_id'] for r in app.ROWS if r['sales_agent']=='Darcel Schlecht')
    other=next(r['opportunity_id'] for r in app.ROWS if r['sales_agent']!='Darcel Schlecht')
    assert h.deal_allowed(own,seller)
    assert not h.deal_allowed(other,seller)
