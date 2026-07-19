# -*- coding: utf-8 -*-
"""Testes da FASE 4 — coerência da matriz de automação com a fonte única."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.automation import (
    AUTOMATION_MATRIX_D1,
    D2_CLASS_ROUTING,
    NEVER_AUTOMATE_RULES,
    TIERS,
    render_matrix_markdown,
    render_routing_markdown,
)
from src.data_prep import EFFORT_MULT_BY_TYPE, TOPIC_CLASSES
from src.roi_model import DEFLECTION_BY_TYPE

CRITERIA = {"repetitividade", "previsibilidade", "risco", "criticidade", "julgamento_humano"}


def test_matrix_covers_exactly_the_5_d1_types():
    assert set(AUTOMATION_MATRIX_D1) == set(DEFLECTION_BY_TYPE) == set(EFFORT_MULT_BY_TYPE)


def test_matrix_uses_plan_criteria_with_valid_scores():
    for t, m in AUTOMATION_MATRIX_D1.items():
        assert set(m["criteria"]) == CRITERIA, t
        assert all(1 <= v <= 5 for v in m["criteria"].values()), t
        assert m["tier"] in TIERS, t
        assert m["automatiza"] and m["nunca_automatiza"] and m["justificativa"], t


def test_tier_ordering_consistent_with_deflection_premises():
    # quem tem tier mais automatizável não pode ter deflexão-base menor
    rank = {"automatizar": 2, "parcial": 1, "nao_automatizar": 0}
    items = [(rank[m["tier"]], DEFLECTION_BY_TYPE[t]["base"], t)
             for t, m in AUTOMATION_MATRIX_D1.items()]
    for r1, d1_, t1 in items:
        for r2, d2_, t2 in items:
            if r1 > r2:
                assert d1_ >= d2_, f"{t1} (tier maior) com deflexão menor que {t2}"


def test_judgment_criterion_blocks_full_automation():
    # nenhum tipo com julgamento humano >= 4 pode ser 'automatizar'
    for t, m in AUTOMATION_MATRIX_D1.items():
        if m["criteria"]["julgamento_humano"] >= 4:
            assert m["tier"] != "automatizar", t


def test_routing_covers_all_8_d2_classes():
    assert set(D2_CLASS_ROUTING) == set(TOPIC_CLASSES)
    for cls, r in D2_CLASS_ROUTING.items():
        assert r["tier"] in TIERS and r["team"] and r["nota"], cls


def test_miscellaneous_is_never_deflected():
    # classe guarda-chuva (D-007): confusão esperada -> humano
    assert D2_CLASS_ROUTING["Miscellaneous"]["tier"] == "nao_automatizar"


def test_never_rules_cover_critical_and_legal():
    txt = " ".join(r["regra"].lower() for r in NEVER_AUTOMATE_RULES)
    assert "critical" in txt and ("advogado" in txt or "legal" in txt)
    for r in NEVER_AUTOMATE_RULES:
        assert r["regra"] and r["motivo"] and r["acao"]


def test_doc_tables_match_code_verbatim():
    # guarda anti-drift (D-013): as tabelas de automation_strategy.md devem ser
    # EXATAMENTE as geradas pelo código — se a matriz mudar, o doc regenera
    doc = (Path(__file__).resolve().parents[1] / "docs" / "automation_strategy.md").read_text(
        encoding="utf-8")
    assert render_matrix_markdown() in doc, "tabela D1 do doc divergiu do código"
    assert render_routing_markdown() in doc, "tabela D2 do doc divergiu do código"


def test_rendered_tables_contain_all_rows_and_single_source_values():
    m = render_matrix_markdown()
    for t in AUTOMATION_MATRIX_D1:
        assert t in m
    # deflexão vem da fonte única (spot-check: base de Product inquiry = 65%)
    assert f"**{DEFLECTION_BY_TYPE['Product inquiry']['base']:.0%}**" in m
    r = render_routing_markdown()
    for cls in TOPIC_CLASSES:
        assert cls in r
