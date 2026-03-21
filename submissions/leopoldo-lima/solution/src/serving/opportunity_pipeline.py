"""Pipeline de serving: lê os 5 CSVs oficiais, aplica normalização e joins, valida FKs.

CRP-REAL-02: caminho principal do produto; `dataset_loader` consome o resultado.
"""

from __future__ import annotations

import logging
import pathlib
from typing import Any

from src.domain.deal_stage import normalize_deal_stage
from src.normalization.mapper import normalize_value
from src.raw.reader import load_raw_rows
from src.serving.models import ServingOpportunity

logger = logging.getLogger("lead_scorer.serving")

DATA_DIR = pathlib.Path(__file__).resolve().parents[2] / "data"
_OFFICIAL_CSVS = (
    "accounts.csv",
    "products.csv",
    "sales_teams.csv",
    "sales_pipeline.csv",
    "metadata.csv",
)

_cache_ops: list[ServingOpportunity] | None = None
_cache_fingerprint: str | None = None
_metadata_index: dict[tuple[str, str], str] | None = None


def clear_serving_cache() -> None:
    """Limpa cache in-memory (testes ou reload de dados)."""
    global _cache_ops, _cache_fingerprint, _metadata_index
    _cache_ops = None
    _cache_fingerprint = None
    _metadata_index = None


def _data_mtimes_fingerprint() -> str:
    parts: list[str] = []
    for name in _OFFICIAL_CSVS:
        p = DATA_DIR / name
        parts.append(f"{name}:{p.stat().st_mtime_ns}")
    return "|".join(parts)


def _load_metadata_index() -> dict[tuple[str, str], str]:
    rows = load_raw_rows("metadata.csv")
    out: dict[tuple[str, str], str] = {}
    for r in rows:
        t = (r.get("Table") or "").strip()
        f = (r.get("Field") or "").strip()
        d = (r.get("Description") or "").strip()
        if t and f:
            out[(t.lower(), f.lower())] = d
    return out


def get_metadata_index() -> dict[tuple[str, str], str]:
    """Dicionário (tabela, campo) -> descrição do `metadata.csv` (linhagem de dados)."""
    global _metadata_index
    if _metadata_index is None:
        _metadata_index = _load_metadata_index()
    return _metadata_index


def validate_referential_for_row(
    *,
    sales_agent: str,
    product_raw: str,
    account_name: str | None,
    teams_set: set[str],
    products_canonical_set: set[str],
    accounts_set: set[str],
) -> bool:
    """True se FKs mínimas passam: agente e produto; conta opcional mas validada se preenchida."""
    agent = (sales_agent or "").strip()
    if not agent or agent not in teams_set:
        return False
    canon = normalize_value("sales_pipeline.csv", "product", (product_raw or "").strip()).canonical
    if not canon or canon not in products_canonical_set:
        return False
    acc = (account_name or "").strip()
    if acc and acc not in accounts_set:
        return False
    return True


def build_serving_opportunities(*, use_cache: bool = True) -> list[ServingOpportunity]:
    """Constrói oportunidades canónicas a partir de `data/*.csv` (5 arquivos)."""
    global _cache_ops, _cache_fingerprint

    fingerprint = _data_mtimes_fingerprint()
    if use_cache and _cache_ops is not None and _cache_fingerprint == fingerprint:
        return _cache_ops

    # Garante carregamento de metadata (presença do arquivo + índice para linhagem).
    idx = get_metadata_index()
    if not idx:
        logger.warning("serving_metadata_index_empty")

    pipeline = load_raw_rows("sales_pipeline.csv")
    teams_by_agent = {r["sales_agent"]: r for r in load_raw_rows("sales_teams.csv")}
    accounts_by_name = {r["account"]: r for r in load_raw_rows("accounts.csv")}
    products_by_name = {r["product"]: r for r in load_raw_rows("products.csv")}

    teams_set = set(teams_by_agent.keys())
    products_canonical_set = set(products_by_name.keys())
    accounts_set = set(accounts_by_name.keys())

    skipped = 0
    out: list[ServingOpportunity] = []

    for p in pipeline:
        opp_id = (p.get("opportunity_id") or "").strip()
        if not opp_id:
            skipped += 1
            continue
        agent = (p.get("sales_agent") or "").strip()
        raw_product = (p.get("product") or "").strip()
        account_name = (p.get("account") or "").strip() or None

        if not validate_referential_for_row(
            sales_agent=agent,
            product_raw=raw_product,
            account_name=account_name,
            teams_set=teams_set,
            products_canonical_set=products_canonical_set,
            accounts_set=accounts_set,
        ):
            skipped += 1
            continue

        product_canonical = normalize_value("sales_pipeline.csv", "product", raw_product).canonical
        team = teams_by_agent[agent]
        manager = (team.get("manager") or "").strip()
        regional = (team.get("regional_office") or "").strip()

        acc_row = accounts_by_name.get(account_name) if account_name else None
        office_loc = (acc_row.get("office_location") or "").strip() if acc_row else None
        acc_revenue = (acc_row.get("revenue") or "").strip() if acc_row else ""
        acc_employees = (acc_row.get("employees") or "").strip() if acc_row else ""

        prod_row = products_by_name[product_canonical]
        series = (prod_row.get("series") or "").strip()
        try:
            list_price = float((prod_row.get("sales_price") or "").strip() or "0")
        except ValueError:
            list_price = 0.0

        try:
            close_value = float((p.get("close_value") or "").strip() or "0")
        except ValueError:
            close_value = 0.0

        close_date = (p.get("close_date") or "").strip() or None
        engage_date = (p.get("engage_date") or "").strip()
        deal_stage = normalize_deal_stage((p.get("deal_stage") or "").strip())

        out.append(
            ServingOpportunity(
                opportunity_id=opp_id,
                sales_agent=agent,
                manager=manager,
                regional_office=regional,
                account_name=account_name,
                account_office_location=office_loc,
                product_canonical=product_canonical,
                product_series=series,
                product_sales_price=list_price,
                deal_stage=deal_stage,
                engage_date=engage_date,
                close_date=close_date,
                close_value=close_value,
                account_revenue=acc_revenue,
                account_employees=acc_employees,
            )
        )

    if skipped:
        logger.warning(
            "serving_pipeline_rows_skipped skipped=%s served=%s",
            skipped,
            len(out),
        )

    _cache_ops = out
    _cache_fingerprint = fingerprint
    return out


def serving_opportunities_to_api_rows(
    opportunities: list[ServingOpportunity],
) -> list[dict[str, Any]]:
    return [o.to_api_row() for o in opportunities]
