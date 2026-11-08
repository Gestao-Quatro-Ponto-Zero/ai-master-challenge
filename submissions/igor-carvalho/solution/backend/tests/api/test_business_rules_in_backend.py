"""O front-end só exibe: agrupamento em abas, faixas de prioridade, textos e totais vêm prontos da API."""
import pytest

from lead_core.constants import SUGGESTED_ACTIONS, VIEW_OF_BAND, VIEWS

API = "/api/v1"


def listing(client, headers, **params):
    return client.get(f"{API}/deals", headers=headers, params={"page_size": 200, **params}).json()


def test_meta_publishes_priority_levels_views_and_confidence_rule(ro_client, seller):
    meta = ro_client.get(f"{API}/meta", headers=seller).json()
    assert [(p["key"], p["label"], p["min_score"], p["max_score"]) for p in meta["priority_levels"]] == [
        ("high", "Alta", 80, 100), ("medium", "Média", 40, 79), ("low", "Baixa", 0, 39)]
    assert {v["key"] for v in meta["views"]} == set(VIEWS) and meta["low_confidence_below_closed_deals"] == 30
    assert {"typical_p50", "stale_days", "review_days"} <= set(meta["thresholds"])


def test_each_deal_carries_view_action_and_confidence_reason(revops, ro_client):
    items = listing(ro_client, revops, view="all")["items"]
    assert items
    for d in items:
        assert d["view"] == VIEW_OF_BAND[d["band"]] and d["suggested_action"] == SUGGESTED_ACTIONS[d["band"]]
        assert d["confidence_reason"]          # sempre explica o nível de confiança


@pytest.mark.parametrize("view", list(VIEWS))
def test_view_filter_returns_only_its_bands(ro_client, revops, view):
    body = listing(ro_client, revops, view=view)
    assert {i["band"] for i in body["items"]} <= set(VIEWS[view]["bands"])
    assert body["total"] == ro_client.get(f"{API}/summary", headers=revops).json()["views"][view]["count"]


def test_ev_view_sorts_by_expected_value_and_hides_review(ro_client, revops):
    items = listing(ro_client, revops, view="ev")["items"]
    values = [i["expected_value"] for i in items]
    assert values == sorted(values, reverse=True) and "review" not in {i["band"] for i in items}


@pytest.mark.parametrize("level,lo,hi", [("high", 80, 100), ("medium", 40, 79), ("low", 0, 39)])
def test_priority_filter_matches_levels(ro_client, revops, level, lo, hi):
    items = listing(ro_client, revops, view="all", priority=level)["items"]
    assert all(lo <= i["score"] <= hi and i["priority_level"] for i in items)


def test_max_score_and_priority_combine(ro_client, revops):
    items = listing(ro_client, revops, view="all", min_score=10, max_score=60)["items"]
    assert all(10 <= i["score"] <= 60 for i in items)
    both = listing(ro_client, revops, view="all", priority="medium", max_score=50)["items"]
    assert all(40 <= i["score"] <= 50 for i in both)


def test_summary_views_are_consistent(ro_client, revops):
    v = ro_client.get(f"{API}/summary", headers=revops).json()["views"]
    t = ro_client.get(f"{API}/summary", headers=revops).json()["totals"]
    assert v["all"]["count"] == t["open_deals"] and v["focus"]["count"] >= t["focus"]   # semana = Alta + Média
    assert v["focus"]["count"] + v["follow"]["count"] == sum(
        1 for i in listing(ro_client, revops, view="all", page_size=200)["items"] if i["band"] in ("focus", "follow_up", "low"))
    assert v["ev"]["count"] == t["open_deals"] - t["review"]
    assert v["ev"]["expected_value"] == pytest.approx(t["expected_value"], abs=0.1)
    assert v["review"]["expected_value"] == 0           # zumbis não somam valor esperado


def test_invalid_view_or_priority_is_422(ro_client, revops):
    for params in ({"view": "x"}, {"priority": "x"}, {"max_score": 101}):
        assert ro_client.get(f"{API}/deals", headers=revops, params=params).status_code == 422


# ------------------------------------------------------------------ transparência (fase 1)
def test_detail_explains_each_factor_with_observed_value_and_reference(ro_client, revops):
    ids = [i["opportunity_id"] for i in listing(ro_client, revops, view="ev", sort="score")["items"][:5]]
    seen_reference = False
    for oid in ids:
        d = ro_client.get(f"{API}/deals/{oid}", headers=revops).json()
        for c in d["explanation"]["contributions"]:
            assert c["factor"] and c["direction"] in ("positive", "negative") and 0 <= c["impact"] <= 1
            assert c["label"].startswith(c["factor"]) and c["observed"]
            seen_reference = seen_reference or bool(c["reference"])
        assert d["explanation"]["disclaimer"]
    assert seen_reference                      # ao menos o prazo típico / média geral aparece como referência


def test_data_quality_is_separate_from_confidence(ro_client, revops):
    items = listing(ro_client, revops, view="all")["items"]
    assert any(i["account_missing"] for i in items)
    for d in items:
        q = d["data_quality"]
        assert (q["status"] == "incomplete") == d["account_missing"] and q["summary"]
        assert [m["field"] for m in q["missing"]] == (["account"] if d["account_missing"] else [])
        assert all(m["affects_prediction"] is False for m in q["missing"])      # a conta não entra no modelo
