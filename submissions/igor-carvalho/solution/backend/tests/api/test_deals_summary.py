import pytest

API = "/api/v1"


def get_all(client, headers, **params):
    items, page = [], 1
    while True:
        body = client.get(f"{API}/deals", headers=headers, params={**params, "page": page, "page_size": 200}).json()
        items += body["items"]
        if len(items) >= body["total"]:
            return items, body["total"]
        page += 1


def test_default_list_hides_review_and_prospecting(ro_client, revops):
    items, total = get_all(ro_client, revops)
    assert total == len(items) > 0
    assert not {"review", "prospecting"} & {i["band"] for i in items}


@pytest.mark.parametrize("band", ["focus", "follow_up", "low", "stale_risk", "review", "prospecting"])
def test_band_filter(ro_client, revops, band):
    items, _ = get_all(ro_client, revops, band=band)
    assert all(i["band"] == band for i in items)


@pytest.mark.parametrize("sort,order", [("score", "desc"), ("score", "asc"), ("expected_value", "desc"),
                                        ("expected_value", "asc"), ("age_days", "desc"), ("age_days", "asc")])
def test_sorting(ro_client, revops, sort, order):
    items, _ = get_all(ro_client, revops, sort=sort)
    items = ro_client.get(f"{API}/deals", headers=revops, params={"sort": sort, "order": order, "page_size": 200}).json()["items"]
    values = [i[sort] for i in items if i[sort] is not None]
    assert values == sorted(values, reverse=(order == "desc"))


def test_pagination_is_consistent(ro_client, revops):
    first = ro_client.get(f"{API}/deals", headers=revops, params={"page_size": 7, "page": 1}).json()
    total = first["total"]
    seen = []
    for p in range(1, -(-total // 7) + 1):
        body = ro_client.get(f"{API}/deals", headers=revops, params={"page_size": 7, "page": p}).json()
        assert body["page"] == p and body["total"] == total and len(body["items"]) <= 7
        seen += [i["opportunity_id"] for i in body["items"]]
    assert len(seen) == total == len(set(seen))
    assert ro_client.get(f"{API}/deals", headers=revops, params={"page": 9999}).json()["items"] == []


@pytest.mark.parametrize("params,status", [({"page": 0}, 422), ({"page_size": 0}, 422), ({"page_size": 201}, 422),
                                           ({"min_score": 101}, 422), ({"sort": "nome"}, 422),
                                           ({"order": "up"}, 422), ({"band": "x"}, 422), ({"stage": "Won"}, 422)])
def test_invalid_query_params(ro_client, revops, params, status):
    r = ro_client.get(f"{API}/deals", headers=revops, params=params)
    assert r.status_code == status and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_filters_combine(ro_client, revops):
    items, _ = get_all(ro_client, revops, seller="Agent 2", product="Prod Pro", min_score=50)
    assert all(i["seller"] == "Agent 2" and i["product"] == "Prod Pro" and i["score"] >= 50 for i in items)
    items, _ = get_all(ro_client, revops, office="West")
    assert items and all(i["office"] == "West" for i in items)


def test_search_by_id_and_account(ro_client, revops):
    some, _ = get_all(ro_client, revops)
    target = next(i for i in some if i["account"])
    by_id = ro_client.get(f"{API}/deals", headers=revops, params={"q": target["opportunity_id"][3:8].lower()}).json()
    assert target["opportunity_id"] in {i["opportunity_id"] for i in by_id["items"]}
    by_acc = ro_client.get(f"{API}/deals", headers=revops, params={"q": target["account"].upper()}).json()
    assert target["opportunity_id"] in {i["opportunity_id"] for i in by_acc["items"]}


def test_seller_sees_only_own_deals(ro_client, seller):
    items, _ = get_all(ro_client, seller, band="review")
    items2, _ = get_all(ro_client, seller)
    assert {i["seller"] for i in items + items2} == {"Agent 1"}
    other = ro_client.get(f"{API}/deals", headers=seller, params={"seller": "Agent 5"}).json()
    assert other["total"] == 0                              # filtrar por outro vendedor não vaza nada


def test_manager_sees_only_team(ro_client, manager):
    items, _ = get_all(ro_client, manager)
    assert {i["manager"] for i in items} == {"Mgr A"}


def test_detail_in_and_out_of_scope(ro_client, seller, revops):
    mine = ro_client.get(f"{API}/deals", headers=seller).json()["items"][0]["opportunity_id"]
    d = ro_client.get(f"{API}/deals/{mine}", headers=seller).json()
    assert d["explanation"]["disclaimer"] and d["suggested_action"] and d["explanation"]["contributions"]
    assert set(d["context"]) == {"seller_product", "typical_duration_days"}
    assert d["context"]["seller_product"]["n"] == d["context"]["seller_product"]["won"] + d["context"]["seller_product"]["lost"]

    others, _ = get_all(ro_client, revops, seller="Agent 5")
    r = ro_client.get(f"{API}/deals/{others[0]['opportunity_id']}", headers=seller)
    assert r.status_code == 404 and r.json()["error"]["code"] == "DEAL_NOT_FOUND"   # fora do escopo = 404


def test_filters_endpoint_is_scoped(ro_client, seller, revops):
    mine = ro_client.get(f"{API}/filters", headers=seller).json()
    allf = ro_client.get(f"{API}/filters", headers=revops).json()
    assert mine["sellers"] == ["Agent 1"] and len(allf["sellers"]) == 8
    assert set(allf) == {"sellers", "managers", "offices", "products", "stages", "bands"}


# ------------------------------------------------------------------ summary
@pytest.mark.parametrize("group_by,expected_groups", [("seller", 8), ("manager", 3), ("office", 2)])
def test_summary_groups(ro_client, revops, group_by, expected_groups):
    s = ro_client.get(f"{API}/summary", headers=revops, params={"group_by": group_by}).json()
    assert len(s["groups"]) == expected_groups and s["reference_date"] == "2017-12-31"
    assert sum(g["open_deals"] for g in s["groups"]) == s["totals"]["open_deals"]
    assert sum(g["focus"] for g in s["groups"]) == s["totals"]["focus"]
    assert sum(g["expected_value"] for g in s["groups"]) == pytest.approx(s["totals"]["expected_value"], abs=0.1)
    assert all(0 <= g["review_share"] <= 1 for g in s["groups"])


def test_summary_totals_match_deal_counts(ro_client, revops):
    t = ro_client.get(f"{API}/summary", headers=revops).json()["totals"]
    for band in ("focus", "stale_risk", "review", "prospecting"):
        assert t[band] == ro_client.get(f"{API}/deals", headers=revops, params={"band": band}).json()["total"]


def test_summary_respects_scope_and_validates(ro_client, seller, manager):
    s = ro_client.get(f"{API}/summary", headers=seller).json()
    assert [g["key"] for g in s["groups"]] == ["Agent 1"]
    m = ro_client.get(f"{API}/summary", headers=manager, params={"group_by": "manager"}).json()
    assert [g["key"] for g in m["groups"]] == ["Mgr A"]
    bad = ro_client.get(f"{API}/summary", headers=seller, params={"group_by": "cor"})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "VALIDATION_ERROR"


def test_summary_funnel_heatmap_matches_deals(ro_client, revops):
    """Heatmap produto x tempo no funil: faixas vêm dos limiares do modelo e a soma bate com os deals com data."""
    body = ro_client.get(f"{API}/summary", headers=revops).json()
    f, th = body["funnel"], ro_client.get(f"{API}/meta", headers=revops).json()["thresholds"]
    assert len(f["columns"]) == 4
    assert f["columns"][0]["max_days"] == th["typical_p50"]
    assert f["columns"][2]["max_days"] == th["review_days"] and f["columns"][3]["max_days"] is None
    total = sum(c["count"] for r in f["rows"] for c in r["cells"])
    open_deals = body["totals"]["open_deals"] - body["totals"]["prospecting"]
    assert total == open_deals
    for r in f["rows"]:
        assert len(r["cells"]) == 4 and r["count"] == sum(c["count"] for c in r["cells"])
