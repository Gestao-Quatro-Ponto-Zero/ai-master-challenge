"""Carrega DS1 e DS2 (data/raw/) nas tabelas ds1_tickets e ds2_tickets do Supabase via COPY.

Pré-requisitos:
  - migration solution/supabase/migrations/20261109000001_raw_datasets.sql aplicada;
  - SUPABASE_DB_URL no .env (Supabase → Connect → "Session pooler", compatível com IPv4).

Idempotente: trunca as tabelas antes de carregar.
Uso: .venv/bin/python scripts/load_raw_datasets.py [--migrate]
  --migrate  aplica antes os .sql de solution/supabase/migrations/ (todos idempotentes)
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg

ROOT = Path(__file__).resolve().parents[1]
SEED, TEST_SHARE = 42, 0.2


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.split(" #")[0].strip())


def ds1() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data/raw/ds1_customer_support/customer_support_tickets.csv")
    out = pd.DataFrame({
        "ticket_id": df["Ticket ID"],
        "customer_name": df["Customer Name"],
        "customer_email": df["Customer Email"],
        "customer_age": df["Customer Age"],
        "customer_gender": df["Customer Gender"],
        "product_purchased": df["Product Purchased"],
        "date_of_purchase": df["Date of Purchase"],
        "ticket_type": df["Ticket Type"],
        "ticket_subject": df["Ticket Subject"],
        "ticket_description": df["Ticket Description"],
        "ticket_status": df["Ticket Status"],
        "resolution": df["Resolution"],
        "ticket_priority": df["Ticket Priority"],
        "ticket_channel": df["Ticket Channel"],
        "first_response_at": df["First Response Time"],
        "resolved_at": df["Time to Resolution"],
        "csat": df["Customer Satisfaction Rating"].astype("Int64"),
    })
    return out


def ds2() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data/raw/ds2_it_tickets/all_tickets_processed_improved_v3.csv")
    rng = np.random.default_rng(SEED)
    split = pd.Series("train", index=df.index)
    for _, idx in df.groupby("Topic_group").groups.items():  # estratificado por categoria
        idx = np.array(idx)
        test = rng.choice(idx, size=round(len(idx) * TEST_SHARE), replace=False)
        split.loc[test] = "test"
    return pd.DataFrame({"id": df.index, "document": df["Document"],
                         "topic_group": df["Topic_group"], "split": split})


def copy(conn: psycopg.Connection, table: str, df: pd.DataFrame) -> None:
    cols = ", ".join(df.columns)
    rows = df.astype(object).where(df.notna(), None).itertuples(index=False, name=None)
    with conn.cursor() as cur:
        cur.execute(f"truncate public.{table}")
        with cur.copy(f"copy public.{table} ({cols}) from stdin") as cp:
            for row in rows:
                cp.write_row(row)
        cur.execute(f"select count(*) from public.{table}")
        print(f"{table}: {cur.fetchone()[0]} linhas")


if __name__ == "__main__":
    load_env()
    url = os.environ.get("SUPABASE_DB_URL")
    if not url:
        raise SystemExit("Defina SUPABASE_DB_URL no .env (Supabase → Connect → Session pooler).")
    d1, d2 = ds1(), ds2()
    print("split DS2:", d2["split"].value_counts().to_dict())
    with psycopg.connect(url) as conn:
        if "--migrate" in sys.argv:
            for sql in sorted((ROOT / "solution/supabase/migrations").glob("*.sql")):
                conn.execute(sql.read_text())
                print("migration aplicada:", sql.name)
        copy(conn, "ds1_tickets", d1)
        copy(conn, "ds2_tickets", d2)
        conn.commit()
