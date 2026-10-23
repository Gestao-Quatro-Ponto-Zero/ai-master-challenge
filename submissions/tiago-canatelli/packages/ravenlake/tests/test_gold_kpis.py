"""Confere KPIs do gold (Supabase SaaS) contra recálculo direto nos CSVs. Só leitura."""

import csv
from collections import Counter
from datetime import date
from pathlib import Path

import pytest

from ravenlake import pipeline
from ravenlake.settings import MONOREPO_ROOT, Settings

DATA = MONOREPO_ROOT.parents[1] / "datasets" / "kaggle-rivalytics"
pytestmark = [
    pytest.mark.db,
    pytest.mark.skipif(not DATA.exists(), reason="CSVs locais não encontrados"),
]


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / f"ravenstack_{name}.csv").open() as f:
        return list(csv.DictReader(f))


def months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + b.month - a.month


@pytest.fixture(scope="module")
def conn():  # type: ignore[no-untyped-def]
    with pipeline.connect(Settings().database_url.get_secret_value()) as c:  # type: ignore[call-arg]
        yield c


def test_hazard_2024q4_new_accounts_matches_csv(conn) -> None:  # type: ignore[no-untyped-def]
    signup = {r["account_id"]: date.fromisoformat(r["signup_date"]) for r in rows("accounts")}
    q4 = [r for r in rows("churn_events") if r["churn_date"] >= "2024-10"]
    events = Counter((r["account_id"], r["churn_date"][:7]) for r in q4)
    exposure = churns = 0
    for acc, s in signup.items():
        for month in (date(2024, 10, 1), date(2024, 11, 1), date(2024, 12, 1)):
            ten = months_between(s, month)
            if 0 <= ten < 3:
                exposure += 1
                churns += events[(acc, month.isoformat()[:7])]
    expected = round(100 * churns / exposure, 2)

    row = conn.execute(
        """select churn_per_100_account_months from gold.kpi_tenure_hazard
            where quarter = '2024Q4' and tenure_bucket = '0-3m'"""
    ).fetchone()
    assert float(row[0]) == pytest.approx(expected, abs=0.01)


def test_churn_events_and_refunds_match_csv(conn) -> None:  # type: ignore[no-untyped-def]
    ce = rows("churn_events")
    row = conn.execute(
        "select count(*), sum(refund_amount_usd) from gold.fct_churn_event"
    ).fetchone()
    assert row[0] == len(ce)
    assert float(row[1]) == pytest.approx(sum(float(r["refund_amount_usd"]) for r in ce), abs=0.01)


def test_csat_scale_and_response_rate_match_csv(conn) -> None:  # type: ignore[no-untyped-def]
    t = rows("support_tickets")
    scored = [float(r["satisfaction_score"]) for r in t if r["satisfaction_score"]]
    row = conn.execute(
        """select min(csat_min_observed), max(csat_max_observed),
                  sum(tickets * csat_response_pct / 100) / sum(tickets)
             from gold.kpi_support_health"""
    ).fetchone()
    assert (float(row[0]), float(row[1])) == (min(scored), max(scored))
    assert float(row[2]) == pytest.approx(len(scored) / len(t), abs=0.001)


def test_risk_scores_cover_active_accounts(conn) -> None:  # type: ignore[no-untyped-def]
    row = conn.execute(
        """select (select count(*) from gold.dim_account where is_active),
                  (select count(*) from gold.risk_scores
                    where scored_at = (select max(scored_at) from gold.risk_scores)),
                  (select count(*) from gold.risk_scores
                    where probability_90d not between 0 and 1)"""
    ).fetchone()
    assert row[0] == row[1]
    assert row[2] == 0


def test_dataset_path_points_to_downloaded_csvs() -> None:
    assert Path(DATA / "ravenstack_accounts.csv").exists()
