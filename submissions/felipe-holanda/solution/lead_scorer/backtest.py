"""Backtest do scorer de produção em segundas-feiras passadas.

Para cada data S: roda score_pipeline(deals, S) — que só enxerga o que se sabia
em S — e mede quanto da receita ganha nos 30 dias seguintes estava no top 10
de cada vendedor. Compara com ordenar só por valor e com ordem aleatória.

    python -m lead_scorer.backtest
"""
import numpy as np
import pandas as pd

from .data import load
from .scoring import HORIZON_DAYS, LANE_FOCUS, LANE_PROSPECT, score_pipeline

TOP_N = 10
BACKTEST_DATES = pd.date_range("2017-04-03", "2017-11-27", freq="4W-MON")

WON_30D, WON_LATER, LOST, STILL_OPEN = "won30", "won_later", "lost", "open"


def scored_with_outcomes(deals, as_of):
    """Pipeline engajado em `as_of`, pontuado só com o passado, + o que aconteceu depois."""
    scored, _ = score_pipeline(deals, as_of)
    scored = scored[scored["lane"] != LANE_PROSPECT].copy()
    horizon = as_of + pd.Timedelta(days=HORIZON_DAYS)
    won = scored["deal_stage"] == "Won"
    won_soon = won & (scored["close_date"] <= horizon)
    scored["revenue_30d"] = np.where(won_soon, scored["close_value"], 0.0)
    scored["outcome"] = np.select(
        [won_soon, won, scored["deal_stage"] == "Lost"], [WON_30D, WON_LATER, LOST], STILL_OPEN)
    scored["days_to_close"] = (scored["close_date"] - as_of).dt.days
    return scored


def rankings(scored):
    # Como na ferramenta: a fila "Foco" vem antes da fila "Revisar ou encerrar"
    in_focus = (scored["lane"] == LANE_FOCUS).astype(int)
    return {
        "Lead Scorer (valor + momento)": in_focus * 1000 + scored["score"] + scored["sales_price"] / 1e6,
        "Só valor de lista": scored["sales_price"].astype(float),
        "Aleatório": pd.Series(np.random.default_rng(0).random(len(scored)), index=scored.index),
    }


def top_per_agent(scored, key, top_n=TOP_N):
    return scored.assign(_k=key).sort_values("_k", ascending=False).groupby("sales_agent").head(top_n)


def run_backtest(deals, dates=BACKTEST_DATES, top_n=TOP_N):
    rows = []
    for as_of in dates:
        scored = scored_with_outcomes(deals, as_of)
        total = scored["revenue_30d"].sum()
        if total == 0:
            continue
        for name, key in rankings(scored).items():
            top = top_per_agent(scored, key, top_n)
            rows.append({
                "as_of": as_of.date().isoformat(),
                "ranking": name,
                "revenue_captured": top["revenue_30d"].sum() / total,
                "hit_rate": float((top["revenue_30d"] > 0).mean()),
                "revenue_top": float(top["revenue_30d"].sum()),
                "revenue_total": float(total),
            })
    return pd.DataFrame(rows)


def summarize(results):
    return (results.groupby("ranking")[["revenue_captured", "hit_rate"]].mean()
            .sort_values("revenue_captured", ascending=False))


if __name__ == "__main__":
    deals, _ = load()
    res = run_backtest(deals)
    pd.set_option("display.width", 200)
    print(f"Top {TOP_N} por vendedor — média em {res['as_of'].nunique()} segundas-feiras simuladas\n")
    print(summarize(res).round(3).to_string())
    print("\nReceita capturada por data:")
    print(res.pivot(index="ranking", columns="as_of", values="revenue_captured").round(2).to_string())
