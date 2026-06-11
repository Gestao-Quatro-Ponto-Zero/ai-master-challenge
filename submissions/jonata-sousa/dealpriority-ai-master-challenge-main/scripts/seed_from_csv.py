#!/usr/bin/env python3
"""
Generate Supabase/Postgres seed.sql from ranked_open_deals_final.csv.

Run:
  python scripts/seed_from_csv.py
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


COLUMNS = [
    "opportunity_id", "account", "sales_agent", "manager", "regional_office",
    "product", "deal_stage", "engage_date", "close_value", "priority_score",
    "priority_label", "top_positive_reason_1", "top_positive_reason_2",
    "top_risk_reason_1", "top_risk_reason_2", "recommended_action",
]


def sql_literal(value: str | None) -> str:
    if value is None:
        return "NULL"

    value = str(value)
    if value == "" or value.lower() == "nan":
        return "NULL"

    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="ranked_open_deals_final.csv")
    parser.add_argument("--out", default="supabase/seed.sql")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    statements: list[str] = []

    statements.append("""-- DealPriority seed
-- Recreates the table used by the dashboard from ranked_open_deals_final.csv.

drop table if exists public.deals;

create table public.deals (
  opportunity_id text primary key,
  account text,
  sales_agent text,
  manager text,
  regional_office text,
  product text,
  deal_stage text,
  engage_date date,
  close_value numeric,
  priority_score numeric,
  priority_label text,
  top_positive_reason_1 text,
  top_positive_reason_2 text,
  top_risk_reason_1 text,
  top_risk_reason_2 text,
  recommended_action text
);
""")

    chunk_size = 250
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        values = []
        for row in chunk:
            values.append("(" + ", ".join(sql_literal(row.get(col)) for col in COLUMNS) + ")")

        statements.append(
            "insert into public.deals (" + ", ".join(COLUMNS) + ")\nvalues\n"
            + ",\n".join(values)
            + ";\n"
        )

    out_path.write_text("\n".join(statements), encoding="utf-8")
    print(f"Generated {out_path} with {len(rows)} rows.")


if __name__ == "__main__":
    main()
