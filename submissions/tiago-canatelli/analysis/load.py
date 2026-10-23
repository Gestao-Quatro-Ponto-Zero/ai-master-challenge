"""Carrega as tabelas do silver em DataFrames (uma consulta por tabela)."""

import pandas as pd
import psycopg

from ravenlake.settings import Settings

TABLES = ("accounts", "subscriptions", "feature_usage", "support_tickets", "churn_events")


def load_silver() -> dict[str, pd.DataFrame]:
    url = Settings().database_url.get_secret_value()  # type: ignore[call-arg]
    frames: dict[str, pd.DataFrame] = {}
    with psycopg.connect(url, prepare_threshold=None) as conn:
        for table in TABLES:
            with conn.cursor() as cur:
                cur.execute(f"select * from silver.{table}")  # nomes fixos, sem entrada externa
                cols = [d.name for d in cur.description or []]
                frames[table] = pd.DataFrame(cur.fetchall(), columns=cols)
    for df in frames.values():
        for col in df.columns:
            if col.endswith(("_date",)) or col in ("submitted_at", "closed_at"):
                df[col] = (
                    pd.to_datetime(df[col], utc=col.endswith("_at")).dt.tz_localize(None)
                    if col.endswith("_at")
                    else pd.to_datetime(df[col])
                )
            if df[col].dtype == object and col.endswith(("amount", "_usd", "_hours")):
                df[col] = df[col].astype(float)
    return frames
