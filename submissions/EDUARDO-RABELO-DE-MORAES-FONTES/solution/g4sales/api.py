import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from g4sales.schemas import (
    AccountOut,
    AccountScoreOut,
    HealthResponse,
    OpportunityOut,
    PipelineMetricsOut,
    ProductOut,
    SalesTeamOut,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "sales.sqlite3"

app = FastAPI(title="g4sales API", version="0.1.0")

# Keep CORS open during local frontend development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


DbConn = Annotated[sqlite3.Connection, Depends(get_connection)]


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/accounts", response_model=list[AccountOut])
def list_accounts(
    conn: DbConn,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[AccountOut]:
    rows = conn.execute(
        """
        SELECT
            account,
            sector,
            year_established,
            revenue,
            employees,
            office_location,
            subsidiary_of
        FROM accounts
        ORDER BY account
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()
    conn.close()
    return [AccountOut(**dict(row)) for row in rows]


@app.get("/products", response_model=list[ProductOut])
def list_products(
    conn: DbConn,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[ProductOut]:
    rows = conn.execute(
        """
        SELECT product, series, sales_price
        FROM products
        ORDER BY product
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()
    conn.close()
    return [ProductOut(**dict(row)) for row in rows]


@app.get("/sales-teams", response_model=list[SalesTeamOut])
def list_sales_teams(
    conn: DbConn,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[SalesTeamOut]:
    rows = conn.execute(
        """
        SELECT sales_agent, manager, regional_office
        FROM sales_teams
        ORDER BY sales_agent
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()
    conn.close()
    return [SalesTeamOut(**dict(row)) for row in rows]


@app.get("/opportunities", response_model=list[OpportunityOut])
def list_opportunities(
    conn: DbConn,
    limit: int = Query(default=100, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    deal_stage: str | None = None,
    sales_agent: str | None = None,
    manager: str | None = None,
    regional_office: str | None = None,
    account: str | None = None,
    product: str | None = None,
) -> list[OpportunityOut]:
    query = """
        SELECT
            sp.opportunity_id,
            sp.sales_agent,
            st.manager,
            st.regional_office,
            sp.product,
            p.series,
            sp.account,
            sp.deal_stage,
            sp.engage_date,
            sp.close_date,
            sp.close_value,
            p.sales_price
        FROM sales_pipeline sp
        LEFT JOIN sales_teams st ON st.sales_agent = sp.sales_agent
        LEFT JOIN products p ON p.product = sp.product
        WHERE 1=1
    """
    params: list[str | int] = []

    if deal_stage:
        query += " AND sp.deal_stage = ?"
        params.append(deal_stage)
    if sales_agent:
        query += " AND sp.sales_agent = ?"
        params.append(sales_agent)
    if manager:
        query += " AND st.manager = ?"
        params.append(manager)
    if regional_office:
        query += " AND st.regional_office = ?"
        params.append(regional_office)
    if account:
        query += " AND sp.account = ?"
        params.append(account)
    if product:
        query += " AND sp.product = ?"
        params.append(product)

    query += " ORDER BY sp.opportunity_id LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [OpportunityOut(**dict(row)) for row in rows]


@app.get("/metrics/pipeline", response_model=list[PipelineMetricsOut])
def pipeline_metrics(conn: DbConn) -> list[PipelineMetricsOut]:
    rows = conn.execute(
        """
        SELECT
            deal_stage,
            COUNT(*) AS opportunities,
            COALESCE(SUM(close_value), 0) AS total_value
        FROM sales_pipeline
        GROUP BY deal_stage
        ORDER BY deal_stage
        """
    ).fetchall()
    conn.close()
    return [PipelineMetricsOut(**dict(row)) for row in rows]


@app.get("/account-scores", response_model=list[AccountScoreOut])
def account_scores(
    conn: DbConn,
    limit: int = Query(default=2000, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
) -> list[AccountScoreOut]:
    rows = conn.execute(
        """
        WITH hist AS (
            SELECT
                account,
                SUM(CASE WHEN deal_stage = 'Won' THEN 1 ELSE 0 END) AS won_deals,
                SUM(CASE WHEN deal_stage = 'Lost' THEN 1 ELSE 0 END) AS lost_deals,
                SUM(
                    CASE WHEN deal_stage IN ('Won', 'Lost') THEN 1 ELSE 0 END
                ) AS closed_deals,
                AVG(CASE WHEN deal_stage = 'Won' THEN close_value END) AS avg_won_value
            FROM sales_pipeline
            WHERE account IS NOT NULL AND TRIM(account) <> ''
            GROUP BY account
        )
        SELECT
            account,
            won_deals,
            lost_deals,
            closed_deals,
            COALESCE(
                ROUND((won_deals * 1.0) / NULLIF(closed_deals, 0), 4),
                0
            ) AS win_rate,
            COALESCE(avg_won_value, 0) AS avg_won_value,
            ROUND(
                MIN(
                    100,
                    MAX(
                        0,
                        45 * COALESCE((won_deals * 1.0) / NULLIF(closed_deals, 0), 0)
                        + MIN(COALESCE(avg_won_value, 0) / 150, 35)
                        + MIN(COALESCE(closed_deals, 0) * 1.0, 20)
                    )
                ),
                2
            ) AS account_score
        FROM hist
        ORDER BY account_score DESC, account ASC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()
    conn.close()
    return [AccountScoreOut(**dict(row)) for row in rows]
