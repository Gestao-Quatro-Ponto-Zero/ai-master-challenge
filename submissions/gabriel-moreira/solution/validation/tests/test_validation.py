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
from power_check import PODER_ALVO, build_report as build_power_report
from reclassification_check import AMOSTRA_PEQUENA_N_MAXIMO, build_report as build_reclassification_report
from scoring import constants
from scoring.export import build_analysis_table, export_processed_dataset
from scoring.fit import build_fit_context
from scoring.pipeline import fechados
from sector_conditioning_check import build_report as build_sector_conditioning_report
from shrinkage_check import build_report as build_shrinkage_report


def _closed(dataset):
    """População única de calibração: os negócios com desfecho observado.
    Eram duas (calibração e orgânica) enquanto o expurgo de 200 dias
    existia — ver docs/decisions-log.md, entrada 2026-08-29."""
    return fechados(dataset)


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
    assert report1.p_hat_por_produto == report2.p_hat_por_produto


def test_shrinkage_conta_produto_and_produto_setor_collapse_k_infinite(dataset):
    """conta×produto e produto×setor colapsam (k infinito) — os dois
    níveis continuam sem sinal além do ruído amostral após a
    reclassificação de 200 dias."""
    closed = _closed(dataset)
    report = build_shrinkage_report(closed)
    assert report.conta_produto.colapsa
    assert report.produto_setor.colapsa


def test_shrinkage_produto_level_colapsa(dataset):
    """Sobre desfecho observado, os três níveis abaixo do global colapsam —
    inclusive produto. Ele chegou a não colapsar (k ≈ 0,6966) entre
    2026-08-21 e 2026-08-29, efeito do expurgo de 200 dias, não dos dados:
    GTK 500 recebia 10 perdas atribuídas sobre 25 fechados e sozinho virava
    a variância em excesso do nível. Ver docs/decisions-log.md."""
    closed = _closed(dataset)
    report = build_shrinkage_report(closed)
    assert report.produto.colapsa
    assert report.produto.var_em_excesso <= 0


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


# --------------------------------------------------------------------------
# Sensibilidade ao expurgo de 200 dias — medido, nunca aplicado.
# --------------------------------------------------------------------------


def test_expurgo_nao_e_aplicado(dataset):
    """A garantia central: o cenário é calculado, o dataset não muda."""
    report = build_reclassification_report(dataset)
    assert report.aplicado_em_producao is False
    assert report.n_candidatos == 653
    assert report.funil_real == 2089
    assert report.funil_hipotetico == 1436
    assert round(report.base_rate_real * 100, 2) == 63.15
    assert round(report.base_rate_hipotetica * 100, 2) == 57.55


def test_expurgo_fabricaria_discriminacao_por_produto(dataset):
    """Sobre desfecho observado o nível de produto colapsa e p̂ é igual
    para os sete. O expurgo sozinho cria 16,66pp de amplitude — puxados por
    GTK 500, o produto de menor amostra."""
    import math

    report = build_reclassification_report(dataset)
    nivel = report.nivel_produto
    assert math.isinf(nivel.k_real)
    assert not math.isinf(nivel.k_hipotetico)
    assert nivel.var_em_excesso_real <= 0 < nivel.var_em_excesso_hipotetica
    assert round(nivel.amplitude_p_hat_real_pp, 2) == 0.00
    assert round(nivel.amplitude_p_hat_hipotetica_pp, 2) == 16.66

    gtk500 = next(p for p in report.produtos if p.produto == "GTK 500")
    assert gtk500.n_real == 25
    assert gtk500.n_hipotetico == 35
    assert gtk500.amostra_pequena is True
    assert round(gtk500.variacao_pp, 2) == -17.14
    maior_variacao = min(report.produtos, key=lambda p: p.variacao_pp)
    assert maior_variacao.produto == "GTK 500"


def test_expurgo_fabricaria_o_sinal_de_vendedor(dataset):
    """O achado que motivou a remoção: nenhum atributo é significativo
    sobre desfecho observado, e o expurgo torna `sales_agent` significativo
    ao concentrar perdas atribuídas em algumas carteiras."""
    report = build_reclassification_report(dataset)
    por_atributo = {s.atributo: s for s in report.sinais}

    assert all(s.p_real > 0.05 for s in report.sinais)
    vendedor = por_atributo["sales_agent"]
    assert vendedor.p_real > 0.05
    assert vendedor.p_hipotetico < 0.05

    assert report.n_vendedores_sem_candidato > 0
    assert report.amplitude_vendedor_hipotetica_pp > report.amplitude_vendedor_real_pp


# --------------------------------------------------------------------------
# Task 8.3 — auditoria de circularidade acima de 138 dias.
# --------------------------------------------------------------------------


def test_circularity_report_sem_desfecho_atribuido(dataset):
    """A invariante que substitui a auditoria das duas populações: nenhum
    negócio da calibração tem desfecho sem evento, e a fronteira de censura
    cobre toda a faixa de idade que a calibração viu. O funil aberto vai
    muito além dela (423 dias) — e continua aberto."""
    report = build_circularity_report(dataset)
    assert report.n_calibracao == 6711
    assert report.n_sem_close_date == 0
    assert report.idade_maxima_observada == 138
    assert report.todos_desfechos_observados is True
    assert report.censura_cobre_a_calibracao is True
    assert report.idade_maxima_aberta > report.fronteira_censura


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
    assert result.n_celulas == 288
    assert result.p_valor > 0.05


def test_fit_cells_with_insufficient_support_are_counted(dataset):
    closed = _closed(dataset)
    fit_ctx = build_fit_context(dataset, closed)
    assert len(fit_ctx.vendor_product) == 178
    assert len(fit_ctx.vendor_sector) == 288
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


# --------------------------------------------------------------------------
# Seção 14 — poder do teste de vendedor. O que sustenta a redação "não
# CONSEGUIMOS VER diferença" no lugar de "não há diferença".
# --------------------------------------------------------------------------


def test_power_report_reproducible_with_fixed_seed(dataset):
    closed = _closed(dataset)
    r1 = build_power_report(closed, n_simulacoes=200)
    r2 = build_power_report(closed, n_simulacoes=200)
    assert dataclasses.astuple(r1) == dataclasses.astuple(r2)


def test_amplitude_observada_cabe_no_que_o_acaso_produz(dataset):
    """O número que impede a leitura ingênua: os 15,42pp entre o melhor e o
    pior vendedor são a amplitude que 30 carteiras deste tamanho já
    produzem sem nenhuma diferença de habilidade."""
    report = build_power_report(_closed(dataset))
    assert report.spread_observado_dentro_do_nulo
    assert report.spread_nulo_p2_5_pp < report.spread_observado_pp < report.spread_nulo_p97_5_pp


def test_dispersao_verdadeira_estimada_e_positiva_mas_abaixo_do_detectavel(dataset):
    """O núcleo da seção: τ̂ > 0 (não afirmamos igualdade) e τ̂ < MDE (não
    afirmamos sinal). As duas leituras extremas caem juntas."""
    report = build_power_report(_closed(dataset))
    assert report.tau_excesso_pp > 0
    assert report.mde_pp is not None
    assert report.tau_abaixo_do_detectavel


def test_curva_de_poder_e_monotonica_e_cobre_o_corte(dataset):
    """Poder cresce com o efeito verdadeiro — e a grade precisa alcançar o
    corte de 80%, senão o MDE seria só o fim da grade."""
    report = build_power_report(_closed(dataset), n_simulacoes=400)
    poderes = [ponto.poder for ponto in report.curva_poder]
    assert poderes == sorted(poderes)
    assert poderes[0] < PODER_ALVO <= poderes[-1]


def test_vendedor_unico_pre_especificado_e_mais_facil_que_o_omnibus(dataset):
    """O teto: um efeito de 10pp num vendedor escolhido de antemão é
    detectável, e é isso que separa "grande demais para escapar" de "pequeno
    demais para ver"."""
    report = build_power_report(_closed(dataset))
    por_delta = {ponto.delta_pp: ponto.poder for ponto in report.poder_vendedor_unico}
    assert por_delta[10.0] > 0.8
    assert por_delta[5.0] < 0.5
