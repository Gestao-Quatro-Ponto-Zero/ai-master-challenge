"""Testes do build: contrato do data.js, desfechos, pessoas, briefs, CSVs e determinismo.

A maior parte usa `build.build_data` (sem disco) com o backtest real; as contagens de cada lista são
conferidas também por uma conta independente (`score_deals` direto). O teste do build completo
(`python -m scorer.build` numa pasta temporária) está no fim.
"""

import copy
import json
import re

import shutil

import pandas as pd
import pytest

from scorer import build, clean, config, fmt, score, validate

REF = config.DEFAULT_REFERENCE_DATE
CATS = config.CATEGORIES


@pytest.fixture(scope="module")
def deals():
    return clean.load_deals()


@pytest.fixture(scope="module")
def teams():
    return clean.load_raw(config.RAW_DIR)["sales_teams"]


def _counts(deals, T, prospecting):
    model = score.fit_model(deals, T)
    scored = score.score_deals(deals, T, model, include_prospecting=prospecting)
    return scored.groupby("category")


@pytest.fixture(scope="module")
def metrics(deals):
    """O backtest real (cerca de 8 s), sem gravar nada em disco."""
    return validate.run_backtest(deals, write=False)


@pytest.fixture(scope="module")
def data(deals, teams, metrics):
    return build.build_data(deals, teams, metrics, REF)


# --- contrato ---------------------------------------------------------------------------------
def test_data_has_the_contract_top_level_and_snapshot_order(data):
    assert list(data) == ["meta", "people", "snapshots", "backtest"]
    dates = [s["date"] for s in data["snapshots"]]
    assert dates == [REF, "2017-09-30", "2017-06-30"]
    assert [s["mode"] for s in data["snapshots"]] == ["hoje", "teste", "teste"]
    assert data["snapshots"][0]["label"] == "Hoje — 31/12/2017"
    assert data["snapshots"][1]["label"] == "Teste: 30/09/2017"
    assert data["meta"]["generated_by"] == f"python -m scorer.build --reference-date {REF}"


def test_contract_invariants_hold_and_are_enforced(data):
    build.check_contract(data)  # já roda dentro de build_data; aqui como regressão explícita
    broken = copy.deepcopy(data)
    broken["snapshots"][0]["summary"]["Foque"]["n"] += 1
    with pytest.raises(AssertionError):
        build.check_contract(broken)
    broken = copy.deepcopy(data)
    broken["snapshots"][1]["deals"][0]["outcome"] = None
    with pytest.raises(AssertionError):
        build.check_contract(broken)


def test_today_matches_the_metrics_and_mismatches_are_caught(data, metrics):
    build.check_against_metrics(data, metrics)
    wrong = copy.deepcopy(metrics)
    wrong["hoje"]["categorias"]["Limpe"]["n"] += 1
    with pytest.raises(AssertionError, match="hoje/Limpe"):
        build.check_against_metrics(data, wrong)
    wrong = copy.deepcopy(metrics)
    wrong["cuts"][3]["categorias"]["Foque"]["n"] += 1  # corte de 30/09
    with pytest.raises(AssertionError, match="2017-09-30/Foque"):
        build.check_against_metrics(data, wrong)


def test_list_sizes_match_an_independent_count(data, deals):
    for snap, prospecting in zip(data["snapshots"], (True, False, False)):
        size = _counts(deals, snap["date"], prospecting).size()
        assert {c: snap["summary"][c]["n"] for c in CATS if size.get(c, 0)} == {c: int(size[c]) for c in size.index}


def test_today_lists_have_the_expected_sizes_and_order(data):
    today = data["snapshots"][0]
    assert sum(today["summary"][c]["n"] for c in CATS) == len(today["deals"])
    assert today["summary"]["Qualifique"]["n"] == 500 and today["summary"]["Qualifique"]["valor_esperado"] is None
    cats = [d["cat"] for d in today["deals"]]
    assert cats == sorted(cats, key=CATS.index)
    foque = [d["ev"] for d in today["deals"] if d["cat"] == "Foque"]
    assert foque == sorted(foque, reverse=True)
    limpe = [d["price"] for d in today["deals"] if d["cat"] == "Limpe"]
    assert limpe == sorted(limpe, reverse=True)


def test_test_snapshots_have_outcomes_and_no_qualifique(data):
    for snap in data["snapshots"][1:]:
        assert snap["summary"]["Qualifique"] == {"n": 0, "valor_tabela": 0, "valor_esperado": None}
        assert all(d["outcome"]["status"] in ("Ganho", "Perdido", "Aberto") for d in snap["deals"])
        for cat in ("Foque", "Reative", "Limpe"):
            summary = snap["outcome_summary"][cat]
            won = [d["outcome"] for d in snap["deals"] if d["cat"] == cat and d["outcome"]["status"] == "Ganho"]
            assert summary["pct_ganhos"] == len(won) / summary["n"]
            assert summary["receita_ganha"] == sum(o["close_value"] for o in won)


def test_no_nan_and_the_json_is_plain(data):
    json.dumps(data, allow_nan=False)  # NaN/Infinity levantariam ValueError
    sentences = [s for snap in data["snapshots"] for d in snap["deals"] for s in d["why"]]
    assert not any(re.search(r"\b(nan|nat|none|null)\b", s, re.I) for s in sentences)
    first = data["snapshots"][0]["deals"][0]
    assert isinstance(first["price"], int) and isinstance(first["age"], int) and isinstance(first["score"], int)


def test_model_section_carries_the_new_limits_and_the_deals_follow_them(data):
    for snap in data["snapshots"]:
        m = snap["model"]
        assert m["version"] == "v2" and m["limpe_rule"] in ("chance", "ciclo") and m["limpe_min_chance"] == config.LIMPE_MIN_CHANCE
        assert m["knot_days"] <= m["limpe_after_days"] and m["max_won_cycle_days"] >= m["knot_days"]
        for d in snap["deals"]:
            if d["cat"] == "Foque":
                assert d["age"] <= m["knot_days"] and d["days_to_knot"] == m["knot_days"] - d["age"]
            elif d["cat"] == "Reative":
                assert m["knot_days"] < d["age"] <= m["limpe_after_days"]
            elif d["cat"] == "Limpe":
                assert d["age"] > m["limpe_after_days"]
        foque = [d["p"] for d in snap["deals"] if d["cat"] == "Foque"]
        assert min(foque) >= config.FOQUE_HALF_FRACTION * m["p_fresh"] - 1e-12
        assert all(d["p"] < config.LIMPE_MIN_CHANCE for d in snap["deals"] if d["cat"] == "Limpe" and d["age"] <= m["max_won_cycle_days"])


def test_every_scored_card_opens_with_the_comparison_sentence(data):
    for snap in data["snapshots"]:
        for d in snap["deals"]:
            if d["cat"] != "Qualifique":
                assert re.fullmatch(r"Deals com [\d.]+ dias? fecharam .+ das vezes(; os novos, \d+%|, o mesmo que os novos)\.", d["why"][0]), d["why"][0]


def test_the_model_of_each_snapshot_only_knows_its_own_date(data):
    for snap in data["snapshots"]:
        assert snap["model"]["as_of_date"] == snap["date"]
        assert max(snap["model"]["train_snapshots"]) <= (pd.Timestamp(snap["date"]) - pd.Timedelta(days=config.HORIZON_DAYS)).strftime("%Y-%m-%d")
    assert data["snapshots"][2]["model"]["train_snapshots"] == ["2017-03-31"]


# --- backtest ---------------------------------------------------------------------------------
def test_backtest_section_rows_and_texts(data, metrics):
    section = data["backtest"]
    assert [m["key"] for m in section["metrics"]] == ["receita_top20", "ganhos_top20", "auc"]
    assert "20%" in section["metrics"][0]["label"] and "métrica principal" in section["metrics"][0]["label"]
    cuts = [r["cut"] for r in section["rows"]]
    assert cuts == [c for cut in config.BACKTEST_CUTS + ["media"] for c in [cut] * 5]
    assert {r["method"] for r in section["rows"]} == set(build.ROW_METHODS)
    assert "p_only" not in {r["method"] for r in section["rows"]}
    assert section["rows"][-1]["cut_label"] == "Média dos 4 cortes"
    assert section["headline"] == build.headline_text(metrics["headline"])
    assert section["criterion_text"].startswith("Critério fixado antes do código: ")
    assert ("Resultado (curva v2): PASSOU." in section["criterion_text"]) == metrics["criterion"]["passed"]
    assert "mudança pós-backtest, pedida pelo Rafael depois de revisar a ferramenta" in section["criterion_text"]
    notes = " ".join(section["notes"])
    assert "A recência (mais recentes primeiro) tem AUC maior que o score" in notes
    assert "já resolvidos" in notes and "zumbis" in notes
    assert "a ordem dentro do Foque" in notes and "score v2" in notes and "otimista" not in notes
    assert "No Foque, " not in notes  # o aviso "Atenção" do Foque saiu: a correção está na curva


def test_backtest_rows_carry_the_metrics_json_values(data, metrics):
    rows = {(r["cut"], r["method"]): r for r in data["backtest"]["rows"]}
    for cut in metrics["cuts"]:
        for method in ("score", *build.BASELINE_METHODS):
            assert rows[(cut["cut"], method)]["receita_top20"] == cut["metodos"][method]["receita_top20"]
    assert rows[("media", "score")]["auc"] == metrics["media_cortes"]["metodos"]["score"]["auc"]
    for cut, old in zip(metrics["cuts"], metrics["cuts_v1"]):  # a curva antiga aparece ao lado, com os mesmos baselines
        assert rows[(cut["cut"], "score_v1")]["receita_top20"] == old["metodos"]["score"]["receita_top20"]
    assert rows[("media", "score_v1")]["receita_top20"] == metrics["media_cortes_v1"]["metodos"]["score"]["receita_top20"]
    assert rows[("media", "score_v1")]["method_label"].startswith("Score v1")


def test_headline_feeds_line_5_of_how_it_works(data, metrics):
    share = fmt.fmt_pct(metrics["headline"]["receita_score"], 0)
    for snap in data["snapshots"]:
        assert snap["how_it_works"][4].startswith(f"Testado no passado em 4 datas: o top 20% do score capturou {share}")


def test_failed_criterion_is_reported_as_such(metrics):
    failed = copy.deepcopy(metrics)
    failed["criterion"].update(passed=False, adjustment_applied=True)
    text = build.criterion_text(failed)
    assert "Resultado (curva v2): FALHOU." in text and "ajuste único" in text
    failed.pop("criterion")
    assert build.criterion_text(failed) is None


# --- desfechos (base de brinquedo) ------------------------------------------------------------
def test_outcomes_only_count_closings_up_to_the_reference_date():
    toy = pd.DataFrame(
        {
            "opportunity_id": ["W1", "W2", "L1", "E1"],
            "deal_stage": ["Won", "Won", "Lost", "Engaging"],
            "close_date": pd.to_datetime(["2017-08-01", "2017-12-01", "2017-09-01", None]),
            "close_value": [100.0, 200.0, 0.0, None],
        }
    )
    out = build.outcomes_by_id(toy, "2017-10-31")
    assert out["W1"] == {"status": "Ganho", "close_date": "2017-08-01", "close_value": 100}
    assert out["W2"] == {"status": "Aberto", "close_date": None, "close_value": None}  # fechou depois da referência
    assert out["L1"] == {"status": "Perdido", "close_date": "2017-09-01", "close_value": None}
    assert out["E1"]["status"] == "Aberto"


# --- pessoas ----------------------------------------------------------------------------------
def test_people_include_the_five_agents_without_deals(data):
    people = data["people"]
    agents = {a["name"]: a for a in people["agents"]}
    assert len(agents) == 35
    assert sum(not a["has_deals"] for a in agents.values()) == 5
    assert sum(a["has_deals"] and a["n_open"] == 0 for a in agents.values()) == 3
    assert sum(a["n_open"] > 0 for a in agents.values()) == 27
    assert sum(a["n_open"] for a in agents.values()) == len(data["snapshots"][0]["deals"])
    assert len(people["managers"]) == 6 and people["regions"] == ["Central", "East", "West"]


def test_people_section_on_a_toy_team():
    teams = pd.DataFrame({"sales_agent": ["B", "A", "C"], "manager": ["M1", "M1", "M2"], "regional_office": ["East", "East", "West"]})
    toy_deals = pd.DataFrame({"sales_agent": ["A", "A", "B"]})
    out = build.people_section(toy_deals, teams, [{"agent": "A"}, {"agent": "A"}])
    assert [a["name"] for a in out["agents"]] == ["A", "B", "C"]
    assert [(a["has_deals"], a["n_open"]) for a in out["agents"]] == [(True, 2), (True, 0), (False, 0)]
    assert out["managers"] == [{"name": "M1", "region": "East"}, {"name": "M2", "region": "West"}]


# --- saídas -----------------------------------------------------------------------------------
def test_data_js_parses_back_and_is_deterministic(tmp_path, deals, teams, metrics, data):
    first, second = tmp_path / "a.js", tmp_path / "b.js"
    size = build.write_data_js(first, data)
    build.write_data_js(second, build.build_data(deals, teams, metrics, REF))
    assert first.read_bytes() == second.read_bytes()
    text = first.read_text(encoding="utf-8")
    assert text.startswith("window.LEAD_DATA = ") and text.endswith(";\n")
    assert json.loads(text[len("window.LEAD_DATA = "):-2]) == data
    assert size == len(text.encode("utf-8")) < build.MAX_DATA_JS_BYTES


def test_snapshot_csvs_match_the_snapshots(tmp_path, data):
    for snap in data["snapshots"]:
        path = tmp_path / f"snapshot_{snap['date']}.csv"
        build.write_snapshot_csv(path, snap)
        table = pd.read_csv(path, encoding="utf-8", dtype=str, keep_default_na=False)
        assert len(table) == len(snap["deals"])
        assert list(table["id"]) == [d["id"] for d in snap["deals"]]
        assert list(table["categoria"]) == [d["cat"] for d in snap["deals"]]
        assert table["explicacao"].str.contains(" | ", regex=False).all()
        assert {"vendedor", "manager", "regiao", "categoria", "desfecho"} <= set(table.columns)
    assert (table["desfecho"] != "").all()  # o último é de teste: todo deal tem desfecho


def test_one_brief_per_agent_with_open_deals_and_an_index(tmp_path, data):
    data_today = data["snapshots"][0]["deals"]
    names = build.write_briefs(tmp_path, data)
    agents = data["people"]["agents"]
    with_deals = [a for a in agents if a["n_open"] > 0]
    assert sorted(names) == sorted(f"{build.slugify(a['name'])}.md" for a in with_deals) and len(names) == 27
    assert sorted(p.name for p in tmp_path.glob("*.md")) == sorted([*names, "README.md"])
    index = (tmp_path / "README.md").read_text(encoding="utf-8")
    for a in agents:
        assert (a["name"] in index) is True  # com brief (tabela) ou listado em "Sem brief"
    assert "Sem nenhum deal no CRM** (5)" in index and "Só com deals fechados** (3)" in index
    zane = (tmp_path / "zane-levy.md").read_text(encoding="utf-8")
    assert zane.startswith("# Brief de segunda-feira — Zane Levy — 31/12/2017")
    zane_deals = [d for d in data_today if d["agent"] == "Zane Levy"]
    for cat, noun in (("Foque", "focar"), ("Reative", "reativar")):
        n = sum(d["cat"] == cat for d in zane_deals)
        assert (f"## {min(n, build.BRIEF_TOP[cat])} para {noun}" in zane) if n else (f"Nenhum deal em {cat}" in zane)
    assert "## Limpe:" in zane
    assert "nan" not in zane.lower().split()


def test_brief_text_handles_empty_lists_and_singulars():
    agent = {"name": "Ana Souza", "manager": "M", "region": "East"}
    deal = {"cat": "Foque", "account": None, "product": "GTX Basic", "price": 550, "age": 1, "score": 10, "why": ["a", "b", "c"]}
    text = build.brief_text(agent, [deal], "2017-12-31")
    assert "foque em 1 deal." in text and "Conta não informada" in text and "aberto há 1 dia " in text
    assert "## 1 para focar" in text and "Nenhum deal em Reative" in text and "Nenhum deal em Limpe" in text


def test_slugify():
    assert build.slugify("Mei-Mei Johns") == "mei-mei-johns"
    assert build.slugify("José  D'Ávila") == "jose-d-avila"


# --- build completo ---------------------------------------------------------------------------
def _full_build(root):
    build.main(["--reference-date", REF, "--out-root", str(root)])
    return {p: p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file() and "raw" not in p.parts}


def test_full_build_in_a_tmp_root_is_reproducible_and_complete(tmp_path):
    root = tmp_path / "solution"
    shutil.copytree(config.RAW_DIR, root / "data" / "raw")
    first = _full_build(root)
    second = _full_build(root)
    assert first == second, "dois builds seguidos devem gerar bytes idênticos"

    text = (root / "app" / "data.js").read_text(encoding="utf-8")
    data = json.loads(text[len("window.LEAD_DATA = "):-2])
    metrics = json.loads((root / "data" / "processed" / "backtest_metrics.json").read_text(encoding="utf-8"))
    for cat, want in metrics["hoje"]["categorias"].items():
        assert data["snapshots"][0]["summary"][cat]["n"] == want["n"]
    for snap in data["snapshots"]:
        assert (root / "data" / "processed" / f"snapshot_{snap['date']}.csv").exists()
    with_open = [a for a in data["people"]["agents"] if a["n_open"] > 0]
    briefs = sorted(p.name for p in (root / "briefs").glob("*.md"))
    assert briefs == sorted([*(f"{build.slugify(a['name'])}.md" for a in with_open), "README.md"])
    assert (root / "data" / "processed" / "deals.csv").exists() and (root / "data" / "processed" / "facts.json").exists()


def test_a_rebuild_removes_stale_outputs(tmp_path):
    root = tmp_path / "solution"
    shutil.copytree(config.RAW_DIR, root / "data" / "raw")
    (root / "briefs").mkdir()
    (root / "briefs" / "velho.md").write_text("antigo", encoding="utf-8")
    (root / "data" / "processed").mkdir(parents=True)
    (root / "data" / "processed" / "snapshot_1999-01-01.csv").write_text("antigo", encoding="utf-8")
    build.main(["--reference-date", REF, "--out-root", str(root)])
    assert not (root / "briefs" / "velho.md").exists()
    assert not (root / "data" / "processed" / "snapshot_1999-01-01.csv").exists()
