"""
Database helper for analysis notebooks.
Connects directly to Supabase Postgres for full SQL support.
Also provides Supabase client for table operations and writes.
"""

import os
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# Load .env.local from project root
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env.local")

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_client():
    """Returns a Supabase client (uses service role key for full access)."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_pg_connection():
    """Returns a direct Postgres connection for raw SQL queries."""
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    # Fallback: derive from Supabase URL (cloud projects)
    # Format: https://<project-ref>.supabase.co -> postgresql://postgres:<service-key>@db.<project-ref>.supabase.co:5432/postgres
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
        return psycopg2.connect(
            host=f"db.{project_ref}.supabase.co",
            port=5432,
            dbname="postgres",
            user="postgres",
            password=SUPABASE_SERVICE_KEY,
        )
    raise ValueError("No DATABASE_URL or SUPABASE_URL configured in .env.local")


def run_query(sql: str, params=None) -> pd.DataFrame:
    """Execute raw SQL and return results as a DataFrame."""
    conn = get_pg_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if cur.description:
                rows = cur.fetchall()
                return pd.DataFrame(rows)
            return pd.DataFrame()
    finally:
        conn.close()


def query_to_df(table: str, columns="*", filters=None, limit=None) -> pd.DataFrame:
    """Query a table using Supabase client, return as DataFrame."""
    client = get_client()
    query = client.table(table).select(columns)
    if filters:
        for col, val in filters.items():
            query = query.eq(col, val)
    if limit:
        query = query.limit(limit)
    result = query.execute()
    return pd.DataFrame(result.data)


def save_finding(
    phase: str,
    category: str,
    title: str,
    description: str,
    evidence: dict,
    impact_hours: float,
    impact_cost: float,
    priority: str,
    recommendation: str,
) -> dict:
    """Save an analysis finding to the process_findings table."""
    client = get_client()
    result = client.table("process_findings").insert({
        "phase": phase,
        "category": category,
        "title": title,
        "description": description,
        "evidence": evidence,
        "impact_hours_month": impact_hours,
        "impact_cost_month": impact_cost,
        "priority": priority,
        "recommendation": recommendation,
    }).execute()
    return result.data[0] if result.data else {}


def save_classification(
    table: str,
    record_id: int,
    category: str,
    confidence: float,
    model: str,
    reasoning: str = None,
) -> dict:
    """Update llm_* columns on a ticket record."""
    client = get_client()
    update = {
        "llm_category": category,
        "llm_confidence": confidence,
        "llm_model": model,
    }
    if reasoning and table == "support_tickets":
        update["llm_reasoning"] = reasoning
    result = client.table(table).update(update).eq("id", record_id).execute()
    return result.data[0] if result.data else {}


def table_info(table: str) -> pd.DataFrame:
    """Get column names, types, and nullable info for a table."""
    return run_query(
        """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table,),
    )


def row_count(table: str) -> int:
    """Get the row count for a table."""
    df = run_query(f"SELECT COUNT(*) as count FROM {table}")
    return int(df["count"].iloc[0]) if len(df) > 0 else 0
