# -*- coding: utf-8 -*-
"""Testes da FASE 6 — heurísticas do Copilot (sem carregar modelos pesados)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.copilot import detect_vetoes, suggest_priority, suggest_response
from src.data_prep import TOPIC_CLASSES


def test_priority_critical_on_urgency_language():
    r = suggest_priority("URGENT: production down, all users blocked, need help ASAP")
    assert r["priority"] == "Critical"
    assert r["method"] == "heurística (demo)"


def test_priority_high_on_functional_blockage():
    assert suggest_priority("I cannot access the shared drive since yesterday")["priority"] == "High"


def test_priority_low_and_default_medium():
    assert suggest_priority("Just a question: how to configure my signature, no rush")["priority"] == "Low"
    assert suggest_priority("please update the address on my profile")["priority"] == "Medium"


def test_veto_legal_and_sentiment_and_fraud():
    assert any("advogado" in v["regra"].lower() or "legal" in v["regra"].lower()
               for v in detect_vetoes("I will contact my lawyer about this"))
    assert any("Sentimento" in v["regra"] for v in detect_vetoes("this is unacceptable, worst support"))
    assert any("fraude" in v["regra"] for v in detect_vetoes("there is an unauthorized charge on my card"))
    assert detect_vetoes("please reset my password") == []


def test_veto_returns_full_rule_payload():
    v = detect_vetoes("I'm furious with this")[0]
    assert {"regra", "motivo", "acao"} <= set(v)


def test_suggested_response_covers_all_classes_and_cites_similars():
    sim = pd.DataFrame({"Topic_group": ["Access", "Access", "Storage"],
                        "Document": ["a", "b", "c"], "similarity": [0.9, 0.8, 0.7]})
    for cls in TOPIC_CLASSES:
        resp = suggest_response(cls, sim)
        assert cls in resp and "3 tickets semelhantes" in resp
