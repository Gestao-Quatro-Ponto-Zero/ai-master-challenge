"""Máquina do tempo (um vendedor numa data, com o desfecho revelado) e a prova agregada do score.

As listas são montadas só com o que se sabia na data; o desfecho é anexado depois, de propósito.
Na prova, empates de ordenação não são sorteados: cada lista conta a expectativa exata do desempate.
"""
from __future__ import annotations

import threading
import weakref
from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from engine import fmt
from engine.core import (HORIZON_DAYS, MIN_CELL, Dataset, ScoredDeal, Snapshot, mondays, resolve_working_seller,
                         snapshot, stale_key)
from engine.shapes import date_dict, person_dict

TOP_N = 10
EVAL_FIRST = date(2017, 7, 3)
EVAL_LAST = date(2017, 11, 27)
TIE_MARGIN = 0.02  # diferença menor que 2% conta como empate nas frases

RULES = ("score", "value_no_stale", "value_no_stale_newest", "value_only", "random", "oracle")
COMPARED = ("value_only", "value_no_stale", "value_no_stale_newest")
PERIODS = (("jul-set", "julho a setembro", (7, 8, 9)), ("out-nov", "outubro e novembro", (10, 11)))

FAIR_TITLE = "E ordenando por valor, já sem os deals sem desfecho?"
HIDDEN_ACCOUNT_NOTE = {
    "title": "Por que o cliente não aparece aqui",
    "body": "Nesta base, todo deal que fechou tem cliente, e a maioria dos que nunca fecharam não tem. "
            "Mostrar o cliente numa data passada adiantaria o desfecho.",
}


# ---------------------------------------------------------------- desfecho e expectativa exata

def _horizon_end(d: date) -> date:
    return d + timedelta(days=HORIZON_DAYS)


def _sale(s: ScoredDeal, d: date) -> Tuple[int, int]:
    """(1, valor fechado) se o deal virou venda antes de d + 30 dias; senão (0, 0)."""
    x = s.deal
    if x.won and x.close_date is not None and x.close_date < _horizon_end(d):
        return 1, x.close_value or 0
    return 0, 0


def _expected_top(items: Sequence[ScoredDeal], key: Callable[[ScoredDeal], Any], d: date,
                  top_n: int) -> Tuple[float, float]:
    """Vendas e receita esperadas no top N ordenando por key (maior primeiro), com desempate ao acaso.

    Grupos de chave igual entram inteiros enquanto cabem; no grupo que não cabe, conta a fração vagas/tamanho.
    """
    groups: Dict[Any, List[ScoredDeal]] = defaultdict(list)
    for s in items:
        groups[key(s)].append(s)
    wins = revenue = 0.0
    slots = top_n
    for k in sorted(groups, reverse=True):
        if slots <= 0:
            break
        group = groups[k]
        share = min(1.0, slots / float(len(group)))
        for s in group:
            y, v = _sale(s, d)
            wins += share * y
            revenue += share * v
        slots -= len(group)
    return wins, revenue


def _rule_keys(d: date) -> Dict[str, Callable[[ScoredDeal], Any]]:
    return {
        "score": lambda s: round(s.expected_value, 2),
        "value_no_stale": lambda s: (not s.stale, s.deal.price),
        "value_no_stale_newest": lambda s: (not s.stale, s.deal.price, -s.age_days),
        "value_only": lambda s: s.deal.price,
        "random": lambda s: 0,
        "oracle": lambda s: _sale(s, d)[1],
    }


# ---------------------------------------------------------------- prova agregada

def _eval_lists(snap: Snapshot, top_n: int) -> List[Tuple[ScoredDeal, ...]]:
    """Listas de abertos dos vendedores com pelo menos top_n abertos, em ordem de nome."""
    return [snap.by_seller[name] for name in sorted(snap.by_seller) if len(snap.by_seller[name]) >= top_n]


def _run(ds: Dataset, dates: Sequence[date], top_n: int) -> Tuple[int, List[Dict[str, Any]]]:
    """Soma, por data e por regra, as vendas e a receita esperadas no top N."""
    n_lists, rows = 0, []
    for d in dates:
        lists = _eval_lists(snapshot(ds, d), top_n)
        keys = _rule_keys(d)
        sums = {r: [0.0, 0.0] for r in RULES}
        for items in lists:
            for rule, key in keys.items():
                w, v = _expected_top(items, key, d, top_n)
                sums[rule][0] += w
                sums[rule][1] += v
        n_lists += len(lists)
        rows.append({"date": d, "lists": len(lists), "sums": sums})
    return n_lists, rows


def _gain(score: float, other: float) -> Optional[float]:
    return score / other - 1 if other else None


def _totals(rows: Sequence[Dict[str, Any]], rule: str) -> Tuple[float, float]:
    return sum(r["sums"][rule][0] for r in rows), sum(r["sums"][rule][1] for r in rows)


def _gains(rows: Sequence[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    score = _totals(rows, "score")[1]
    return {"vs_" + rule: _gain(score, _totals(rows, rule)[1]) for rule in COMPARED}


def _auc(pairs: List[Tuple[float, int]]) -> Optional[float]:
    """Probabilidade de um positivo ficar acima de um negativo (empate conta 0,5)."""
    pairs = sorted(pairs, key=lambda t: t[0])
    pos = sum(y for _, y in pairs)
    neg = len(pairs) - pos
    if not pos or not neg:
        return None
    rank_sum, i = 0.0, 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        rank_sum += ((i + j) / 2.0 + 1) * sum(y for _, y in pairs[i:j + 1])
        i = j + 1
    return (rank_sum - pos * (pos + 1) / 2.0) / (pos * neg)


def _age_only_chances(ds: Dataset, snap: Snapshot) -> List[float]:
    """Chance por faixa só pela idade (célula com n >= 30, senão a taxa geral), com as segundas do modelo da data."""
    bands = [[0, 0] for _ in snap.bands]
    total = [0, 0]
    for m in snap.model.mondays:
        for b, (y, n) in enumerate(ds.monday_counts[m]):
            bands[b][0] += y
            bands[b][1] += n
            total[0] += y
            total[1] += n
    overall = total[0] / float(total[1]) if total[1] else 0.0
    return [y / float(n) if n >= MIN_CELL else overall for y, n in bands]


def _auc_block(ds: Dataset, dates: Sequence[date]) -> Dict[str, Any]:
    """AUC sobre todos os pares deal-data. chance: tabela da data (idade e trimestre), sem zerar os sem
    desfecho; age_only: só a faixa de idade; expected_value: a ordem do app (receita esperada, 2 casas)."""
    chance, age, price, expected = [], [], [], []
    for d in dates:
        snap = snapshot(ds, d)
        age_chances = _age_only_chances(ds, snap)
        for s in snap.deals:
            y = _sale(s, d)[0]
            chance.append((snap.bands[s.age_band].chance, y))
            age.append((age_chances[s.age_band], y))
            price.append((float(s.deal.price), y))
            expected.append((round(s.expected_value, 2), y))
    return {"chance": _auc(chance), "age_only": _auc(age), "price": _auc(price), "expected_value": _auc(expected),
            "pairs": len(chance), "positives": sum(y for _, y in chance)}


def _signed_pct(frac: float) -> str:
    """"+42%" para ganho, "-5%" para perda, "0%" quando arredonda a zero."""
    text = fmt.pct(frac)
    return "+" + text if frac > 0 and text != "0%" else text


def _dates_label(first: date, last: date) -> str:
    """"de 3 jul a 27 nov 2017"."""
    if first.year == last.year:
        return "de %s a %s %d" % (fmt.day_month(first), fmt.day_month(last), last.year)
    return "de %s a %s" % (fmt.date_label(first), fmt.date_label(last))


def _sentences(n_lists: int, n_dates: int, period: str, rules: Dict[str, Dict[str, float]],
               gains: Dict[str, Optional[float]], dates_won: Dict[str, Dict[str, Any]],
               by_period: List[Dict[str, Any]]) -> Dict[str, Any]:
    g_simple, g_value = gains["vs_value_no_stale"] or 0.0, gains["vs_value_only"] or 0.0
    headline_detail = ("de receita em 30 dias contra ordenar por valor já sem os deals sem desfecho. "
                       "Contra ordenar só por valor, %s." % _signed_pct(g_value))
    per10 = {k: fmt.number(rules[k]["wins_per_list"] * 10.0 / TOP_N, 1) for k in rules}
    method = ("Soma das %s de %d deals, em %s %s. A cada %d indicados, %s %s venda pelo score, %s pela regra "
              "simples e %s só por valor." % (
                  fmt.plural(n_lists, "lista"), TOP_N, fmt.plural(n_dates, "segunda-feira", "segundas-feiras"),
                  period, TOP_N, per10["score"],
                  fmt.plural_word(rules["score"]["wins_per_list"] * 10.0 / TOP_N, "virou", "viraram"),
                  per10["value_no_stale"], per10["value_only"]))

    simple, value = dates_won["vs_value_no_stale"], dates_won["vs_value_only"]
    if simple["won"] == simple["total"]:
        title1 = "Vence nas %d semanas" % simple["total"]
        body1 = "Contra a regra simples, o score venceu em todas as %d." % simple["total"]
    else:
        title1 = "Vence em %d de %d semanas" % (simple["won"], simple["total"])
        body1 = "Contra a regra simples, o score perdeu em %s." % fmt.join(simple["lost_labels"])
    if value["won"] == value["total"]:
        body1 += " Contra ordenar só por valor, venceu nas %d." % value["total"]
    else:
        body1 += " Contra ordenar só por valor, venceu em %d de %d." % (value["won"], value["total"])

    first, second = by_period
    g1, g2 = first["gain_vs_value_no_stale"] or 0.0, second["gain_vs_value_no_stale"] or 0.0
    title2 = "Mais forte de julho a setembro" if g1 >= g2 else "Mais forte em outubro e novembro"
    newest = second["gain_vs_value_no_stale_newest"] or 0.0
    if fmt.pct(abs(newest)) == "0%":
        tail = "nesses dois meses dá empate."
    elif abs(newest) < TIE_MARGIN:
        tail = "nesses dois meses quase empata: o score fica %s %s." % (
            fmt.pct(abs(newest)), "acima" if newest > 0 else "abaixo")
    else:
        tail = "nesses dois meses o score fica %s %s." % (fmt.pct(abs(newest)), "acima" if newest > 0 else "abaixo")
    body2 = ("%s no 3º trimestre e %s em outubro e novembro. Se a regra simples puser o deal mais novo na "
             "frente, %s" % (_signed_pct(g1), _signed_pct(g2), tail))
    return {
        "headline": _signed_pct(g_simple),
        "headline_detail": headline_detail,
        "method": method,
        "limits": [
            {"title": title1, "body": body1},
            {"title": title2, "body": body2},
            {"title": "Mede a ordem, não o efeito",
             "body": "A conta mostra quanto da receita que viria a lista captura. "
                     "Não mostra o que muda quando o vendedor trabalha esses deals."},
            {"title": "Conferida duas vezes",
             "body": "Uma segunda implementação, escrita do zero a partir da regra, chegou a números muito "
                     "próximos (diferença abaixo de 0,3%, por causa do desempate) e não achou uso de "
                     "informação do futuro. Um script de conferência refaz os números do app, e todos batem."},
        ],
    }


def _build_proof(ds: Dataset) -> Dict[str, Any]:
    dates = mondays(EVAL_FIRST, EVAL_LAST)
    n_lists, rows = _run(ds, dates, TOP_N)
    rules = {}
    for rule in RULES:
        wins, revenue = _totals(rows, rule)
        rules[rule] = {"revenue": revenue, "wins": wins, "wins_per_list": wins / n_lists if n_lists else 0.0}
    gains = _gains(rows)

    per_date = []
    for r in rows:
        item = {"date": r["date"].isoformat(), "label": fmt.day_month(r["date"]),
                "month_label": fmt.MONTHS_SHORT[r["date"].month - 1], "lists": r["lists"]}
        for rule in ("score",) + COMPARED:
            item[rule] = {"wins": r["sums"][rule][0], "revenue": r["sums"][rule][1]}
        per_date.append(item)

    dates_won: Dict[str, Dict[str, Any]] = {}
    for rule in COMPARED:
        lost = [r["date"] for r in rows if r["sums"]["score"][1] <= r["sums"][rule][1]]
        dates_won["vs_" + rule] = {"won": len(rows) - len(lost), "total": len(rows)}
        if rule == "value_no_stale":
            dates_won["vs_" + rule]["lost_labels"] = [fmt.day_month(d) for d in lost]

    by_period = []
    for key, label, months in PERIODS:
        part = [r for r in rows if r["date"].month in months]
        item = {"key": key, "label": label, "n_dates": len(part)}
        item.update({"gain_" + k: v for k, v in _gains(part).items()})
        by_period.append(item)

    sensitivity = {}
    for n in (5, 20):
        lists_n, rows_n = _run(ds, dates, n)
        g = _gains(rows_n)
        sensitivity["top%d" % n] = {"n_lists": lists_n, "gain_vs_value_only": g["vs_value_only"],
                                    "gain_vs_value_no_stale": g["vs_value_no_stale"]}

    peak = max(rows, key=lambda r: (r["sums"]["score"][0], -r["date"].toordinal()))
    period = _dates_label(dates[0], dates[-1])
    return {
        "n_dates": len(dates),
        "n_lists": n_lists,
        "first_date": date_dict(dates[0]),
        "last_date": date_dict(dates[-1]),
        "top_n": TOP_N,
        "period_label": period,
        "rules": rules,
        "gains": gains,
        "per_date": per_date,
        "dates_won": dates_won,
        "by_period": by_period,
        "auc": _auc_block(ds, dates),
        "sensitivity": sensitivity,
        "peak": {"wins": peak["sums"]["score"][0], "lists": peak["lists"], "date": peak["date"].isoformat(),
                 "label": fmt.day_month(peak["date"])},
        "sentences": _sentences(n_lists, len(dates), period, rules, gains, dates_won, by_period),
    }


_PROOF_CACHE: "weakref.WeakKeyDictionary[Dataset, Dict[str, Any]]" = weakref.WeakKeyDictionary()
_PROOF_LOCK = threading.Lock()


def proof(ds: Dataset) -> Dict[str, Any]:
    """Prova agregada: 22 segundas de 3 jul a 27 nov de 2017, listas de 10 por vendedor. Calculada uma vez."""
    with _PROOF_LOCK:
        result = _PROOF_CACHE.get(ds)
        if result is None:
            result = _PROOF_CACHE[ds] = _build_proof(ds)
        return result


# ---------------------------------------------------------------- máquina do tempo

def _outcome(s: ScoredDeal, d: date) -> Dict[str, Any]:
    x = s.deal
    if x.close_date is not None and x.close_date < _horizon_end(d):
        when = fmt.date_in_context(x.close_date, d)
        if x.won:
            return {"kind": "venda", "label": "Venda · %s" % fmt.money(x.close_value or 0),
                    "value": x.close_value or 0, "date_label": when}
        return {"kind": "perda", "label": "Perda", "value": 0, "date_label": when}
    return {"kind": "aberto", "label": "Segue aberto", "value": None, "date_label": None}


def _tm_list(title: str, items: Sequence[ScoredDeal], d: date) -> Dict[str, Any]:
    rows = []
    for rank, s in enumerate(items, 1):
        rows.append({"rank": rank, "id": s.deal.id, "product": s.deal.product, "price": s.deal.price,
                     "age_days": s.age_days, "stale": s.stale, "outcome": _outcome(s, d)})
    wins = sum(1 for r in rows if r["outcome"]["kind"] == "venda")
    revenue = sum(r["outcome"]["value"] for r in rows if r["outcome"]["kind"] == "venda")
    return {"title": title, "wins": wins, "revenue": revenue,
            "total_label": "%s · %s" % (fmt.plural(wins, "venda"), fmt.money(revenue)), "rows": rows}


def _realized(items: Sequence[ScoredDeal], d: date) -> Dict[str, int]:
    sales = [_sale(s, d) for s in items]
    return {"wins": sum(y for y, _ in sales), "revenue": sum(v for _, v in sales)}


def _compare(score: float, ref: float) -> int:
    """-1, 0 ou 1 comparando receitas arredondadas ao dólar."""
    a, b = int(round(score)), int(round(ref))
    return (a > b) - (a < b)


def _fair_verdict(score: Dict[str, int], low: float, mean: float, high: float) -> str:
    vs_high, vs_mean, vs_low = (_compare(score["revenue"], v) for v in (high, mean, low))
    if vs_high > 0:
        return "acima até do melhor desempate"
    if vs_high == 0:
        return "igual ao melhor desempate"
    if vs_mean > 0:
        return "acima da média, abaixo do melhor desempate"
    if vs_mean == 0:
        return "igual à média, abaixo do melhor desempate"
    if vs_low > 0:
        return "abaixo da média, acima do pior desempate"
    return "igual ao pior desempate" if vs_low == 0 else "abaixo até do pior desempate"


def _fair(mine: Sequence[ScoredDeal], d: date, score: Dict[str, int]) -> Dict[str, Any]:
    by_price = sorted(mine, key=lambda s: (s.stale, -s.deal.price, -s.age_days, s.deal.id))
    oldest = _realized(by_price[:TOP_N], d)
    newest = _realized(sorted(mine, key=lambda s: (s.stale, -s.deal.price, s.age_days, s.deal.id))[:TOP_N], d)
    exp_wins, exp_revenue = _expected_top(mine, lambda s: (not s.stale, s.deal.price), d, TOP_N)
    out = {"oldest_first": oldest, "newest_first": newest,
           "expected": {"wins": exp_wins, "revenue": exp_revenue}, "title": FAIR_TITLE}
    if not mine:
        out["sentence"] = "Nenhum deal aberto nesta data."
        return out
    score_part = "O score fez %s e %s" % (fmt.plural(score["wins"], "venda"), fmt.money(score["revenue"]))
    same = oldest == newest and abs(exp_wins - oldest["wins"]) < 1e-9 and _compare(exp_revenue, oldest["revenue"]) == 0
    if same:
        verdict = ("igual à", "acima da", "abaixo da")[_compare(score["revenue"], exp_revenue)] + " regra simples"
    else:
        revenues = (oldest["revenue"], newest["revenue"], exp_revenue)
        verdict = _fair_verdict(score, min(revenues), exp_revenue, max(revenues))
    # o veredito compara receita; se a contagem de vendas aponta para outro lado, a frase diz isso
    wins_side = (score["wins"] > exp_wins) - (score["wins"] < exp_wins)
    if wins_side != _compare(score["revenue"], exp_revenue):
        verdict = "em receita, " + verdict
    if same:
        out["sentence"] = ("Entre deals do mesmo preço, a ordem não muda o resultado: %s (%s). %s: %s." % (
            fmt.plural(oldest["wins"], "venda"), fmt.money(oldest["revenue"]), score_part, verdict))
        return out
    out["sentence"] = (
        "Depende de quem vem primeiro entre deals do mesmo preço: %s com o mais antigo na frente, %s com o mais "
        "novo e %s em média no sorteio (%s). %s: %s." % (
            fmt.plural(oldest["wins"], "venda"), fmt.number(newest["wins"]), fmt.number(exp_wins, 1),
            fmt.money(exp_revenue), score_part, verdict))
    return out


def _window(ds: Dataset, d: date) -> Dict[str, Any]:
    last = d + timedelta(days=HORIZON_DAYS - 1)
    note = "Venda mostra o valor fechado no CRM."
    if last > ds.end_date:
        gap = (ds.end_date - d).days
        return {"days": gap, "truncated": True, "until": ds.end_date.isoformat(),
                "until_label": fmt.date_label(ds.end_date),
                "sentence": "Desfecho real até %s, último dia da base: %s depois. %s" % (
                    fmt.date_label(ds.end_date), fmt.days(gap), note)}
    return {"days": HORIZON_DAYS, "truncated": False, "until": last.isoformat(), "until_label": fmt.date_label(last),
            "sentence": "Desfecho real nos %d dias seguintes, até %s. %s" % (HORIZON_DAYS, fmt.date_label(last), note)}


def time_machine(ds: Dataset, d: date, name: str) -> Dict[str, Any]:
    """Top 10 de um vendedor numa data passada, pelo score e só por valor, com o desfecho real anexado."""
    seller = resolve_working_seller(ds, name)
    snap = snapshot(ds, d)
    mine = snap.by_seller.get(seller, ())
    score_list = _tm_list("Pelo score", mine[:TOP_N], d)
    by_value = sorted(mine, key=stale_key)[:TOP_N]
    score_result = {"wins": score_list["wins"], "revenue": score_list["revenue"]}
    return {
        "seller": person_dict(ds, seller),
        "date": date_dict(d),
        "enough": len(mine) >= TOP_N,
        "open_count": len(mine),
        "window": _window(ds, d),
        "lists": {"score": score_list, "value_only": _tm_list("Só por valor", by_value, d)},
        "fair": _fair(mine, d, score_result),
        "hidden_account_note": dict(HIDDEN_ACCOUNT_NOTE),
    }
