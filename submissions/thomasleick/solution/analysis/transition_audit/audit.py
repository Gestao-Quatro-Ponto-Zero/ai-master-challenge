"""Audit explicit subscription-row transition flags against inferred plan changes.

The source flags have account/subscription row scope. They do not name a from/to
subscription pair or a transition date, so this module never promotes them to a
confirmed migration.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


def _truth(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _number(value: str | None) -> Decimal | None:
    try:
        return Decimal(str(value)) if value not in (None, "") else None
    except InvalidOperation:
        return None


def classify_transition(*, source_flag: bool, target_flag: bool, interval_link: bool, hierarchy_verified: bool) -> str:
    """Conservative classification of a candidate transition pair."""
    if interval_link and hierarchy_verified and (source_flag or target_flag):
        return "INFERRED"
    return "POSSIBLE" if source_flag or target_flag or interval_link else "UNCLASSIFIED"


def audit(data_dir: Path, ledger_path: Path) -> dict[str, Any]:
    data_dir, ledger_path = Path(data_dir), Path(ledger_path)
    with (data_dir / "ravenstack_subscriptions.csv").open(newline="", encoding="utf-8-sig") as handle:
        subscriptions = list(csv.DictReader(handle))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    upgrade = [row for row in subscriptions if _truth(row.get("upgrade_flag"))]
    downgrade = [row for row in subscriptions if _truth(row.get("downgrade_flag"))]
    both = [row for row in subscriptions if _truth(row.get("upgrade_flag")) and _truth(row.get("downgrade_flag"))]
    by_tier: dict[str, Counter[str]] = defaultdict(Counter)
    by_billing: dict[str, Counter[str]] = defaultdict(Counter)
    null_end: Counter[str] = Counter()
    amount_by_flag: dict[str, list[Decimal]] = defaultdict(list)
    accounts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in subscriptions:
        tier = row.get("plan_tier") or "UNKNOWN"
        billing = row.get("billing_frequency") or "UNKNOWN"
        up, down = _truth(row.get("upgrade_flag")), _truth(row.get("downgrade_flag"))
        if up:
            by_tier[tier]["upgrade_rows"] += 1
            by_billing[billing]["upgrade_rows"] += 1
            accounts[row["account_id"]]["upgrade_rows"] += 1
        if down:
            by_tier[tier]["downgrade_rows"] += 1
            by_billing[billing]["downgrade_rows"] += 1
            accounts[row["account_id"]]["downgrade_rows"] += 1
        if up and down:
            by_tier[tier]["both_rows"] += 1
        if not row.get("end_date"):
            if up:
                null_end["upgrade_rows"] += 1
            if down:
                null_end["downgrade_rows"] += 1
        amount = _number(row.get("mrr_amount"))
        if amount is not None:
            if up:
                amount_by_flag["upgrade"].append(amount)
            if down:
                amount_by_flag["downgrade"].append(amount)
    candidates = ledger["plan_transition_analysis"].get("candidate_transitions", [])
    windows = ledger["plan_transition_analysis"].get("windows_days", {})
    rows = []
    for candidate in candidates:
        flags = accounts.get(candidate["account_id"], Counter())
        rows.append({
            **candidate,
            "account_has_upgrade_flag": flags["upgrade_rows"] > 0,
            "account_has_downgrade_flag": flags["downgrade_rows"] > 0,
            "transition_flag_link": "UNKNOWN; flags are not tied to candidate subscription IDs or dates",
            "tier_hierarchy": "ASSUMED ONLY; no verified rank field",
            "classification": "POSSIBLE_ONLY",
        })
    def amount_summary(name: str) -> dict[str, Any]:
        values = amount_by_flag[name]
        ordered = sorted(values)
        midpoint = len(ordered) // 2
        median = (ordered[midpoint] if len(ordered) % 2 else (ordered[midpoint - 1] + ordered[midpoint]) / 2) if ordered else None
        return {
            "rows_with_numeric_mrr_amount": len(values),
            "min_recorded_mrr_amount": str(min(values)) if values else None,
            "median_recorded_mrr_amount": str(median) if median is not None else None,
            "max_recorded_mrr_amount": str(max(values)) if values else None,
            "interpretation": "Row values only; currency/effective period/contract version and transition linkage are not reconciled.",
        }
    result = {
        "classification": "ROW_FLAGS_OBSERVED; MIGRATION_NOT_CONFIRMED",
        "source_rows": len(subscriptions),
        "explicit_flags": {
            "upgrade_flag_rows": len(upgrade),
            "downgrade_flag_rows": len(downgrade),
            "rows_with_both_flags": len(both),
            "accounts_with_upgrade_flag": len({row["account_id"] for row in upgrade}),
            "accounts_with_downgrade_flag": len({row["account_id"] for row in downgrade}),
            "flagged_rows_with_null_end_date": dict(null_end),
            "by_plan_tier": {key: dict(value) for key, value in sorted(by_tier.items())},
            "by_billing_frequency": {key: dict(value) for key, value in sorted(by_billing.items())},
            "recorded_mrr_amount_by_flag": {key: amount_summary(key) for key in ("upgrade", "downgrade")},
        },
        "candidate_transition_windows": windows,
        "candidate_transitions": rows,
        "classification_counts": {
            "confirmed": 0,
            "inferred": 0,
            "possible": len(rows),
            "possible_upgrade_pairs_30d": windows.get("30", {}).get("possible_upgrade_pairs", 0),
            "possible_downgrade_pairs_30d": windows.get("30", {}).get("possible_downgrade_pairs", 0),
        },
        "methodology": [
            "Source upgrade_flag and downgrade_flag rows are counted directly from ravenstack_subscriptions.csv.",
            "Flags are not joined to specific outgoing/incoming subscription IDs; account-level coincidence does not confirm a transition.",
            "Candidate pairs are inherited from the daily ledger's assumed Basic < Pro < Enterprise ordering and 0/1/7/30-day windows.",
            "No verified tier hierarchy, explicit from/to foreign key, dated transition field, or reconciled effective-dated price is available.",
            "Recorded mrr_amount values are described but never summed as recurring revenue contraction or expansion.",
        ],
    }
    return result


def write(data_dir: Path, ledger_path: Path, output_dir: Path) -> dict[str, Any]:
    result = audit(data_dir, ledger_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "transition-audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (output_dir / "transition-candidates.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(result["candidate_transitions"][0]) if result["candidate_transitions"] else ["date", "account_id", "classification"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result["candidate_transitions"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).parents[3] / "data" / "raw")
    parser.add_argument("--ledger", type=Path, default=Path(__file__).parents[3] / "analysis/daily_portfolio_churn/outputs/g4-alignment/daily-portfolio-churn.json")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "outputs")
    args = parser.parse_args()
    print(json.dumps(write(args.data_dir, args.ledger, args.output_dir)["classification_counts"], indent=2))


if __name__ == "__main__":
    main()
