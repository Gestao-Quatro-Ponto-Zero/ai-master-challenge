import numpy as np
import pandas as pd
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

MONTH_NAMES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


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


def compute_win_rates(df: pd.DataFrame) -> tuple[dict, dict, dict, dict]:
    closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    closed["won"] = (closed["deal_stage"] == "Won").astype(int)

    def win_rate_dict(group_col):
        grp = closed.groupby(group_col)["won"].agg(["sum", "count"])
        grp["win_rate"] = grp["sum"] / grp["count"]
        return grp["win_rate"].to_dict()

    # Monthly win rate: key is month number (1–12)
    closed["engage_month"] = closed["engage_date"].dt.month
    month_grp = closed.groupby("engage_month")["won"].agg(["sum", "count"])
    month_grp["win_rate"] = month_grp["sum"] / month_grp["count"]
    month_wr = month_grp["win_rate"].to_dict()

    # Combined agent+sector win rate (min 10 deals for statistical reliability)
    agent_sector_wr = {}
    for (agent, sector), group in closed.groupby(["sales_agent", "sector"]):
        total = len(group)
        if total >= 10:
            wins = (group["deal_stage"] == "Won").sum()
            agent_sector_wr[(agent, sector)] = wins / total

    return win_rate_dict("sector"), win_rate_dict("sales_agent"), month_wr, agent_sector_wr


def score_deal(row, sector_wr: dict, agent_wr: dict, max_value: float, month_wr: dict, agent_sector_wr: dict) -> tuple[int, str, dict]:
    breakdown = {}

    # 1. Deal stage (max 30)
    stage_scores = {"Engaging": 30, "Prospecting": 15}
    breakdown["Estágio do deal"] = stage_scores.get(row["deal_stage"], 0)

    # 2. Sazonalidade: win rate histórico do mês de engage_date (max 20)
    engage_month = row["engage_date"].month if pd.notna(row["engage_date"]) else None
    month_wr_val = month_wr.get(engage_month, 0.5)
    season_score = round(month_wr_val * 20)
    if engage_month:
        month_name = MONTH_NAMES_PT.get(engage_month, str(engage_month))
        season_label = f"Sazonalidade — {month_name} ({round(month_wr_val * 100)}% win rate)"
    else:
        season_label = "Sazonalidade — mês desconhecido"
    breakdown[season_label] = season_score

    # 3. Deal value relative to max (max 20)
    val = float(row["effective_value"]) if max_value > 0 else 0
    value_score = round((val / max_value) * 20) if max_value > 0 else 0
    breakdown["Valor do deal"] = value_score

    # 4. Sector win rate — from historical data (max 15)
    sector_score = round(sector_wr.get(row.get("sector", ""), 0.5) * 15)
    breakdown["Win rate do setor"] = sector_score

    # 5. Agent+sector combined win rate — fallback to agent win rate (max 10)
    agent  = row.get("sales_agent", "")
    sector_val = row.get("sector", "")
    combo_key = (agent, sector_val)
    if combo_key in agent_sector_wr:
        combo_wr = agent_sector_wr[combo_key]
        wr_label = "Win rate vendedor+setor"
    else:
        combo_wr = agent_wr.get(agent, 0.5)
        wr_label = "Win rate vendedor"
    combo_wr_pts = round(combo_wr * 10)
    breakdown[wr_label] = combo_wr_pts

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

    sector_wr, agent_wr, month_wr, agent_sector_wr = compute_win_rates(df)
    max_value = float(open_deals["effective_value"].max()) or 1.0

    # ── 1. Stage pts (vectorized) ────────────────────────────────────────────
    stage_pts = (
        open_deals["deal_stage"]
        .map({"Engaging": 30, "Prospecting": 15})
        .fillna(0)
        .astype(int)
    )

    # ── 2. Sazonalidade pts (vectorized) ────────────────────────────────────
    engage_month = open_deals["engage_date"].dt.month
    month_wr_vals = engage_month.map(month_wr).fillna(0.5)
    season_pts = (month_wr_vals * 20).round().astype(int)

    # ── 3. Value pts (vectorized) ────────────────────────────────────────────
    value_pts = (
        (open_deals["effective_value"] / max_value * 20)
        .round()
        .clip(0, 20)
        .astype(int)
    )

    # ── 4. Sector win rate pts (vectorized) ──────────────────────────────────
    sector_pts = (
        (open_deals["sector"].map(sector_wr).fillna(0.5) * 15)
        .round()
        .astype(int)
    )

    # ── 5. Agent+sector combo pts (plain Python loop — no pd.Series overhead) ─
    _agents  = open_deals["sales_agent"].values
    _sectors = open_deals["sector"].values
    _combo_pts_list:   list[int] = []
    _combo_label_list: list[str] = []
    for _ag, _sec in zip(_agents, _sectors):
        _key = (_ag, _sec)
        if _key in agent_sector_wr:
            _combo_pts_list.append(round(agent_sector_wr[_key] * 10))
            _combo_label_list.append("Win rate vendedor+setor")
        else:
            _combo_pts_list.append(round(agent_wr.get(_ag, 0.5) * 10))
            _combo_label_list.append("Win rate vendedor")
    combo_pts    = pd.Series(_combo_pts_list,   index=open_deals.index, dtype=int)
    combo_labels = pd.Series(_combo_label_list, index=open_deals.index)

    # ── 6. Account size pts (np.select vectorized) ───────────────────────────
    rev = open_deals["revenue"].astype(float)
    emp = open_deals["employees"].astype(float)
    size_pts_arr = np.select(
        condlist=[(rev > 10) | (emp > 500), (rev > 1) | (emp > 100)],
        choicelist=[5, 3],
        default=1,
    )
    size_pts = pd.Series(size_pts_arr, index=open_deals.index)

    # ── Score & tier (vectorized) ────────────────────────────────────────────
    score = (
        stage_pts + season_pts + value_pts + sector_pts + combo_pts + size_pts
    ).clip(0, 100).astype(int)

    tier = pd.cut(
        score,
        bins=[-1, 39, 69, 100],
        labels=["C", "B", "A"],
    ).astype(str)

    # ── Breakdown dicts (Python loop with array indexing — display only) ─────
    _stage_arr   = stage_pts.values
    _season_arr  = season_pts.values
    _value_arr   = value_pts.values
    _sector_arr  = sector_pts.values
    _combo_arr   = combo_pts.values
    _size_arr2   = size_pts.values
    _month_arr   = engage_month.values
    _mwr_arr     = month_wr_vals.values
    _labels_arr  = combo_labels.values

    breakdowns = []
    for i in range(len(open_deals)):
        _m   = _month_arr[i]
        _mwr = _mwr_arr[i]
        if not np.isnan(float(_m)) if _m is not None else False:
            _season_label = (
                f"Sazonalidade — {MONTH_NAMES_PT.get(int(_m), str(int(_m)))} "
                f"({round(_mwr * 100)}% win rate)"
            )
        else:
            _season_label = "Sazonalidade — mês desconhecido"
        breakdowns.append({
            "Estágio do deal":   int(_stage_arr[i]),
            _season_label:       int(_season_arr[i]),
            "Valor do deal":     int(_value_arr[i]),
            "Win rate do setor": int(_sector_arr[i]),
            _labels_arr[i]:      int(_combo_arr[i]),
            "Tamanho da conta":  int(_size_arr2[i]),
        })
    breakdowns_series = pd.Series(breakdowns, index=open_deals.index)

    # ── Assemble result ──────────────────────────────────────────────────────
    scored = open_deals.copy()
    scored["score"]     = score
    scored["tier"]      = tier
    scored["breakdown"] = breakdowns_series

    return scored.sort_values("score", ascending=False).reset_index(drop=True)
