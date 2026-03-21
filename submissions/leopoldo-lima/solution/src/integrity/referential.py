from __future__ import annotations

import csv
import pathlib
from dataclasses import dataclass
from typing import Any

from src.normalization.mapper import normalize_value

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


@dataclass(frozen=True)
class RelationResult:
    relation: str
    match_rate: float
    total_rows_with_value: int
    matched_rows: int
    classification: str
    notes: str


def _read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / name).open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def evaluate_referential_integrity() -> dict[str, Any]:
    pipeline = _read_csv("sales_pipeline.csv")
    accounts = _read_csv("accounts.csv")
    products = _read_csv("products.csv")
    teams = _read_csv("sales_teams.csv")

    accounts_set = {(r.get("account") or "").strip() for r in accounts}
    products_set = {(r.get("product") or "").strip() for r in products}
    teams_set = {(r.get("sales_agent") or "").strip() for r in teams}

    def eval_relation(
        key: str, ref_set: set[str], relation: str, use_normalization: bool = False
    ) -> tuple[int, int]:
        total = 0
        matched = 0
        for row in pipeline:
            value = (row.get(key) or "").strip()
            if not value:
                continue
            total += 1
            check = value
            if use_normalization:
                check = normalize_value("sales_pipeline.csv", key, value).canonical
            if check in ref_set:
                matched += 1
        return total, matched

    account_total, account_matched = eval_relation(
        "account", accounts_set, "sales_pipeline.account -> accounts.account"
    )
    product_total, product_matched = eval_relation(
        "product",
        products_set,
        "sales_pipeline.product -> products.product (com normalizacao)",
        use_normalization=True,
    )
    agent_total, agent_matched = eval_relation(
        "sales_agent", teams_set, "sales_pipeline.sales_agent -> sales_teams.sales_agent"
    )

    def to_result(
        relation: str,
        total: int,
        matched: int,
        classification: str,
        notes: str,
    ) -> RelationResult:
        rate = 1.0 if total == 0 else matched / total
        return RelationResult(
            relation=relation,
            match_rate=rate,
            total_rows_with_value=total,
            matched_rows=matched,
            classification=classification,
            notes=notes,
        )

    results = [
        to_result(
            "sales_pipeline.account -> accounts.account",
            account_total,
            account_matched,
            "blocking" if account_matched < account_total else "ok",
            "Conta vazia e permitida; chave presente deve bater com dimensão.",
        ),
        to_result(
            "sales_pipeline.product -> products.product (com normalizacao)",
            product_total,
            product_matched,
            "blocking" if product_matched < product_total else "ok",
            "Alias semântico (ex.: GTXPro) aplicado antes do join.",
        ),
        to_result(
            "sales_pipeline.sales_agent -> sales_teams.sales_agent",
            agent_total,
            agent_matched,
            "blocking" if agent_matched < agent_total else "ok",
            "Agente preenchido deve existir na dimensão de times.",
        ),
    ]

    used_agents = {
        (r.get("sales_agent") or "").strip()
        for r in pipeline
        if (r.get("sales_agent") or "").strip()
    }
    unused_agents = sorted([a for a in teams_set if a and a not in used_agents])

    return {
        "relations": [r.__dict__ for r in results],
        "unused_dimension_agents": {
            "count": len(unused_agents),
            "classification": "warning",
            "samples": unused_agents[:10],
            "notes": "Agentes sem uso no pipeline atual não bloqueiam integridade.",
        },
    }
