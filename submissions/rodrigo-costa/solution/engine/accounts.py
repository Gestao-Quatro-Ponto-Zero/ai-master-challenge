"""Tela "Clientes": lista por regional e ficha de um cliente numa data.

O histórico do cliente usa só deals fechados antes da data. O campo account dos deals abertos é mostrado
como está na base, mas não entra em chance, score nem ordenação.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple

from engine import fmt
from engine.core import REGION_LABELS, Dataset, Deal, home_region, resolve_account, resolve_region, snapshot, \
    summarize, win_rate
from engine.shapes import closed_deal_dict, date_dict, open_deal_dict, viewer_scope

LISTING_NOTE = ("Ordenado por valor ganho até %s. A taxa de ganho muda pouco de um cliente para outro, "
                "nada além do que o acaso explica, por isso não entra no score.")
HOME_REGION_NOTE = ("A regional de casa é a que mais fechou deals com o cliente até a véspera da data. "
                    "Num cliente dividido entre regionais, ela pode mudar de uma semana para outra.")
DETAIL_NOTE = ("Porte e histórico descrevem o cliente, mas não entram no score. "
               "Foram testados e não mudam a chance de fechar nesta base.")
WARNING_TITLE = "O cliente de um deal aberto não é confiável nesta base"
QUARTER_END_MONTHS = (3, 6, 9, 12)
QUARTER_END_LIFT = 1.5  # só fala em "ritmo de fim de trimestre" se esses meses vendem 50% mais, em média


# ---------------------------------------------------------------- histórico

def _history(ds: Dataset, d: date, name: str) -> Tuple[Deal, ...]:
    return ds.closed_before(d, account=name)


def _stats(closed: Sequence[Deal]) -> Dict[str, Any]:
    won = [x for x in closed if x.won]
    last = max((x.close_date for x in won), default=None)
    return {
        "closed_count": len(closed),
        "won_count": len(won),
        "lost_count": sum(1 for x in closed if x.lost),
        "won_value": sum(x.close_value or 0 for x in won),
        "last_sale": last,
    }


def _home_by_account(ds: Dataset, d: date) -> Dict[str, Optional[str]]:
    return {name: home_region(_history(ds, d, name)) for name in ds.accounts}


# ---------------------------------------------------------------- lista

def listing(ds: Dataset, d: date, region: Optional[str] = None) -> Dict[str, Any]:
    """Clientes da regional de casa dada (ou todos), por valor ganho decrescente e depois nome."""
    code = resolve_region(ds, region) if region else None
    homes = _home_by_account(ds, d)
    rows = []
    for name, account in ds.accounts.items():
        if code is not None and homes[name] != code:
            continue
        st = _stats(_history(ds, d, name))
        last = st["last_sale"]
        rows.append({
            "name": name,
            "sector_label": account.sector_label,
            "home_region": homes[name],
            "home_region_label": REGION_LABELS[homes[name]] if homes[name] else None,
            "closed_count": st["closed_count"],
            "won_count": st["won_count"],
            "lost_count": st["lost_count"],
            "win_rate": win_rate(st["won_count"], st["lost_count"]),
            "won_value": st["won_value"],
            "last_sale_date": last.isoformat() if last else None,
            "last_sale_label": fmt.date_in_context(last, d) if last else None,
        })
    rows.sort(key=lambda r: (-r["won_value"], r["name"]))
    count = len(rows)
    if code is None:
        title = "Clientes da empresa"
        subtitle = "%s no total." % fmt.plural(count, "cliente")
    else:
        title = "Clientes da regional %s" % REGION_LABELS[code]
        if count == 0:
            subtitle = "Nenhum cliente compra desta regional até agora."
        else:
            subtitle = "%s %s desta regional." % (fmt.plural(count, "cliente"), fmt.plural_word(count, "compra", "compram"))
    subtitle += " Os números vêm dos deals fechados, onde o cliente é confiável."
    return {
        "date": date_dict(d),
        "region": code,
        "region_label": REGION_LABELS[code] if code else None,
        "count": count,
        "title": title,
        "subtitle": subtitle,
        "accounts": rows,
        "note": LISTING_NOTE % fmt.date_label(d - timedelta(days=1)),
        "home_region_note": HOME_REGION_NOTE,
    }


# ---------------------------------------------------------------- ficha

def _headline_detail(closed: int, won: int, lost: int) -> str:
    if closed == 0:
        return "em nenhuma venda. Ainda não há deals fechados com este cliente."
    sales = "em %s." % fmt.plural(won, "venda") if won else "em nenhuma venda."
    if lost == 0:
        tail = "O deal fechado foi ganho." if closed == 1 else "Nenhum dos %s foi perdido." % fmt.plural(
            closed, "deal fechado", "deals fechados")
    elif lost == closed:
        tail = "O deal fechado foi perdido." if closed == 1 else "Os %s foram perdidos." % fmt.plural(
            closed, "deal fechado", "deals fechados")
    else:
        tail = "Dos %s, %s %s." % (fmt.plural(closed, "deal fechado", "deals fechados"), fmt.number(lost),
                                   fmt.plural_word(lost, "foi perdido", "foram perdidos"))
    return "%s %s" % (sales, tail)


def _top_products(closed: Sequence[Deal]) -> List[Dict[str, Any]]:
    count: Dict[str, int] = defaultdict(int)
    value: Dict[str, int] = defaultdict(int)
    for x in closed:
        if x.won:
            count[x.product] += 1
            value[x.product] += x.close_value or 0
    ranked = sorted(value, key=lambda p: (-value[p], p))[:3]
    top = value[ranked[0]] if ranked else 0
    return [{"product": p, "won_count": count[p], "won_value": value[p],
             "share": value[p] / float(top) if top else 0.0} for p in ranked]


def _warning(account: str, items: Sequence[Dict[str, Any]], closed: Sequence[Deal]) -> Optional[Dict[str, str]]:
    total = len(items)
    if total == 0:
        return None
    tail = "Por isso o cliente não entra no score."
    others = [i for i in items if i["other_region"]]
    if not others:
        return {"title": WARNING_TITLE,
                "body": "Nesta base, só os deals fechados têm cliente confiável. " + tail}
    k = len(others)
    sellers = {i["seller"] for i in others}
    regions = {i["region"] for i in others}
    who = "um vendedor" if len(sellers) == 1 else "vendedores"
    where = "de outra regional" if len(regions) == 1 else "de outras regionais"
    if total == 1:
        lead = "O deal abaixo está"
    elif k == total:
        lead = "Os %s abaixo estão" % fmt.number(total)
    else:
        lead = "Dos %s abaixo, %s %s" % (fmt.number(total), fmt.number(k), fmt.plural_word(k, "está", "estão"))
    body = "%s com %s %s" % (lead, who, where)
    closed_sellers = {x.seller for x in closed}
    if not sellers & closed_sellers:
        body += ", que nunca %s negócio com a %s" % (
            "fechou" if len(sellers) == 1 else "fecharam", account)
    return {"title": WARNING_TITLE, "body": body + ". " + tail}


def _month_iter(first: date, last: date) -> List[date]:
    out, m = [], date(first.year, first.month, 1)
    while m <= last:
        out.append(m)
        m = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    return out


def _by_month(ds: Dataset, d: date, closed: Sequence[Deal]) -> List[Dict[str, Any]]:
    """Vendas por mês, do primeiro mês com fechamentos na base até o mês de d (se já tem algum dia)."""
    first = ds.closed[0].close_date
    last_day = d - timedelta(days=1)
    wins = Counter((x.close_date.year, x.close_date.month) for x in closed if x.won)
    return [{"month": "%04d-%02d" % (m.year, m.month), "label": fmt.MONTHS_SHORT[m.month - 1],
             "won_count": wins[(m.year, m.month)], "quarter_end": m.month in QUARTER_END_MONTHS,
             "complete": (m.year, m.month) != (last_day.year, last_day.month) or d.day == 1}
            for m in _month_iter(first, last_day)]


def _month_sentence(d: date, months: Sequence[Dict[str, Any]], won_total: int) -> Optional[str]:
    """Só afirma o ritmo de fim de trimestre se os meses completos de fim de trimestre vendem bem mais, em média."""
    done = [m for m in months if m["complete"]]
    ends = [m for m in done if m["quarter_end"]]
    rest = [m for m in done if not m["quarter_end"]]
    if won_total == 0 or not ends or not rest:
        return None
    end_sum = sum(m["won_count"] for m in ends)
    rest_sum = sum(m["won_count"] for m in rest)
    end_mean, rest_mean = end_sum / float(len(ends)), rest_sum / float(len(rest))
    if end_sum and end_mean >= QUARTER_END_LIFT * rest_mean:
        names = [fmt.MONTHS_LONG[int(m["month"][5:]) - 1] for m in ends]
        if won_total == 1:
            month = next(n for n, m in zip(names, ends) if m["won_count"])
            text = "A única venda foi em %s, mês de fim de trimestre." % month
        else:
            part = ("todas as %s" % fmt.plural(won_total, "venda") if end_sum == won_total
                    else "%s das %s" % (fmt.number(end_sum), fmt.plural(won_total, "venda")))
            text = "%s %s %s: é o ritmo de fim de trimestre." % (
                fmt.join(names).capitalize(), "soma" if len(ends) == 1 else "somam", part)
    elif end_mean > rest_mean:
        text = "Os meses de fim de trimestre vendem só um pouco mais que os outros para este cliente."
    else:
        text = "Os meses de fim de trimestre não vendem mais que os outros para este cliente."
    current = months[-1]
    if not current["complete"]:
        last_day = d - timedelta(days=1)
        text += " %s conta só até o dia %d." % (fmt.month_name(last_day).capitalize(), last_day.day)
    return text


def detail(ds: Dataset, d: date, name: str, viewer: Optional[str] = None) -> Dict[str, Any]:
    """Ficha do cliente: porte, histórico até a véspera de d, abertos com ele no campo e fechados."""
    name = resolve_account(ds, name)
    who, viewer_sellers = viewer_scope(ds, viewer)
    mine = set(viewer_sellers)
    acc = ds.accounts[name]
    closed = _history(ds, d, name)
    home = home_region(closed)
    home_label = REGION_LABELS[home] if home else None
    st = _stats(closed)
    seller_names = {x.seller for x in closed}
    region_labels = sorted({REGION_LABELS[x.region] for x in closed})
    if not seller_names:
        sellers_label = "vendedores"
    elif len(region_labels) == 1:
        sellers_label = "%s com deal fechado, da regional %s" % (fmt.plural_word(len(seller_names), "vendedor", "vendedores"),
                                               region_labels[0])
    else:
        sellers_label = "%s com deal fechado, de %s regionais" % (fmt.plural_word(len(seller_names), "vendedor", "vendedores"),
                                                len(region_labels))
    last = st["last_sale"]
    subtitle = acc.sector_label + (" · atendido pela regional %s" % home_label if home_label else "")

    snap = snapshot(ds, d)
    live, stale = [], []
    for s in snap.deals:
        if s.deal.account != name:
            continue
        item = open_deal_dict(snap, s)
        item["is_viewer"] = s.deal.seller in mine
        item["other_region"] = home is not None and s.deal.region != home
        (stale if s.stale else live).append(item)
    items = live + stale
    totals = summarize(s for s in snap.deals if s.deal.account == name)

    months = _by_month(ds, d, closed)
    # mesma ordem das colunas Ganhos e Perdidos do pipeline: mais recente primeiro, id crescente no empate
    recent = sorted(closed, key=lambda x: (-x.close_date.toordinal(), x.id))
    deals = []
    for x in recent:
        row = closed_deal_dict(ds, x)
        row["is_viewer"] = x.seller in mine
        deals.append(row)

    return {
        "date": date_dict(d),
        "viewer": who,
        "account": {
            "name": name,
            "sector_label": acc.sector_label,
            "home_region": home,
            "home_region_label": home_label,
            "revenue": acc.revenue,
            "revenue_label": fmt.money_long(acc.revenue * 1e6),
            "employees": acc.employees,
            "year_established": acc.year_established,
            "office_label": acc.country_label,
            "parent": acc.subsidiary_of,
            "subtitle": subtitle,
            "home_region_note": HOME_REGION_NOTE,
        },
        "history": {
            "closed_count": st["closed_count"],
            "won_count": st["won_count"],
            "lost_count": st["lost_count"],
            "won_value": st["won_value"],
            "avg_ticket": st["won_value"] / float(st["won_count"]) if st["won_count"] else None,
            "last_sale_date": last.isoformat() if last else None,
            "last_sale_label": fmt.date_in_context(last, d) if last else None,
            "seller_count": len(seller_names),
            "seller_regions": region_labels,
            "headline_detail": _headline_detail(st["closed_count"], st["won_count"], st["lost_count"]),
            "sellers_label": sellers_label,
        },
        "top_products": _top_products(closed),
        "note": DETAIL_NOTE,
        "open": {
            "count": len(items),
            "live_count": len(live),
            "stale_count": len(stale),
            "live_value": totals["live_value"],
            "stale_value": totals["stale_value"],
            "other_region_count": sum(1 for i in items if i["other_region"]),
            "warning": _warning(name, items, closed),
            "live": live,
            "stale": stale,
        },
        "closed": {
            "count": st["closed_count"],
            "won_count": st["won_count"],
            "lost_count": st["lost_count"],
            "won_value": st["won_value"],
            "value_label": "em vendas, até %s" % fmt.date_label(d - timedelta(days=1)),
            "by_month": [{k: v for k, v in m.items() if k != "complete"} for m in months],
            "month_sentence": _month_sentence(d, months, st["won_count"]),
            "deals": deals,
        },
    }
