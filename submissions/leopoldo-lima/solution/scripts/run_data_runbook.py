from __future__ import annotations

import csv
import json
import pathlib
import sys
from dataclasses import asdict
from datetime import date
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "artifacts" / "data-validation"
JSON_PATH = OUT_DIR / "runbook-data-evidence.json"
MD_PATH = OUT_DIR / "runbook-data-evidence.md"


def _read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / name).open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    from src.domain.models import (
        Account,
        Opportunity,
        Product,
        RawOpportunity,
        SalesAgent,
        core_opportunity_to_gold,
        raw_opportunity_to_core,
    )
    from src.features.engineering import build_feature_set
    from src.scoring.engine import score_from_features

    accounts_rows = _read_csv("accounts.csv")
    products_rows = _read_csv("products.csv")
    sales_teams_rows = _read_csv("sales_teams.csv")
    pipeline_rows = _read_csv("sales_pipeline.csv")

    by_account = {r["account"]: r for r in accounts_rows}
    by_product = {r["product"]: r for r in products_rows}
    by_agent = {r["sales_agent"]: r for r in sales_teams_rows}

    source = pipeline_rows[0]
    raw = RawOpportunity(
        opportunity_id=source["opportunity_id"],
        sales_agent=source["sales_agent"],
        product=source["product"],
        account=source.get("account") or None,
        deal_stage=source["deal_stage"],
        engage_date=source["engage_date"],
        close_date=source.get("close_date") or None,
        close_value=source["close_value"],
    )
    core = raw_opportunity_to_core(raw)
    gold_from_domain = core_opportunity_to_gold(core)

    acc_row = by_account.get(core.account or "")
    prod_row = by_product.get(core.product)
    agent_row = by_agent.get(core.sales_agent)
    account = Account(**acc_row) if acc_row else None
    product = Product(**prod_row) if prod_row else None
    sales_agent = SalesAgent(**agent_row) if agent_row else None

    feature_set = build_feature_set(
        Opportunity(
            opportunity_id=core.opportunity_id,
            sales_agent=core.sales_agent,
            product=core.product,
            account=core.account,
            deal_stage=core.deal_stage,
            engage_date=core.engage_date,
            close_date=core.close_date,
            close_value=core.close_value,
        ),
        account=account,
        product=product,
        sales_agent=sales_agent,
        reference_date=date.today(),
    )
    score = score_from_features(feature_set)

    payload: dict[str, Any] = {
        "inputs": {
            "accounts_rows": len(accounts_rows),
            "products_rows": len(products_rows),
            "sales_teams_rows": len(sales_teams_rows),
            "sales_pipeline_rows": len(pipeline_rows),
        },
        "sample_pipeline_row": source,
        "sample_raw_to_core": asdict(core),
        "sample_core_to_gold_minimal": asdict(gold_from_domain),
        "sample_feature_set_joined": asdict(feature_set),
        "sample_score": asdict(score),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    md = [
        "# Runbook Data Evidence",
        "",
        f"- Arquivo JSON: `{JSON_PATH.relative_to(ROOT)}`",
        f"- Linhas lidas: accounts={len(accounts_rows)}, products={len(products_rows)}, "
        f"sales_teams={len(sales_teams_rows)}, sales_pipeline={len(pipeline_rows)}",
        f"- Oportunidade amostra: `{core.opportunity_id}`",
        f"- Produto normalizado: `{core.product}`",
        f"- Score amostra: `{score.score}`",
        "",
        "Este artefato foi gerado por `python scripts/run_data_runbook.py`.",
    ]
    MD_PATH.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote {JSON_PATH}")
    print(f"Wrote {MD_PATH}")


if __name__ == "__main__":
    main()
