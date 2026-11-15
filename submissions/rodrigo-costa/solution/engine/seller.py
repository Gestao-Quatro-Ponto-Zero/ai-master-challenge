"""Telas do vendedor: "Foco da semana" (focus) e "Pipeline" (pipeline).

Só usa o que se sabia na data: deals com close_date >= d aparecem como em negociação, sem estágio final.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Sequence

from engine import fmt
from engine.core import (CLOSING_DAYS_MIN, FIRST_DATE, HORIZON_DAYS, HOT_MIN, REGION_LABELS, WARM_MIN, BandRow,
                         Dataset, ScoredDeal, Snapshot, Window, WinRecord, closing_is_strong, days_to_quarter_end,
                         phase_title, resolve_working_seller, snapshot, stale_key, summarize, win_record)
from engine.shapes import closed_deal_dict, date_dict, open_deal_dict, person_dict

EXCLUDED_TEXT = ("Cliente, setor e vendedor: foram testados nesta base e não mudam a chance. "
                 "O produto entra só pelo preço.")
PHASE_OPENERS = {
    "abre": "É o primeiro mês do trimestre",
    "meio": "É o meio do trimestre",
    "fecha": "É o último mês do trimestre",
}
LEVEL_PLACES = {
    "semana": "nesta mesma semana do trimestre",
    "mes": "neste mesmo mês do trimestre",
    "idade": "em qualquer época do trimestre",
}
STALE_PLACES = {
    "semana": "nessa altura do trimestre",
    "mes": "neste mesmo mês do trimestre",
    "idade": "em qualquer época do trimestre",
    "geral": "em qualquer época do trimestre",
}
MATURE_AGE = 46  # a partir desta idade o deal é "maduro" nas frases de contexto
OLD_AGE = 61  # "deal com mais de 60 dias" na frase do começo do trimestre
NEARLY_ZERO = 0.05
NEAR_LIMIT_DAYS = 30  # "se aproxima do maior ciclo" quando falta até isto
TOP_DEALS = 10


# ---------------------------------------------------------------- textos gerais

def _band_text(band: BandRow) -> str:
    if band.max_age is None:
        return "%d dias ou mais" % band.min_age
    if band.min_age == 0:
        return "até %d dias" % band.max_age
    return "%d a %d dias" % (band.min_age, band.max_age)


def _between(w: Window) -> str:
    return "entre %d e %d dias" % (w.min_age, w.max_age)


def context_sentence(ds: Dataset, snap: Snapshot) -> str:
    """Frase sobre o momento do trimestre, conferida contra a tabela de chance da data."""
    w, phase = snap.window, snap.quarter_phase
    opener = PHASE_OPENERS[phase]
    if w is None:
        return opener + ": nesta altura, nenhum deal aberto virou venda em 30 dias nesta base."
    generic = "%s: nesta altura, os deals que mais fecham estão %s." % (opener, _between(w))
    if phase == "fecha":
        if w.min_age >= MATURE_AGE and closing_is_strong(snap):
            return "É o último mês do trimestre, quando os deals maduros desta base mais fecham."
        return generic
    if phase == "abre":
        if w.first_band != 0:
            return generic
        old = max(b.chance for b in snap.bands if b.max_age is not None and b.min_age >= OLD_AGE)
        if old == 0:
            return ("É o primeiro mês do trimestre: nesta altura, nenhum deal com mais de %d dias virou venda "
                    "em 30 dias nesta base." % (OLD_AGE - 1))
        if old < NEARLY_ZERO:
            return ("É o primeiro mês do trimestre: nesta base, deal com mais de %d dias quase não vira venda "
                    "nos 30 dias seguintes." % (OLD_AGE - 1))
        return ("É o primeiro mês do trimestre: nesta base, os deals novos, de até %d dias, "
                "são os que mais fecham agora." % w.max_age)
    prev = snap.date - timedelta(days=28)
    if prev >= FIRST_DATE:
        before = snapshot(ds, prev).window
        if before is None or w.peak_chance > before.peak_chance:
            return "É o meio do trimestre: os fechamentos começam a acelerar."
    return generic


def _date_block(ds: Dataset, snap: Snapshot) -> Dict[str, Any]:
    out = date_dict(snap.date)
    out["context_sentence"] = context_sentence(ds, snap)
    return out


def _window_chance(snap: Snapshot) -> Optional[float]:
    w = snap.window
    if w is None:
        return None
    rows = snap.bands[w.first_band:w.last_band + 1]
    n = sum(b.n for b in rows)
    return sum(b.y for b in rows) / float(n) if n else 0.0


def _in_window(snap: Snapshot, s: ScoredDeal) -> bool:
    w = snap.window
    return w is not None and not s.stale and w.min_age <= s.age_days <= w.max_age


def _summary_sentence(totals: Dict[str, Any], max_cycle: int) -> str:
    declared = totals["declared_value"]
    if totals["open"] == 0:
        return "Você não tem deal em negociação nesta data."
    head = "(%s a preço de tabela)" % fmt.money(declared)
    if totals["stale"] == 0:
        return "Tudo o que está declarado %s ainda pode fechar: nenhum deal passou de %d dias." % (head, max_cycle)
    stale_text = "%s em negociação há mais de %d dias" % (fmt.plural(totals["stale"], "deal"), max_cycle)
    if totals["live"] == 0:
        return "Do que está declarado %s, nada ainda pode fechar: %s %s." % (
            head, "é" if totals["stale"] == 1 else "são", stale_text)
    # as duas partes existem: nenhuma pode aparecer como 0% nem 100%
    live_pct = min(99, max(1, int(fmt.pct(totals["live_value"] / float(declared))[:-1])))
    return "Do que está declarado %s, %d%% ainda pode fechar. Os outros %d%% %s %s." % (
        head, live_pct, 100 - live_pct, "é" if totals["stale"] == 1 else "são", stale_text)


# ---------------------------------------------------------------- explicação de cada deal

def _position(snap: Snapshot, s: ScoredDeal) -> str:
    if s.stale:
        return "sem_desfecho"
    w = snap.window
    if w is None:
        return "sem_janela"
    if s.age_days < w.min_age:
        return "cedo"
    return "janela" if s.age_days <= w.max_age else "tarde"


POSITION_LABELS = {"cedo": "ainda é cedo", "janela": "", "tarde": "passando da janela", "sem_desfecho": "",
                   "sem_janela": ""}


def _action(snap: Snapshot, s: ScoredDeal, position: str) -> str:
    w, limit = snap.window, snap.max_cycle
    if position == "sem_desfecho":
        return ("aberto há mais de %d dias, e nesta base nenhum deal fechou depois disso. "
                "Decida: segue de pé ou encerra." % limit)
    if position == "sem_janela":
        return "nesta altura do trimestre nenhuma faixa de idade se destaca. Mantenha o contato."
    if position == "janela":
        late_in_quarter = snap.quarter_phase == "fecha" and days_to_quarter_end(snap.date) >= CLOSING_DAYS_MIN
        when = ("ainda em " + fmt.month_name(snap.date)) if late_in_quarter else "nas próximas semanas"
        return "o deal está na faixa de idade em que mais se fecha. Proponha o fechamento %s." % when
    if position == "cedo":
        if s.age_band == 0 and snap.bands[0].chance > snap.bands[1].chance:
            return ("deal novo: nesta base uma parte fecha logo nas duas primeiras semanas. "
                    "Vale um contato já.")
        return ("ainda é cedo: nesta altura do trimestre os deals fecham mais %s. Mantenha o contato."
                % _between(w))
    if s.chance >= w.threshold:
        # faixa fora da janela, mas com chance quase igual à da melhor (janela não contígua)
        return ("a faixa de idade deste deal fecha quase tanto quanto a melhor agora (%s contra %s). "
                "Trate como prioridade." % (fmt.pct(s.chance), fmt.pct(w.peak_chance)))
    if s.age_days >= limit - NEAR_LIMIT_DAYS:
        return ("o deal já passou da faixa que mais fecha e se aproxima dos %d dias. "
                "Confirme com o cliente se segue de pé." % limit)
    return ("nesta altura do trimestre, quem mais fecha são os deals de %s. Na faixa deste, a chance agora é "
            "menor (%s). Mantenha o contato." % (w.label, fmt.pct(s.chance)))


def _sold_text(y: int) -> str:
    if y == 0:
        return "nenhum virou venda em 30 dias"
    return "%s %s venda em 30 dias" % (fmt.number(y), fmt.plural_word(y, "virou", "viraram"))


def _source(snap: Snapshot, s: ScoredDeal) -> str:
    band = snap.bands[s.age_band]
    if s.stale:
        if band.min_age == snap.max_cycle + 1:
            what = "além desse prazo"
        else:
            what = "com " + _band_text(band)
        return "Dos %s que já %s %s %s, %s." % (
            fmt.plural(s.n, "deal"), fmt.plural_word(s.n, "esteve", "estiveram"), what,
            STALE_PLACES[s.level], _sold_text(s.y))
    if s.level == "geral":
        return ("Há poucos casos parecidos, então vale a taxa geral: %s de %s %s venda em 30 dias."
                % (fmt.number(s.y), fmt.plural(s.n, "deal"), fmt.plural_word(s.y, "virou", "viraram")))
    return "%s já %s assim: %s, %s. Deles, %s." % (
        fmt.plural(s.n, "deal"), fmt.plural_word(s.n, "esteve", "estiveram"), _band_text(band),
        LEVEL_PLACES[s.level], _sold_text(s.y))


def _reason(snap: Snapshot, s: ScoredDeal, share_above: Optional[float]) -> str:
    if s.stale:
        return ("Aberto há %s. Nesta base nenhum deal fechou depois de %d dias, por isso ele sai da fila do score."
                % (fmt.days(s.age_days), snap.max_cycle))
    head = "%s de chance vezes %s dá %s esperados em 30 dias." % (
        fmt.pct(s.chance), fmt.money(s.deal.price), fmt.money(s.expected_value))
    if not share_above:
        return head + " Nenhum deal vivo da empresa tem receita esperada maior."
    shown = fmt.pct(share_above)
    if shown == "0%":
        return head + " Menos de 1% dos deals vivos da empresa têm receita esperada maior."
    prefix = "Só " if share_above <= 0.1 else ""
    return head + " %s%s dos deals vivos da empresa têm receita esperada maior." % (prefix, shown)


def _deal_entry(snap: Snapshot, s: ScoredDeal) -> Dict[str, Any]:
    out = open_deal_dict(snap, s)
    position = _position(snap, s)
    share_above = None if s.stale else snap.fraction_above(s.expected_value)
    action = _action(snap, s, position)
    out.update({
        "position": position,
        "position_label": POSITION_LABELS[position],
        "base": {"n": s.n, "y": s.y, "level": s.level, "bucket_label": snap.bands[s.age_band].label},
        "share_above": share_above,
        "why": {"reason": _reason(snap, s, share_above), "source": _source(snap, s),
                "excluded": EXCLUDED_TEXT, "action": action},
    })
    parts = ["#" + s.deal.id, s.deal.product, fmt.money(s.deal.price), "aberto há " + fmt.days(s.age_days)]
    if s.stale:
        parts.append("sem desfecho (mais de %d dias)" % snap.max_cycle)
    else:
        parts.append("score %d" % s.score)
        parts.append("%s de chance de virar venda em 30 dias (%s de %s parecidos)" % (
            fmt.pct(s.chance), fmt.number(s.y), fmt.plural(s.n, "deal")))
    out["summary_text"] = " · ".join(parts) + ". O que fazer: " + action
    return out


# ---------------------------------------------------------------- cartões da Gabi

def _card(kind: str, title: str, body: str, link_label: Optional[str] = None,
          link_target: Optional[str] = None, highlight: bool = False) -> Dict[str, Any]:
    return {"kind": kind, "label": kind.upper(), "title": title, "body": body, "link_label": link_label,
            "link_target": link_target, "highlight": highlight}


def _see(n: int) -> str:
    return "Ver o deal" if n == 1 else "Ver os %s" % fmt.plural(n, "deal")


def _moment_card(snap: Snapshot, items: Sequence[ScoredDeal]) -> Dict[str, Any]:
    title = phase_title(snap) + "."
    w = snap.window
    if w is None:
        return _card("momento", title, "Nesta altura do trimestre, nenhuma faixa de idade teve deal virando venda "
                     "em 30 dias nesta base.", highlight=True)
    count = sum(1 for s in items if _in_window(snap, s))
    if count == 0:
        body = ("Você não tem deal na faixa de %s, a que mais fecha nesta altura do trimestre." % w.label)
        return _card("momento", title, body, highlight=True)
    rate = _window_chance(snap) or 0.0
    if 0.45 <= rate <= 0.55:
        sold = "metade dos deals nessa faixa virou venda em 30 dias"
    else:
        sold = "%s dos deals nessa faixa viraram venda em 30 dias" % fmt.pct(rate)
    who = ("1 dos seus deals vivos está" if count == 1
           else "%s dos seus deals vivos estão" % fmt.number(count))
    body = "%s na faixa de %s. Nesta altura do trimestre, %s." % (who, w.label, sold)
    return _card("momento", title, body, _see(count), "janela", True)


def top_by_price(items: Sequence[ScoredDeal]) -> List[ScoredDeal]:
    """Os maiores deals por preço: os 10 primeiros, estendidos até não partir um empate de preço."""
    ordered = sorted(items, key=stale_key)
    size = min(TOP_DEALS, len(ordered))
    while size < len(ordered) and ordered[size - 1].deal.price == ordered[size].deal.price:
        size += 1
    return ordered[:size]


def _pipeline_card(snap: Snapshot, items: Sequence[ScoredDeal]) -> Dict[str, Any]:
    if not items:
        return _card("pipeline", "Você não tem deal em negociação.", "Nada a revisar no pipeline nesta data.")
    top = top_by_price(items)
    size, limit = len(top), snap.max_cycle
    stale_top = sum(1 for s in top if s.stale)
    if size > TOP_DEALS:
        # o empate de preço esticou a lista: dizer qual é o grupo, e não "seus 49 maiores"
        products = sorted({s.deal.product for s in top})
        group = ("seus %d deals de %s" % (size, products[0]) if len(products) == 1
                 else "seus %d deals de maior preço" % size)
    elif size == TOP_DEALS:
        group = "seus %d maiores deals" % size
    else:
        group = "seu único deal aberto" if size == 1 else "seus %d deals abertos" % size
    if stale_top == 0:
        title = "Seus maiores deals estão todos vivos." if size > 1 else "Seu deal aberto está vivo."
        if size > 1 and not any(s.stale for s in items):
            # sem nenhum parado, falar de todos evita um "68 maiores" inflado por empates de preço
            group = "seus %d deals abertos" % len(items)
        return _card("pipeline", title, "Nenhum dos %s passou de %d dias." % (group, limit)
                     if size > 1 else "Ele não passou de %d dias." % limit)
    if size == 1:
        title = "Seu único deal aberto passou de %d dias." % limit
    elif stale_top == size:
        title = "Todos os %s passaram de %d dias." % (group, limit)
    else:
        title = "%d dos %s %s de %d dias." % (stale_top, group, "passou" if stale_top == 1 else "passaram", limit)
    body = ("Nesta base nenhum deal fechou depois desse prazo. "
            "Confirme com o cliente se o deal segue de pé ou encerre.")
    total_stale = sum(1 for s in items if s.stale)
    # o título fala só dos maiores; se o link abre mais deals que isso, o rótulo diz quantos são
    link = (_see(total_stale) if total_stale == stale_top
            else "Ver todos os %s sem desfecho" % fmt.number(total_stale))
    return _card("pipeline", title, body, link, "sem_desfecho")


def _indicator_card(record: WinRecord, limit: int) -> Dict[str, Any]:
    if record.official_rate is None:
        return _card("indicador", "Você ainda não tem taxa de ganho.",
                     "Nenhum deal seu foi ganho ou perdido antes desta data.")
    official = fmt.pct1(record.official_rate)
    if record.stale == 0:
        return _card("indicador", "Sua taxa de ganho conta a história toda.",
                     "Você não tem deal aberto há mais de %d dias, então os %s do CRM não escondem nada."
                     % (limit, official))
    if record.stale == 1:
        subject = "o deal sem desfecho contado como não ganho"
    else:
        subject = "os %s sem desfecho contados como não ganhos" % fmt.plural(record.stale, "deal")
    closed = record.won + record.lost
    # a conta fica no próprio cartão: ele não leva a outra tela
    body = ("Hoje o CRM mostra %s: %s em %s. Com %s, são %s em %s, ou %s. "
            "Cada deal que você confirma com o cliente ou encerra aproxima os dois números."
            % (official, fmt.plural(record.won, "ganho"), fmt.plural(closed, "deal fechado", "deals fechados"),
               subject, fmt.number(record.won), fmt.number(closed + record.stale),
               fmt.pct1(record.rate_with_stale)))
    return _card("indicador", "Decidir os sem desfecho deixa sua taxa mais fiel.", body)


# ---------------------------------------------------------------- telas

def _band_groups(items: Sequence[ScoredDeal], limit: int) -> List[Dict[str, Any]]:
    specs = (("quente", "Quentes", "score %d ou mais" % HOT_MIN),
             ("morno", "Mornos", "score de %d a %d" % (WARM_MIN, HOT_MIN - 1)),
             ("frio", "Frios", "score abaixo de %d" % WARM_MIN),
             ("sem_desfecho", "Sem desfecho", "mais de %d dias" % limit))
    out = []
    for key, label, hint in specs:
        group = [s for s in items if s.score_band == key]
        with_account = sum(1 for s in group if s.deal.account is not None)
        out.append({"key": key, "label": label, "hint": hint, "count": len(group),
                    "with_account": with_account, "without_account": len(group) - with_account})
    return out


def focus(ds: Dataset, d: date, name: str) -> Dict[str, Any]:
    """Foco da semana do vendedor: resumo, deals em ordem de prioridade com o porquê, cartões da Gabi."""
    seller = resolve_working_seller(ds, name)
    snap = snapshot(ds, d)
    items = snap.by_seller.get(seller, ())
    totals = summarize(items)
    record = win_record(ds, snap, seller)
    w = snap.window
    declared = totals["declared_value"]
    return {
        "seller": person_dict(ds, seller),
        "date": _date_block(ds, snap),
        "summary": {
            "open_count": totals["open"], "live_count": totals["live"], "stale_count": totals["stale"],
            "declared_value": declared, "live_value": totals["live_value"], "stale_value": totals["stale_value"],
            "expected_30d": round(totals["expected_value"], 2),
            "live_share": totals["live_value"] / float(declared) if declared else None,
            "sentence": _summary_sentence(totals, snap.max_cycle),
        },
        "window": None if w is None else {"from_days": w.min_age, "to_days": w.max_age,
                                          "max_days": snap.max_cycle, "chance": _window_chance(snap)},
        "bands": _band_groups(items, snap.max_cycle),
        "deals": [_deal_entry(snap, s) for s in items],
        "insights": [_moment_card(snap, items), _pipeline_card(snap, items),
                     _indicator_card(record, snap.max_cycle)],
        "rates": {"won": record.won, "lost": record.lost, "official": record.official_rate,
                  "with_stale": record.rate_with_stale},
    }


def _prospecting_note(ds: Dataset, has_own: bool) -> str:
    if has_own:
        return ("Sem data de entrada: não dá para calcular idade nem score, nem saber desde quando estão aqui. "
                "A lista é a do fim da base, em ordem de valor.")
    regions = sorted({x.region for x in ds.prospecting})
    total = len(ds.prospecting)
    if not regions:
        return "Nenhuma regional usa a prospecção nesta base."
    labels = [REGION_LABELS[r] for r in regions]
    if len(labels) == 1:
        who = "Só a regional %s usa" % labels[0]
    else:
        who = "Só as regionais %s e %s usam" % (", ".join(labels[:-1]), labels[-1])
    return "%s a prospecção. Lá %s %s, %s sem data, então %s na lista só pelo valor." % (
        who, "é" if total == 1 else "são", fmt.plural(total, "deal"), "ele" if total == 1 else "todos",
        "entra" if total == 1 else "entram")


def pipeline(ds: Dataset, d: date, name: str) -> Dict[str, Any]:
    """Visão kanban (só leitura) do vendedor na data d."""
    seller = resolve_working_seller(ds, name)
    snap = snapshot(ds, d)
    items = snap.by_seller.get(seller, ())
    live = [s for s in items if not s.stale]
    stale = [s for s in items if s.stale]
    own = ds.deals_by_seller.get(seller, ())
    prospects = sorted((x for x in own if x.engage_date is None), key=lambda x: (-x.price, x.id))
    since = d - timedelta(days=HORIZON_DAYS)
    recent = sorted((x for x in ds.closed_before(d, seller=seller) if x.close_date >= since),
                    key=lambda x: (-x.close_date.toordinal(), x.id))
    won = [x for x in recent if x.won]
    lost = [x for x in recent if x.lost]
    live_value = sum(s.deal.price for s in live)
    stale_value = sum(s.deal.price for s in stale)
    won_value = sum(x.close_value or 0 for x in won)
    with_account = sum(1 for s in items if s.deal.account is not None)
    return {
        "seller": person_dict(ds, seller),
        "date": _date_block(ds, snap),
        "counts": {"all": len(items), "with_account": with_account, "without_account": len(items) - with_account},
        "columns": [
            {"key": "prospecting", "title": "Prospecção", "hint": "Antes da negociação", "count": len(prospects),
             "value": sum(x.price for x in prospects),
             "deals": [{"id": x.id, "product": x.product, "price": x.price, "account": x.account}
                       for x in prospects],
             "note": _prospecting_note(ds, bool(prospects))},
            {"key": "engaging", "title": "Em negociação",
             "hint": "%s · até %d dias" % (fmt.money(live_value), snap.max_cycle), "count": len(live),
             "value": live_value, "deals": [open_deal_dict(snap, s) for s in live]},
            {"key": "stale", "title": "Sem desfecho",
             "hint": "%s · mais de %d dias" % (fmt.money(stale_value), snap.max_cycle), "count": len(stale),
             "value": stale_value, "deals": [open_deal_dict(snap, s) for s in stale]},
            {"key": "won", "title": "Ganhos", "hint": "%s · últimos 30 dias" % fmt.money(won_value),
             "count": len(won), "value": won_value, "deals": [closed_deal_dict(ds, x) for x in won]},
            {"key": "lost", "title": "Perdidos", "hint": "Últimos 30 dias", "count": len(lost),
             "deals": [closed_deal_dict(ds, x) for x in lost]},
        ],
    }
