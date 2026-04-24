import pandas as pd
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def _normalize_str(series: pd.Series) -> pd.Series:
    """Strip whitespace and normalize case for join keys."""
    return series.astype(str).str.strip()


def load_and_merge() -> pd.DataFrame:
    pipeline = pd.read_csv(DATA_DIR / "sales_pipeline.csv")
    accounts = pd.read_csv(DATA_DIR / "accounts.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")
    teams = pd.read_csv(DATA_DIR / "sales_teams.csv")

    # ── Normalize all join keys (strip whitespace) ───────────────────────────
    pipeline["sales_agent"] = _normalize_str(pipeline["sales_agent"])
    pipeline["product"] = _normalize_str(pipeline["product"])
    # account is genuinely NaN for 1425 rows — preserve NaN, strip valid ones
    pipeline["account"] = pipeline["account"].where(pipeline["account"].isna(),
                                                     pipeline["account"].str.strip())

    accounts["account"] = _normalize_str(accounts["account"])
    products["product"] = _normalize_str(products["product"])
    teams["sales_agent"] = _normalize_str(teams["sales_agent"])

    # Known product name mismatch: pipeline uses "GTXPro", table uses "GTX Pro"
    pipeline["product"] = pipeline["product"].replace("GTXPro", "GTX Pro")

    open_before = pipeline[pipeline["deal_stage"].isin(["Engaging", "Prospecting"])].shape[0]

    df = (
        pipeline
        .merge(accounts, on="account", how="left")
        .merge(products, on="product", how="left")
        .merge(teams, on="sales_agent", how="left")
    )

    # ── Report unmatched join keys ───────────────────────────────────────────
    unmatched_accounts = set(
        pipeline.loc[pipeline["account"].notna(), "account"].unique()
    ) - set(accounts["account"].unique())
    unmatched_products = set(pipeline["product"].unique()) - set(products["product"].unique())
    unmatched_agents = set(pipeline["sales_agent"].unique()) - set(teams["sales_agent"].unique())

    nan_sector = df["sector"].isna().sum()
    nan_manager = df["manager"].isna().sum()
    nan_regional = df["regional_office"].isna().sum()

    print(f"[merge] open deals before merge: {open_before}")
    print(f"[merge] unmatched accounts (non-NaN): {unmatched_accounts or 'none'}")
    print(f"[merge] unmatched products: {unmatched_products or 'none'}")
    print(f"[merge] unmatched agents: {unmatched_agents or 'none'}")
    print(f"[merge] NaN after merge — sector:{nan_sector} manager:{nan_manager} regional:{nan_regional}")
    print(f"[merge] root cause: {pipeline['account'].isna().sum()} rows have genuinely null account in source CSV")

    # ── Fill remaining NaNs with "Desconhecido" ───────────────────────────────
    str_cols = ["account", "sector", "year_established", "office_location",
                "subsidiary_of", "manager", "regional_office", "series"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].fillna("Desconhecido")

    df["engage_date"] = pd.to_datetime(df["engage_date"], errors="coerce")
    df["close_date"] = pd.to_datetime(df["close_date"], errors="coerce")

    today = pd.Timestamp(date.today())
    df["days_in_pipeline"] = (today - df["engage_date"]).dt.days.fillna(0).astype(int)

    # Revenue in millions USD (per metadata.csv)
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0)
    df["employees"] = pd.to_numeric(df["employees"], errors="coerce").fillna(0)
    df["sales_price"] = pd.to_numeric(df["sales_price"], errors="coerce").fillna(0)
    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce").fillna(0)

    # Open deals have no close_value — use product sales_price as expected value
    df["effective_value"] = df["close_value"].where(df["close_value"] > 0, df["sales_price"])

    open_after = df[df["deal_stage"].isin(["Engaging", "Prospecting"])].shape[0]
    print(f"[merge] open deals after merge: {open_after}")

    return df


def compute_win_rates(df: pd.DataFrame) -> tuple[dict, dict]:
    closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    closed["won"] = (closed["deal_stage"] == "Won").astype(int)

    def win_rate_dict(group_col):
        grp = closed.groupby(group_col)["won"].agg(["sum", "count"])
        grp["win_rate"] = grp["sum"] / grp["count"]
        return grp["win_rate"].to_dict()

    return win_rate_dict("sector"), win_rate_dict("sales_agent")


def score_deal(row, sector_wr: dict, agent_wr: dict, max_value: float) -> tuple[int, str, dict]:
    breakdown = {}

    # 1. Deal stage (max 30)
    stage_scores = {"Engaging": 30, "Prospecting": 15}
    breakdown["Estágio do deal"] = stage_scores.get(row["deal_stage"], 0)

    # 2. Days in pipeline (max 20)
    days = int(row["days_in_pipeline"])
    if days <= 30:
        days_score = 20
    elif days <= 60:
        days_score = 15
    elif days <= 90:
        days_score = 8
    elif days <= 180:
        days_score = 3
    else:
        days_score = 0
    breakdown["Tempo no pipeline"] = days_score

    # 3. Deal value relative to max (max 20)
    val = float(row["effective_value"]) if max_value > 0 else 0
    value_score = round((val / max_value) * 20) if max_value > 0 else 0
    breakdown["Valor do deal"] = value_score

    # 4. Sector win rate — from historical data (max 15)
    sector_score = round(sector_wr.get(row.get("sector", ""), 0.5) * 15)
    breakdown["Win rate do setor"] = sector_score

    # 5. Agent win rate — from historical data (max 10)
    agent_score = round(agent_wr.get(row.get("sales_agent", ""), 0.5) * 10)
    breakdown["Win rate do vendedor"] = agent_score

    # 6. Account size — revenue in millions USD (max 5)
    rev = float(row.get("revenue", 0))
    emp = float(row.get("employees", 0))
    if rev > 10 or emp > 500:
        size_score = 5
    elif rev > 1 or emp > 100:
        size_score = 3
    else:
        size_score = 1
    breakdown["Tamanho da conta"] = size_score

    score = sum(breakdown.values())
    tier = "A" if score >= 70 else ("B" if score >= 40 else "C")

    return score, tier, breakdown


def score_all(df: pd.DataFrame) -> pd.DataFrame:
    open_deals = df[df["deal_stage"].isin(["Engaging", "Prospecting"])].copy()

    sector_wr, agent_wr = compute_win_rates(df)
    max_value = open_deals["effective_value"].max()
    if max_value == 0:
        max_value = 1

    results = open_deals.apply(
        lambda row: pd.Series(score_deal(row, sector_wr, agent_wr, max_value)),
        axis=1,
    )
    results.columns = ["score", "tier", "breakdown"]

    scored = open_deals.copy()
    scored["score"] = results["score"].astype(int)
    scored["tier"] = results["tier"]
    scored["breakdown"] = results["breakdown"]

    return scored.sort_values("score", ascending=False).reset_index(drop=True)
