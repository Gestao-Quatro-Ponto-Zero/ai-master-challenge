"""Testes de `explain.py`: frases curtas e sem jargão, frase principal comparativa, números do modelo do corte."""

import re

import pytest

from scorer import clean, config, explain, fmt, score

BANNED = ["nan", "none", "<na>", "nat", "logit", "probabilidade", "coeficiente", "sigmoid", "erro padrão"]


@pytest.fixture(scope="module")
def deals():
    return clean.load_deals()


@pytest.fixture(scope="module")
def today(deals):
    T = config.DEFAULT_REFERENCE_DATE
    model = score.fit_model(deals, T)
    return model, score.score_deals(deals, T, model, include_prospecting=True)


def model_with(knot=95, limpe=138, slope=-2.59, p_fresh_logit=-0.41) -> score.ScoreModel:
    """Modelo v1 (platô + queda) à mão."""
    curve = score.AgeCurve(knot, p_fresh_logit, slope, 0.33, 13100, ("2017-03-31", "2017-09-30"))
    return score.ScoreModel(curve, limpe, price_min=55.0, price_max=26768.0, as_of_date="2017-12-31", max_won_cycle_days=138)


def model_v2(p_fresh=0.50, knot=62, limpe=95, cycle=138) -> score.ScoreModel:
    """Modelo v2 à mão: o Limpe começa pela chance (95 < 138)."""
    binned = score.BinnedCurve((7.5, 22.5, 82.5), (p_fresh, p_fresh, 0.07), (100, 100, 100), 0.3)
    curve = score.PhaseCurve(binned, 3, knot, 5425, ("2017-03-31", "2017-06-30", "2017-09-30"))
    return score.ScoreModel(curve, limpe, price_min=55.0, price_max=26768.0, as_of_date="2017-12-31", max_won_cycle_days=cycle)


def row(category, **overrides) -> dict:
    base = {
        "category": category, "age_days": 60, "p_win": 0.40, "expected_value": 1928.4, "sales_price": 4821,
        "product": "GTX Pro", "has_account": True, "days_to_knot": 35, "days_to_limpe": 78,
        "sales_agent": "Fulana de Tal",
    }
    return {**base, **overrides}


def test_every_deal_today_gets_two_to_four_short_clean_sentences(today):
    model, scored = today
    assert set(scored["category"]) == set(config.CATEGORIES)
    for _, deal in scored.iterrows():
        sentences = explain.explain_deal(deal, model)
        assert 2 <= len(sentences) <= 4, (deal["opportunity_id"], sentences)
        text = " ".join(sentences).lower()
        assert not any(re.search(rf"\b{re.escape(word)}\b", text) for word in BANNED), sentences
        assert all(len(s) <= 160 and s.endswith(".") for s in sentences), sentences
        assert deal["sales_agent"].lower() not in text  # o vendedor nunca aparece como fator


def test_main_sentence_compares_the_deals_of_that_age_with_the_new_ones():
    sentences = explain.explain_deal(row("Reative", age_days=81, p_win=0.07), model_v2())
    assert sentences[0] == "Deals com 81 dias fecharam 7% das vezes; os novos, 50%."
    same = explain.explain_deal(row("Foque", age_days=3, p_win=0.499), model_v2())
    assert same[0] == "Deals com 3 dias fecharam 50% das vezes, o mesmo que os novos."
    tiny = explain.explain_deal(row("Limpe", age_days=300, p_win=0.001), model_v2())
    assert tiny[0] == "Deals com 300 dias fecharam menos de 1% das vezes; os novos, 50%."
    assert explain.explain_deal(row("Foque", age_days=1, p_win=0.4), model_v2())[0].startswith("Deals com 1 dia fecharam")


def test_the_comparison_numbers_equal_the_rounded_chances_of_the_model(today):
    model, scored = today
    for category in ("Foque", "Reative", "Limpe"):
        deal = scored[scored["category"] == category].iloc[3]
        first = explain.explain_deal(deal, model)[0]
        assert f"Deals com {fmt.fmt_int(deal['age_days'])}" in first
        shown = [int(n) for n in re.findall(r"(\d+)%", first.replace("menos de 1%", ""))]
        want = [round(100 * deal["p_win"]), round(100 * model.p_fresh)]
        if want[0] == 0:
            want = want[1:]  # "menos de 1%" não leva número
        assert shown == want, (category, first)


def test_sentences_have_the_expected_content_per_list():
    model = model_v2()
    foque = explain.explain_deal(row("Foque", p_win=0.4), model)
    assert foque[0] == "Deals com 60 dias fecharam 40% das vezes; os novos, 50%."
    assert foque[1] == "GTX Pro: valor de tabela US$ 4.821; valor esperado US$ 1.928."
    assert foque[2] == "Faltam 35 dias para a chance cair à metade da de um deal novo e o deal sair do Foque."

    reative = explain.explain_deal(row("Reative", age_days=81, p_win=0.07, expected_value=337.5, days_to_knot=None, days_to_limpe=14), model)
    assert reative[0].startswith("Deals com 81 dias fecharam 7%")
    assert reative[2] == "Depois de 95 dias aberto a chance de ganho cai abaixo de 2% — faltam 14 dias. Fale com o cliente esta semana."
    by_cycle = explain.explain_deal(row("Reative", age_days=110, p_win=0.2, days_to_limpe=28), model_v2(limpe=138))
    assert "Depois de 138 dias aberto nenhum deal foi ganho" in by_cycle[2] and "faltam 28 dias" in by_cycle[2]

    limpe = explain.explain_deal(row("Limpe", age_days=300, p_win=1e-9, days_to_knot=None, days_to_limpe=None), model)
    assert limpe[0].startswith("Deals com 300 dias fecharam menos de 1%")
    assert limpe[2] == "São US$ 4.821 inflando o pipeline (nenhum deal foi ganho com mais de 138 dias)."
    assert "Pergunte ao cliente" in limpe[1] and "marque Lost" in limpe[1] and "Reative ou Foque" in limpe[1]
    by_chance = explain.explain_deal(row("Limpe", age_days=120, p_win=0.004, days_to_knot=None, days_to_limpe=None), model)
    assert by_chance[2] == "São US$ 4.821 inflando o pipeline (a chance cai abaixo de 2% depois de 95 dias)."

    qualifique = explain.explain_deal(row("Qualifique", age_days=None, p_win=None, expected_value=None), model)
    assert len(qualifique) == 2 and "Prospecting" in qualifique[0] and "US$ 4.821" in qualifique[1]


def test_missing_account_adds_exactly_one_hygiene_sentence():
    model = model_v2()
    for category in config.CATEGORIES:
        with_account = explain.explain_deal(row(category), model)
        without = explain.explain_deal(row(category, has_account=False), model)
        assert without[:-1] == with_account and len(without) == len(with_account) + 1
        assert without[-1].startswith("Conta não informada no CRM — preencha; isso não muda")
        assert all("Conta não informada" not in s for s in with_account)
        assert len(without) <= 4
    assert explain.explain_deal(row("Foque", has_account=False), model)[-1] == explain.NO_ACCOUNT_SENTENCE


def test_singular_and_last_day_wording():
    model = model_v2()
    assert "Falta 1 dia para a chance cair" in explain.explain_deal(row("Foque", days_to_knot=1), model)[2]
    assert "último dia no Foque" in explain.explain_deal(row("Foque", days_to_knot=0), model)[2]
    assert "falta 1 dia" in explain.explain_deal(row("Reative", days_to_limpe=1), model)[2]
    assert "último dia" in explain.explain_deal(row("Reative", days_to_limpe=0), model)[2]
    assert explain.explain_deal(row("Limpe", age_days=1, p_win=0.4), model)[0].startswith("Deals com 1 dia ")


def test_a_chance_that_rounds_to_zero_is_shown_as_less_than_one_percent():
    sentences = explain.explain_deal(row("Reative", p_win=0.002), model_v2())
    assert sentences[0].startswith("Deals com 60 dias fecharam menos de 1% das vezes") and "fecharam 0%" not in sentences[0]


def test_explanation_uses_the_cut_model_not_a_global_one(deals):
    models = {T: score.fit_model(deals, T) for T in ("2017-06-30", "2017-09-30")}
    assert models["2017-06-30"].knot_days != models["2017-09-30"].knot_days
    for T, model in models.items():
        scored = score.score_deals(deals, T, model)
        foque = scored[(scored["category"] == "Foque") & (scored["days_to_knot"] > 0)]
        deal = foque.iloc[0]
        sentences = explain.explain_deal(deal, model)
        assert f"{round(100 * deal['p_win'])}%" in sentences[0] and f"os novos, {round(100 * model.p_fresh)}%" in sentences[0]
        assert f"{int(deal['days_to_knot'])} dia" in sentences[2]
        lines = explain.how_it_works(model)
        assert f"Foque: até {model.knot_days} dias de idade" in lines[3]
        assert fmt.fmt_date(model.curve.train_snapshots[0]) in lines[0]


def test_how_it_works_has_five_lines_with_the_model_numbers(today):
    model, _ = today
    lines = explain.how_it_works(model)
    assert len(lines) == 5
    assert "3 fotos mensais" in lines[0] and "31/03/2017 a 30/09/2017" in lines[0]
    assert f"{fmt.fmt_int(model.curve.train_rows)} casos" in lines[0] and "mesmo ponto do trimestre" in lines[0]
    assert "desde o primeiro dia" in lines[1] and f"{round(100 * model.p_fresh)}% de chance" in lines[1]
    for age in config.EXPLAIN_CURVE_AGES:
        assert f"com {age} dias, " in lines[1]
    assert "chance × preço de tabela" in lines[2] and "487 vezes" in lines[2]
    assert f"Foque: até {model.knot_days} dias" in lines[3] and f"Limpe: acima de {model.limpe_after_days} dias" in lines[3]
    assert "Vendedor não entra no score." in lines[4] and "ainda não foi rodado" in lines[4]
    assert not any(word in " ".join(lines).lower() for word in BANNED)


def test_how_it_works_describes_the_new_curve_and_not_the_plateau(today):
    model, _ = today
    text = " ".join(explain.how_it_works(model))
    assert "se mantém" not in text and "joelho" not in text.lower() and "platô" not in text.lower()
    assert "metade da de um deal novo" in text and "abaixo de 2%" in text


def test_how_it_works_fills_the_last_line_with_the_backtest_average(today):
    model, _ = today
    metrics = {"n_cortes": 4, "receita_score": 0.612, "receita_valor": 0.481, "receita_recencia": 0.298}
    last = explain.how_it_works(model, metrics)[4]
    assert last == (
        "Testado no passado em 4 datas: o top 20% do score capturou 61% da receita ganha depois, contra 48% "
        "ordenando por valor e 30% pelos mais recentes. Vendedor não entra no score."
    )


def test_how_it_works_for_the_v1_curve_and_its_degenerate_cases():
    flat = explain.how_it_works(model_with(slope=0.0))
    assert "não muda com a idade" in flat[1]
    immediate = explain.how_it_works(model_with(knot=0))
    assert "desde o primeiro dia" in immediate[1]
    no_reative = explain.how_it_works(model_with(knot=138, limpe=138))
    assert "Reative: nenhum." in no_reative[3]
    plateau = explain.how_it_works(model_with())
    assert "se mantém até 95 dias" in plateau[1] and "mais do que qualquer deal já ganho" in plateau[3]


def test_how_it_works_records_the_fallback_when_the_phase_had_no_photo():
    binned = score.BinnedCurve((7.5,), (0.5,), (100,), 0.3)
    curve = score.PhaseCurve(binned, 2, 62, 100, ("2017-04-30",), fallback=True)
    model = score.ScoreModel(curve, 95, 55.0, 26768.0, "2017-07-31", max_won_cycle_days=138)
    assert "usei todas as fotos" in explain.how_it_works(model)[0]
