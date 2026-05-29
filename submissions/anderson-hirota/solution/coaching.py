# coaching.py — Per-rep alpha/leverage signals from historical CRM data.
#
# 100% data — no LLM. The signals are arithmetic over Won/Lost deals.
# Surface in Rep mode: "Where you have leverage, where you bleed."

from __future__ import annotations

from typing import Optional

import pandas as pd

MIN_SAMPLE = 5  # don't draw conclusions from <5 closed deals in any slice


def _slice_winrate(closed: pd.DataFrame, key: str | None = None) -> pd.DataFrame:
    """Win rate per slice of `key` (or overall if None). Returns df with
    columns: <key>, n_won, n_lost, n_total, win_rate."""
    if key is None:
        grp = closed.groupby(closed.index >= 0)  # all in one group
    else:
        grp = closed.groupby(key)
    out = grp.agg(
        n_won=("deal_stage", lambda s: (s == "Won").sum()),
        n_lost=("deal_stage", lambda s: (s == "Lost").sum()),
    ).reset_index() if key is not None else pd.DataFrame({
        "n_won": [(closed["deal_stage"] == "Won").sum()],
        "n_lost": [(closed["deal_stage"] == "Lost").sum()],
    })
    out["n_total"] = out["n_won"] + out["n_lost"]
    out["win_rate"] = out["n_won"] / out["n_total"].replace(0, pd.NA)
    return out


def _team_winrate_by(closed: pd.DataFrame, key: str) -> dict:
    df = _slice_winrate(closed, key)
    return dict(zip(df[key], df["win_rate"]))


def _days_to_close(df: pd.DataFrame) -> pd.Series:
    return (df["close_date"] - df["engage_date"]).dt.days


def rep_alpha_signals(
    rep: str,
    scored: pd.DataFrame,
    min_sample: int = MIN_SAMPLE,
) -> dict:
    """Compute leverage signals for one rep.

    Returns:
      {
        "rep": str,
        "overall": {"rep_wr": float, "team_wr": float, "n": int, "delta_pp": float},
        "sector_alpha": [list of dicts where rep > team meaningfully],
        "sector_bleed":  [list of dicts where rep < team meaningfully],
        "product_alpha": [...],
        "product_bleed": [...],
        "temporal": {"fast": {n,wr}, "medium": {n,wr}, "slow": {n,wr}, "verdict": str},
        "closing_speed": {"rep_median_days": int, "team_median_days": int, "delta": int},
      }
    Empty dicts/lists when sample too small.
    """
    closed_all = scored[scored["deal_stage"].isin(["Won", "Lost"])].copy()
    rep_closed = closed_all[closed_all["sales_agent"] == rep].copy()

    out = {
        "rep": rep,
        "overall": {},
        "sector_alpha": [],
        "sector_bleed": [],
        "product_alpha": [],
        "product_bleed": [],
        "temporal": {},
        "closing_speed": {},
    }

    if len(rep_closed) < min_sample:
        return out

    # ---- Overall
    rep_wr = float((rep_closed["deal_stage"] == "Won").mean())
    team_wr = float((closed_all["deal_stage"] == "Won").mean())
    out["overall"] = {
        "rep_wr": rep_wr,
        "team_wr": team_wr,
        "n": int(len(rep_closed)),
        "delta_pp": (rep_wr - team_wr) * 100,
    }

    # ---- Sector alpha / bleed
    team_sector_wr = _team_winrate_by(closed_all, "sector")
    rep_by_sector = _slice_winrate(rep_closed, "sector")
    rep_by_sector = rep_by_sector[rep_by_sector["n_total"] >= min_sample].copy()
    if len(rep_by_sector):
        rep_by_sector["team_wr"] = rep_by_sector["sector"].map(team_sector_wr)
        rep_by_sector["delta_pp"] = (rep_by_sector["win_rate"] - rep_by_sector["team_wr"]) * 100
        rep_by_sector = rep_by_sector.dropna(subset=["delta_pp", "sector"])
        rep_by_sector = rep_by_sector[rep_by_sector["sector"].notna()]
        # alpha = ≥+10pp; bleed = ≤-10pp
        alpha = rep_by_sector[rep_by_sector["delta_pp"] >= 10].nlargest(2, "delta_pp")
        bleed = rep_by_sector[rep_by_sector["delta_pp"] <= -10].nsmallest(2, "delta_pp")
        out["sector_alpha"] = alpha.assign(
            label=alpha["sector"]).rename(columns={"win_rate": "rep_wr"})[
            ["label", "rep_wr", "team_wr", "delta_pp", "n_total"]
        ].to_dict("records")
        out["sector_bleed"] = bleed.assign(
            label=bleed["sector"]).rename(columns={"win_rate": "rep_wr"})[
            ["label", "rep_wr", "team_wr", "delta_pp", "n_total"]
        ].to_dict("records")

    # ---- Product alpha / bleed
    team_product_wr = _team_winrate_by(closed_all, "product")
    rep_by_product = _slice_winrate(rep_closed, "product")
    rep_by_product = rep_by_product[rep_by_product["n_total"] >= min_sample].copy()
    if len(rep_by_product):
        rep_by_product["team_wr"] = rep_by_product["product"].map(team_product_wr)
        rep_by_product["delta_pp"] = (rep_by_product["win_rate"] - rep_by_product["team_wr"]) * 100
        rep_by_product = rep_by_product.dropna(subset=["delta_pp"])
        alpha = rep_by_product[rep_by_product["delta_pp"] >= 10].nlargest(2, "delta_pp")
        bleed = rep_by_product[rep_by_product["delta_pp"] <= -10].nsmallest(2, "delta_pp")
        out["product_alpha"] = alpha.assign(
            label=alpha["product"]).rename(columns={"win_rate": "rep_wr"})[
            ["label", "rep_wr", "team_wr", "delta_pp", "n_total"]
        ].to_dict("records")
        out["product_bleed"] = bleed.assign(
            label=bleed["product"]).rename(columns={"win_rate": "rep_wr"})[
            ["label", "rep_wr", "team_wr", "delta_pp", "n_total"]
        ].to_dict("records")

    # ---- Temporal: win rate by cycle length bucket
    rep_with_dates = rep_closed[rep_closed["engage_date"].notna() & rep_closed["close_date"].notna()].copy()
    if len(rep_with_dates) >= min_sample * 3:
        rep_with_dates["cycle"] = _days_to_close(rep_with_dates)
        buckets = {
            "fast (<30d)": rep_with_dates[rep_with_dates["cycle"] < 30],
            "medium (30-90d)": rep_with_dates[(rep_with_dates["cycle"] >= 30) & (rep_with_dates["cycle"] < 90)],
            "slow (≥90d)": rep_with_dates[rep_with_dates["cycle"] >= 90],
        }
        temp = {}
        for label, df in buckets.items():
            if len(df) >= min_sample:
                temp[label] = {
                    "n": int(len(df)),
                    "wr": float((df["deal_stage"] == "Won").mean()),
                }
        out["temporal"] = temp
        # Verdict: monotonic decline = "fade quickly"; flat = "consistent"; increase = "stronger over time"
        if {"fast (<30d)", "slow (≥90d)"}.issubset(temp.keys()):
            fast_wr = temp["fast (<30d)"]["wr"]
            slow_wr = temp["slow (≥90d)"]["wr"]
            if fast_wr - slow_wr >= 0.15:
                out["temporal_verdict"] = (
                    f"You close fast deals at {fast_wr*100:.0f}% but drop to {slow_wr*100:.0f}% on slow ones. "
                    "Push for decisions early — your win rate fades with time."
                )
            elif slow_wr - fast_wr >= 0.15:
                out["temporal_verdict"] = (
                    f"You close slow deals at {slow_wr*100:.0f}% vs {fast_wr*100:.0f}% on fast ones. "
                    "You're a patient closer — don't force premature commits."
                )

    # ---- Closing speed (median days to close on Won)
    rep_won = rep_closed[(rep_closed["deal_stage"] == "Won")
                        & rep_closed["engage_date"].notna()
                        & rep_closed["close_date"].notna()].copy()
    team_won = closed_all[(closed_all["deal_stage"] == "Won")
                         & closed_all["engage_date"].notna()
                         & closed_all["close_date"].notna()].copy()
    if len(rep_won) >= min_sample and len(team_won) >= min_sample:
        rep_med = int(_days_to_close(rep_won).median())
        team_med = int(_days_to_close(team_won).median())
        out["closing_speed"] = {
            "rep_median_days": rep_med,
            "team_median_days": team_med,
            "delta": rep_med - team_med,
        }

    return out


def benchmark_for_rep(rep: str, scored: pd.DataFrame, min_sample: int = 10) -> dict:
    """Benchmark this rep against top performers across the org.
    Returns rep's close rate + median cycle days vs top-quartile / top-decile.
    """
    closed_all = scored[scored["deal_stage"].isin(["Won", "Lost"])].copy()
    rep_closed = closed_all[closed_all["sales_agent"] == rep].copy()

    out = {"rep": rep, "has_data": False}
    if len(rep_closed) < min_sample:
        out["reason"] = f"only {len(rep_closed)} closed deals (need {min_sample}+)"
        return out

    # Rep close rate
    rep_wr = float((rep_closed["deal_stage"] == "Won").mean())

    # Top quartile close rate across all reps with enough sample
    all_reps = closed_all["sales_agent"].dropna().unique()
    rep_wrs = []
    for r in all_reps:
        r_closed = closed_all[closed_all["sales_agent"] == r]
        if len(r_closed) >= min_sample:
            rep_wrs.append((r_closed["deal_stage"] == "Won").mean())
    if not rep_wrs:
        out["reason"] = "no peers with enough closed deals"
        return out
    rep_wrs_sorted = sorted(rep_wrs)
    top_quartile_wr = rep_wrs_sorted[max(0, int(len(rep_wrs_sorted) * 0.75))]

    # Rep median cycle (Won deals only)
    rep_won = rep_closed[(rep_closed["deal_stage"] == "Won")
                        & rep_closed["engage_date"].notna()
                        & rep_closed["close_date"].notna()]
    rep_cycle = int(_days_to_close(rep_won).median()) if len(rep_won) >= min_sample // 2 else None

    # Top decile cycle (fastest 10%) across all reps
    rep_cycles = []
    for r in all_reps:
        r_won = closed_all[(closed_all["sales_agent"] == r)
                          & (closed_all["deal_stage"] == "Won")
                          & closed_all["engage_date"].notna()
                          & closed_all["close_date"].notna()]
        if len(r_won) >= min_sample // 2:
            rep_cycles.append(int(_days_to_close(r_won).median()))
    top_decile_cycle = None
    if rep_cycles:
        rep_cycles_sorted = sorted(rep_cycles)
        top_decile_cycle = rep_cycles_sorted[max(0, int(len(rep_cycles_sorted) * 0.10))]

    out["has_data"] = True
    out["close_rate"] = {
        "you": rep_wr,
        "top_quartile": top_quartile_wr,
        "delta_pp": (rep_wr - top_quartile_wr) * 100,
        "you_are_top": rep_wr >= top_quartile_wr,
    }
    if rep_cycle is not None and top_decile_cycle is not None:
        out["cycle"] = {
            "you_days": rep_cycle,
            "top_decile_days": top_decile_cycle,
            "delta_days": rep_cycle - top_decile_cycle,
            "you_are_top": rep_cycle <= top_decile_cycle,
        }

    # Leaderboard: all reps with enough sample, sorted desc by close rate
    rep_pairs = []
    for r in all_reps:
        r_closed = closed_all[closed_all["sales_agent"] == r]
        if len(r_closed) >= min_sample:
            rep_pairs.append((r, (r_closed["deal_stage"] == "Won").mean()))
    rep_pairs.sort(key=lambda x: x[1], reverse=True)
    you_idx = next((i for i, (r, _) in enumerate(rep_pairs) if r == rep), None)
    out["leaderboard"] = {
        "top5": [{"name": r, "close_rate": wr} for r, wr in rep_pairs[:5]],
        "you_in_top5": you_idx is not None and you_idx < 5,
        "ahead": you_idx if you_idx is not None else None,
        "behind": (len(rep_pairs) - you_idx - 1) if you_idx is not None else None,
        "total_ranked": len(rep_pairs),
    }
    return out


def benchmark_for_team(manager: str, scored: pd.DataFrame, min_sample: int = 20) -> dict:
    """Benchmark this team (manager's reps) against top-3 teams."""
    closed_all = scored[scored["deal_stage"].isin(["Won", "Lost"])].copy()
    team_closed = closed_all[closed_all["manager"] == manager].copy()

    out = {"manager": manager, "has_data": False}
    if len(team_closed) < min_sample:
        out["reason"] = f"only {len(team_closed)} closed deals (need {min_sample}+)"
        return out

    team_wr = float((team_closed["deal_stage"] == "Won").mean())

    # Per-team close rates
    all_managers = closed_all["manager"].dropna().unique()
    team_wrs = []
    for m in all_managers:
        m_closed = closed_all[closed_all["manager"] == m]
        if len(m_closed) >= min_sample:
            team_wrs.append((m, (m_closed["deal_stage"] == "Won").mean()))
    if len(team_wrs) < 2:
        out["reason"] = "not enough peer teams to benchmark"
        return out
    team_wrs_sorted = sorted(team_wrs, key=lambda x: x[1], reverse=True)
    top3 = team_wrs_sorted[:3]
    top3_avg = sum(wr for _, wr in top3) / len(top3)

    # Team median cycle
    team_won = team_closed[(team_closed["deal_stage"] == "Won")
                          & team_closed["engage_date"].notna()
                          & team_closed["close_date"].notna()]
    team_cycle = int(_days_to_close(team_won).median()) if len(team_won) >= min_sample // 2 else None

    # Top-3 teams cycle
    team_cycles = []
    for m in all_managers:
        m_won = closed_all[(closed_all["manager"] == m)
                          & (closed_all["deal_stage"] == "Won")
                          & closed_all["engage_date"].notna()
                          & closed_all["close_date"].notna()]
        if len(m_won) >= min_sample // 2:
            team_cycles.append((m, int(_days_to_close(m_won).median())))
    top3_cycle_avg = None
    if len(team_cycles) >= 2:
        team_cycles_sorted = sorted(team_cycles, key=lambda x: x[1])  # faster first
        top3_cycles = team_cycles_sorted[:3]
        top3_cycle_avg = sum(c for _, c in top3_cycles) / len(top3_cycles)

    is_top3 = manager in {m for m, _ in top3}

    out["has_data"] = True
    out["close_rate"] = {
        "you": team_wr,
        "top3_avg": top3_avg,
        "delta_pp": (team_wr - top3_avg) * 100,
        "you_are_top": is_top3,
    }
    if team_cycle is not None and top3_cycle_avg is not None:
        out["cycle"] = {
            "you_days": team_cycle,
            "top3_avg_days": round(top3_cycle_avg, 0),
            "delta_days": team_cycle - top3_cycle_avg,
            "you_are_top": team_cycle <= top3_cycle_avg,
        }

    # Leaderboard: all teams sorted desc by close rate
    you_idx = next((i for i, (m, _) in enumerate(team_wrs_sorted) if m == manager), None)
    out["leaderboard"] = {
        "top5": [{"name": m, "close_rate": wr} for m, wr in team_wrs_sorted[:5]],
        "you_in_top5": you_idx is not None and you_idx < 5,
        "ahead": you_idx if you_idx is not None else None,
        "behind": (len(team_wrs_sorted) - you_idx - 1) if you_idx is not None else None,
        "total_ranked": len(team_wrs_sorted),
    }
    return out


def team_alpha_signals(
    manager: str,
    scored: pd.DataFrame,
    min_sample: int = MIN_SAMPLE,
) -> dict:
    """Team-level leverage signals — aggregates over the manager's reps.
    Mirrors `rep_alpha_signals` but unit of analysis is the team vs company.
    """
    closed_all = scored[scored["deal_stage"].isin(["Won", "Lost"])].copy()
    team_closed = closed_all[closed_all["manager"] == manager].copy()

    out = {
        "manager": manager,
        "overall": {},
        "sector_alpha": [],
        "sector_bleed": [],
        "product_alpha": [],
        "product_bleed": [],
        "rep_load_imbalance": None,
    }
    if len(team_closed) < min_sample:
        return out

    team_wr = float((team_closed["deal_stage"] == "Won").mean())
    company_wr = float((closed_all["deal_stage"] == "Won").mean())
    out["overall"] = {
        "team_wr": team_wr,
        "company_wr": company_wr,
        "n": int(len(team_closed)),
        "delta_pp": (team_wr - company_wr) * 100,
        "n_reps": int(scored[scored["manager"] == manager]["sales_agent"].nunique()),
    }

    # ---- Sector alpha / bleed (team vs company)
    company_sector_wr = _team_winrate_by(closed_all, "sector")
    team_by_sector = _slice_winrate(team_closed, "sector")
    team_by_sector = team_by_sector[team_by_sector["n_total"] >= min_sample * 2].copy()
    if len(team_by_sector):
        team_by_sector["company_wr"] = team_by_sector["sector"].map(company_sector_wr)
        team_by_sector["delta_pp"] = (team_by_sector["win_rate"] - team_by_sector["company_wr"]) * 100
        team_by_sector = team_by_sector.dropna(subset=["delta_pp", "sector"])
        team_by_sector = team_by_sector[team_by_sector["sector"].notna()]
        alpha = team_by_sector[team_by_sector["delta_pp"] >= 5].nlargest(3, "delta_pp")
        bleed = team_by_sector[team_by_sector["delta_pp"] <= -5].nsmallest(3, "delta_pp")
        out["sector_alpha"] = alpha.assign(label=alpha["sector"]).rename(
            columns={"win_rate": "team_wr"})[
            ["label", "team_wr", "company_wr", "delta_pp", "n_total"]
        ].to_dict("records")
        out["sector_bleed"] = bleed.assign(label=bleed["sector"]).rename(
            columns={"win_rate": "team_wr"})[
            ["label", "team_wr", "company_wr", "delta_pp", "n_total"]
        ].to_dict("records")

    # ---- Product alpha / bleed
    company_product_wr = _team_winrate_by(closed_all, "product")
    team_by_product = _slice_winrate(team_closed, "product")
    team_by_product = team_by_product[team_by_product["n_total"] >= min_sample * 2].copy()
    if len(team_by_product):
        team_by_product["company_wr"] = team_by_product["product"].map(company_product_wr)
        team_by_product["delta_pp"] = (team_by_product["win_rate"] - team_by_product["company_wr"]) * 100
        team_by_product = team_by_product.dropna(subset=["delta_pp"])
        alpha = team_by_product[team_by_product["delta_pp"] >= 5].nlargest(3, "delta_pp")
        bleed = team_by_product[team_by_product["delta_pp"] <= -5].nsmallest(3, "delta_pp")
        out["product_alpha"] = alpha.assign(label=alpha["product"]).rename(
            columns={"win_rate": "team_wr"})[
            ["label", "team_wr", "company_wr", "delta_pp", "n_total"]
        ].to_dict("records")
        out["product_bleed"] = bleed.assign(label=bleed["product"]).rename(
            columns={"win_rate": "team_wr"})[
            ["label", "team_wr", "company_wr", "delta_pp", "n_total"]
        ].to_dict("records")

    # ---- Rep load imbalance
    team_open = scored[(scored["manager"] == manager) & scored["deal_stage"].isin(["Prospecting", "Engaging"])]
    if len(team_open):
        rep_pipe = team_open.groupby("sales_agent")["expected_value"].sum().sort_values(ascending=False)
        if len(rep_pipe) >= 3:
            top = float(rep_pipe.iloc[0])
            bot = float(rep_pipe.iloc[-1])
            out["rep_load_imbalance"] = {
                "top_rep": rep_pipe.index[0],
                "top_pipeline_value": top,
                "bottom_rep": rep_pipe.index[-1],
                "bottom_pipeline_value": bot,
                "ratio": (top / bot) if bot > 0 else None,
            }

    return out
