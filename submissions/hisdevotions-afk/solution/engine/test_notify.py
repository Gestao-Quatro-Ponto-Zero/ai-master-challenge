"""Testes do bot de notificação. Rodam com `python -m pytest` ou `python test_notify.py`."""
import notify as n

DATA = {
    "deals": [
        {"stage": "Engaging", "agent": "Ana Lima", "bucket": "fechar", "account": "Acme", "product": "X",
         "action": "Priorize esta semana.", "ev_soon": 500, "ev": 500, "price": 1000},
        {"stage": "Engaging", "agent": "Ana Lima", "bucket": "decidir", "account": None, "product": "Y",
         "action": "Requalifique ou encerre.", "ev_soon": 0, "ev": 0, "price": 2000},
        {"stage": "Engaging", "agent": "Bea Costa", "bucket": "prospectar", "account": "Beta", "product": "Z",
         "action": "Engaje.", "ev_soon": 100, "ev": 100, "price": 300},
        {"stage": "Won", "agent": "Ana Lima", "bucket": None, "account": "Acme", "product": "X",
         "action": None, "ev_soon": 0, "ev": 0, "price": 1000},
    ],
    "agents": [{"name": "Ana Lima"}, {"name": "Bea Costa"}, {"name": "Cid Rocha"}],  # Cid não tem deal aberto
}


def test_digest_filters_by_agent_and_open_stage():
    text = n.build_digest(DATA, "Ana Lima")
    assert "Acme" in text and "Beta" not in text  # só deals abertos da Ana; o Won dela não entra na fila


def test_digest_flags_missing_account():
    assert "sem conta vinculada" in n.build_digest(DATA, "Ana Lima").lower()


def test_digest_without_agent_is_company_wide():
    text = n.build_digest(DATA, None)
    assert "Acme" in text and "Beta" in text


def test_digest_shows_action_not_just_number():
    assert "Priorize esta semana." in n.build_digest(DATA, "Ana Lima")


def test_destination_prefers_targets_over_global_fallback():
    targets = {"Ana Lima": {"webhook": "https://slack/ana"}}
    assert n.destination("Ana Lima", targets, "https://slack/default", None) == ("https://slack/ana", None)


def test_destination_falls_back_to_global_when_agent_not_configured():
    targets = {"Ana Lima": {"webhook": "https://slack/ana"}}
    assert n.destination("Bea Costa", targets, "https://slack/default", "ops@ex.com") == ("https://slack/default", "ops@ex.com")


def test_load_targets_without_file_is_empty():
    assert n.load_targets(None) == {}


def test_run_all_covers_whole_roster_including_agents_without_deals():
    sent = []
    lines = n.run_all(
        DATA, targets={"Ana Lima": {"webhook": "https://slack/ana"}}, webhook=None, to=None,
        send_slack=lambda url, text: sent.append(("slack", url)),
        send_email=lambda to, subject, text: sent.append(("email", to)),
    )
    assert len(lines) == 3  # todo o roster, não só quem tem deal aberto
    assert any("Ana Lima" in l and "Slack" in l for l in lines)          # tinha target: foi "enviado"
    assert any("Cid Rocha" in l and "sem destino" in l for l in lines)   # sem target nem fallback: modo seguro
    assert sent == [("slack", "https://slack/ana")]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
