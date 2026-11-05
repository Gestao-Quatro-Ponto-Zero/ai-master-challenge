"""Facts that help a rep prepare for a deal. They are shown as context and never affect the score.

Everything uses only deals closed before as_of.
"""
from __future__ import annotations

import pandas as pd


def _closed_before(deals: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    return deals[deals["close_date"] < as_of]


def product_stats(deals: pd.DataFrame, as_of: pd.Timestamp) -> dict:
    """What each product usually brings in when it is won."""
    closed = _closed_before(deals, as_of)
    stats = {}
    for product, group in closed.groupby("product"):
        won = group[group["deal_stage"] == "Won"]["close_value"]
        stats[product] = {
            "median": round(float(won.median())),
            "low": round(float(won.quantile(0.25))),
            "high": round(float(won.quantile(0.75))),
            "wins": int(len(won)),
            "closed": int(len(group)),
        }
    return stats


def account_profiles(deals: pd.DataFrame, as_of: pd.Timestamp) -> dict:
    """Company facts and the relationship so far, by account name."""
    closed = _closed_before(deals, as_of)
    won = closed[closed["deal_stage"] == "Won"]
    known = deals[deals["account"].notna()]
    company = known.drop_duplicates("account").set_index("account")
    group_of = company["subsidiary_of"].fillna(pd.Series(company.index, index=company.index))
    group_revenue = won.assign(group=won["account"].map(group_of)).groupby("group")["close_value"].sum()

    profiles = {}
    for name, facts in company.iterrows():
        account_closed = closed[closed["account"] == name]
        account_won = won[won["account"] == name]
        products = {}
        for product, purchases in account_won.groupby("product"):
            products[product] = {"wins": int(len(purchases)), "last": purchases["close_date"].max().strftime("%Y-%m-%d")}
        parent = facts["subsidiary_of"]
        profiles[name] = {
            "sector": facts["sector"],
            "revenue": float(facts["revenue"]),
            "employees": int(facts["employees"]),
            "location": facts["office_location"],
            "founded": int(facts["year_established"]),
            "parent": None if pd.isna(parent) else parent,
            "groupRevenue": None if pd.isna(parent) else round(float(group_revenue.get(group_of[name], 0))),
            "wins": int(len(account_won)),
            "closed": int(len(account_closed)),
            "wonRevenue": round(float(account_won["close_value"].sum())),
            "lastWin": None if account_won.empty else account_won["close_date"].max().strftime("%Y-%m-%d"),
            "products": products,
        }
    return profiles


def rep_track_record(deals: pd.DataFrame, as_of: pd.Timestamp) -> dict:
    """Each rep's closed deals by product and by account."""
    closed = _closed_before(deals, as_of).assign(is_won=lambda d: (d["deal_stage"] == "Won").astype(int))

    def table(column: str) -> dict:
        grouped = closed.groupby(["sales_agent", column])["is_won"].agg(["sum", "size"])
        return {key: (int(row["sum"]), int(row["size"])) for key, row in grouped.iterrows()}

    return {"product": table("product"), "account": table("account")}


def add_rep_record(row: dict, record: dict) -> dict:
    """Attach the rep's record with this deal's product and account to an app row."""
    product_wins, product_closed = record["product"].get((row["agent"], row["product"]), (0, 0))
    account_wins, account_closed = record["account"].get((row["agent"], row["account"]), (0, 0))
    row.update(repProductWins=product_wins, repProductClosed=product_closed, repAccountWins=account_wins, repAccountClosed=account_closed)
    return row
