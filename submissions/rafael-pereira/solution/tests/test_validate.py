"""Testes das primitivas de métrica do backtest (dados de brinquedo, resultados conferidos à mão)."""

import itertools
import math

import numpy as np
import pytest

from scorer import validate
from scorer.validate import auc, beats, bootstrap_diff, brier, log_loss, random_baseline, top_share


# --- auc -------------------------------------------------------------------------------------
def test_auc_perfect_inverted_and_all_tied():
    y = [1, 1, 0, 0, 0]
    assert auc([0.9, 0.8, 0.3, 0.2, 0.1], y) == 1.0
    assert auc([0.1, 0.2, 0.3, 0.8, 0.9], y) == 0.0
    assert auc([0.5] * 5, y) == 0.5


def test_auc_small_case_by_hand():
    # positivos: 0,9 e 0,7; negativos: 0,8, 0,6 e 0,5. São 6 pares; 0,9 vence 3 e 0,7 vence 2: 5/6.
    assert auc([0.9, 0.8, 0.7, 0.6, 0.5], [1, 0, 1, 0, 0]) == pytest.approx(5 / 6)


def test_auc_ties_count_half():
    # positivos 1 e 2, negativo 1: o par (1, 1) vale 0,5 e o par (2, 1) vale 1 -> 1,5/2.
    assert auc([1, 1, 2], [1, 0, 1]) == pytest.approx(0.75)


def test_auc_accepts_bool_and_ignores_input_order():
    score = np.array([0.9, 0.1, 0.8, 0.3])
    y = np.array([True, False, True, False])
    assert auc(score, y) == 1.0
    order = np.array([2, 0, 3, 1])
    assert auc(score[order], y[order]) == 1.0


def test_auc_single_class_is_nan():
    assert math.isnan(auc([0.1, 0.2, 0.3], [1, 1, 1]))
    assert math.isnan(auc([0.1, 0.2, 0.3], [0, 0, 0]))


def test_auc_length_mismatch_raises():
    with pytest.raises(ValueError):
        auc([0.1, 0.2], [1, 0, 1])


# --- top_share -------------------------------------------------------------------------------
def test_top_share_all_tied_equals_frac():
    gain = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0], dtype=float)
    assert top_share(np.zeros(10), gain, 0.2) == pytest.approx(0.2)
    # com ganhos desiguais, o valor esperado sob desempate aleatório continua sendo frac
    assert top_share(np.ones(10), np.arange(10.0), 0.2) == pytest.approx(0.2)


def test_top_share_default_frac_is_config_top_frac():
    assert top_share(np.zeros(10), np.ones(10)) == pytest.approx(0.2)


def test_top_share_perfect_order_concentrates():
    score = np.arange(10, 0, -1, dtype=float)  # 10, 9, ..., 1
    gain = np.array([5, 3, 1, 1, 0, 0, 0, 0, 0, 0], dtype=float)
    assert top_share(score, gain, 0.2) == pytest.approx(8 / 10)  # K = 2: 5 + 3 de 10
    # ganhos todos no topo: captura 100%
    assert top_share(score, np.array([1, 1] + [0] * 8, dtype=float), 0.2) == 1.0
    # ordem invertida: o topo não tem ganho
    assert top_share(-score, np.array([1, 1] + [0] * 8, dtype=float), 0.2) == 0.0


def test_top_share_ignores_input_order():
    score = np.array([5, 4, 4, 4, 3, 3, 2, 2, 1, 1], dtype=float)
    gain = np.array([10, 3, 6, 9, 1, 1, 1, 1, 1, 1], dtype=float)
    order = np.random.default_rng(7).permutation(10)
    assert top_share(score[order], gain[order], 0.2) == pytest.approx(top_share(score, gain, 0.2))


def test_top_share_tie_at_cut_by_hand():
    # n = 10, K = 2. O score 5 (ganho 10) cabe inteiro; o grupo do score 4 tem 3 deals
    # (ganhos 3, 6 e 9 = 18) e cruza o corte: entra (2 - 1)/3 = 1/3 do grupo = 6.
    # Total = 10 + 18 + 6 = 34, então a captura é (10 + 6)/34.
    score = np.array([5, 4, 4, 4, 3, 3, 2, 2, 1, 1], dtype=float)
    gain = np.array([10, 3, 6, 9, 1, 1, 1, 1, 1, 1], dtype=float)
    assert top_share(score, gain, 0.2) == pytest.approx(16 / 34)


def test_top_share_group_that_fits_exactly_has_no_fraction():
    # K = 3: o grupo do topo (1 deal) e o seguinte (2 deals) cabem exatamente; o terceiro não entra.
    score = np.array([3, 2, 2, 1, 1, 1], dtype=float)
    gain = np.array([4, 2, 2, 8, 8, 8], dtype=float)
    assert top_share(score, gain, 0.5) == pytest.approx(8 / 32)


def test_top_share_matches_exact_expectation_over_random_tiebreaks():
    # Confere o tratamento fracionário contra a média exata de TODOS os desempates possíveis.
    # n = 6 e frac = 1/3 dão K = 2 inteiro, então o valor esperado é uma média simples.
    rng = np.random.default_rng(123)
    for _ in range(15):
        score = rng.integers(0, 3, size=6).astype(float)  # poucos valores: muitos empates
        gain = rng.integers(0, 10, size=6).astype(float)
        if gain.sum() == 0:
            continue
        shares = []
        for perm in itertools.permutations(range(6)):
            order = np.lexsort((np.array(perm), -score))  # score decrescente, desempate pela permutação
            shares.append(gain[order[:2]].sum() / gain.sum())
        assert top_share(score, gain, 1 / 3) == pytest.approx(np.mean(shares))


def test_top_share_full_population_is_one():
    assert top_share([3, 1, 2, 2], [1, 2, 3, 4], 1.0) == pytest.approx(1.0)


def test_top_share_zero_total_gain_is_nan():
    assert math.isnan(top_share([3, 2, 1, 0], [0, 0, 0, 0], 0.5))
    assert math.isnan(top_share([], [], 0.2))


# --- random_baseline -------------------------------------------------------------------------
def _synthetic(n=2000, seed=11):
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < 0.4).astype(float)
    gain = y * rng.lognormal(mean=8.0, sigma=1.0, size=n)
    return gain, y


def test_random_baseline_revenue_near_frac():
    gain, y = _synthetic()
    out = random_baseline(gain, y, n_seeds=50)
    assert set(out) == {"auc", "capture", "revenue"}
    for metric in out.values():
        assert set(metric) == {"mean", "p5", "p95"}
        assert metric["p5"] <= metric["mean"] <= metric["p95"]
    assert out["revenue"]["mean"] == pytest.approx(0.20, abs=0.02)
    assert out["capture"]["mean"] == pytest.approx(0.20, abs=0.02)
    assert out["auc"]["mean"] == pytest.approx(0.50, abs=0.02)


def test_random_baseline_is_deterministic():
    gain, y = _synthetic(n=500)
    assert random_baseline(gain, y, n_seeds=20) == random_baseline(gain, y, n_seeds=20)


def test_random_baseline_uses_seeds_zero_to_n_minus_one():
    gain, y = _synthetic(n=300)
    expected = [top_share(np.random.default_rng(s).random(300), gain, 0.2) for s in range(5)]
    out = random_baseline(gain, y, n_seeds=5)
    assert out["revenue"]["mean"] == pytest.approx(np.mean(expected))
    assert out["revenue"]["p5"] == pytest.approx(np.percentile(expected, 5))
    assert out["revenue"]["p95"] == pytest.approx(np.percentile(expected, 95))


# --- bootstrap_diff --------------------------------------------------------------------------
def test_bootstrap_diff_same_scores_is_zero():
    gain, _ = _synthetic(n=400)
    score = np.random.default_rng(3).random(400)
    out = bootstrap_diff(score, score, gain, reps=100)
    assert out["diff"] == 0.0
    assert out["ci_low"] == 0.0
    assert out["ci_high"] == 0.0


def test_bootstrap_diff_is_deterministic_and_seed_dependent():
    gain, _ = _synthetic(n=400)
    rng = np.random.default_rng(5)
    a, b = rng.random(400), rng.random(400)
    first = bootstrap_diff(a, b, gain, reps=200, seed=0)
    assert first == bootstrap_diff(a, b, gain, reps=200, seed=0)
    assert first["diff"] == bootstrap_diff(a, b, gain, reps=200, seed=1)["diff"]  # observada não depende da semente
    assert first["ci_low"] != bootstrap_diff(a, b, gain, reps=200, seed=1)["ci_low"]


def test_bootstrap_diff_detects_clearly_better_method():
    gain, _ = _synthetic(n=600)
    noise = np.random.default_rng(9).random(600)
    good = gain + 0.1 * noise  # ordena pela própria receita (oráculo)
    bad = -good
    out = bootstrap_diff(good, bad, gain, reps=200)
    assert out["diff"] == pytest.approx(top_share(good, gain) - top_share(bad, gain))
    assert out["ci_low"] <= out["diff"] <= out["ci_high"]
    assert out["ci_low"] > 0.5
    assert out["n_valid"] == 200


def test_bootstrap_diff_length_mismatch_raises():
    with pytest.raises(ValueError):
        bootstrap_diff([1, 2, 3], [1, 2, 3], [1, 2], reps=5)
    with pytest.raises(ValueError):
        bootstrap_diff([1, 2, 3], [1, 2], [1, 2, 3], reps=5)


# --- brier e log_loss -----------------------------------------------------------------------
def test_brier_known_values():
    assert brier([1, 0], [1, 0]) == 0.0
    assert brier([0.5, 0.5, 0.5, 0.5], [1, 0, 1, 0]) == pytest.approx(0.25)
    assert brier([1.0, 0.0, 0.5], [1, 0, 1]) == pytest.approx(0.25 / 3)
    assert brier([0.0, 1.0], [1, 0]) == 1.0  # pior caso


def test_brier_of_constant_base_rate():
    y = np.array([1, 1, 0, 0, 0])
    base = y.mean()  # 0,4
    assert brier(np.full(5, base), y) == pytest.approx(base * (1 - base))


def test_log_loss_known_values():
    assert log_loss([0.5, 0.5], [1, 0]) == pytest.approx(math.log(2))
    assert log_loss([0.9, 0.1], [1, 0]) == pytest.approx(-math.log(0.9))
    assert log_loss([0.8, 0.4], [1, 0]) == pytest.approx(-(math.log(0.8) + math.log(0.6)) / 2)


def test_log_loss_clips_extreme_probabilities():
    wrong = log_loss([0.0, 1.0], [1, 0])
    assert math.isfinite(wrong)
    assert wrong == pytest.approx(-math.log(1e-12))
    assert log_loss([1.0, 0.0], [1, 0]) == pytest.approx(1e-12, abs=1e-15)


# --- beats -----------------------------------------------------------------------------------
def test_beats_tie_within_tolerance_does_not_beat():
    assert beats(0.605, [0.60]) is False
    assert beats(0.60, [0.60]) is False
    assert beats(0.50, [0.60]) is False
    # diferença de exatamente 0,01: 0,61 - 0,60 vale 0,010000000000000009 em float, e é empate
    assert beats(0.61, [0.60]) is False
    assert beats(0.49, [0.48]) is False


def test_beats_above_tolerance_beats():
    assert beats(0.62, [0.60]) is True
    assert beats(0.611, [0.60]) is True


def test_beats_needs_to_beat_every_other():
    assert beats(0.65, [0.30, 0.47, 0.20]) is True
    assert beats(0.65, [0.30, 0.64, 0.20]) is False  # empata com um deles
    assert beats(0.65, [0.30, 0.70, 0.20]) is False  # perde para um deles


def test_beats_custom_tolerance_and_nan():
    assert beats(0.62, [0.60], tie_tol=0.05) is False
    assert beats(0.70, [0.60], tie_tol=0.05) is True
    assert beats(float("nan"), [0.1]) is False
    assert beats(0.9, [0.1, float("nan")]) is False


def test_beats_empty_others_raises():
    with pytest.raises(ValueError):
        beats(0.9, [])


def test_module_exports_expected_functions():
    for name in ("auc", "top_share", "random_baseline", "bootstrap_diff", "brier", "log_loss", "beats"):
        assert callable(getattr(validate, name))


# =============================================================================================
# Backtest (bloco 3b)
# =============================================================================================
import json  # noqa: E402
import pandas as pd  # noqa: E402

from scorer import clean, config  # noqa: E402
from scorer.score import fit_logistic  # noqa: E402


# --- PAVA e curva em faixas --------------------------------------------------------------------
def test_pava_nonincreasing_pools_violations_with_weights():
    out = validate.pava_nonincreasing([0.5, 0.6, 0.4, 0.2], [1, 1, 1, 1])
    assert out == pytest.approx([0.55, 0.55, 0.4, 0.2])
    weighted = validate.pava_nonincreasing([0.2, 0.6], [3, 1])  # sobe: funde pela média ponderada
    assert weighted == pytest.approx([0.3, 0.3])


def test_pava_output_is_always_nonincreasing():
    rng = np.random.default_rng(1)
    out = validate.pava_nonincreasing(rng.random(40), rng.integers(1, 50, 40))
    assert np.all(np.diff(out) <= 1e-12)


def test_binned_curve_shrinks_small_bins_and_never_increases():
    age = np.array([1.0] * 100 + [20.0] * 4 + [40.0] * 100)
    y = np.array([1.0] * 50 + [0.0] * 50 + [1.0] * 4 + [0.0] * 100)
    curve = validate.fit_binned_curve(age, y, width=15, alpha=20)
    base = y.mean()
    assert curve.counts == (100, 4, 100)
    # a faixa de 4 casos (todos ganhos) fica puxada para a taxa média, não vira 100%
    first = (50 + 20 * base) / (100 + 20)
    assert curve.rates[0] == pytest.approx(first)
    assert list(curve.rates) == sorted(curve.rates, reverse=True)
    grid = np.arange(0, 400)
    assert np.all(np.diff(curve.p_win(grid)) <= 1e-12)
    assert 0 < curve.p_win(10_000) < 1
    assert curve.p_win(7.5) == pytest.approx(curve.rates[0])


def test_binned_curve_skips_empty_bins():
    curve = validate.fit_binned_curve([1, 2, 100, 101], [1, 0, 0, 0], width=15, alpha=1)
    assert curve.midpoints == (7.5, 97.5)


# --- logística com penalização seletiva ---------------------------------------------------------
def test_masked_logistic_matches_fit_logistic_when_penalties_coincide():
    rng = np.random.default_rng(0)
    X = np.column_stack([np.ones(300), rng.normal(size=300), rng.normal(size=300)])
    y = (rng.random(300) < 1 / (1 + np.exp(-(0.3 + X[:, 1])))).astype(float)
    a = fit_logistic(X, y, l2=1.0)
    b = validate.fit_logistic_masked(X, y, 1.0, penalized=[1, 2])
    assert b.coef == pytest.approx(a.coef, abs=1e-6)
    assert b.nll == pytest.approx(a.nll, abs=1e-6)
    c = validate.fit_logistic_masked(X, y, 1.0, penalized=[2])  # coluna 1 livre: coeficiente maior
    assert abs(c.coef[1]) > abs(b.coef[1])


# --- critério ------------------------------------------------------------------------------------
def _cut(cut, score, valor, rec, rnd, p95):
    mk = lambda r: {"auc": 0.5, "ganhos_top20": 0.2, "receita_top20": r}
    return {"cut": cut, "metodos": {"score": mk(score), "valor": mk(valor), "recencia": mk(rec),
                                    "aleatorio": {**mk(rnd), "p95": {"receita_top20": p95}}}}


def test_check_criterion_requires_every_cut_and_every_baseline():
    good = [_cut(f"c{i}", 0.60, 0.49, 0.28, 0.20, 0.24) for i in range(4)]
    assert validate.check_criterion(good)["passed"] is True
    worse = good[:3] + [_cut("c3", 0.60, 0.49, 0.62, 0.20, 0.24)]  # a recência vence em um corte
    result = validate.check_criterion(worse)
    assert result["passed"] is False
    assert [r["passa"] for r in result["per_cut"]] == [True, True, True, False]
    assert result["per_cut"][3]["bate_recencia"] is False


def test_check_criterion_tie_of_one_point_does_not_win():
    tie = [_cut("c", 0.61, 0.60, 0.30, 0.20, 0.24)]
    assert validate.check_criterion(tie)["passed"] is False
    assert validate.check_criterion([_cut("c", 0.62, 0.60, 0.30, 0.20, 0.24)])["passed"] is True
    p95 = [_cut("c", 0.60, 0.40, 0.30, 0.20, 0.595)]  # só empata com o p95 do aleatório
    assert validate.check_criterion(p95)["passed"] is False


def test_check_criterion_empty_is_not_passed():
    assert validate.check_criterion([])["passed"] is False


def test_py_converts_numpy_and_nan_for_json():
    out = validate._py({"a": np.float64("nan"), "b": np.int64(3), "c": (np.bool_(True), 2.5), "d": pd.NA})
    assert out == {"a": None, "b": 3, "c": [True, 2.5], "d": None}
    json.dumps(out, allow_nan=False)


# --- um corte com os dados reais -------------------------------------------------------------------
@pytest.fixture(scope="module")
def deals():
    return clean.load_deals()


@pytest.fixture(scope="module")
def cut_0630(deals):
    return validate._build_cut(deals, "2017-06-30")


def test_cut_population_is_engaging_open_at_T_with_real_outcome(cut_0630):
    pop = cut_0630.pop
    assert (pop["deal_stage"] == "Engaging").all() and (pop["age_days"] >= 0).all()
    assert (pop["engage_date"] <= pd.Timestamp("2017-06-30")).all()
    assert pop["close_date"].isna().all()  # a visão em T não conhece o fechamento
    assert (pop.loc[pop["y"] == 0, "gain"] == 0).all() and (pop.loc[pop["y"] == 1, "gain"] > 0).all()
    assert (pop["y_h"] <= pop["y"]).all()
    assert (pop["resolved"] | (pop["y"] == 0)).all()  # ganho implica resolvido


def test_evaluate_cut_has_all_methods_and_is_deterministic(deals):
    a = validate.evaluate_cut(deals, "2017-06-30")
    b = validate.evaluate_cut(deals, "2017-06-30")
    assert json.dumps(validate._py(a), sort_keys=True) == json.dumps(validate._py(b), sort_keys=True)
    assert set(a["metodos"]) == {"score", "p_only", "valor", "recencia", "aleatorio"}
    assert 0.15 < a["metodos"]["aleatorio"]["receita_top20"] < 0.25
    assert set(a["categorias"]) == {"Foque", "Reative", "Limpe"}
    assert sum(c["n"] for c in a["categorias"].values()) == a["populacao"]["n"]


def test_binned_cut_uses_the_same_population_and_baselines(deals, cut_0630):
    binned = validate._evaluate(validate._build_cut(deals, "2017-06-30", kind="binned"))
    plateau = validate._evaluate(cut_0630)
    for method in ("valor", "recencia"):
        assert binned["metodos"][method] == plateau["metodos"][method]
    assert binned["populacao"] == plateau["populacao"]
    assert binned["curva"] == "binned"


# --- o JSON gerado ------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def backtest():
    assert config.BACKTEST_JSON.exists(), "rode `python -m scorer.validate` antes"
    with open(config.BACKTEST_JSON, encoding="utf-8") as handle:
        return json.load(handle)


def test_json_has_four_cuts_and_all_top_level_keys(backtest):
    for key in ("config", "criterion", "headline", "cuts", "cuts_v1", "media_cortes", "media_cortes_v1", "intra_foque", "diagnostico_fases",
                "sensibilidade_2017-02-28", "sensibilidade_pseudo_contagem", "auditoria", "atributos", "hoje", "hoje_v1"):
        assert key in backtest
    assert [c["cut"] for c in backtest["cuts"]] == config.BACKTEST_CUTS
    assert isinstance(backtest["criterion"]["passed"], bool)
    for cut in backtest["cuts"]:
        for key in ("modelo", "populacao", "metodos", "brier", "bootstrap", "categorias", "calibracao", "resolvidos", "foque_por_idade"):
            assert key in cut
        assert set(cut["metodos"]) == {"score", "p_only", "valor", "recencia", "aleatorio"}
        for method, values in cut["metodos"].items():
            assert set(validate.METRIC_KEYS) <= set(values)
    assert len(backtest["atributos"]) == 4 and len(backtest["auditoria"]["vazado"]) == 4
    assert set(backtest["hoje"]["categorias"]) == set(config.CATEGORIES)


def test_criterion_function_reproduces_the_stored_verdict(backtest):
    again = validate.check_criterion(backtest["cuts"])
    assert again["passed"] == backtest["criterion"]["passed"]
    assert again["per_cut"] == backtest["criterion"]["per_cut"]


def test_headline_is_the_mean_of_the_cuts(backtest):
    head = validate.headline_metrics(backtest)
    mean = lambda m: np.mean([c["metodos"][m]["receita_top20"] for c in backtest["cuts"]])
    assert head["n_cortes"] == 4
    assert head["receita_score"] == pytest.approx(mean("score"))
    assert head["receita_valor"] == pytest.approx(mean("valor"))
    assert head["receita_recencia"] == pytest.approx(mean("recencia"))


def test_attribute_rule_is_applied_as_pre_registered(backtest):
    for attr in backtest["atributos"]:
        ll = all(r["delta_log_loss"] < 0 for r in attr["por_corte"])
        rev = all(r["delta_receita_top20"] >= -1e-12 for r in attr["por_corte"])
        assert attr["entra"] == (ll and rev)


def test_leaked_audit_is_labeled_and_never_in_the_headline(backtest):
    assert all("VAZADO" in v["rotulo"] for v in backtest["auditoria"]["vazado"])
    assert backtest["headline"]["receita_score"] == pytest.approx(
        np.mean([c["metodos"]["score"]["receita_top20"] for c in backtest["cuts"]])
    )


def test_today_counts_match_the_facts(backtest):
    from scorer.facts import load_facts

    facts = load_facts()
    faixas = facts["idade_hoje"]["faixas"]
    hoje = backtest["hoje"]
    # a curva v1 (limite de Limpe = maior ciclo) reproduz os fatos; a v2 acrescenta ao Limpe o que a chance já tirou do jogo
    old = backtest["hoje_v1"]
    assert old["categorias"]["Limpe"]["n"] == faixas["acima_do_ciclo_maximo"]["n"]
    assert old["categorias"]["Limpe"]["valor_tabela"] == faixas["acima_do_ciclo_maximo"]["valor_tabela"]
    detail = hoje["limpe_detalhe"]
    assert detail["acima_do_maior_ciclo"]["n"] == faixas["acima_do_ciclo_maximo"]["n"]
    assert detail["acima_do_maior_ciclo"]["n"] + detail["so_pela_chance"]["n"] == hoje["categorias"]["Limpe"]["n"]
    assert hoje["categorias"]["Limpe"]["n"] >= faixas["acima_do_ciclo_maximo"]["n"]
    assert hoje["categorias"]["Qualifique"]["n"] == facts["prospecting"]["n"]
    # as faixas fixas do briefing batem com os fatos
    assert hoje["faixas_fixas_do_briefing"]["ate_90"] == faixas["ate_limite_fresco"]["n"]
    assert hoje["faixas_fixas_do_briefing"]["de_91_a_138"] == faixas["entre_limite_fresco_e_ciclo_maximo"]["n"]

def test_how_it_works_line_5_uses_the_headline_from_the_json(backtest, deals):
    from scorer import explain
    from scorer.fmt import fmt_pct
    from scorer.score import fit_model

    head = validate.headline_metrics(backtest)
    lines = explain.how_it_works(fit_model(deals, config.DEFAULT_REFERENCE_DATE), head)
    assert len(lines) == 5
    assert "Testado no passado em 4 datas" in lines[4]
    for key in ("receita_score", "receita_valor", "receita_recencia"):
        assert fmt_pct(head[key], 0) in lines[4]
    assert "Vendedor não entra no score." in lines[4]

# --- Correção após revisão do Rafael: curva v2, v1 ao lado, ordem dentro do Foque ---------------------


def test_v2_is_the_reported_curve_and_v1_sits_beside_it(backtest):
    assert all(c["curva"] == "v2" and c["modelo"]["versao"] == "v2" for c in backtest["cuts"])
    assert all(c["curva"] == "plateau" and c["modelo"]["versao"] == "v1" for c in backtest["cuts_v1"])
    crit = backtest["criterion"]
    assert crit["final_curve"] == "v2" and crit["post_backtest_change"] is True and set(crit["runs"]) == {"v1", "v2"}
    assert crit["passed"] == crit["runs"]["v2"]["passed"] and crit["v1_passed"] == crit["runs"]["v1"]["passed"]
    assert validate.check_criterion(backtest["cuts_v1"])["passed"] == crit["v1_passed"]
    for new, old in zip(backtest["cuts"], backtest["cuts_v1"]):
        for method in ("valor", "recencia"):  # mesmos deals e mesmos baselines nas duas curvas
            assert new["metodos"][method] == old["metodos"][method]
        assert new["populacao"] == old["populacao"]


def test_headline_is_the_v2_average(backtest):
    mean = np.mean([c["metodos"]["score"]["receita_top20"] for c in backtest["cuts"]])
    old = np.mean([c["metodos"]["score"]["receita_top20"] for c in backtest["cuts_v1"]])
    assert backtest["headline"]["receita_score"] == pytest.approx(mean)
    assert backtest["headline_v1"]["receita_score"] == pytest.approx(old)


def _toy_cut(ages, prices, y, p_fn):
    import types

    ages, prices, y = np.asarray(ages, float), np.asarray(prices, float), np.asarray(y)
    pop = pd.DataFrame({
        "opportunity_id": [f"D{i}" for i in range(len(ages))], "age_days": ages, "sales_price": prices, "y": y,
        "gain": y * prices,
    })
    return types.SimpleNamespace(T=pd.Timestamp("2017-09-30"), pop=pop, p_fn=p_fn)


def test_intra_foque_metric_uses_the_same_population_for_every_method():
    ages = [10, 20, 30, 95, 200]
    prices = [100, 100, 100, 100, 100]
    y = [1, 0, 0, 1, 0]  # o ganho de 95 dias fica fora da população (idade > 90)
    v2 = _toy_cut(ages, prices, y, lambda a: 1 - np.asarray(a) / 400)
    v1 = _toy_cut(ages, prices, y, lambda a: np.full(len(np.atleast_1d(a)), 0.5))
    out = validate._intra_foque(v1, v2)
    assert out["n"] == 3 and out["ganhos"] == 1 and out["receita_ganha"] == 100
    m = out["metodos"]
    assert m["score_v2"]["auc"] == 1.0 and m["score_v2"]["receita_top20"] == pytest.approx(0.6)  # K = 20% de 3 deals = 0,6 deal: o topo é o único ganho
    assert m["recencia"]["auc"] == 1.0
    assert m["score_v1"]["auc"] == 0.5 and m["valor"]["auc"] == 0.5  # empate total: nenhuma informação
    assert m["score_v1"]["receita_top20"] == pytest.approx(0.2) and m["valor"]["receita_top20"] == pytest.approx(0.2)
    assert set(m) == {"score_v2", "score_v1", "valor", "recencia", "aleatorio"}


def test_intra_foque_metric_ranks_by_expected_value_not_by_age_alone():
    ages = [5, 80]
    prices = [100, 10000]
    y = [0, 1]  # o deal velho e caro é o que ganha
    v2 = _toy_cut(ages, prices, y, lambda a: np.where(np.asarray(a) < 50, 0.5, 0.2))
    v1 = _toy_cut(ages, prices, y, lambda a: np.full(len(np.atleast_1d(a)), 0.5))
    out = validate._intra_foque(v1, v2)
    assert out["metodos"]["score_v2"]["auc"] == 1.0 and out["metodos"]["recencia"]["auc"] == 0.0


def test_intra_foque_in_the_json_covers_all_cuts_and_methods(backtest, deals):
    intra = backtest["intra_foque"]
    assert intra["idade_max"] == config.INTRA_FOQUE_MAX_AGE and len(intra["por_corte"]) == 4
    for c in intra["por_corte"]:
        pop = validate._build_cut(deals, c["cut"]).pop
        assert c["n"] == int((pop["age_days"] <= config.INTRA_FOQUE_MAX_AGE).sum())
        assert set(c["metodos"]) == {"score_v2", "score_v1", "valor", "recencia", "aleatorio"}
        assert all(set(v) == {"auc", "receita_top20"} for v in c["metodos"].values())
    for method, values in intra["media"].items():
        assert values["auc"] == pytest.approx(np.mean([c["metodos"][method]["auc"] for c in intra["por_corte"]]))


def test_diagnostic_by_phase_is_consistent(backtest):
    diag = backtest["diagnostico_fases"]
    groups = diag["grupos"]
    assert groups["fim_de_trimestre"]["fotos"] == ["2017-03-31", "2017-06-30", "2017-09-30"]
    assert groups["fim_de_trimestre"]["linhas"] + groups["meio_de_trimestre"]["linhas"] == groups["todas"]["linhas"]
    for i, band in enumerate(groups["todas"]["por_faixa"]):
        parts = [groups[g]["por_faixa"][i] for g in ("fim_de_trimestre", "meio_de_trimestre")]
        assert band["n"] == sum(p["n"] for p in parts) and band["ganhos"] == sum(p["ganhos"] for p in parts)
    first, last = groups["fim_de_trimestre"]["por_faixa"][0], groups["fim_de_trimestre"]["por_faixa"][2]
    assert first["taxa_ganho_90d"] > 0.4 and last["taxa_ganho_90d"] < 0.2  # o padrão de fim de trimestre, que o platô escondia
    assert sum(diag["fases"][p]["linhas"] for p in "123") == groups["todas"]["linhas"]
