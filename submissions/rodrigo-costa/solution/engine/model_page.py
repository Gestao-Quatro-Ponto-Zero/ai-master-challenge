"""Tela "Como o score funciona": exemplo de cálculo, tabela de chance da data, faixas e sinais testados.

A tabela de sinais testados descreve a base inteira (deals fechados) de propósito e diz isso no texto.
"""
from __future__ import annotations

import math
import threading
import weakref
from collections import defaultdict
from datetime import date, timedelta
from statistics import median
from typing import Any, Dict, List, Optional, Sequence, Tuple

from engine import fmt
from engine.core import (HORIZON_DAYS, HOT_MIN, LEVEL_LABELS, MIN_CELL, SCORE_BAND_LABELS, WARM_MIN, Dataset, Deal,
                         ScoredDeal, Snapshot, available_dates, home_region, snapshot, win_rate)
from engine.shapes import date_dict, viewer_scope

HISTORY_FIRST = date(2017, 4, 1)  # um mês depois do primeiro fechamento: antes disso não há histórico a olhar
COUNT_WORDS = {1: "um", 2: "dois", 3: "três", 4: "quatro", 5: "cinco", 6: "seis"}


# ---------------------------------------------------------------- utilidades de texto

def _days_list(days: Sequence[date]) -> str:
    """"6 mar, 5 jun e 4 set 2017" (ano uma vez só quando todas são do mesmo ano)."""
    if len({d.year for d in days}) == 1:
        return "%s %d" % (fmt.join([fmt.day_month(d) for d in days]), days[0].year)
    return fmt.join([fmt.date_label(d) for d in days])


def _more_or_less(frac: float) -> str:
    """"42% mais" ou "5% menos"."""
    return "%s %s" % (fmt.pct(abs(frac)), "mais" if frac >= 0 else "menos")


# ---------------------------------------------------------------- exemplo

def _chance_sentence(s: ScoredDeal, band_label: str) -> str:
    where = {
        "semana": "Na faixa de %s dias, na mesma semana do trimestre," % band_label,
        "mes": "Na faixa de %s dias, no mesmo mês do trimestre," % band_label,
        "idade": "Na faixa de %s dias," % band_label,
        "geral": "Somando todas as faixas,",
    }[s.level]
    return "%s %s de %s viraram venda em até %d dias: chance de %s." % (
        where, fmt.number(s.y), fmt.plural(s.n, "caso"), HORIZON_DAYS, fmt.pct(s.chance))


def _example(ds: Dataset, snap: Snapshot, viewer: Optional[str]) -> Optional[Dict[str, Any]]:
    name, sellers = viewer_scope(ds, viewer)
    mine = [s for s in snap.for_sellers(sellers) if not s.stale]
    s = mine[0] if mine else (snap.live[0] if snap.live else None)
    if s is None:
        return None
    band = snap.bands[s.age_band]
    total = len(snap.live)
    note = None
    if name is not None and not mine:
        note = "%s não tem deal vivo nesta data. O exemplo é o primeiro da empresa." % name
    steps = [
        "O deal tem %s: está na faixa de %s dias." % (fmt.days(s.age_days), band.label),
        _chance_sentence(s, band.label),
        "Receita esperada: %s ÷ %s × %s (preço de tabela) = %s." % (
            fmt.number(s.y), fmt.number(s.n), fmt.money(s.deal.price), fmt.money(s.expected_value)),
        "Essa receita esperada é igual ou maior que a de %s dos %s da empresa: score %d." % (
            fmt.pct(s.score / 100.0), fmt.plural(total, "deal vivo", "deals vivos"), s.score),
    ]
    return {
        "id": s.deal.id,
        "product": s.deal.product,
        "price": s.deal.price,
        "seller": s.deal.seller,
        "age_days": s.age_days,
        "age_band": band.label,
        "chance": s.chance,
        "y": s.y,
        "n": s.n,
        "level": s.level,
        "level_label": LEVEL_LABELS[s.level],
        "expected_value": round(s.expected_value, 2),
        "score": s.score,
        "band": s.score_band,
        "band_label": SCORE_BAND_LABELS[s.score_band],
        "live_count": total,
        "is_viewer": bool(mine),
        "note": note,
        "steps": steps,
    }


# ---------------------------------------------------------------- tabela e treino

def _table(snap: Snapshot) -> List[Dict[str, Any]]:
    w = snap.window
    rows = []
    for b in snap.bands:
        rows.append({
            "label": b.label,
            "from_days": b.min_age,
            "to_days": b.max_age,
            "chance": b.chance,
            "chance_label": fmt.pct(b.chance),
            "n": b.n,
            "y": b.y,
            "level": b.level,
            "level_label": LEVEL_LABELS[b.level],
            "in_window": w is not None and w.first_band <= b.index <= w.last_band,
            "stale": b.min_age > snap.max_cycle,
        })
    return rows


def _table_sentence(snap: Snapshot) -> str:
    text = "Tabela usada na semana de %s." % fmt.date_label(snap.date)
    if snap.window is not None:
        text += " A janela boa vai de %s." % snap.window.label
    return text


FALLBACK_TEXT = {
    "mes": "a semana tinha menos de %d casos; a taxa usa o mesmo mês do trimestre." % MIN_CELL,
    "idade": "a semana e o mês tinham menos de %d casos; a taxa usa todas as segundas anteriores." % MIN_CELL,
    "geral": "nem somando todas as segundas havia %d casos; a taxa é a geral, de todas as faixas juntas." % MIN_CELL,
}


def _training(snap: Snapshot) -> Dict[str, Any]:
    weeks = snap.model.week_mondays
    text = "Embaixo de cada faixa, em dias de idade, está o número de casos que formam a taxa."
    if len(weeks) == 1:
        text += " Eles vêm da mesma semana do trimestre anterior (%s)." % _days_list(weeks)
    elif weeks:
        text += " Eles vêm da mesma semana dos %s trimestres anteriores (%s)." % (
            COUNT_WORDS.get(len(weeks), str(len(weeks))), _days_list(weeks))
    else:
        text += " Nenhum trimestre anterior tem esta mesma semana com dados."
    by_level: Dict[str, List[str]] = defaultdict(list)
    for b in snap.bands:
        if b.level != "semana":
            by_level[b.level].append(b.label)
    for level in ("mes", "idade", "geral"):
        labels = by_level.get(level)
        if labels:
            lead = "Na faixa %s, " % labels[0] if len(labels) == 1 else "Nas faixas %s, " % fmt.join(labels)
            text += " " + lead + FALLBACK_TEXT[level]
    return {"mondays": [date_dict(m) for m in weeks], "sentence": text}


def _bands(snap: Snapshot) -> Dict[str, Any]:
    return {
        "score": [
            {"key": "quente", "label": SCORE_BAND_LABELS["quente"], "rule": "score %d ou mais" % HOT_MIN},
            {"key": "morno", "label": SCORE_BAND_LABELS["morno"], "rule": "de %d a %d" % (WARM_MIN, HOT_MIN - 1)},
            {"key": "frio", "label": SCORE_BAND_LABELS["frio"], "rule": "abaixo de %d" % WARM_MIN},
        ],
        "stale": {
            "label": SCORE_BAND_LABELS["sem_desfecho"],
            "rule": "mais de %s" % fmt.days(snap.max_cycle),
            "text": "Antes de %s, nenhum deal fechou com mais de %s de negociação. Sai da fila e pede uma "
                    "decisão: segue de pé ou encerra." % (fmt.date_label(snap.date), fmt.days(snap.max_cycle)),
        },
    }


# ---------------------------------------------------------------- prova (módulo engine.proof)

def _proof_block(ds: Dataset) -> Dict[str, Any]:
    from engine.proof import proof  # tardio: módulo da prova é independente desta tela

    p = proof(ds)
    g_value, g_simple = p["gains"]["vs_value_only"], p["gains"]["vs_value_no_stale"]
    sentence = None
    if g_value is not None and g_simple is not None:
        sentence = ("Em %s, %s, os %d primeiros do score de cada vendedor somaram %s receita em %d dias que os %d "
                    "primeiros por valor, e %s que por valor já sem os deals sem desfecho." % (
                        fmt.plural(p["n_dates"], "segunda-feira", "segundas-feiras"), p["period_label"],
                        p["top_n"], _more_or_less(g_value), HORIZON_DAYS, p["top_n"], _more_or_less(g_simple)))
    return {"gain_vs_value_only": g_value, "gain_vs_value_no_stale": g_simple, "n_dates": p["n_dates"],
            "top_n": p["top_n"], "sentence": sentence}


# ---------------------------------------------------------------- tela

def score_model(ds: Dataset, d: date, viewer: Optional[str] = None) -> Dict[str, Any]:
    """Tela "Como o score funciona" na data d. viewer: vendedor (ou gestor) para escolher o exemplo."""
    snap = snapshot(ds, d)
    return {
        "date": date_dict(d),
        "example": _example(ds, snap, viewer),
        "table": _table(snap),
        "table_sentence": _table_sentence(snap),
        "training": _training(snap),
        "bands": _bands(snap),
        "max_cycle": snap.max_cycle,
        "signals": tested_signals(ds),
        "proof": _proof_block(ds),
    }


# ---------------------------------------------------------------- sinais testados (base inteira)

def _rate(deals: Sequence[Deal]) -> Optional[float]:
    """Taxa de ganho oficial de uma lista de deals fechados."""
    return win_rate(sum(1 for x in deals if x.won), sum(1 for x in deals if x.lost))


def _windows(ds: Dataset) -> Tuple[date, date]:
    """Janela limpa: do primeiro fechamento até o fim da base menos o maior ciclo (antes disso não há
    fechamentos; depois, os deals ainda não tiveram tempo de fechar)."""
    longest = ds.max_cycle_before(ds.end_date + timedelta(days=1))
    return ds.closed[0].close_date, ds.end_date - timedelta(days=longest)


def _revenue_signal(ds: Dataset, cutoff: date) -> Dict[str, Any]:
    accounts = sorted(ds.accounts.values(), key=lambda a: (a.revenue, a.name))
    third = {a.name: i * 3 // len(accounts) for i, a in enumerate(accounts)}
    rates = [_rate([x for x in ds.closed if third[x.account] == t]) for t in range(3)]
    mature = [x for x in ds.dated if x.account and x.engage_date < cutoff]
    stale = []
    for t in (0, 2):
        group = [x for x in mature if third[x.account] == t]
        stale.append(sum(1 for x in group if x.close_date is None) / float(len(group)))
    return {
        "key": "revenue",
        "signal": "Faturamento e porte do cliente",
        "finding": "Entre os fechados, a taxa de ganho não muda com o porte. Entre os abertos aparecia um sinal "
                   "(cliente menor, mais deals sem desfecho), mas era efeito do cliente trocado.",
        "decision": "Fora",
        "evidence": "Fechados da base inteira, por terço de faturamento do cliente (menor, meio, maior): %s de "
                    "ganho. Deals com cliente que entraram até %s: ficaram sem desfecho %s no terço menor "
                    "e %s no maior." % (fmt.join([fmt.pct1(r) for r in rates]), fmt.date_label(cutoff - timedelta(days=1)),
                                        fmt.pct1(stale[0]), fmt.pct1(stale[1])),
    }


def _history_signal(ds: Dataset, cutoff: date) -> Dict[str, Any]:
    wins: Dict[Tuple[str, str], List[date]] = defaultdict(list)
    for x in ds.closed:
        if x.won:
            wins[(x.seller, x.account)].append(x.close_date)

    def sold_before(x: Deal) -> bool:  # só vendas fechadas antes de o deal entrar
        return any(c < x.engage_date for c in wins.get((x.seller, x.account), ()))

    cohort = [x for x in ds.dated if x.account and HISTORY_FIRST <= x.engage_date < cutoff]
    closed = [x for x in cohort if x.close_date is not None]
    yes = [x for x in closed if sold_before(x)]
    no = [x for x in closed if not sold_before(x)]
    stale_yes = [x for x in cohort if sold_before(x)]
    stale_no = [x for x in cohort if not sold_before(x)]
    home = {a: home_region(ds.closed_before(ds.end_date + timedelta(days=1), account=a)) for a in ds.accounts}
    open_acc = [x for x in ds.deals if x.close_date is None and x.account]
    match_open = sum(1 for x in open_acc if home[x.account] == x.region) / float(len(open_acc))
    match_closed = sum(1 for x in ds.closed if home[x.account] == x.region) / float(len(ds.closed))
    return {
        "key": "history",
        "signal": "Histórico de compras do cliente",
        "finding": "\"Vendedor que nunca vendeu para este cliente\" parecia um alerta forte. Vinha do mesmo "
                   "defeito: o cliente dos deals abertos não é confiável.",
        "decision": "Fora",
        "evidence": "Deals com cliente que entraram de %s a %s: ficaram sem desfecho %s quando o vendedor nunca "
                    "tinha vendido para o cliente e %s quando já tinha. Entre os que fecharam desse mesmo grupo, a taxa "
                    "de ganho é %s com venda anterior (%s) e %s sem (%s). O cliente do deal aberto é da regional do vendedor "
                    "em %s dos casos; no fechado, em %s." % (
                        fmt.day_month(HISTORY_FIRST), fmt.date_label(cutoff - timedelta(days=1)),
                        fmt.pct1(sum(1 for x in stale_no if x.close_date is None) / float(len(stale_no))),
                        fmt.pct1(sum(1 for x in stale_yes if x.close_date is None) / float(len(stale_yes))),
                        fmt.pct1(_rate(yes)), fmt.plural(len(yes), "deal"),
                        fmt.pct1(_rate(no)), fmt.plural(len(no), "deal"),
                        fmt.pct1(match_open), fmt.pct1(match_closed)),
    }


def _product_signal(ds: Dataset, first: date, cutoff: date) -> Dict[str, Any]:
    wins = [x for x in ds.closed if x.won and first <= x.engage_date < cutoff]
    rows = []
    for p in sorted(ds.products.values(), key=lambda p: (p.price, p.name)):
        cycles = [x.cycle_days for x in wins if x.product == p.name]
        if cycles:
            rows.append((p.name, int(math.floor(median(cycles) + 0.5)), len(cycles)))
    solid = [r for r in rows if r[2] >= MIN_CELL]
    few = [r for r in rows if r[2] < MIN_CELL]
    finding = ("O tempo de fechamento não muda de um produto para outro: as medianas ficam entre %d e %d dias."
               % (min(r[1] for r in solid), max(r[1] for r in solid)))
    if few:
        if len(few) == 1:
            finding += " Só o %s foge (%s), mas tem apenas %s." % (
                few[0][0], fmt.days(few[0][1]), fmt.plural(few[0][2], "venda"))
        else:
            finding += " Fogem %s, mas com poucas vendas." % fmt.join(
                ["o %s (%s, %s)" % (r[0], fmt.days(r[1]), fmt.plural(r[2], "venda")) for r in few])
    parts = ["%s %d" % (r[0], r[1]) for r in solid] + ["%s %d (%s)" % (r[0], r[1], fmt.plural(r[2], "venda"))
                                                        for r in few]
    return {
        "key": "product",
        "signal": "Produto",
        "finding": finding,
        "decision": "Entra só pelo preço",
        "evidence": "Vendas de deals que entraram de %s a %s, mediana de dias até fechar: %s." % (
            fmt.day_month(first), fmt.date_label(cutoff - timedelta(days=1)), fmt.join(parts)),
    }


def _group_rates(deals: Sequence[Deal], key) -> List[float]:
    groups: Dict[str, List[Deal]] = defaultdict(list)
    for x in deals:
        groups[key(x)].append(x)
    return sorted(_rate(v) for v in groups.values())


def _groups_signal(ds: Dataset) -> Dict[str, Any]:
    parts = []
    for label, key in (("setor", lambda x: ds.accounts[x.account].sector), ("regional", lambda x: x.region),
                       ("gestor", lambda x: x.manager)):
        rates = _group_rates(ds.closed, key)
        parts.append("%s de %s a %s" % (label, fmt.pct1(rates[0]), fmt.pct1(rates[-1])))
    return {
        "key": "groups",
        "signal": "Setor, regional e gestor",
        "finding": "A taxa de ganho é praticamente a mesma em todos os grupos.",
        "decision": "Fora",
        "evidence": "Fechados da base inteira, taxa de ganho do menor ao maior grupo: %s." % "; ".join(parts),
    }


def _seller_signal(ds: Dataset) -> Dict[str, Any]:
    groups: Dict[str, List[Deal]] = defaultdict(list)
    for x in ds.closed:
        groups[x.seller].append(x)
    overall = _rate(ds.closed)
    rates, outside = [], 0
    for deals in groups.values():
        r = _rate(deals)
        rates.append(r)
        # fora de 2 desvios-padrão binomiais da taxa da empresa
        if abs(r - overall) > 2 * math.sqrt(overall * (1 - overall) / len(deals)):
            outside += 1
    expected = len(groups) * math.erfc(2 / math.sqrt(2))
    low, high = int(math.floor(expected)), int(math.ceil(expected))
    chance_text = fmt.plural(low, "caso") if low == high else "%d ou %s" % (low, fmt.plural(high, "caso"))
    return {
        "key": "seller",
        "signal": "Vendedor",
        "finding": "As diferenças de taxa de ganho entre vendedores são do tamanho que o acaso explica. Um "
                   "score que punisse o vendedor seria injusto e inútil.",
        "decision": "Fora",
        "evidence": "Fechados da base inteira: a taxa vai de %s a %s entre os %s (empresa: %s). %s longe "
                    "da média da empresa a ponto de chamar atenção, e o acaso sozinho já daria %s assim." % (
                        fmt.pct1(min(rates)), fmt.pct1(max(rates)), fmt.plural(len(groups), "vendedor", "vendedores"),
                        fmt.pct1(overall),
                        "Nenhum fica" if outside == 0 else "Só %s %s" % (
                            fmt.plural(outside, "vendedor", "vendedores"), fmt.plural_word(outside, "fica", "ficam")),
                        chance_text),
    }


def _account_field_signal(ds: Dataset) -> Dict[str, Any]:
    open_deals = [x for x in ds.deals if x.close_date is None]
    with_acc = sum(1 for x in open_deals if x.account)
    closed_with = sum(1 for x in ds.closed if x.account)
    frac = with_acc / float(len(open_deals))
    counts = {True: [0, 0], False: [0, 0]}  # tem cliente -> [vendas em 30 dias, casos]
    dates = [d for d in available_dates(ds) if d + timedelta(days=HORIZON_DAYS) <= ds.end_date]
    for d in dates:
        limit = d + timedelta(days=HORIZON_DAYS)
        for s in snapshot(ds, d).live:
            cell = counts[s.deal.account is not None]
            cell[1] += 1
            cell[0] += int(s.deal.won and s.deal.close_date < limit)
    sold_no, cases_no = counts[False]
    sold_yes, cases_yes = counts[True]
    if sold_no == 0:
        no_text = "nenhum dos %s de deal vivo sem cliente virou venda em %d dias" % (
            fmt.plural(cases_no, "caso"), HORIZON_DAYS)
    else:
        no_text = "%s dos casos de deal vivo sem cliente viraram venda em %d dias" % (
            fmt.pct1(sold_no / float(cases_no)), HORIZON_DAYS)
    one_in = int(round(1 / frac)) if frac else 0
    share = "só um em cada %s" % COUNT_WORDS[one_in] if one_in in COUNT_WORDS and one_in > 1 else \
        "só %s" % fmt.pct(frac)
    return {
        "key": "account_field",
        "signal": "Ter cliente no cadastro",
        "finding": "Todo deal fechado tem cliente; dos que seguem abertos no fim da base, %s. Numa data simulada, o campo adianta quem vai "
                   "fechar. Usar isso seria trapaça." % share,
        "decision": "Fora, por vazamento",
        "evidence": "Na base inteira, %s fechados têm cliente; dos %s, %s (%s). Em %s, de %s a %s, %s; com "
                    "cliente, %s viraram." % (
                        "todos os %s" % fmt.number(closed_with) if closed_with == len(ds.closed) else
                        "%s de %s" % (fmt.number(closed_with), fmt.number(len(ds.closed))),
                        fmt.plural(len(open_deals), "aberto"), fmt.number(with_acc), fmt.pct1(frac),
                        fmt.plural(len(dates), "segunda-feira", "segundas-feiras"), fmt.day_month(dates[0]),
                        fmt.date_label(dates[-1]), no_text,
                        fmt.pct1(sold_yes / float(cases_yes))),
    }


def _build_signals(ds: Dataset) -> List[Dict[str, Any]]:
    first, cutoff = _windows(ds)
    return [_revenue_signal(ds, cutoff), _history_signal(ds, cutoff), _product_signal(ds, first, cutoff),
            _groups_signal(ds), _seller_signal(ds), _account_field_signal(ds)]


_SIGNALS: "weakref.WeakKeyDictionary[Dataset, List[Dict[str, Any]]]" = weakref.WeakKeyDictionary()
_SIGNALS_LOCK = threading.Lock()


def tested_signals(ds: Dataset) -> List[Dict[str, Any]]:
    """O que foi testado e ficou de fora do score, cada linha com o número que a sustenta (base inteira)."""
    with _SIGNALS_LOCK:
        rows = _SIGNALS.get(ds)
        if rows is None:
            rows = _SIGNALS[ds] = _build_signals(ds)
        return [dict(r) for r in rows]
