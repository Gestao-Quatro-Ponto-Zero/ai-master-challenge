import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app

def test_personas_start_without_pinned_identity():
    assert app.DEMO_PERSONAS['manager']['manager'] is None
    assert app.DEMO_PERSONAS['seller']['seller'] is None

def test_unselected_persona_cannot_access_deal():
    deal=next(iter(app.INDEX))
    assert not app.Handler.deal_allowed(None,deal,{'role':'MANAGER','manager':None})
    assert not app.Handler.deal_allowed(None,deal,{'role':'SELLER','seller':None})

def test_hierarchy_all_regions_before_identity():
    for role in ('MANAGER','SELLER'):
        p={'role':role,'manager':None,'seller':None}
        assert {r['name'] for r in app.hierarchy(p)['regions']} == {r['regional_office'] for r in app.ROWS}

def test_scoped_args_fail_closed_until_identity():
    assert app.Handler.scoped_args(None,{}, {'role':'MANAGER','manager':None})['manager']=='__UNSELECTED_MANAGER__'
    assert app.Handler.scoped_args(None,{}, {'role':'SELLER','seller':None})['sales_agent']=='__UNSELECTED_SELLER__'
