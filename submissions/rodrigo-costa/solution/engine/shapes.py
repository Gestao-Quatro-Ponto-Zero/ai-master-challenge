"""Dicionários padrão (prontos para JSON) que todas as telas reutilizam."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from engine import fmt
from engine.core import AGE_BAND_LABELS, REGION_LABELS, SCORE_BAND_LABELS, Dataset, Deal, InputError, ScoredDeal, \
    Snapshot, echo, quarter_point, resolve_manager, resolve_seller, resolve_working_seller


def date_dict(d: date) -> Dict[str, Any]:
    """Data em ISO, rótulos prontos e ponto do trimestre."""
    week, month, phase = quarter_point(d)
    return {
        "iso": d.isoformat(),
        "label": fmt.date_label(d),
        "label_short": fmt.date_short(d),
        "label_long": fmt.date_long(d),
        "day_month": fmt.day_month(d),
        "month_name": fmt.month_name(d),
        "week_of_quarter": week,
        "month_in_quarter": month,
        "quarter_phase": phase,
    }


def person_dict(ds: Dataset, name: str) -> Dict[str, Any]:
    """Vendedor ou gestor. Para gestor, manager é None e a regional é a do time dele. InputError se não existir."""
    try:
        canonical = resolve_seller(ds, name)
        seller = ds.sellers[canonical]
        manager, region = seller.manager, seller.region
    except ValueError:
        try:
            canonical = resolve_manager(ds, name)
        except ValueError:
            raise InputError("Pessoa não encontrada: \"%s\"." % echo(name))
        manager, region = None, ds.sellers[ds.managers[canonical][0]].region
    parts = canonical.split()
    return {
        "name": canonical,
        "first_name": parts[0],
        "initials": (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper(),
        "manager": manager,
        "region": region,
        "region_label": REGION_LABELS[region],
    }


def viewer_scope(ds: Dataset, viewer: Optional[str]) -> Tuple[Optional[str], List[str]]:
    """(nome canônico, vendedores cujos deals contam como "do viewer"). Gestor: o time dele."""
    if viewer is None or not viewer.strip():
        return None, []
    person = person_dict(ds, viewer)
    name = person["name"]
    if person["manager"] is None:
        return name, list(ds.managers[name])
    return resolve_working_seller(ds, name), [name]


def open_deal_dict(snap: Snapshot, scored: ScoredDeal) -> Dict[str, Any]:
    """Deal aberto na data do retrato. Não traz nada do desfecho futuro."""
    deal = scored.deal
    return {
        "id": deal.id,
        "product": deal.product,
        "price": deal.price,
        "account": deal.account,
        "seller": deal.seller,
        "region": deal.region,
        "region_label": REGION_LABELS[deal.region],
        "engage_date": deal.engage_date.isoformat(),
        "engage_label": fmt.date_in_context(deal.engage_date, snap.date),
        "age_days": scored.age_days,
        "age_band": AGE_BAND_LABELS[scored.age_band],
        "stale": scored.stale,
        "band": scored.score_band,
        "band_label": SCORE_BAND_LABELS[scored.score_band],
        "score": scored.score,
        "chance": scored.chance,
        "expected_value": round(scored.expected_value, 2),
    }


def closed_deal_dict(ds: Dataset, deal: Deal) -> Dict[str, Any]:
    """Deal fechado (Won/Lost). Só use com deals fechados antes da data da tela."""
    if deal.close_date is None:
        raise ValueError("O deal %s ainda não foi fechado." % deal.id)
    return {
        "id": deal.id,
        "product": deal.product,
        "price": deal.price,
        "account": deal.account,
        "seller": deal.seller,
        "region_label": REGION_LABELS[ds.sellers[deal.seller].region],
        "close_date": deal.close_date.isoformat(),
        "close_label": fmt.date_label(deal.close_date),
        "won": deal.won,
        "close_value": deal.close_value,
        "cycle_days": deal.cycle_days,
    }
