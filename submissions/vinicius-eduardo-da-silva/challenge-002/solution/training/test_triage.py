from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import triage_model as tm

DATA = Path(__file__).resolve().parent.parent / "data"
needs_data = pytest.mark.skipif(not (DATA / tm.IT_FILE).exists(), reason="dataset not downloaded")


@pytest.fixture(scope="module")
def trained():
    tickets = tm.load_it_tickets(DATA)
    train, validation, test = tm.split_by_order(tickets)
    return tm.train_model(train, validation), train, validation, test


@pytest.mark.parametrize(
    "case,expected",
    [
        (dict(confidence=0.99, category="Hardware", known_share=1.0, sensitive=False), ("rotear", "confianca_alta")),
        (dict(confidence=0.99, category="Hardware", known_share=1.0, sensitive=True), ("humano", "sensivel")),
        (dict(confidence=0.99, category="Hardware", known_share=0.5, sensitive=False), ("humano", "desconhecido")),
        (dict(confidence=0.99, category="Administrative rights", known_share=1.0, sensitive=False), ("sugerir", "categoria_protegida")),
        (dict(confidence=0.7, category="Hardware", known_share=1.0, sensitive=False), ("sugerir", "confianca_media")),
        (dict(confidence=0.4, category="Hardware", known_share=1.0, sensitive=False), ("humano", "incerto")),
        (dict(confidence=0.4, category="Administrative rights", known_share=1.0, sensitive=False), ("humano", "incerto")),
    ],
)
def test_policy(case, expected):
    assert tm.decide(guard=0.9, **case) == expected


def test_sensitive_words_match_whole_words_only():
    assert tm.has_sensitive_word("Please process the TERMINATION today")
    assert not tm.has_sensitive_word("illegal legally breachable")


def test_tokenizer_matches_the_vectorizer_rule():
    assert tm.tokenize("Hi, I am a user: é2 x") == ["hi", "am", "user", "é2"]


@needs_data
def test_test_rows_are_the_last_rows_and_never_used_to_learn(trained):
    _, train, validation, test = trained
    tickets = tm.load_it_tickets(DATA)
    assert test.index.min() == int(len(tickets) * 0.8)
    assert test.index.max() == len(tickets) - 1
    assert not set(test.index) & set(train.index)
    assert not set(test.index) & set(validation.index)
    assert not set(train.index) & set(validation.index)


@needs_data
def test_guard_blocks_about_the_chosen_share_of_validation(trained):
    model, _, validation, _ = trained
    assert abs((model.known_share(validation["Document"]) < model.guard).mean() - 0.05) < 0.01


@needs_data
def test_no_sensitive_ticket_is_ever_routed(trained):
    model, _, _, test = trained
    frame = tm.triage_frame(model, test["Document"])
    assert frame["sensitive"].any()
    assert (frame.loc[frame["sensitive"], "lane"] == tm.HUMAN).all()
    assert not (frame.loc[frame["predicted"].isin(tm.NEVER_ROUTE_CATEGORIES), "lane"] == tm.ROUTE).any()


@needs_data
def test_customer_tickets_are_almost_never_routed(trained):
    model, _, _, _ = trained
    frame = tm.triage_frame(model, tm.load_support_tickets(DATA)["Ticket Description"])
    assert (frame["lane"] == tm.ROUTE).mean() < 0.01


def test_empty_ticket_goes_to_a_human():
    tickets = pd.DataFrame(
        {"Document": ["printer broken", "password reset", "printer jam", "reset access", "printer toner", "access password"], "Topic_group": ["Hardware", "Access", "Hardware", "Access", "Hardware", "Access"]}
    )
    model = tm.train_model(tickets, tickets)
    frame = tm.triage_frame(model, pd.Series([""]))
    assert frame["lane"].iloc[0] == tm.HUMAN
