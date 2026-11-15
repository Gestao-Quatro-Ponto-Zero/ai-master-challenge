"""Fatos da base inteira (inclusive desfechos depois de qualquer data), usados pela qualidade dos dados,
pelas fontes e pelos metadados. Nenhuma tela de trabalho deve ler daqui números que dependam do desfecho.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional

from engine import fmt
from engine.core import HORIZON_DAYS, Dataset, home_region

DATASET_NAME = "CRM Sales Predictive Analytics"
DATASET_LICENSE = "CC0"


@lru_cache(maxsize=4)
def base_facts(ds: Dataset) -> Dict[str, Any]:
    """Fatos da base inteira, calculados uma vez por Dataset."""
    deals = ds.deals
    engages = [x.engage_date for x in deals if x.engage_date is not None]
    first_close = ds.closed[0].close_date
    unfinished = [x for x in deals if x.close_date is None]
    closed = ds.closed
    after_end = ds.end_date + timedelta(days=1)
    home = {a: home_region(ds.closed_before(after_end, account=a)) for a in ds.accounts}
    open_with = [x for x in unfinished if x.account is not None]

    # Começo de trimestre dentro do período com fechamentos: deals com mais de 30 dias abertos nesse dia.
    quarter_rows = []
    for month in (1, 4, 7, 10):
        start = date(first_close.year, month, 1)
        if start < first_close or start > ds.end_date:
            continue
        month_end = date(start.year, start.month + 1, 1)
        old = [x for x in ds.dated if x.is_open_at(start) and (start - x.engage_date).days > HORIZON_DAYS]
        quarter_rows.append((start, len(old), sum(1 for x in old if x.close_date is not None
                                                  and x.close_date < month_end)))
    by_month: Dict[int, List[int]] = {0: [0, 0], 1: [0, 0], 2: [0, 0]}
    for x in closed:
        row = by_month[(x.close_date.month - 1) % 3]
        row[0] += x.won
        row[1] += 1

    return {
        "stages": Counter(x.stage for x in deals),
        "first_engage": min(engages), "last_engage": max(engages),
        "first_close": first_close, "last_close": ds.end_date,
        "early": [x for x in deals if x.engage_date is not None and x.engage_date < first_close],
        "unfinished": unfinished,
        "open_no_account": sum(1 for x in unfinished if x.account is None),
        "open_with_account": len(open_with),
        "open_home": sum(1 for x in open_with if home.get(x.account) == x.region),
        "closed_with_account": sum(1 for x in closed if x.account is not None),
        "closed_home": sum(1 for x in closed if x.account is not None and home.get(x.account) == x.region),
        "accounts_with_closed": sum(1 for h in home.values() if h is not None),
        "no_account": [x for x in deals if x.account is None],
        "no_engage": sum(1 for x in deals if x.engage_date is None),
        "max_cycle": max(x.cycle_days for x in closed),
        "quarter_rows": quarter_rows,
        "by_month": by_month,
        "sellers_with_deals": sorted(ds.deals_by_seller),
    }


def share_or_none(part: int, whole: int) -> Optional[float]:
    """part / whole, ou None quando whole é zero."""
    return part / float(whole) if whole else None


def months_between(first: date, last: date) -> int:
    return (last.year - first.year) * 12 + last.month - first.month - (1 if last.day < first.day else 0)


def base_period_label(ds: Dataset) -> str:
    """Período da base inteira: "de out 2016 a dez 2017"."""
    b = base_facts(ds)
    first, last = b["first_engage"], max(b["last_engage"], b["last_close"])
    return "de %s %d a %s %d" % (fmt.MONTHS_SHORT[first.month - 1], first.year,
                                 fmt.MONTHS_SHORT[last.month - 1], last.year)


def in_proof(ds: Dataset, d: date) -> bool:
    """A data entra na prova quando a base cobre os 30 dias seguintes a ela."""
    return d + timedelta(days=HORIZON_DAYS) <= ds.end_date
