"""Build do zero do Lead Scorer: CSVs brutos -> `app/data.js`, snapshots CSV e briefs por vendedor.

Uso: `python -m scorer.build --reference-date 2017-12-31 [--out-root DIR]`.

Sequência (tudo é regerado, nada é reaproveitado de uma execução anterior):
apaga as saídas -> `clean` (deals.csv e facts.json) -> `validate.run_backtest` (backtest_metrics.json)
-> snapshots (hoje + cortes de teste da UI) -> CSVs -> data.js -> briefs -> `docs.inject`.

O contrato do `data.js` está em `app/data-contract.md`; `check_contract` o confere com `assert`.
As funções deste módulo são puras (DataFrame/dict entram, dict/texto saem); só `write_*`, `clear_outputs`
e `main` tocam o disco. Determinístico: sem timestamp, ordem estável, JSON compacto.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import clean, config, docs, explain, fmt, score, validate

TODAY, TEST = "hoje", "teste"
CATS = config.CATEGORIES
SCORED_CATS = CATS[:3]  # Foque, Reative, Limpe: as listas que têm score e desfecho no modo teste
ROW_METHODS = ("score", "score_v1", "valor", "recencia", "aleatorio")  # métodos de `backtest.rows[].method`, na ordem de exibição
BASELINE_METHODS = ("valor", "recencia", "aleatorio")  # os que o critério pré-registrado compara com o score
AUC_RANDOM = 0.5  # AUC de um sorteio (só para o rótulo da tabela)
MAX_DATA_JS_BYTES = 4 * 1024 * 1024  # meta do contrato
BRIEF_TOP = {"Foque": 3, "Reative": 3, "Limpe": 5, "Qualifique": 3}  # quantos deals cada lista mostra no brief


# =============================================================================================
# Caminhos
# =============================================================================================
@dataclass(frozen=True)
class Paths:
    """Pastas de entrada e saída a partir de uma raiz (`solution/` por padrão)."""

    root: Path

    @property
    def raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def processed(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def data_js(self) -> Path:
        return self.root / "app" / "data.js"

    @property
    def briefs(self) -> Path:
        return self.root / "briefs"

    def snapshot_csv(self, date: str) -> Path:
        return self.processed / f"snapshot_{date}.csv"

    @property
    def deals_csv(self) -> Path:
        return self.processed / "deals.csv"

    @property
    def backtest_json(self) -> Path:
        return self.processed / "backtest_metrics.json"


# =============================================================================================
# Valores Python puros (nada de NaN, NaT, pd.NA ou tipos numpy no JSON)
# =============================================================================================
def _py(value):
    """None para qualquer ausente; tipo nativo para o resto."""
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value.item() if isinstance(value, np.generic) else value


def _iso(value) -> str | None:
    value = _py(value)
    return None if value is None else pd.Timestamp(value).strftime("%Y-%m-%d")


def _amount(value):
    """Inteiro quando o valor é inteiro (preços de tabela), senão float; None se ausente."""
    value = _py(value)
    if value is None:
        return None
    return int(value) if float(value).is_integer() else float(value)


def _plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


def _days(n: int) -> str:
    return f"{fmt.fmt_int(n)} {_plural(n, 'dia', 'dias')}"


def slugify(name: str) -> str:
    """'Mei-Mei Johns' -> 'mei-mei-johns' (minúsculas, sem acento, hífen entre palavras)."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def last_event_date(deals: pd.DataFrame) -> pd.Timestamp:
    """Última data registrada no CRM (engajamento ou fechamento): o fim dos dados."""
    return deals[["engage_date", "close_date"]].max().max()


# =============================================================================================
# Snapshot: uma foto da carteira numa data
# =============================================================================================
def model_section(model: score.ScoreModel) -> dict:
    """Parâmetros do modelo do corte (os primeiros são o contrato; o resto é diagnóstico).

    `knot_days` é o último dia do Foque (a chance ainda é pelo menos metade da de um deal novo); `limpe_after_days`, o
    último dia do Reative; `limpe_rule` diz se o Limpe começa pela chance mínima ("chance") ou pelo maior ciclo ganho ("ciclo").
    """
    curve = model.curve
    return {
        "version": model.version,
        "knot_days": model.knot_days,
        "p_fresh": model.p_fresh,
        "limpe_after_days": model.limpe_after_days,
        "limpe_rule": model.limpe_rule,
        "limpe_min_chance": config.LIMPE_MIN_CHANCE,
        "max_won_cycle_days": model.max_won_cycle_days,
        "halving_days": curve.halving_days,
        "slope_per_30d": getattr(curve, "slope_per_30d", None),
        "phase": getattr(curve, "phase", None),
        "base_rate": curve.base_rate,
        "train_rows": curve.train_rows,
        "train_snapshots": list(curve.train_snapshots),
        "as_of_date": model.as_of_date,
    }


def outcomes_by_id(deals: pd.DataFrame, reference_date) -> dict[str, dict]:
    """Desfecho real de cada deal até a data de referência.

    `Ganho` e `Perdido` só valem para fechamentos até a referência; o resto é `Aberto`.
    Perdido não leva valor de fechamento (o CRM grava 0, que não é um valor).
    """
    ref = pd.Timestamp(reference_date)
    closed = deals["close_date"].notna() & (deals["close_date"] <= ref) & deals["deal_stage"].isin(config.CLOSED_STAGES)
    out = {}
    for is_closed, opp, stage, close_date, close_value in zip(
        closed, deals["opportunity_id"], deals["deal_stage"], deals["close_date"], deals["close_value"]
    ):
        if not is_closed:
            out[opp] = {"status": "Aberto", "close_date": None, "close_value": None}
        elif stage == "Won":
            out[opp] = {"status": "Ganho", "close_date": _iso(close_date), "close_value": _amount(close_value)}
        else:
            out[opp] = {"status": "Perdido", "close_date": _iso(close_date), "close_value": None}
    return out


def deal_record(row: dict, model: score.ScoreModel, outcome: dict | None) -> dict:
    """Um deal no formato do contrato (seção 6). `row` é uma linha de `score.score_deals`."""
    return {
        "id": row["opportunity_id"],
        "agent": row["sales_agent"],
        "manager": row["manager"],
        "region": row["regional_office"],
        "account": _py(row["account"]),
        "product": row["product"],
        "price": _amount(row["sales_price"]),
        "engage_date": _iso(row["engage_date"]),
        "age": _py(row["age_days"]),
        "p": _py(row["p_win"]),
        "ev": _py(row["expected_value"]),
        "score": _py(row["score"]),
        "cat": row["category"],
        "why": explain.explain_deal(row, model),
        "days_to_knot": _py(row["days_to_knot"]),
        "days_to_limpe": _py(row["days_to_limpe"]),
        "outcome": outcome,
    }


def summarize(records: list[dict]) -> dict:
    """`summary`: por lista, n, soma do preço de tabela e soma do valor esperado (None em Qualifique)."""
    out = {}
    for cat in CATS:
        part = [d for d in records if d["cat"] == cat]
        out[cat] = {
            "n": len(part),
            "valor_tabela": _amount(sum(d["price"] for d in part)),
            "valor_esperado": None if cat == "Qualifique" else math.fsum(d["ev"] for d in part),
        }
    return out


def summarize_outcomes(records: list[dict]) -> dict:
    """`outcome_summary` (só modo teste): por lista, n, fração ganha até a referência e receita ganha."""
    out = {}
    for cat in SCORED_CATS:
        part = [d for d in records if d["cat"] == cat]
        won = [d for d in part if d["outcome"]["status"] == "Ganho"]
        out[cat] = {
            "n": len(part),
            "pct_ganhos": len(won) / len(part) if part else 0.0,
            "receita_ganha": _amount(sum(d["outcome"]["close_value"] for d in won)),
        }
    return out


def snapshot_label(mode: str, date: str) -> str:
    prefix = "Hoje —" if mode == TODAY else "Teste:"
    return f"{prefix} {fmt.fmt_date(date)}"


def build_snapshot(deals: pd.DataFrame, date, mode: str, reference_date, headline: dict | None = None) -> dict:
    """A foto da carteira em `date`, só com o que se sabia nela.

    Ajusta o modelo do corte (`fit_model`), pontua, ordena (`order_for_list`) e explica cada deal.
    No modo `hoje`, `date` é a referência e os Prospecting entram como Qualifique (se a referência é o fim
    dos dados). No modo `teste`, `date` é anterior à referência e cada deal leva o desfecho real até ela.
    `headline` alimenta a linha 5 de "Como funciona" (ver `backtest_section`).
    """
    assert mode in (TODAY, TEST), f"modo inválido: {mode}"
    T, ref = pd.Timestamp(date), pd.Timestamp(reference_date)
    assert (T == ref) if mode == TODAY else (T < ref), f"data {T.date()} incompatível com o modo {mode}"
    model = score.fit_model(deals, T)
    prospecting = mode == TODAY and T >= last_event_date(deals)
    scored = score.order_for_list(score.score_deals(deals, T, model, include_prospecting=prospecting))
    outcomes = outcomes_by_id(deals, ref) if mode == TEST else {}
    records = [
        deal_record(row, model, outcomes.get(row["opportunity_id"]))
        for row in scored.to_dict("records")
    ]
    snapshot = {
        "date": T.strftime("%Y-%m-%d"),
        "mode": mode,
        "label": snapshot_label(mode, T.strftime("%Y-%m-%d")),
        "model": model_section(model),
        "how_it_works": explain.how_it_works(model, headline),
        "summary": summarize(records),
    }
    if mode == TEST:
        snapshot["outcome_summary"] = summarize_outcomes(records)
    snapshot["deals"] = records
    return snapshot


# =============================================================================================
# Pessoas
# =============================================================================================
def people_section(deals: pd.DataFrame, teams: pd.DataFrame, open_today: list[dict]) -> dict:
    """Os vendedores do cadastro (inclusive os sem nenhum deal), os managers e as regiões.

    `has_deals`: aparece em algum estágio do pipeline. `n_open`: deals do snapshot de hoje (`open_today`).
    """
    with_deals = set(deals["sales_agent"])
    open_by_agent = pd.Series([d["agent"] for d in open_today], dtype="str").value_counts()
    agents = [
        {
            "name": r.sales_agent,
            "manager": r.manager,
            "region": r.regional_office,
            "has_deals": r.sales_agent in with_deals,
            "n_open": int(open_by_agent.get(r.sales_agent, 0)),
        }
        for r in teams.sort_values("sales_agent").itertuples(index=False)
    ]
    pairs = teams[["manager", "regional_office"]].drop_duplicates().sort_values("manager")
    assert pairs["manager"].is_unique, "um manager em mais de uma região"
    return {
        "agents": agents,
        "managers": [{"name": m, "region": r} for m, r in pairs.itertuples(index=False)],
        "regions": sorted(teams["regional_office"].unique()),
    }


# =============================================================================================
# Backtest: ADAPTADOR do backtest_metrics.json (único ponto que conhece o formato do arquivo)
# =============================================================================================
# Chaves lidas (formato de `validate.run_backtest`):
#   config.method_labels[m]            rótulo de cada método
#   criterion.{rule, passed, adjustment_applied}
#   headline.{n_cortes, receita_score, receita_valor, receita_recencia}   (= validate.headline_metrics)
#   cuts[i].{cut, metodos[m].{auc, ganhos_top20, receita_top20}, categorias[cat].n,
#            resolvidos.metodos[m].receita_top20, foque_por_idade.{faixas, diferenca_ultima_menos_primeira_90d}}
#   media_cortes.metodos[m]            (mesmas três métricas)
#   hoje.{categorias[cat].{n, valor_tabela, valor_esperado}, foque_por_idade[].{faixa, n}}
def metric_definitions() -> list[dict]:
    """As tabelas do painel; a 1ª é a métrica primária. Nenhum número fica escrito à mão."""
    top = fmt.fmt_pct(config.TOP_FRAC, 0)
    return [
        {"key": "receita_top20", "label": f"Receita ganha capturada pelo top {top} (métrica principal)", "kind": "pct"},
        {"key": "ganhos_top20", "label": f"Ganhos capturados pelo top {top}", "kind": "pct"},
        {
            "key": "auc",
            "label": f"AUC (separa ganhos de perdas; {fmt.fmt_dec(AUC_RANDOM, 1)} = sorteio)",
            "kind": "dec",
        },
    ]


def _cut_blocks(metrics: dict) -> list[tuple[str, str, dict]]:
    """(chave do corte, rótulo, métricas por método), os cortes em ordem e a média por último.

    O método `score_v1` (curva antiga, mesmos deals e mesmos baselines) vem de `cuts_v1`.
    """
    blocks = [
        (c["cut"], fmt.fmt_date(c["cut"]), {**c["metodos"], "score_v1": old["metodos"]["score"]})
        for c, old in zip(metrics["cuts"], metrics["cuts_v1"])
    ]
    n = len(metrics["cuts"])
    mean = {**metrics["media_cortes"]["metodos"], "score_v1": metrics["media_cortes_v1"]["metodos"]["score"]}
    blocks.append(("media", f"Média dos {fmt.fmt_int(n)} cortes", mean))
    return blocks


def backtest_rows(metrics: dict) -> list[dict]:
    """Formato longo: uma linha por (corte, método), na ordem de exibição."""
    labels = metrics["config"]["method_labels"]
    rows = []
    for cut, cut_label, by_method in _cut_blocks(metrics):
        for method in ROW_METHODS:
            values = by_method[method]
            rows.append(
                {
                    "cut": cut,
                    "cut_label": cut_label,
                    "method": method,
                    "method_label": labels[method],
                    "auc": values["auc"],
                    "ganhos_top20": values["ganhos_top20"],
                    "receita_top20": values["receita_top20"],
                }
            )
    return rows


def headline_text(head: dict) -> str:
    return (
        f"Testado em {fmt.fmt_int(head['n_cortes'])} datas passadas: o top {fmt.fmt_pct(config.TOP_FRAC, 0)} do score "
        f"capturou {fmt.fmt_pct(head['receita_score'], 0)} da receita ganha depois, contra "
        f"{fmt.fmt_pct(head['receita_valor'], 0)} ordenando por valor e "
        f"{fmt.fmt_pct(head['receita_recencia'], 0)} pelos mais recentes."
    )


def criterion_text(metrics: dict) -> str | None:
    """O critério pré-registrado e o resultado, em uma frase (None se o JSON não traz critério)."""
    criterion = metrics.get("criterion")
    if not criterion:
        return None
    verdict = "PASSOU" if criterion["passed"] else "FALHOU"
    adjusted = " Foi aplicado o ajuste único pré-definido." if criterion.get("adjustment_applied") else ""
    change = ""
    if criterion.get("post_backtest_change"):
        old = "PASSOU" if criterion.get("v1_passed") else "FALHOU"
        change = (
            f" A curva v2 é uma mudança pós-backtest, pedida pelo Rafael depois de revisar a ferramenta (a v1 também {old}); "
            "o critério foi mantido e reportado para as duas."
        )
    return f"Critério fixado antes do código: {criterion['rule']} Resultado (curva v2): {verdict}.{adjusted}{change}"


def _note_recency_auc(cuts: list[dict], label: dict) -> str | None:
    wins = [label[c["cut"]] for c in cuts if c["metodos"]["recencia"]["auc"] > c["metodos"]["score"]["auc"]]
    if not wins:
        return None
    return (
        f"A recência (mais recentes primeiro) tem AUC maior que o score em {fmt.fmt_int(len(wins))} de "
        f"{fmt.fmt_int(len(cuts))} cortes ({', '.join(wins)}). AUC e captura de ganhos são reportadas, "
        "mas não decidem o critério: a métrica principal é a receita."
    )


def _note_margin_and_recency_low(cuts: list[dict], label: dict) -> list[str]:
    others = list(BASELINE_METHODS)
    margins = [
        (c["metodos"]["score"]["receita_top20"] - max(c["metodos"][m]["receita_top20"] for m in others), c["cut"])
        for c in cuts
    ]
    margin, cut = min(margins)
    low = min(cuts, key=lambda c: c["metodos"]["recencia"]["receita_top20"])
    return [
        "A menor vantagem do score na receita capturada sobre o melhor dos outros métodos foi de "
        f"{fmt.fmt_pp(margin)} (corte de {label[cut]}).",
        f"A recência é instável na receita: no corte de {label[low['cut']]} ela capturou só "
        f"{fmt.fmt_pct(low['metodos']['recencia']['receita_top20'], 0)} da receita, "
        f"contra {fmt.fmt_pct(low['metodos']['score']['receita_top20'], 0)} do score.",
    ]


def _note_resolved(cuts: list[dict], reference_date) -> str:
    """Entre os deals já fechados, o score e o valor empatam: a vantagem vem de achar os zumbis."""
    gaps = [
        abs(c["resolvidos"]["metodos"]["score"]["receita_top20"] - c["resolvidos"]["metodos"]["valor"]["receita_top20"])
        for c in cuts
    ]
    worst = f"{fmt.fmt_dec(max(gaps) * 100, 1)} pp"
    if max(gaps) <= config.CRITERION_TIE_TOL:
        verdict = f"o score e ordenar por valor empatam na receita capturada (diferença máxima de {worst} nos cortes)"
    else:
        verdict = f"o score e ordenar por valor diferem na receita capturada em até {worst}"
    return (
        f"Só entre os deals já resolvidos (fechados até {fmt.fmt_date(reference_date)}), {verdict}: a vantagem do "
        "score vem de achar os zumbis, deals abertos há mais tempo do que qualquer ganho do histórico."
    )


def _note_intra_foque(metrics: dict, label: dict) -> str | None:
    """Ordem dentro do Foque: o score v2 contra o v1, o valor e a recência (mesma população para todos)."""
    intra = metrics.get("intra_foque")
    if not intra:
        return None
    media = intra["media"]
    best = max(intra["por_corte"], key=lambda c: c["metodos"]["score_v2"]["receita_top20"] - c["metodos"]["score_v1"]["receita_top20"])
    gap = best["metodos"]["score_v2"]["receita_top20"] - best["metodos"]["score_v1"]["receita_top20"]
    return (
        f"Só entre os deals com até {fmt.fmt_int(intra['idade_max'])} dias (a ordem dentro do Foque), o top {fmt.fmt_pct(config.TOP_FRAC, 0)} do "
        f"score v2 capturou em média {fmt.fmt_pct(media['score_v2']['receita_top20'], 0)} da receita ganha depois, contra "
        f"{fmt.fmt_pct(media['score_v1']['receita_top20'], 0)} do v1 e {fmt.fmt_pct(media['valor']['receita_top20'], 0)} ordenando por valor; "
        f"a AUC é {fmt.fmt_dec(media['score_v2']['auc'], 2)}, perto de um sorteio. A diferença para o v1 está concentrada no corte de "
        f"{label[best['cut']]} ({fmt.fmt_pp(gap)}); nos outros cortes os dois ordenam quase igual."
    )


def backtest_notes(metrics: dict, reference_date) -> list[str]:
    """Ressalvas honestas, todas calculadas das métricas (nenhum número escrito à mão)."""
    cuts = metrics["cuts"]
    label = {c["cut"]: fmt.fmt_date(c["cut"]) for c in cuts}
    notes = [
        _note_recency_auc(cuts, label),
        *_note_margin_and_recency_low(cuts, label),
        _note_resolved(cuts, reference_date),
        _note_intra_foque(metrics, label),
        f"Deals ainda abertos em {fmt.fmt_date(reference_date)} contam como não ganhos: o desfecho vai só até essa data.",
    ]
    return [n for n in notes if n]


def backtest_section(metrics: dict, reference_date) -> tuple[dict, dict]:
    """Converte o JSON de métricas na seção `backtest` do contrato.

    Devolve (seção, dict `headline` da linha 5 de "Como funciona": n_cortes, receita_score,
    receita_valor, receita_recencia).
    """
    head = validate.headline_metrics(metrics)
    section = {
        "headline": headline_text(head),
        "criterion_text": criterion_text(metrics),
        "notes": backtest_notes(metrics, reference_date),
        "metrics": metric_definitions(),
        "rows": backtest_rows(metrics),
    }
    return section, head


def metrics_today(metrics: dict) -> dict:
    """Contagens e valores das 4 listas hoje, segundo o JSON de métricas."""
    return metrics["hoje"]["categorias"]


def metrics_cut_counts(metrics: dict, date: str) -> dict:
    """n por lista de um corte, segundo o JSON de métricas."""
    cut = next(c for c in metrics["cuts"] if c["cut"] == date)
    return {cat: v["n"] for cat, v in cut["categorias"].items()}


# =============================================================================================
# Invariantes
# =============================================================================================
def check_contract(data: dict) -> None:
    """Os invariantes do data-contract.md (seções 4 a 7), com assert."""
    snaps, people = data["snapshots"], data["people"]
    assert snaps and snaps[0]["mode"] == TODAY and snaps[0]["date"] == data["meta"]["reference_date"]
    assert all(s["mode"] == TEST for s in snaps[1:])
    test_dates = [s["date"] for s in snaps[1:]]
    assert test_dates == sorted(test_dates, reverse=True), "snapshots de teste fora da ordem (mais recente primeiro)"
    names = {a["name"] for a in people["agents"]}
    managers = {m["name"]: m["region"] for m in people["managers"]}
    assert len(names) == len(people["agents"]), "vendedor repetido"
    for agent in people["agents"]:
        assert managers[agent["manager"]] == agent["region"], f"{agent['name']}: manager/região inconsistentes"
        assert agent["has_deals"] or agent["n_open"] == 0
    assert set(people["regions"]) == set(managers.values())
    today_count = pd.Series([d["agent"] for d in snaps[0]["deals"]]).value_counts()
    for agent in people["agents"]:
        assert int(today_count.get(agent["name"], 0)) == agent["n_open"], f"{agent['name']}: n_open != deals de hoje"
    for snap in snaps:
        _check_snapshot(snap, names)
    bt = data["backtest"]
    assert bt["headline"] and bt["metrics"] and bt["rows"] and isinstance(bt["notes"], list)


def _check_snapshot(snap: dict, agent_names: set) -> None:
    where = snap["date"]
    assert len(snap["how_it_works"]) == 5, f"{where}: how_it_works deve ter 5 linhas"
    ids = [d["id"] for d in snap["deals"]]
    assert len(ids) == len(set(ids)), f"{where}: ids repetidos"
    order = [CATS.index(d["cat"]) for d in snap["deals"]]
    assert order == sorted(order), f"{where}: deals fora do agrupamento por lista"
    for cat in CATS:
        part = [d for d in snap["deals"] if d["cat"] == cat]
        summary = snap["summary"][cat]
        assert summary["n"] == len(part), f"{where}: summary[{cat}].n"
        assert math.isclose(summary["valor_tabela"], sum(d["price"] for d in part)), f"{where}: valor_tabela[{cat}]"
        if cat == "Qualifique":
            assert summary["valor_esperado"] is None
        else:
            assert math.isclose(summary["valor_esperado"], math.fsum(d["ev"] for d in part), abs_tol=1e-6)
    for d in snap["deals"]:
        assert d["agent"] in agent_names, f"{d['id']}: vendedor fora de people.agents"
        assert 2 <= len(d["why"]) <= 4, f"{d['id']}: {len(d['why'])} frases"
        no_score = d["cat"] == "Qualifique"
        assert all((d[k] is None) == no_score for k in ("p", "ev", "score")), f"{d['id']}: nulos de {d['cat']}"
        assert (d["engage_date"] is None) == no_score and (d["age"] is None) == no_score
        assert (d["days_to_knot"] is not None) == (d["cat"] == "Foque")
        assert (d["days_to_limpe"] is not None) == (d["cat"] in ("Foque", "Reative"))
        assert (d["outcome"] is None) == (snap["mode"] == TODAY), f"{d['id']}: outcome incompatível com o modo"
    if snap["mode"] == TEST:
        assert snap["summary"]["Qualifique"]["n"] == 0
        for cat in SCORED_CATS:
            assert snap["outcome_summary"][cat]["n"] == snap["summary"][cat]["n"], f"{where}: outcome_summary[{cat}].n"
    else:
        assert "outcome_summary" not in snap


def check_against_metrics(data: dict, metrics: dict) -> None:
    """O resumo de hoje e as listas de cada corte de teste batem com o backtest_metrics.json."""
    today, want = data["snapshots"][0]["summary"], metrics_today(metrics)
    for cat in CATS:
        assert today[cat]["n"] == want[cat]["n"], f"hoje/{cat}: n {today[cat]['n']} != {want[cat]['n']}"
        assert math.isclose(today[cat]["valor_tabela"], want[cat]["valor_tabela"], abs_tol=0.5), f"hoje/{cat}: valor de tabela"
        if cat != "Qualifique":
            assert math.isclose(today[cat]["valor_esperado"], want[cat]["valor_esperado"], rel_tol=1e-9, abs_tol=1e-6), (
                f"hoje/{cat}: valor esperado"
            )
    for snap in data["snapshots"][1:]:
        counts = metrics_cut_counts(metrics, snap["date"])
        for cat in SCORED_CATS:
            assert snap["summary"][cat]["n"] == counts[cat], f"{snap['date']}/{cat}: n {snap['summary'][cat]['n']} != {counts[cat]}"


# =============================================================================================
# Montagem
# =============================================================================================
def build_data(
    deals: pd.DataFrame, teams: pd.DataFrame, metrics: dict, reference_date, test_dates=config.UI_BACKTEST_SNAPSHOTS
) -> dict:
    """O `window.LEAD_DATA` inteiro (sem tocar no disco). Os cortes de teste vão do mais recente ao mais antigo."""
    ref = pd.Timestamp(reference_date).strftime("%Y-%m-%d")
    backtest, head = backtest_section(metrics, ref)
    today = build_snapshot(deals, ref, TODAY, ref, head)
    tests = [build_snapshot(deals, d, TEST, ref, head) for d in sorted(test_dates, reverse=True) if d < ref]
    data = {
        "meta": {
            "reference_date": ref,
            "horizon_days": config.HORIZON_DAYS,
            "generated_by": f"python -m scorer.build --reference-date {ref}",
        },
        "people": people_section(deals, teams, today["deals"]),
        "snapshots": [today, *tests],
        "backtest": backtest,
    }
    check_contract(data)
    check_against_metrics(data, metrics)
    return data


# =============================================================================================
# Saídas
# =============================================================================================
def write_data_js(path, data: dict) -> int:
    """Grava `window.LEAD_DATA = {...};` (UTF-8, JSON compacto, sem NaN). Devolve o tamanho em bytes."""
    text = "window.LEAD_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + ";\n"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8", newline="\n")
    return len(text.encode("utf-8"))


CSV_COLUMNS = [  # (coluna no CSV, campo do deal)
    ("id", "id"), ("vendedor", "agent"), ("manager", "manager"), ("regiao", "region"), ("conta", "account"),
    ("produto", "product"), ("preco", "price"), ("engage_date", "engage_date"), ("idade", "age"), ("p", "p"),
    ("ev", "ev"), ("score", "score"), ("categoria", "cat"), ("dias_ate_joelho", "days_to_knot"),
    ("dias_ate_limpe", "days_to_limpe"),
]
CSV_OUTCOME_COLUMNS = ["desfecho", "data_fechamento", "valor_fechamento"]


def snapshot_csv_rows(snapshot: dict) -> list[list]:
    """Cabeçalho e uma linha por deal (explicação unida por ' | '; desfecho vazio no modo hoje)."""
    header = [col for col, _ in CSV_COLUMNS] + ["explicacao"] + CSV_OUTCOME_COLUMNS
    rows = [header]
    for d in snapshot["deals"]:
        outcome = d["outcome"] or {}
        values = [d[field] for _, field in CSV_COLUMNS] + [" | ".join(d["why"])]
        values += [outcome.get("status"), outcome.get("close_date"), outcome.get("close_value")]
        rows.append(["" if v is None else v for v in values])
    return rows


def write_snapshot_csv(path, snapshot: dict) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(snapshot_csv_rows(snapshot))


# --- Briefs ----------------------------------------------------------------------------------
def action_sentence(counts: dict, limpe_value) -> str:
    """'Esta semana: foque em 3 deals, reative 2 antes que esfriem, limpe 5 do CRM (US$ 9.000 parados) ...'."""
    parts = []
    if counts["Foque"]:
        parts.append(f"foque em {fmt.fmt_int(counts['Foque'])} {_plural(counts['Foque'], 'deal', 'deals')}")
    if counts["Reative"]:
        n = counts["Reative"]
        parts.append(f"reative {fmt.fmt_int(n)} antes que {_plural(n, 'esfrie', 'esfriem')}")
    if counts["Limpe"]:
        parts.append(f"limpe {fmt.fmt_int(counts['Limpe'])} do CRM ({fmt.fmt_usd(limpe_value)} parados)")
    if counts["Qualifique"]:
        parts.append(f"qualifique {fmt.fmt_int(counts['Qualifique'])} em Prospecting")
    if not parts:
        return "Esta semana: nenhum deal aberto para priorizar."
    head = ", ".join(parts[:-1]) + " e " + parts[-1] if len(parts) > 1 else parts[0]
    return f"Esta semana: {head}."


def _deal_headline(d: dict) -> str:
    account = d["account"] or config.NO_ACCOUNT_LABEL
    bits = [f"**{account}**", d["product"], f"{fmt.fmt_usd(d['price'])} de tabela"]
    if d["age"] is not None:
        bits.append(f"aberto há {_days(d['age'])}")
    if d["score"] is not None:
        bits.append(f"score {d['score']}")
    return " · ".join(bits)


def _top_section(title_noun: str, cat: str, deals: list[dict], with_why: bool) -> list[str]:
    """Seção 'N para focar/reativar': os primeiros da lista, cada um com a 1ª e a 3ª frases."""
    k = BRIEF_TOP[cat]
    top = deals[:k]
    if not deals:
        return [f"## {cat}", "", f"Nenhum deal em {cat} esta semana.", ""]
    lines = [f"## {fmt.fmt_int(len(top))} para {title_noun}", ""]
    if len(deals) > len(top):
        lines += [f"{fmt.fmt_int(len(deals))} deals em {cat}; estes são os {fmt.fmt_int(len(top))} de maior valor esperado.", ""]
    for i, d in enumerate(top, 1):
        lines.append(f"{i}. {_deal_headline(d)}")
        if with_why:
            lines += [f"   - {d['why'][0]}", f"   - {d['why'][2]}"]
    return lines + [""]


def _list_section(cat: str, deals: list[dict], value: float) -> list[str]:
    """Seção resumida (Limpe e Qualifique): total e os maiores por valor de tabela."""
    k = BRIEF_TOP[cat]
    if not deals:
        return [f"## {cat}", "", f"Nenhum deal em {cat}.", ""]
    lines = [f"## {cat}: {fmt.fmt_int(len(deals))} {_plural(len(deals), 'deal', 'deals')} ({fmt.fmt_usd(value)} de tabela)", ""]
    lines.append(f"Os {fmt.fmt_int(min(k, len(deals)))} de maior valor:")
    lines.append("")
    lines += [f"- {_deal_headline(d)}" for d in deals[:k]]
    return lines + [""]


def brief_text(agent: dict, deals: list[dict], reference_date) -> str:
    """Brief de segunda-feira de um vendedor. `deals` são os dele no snapshot de hoje, na ordem de exibição."""
    by_cat = {cat: [d for d in deals if d["cat"] == cat] for cat in CATS}
    counts = {cat: len(by_cat[cat]) for cat in CATS}
    value = {cat: sum(d["price"] for d in by_cat[cat]) for cat in CATS}
    lines = [
        f"# Brief de segunda-feira — {agent['name']} — {fmt.fmt_date(reference_date)}",
        "",
        f"Manager: {agent['manager']} · Região: {agent['region']}",
        "",
        f"**{action_sentence(counts, value['Limpe'])}**",
        "",
    ]
    lines += _top_section("focar", "Foque", by_cat["Foque"], with_why=True)
    lines += _top_section("reativar", "Reative", by_cat["Reative"], with_why=True)
    lines += _list_section("Limpe", by_cat["Limpe"], value["Limpe"])
    lines += _list_section("Qualifique", by_cat["Qualifique"], value["Qualifique"])
    lines += [
        "---",
        "",
        "Score = chance de ganho × preço de tabela, pela idade do deal. O vendedor não entra no cálculo.",
        "Gerado por `python -m scorer.build`.",
        "",
    ]
    return "\n".join(lines)


def briefs_index(people: dict, today: dict, reference_date) -> str:
    """`briefs/README.md`: quem tem brief (com as contagens) e quem não tem, e por quê."""
    counts = {a["name"]: dict.fromkeys(CATS, 0) for a in people["agents"]}
    for d in today["deals"]:
        counts[d["agent"]][d["cat"]] += 1
    with_brief = [a for a in people["agents"] if a["n_open"] > 0]
    only_closed = [a for a in people["agents"] if a["has_deals"] and a["n_open"] == 0]
    no_deals = [a for a in people["agents"] if not a["has_deals"]]
    lines = [
        f"# Briefs de segunda-feira — {fmt.fmt_date(reference_date)}",
        "",
        f"Um brief por vendedor com deal aberto ({fmt.fmt_int(len(with_brief))} de {fmt.fmt_int(len(people['agents']))} "
        "vendedores do cadastro). Gerados por `python -m scorer.build`; não edite à mão.",
        "",
        "| Vendedor | Manager | Região | " + " | ".join(CATS) + " |",
        "| :--- | :--- | :--- | " + " | ".join(["---:"] * len(CATS)) + " |",
    ]
    for a in with_brief:
        c = counts[a["name"]]
        cells = " | ".join(fmt.fmt_int(c[cat]) for cat in CATS)
        lines.append(f"| [{a['name']}]({slugify(a['name'])}.md) | {a['manager']} | {a['region']} | {cells} |")
    lines += ["", "## Sem brief", ""]
    lines += [f"**Sem nenhum deal no CRM** ({fmt.fmt_int(len(no_deals))}): cadastro sem pipeline, nada para priorizar.", ""]
    lines += [f"- {a['name']} — {a['manager']}, {a['region']}" for a in no_deals]
    lines += ["", f"**Só com deals fechados** ({fmt.fmt_int(len(only_closed))}): sem deals abertos nesta data.", ""]
    lines += [f"- {a['name']} — {a['manager']}, {a['region']}" for a in only_closed]
    return "\n".join(lines) + "\n"


def write_briefs(briefs_dir, data: dict) -> list[str]:
    """Grava um brief por vendedor com deal aberto e o índice. Devolve os nomes dos arquivos dos briefs."""
    briefs_dir = Path(briefs_dir)
    briefs_dir.mkdir(parents=True, exist_ok=True)
    today, people = data["snapshots"][0], data["people"]
    ref = data["meta"]["reference_date"]
    names = []
    for agent in people["agents"]:
        if agent["n_open"] == 0:
            continue
        mine = [d for d in today["deals"] if d["agent"] == agent["name"]]
        name = f"{slugify(agent['name'])}.md"
        (briefs_dir / name).write_text(brief_text(agent, mine, ref), encoding="utf-8", newline="\n")
        names.append(name)
    (briefs_dir / "README.md").write_text(briefs_index(people, today, ref), encoding="utf-8", newline="\n")
    return names


# =============================================================================================
# Linha de comando
# =============================================================================================
def clear_outputs(paths: Paths) -> None:
    """Apaga o que o build gera (data.js, briefs/*.md, snapshot_*.csv): nada é reaproveitado."""
    paths.data_js.unlink(missing_ok=True)
    for pattern, folder in (("*.md", paths.briefs), ("snapshot_*.csv", paths.processed)):
        for old in folder.glob(pattern):
            old.unlink()


def run_backtest(paths: Paths, deals: pd.DataFrame) -> dict:
    """Roda `validate.run_backtest` e devolve as métricas gravadas em backtest_metrics.json.

    Na solução real o validate grava o JSON e as tabelas nos caminhos globais; numa raiz de teste o JSON vai
    para a própria raiz e nada global é tocado.
    """
    real = paths.root == config.SOLUTION_DIR
    metrics = validate.run_backtest(deals, write=real)
    if not real:
        with open(paths.backtest_json, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(metrics, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    return metrics


def _print_summary(data: dict, size: int, briefs: list[str]) -> None:
    print(f"\nreferência: {fmt.fmt_date(data['meta']['reference_date'])}")
    for snap in data["snapshots"]:
        cells = "  ".join(f"{cat} {fmt.fmt_int(snap['summary'][cat]['n'])}" for cat in CATS)
        print(f"  {snap['label']:<22} {fmt.fmt_int(len(snap['deals'])):>6} deals  |  {cells}")
    megabytes = size / (1024 * 1024)
    status = "ok" if size < MAX_DATA_JS_BYTES else f"ACIMA da meta de {fmt.fmt_dec(MAX_DATA_JS_BYTES / 1024 / 1024, 0)} MB"
    print(f"data.js: {fmt.fmt_dec(megabytes, 2)} MB ({status}); briefs: {fmt.fmt_int(len(briefs))} + README")


def build(paths: Paths, reference_date, inject_docs=True) -> dict:
    """Todo o build. Devolve o `data` gravado em app/data.js."""
    ref = pd.Timestamp(reference_date).strftime("%Y-%m-%d")
    clear_outputs(paths)
    clean.main(["--reference-date", ref, "--raw-dir", str(paths.raw), "--out-dir", str(paths.processed)])
    deals = clean.load_deals(paths.deals_csv)
    teams = clean.load_raw(paths.raw)["sales_teams"]
    metrics = run_backtest(paths, deals)
    data = build_data(deals, teams, metrics, ref)
    for snap in data["snapshots"]:
        write_snapshot_csv(paths.snapshot_csv(snap["date"]), snap)
    size = write_data_js(paths.data_js, data)
    briefs = write_briefs(paths.briefs, data)
    if inject_docs:
        blocks = docs.render_blocks()
        for doc in config.COVERED_DOCS:
            print(f"{Path(doc).name}: {'atualizado' if docs.inject(doc, blocks) else 'sem mudanças'}")
    _print_summary(data, size, briefs)
    return data


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Regenera do zero data.js, snapshots CSV e briefs.")
    parser.add_argument("--reference-date", default=config.DEFAULT_REFERENCE_DATE)
    parser.add_argument("--out-root", default=config.SOLUTION_DIR, help="raiz com data/raw (padrão: solution/)")
    args = parser.parse_args(argv)
    root = Path(args.out_root).resolve()
    # Os documentos e o facts/backtest globais pertencem à solução real; fora dela não se injeta nada.
    build(Paths(root), args.reference_date, inject_docs=root == config.SOLUTION_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
