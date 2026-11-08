"""Casos de uso ponta a ponta das regras de negócio (via API, com o modelo treinado nos dados sintéticos)."""
import pytest

from lead_core.constants import LOW_CONFIDENCE_AGENT_N, PRIORITY_LEVELS, SUGGESTED_ACTIONS
from tests.api.conftest import login

API = "/api/v1"


def all_deals(client, headers, **params):
    items, page = [], 1
    while True:
        body = client.get(f"{API}/deals", headers=headers, params={"view": "all", "page_size": 200, "page": page, **params}).json()
        items += body["items"]
        if len(items) >= body["total"]:
            return items
        page += 1


@pytest.fixture(scope="module")
def deals(ro_client, revops):
    return all_deals(ro_client, revops)


@pytest.fixture(scope="module")
def card(ro_client, seller):
    return ro_client.get(f"{API}/model", headers=seller).json()


# ------------------------------------------------------------------ UC1: o vendedor abre o dia
def test_uc_seller_morning_list_is_priority_ordered(ro_client, seller):
    items = all_deals(ro_client, seller, view="focus")
    scores = [i["score"] for i in items]
    assert scores == sorted(scores, reverse=True) and all(s >= 80 for s in scores)
    assert all(i["priority_level"] == "Alta" and i["view"] == "focus" for i in items)


def test_uc_list_ties_are_broken_by_expected_value(ro_client, revops):
    items = ro_client.get(f"{API}/deals", headers=revops, params={"view": "follow", "page_size": 200}).json()["items"]
    for a, b in zip(items, items[1:]):
        assert (a["score"], a["expected_value"]) >= (b["score"], b["expected_value"])


# ------------------------------------------------------------------ UC2: deals velhos (zumbis)
def test_uc_zombie_deals_have_no_score_and_get_review_action(deals, card):
    review_days = card["thresholds"]["review_days"]
    zombies = [d for d in deals if d["band"] == "review"]
    assert all(d["age_days"] > review_days and d["score"] is None and d["priority_level"] is None for d in zombies)
    assert all(d["suggested_action"] == SUGGESTED_ACTIONS["review"] and d["view"] == "review" for d in zombies)


def test_uc_no_deal_older_than_the_longest_closed_one_is_ranked(deals, card):
    old = [d for d in deals if d["stage"] == "Engaging" and d["age_days"] is not None and d["age_days"] > card["thresholds"]["review_days"]]
    assert all(d["score"] is None for d in old)


# ------------------------------------------------------------------ UC3: deal passou do prazo normal
def test_uc_stale_deals_are_never_in_focus_even_with_high_score(deals, card):
    stale, review = card["thresholds"]["stale_days"], card["thresholds"]["review_days"]
    between = [d for d in deals if d["stage"] == "Engaging" and d["age_days"] is not None and stale < d["age_days"] <= review]
    assert all(d["band"] == "stale_risk" and d["view"] == "decide" for d in between)
    assert all(d["band"] != "stale_risk" for d in deals if d["stage"] == "Engaging" and (d["age_days"] or 0) <= stale)


# ------------------------------------------------------------------ UC4: prospecção
def test_uc_prospecting_deals_have_no_age_or_score(deals):
    prospects = [d for d in deals if d["stage"] == "Prospecting"]
    assert prospects and all(d["band"] == "prospecting" and d["score"] is None and d["view"] == "prospecting" for d in prospects)
    assert all(d["suggested_action"] == SUGGESTED_ACTIONS["prospecting"] for d in prospects)


# ------------------------------------------------------------------ UC5: prioridade e score coerentes
def test_uc_priority_level_always_matches_score(deals):
    for d in deals:
        if d["score"] is None:
            assert d["priority_level"] is None
        else:
            assert d["priority_level"] == next(lbl for _, lbl, lo, hi in PRIORITY_LEVELS if lo <= d["score"] <= hi)


def test_uc_band_matches_score_for_deals_within_normal_age(deals, card):
    for d in deals:
        if d["stage"] == "Engaging" and d["age_days"] is not None and d["age_days"] <= card["thresholds"]["stale_days"]:
            expected = "focus" if d["score"] >= 80 else "follow_up" if d["score"] >= 40 else "low"
            assert d["band"] == expected


def test_uc_higher_expected_value_never_has_lower_score(deals):
    ranked = [(d["expected_value"], d["score"]) for d in deals if d["score"] is not None]
    for ev_a, score_a in ranked:               # o valor esperado sai arredondado em 2 casas: ignora empates de arredondamento
        assert all(score_b >= score_a for ev_b, score_b in ranked if ev_b - ev_a > 0.011)


def test_uc_scores_use_the_whole_scale(deals):
    scores = [d["score"] for d in deals if d["score"] is not None]
    assert max(scores) >= 95 and min(scores) <= 5


# ------------------------------------------------------------------ UC6: confiança
def test_uc_low_confidence_follows_seller_history(ro_client, deals, revops):
    tables = ro_client.app.state.container.store.require().bundle.tables["agent"]
    for d in deals:
        if d["stage"] != "Engaging":
            continue
        closed = tables.get(d["seller"], [0, 0])[1]
        assert (d["confidence"] == "low") == (closed < LOW_CONFIDENCE_AGENT_N), d["seller"]
        assert (d["confidence_reason"] is None) == (d["confidence"] != "low")


# ------------------------------------------------------------------ UC7: probabilidade oculta
def test_uc_probability_is_hidden_by_default_everywhere(ro_client, seller, deals):
    assert all(d["p_win"] is None for d in deals)
    detail = ro_client.get(f"{API}/deals/{deals[0]['opportunity_id']}", headers=login(ro_client, "revops")).json()
    assert detail["p_win"] is None
    assert ro_client.post(f"{API}/score/what-if", headers=seller, json={"product": "Prod Pro", "seller": "Agent 1", "age_days": 10}).json()["p_win"] is None


# ------------------------------------------------------------------ UC8: escopo por papel
@pytest.mark.parametrize("user_key,expected_sellers", [("agent-1", {"Agent 1"}), ("agent-5", {"Agent 5"})])
def test_uc_each_seller_sees_only_own_deals(ro_client, user_key, expected_sellers):
    assert {d["seller"] for d in all_deals(ro_client, login(ro_client, user_key))} == expected_sellers


def test_uc_manager_counts_are_the_sum_of_team_sellers(ro_client, manager):
    team = ro_client.get(f"{API}/me", headers=manager).json()["scope"]["sellers"]
    summary = ro_client.get(f"{API}/summary", headers=manager, params={"group_by": "seller"}).json()
    assert {g["key"] for g in summary["groups"]} == set(team)
    assert sum(g["open_deals"] for g in summary["groups"]) == summary["views"]["all"]["count"]


def test_uc_revops_sees_everything_and_totals_match(ro_client, revops, deals):
    summary = ro_client.get(f"{API}/summary", headers=revops).json()
    assert summary["views"]["all"]["count"] == len(deals) == summary["totals"]["open_deals"]


# ------------------------------------------------------------------ UC9: simulação (what-if)
def test_uc_whatif_age_thresholds(ro_client, seller, card):
    stale, review = card["thresholds"]["stale_days"], card["thresholds"]["review_days"]
    for a, expected in ((stale, {"focus", "follow_up", "low"}), (stale + 1, {"stale_risk"}), (review, {"stale_risk"}), (review + 1, {"review"})):
        out = ro_client.post(f"{API}/score/what-if", headers=seller, json={"product": "Prod Pro", "seller": "Agent 1", "age_days": min(a, 400)}).json()
        assert out["band"] in expected, (a, out["band"])


def test_uc_whatif_agrees_with_listing_for_every_scored_deal(ro_client, revops, deals):
    for d in [x for x in deals if x["stage"] == "Engaging" and x["score"] is not None][:15]:
        out = ro_client.post(f"{API}/score/what-if", headers=revops, json={"product": d["product"], "seller": d["seller"], "age_days": d["age_days"]}).json()
        assert (out["score"], out["band"], out["priority_level"]) == (d["score"], d["band"], d["priority_level"])


# ------------------------------------------------------------------ UC10: feedback guarda o contexto
@pytest.mark.parametrize("action", ["worked", "disagree", "ignore"])
def test_uc_feedback_snapshots_score_band_and_model(rw_client, action):
    h = login(rw_client, "agent-1")
    deal = rw_client.get(f"{API}/deals", headers=h, params={"view": "all", "page_size": 1}).json()["items"][0]
    rw_client.post(f"{API}/deals/{deal['opportunity_id']}/feedback", headers=h, json={"action": action, "comment": "ok"})
    row = rw_client.app.state.container.feedback.feedback.all()[-1]
    assert (row["action"], row["score_at_feedback"], row["band_at_feedback"]) == (action, deal["score"], deal["band"])
    assert row["model_version"] == rw_client.get(f"{API}/meta", headers=h).json()["model_version"]


# ------------------------------------------------------------------ UC11: filtros combinados por regra
@pytest.mark.parametrize("params", [
    {"view": "focus", "priority": "high"}, {"view": "follow", "priority": "medium"}, {"view": "follow", "priority": "low"},
    {"view": "all", "priority": "high", "min_score": 90}, {"view": "all", "min_score": 20, "max_score": 30},
])
def test_uc_filters_never_return_deals_outside_the_rule(ro_client, revops, params):
    items = all_deals(ro_client, revops, **params)
    for d in items:
        assert d["score"] is not None
        if "priority" in params:
            lo, hi = next((lo, hi) for k, _, lo, hi in PRIORITY_LEVELS if k == params["priority"])
            assert lo <= d["score"] <= hi
        assert params.get("min_score", 0) <= d["score"] <= params.get("max_score", 100)


def test_uc_priority_filter_excludes_deals_without_score(ro_client, revops):
    assert all(d["band"] not in ("review", "prospecting") for d in all_deals(ro_client, revops, priority="low"))
