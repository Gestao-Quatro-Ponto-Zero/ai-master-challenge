"""Tasks 6.9, 6.10 — determinismo e consistência entre artefato, exportação
CSV e (por transitividade, ver api/tests/test_e2e.py) a API."""

from __future__ import annotations

import dataclasses

import pandas as pd
from aging_by_product_check import build_report as build_aging_by_product_report
from confianca_distribution import build_report as build_confianca_distribution_report
from cycle_duration_permutation import (
    resolution_rate_by_product_and_age,
    run as run_cycle_duration_permutation,
)
from isotonic_check import recompute_curves
from permutation_tests import run_all as run_permutation_tests
from scoring import constants
from scoring.export import export_processed_dataset
from sector_conditioning_check import build_report as build_sector_conditioning_report
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


def test_shrinkage_produto_level_collapses_k_infinite(dataset):
    """Correção do cenário incorreto: o nível de produto NÃO produz k=4 —
    ele colapsa (k infinito) junto com conta×produto e produto×setor.
    K_PRODUTO=4 é uma aproximação retida por política, não o resultado
    deste cálculo."""
    closed = _closed(dataset)
    report = build_shrinkage_report(closed)
    assert report.produto.colapsa
    assert report.conta_produto.colapsa
    assert report.produto_setor.colapsa


def test_determinism_sector_conditioning_report(dataset):
    closed = _closed(dataset)
    report1 = build_sector_conditioning_report(closed)
    report2 = build_sector_conditioning_report(closed)
    for nome in ("prior_global", "produto_encolhido", "produto_setor_encolhido", "produto_setor_bruto"):
        assert report1.score(nome).logloss == report2.score(nome).logloss


def test_sector_conditioning_is_worse_than_global_prior(dataset):
    closed = _closed(dataset)
    report = build_sector_conditioning_report(closed)
    assert report.score("produto_setor_encolhido").logloss > report.score("prior_global").logloss
    assert report.n_celulas_produto_setor > 0


def test_determinism_aging_by_product_report(dataset):
    closed = _closed(dataset)
    report1 = build_aging_by_product_report(closed)
    report2 = build_aging_by_product_report(closed)
    for nome in ("prior_global", "curva_global", "curva_por_produto_bruta", "curva_por_produto_encolhida"):
        assert report1.score(nome).logloss == report2.score(nome).logloss


def test_global_aging_curve_beats_per_product_alternatives(dataset):
    closed = _closed(dataset)
    report = build_aging_by_product_report(closed)
    global_logloss = report.score("curva_global").logloss
    assert global_logloss == min(s.logloss for s in report.scores)
    assert report.existe_celula_com_uma_observacao


def test_determinism_cycle_duration_permutation(dataset):
    closed = _closed(dataset)
    result1 = run_cycle_duration_permutation(closed)
    result2 = run_cycle_duration_permutation(closed)
    assert result1 == result2


def test_cycle_duration_dispersion_compatible_with_noise(dataset):
    closed = _closed(dataset)
    result = run_cycle_duration_permutation(closed)
    assert result.dispersao_observada < result.dispersao_nula_media
    assert result.p_valor > 0.05


def test_resolution_rate_by_product_and_age_covers_all_products(dataset):
    closed = _closed(dataset)
    taxas = resolution_rate_by_product_and_age(closed)
    assert set(taxas["product"]) >= set(constants.PRECO_TABELA) | {"GLOBAL"}


def test_confianca_distribution_report(scored_pipeline):
    report = build_confianca_distribution_report(scored_pipeline.scored)
    assert report.n == 2089
    assert 0 <= report.fracao_sem_precedente <= 1
    assert 0 <= report.fracao_completude_governante <= 1
    for p in (10, 25, 50, 75, 90, 95, 99):
        assert 0 <= report.percentis_confianca[p] <= 100


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
