#!/usr/bin/env python3
"""Build normalized Supabase imports and deterministic POWER scores."""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "processed"
SCORE_VERSION = "power-v0.6"
PROPENSITY_HISTORY_THRESHOLD = 30
ACTIVE_STAGES = {"Prospecting", "Engaging"}
CLOSED_STAGES = {"Won", "Lost"}

VALUE_TIER_NAMES = ("Bronze", "Silver", "Gold", "Diamond")


def read_csv(filename: str) -> list[dict[str, str]]:
    with (RAW_DIR / filename).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def normalize_sector(value: str | None) -> str | None:
    if not value:
        return None
    return "technology" if value == "technolgy" else value


def normalize_location(value: str | None) -> str | None:
    if not value:
        return None
    return "Philippines" if value == "Philipines" else value


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def empty_counter() -> dict[Any, list[int]]:
    return defaultdict(lambda: [0, 0])


def counter_read(counter: dict[Any, list[int]], key: Any) -> dict[str, Any]:
    won, cases = counter.get(key, [0, 0])
    lost = cases - won
    win_rate = (100 * won / cases) if cases else None
    strength = min(cases / PROPENSITY_HISTORY_THRESHOLD, 1) if cases else 0
    return {
        "won": won,
        "lost": lost,
        "cases": cases,
        "win_rate": round(win_rate, 2) if win_rate is not None else None,
        "strength": round(strength, 4),
    }


def add_history(counter: dict[Any, list[int]], key: Any, won: bool) -> None:
    if key is None or (isinstance(key, tuple) and any(part is None for part in key)):
        return
    counter[key][0] += int(won)
    counter[key][1] += 1


def score_propensity(lenses: list[dict[str, Any]]) -> float | None:
    usable = [lens for lens in lenses if lens["win_rate"] is not None and lens["strength"] > 0]
    total_strength = sum(lens["strength"] for lens in usable)
    if not total_strength:
        return None
    return sum(lens["win_rate"] * lens["strength"] for lens in usable) / total_strength


def score_execution(fits: list[dict[str, Any]]) -> float | None:
    available = [fit["fit"] for fit in fits if fit["fit"] is not None]
    return sum(available) / len(available) if available else None


def stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_value_tiers(products: list[dict[str, str]]) -> dict[str, str]:
    """Distribute distinct catalog prices across four relative value tiers."""
    distinct_prices = sorted({int(row["sales_price"]) for row in products})
    tier_by_price: dict[int, str] = {}
    for position, price in enumerate(distinct_prices, start=1):
        tier_number = 1 + math.floor(4 * (position - 1) / len(distinct_prices))
        tier_by_price[price] = VALUE_TIER_NAMES[min(tier_number, 4) - 1]
    return {
        normalize_key(row["product"]): tier_by_price[int(row["sales_price"])]
        for row in products
    }


def percentile(sorted_values: list[int], fraction: float) -> float:
    """Linear percentile equivalent to the default method used in the audit."""
    if not sorted_values:
        raise ValueError("Cannot calculate a percentile from an empty sequence")
    position = (len(sorted_values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(sorted_values[lower])
    weight = position - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * weight


def build(output_dir: Path) -> dict[str, Any]:
    pipeline = read_csv("sales_pipeline.csv")
    raw_accounts = read_csv("accounts.csv")
    raw_products = read_csv("products.csv")
    raw_teams = read_csv("sales_teams.csv")

    accounts = {row["account"]: row for row in raw_accounts}
    products = {normalize_key(row["product"]): row for row in raw_products}
    value_tiers = build_value_tiers(raw_products)

    known_dates = [
        parsed
        for row in pipeline
        for parsed in (parse_date(row.get("engage_date")), parse_date(row.get("close_date")))
        if parsed
    ]
    snapshot_date = max(known_dates)
    active_as_of = snapshot_date + timedelta(days=1)

    account_rows = [
        {
            "account": row["account"],
            "sector": normalize_sector(row.get("sector")) or "unknown",
            "year_established": row.get("year_established") or "",
            "revenue_musd": row.get("revenue") or "",
            "employees": row.get("employees") or "",
            "office_location": normalize_location(row.get("office_location")) or "",
            "subsidiary_of": row.get("subsidiary_of") or "",
        }
        for row in raw_accounts
    ]
    product_rows = [
        {
            "product_key": normalize_key(row["product"]),
            "product": row["product"],
            "series": row["series"],
            "sales_price": row["sales_price"],
            "value_tier": value_tiers[normalize_key(row["product"])],
        }
        for row in raw_products
    ]
    team_rows = [
        {
            "sales_agent": row["sales_agent"],
            "manager": row["manager"],
            "regional_office": row["regional_office"],
        }
        for row in raw_teams
    ]

    enriched: list[dict[str, Any]] = []
    for row in pipeline:
        product_key = normalize_key(row["product"])
        product = products[product_key]
        account = accounts.get(row.get("account") or "")
        engage_date = parse_date(row.get("engage_date"))
        close_date = parse_date(row.get("close_date"))
        if row["deal_stage"] in CLOSED_STAGES and engage_date:
            as_of = engage_date
        else:
            as_of = active_as_of

        if row["deal_stage"] == "Prospecting":
            age_days = None
        elif row["deal_stage"] in CLOSED_STAGES and engage_date and close_date:
            age_days = (close_date - engage_date).days
        elif engage_date:
            age_days = (snapshot_date - engage_date).days
        else:
            age_days = None

        enriched.append(
            {
                **row,
                "product_key": product_key,
                "product_name": product["product"],
                "ticket_tier": value_tiers[product_key],
                "potential_value": int(product["sales_price"]),
                "sector": normalize_sector(account.get("sector")) if account else None,
                "engage_date_value": engage_date,
                "close_date_value": close_date,
                "as_of": as_of,
                "age_days": age_days,
            }
        )

    closed_history = sorted(
        [row for row in enriched if row["deal_stage"] in CLOSED_STAGES and row["close_date_value"]],
        key=lambda row: row["close_date_value"],
    )
    closed_cycles = sorted(
        row["age_days"] for row in closed_history if row["age_days"] is not None
    )
    warmth_quartiles = {
        "q1": percentile(closed_cycles, 0.25),
        "q2": percentile(closed_cycles, 0.50),
        "q3": percentile(closed_cycles, 0.75),
    }
    max_price = max(int(row["sales_price"]) for row in raw_products)

    global_counters = {
        "sector": empty_counter(),
        "product": empty_counter(),
        "ticket": empty_counter(),
        "match": empty_counter(),
    }
    seller_counters: dict[str, dict[str, dict[Any, list[int]]]] = defaultdict(
        lambda: {
            "sector": empty_counter(),
            "product": empty_counter(),
            "ticket": empty_counter(),
        }
    )

    def ingest_history(row: dict[str, Any]) -> None:
        won = row["deal_stage"] == "Won"
        match_key = (row["sector"], row["product_key"], row["ticket_tier"])
        add_history(global_counters["sector"], row["sector"], won)
        add_history(global_counters["product"], row["product_key"], won)
        add_history(global_counters["ticket"], row["ticket_tier"], won)
        add_history(global_counters["match"], match_key, won)
        seller = seller_counters[row["sales_agent"]]
        add_history(seller["sector"], row["sector"], won)
        add_history(seller["product"], row["product_key"], won)
        add_history(seller["ticket"], row["ticket_tier"], won)

    opportunity_rows: list[dict[str, Any]] = []
    score_rows: list[dict[str, Any]] = []
    history_index = 0

    for row in sorted(enriched, key=lambda item: (item["as_of"], item["opportunity_id"])):
        while (
            history_index < len(closed_history)
            and closed_history[history_index]["close_date_value"] < row["as_of"]
        ):
            ingest_history(closed_history[history_index])
            history_index += 1

        match_key = (row["sector"], row["product_key"], row["ticket_tier"])
        propensity_lenses = [
            {"name": "sector", **counter_read(global_counters["sector"], row["sector"])},
            {"name": "product", **counter_read(global_counters["product"], row["product_key"])},
            {"name": "ticket", **counter_read(global_counters["ticket"], row["ticket_tier"])},
            {"name": "full_match", **counter_read(global_counters["match"], match_key)},
        ]
        propensity_score = score_propensity(propensity_lenses)

        seller = seller_counters[row["sales_agent"]]
        execution_fits = []
        for name, key in (
            ("product", row["product_key"]),
            ("sector", row["sector"]),
            ("ticket", row["ticket_tier"]),
        ):
            evidence = counter_read(seller[name], key)
            execution_fits.append(
                {
                    "name": name,
                    "won": evidence["won"],
                    "acted": evidence["cases"],
                    "fit": evidence["win_rate"],
                }
            )
        execution_score = score_execution(execution_fits)

        opportunity_value_score = 100 * row["potential_value"] / max_price
        if row["deal_stage"] == "Prospecting" or row["age_days"] is None:
            warmth_score = 0.0
            temperature = "Sem contato"
            historical_survivors = 0
        else:
            historical_survivors = len(closed_cycles) - bisect.bisect_left(closed_cycles, row["age_days"])
            warmth_score = 100 * historical_survivors / len(closed_cycles)
            if row["age_days"] <= warmth_quartiles["q1"]:
                temperature = "Quente"
            elif row["age_days"] <= warmth_quartiles["q2"]:
                temperature = "Morna"
            elif row["age_days"] <= warmth_quartiles["q3"]:
                temperature = "Fria"
            else:
                temperature = "Estagnada"

        propensity_evidence = {
            "as_of": row["as_of"].isoformat(),
            "history_threshold": PROPENSITY_HISTORY_THRESHOLD,
            "lenses": propensity_lenses,
            "warning": "Product, ticket and full match are correlated in this dataset.",
        }
        warmth_evidence = {
            "age_days": row["age_days"],
            "historical_cycles": len(closed_cycles),
            "historical_cycles_at_least_this_long": historical_survivors,
        }
        execution_evidence = {
            "as_of": row["as_of"].isoformat(),
            "fits": execution_fits,
            "criteria_used": sum(fit["fit"] is not None for fit in execution_fits),
            "company_fit": {
                "status": "unavailable",
                "reason": "Firmographic similarity bands have not been defined yet.",
            },
        }

        score_payload = {
            "score_version": SCORE_VERSION,
            "opportunity_id": row["opportunity_id"],
            "stage": row["deal_stage"],
            "seller": row["sales_agent"],
            "product": row["product_key"],
            "account": row.get("account") or None,
            "propensity_score": round(propensity_score, 2) if propensity_score is not None else None,
            "opportunity_value_score": round(opportunity_value_score, 2),
            "warmth_score": round(warmth_score, 2),
            "execution_fit_score": round(execution_score, 2) if execution_score is not None else None,
        }

        opportunity_rows.append(
            {
                "opportunity_id": row["opportunity_id"],
                "sales_agent": row["sales_agent"],
                "product_key": row["product_key"],
                "account": row.get("account") or "",
                "deal_stage": row["deal_stage"],
                "engage_date": row.get("engage_date") or "",
                "close_date": row.get("close_date") or "",
                "close_value": row.get("close_value") or "",
                "snapshot_date": snapshot_date.isoformat(),
                "potential_value": row["potential_value"],
                "age_days": row["age_days"] if row["age_days"] is not None else "",
            }
        )
        score_rows.append(
            {
                "opportunity_id": row["opportunity_id"],
                "score_version": SCORE_VERSION,
                "input_hash": stable_hash(score_payload),
                "propensity_score": score_payload["propensity_score"] if score_payload["propensity_score"] is not None else "",
                "propensity_evidence": json_cell(propensity_evidence),
                "opportunity_value_score": score_payload["opportunity_value_score"],
                "opportunity_value_tier": row["ticket_tier"],
                "warmth_score": score_payload["warmth_score"],
                "warmth_temperature": temperature,
                "warmth_evidence": json_cell(warmth_evidence),
                "execution_fit_score": score_payload["execution_fit_score"] if score_payload["execution_fit_score"] is not None else "",
                "execution_fit_evidence": json_cell(execution_evidence),
            }
        )

    write_csv(output_dir / "accounts.csv", list(account_rows[0]), account_rows)
    write_csv(output_dir / "products.csv", list(product_rows[0]), product_rows)
    write_csv(output_dir / "sales_teams.csv", list(team_rows[0]), team_rows)
    write_csv(output_dir / "opportunities.csv", list(opportunity_rows[0]), opportunity_rows)
    write_csv(output_dir / "power_scores.csv", list(score_rows[0]), score_rows)

    assumptions = [
        "Distinct catalog prices are distributed across four relative value tiers by rank.",
        "The same catalog-derived value tiers are reused as ticket bands in P and E.",
        "Company Fit is omitted until firmographic similarity bands are defined.",
        "Closed opportunities use only history closed before their engage date for P and E.",
        "Active opportunities use all Won/Lost history available at the dataset snapshot.",
        "Warmth uses the empirical distribution and quartiles of all 6,711 closed cycles.",
    ]
    run_rows = [
        {
            "score_version": SCORE_VERSION,
            "snapshot_date": snapshot_date.isoformat(),
            "opportunity_count": len(opportunity_rows),
            "closed_history_count": len(closed_history),
            "propensity_history_threshold": PROPENSITY_HISTORY_THRESHOLD,
            "assumptions": json_cell(assumptions),
        }
    ]
    write_csv(output_dir / "power_score_runs.csv", list(run_rows[0]), run_rows)

    summary = {
        "score_version": SCORE_VERSION,
        "snapshot_date": snapshot_date.isoformat(),
        "rows": {
            "accounts": len(account_rows),
            "products": len(product_rows),
            "sales_teams": len(team_rows),
            "opportunities": len(opportunity_rows),
            "power_scores": len(score_rows),
        },
        "coverage": {
            "propensity": sum(row["propensity_score"] != "" for row in score_rows),
            "opportunity_value": len(score_rows),
            "warmth": len(score_rows),
            "execution_fit": sum(row["execution_fit_score"] != "" for row in score_rows),
        },
        "assumptions": assumptions,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    summary = build(args.output_dir.resolve())
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
