import app

def test_manager_sector_reconciles_with_head():
    app.init_db()
    for region in ("Central","East","West"):
        for entry in app.management_intelligence(region)["sectors"]:
            sector=entry["name"]
            head=app.executive_intelligence(region,"",sector)["stages"]
            manager=app.management_intelligence(region,"",sector)["team"]
            for key in ("Won","Lost","Prospecting","Engaging"):
                assert head[key] == manager[key.lower()]
            assert sum(head.values()) == manager["deals"]

def test_manager_sector_scopes_team():
    app.init_db()
    region="Central"
    names=[m["name"] for m in app.management_intelligence(region)["managers"]]
    assert names
    for manager in names[:2]:
        for entry in app.management_intelligence(region,manager)["sectors"]:
            sector=entry["name"]
            head=app.executive_intelligence(region,manager,sector)["stages"]
            tactical=app.management_intelligence(region,manager,sector)["team"]
            assert tactical["deals"] == sum(head.values())
