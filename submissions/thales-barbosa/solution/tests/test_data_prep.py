# -*- coding: utf-8 -*-
"""Testes da FASE 2 — mecanismo de SLA (função pura) e contratos do pipeline."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_prep import (
    ANNUALIZATION_FACTOR,
    FEATURE_STATUS,
    build_dataset1,
    build_dataset2,
    features_by_status,
    sla_violation,
)


# ---------------------------------------------------------------------------
# sla_violation — mecanismo real (duração >= 0 contra alvo), com durações
# fabricadas VÁLIDAS (nunca os timestamps sintéticos do dataset — D-009)
# ---------------------------------------------------------------------------

def test_sla_violation_basic_rule():
    dur = pd.Series([3 * 60.0, 5 * 60.0, 7 * 60.0, 9 * 60.0])       # horas -> min
    prio = pd.Series(["Critical", "Critical", "High", "High"])       # alvos: 4h, 8h
    out = sla_violation(dur, prio)
    assert out.tolist() == [False, True, False, True]
    assert out.dtype.name == "boolean"


def test_sla_violation_boundary_not_violated():
    # exatamente no alvo NÃO viola (regra é estritamente maior)
    dur = pd.Series([4 * 60.0, 48 * 60.0])
    prio = pd.Series(["Critical", "Low"])
    assert sla_violation(dur, prio).tolist() == [False, False]


def test_sla_violation_null_and_negative_inputs_are_na():
    dur = pd.Series([np.nan, -10.0, 100.0])
    prio = pd.Series(["Low", "Low", "Low"])
    out = sla_violation(dur, prio)
    assert out.isna().tolist() == [True, True, False]  # negativo = input inválido -> NA


def test_sla_violation_accepts_categorical_priority():
    # regressão: .map sobre Series categórica devolve categorical (não multiplica)
    dur = pd.Series([3 * 60.0, 5 * 60.0])
    prio = pd.Series(pd.Categorical(["Critical", "Critical"]))
    assert sla_violation(dur, prio).tolist() == [False, True]


def test_sla_violation_custom_targets():
    dur = pd.Series([30.0, 90.0])
    prio = pd.Series(["Medium", "Medium"])
    out = sla_violation(dur, prio, targets_hours={"Medium": 1.0})
    assert out.tolist() == [False, True]


# ---------------------------------------------------------------------------
# Contratos do pipeline
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def d1():
    return build_dataset1()


@pytest.fixture(scope="module")
def d2():
    return build_dataset2()


def test_d1_shape_and_no_sla_column(d1):
    assert len(d1) == 8469
    # D-009: nenhuma coluna de SLA materializada sobre tempos sintéticos
    assert not any("sla" in c.lower() for c in d1.columns)


def test_d1_synthetic_prefix_convention(d1):
    demo = features_by_status("synthetic_demo")
    assert demo and all(f.startswith("synthetic_") for f in demo)
    assert set(demo) <= set(d1.columns)


def test_d1_structural_nulls_preserved(d1):
    # D-006: NA para quem não tem o estágio, nunca imputado
    assert d1.loc[d1["is_open"], "synthetic_first_response_ts"].isna().all()
    assert d1.loc[~d1["is_closed"], "synthetic_delta_resolution_minutes"].isna().all()
    assert d1.loc[~d1["is_closed"], "is_dissatisfied"].isna().all()
    assert d1.loc[~d1["is_closed"], "resolution_words"].isna().all()


def test_d1_delta_matches_audit(d1):
    delta = d1["synthetic_delta_resolution_minutes"].dropna()
    assert len(delta) == 2769
    neg_pct = (delta < 0).mean() * 100
    assert 48.0 < neg_pct < 51.0  # auditoria: 49,3% negativos


def test_d1_assumption_features_flagged(d1):
    assert FEATURE_STATUS["est_handle_minutes"] == "assumption"
    assert FEATURE_STATUS["est_cost_brl"] == "assumption"
    assert (d1["est_cost_brl"] > 0).all()
    # est_cost coerente: minutos/60 * R$40
    expected = d1["est_handle_minutes"] / 60 * 40.0
    assert np.allclose(d1["est_cost_brl"], expected)


def test_annualization_factor():
    assert ANNUALIZATION_FACTOR == pytest.approx(30_000 / 8_469)


def test_d2_traceability(d2):
    assert len(d2) == 47_823
    assert d2.attrs["rows_removed_short_docs"] == 14
    assert len(d2.attrs["removed_doc_ids"]) == 14
    # doc_id preserva a linha do CSV bruto mesmo após o filtro
    assert d2["doc_id"].max() <= 47_836


def test_feature_status_covers_all_new_columns(d1):
    raw = 17
    assert len(d1.columns) - raw == len(FEATURE_STATUS)


def test_demo_only_never_leaks_into_model_features():
    # guardrail: description_demo não pode sair em nenhuma lista "segura p/ modelo"
    assert FEATURE_STATUS["description_demo"] == "demo_only"
    assert "description_demo" not in features_by_status("measured")
