"""Tela "Meu time": visão do gestor sobre a carteira de cada vendedor numa segunda-feira.

Só usa o que se sabia na data: deals abertos do retrato e fechamentos anteriores à data.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Any, Dict, List, Optional, Sequence

from engine import fmt
from engine.core import REGION_LABELS, Dataset, InputError, ScoredDeal, Snapshot, closing_is_strong, phase_title, \
    resolve_manager, resolve_region, resolve_working_seller, select_sellers, snapshot, summarize, win_record
from engine.shapes import date_dict, person_dict
TOP_DECISION = 3
TOP_INDICATOR = 3
TOP_MOMENT = 2
STALE_FIRST_BATCH = 10


def team(ds: Dataset, d: date, manager: Optional[str] = None, region: Optional[str] = None,
         seller: Optional[str] = None) -> Dict[str, Any]:
    """Resumo, linhas por vendedor, pauta da Gabi e mensagens prontas para o escopo escolhido."""
    scope = _scope(ds, manager or None, region or None, seller or None)
    snap = snapshot(ds, d)
    names = [n for n in select_sellers(ds, scope["manager"], scope["region"], scope["seller"])
             if n in ds.deals_by_seller]
    rows = sorted((_row(ds, snap, n) for n in names), key=lambda r: (-r["declared_value"], r["name"]))
    total = summarize(snap.for_sellers(names))
    summary = {
        "seller_count": len(rows),
        "open_count": total["open"],
        "live_count": total["live"],
        "stale_count": total["stale"],
        "declared_value": total["declared_value"],
        "live_value": total["live_value"],
        "stale_value": total["stale_value"],
        "expected_30d": round(total["expected_value"], 2),
        "live_share": _fraction(total["live_value"], total["declared_value"]),
        "stale_share": _fraction(total["stale_value"], total["declared_value"]),
        "hot_count": total["hot"],
        "headline": "Declarado: %s. Ainda vivo: %s." % (fmt.money(total["declared_value"]),
                                                         fmt.money(total["live_value"])),
    }
    place = _place(scope)
    return {
        "scope": scope,
        "options": _options(ds, scope),
        "date": date_dict(d),
        "summary": summary,
        "rows": rows,
        "agenda": [_decision_card(snap, rows, place), _indicator_card(rows), _moment_card(snap, rows, summary, place)],
        "messages": [{"seller": r["name"], "first_name": r["first_name"], "initials": r["initials"],
                      "text": _message(snap, r)} for r in rows],
    }


# ---------------------------------------------------------------- escopo

def _scope(ds: Dataset, manager: Optional[str], region: Optional[str], seller: Optional[str]) -> Dict[str, Any]:
    """Valida a combinação de filtros; InputError (em português) se ela for impossível."""
    region = resolve_region(ds, region) if region else None
    manager = resolve_manager(ds, manager) if manager else None
    seller = resolve_working_seller(ds, seller) if seller else None
    if manager and region and manager not in ds.regions[region]:
        raise InputError("%s não é gestor da regional %s." % (manager, REGION_LABELS[region]))
    if seller:
        info = ds.sellers[seller]
        if manager and info.manager != manager:
            raise InputError("%s não é do time de %s." % (seller, manager))
        if region and info.region != region:
            raise InputError("%s não é da regional %s." % (seller, REGION_LABELS[region]))
    if seller:
        title = "Carteira de %s" % seller
    elif manager:
        title = "Time de %s" % manager
    elif region:
        title = "Regional %s" % REGION_LABELS[region]
    else:
        title = "Empresa"
    return {"region": region, "region_label": REGION_LABELS[region] if region else None,
            "manager": manager, "seller": seller, "title": title}


def _options(ds: Dataset, scope: Dict[str, Any]) -> Dict[str, Any]:
    regions = [scope["region"]] if scope["region"] else list(REGION_LABELS)
    managers = sorted((m, r) for r in regions for m in ds.regions[r])
    sellers = [n for n in select_sellers(ds, scope["manager"], scope["region"]) if n in ds.deals_by_seller]
    return {
        "regions": [{"key": k, "label": v} for k, v in REGION_LABELS.items()],
        "managers": [{"name": m, "region": r, "region_label": REGION_LABELS[r]} for m, r in managers],
        "sellers": sellers,
    }


def _place(scope: Dict[str, Any]) -> str:
    """Onde estão os deals, para os títulos: "no time", "na regional"..."""
    if scope["seller"]:
        return "na carteira"
    if scope["manager"]:
        return "no time"
    return "na regional" if scope["region"] else "na empresa"


# ---------------------------------------------------------------- linhas

def _row(ds: Dataset, snap: Snapshot, name: str) -> Dict[str, Any]:
    person = person_dict(ds, name)
    s = summarize(snap.by_seller.get(name, ()))
    rec = win_record(ds, snap, name)
    delta = 0.0
    if rec.official_rate is not None and rec.rate_with_stale is not None:
        delta = round(100.0 * (rec.official_rate - rec.rate_with_stale), 2)
    return {
        "name": name,
        "first_name": person["first_name"],
        "initials": person["initials"],
        "region_label": person["region_label"],
        "manager": person["manager"],
        "open_count": s["open"],
        "live_count": s["live"],
        "stale_count": s["stale"],
        "hot_count": s["hot"],
        "declared_value": s["declared_value"],
        "live_value": s["live_value"],
        "expected_30d": round(s["expected_value"], 2),
        "won": rec.won,
        "lost": rec.lost,
        "rate_official": rec.official_rate,
        "rate_with_stale": rec.rate_with_stale,
        "rate_delta_points": delta,
        "stale_label": "%s sem desfecho" % fmt.number(s["stale"]),
    }


def _fraction(part: float, whole: float) -> float:
    """part / whole, ou 0.0 quando whole é zero."""
    return part / float(whole) if whole else 0.0


# ---------------------------------------------------------------- pauta da Gabi

def _top(rows: List[Dict[str, Any]], field: str, limit: int) -> List[Dict[str, Any]]:
    """Os que mais têm em field (maior primeiro, depois nome), só com valor positivo."""
    ranked = sorted((r for r in rows if r[field] > 0), key=lambda r: (-r[field], r["name"]))
    return ranked[:limit]


def _share_verb(covered: int, total: int, noun: str) -> str:
    """"concentram todos", "concentram 31 desses deals" (metade ou mais) ou "têm 42 desses deals"."""
    if covered == total:
        return "concentram todos"
    verb = "concentram" if 2 * covered >= total else "têm"
    return "%s %s %s" % (verb, fmt.number(covered), noun)


def _decision_card(snap: Snapshot, rows: List[Dict[str, Any]], place: str) -> Dict[str, Any]:
    total = sum(r["stale_count"] for r in rows)
    card = {"kind": "decisao", "label": "DECISÃO", "highlight": total > 0}
    if not total:
        who = "%s não" % rows[0]["first_name"] if len(rows) == 1 else "Ninguém"
        card.update(title="Nenhum deal sem desfecho %s." % place,
                    body="%s tem deal aberto há mais de %s." % (who, fmt.days(snap.max_cycle)),
                    link_label=None, link_target=None)
        return card
    top = _top(rows, "stale_count", TOP_DECISION)
    covered = sum(r["stale_count"] for r in top)
    if total == 1:
        who = "É de %s. Peça uma decisão: confirmar com o cliente ou encerrar." % top[0]["first_name"]
    else:
        if len(top) == 1:
            lead = "Todos são de %s." % top[0]["first_name"]
        else:
            people = fmt.join("%s (%s)" % (r["first_name"], fmt.number(r["stale_count"])) for r in top)
            lead = "%s %s." % (people, _share_verb(covered, total, "deles"))
        who = lead + " Peça uma decisão por deal: confirmar com o cliente ou encerrar."
    card.update(title="%s %s uma decisão." % (fmt.plural(total, "deal sem desfecho", "deals sem desfecho"),
                                              "espera" if total == 1 else "esperam"),
                body=who,
                link_label="Ver o deal" if total == 1 else "Ver os %s deals" % fmt.number(total),
                link_target="sem_desfecho")
    return card


def _points(values: Sequence[int]) -> str:
    """Faixa de pontos já arredondados: "11 pontos", "de 11 a 14 pontos", "menos de 1 ponto"."""
    low, high = min(values), max(values)
    if high == 0:
        return "menos de 1 ponto"
    if low == high:
        return fmt.plural(high, "ponto")
    return "de %s a %s" % (fmt.number(low) if low else "menos de 1", fmt.plural(high, "ponto"))


def _shown_points(r: Dict[str, Any]) -> float:
    """Diferença das duas taxas já arredondadas a uma casa, como a coluna Taxa de ganho mostra."""
    official = math.floor(r["rate_official"] * 1000 + 0.5)
    with_stale = math.floor(r["rate_with_stale"] * 1000 + 0.5)
    return abs(official - with_stale) / 10.0


def _indicator_card(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = sum(r["stale_count"] for r in rows)
    # sem link: a conta de cada vendedor está na coluna Taxa de ganho da tabela, na mesma tela
    card = {"kind": "indicador", "label": "INDICADOR", "highlight": False,
            "link_label": None, "link_target": None}
    if not total:
        card.update(title="A taxa oficial não esconde nada aqui.",
                    body="Sem deal sem desfecho, a taxa de ganho oficial já mostra o quadro real.")
        return card
    losers = [r for r in rows if r["stale_count"] > 0]
    steady = [r for r in rows if r["stale_count"] == 0]
    if len(losers) > TOP_INDICATOR:
        cited = sorted(losers, key=lambda r: (-_shown_points(r), r["name"]))[:TOP_INDICATOR]
    else:
        cited = losers
    # o cartão manda conferir na coluna da tabela: os pontos saem da mesma conta que ela mostra
    points = [int(math.floor(_shown_points(r) + 0.5)) for r in cited]
    verb = "perde" if len(cited) == 1 else "perdem"
    rest = [r for r in losers if r not in cited]
    if rest:
        body = "%s são os que mais perdem: %s de taxa de ganho quando esses deals entram na conta." % (
            fmt.join(r["first_name"] for r in cited), _points(points))
        if len(rest) == 1:
            body += " A taxa de %s também cai." % rest[0]["first_name"]
        else:
            body += " A taxa de outros %s também cai." % fmt.plural(len(rest), "vendedor", "vendedores")
    else:
        body = "%s %s %s de taxa de ganho quando esses deals entram na conta." % (
            fmt.join(r["first_name"] for r in cited), verb, _points(points))
    if steady:
        if len(steady) == 1:
            body += " %s não tem nenhum, e a taxa não muda." % steady[0]["first_name"]
        elif len(steady) <= TOP_INDICATOR:
            body += " %s não têm nenhum, e a deles não muda." % fmt.join(r["first_name"] for r in steady)
        else:
            body += " %s não têm nenhum, e a taxa deles não muda." % fmt.plural(
                len(steady), "vendedor", "vendedores")
    body += " A conta %sestá na coluna Taxa de ganho." % ("de cada um " if len(rows) > 1 else "")
    card.update(title="A taxa oficial deixa de fora %s sem desfecho." % fmt.plural(total, "deal"), body=body)
    return card


def _moment_card(snap: Snapshot, rows: List[Dict[str, Any]], summary: Dict[str, Any],
                 place: str) -> Dict[str, Any]:
    hot = summary["hot_count"]
    phase = phase_title(snap)
    card = {"kind": "momento", "label": "MOMENTO", "highlight": False}
    body = "A receita esperada em 30 dias é %s." % fmt.money(summary["expected_30d"])
    if not hot:
        card.update(title="%s: nenhum deal quente %s." % (phase, place), body=body,
                    link_label=None, link_target=None)
        return card
    top = _top(rows, "hot_count", TOP_MOMENT)
    covered = sum(r["hot_count"] for r in top)
    if len(rows) > 1:
        if len(top) == 1:
            body += " %s %s." % ("Todos são de" if hot > 1 else "É de", top[0]["first_name"])
        else:
            body += " %s %s." % (fmt.join(r["first_name"] for r in top), _share_verb(covered, hot, "desses deals"))
    card.update(title="%s: %s %s." % (phase, fmt.plural(hot, "deal quente", "deals quentes"), place),
                body=body,
                link_label="Ver o deal" if hot == 1 else "Ver os %s" % fmt.number(hot),
                link_target="quentes")
    return card


# ---------------------------------------------------------------- mensagens

def _phase_sentence(snap: Snapshot) -> str:
    month = fmt.month_name(snap.date).capitalize()
    if snap.quarter_phase == "fecha":
        return ("%s é mês de fechar." if closing_is_strong(snap) else "%s fecha o trimestre.") % month
    if snap.quarter_phase == "abre":
        return "%s abre o trimestre." % month
    return "Estamos no meio do trimestre."


def _deal_ref(s: ScoredDeal) -> str:
    return "#%s (%s, %s)" % (s.deal.id, s.deal.product, fmt.days(s.age_days))


def _message(snap: Snapshot, row: Dict[str, Any]) -> str:
    """Mensagem do gestor para o vendedor: prioridades da semana e os deals sem desfecho."""
    items = snap.by_seller.get(row["name"], ())
    live = [s for s in items if not s.stale][:3]
    stale = row["stale_count"]
    parts = ["%s, bom dia." % row["first_name"], _phase_sentence(snap)]
    if len(live) == 1:
        parts.append("Seu deal de maior prioridade esta semana: %s." % _deal_ref(live[0]))
    elif live:
        parts.append("Seus %d deals de maior prioridade esta semana: %s." % (
            len(live), fmt.join(_deal_ref(s) for s in live)))
    elif stale:
        parts.append("Você não tem deal vivo esta semana.")
    else:
        parts.append("Você não tem deal aberto esta semana.")
        return " ".join(parts)
    if not stale:
        parts.append("Você não tem deal sem desfecho: siga a ordem do score.")
        return " ".join(parts)
    also = " também" if live else ""
    old = fmt.days(snap.max_cycle)
    if stale == 1:
        parts.append("Você%s tem 1 deal aberto há mais de %s. Me diga até sexta se ele segue de pé "
                     "ou se vamos encerrar." % (also, old))
        return " ".join(parts)
    parts.append("Você%s tem %s abertos há mais de %s." % (also, fmt.plural(stale, "deal"), old))
    if stale >= STALE_FIRST_BATCH:
        parts.append("Comece pelos %d de maior valor e me diga até sexta quais seguem de pé "
                     "e quais vamos encerrar." % STALE_FIRST_BATCH)
    else:
        parts.append("Me diga até sexta quais seguem de pé e quais vamos encerrar.")
    return " ".join(parts)
