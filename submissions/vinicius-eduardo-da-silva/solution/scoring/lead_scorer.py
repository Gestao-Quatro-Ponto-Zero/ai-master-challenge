"""Core scoring logic shared by the app build and the backtest.

Everything here takes an ``as_of`` date and only uses what was known on that
date, so the same code can score today's pipeline and replay past Mondays.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# The data ends on Sunday 2017-12-31, so the rep opens the tool the next morning.
AS_OF = pd.Timestamp("2018-01-01")
HORIZON_DAYS = 30
TOP_K = 10
# Below this chance the timing signal is indistinguishable from zero. Without a
# floor, log-scale points would be dominated by tiny differences in the tail.
PROBABILITY_FLOOR = 0.01
PROBABILITY_CEILING = 0.45
AGE_BIN_DAYS = 15
SMOOTHING = 10
# Nothing closes before this date in the data, although deals were engaged since
# 2016-10. Fast outcomes from that period are missing, so it cannot teach rates.
FIRST_RELIABLE_DATE = pd.Timestamp("2017-03-01")

PRODUCT_FIXES = {"GTXPro": "GTX Pro"}
SECTOR_FIXES = {"technolgy": "technology"}
LOCATION_FIXES = {"Philipines": "Philippines"}


def load_deals(data_dir: str | Path) -> pd.DataFrame:
    """Read the four CRM tables, fix known data errors, and join them."""
    data_dir = Path(data_dir)
    accounts = pd.read_csv(data_dir / "accounts.csv")
    products = pd.read_csv(data_dir / "products.csv")
    teams = pd.read_csv(data_dir / "sales_teams.csv")
    pipeline = pd.read_csv(data_dir / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])

    pipeline["product"] = pipeline["product"].replace(PRODUCT_FIXES)
    accounts["sector"] = accounts["sector"].replace(SECTOR_FIXES)
    accounts["office_location"] = accounts["office_location"].replace(LOCATION_FIXES)

    deals = (
        pipeline.merge(products, on="product", how="left", validate="m:1")
        .merge(teams, on="sales_agent", how="left", validate="m:1")
        .merge(accounts, on="account", how="left", validate="m:1")
    )
    if deals["sales_price"].isna().any():
        raise ValueError("Deals with a product missing from the catalog")
    if deals["manager"].isna().any():
        raise ValueError("Deals with an agent missing from the sales team")
    return deals


def quarter_position(dates: pd.Series | pd.DatetimeIndex) -> np.ndarray:
    """Month position inside the quarter: 1, 2 or 3."""
    months = pd.DatetimeIndex(dates).month
    return np.asarray((months - 1) % 3 + 1)


def age_bin(ages: pd.Series | np.ndarray) -> np.ndarray:
    return np.asarray(ages) // AGE_BIN_DAYS * AGE_BIN_DAYS


def known_max_cycle(deals: pd.DataFrame, as_of: pd.Timestamp) -> int:
    """Longest engage-to-close time among deals already closed by as_of."""
    closed = deals[deals["close_date"] < as_of]
    return int((closed["close_date"] - closed["engage_date"]).dt.days.max())


def open_deals_at(deals: pd.DataFrame, moment: pd.Timestamp) -> pd.DataFrame:
    """Engaged deals still open at ``moment``, with their age in days."""
    engaged = deals[deals["engage_date"] < moment]
    still_open = engaged["close_date"].isna() | (engaged["close_date"] >= moment)
    result = engaged[still_open].copy()
    result["age"] = (moment - result["engage_date"]).dt.days
    return result


def learning_observations(deals: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """One row per open deal per past Monday, labeled by a win in the next 30 days.

    A Monday is only used when its whole 30-day outcome window ended by as_of,
    which is what keeps future information out of the rates.
    """
    last_moment = as_of - pd.Timedelta(days=HORIZON_DAYS)
    mondays = pd.date_range(FIRST_RELIABLE_DATE, last_moment, freq="W-MON")
    frames = []
    for monday in mondays:
        snapshot = open_deals_at(deals, monday)
        window_end = monday + pd.Timedelta(days=HORIZON_DAYS)
        won_in_window = (
            (snapshot["deal_stage"] == "Won")
            & (snapshot["close_date"] >= monday)
            & (snapshot["close_date"] < window_end)
        )
        frames.append(
            pd.DataFrame(
                {
                    "age": snapshot["age"].to_numpy(),
                    "position": quarter_position(pd.DatetimeIndex([monday]))[0],
                    "won": won_in_window.to_numpy().astype(int),
                }
            )
        )
    if not frames:
        return pd.DataFrame(columns=["age", "position", "won"])
    return pd.concat(frames, ignore_index=True)


@dataclass
class TimingRates:
    """P(deal is won within 30 days | age, month of the quarter)."""

    overall: float
    by_age: dict[int, float]
    by_age_position: dict[tuple[int, int], float]
    max_cycle: int
    use_quarter: bool

    def probability(self, age: int, position: int) -> float:
        if age > self.max_cycle:
            return 0.0
        bin_start = int(age // AGE_BIN_DAYS * AGE_BIN_DAYS)
        age_rate = self.by_age.get(bin_start, self.overall)
        if not self.use_quarter:
            return age_rate
        return self.by_age_position.get((bin_start, position), age_rate)


def learn_rates(deals: pd.DataFrame, as_of: pd.Timestamp, use_quarter: bool = False) -> TimingRates:
    """Learn timing rates using only data observable at as_of."""
    max_cycle = known_max_cycle(deals, as_of)
    obs = learning_observations(deals, as_of)
    obs = obs[obs["age"] <= max_cycle].copy()
    overall = float(obs["won"].mean())
    obs["bin"] = age_bin(obs["age"])

    by_age = {}
    for bin_start, group in obs.groupby("bin"):
        by_age[int(bin_start)] = (group["won"].sum() + SMOOTHING * overall) / (len(group) + SMOOTHING)

    by_age_position = {}
    for (bin_start, position), group in obs.groupby(["bin", "position"]):
        prior = by_age[int(bin_start)]
        by_age_position[(int(bin_start), int(position))] = (group["won"].sum() + SMOOTHING * prior) / (len(group) + SMOOTHING)

    return TimingRates(overall, by_age, by_age_position, max_cycle, use_quarter)


def ranking_value(probability: np.ndarray | pd.Series, price: np.ndarray | pd.Series) -> np.ndarray:
    """Expected revenue on the same bounded scale as the score. Stale deals rank last."""
    probability = np.asarray(probability, dtype=float)
    bounded = np.clip(probability, PROBABILITY_FLOOR, PROBABILITY_CEILING)
    return np.where(probability > 0, bounded * np.asarray(price, dtype=float), 0.0)


def score_points(probability: float, price: float, price_min: float, price_max: float) -> tuple[float, float]:
    """Split the score into value and timing points.

    Both parts use the same points per log unit, so they add up to a rescaled
    log(probability x price). Ranking by score is ranking by expected revenue.
    """
    span = np.log(price_max / price_min) + np.log(PROBABILITY_CEILING / PROBABILITY_FLOOR)
    points_per_log = 100 / span
    bounded = min(max(probability, PROBABILITY_FLOOR), PROBABILITY_CEILING)
    value_points = points_per_log * np.log(price / price_min)
    timing_points = points_per_log * np.log(bounded / PROBABILITY_FLOOR)
    return float(value_points), float(timing_points)


def age_zone(age: int, max_cycle: int) -> str:
    if age > max_cycle:
        return "parado"
    if age <= 14:
        return "novo"
    if age < 45:
        return "intermediario"
    if age < 120:
        return "janela"
    return "prazo_final"


def suggested_action(age: int, max_cycle: int) -> str:
    zone = age_zone(age, max_cycle)
    if zone == "novo":
        return "Fale com o cliente esta semana: 42% dos deals encerrados se definiram em até 14 dias."
    if zone == "intermediario":
        return "Confirme o próximo passo com data: nessa idade, poucos deals se definem por conta própria."
    if zone == "janela":
        return "Peça a decisão: é a faixa de idade em que os deals mais fecham."
    if zone == "prazo_final":
        days_left = max_cycle - age
        remaining = {0: "este é o último dia", 1: "falta 1 dia"}.get(days_left, f"faltam {days_left} dias")
        return f"Último empurrão: nenhum deal fechou depois de {max_cycle} dias, e {remaining}."
    return f"Confirme se ainda existe ou encerre: nenhum deal fechou depois de {max_cycle} dias."


def account_history(deals: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """Past closed deals per account, shown as context and never used to rank."""
    closed = deals[(deals["close_date"] < as_of) & deals["account"].notna()]
    history = closed.groupby("account")["deal_stage"].agg(
        past_deals="size", past_wins=lambda stage: int((stage == "Won").sum())
    )
    return history.reset_index()


def score_pipeline(deals: pd.DataFrame, as_of: pd.Timestamp = AS_OF, use_quarter: bool = True) -> tuple[pd.DataFrame, TimingRates]:
    """Score every Engaging deal open at as_of and assign it to a queue."""
    rates = learn_rates(deals, as_of, use_quarter=use_quarter)
    position = int(quarter_position(pd.DatetimeIndex([as_of]))[0])
    price_min, price_max = float(deals["sales_price"].min()), float(deals["sales_price"].max())

    scored = open_deals_at(deals, as_of).merge(account_history(deals, as_of), on="account", how="left")
    scored["probability"] = [rates.probability(age, position) for age in scored["age"]]
    points = [score_points(p, price, price_min, price_max) for p, price in zip(scored["probability"], scored["sales_price"])]
    scored["value_points"] = [item[0] for item in points]
    scored["timing_points"] = [item[1] for item in points]
    scored["score"] = (scored["value_points"] + scored["timing_points"]).round().astype(int)
    scored["expected_revenue"] = scored["probability"] * scored["sales_price"]
    scored["zone"] = [age_zone(age, rates.max_cycle) for age in scored["age"]]
    scored["queue"] = np.where(scored["age"] > rates.max_cycle, "decidir", "foco")
    scored["action"] = [suggested_action(age, rates.max_cycle) for age in scored["age"]]
    scored["_rank"] = ranking_value(scored["probability"], scored["sales_price"])
    ordered = scored.sort_values(["_rank", "sales_price"], ascending=False).drop(columns="_rank")
    return ordered.reset_index(drop=True), rates
