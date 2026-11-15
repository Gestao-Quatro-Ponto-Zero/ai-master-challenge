"""Metadados do app (meta) e tela de acesso simulado (login). Reexportados por engine.quality.

A tela de acesso usa o retrato da data; só o card "oportunidades na base" descreve a base inteira, e o
rótulo diz isso.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any, Dict

from engine import fmt
from engine.core import DEFAULT_DATE, REGION_LABELS, Dataset, available_dates, snapshot, summarize
from engine.facts import (DATASET_LICENSE, DATASET_NAME, base_facts, base_period_label, in_proof,
                          share_or_none)
from engine.proof import proof
from engine.shapes import date_dict, person_dict

SUGGESTED_SELLERS = ("Daniell Hammack", "Reed Clapper", "Darcel Schlecht")


# ---------------------------------------------------------------- metadados

def meta(ds: Dataset) -> Dict[str, Any]:
    """Dados fixos que o front usa em todas as telas: base, datas, regionais, gestores, vendedores e produtos."""
    b = base_facts(ds)
    with_deals = b["sellers_with_deals"]
    dates = []
    for d in available_dates(ds):
        item = date_dict(d)
        item["month_label"] = fmt.MONTHS_SHORT[d.month - 1]
        item["in_proof"] = in_proof(ds, d)
        dates.append(item)
    managers = []
    for name in sorted(ds.managers):
        person = person_dict(ds, name)
        managers.append({"name": name, "region": person["region"], "region_label": person["region_label"],
                         "team": [s for s in ds.managers[name] if s in ds.deals_by_seller]})
    sellers = []
    for name in with_deals:
        p = person_dict(ds, name)
        sellers.append({k: p[k] for k in ("name", "first_name", "initials", "manager", "region", "region_label")})
    return {
        "dataset": {
            "name": DATASET_NAME, "license": DATASET_LICENSE, "deals": len(ds.deals),
            "by_stage": {k: b["stages"].get(k, 0) for k in ("Won", "Lost", "Engaging", "Prospecting")},
            "accounts": len(ds.accounts), "sellers_total": len(ds.sellers), "sellers_with_deals": len(with_deals),
            "managers": len(ds.managers), "regions": len(REGION_LABELS),
            "first_engage": b["first_engage"].isoformat(), "last_engage": b["last_engage"].isoformat(),
            "first_close": b["first_close"].isoformat(), "last_close": b["last_close"].isoformat(),
            "period_label": base_period_label(ds),
        },
        "default_date": DEFAULT_DATE.isoformat(),
        "dates": dates,
        "regions": [{"key": k, "label": v} for k, v in REGION_LABELS.items()],
        "managers": managers,
        "sellers": sellers,
        "products": [{"name": p.name, "price": p.price}
                     for p in sorted(ds.products.values(), key=lambda p: (-p.price, p.name))],
    }


# ---------------------------------------------------------------- tela de acesso

def _seller_descriptor(region_label: str, summary: Dict[str, Any], prospecting: int) -> str:
    if summary["stale"]:
        return "%s · %s sem desfecho" % (region_label, fmt.number(summary["stale"]))
    if prospecting:
        return "%s · %s e %s em prospecção" % (region_label, fmt.plural(summary["live"], "vivo"),
                                               fmt.number(prospecting))
    return "%s · nenhum deal sem desfecho" % region_label


def login(ds: Dataset, d: date) -> Dict[str, Any]:
    """Tela de acesso simulado: sugestões, lista de vendedores e gestores e o painel do pipeline."""
    snap = snapshot(ds, d)
    prospecting = Counter(x.seller for x in ds.prospecting)
    per_seller = {name: summarize(snap.by_seller.get(name, ())) for name in base_facts(ds)["sellers_with_deals"]}
    # "Maior carteira" = maior valor declarado (preço de tabela dos abertos) na data
    biggest = max(v["declared_value"] for v in per_seller.values())

    def seller_row(name: str) -> Dict[str, Any]:
        s = ds.sellers[name]
        summary = per_seller[name]
        return {"name": name, "region_label": REGION_LABELS[s.region], "manager": s.manager,
                "open_count": summary["open"], "stale_count": summary["stale"],
                "descriptor": _seller_descriptor(REGION_LABELS[s.region], summary, prospecting.get(name, 0))}

    suggestions = []
    for name in SUGGESTED_SELLERS:
        row, summary = seller_row(name), per_seller[name]
        if summary["declared_value"] == biggest:
            tag = "Maior carteira"
        elif summary["stale"] == 0:
            tag = "Carteira em dia"
        else:
            tag = "Carteira com deals sem desfecho"
        suggestions.append({"name": name, "region_label": row["region_label"], "tag": tag,
                            "descriptor": row["descriptor"]})

    managers = []
    for name in sorted(ds.managers):
        team = [s for s in ds.managers[name] if s in per_seller]
        summary = summarize(snap.for_sellers(team))
        region_label = person_dict(ds, name)["region_label"]
        stale_text = ("%s sem desfecho" % fmt.number(summary["stale"]) if summary["stale"]
                      else "nenhum deal sem desfecho")
        managers.append({"name": name, "region_label": region_label, "team_size": len(team),
                         "open_count": summary["open"], "stale_count": summary["stale"],
                         "descriptor": "%s · %s · %s" % (region_label, fmt.plural(len(team), "vendedor",
                                                                                   "vendedores"), stale_text)})
    return {
        "date": date_dict(d),
        "suggestions": suggestions,
        "sellers": [seller_row(name) for name in sorted(per_seller)],
        "managers": managers,
        "panel": _login_panel(ds, d),
    }


def _login_panel(ds: Dataset, d: date) -> Dict[str, Any]:
    snap = snapshot(ds, d)
    total = summarize(snap.deals)
    when = fmt.date_label(d) + (", a data em que o app abre" if d == DEFAULT_DATE else "")
    stale, opened = total["stale"], total["open"]
    if stale == 0:
        first = "Em %s, nenhum dos %s em negociação tinha passado de %s." % (
            when, fmt.plural(opened, "deal"), fmt.days(snap.max_cycle))
    else:
        first = "Em %s, %s %s %s em negociação já %s passado de %s." % (
            when, fmt.number(stale), "do" if opened == 1 else "dos", fmt.plural(opened, "deal"),
            "tinha" if stale == 1 else "tinham", fmt.days(snap.max_cycle))
    result = proof(ds)
    mondays, lift = result["n_dates"], result["gains"]["vs_value_no_stale"]
    lift_text = "—" if lift is None else ("+" if lift >= 0 else "") + fmt.pct(lift)
    return {
        "declared_value": total["declared_value"],
        "live_value": total["live_value"],
        "open_count": opened,
        "stale_count": stale,
        "max_cycle": snap.max_cycle,
        "live_share": share_or_none(total["live_value"], total["declared_value"]),
        "label": "O PIPELINE DECLARADO NÃO É O PIPELINE REAL",
        "headline_1": "%s em negociação." % fmt.money_long(total["declared_value"]),
        "headline_2": "%s %s." % (fmt.money_long(total["live_value"]),
                                  "vivo" if total["live"] == 1 else "vivos"),
        "sentence": first + " Nenhum deal desta empresa fechou depois desse prazo.",
        "stats": [
            {"value": fmt.number(len(ds.deals)),
             "label": "oportunidades na base inteira, até %s" % fmt.date_label(ds.end_date)},
            {"value": fmt.number(mondays), "label": "%s no passado" % (
                "segunda-feira testada" if mondays == 1 else "segundas-feiras testadas")},
            {"value": lift_text, "label": "de receita contra ordenar por valor, já tirando os sem desfecho"},
        ],
    }
