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
from circularity_check import build_report as build_circularity_report
from denominator_check import audit as audit_denominator
from fit_permutation import run_produto as run_fit_permutation_produto, run_setor as run_fit_permutation_setor
from isotonic_check import recompute_curves
from permutation_tests import run_all as run_permutation_tests
from reclassification_check import AMOSTRA_PEQUENA_N_MAXIMO, build_report as build_reclassification_report
from scoring import constants
from scoring.export import build_analysis_table, export_processed_dataset
from scoring.fit import build_fit_context
from scoring.pipeline import fechados_calibracao, fechados_organicos
from sector_conditioning_check import build_report as build_sector_conditioning_report
from shrinkage_check import build_report as build_shrinkage_report


def _closed(dataset):
    """População de CALIBRAÇÃO — usada onde idade não é insumo."""
    return fechados_calibracao(dataset)


def _closed_organico(dataset):
    """População ORGÂNICA — a única que pode alimentar idade/duração
    (design.md, D2); usada pelas seções 4/7/8 do backtest."""
    return fechados_organicos(dataset)


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


def test_shrinkage_conta_produto_and_produto_setor_collapse_k_infinite(dataset):
    """conta×produto e produto×setor colapsam (k infinito) — os dois
    níveis continuam sem sinal além do ruído amostral após a
    reclassificação de 200 dias."""
    closed = _closed(dataset)
    report = build_shrinkage_report(closed)
    assert report.conta_produto.colapsa
    assert report.produto_setor.colapsa


def test_shrinkage_produto_level_no_longer_collapses_after_reclassification(dataset):
    """Achado real da recalibração (add-analise-carga-fit, validation
    seção 3): diferente da calibração anterior, o nível de PRODUTO deixa
    de colapsar — GTK 500 cai de n=25/60% para n=35/42,86% e passa a
    dominar a variância entre produtos, produzindo k finito. K_PRODUTO=4
    permanece retido por política (docs/decisions-log.md); este teste
    documenta o novo estado real, não o antigo."""
    closed = _closed(dataset)
    report = build_shrinkage_report(closed)
    assert not report.produto.colapsa
    assert report.produto.k < constants.K_PRODUTO


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
    closed = _closed_organico(dataset)
    report1 = build_aging_by_product_report(closed)
    report2 = build_aging_by_product_report(closed)
    for nome in ("prior_global", "curva_global", "curva_por_produto_bruta", "curva_por_produto_encolhida"):
        assert report1.score(nome).logloss == report2.score(nome).logloss


def test_global_aging_curve_beats_per_product_alternatives(dataset):
    closed = _closed_organico(dataset)
    report = build_aging_by_product_report(closed)
    global_logloss = report.score("curva_global").logloss
    assert global_logloss == min(s.logloss for s in report.scores)
    assert report.existe_celula_com_uma_observacao


def test_determinism_cycle_duration_permutation(dataset):
    closed = _closed_organico(dataset)
    result1 = run_cycle_duration_permutation(closed)
    result2 = run_cycle_duration_permutation(closed)
    assert result1 == result2


def test_cycle_duration_dispersion_compatible_with_noise(dataset):
    closed = _closed_organico(dataset)
    result = run_cycle_duration_permutation(closed)
    assert result.dispersao_observada < result.dispersao_nula_media
    assert result.p_valor > 0.05


def test_resolution_rate_by_product_and_age_covers_all_products(dataset):
    closed = _closed_organico(dataset)
    taxas = resolution_rate_by_product_and_age(closed)
    assert set(taxas["product"]) >= set(constants.PRECO_TABELA) | {"GLOBAL"}


def test_confianca_distribution_report(scored_pipeline):
    report = build_confianca_distribution_report(scored_pipeline.scored)
    assert report.n == 1436
    assert 0 <= report.fracao_sem_precedente <= 1
    assert 0 <= report.fracao_completude_governante <= 1
    for p in (10, 25, 50, 75, 90, 95, 99):
        assert 0 <= report.percentis_confianca[p] <= 100


def test_determinism_aging_curves(dataset):
    closed = _closed_organico(dataset)
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


# --------------------------------------------------------------------------
# Task 8.1/8.2 — antes/depois da reclassificação de 200 dias.
# --------------------------------------------------------------------------


def test_reclassification_report_matches_proposal_numbers(dataset):
    report = build_reclassification_report(dataset)
    assert report.n_reclassificados == 653
    assert report.funil_antes == 2089
    assert report.funil_depois == 1436
    assert round(report.base_rate_antes * 100, 2) == 63.15
    assert round(report.base_rate_depois * 100, 2) == 57.55


def test_reclassification_report_flags_gtk_500_as_small_sample(dataset):
    report = build_reclassification_report(dataset)
    gtk500 = next(p for p in report.produtos if p.produto == "GTK 500")
    assert gtk500.n_depois <= AMOSTRA_PEQUENA_N_MAXIMO
    assert gtk500.amostra_pequena is True
    assert round(gtk500.variacao_pp, 2) == -17.14
    maior_variacao = min(report.produtos, key=lambda p: p.variacao_pp)
    assert maior_variacao.produto == "GTK 500"


# --------------------------------------------------------------------------
# Task 8.3 — auditoria de circularidade acima de 138 dias.
# --------------------------------------------------------------------------


def test_circularity_report_populations_do_not_overlap(dataset):
    report = build_circularity_report(dataset)
    assert report.idade_maxima_organica == 138
    assert report.idade_minima_reclassificada == 200
    assert report.populacoes_nao_se_sobrepoem is True
    assert report.curvas_protegidas is True


# --------------------------------------------------------------------------
# Task 8.4/8.5 — permutação do fit por vendedor e suporte por célula.
# --------------------------------------------------------------------------


def test_fit_permutation_reproducible_with_fixed_seed(dataset):
    closed = _closed(dataset)
    r1 = run_fit_permutation_produto(closed, n_permutations=200)
    r2 = run_fit_permutation_produto(closed, n_permutations=200)
    assert r1 == r2


def test_fit_permutation_setor_not_distinguishable_from_chance(dataset):
    closed = _closed(dataset)
    result = run_fit_permutation_setor(closed)
    assert result.n_celulas == 292
    assert result.p_valor > 0.05


def test_fit_cells_with_insufficient_support_are_counted(dataset):
    closed = _closed(dataset)
    fit_ctx = build_fit_context(dataset, closed)
    assert len(fit_ctx.vendor_product) == 178
    assert len(fit_ctx.vendor_sector) == 292
    insuficientes = sum(1 for g in fit_ctx.vendor_product.values() if g.n < constants.FIT_SUPORTE_MINIMO)
    assert insuficientes > 0


# --------------------------------------------------------------------------
# Task 8.6 — auditoria do denominador dos artefatos de análise.
# --------------------------------------------------------------------------


def test_denominator_audit_passes_for_generated_artifacts(dataset):
    closed = _closed(dataset)
    fit_ctx = build_fit_context(dataset, closed)
    tabela_produto = build_analysis_table(fit_ctx.vendor_product, dataset, "product", "Produto")
    tabela_setor = build_analysis_table(fit_ctx.vendor_sector, dataset, "sector", "Setor")

    assert audit_denominator(tabela_produto, "produto").aprovado
    assert audit_denominator(tabela_setor, "setor").aprovado


def test_denominator_audit_fails_on_inflated_denominator():
    import pandas as pd

    linha_inflada = pd.DataFrame(
        [{"Won": 32, "Lost": 19, "Fechados": 64, "Taxa Vitória %": 50.0, "Engaging": 8, "Prospecting": 5}]
    )
    resultado = audit_denominator(linha_inflada, "artefato de teste")
    assert resultado.aprovado is False
