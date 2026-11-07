"""Testes do motor. Rodam com `python -m pytest` ou, sem pytest, `python test_scoring.py`."""
import random
from datetime import date, timedelta

import scoring as s

REF = date(2017, 12, 31)


def _closed(cycle, won, start=date(2017, 1, 1)):
    return {"stage": "Won" if won else "Lost", "engage": start, "close": start + timedelta(days=cycle)}


def _open(stage="Engaging", age=None, price=1000, account="Acme"):
    return {"stage": stage, "engage": REF - timedelta(days=age) if age is not None else None,
            "price": price, "product": "X", "account": account}


# histórico sintético: tudo que passa de 60 dias fecha até o dia 100
TOY = s.fit_curve([_closed(5, False)] * 40 + [_closed(90, True)] * 50 + [_closed(100, False)] * 10, [])


def test_data_quality_fixes_applied():
    deals, _, products, accounts = s.load()
    assert all(d["product"] in products for d in deals), "join de produto quebrado"
    assert "technolgy" not in {a["sector"] for a in accounts.values()}
    assert sum(d["product"] == "GTX Pro" for d in deals) >= 1480


def test_curve_learns_from_survival():
    assert TOY.max_cycle == 100
    assert TOY.win[70] > TOY.base_rate            # quem sobrevive à fase de morte rápida ganha mais
    assert TOY.close_soon[70] == 1.0 and TOY.close_soon[10] == 0.0
    assert TOY.window_start <= 70 < 100


def test_zombie_has_no_value_and_goes_to_decide():
    r = s.score_open(_open(age=150), TOY, REF)
    assert r["bucket"] == "decidir" and r["ev"] == 0 and r["ev_soon"] == 0 and r["win_prob"] is None


def test_buckets_by_age_and_stage():
    assert s.score_open(_open(age=80), TOY, REF)["bucket"] == "fechar"
    assert s.score_open(_open(age=10), TOY, REF)["bucket"] == "avancar"
    p = s.score_open(_open(stage="Prospecting"), TOY, REF)
    assert p["bucket"] == "prospectar" and p["age"] is None


def test_window_outranks_young_deal_of_same_value():
    deals = [s.score_open(_open(age=80), TOY, REF), s.score_open(_open(age=10), TOY, REF)]
    assert deals[0]["score"] > deals[1]["score"]


def test_censoring_pulls_close_soon_down():
    # 40 deals reach age 89 and are STILL OPEN 30+ days later without closing.
    # Ignoring them (closed-only) would say close_soon[89] == 1.0; they prove
    # otherwise and must drag the estimate down.
    closed = [_closed(5, False)] * 20 + [_closed(90, True)] * 30
    blind = s.fit_curve(closed, [])
    honest = s.fit_curve(closed, open_ages=[130] * 40)  # observed 41+ days past age 89, never closed
    assert blind.close_soon[89] == 1.0
    assert honest.close_soon[89] < 0.5


def test_prospecting_and_zombie_have_no_score():
    zombie = s.score_open(_open(age=150), TOY, REF)
    prospect = s.score_open(_open(stage="Prospecting"), TOY, REF)
    assert zombie["score"] is None and prospect["score"] is None
    assert s.score_open(_open(age=80), TOY, REF)["score"] is not None


def test_every_deal_explains_itself_and_flags_missing_account():
    r = s.score_open(_open(age=80, account=None), TOY, REF)
    kinds = [x["kind"] for x in r["reasons"]]
    assert "+" in kinds and "!" in kinds and r["action"]


def _scored(**kwargs):
    d = _open(**kwargs)
    d.update(s.score_open(d, TOY, REF))  # como build() faz: mescla no dict original (mantém account etc.)
    return d


def test_suggest_decide_uses_staleness_not_missing_account():
    # TOY.max_cycle == 100. Sem histórico de outcome pra zumbi (ainda abertos):
    # a sugestão vem só de quanto além do maior ciclo. Conta vazia é falha de
    # cadastro, não sinal de deal morto: não pode, sozinha, mandar encerrar.
    barely_no_account = _scored(age=102, account=None)  # 2 dias além, sem conta
    barely_over = _scored(age=101, account="Acme")      # 1 dia além
    way_over = _scored(age=180, account="Acme")         # 80 dias além
    way_over_2 = _scored(age=190, account="Acme")
    stalled = [barely_no_account, barely_over, way_over, way_over_2]
    s.suggest_decide(stalled, TOY.max_cycle)
    assert barely_no_account["suggested_action"] == "confirmar"
    assert "cadastre a conta" in barely_no_account["action"].lower()
    assert barely_over["suggested_action"] == "confirmar"
    assert way_over_2["suggested_action"] == "encerrar"
    assert "1 dia " in barely_over["action"]  # singular, não "1 dias"


def test_close_window_actions_differ_by_phase():
    curve = s.fit_curve(*_real_curve_inputs())
    ages = [curve.window_start, curve.peak_age, curve.peak_age + s.PEAK_BAND + 1, curve.late_start]
    actions = [s.score_open(_open(age=a), curve, REF)["action"] for a in ages]
    assert len(set(actions)) == 4, actions


def _real_curve_inputs():
    deals, *_ = s.load()
    closed = [d for d in deals if d["stage"] in ("Won", "Lost")]
    open_ages = [(REF - d["engage"]).days for d in deals if d["stage"] in s.OPEN_STAGES and d["engage"]]
    return closed, open_ages


def test_tier_is_relative_to_best_possible_score():
    assert s.tier(28, 31) == "alta" and s.tier(15, 31) == "media" and s.tier(5, 31) == "baixa"
    assert s.tier(None, 31) is None


def test_account_context_changes_action_not_score():
    history = [{"account": "Acme", "stage": "Won"}] * 3
    a, b = _scored(age=80), _scored(age=80)
    score_before = a["score"]
    s.add_account_context([a, b], history + [a, b])
    assert a["score"] == score_before
    assert "cliente da casa" in a["action"] and "o outro deal aberto" in a["action"]


def test_cycle_test_separates_noise_from_signal():
    rng = random.Random(5)
    start = date(2017, 1, 1)
    mk = lambda g, c: {"g": g, "engage": start, "close": start + timedelta(days=c)}  # noqa: E731
    noise = [mk(i % 4, rng.randint(10, 90)) for i in range(800)]
    signal = [mk(i % 2, rng.randint(10, 50) + 40 * (i % 2)) for i in range(800)]
    assert s.cycle_dispersion_p(noise, lambda d: d["g"], random.Random(6))[1] > 0.05
    assert s.cycle_dispersion_p(signal, lambda d: d["g"], random.Random(6))[1] < 0.01


def test_suggest_decide_empty_list_does_nothing():
    s.suggest_decide([], 100)  # não deve levantar exceção


def test_significance_separates_noise_from_signal():
    rng = random.Random(1)
    noise = [{"stage": "Won" if rng.random() < 0.6 else "Lost", "g": i % 5} for i in range(1000)]
    signal = [{"stage": "Won" if (i % 2 == 0) == (rng.random() < 0.9) else "Lost", "g": i % 2} for i in range(1000)]
    assert s.dispersion_p(noise, lambda d: d["g"], random.Random(2))[1] > 0.05
    assert s.dispersion_p(signal, lambda d: d["g"], random.Random(2))[1] < 0.01


def test_continuous_split_finds_signal_not_noise():
    rng = random.Random(3)
    noise = [(rng.random(), 1 if rng.random() < 0.6 else 0) for _ in range(500)]
    signal = [(v, 1 if (v > 0.5) == (rng.random() < 0.9) else 0) for v in [rng.random() for _ in range(500)]]
    assert s.continuous_split_p(noise, random.Random(4))[1] > 0.05
    assert s.continuous_split_p(signal, random.Random(4))[1] < 0.01


def test_wilson_interval():
    low, high = s.wilson(60, 100)
    assert 0.49 < low < 0.6 < high < 0.7


def test_real_data_end_to_end():
    data = s.build()
    m = data["meta"]
    assert m["reference_date"] == "2017-12-31" and m["max_cycle"] == 138
    open_deals = [d for d in data["deals"] if d["stage"] in s.OPEN_STAGES]
    assert len(open_deals) == 2089
    assert all(d["reasons"] for d in open_deals)
    assert all(d["score"] is None or 0 <= d["score"] <= 100 for d in open_deals)
    # zumbi e prospecção não têm histórico confiável para um score de curto prazo
    assert all(d["score"] is None for d in open_deals if d["bucket"] in ("decidir", "prospectar"))
    assert all(d["score"] is not None for d in open_deals if d["bucket"] in ("fechar", "avancar"))
    assert sum(d["bucket"] == "decidir" for d in open_deals) == 1301  # idade >= 138: aberto aos 138 só fecharia depois, e isso nunca aconteceu
    decidir = [d for d in open_deals if d["bucket"] == "decidir"]
    assert all(d["suggested_action"] in ("encerrar", "confirmar") for d in decidir)
    assert all(d["suggested_action"] is None for d in open_deals if d["bucket"] != "decidir")
    used = {t["feature"] for t in data["significance"] if t["used"]}
    assert used == {"Idade do deal (fechou em até 15 dias ou não)"}
    # teste global de vendedor deu p≈0,3: nenhum vendedor pode ser rotulado como diferente
    assert {a["verdict"] for a in data["agents"]} <= {"dentro da média", "sem histórico"}
    # receita do time é fato, não estimativa: soma do close_value dos ganhos
    won_value = sum(d["close_value"] for d in data["deals"] if d["stage"] == "Won")
    assert sum(a["revenue_won"] for a in data["agents"]) == won_value
    # sem conta não manda encerrar sozinho: os dois lados da fila têm deals sem conta
    no_acc = {d["suggested_action"] for d in decidir if d["account"] is None}
    assert no_acc == {"encerrar", "confirmar"}


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
