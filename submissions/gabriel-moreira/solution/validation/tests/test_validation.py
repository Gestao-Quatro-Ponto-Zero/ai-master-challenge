"""Tasks 6.9, 6.10 — determinismo e consistência entre artefato, exportação
CSV e (por transitividade, ver api/tests/test_e2e.py) a API."""

from __future__ import annotations

import dataclasses

import pandas as pd
from isotonic_check import recompute_curves
from permutation_tests import run_all as run_permutation_tests
from scoring import constants
from scoring.export import export_processed_dataset
from shrinkage_check import build_report as build_shrinkage_report


def _closed(dataset):
    return dataset.pipeline[dataset.pipeline["deal_stage"].isin(constants.DEAL_STAGES_FECHADOS)]


def test_determinism_permutation_tests(dataset):
    closed = _closed(dataset)
    run1 = run_permutation_tests(closed)
    run2 = run_permutation_tests(closed)
    assert [dataclasses.astuple(r) for r in run1] == [dataclasses.astuple(r) for r in run2]


def test_determinism_shrinkage_report(dataset):
    closed = _closed(dataset)
    report1 = build_shrinkage_report(closed)
    report2 = build_shrinkage_report(closed)
    assert report1.produto.k == report2.produto.k
    assert report1.conta_produto.k == report2.conta_produto.k
    assert report1.produto_setor.k == report2.produto_setor.k
    assert report1.p_hat_por_produto_congelado == report2.p_hat_por_produto_congelado


def test_determinism_aging_curves(dataset):
    closed = _closed(dataset)
    curves1 = recompute_curves(closed)
    curves2 = recompute_curves(closed)
    assert curves1.risco_isotonico == curves2.risco_isotonico
    assert curves1.p_ganho_isotonico == curves2.p_ganho_isotonico
    assert curves1.max_duracao_dias == curves2.max_duracao_dias


def test_priority_identical_artifact_vs_exported_csv(scored_pipeline, tmp_path):
    """Task 6.10 — a mesma oportunidade tem PRIORIDADE idêntica calculada
    pelo artefato (em memória) e lida de volta do CSV exportado. Combinado
    com api/tests/test_e2e.py::test_priority_identical_across_api_and_exported_csv
    (task 8.4), isso triangula artefato == API == CSV exportado, todos
    consumindo o mesmo `scoring/`."""
    output_path = export_processed_dataset(scored_pipeline, tmp_path / "processed.csv")
    exported = pd.read_csv(output_path)

    amostra = scored_pipeline.scored.iloc[0]
    linha_exportada = exported[exported["opportunity_id"] == amostra["opportunity_id"]].iloc[0]

    assert round(float(linha_exportada["prioridade"]), 2) == round(float(amostra["prioridade"]), 2)
    assert round(float(linha_exportada["score"]), 1) == round(float(amostra["score"]), 1)
    assert linha_exportada["confianca"] == amostra["confianca"]
    assert linha_exportada["estado"] == amostra["estado"]
