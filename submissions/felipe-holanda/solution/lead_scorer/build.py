"""Gera app/data.js com o pipeline pontuado — é o que a interface lê.

    python -m lead_scorer.build                    # usa o último dia do CRM como "hoje"
    python -m lead_scorer.build --as-of 2017-09-18 # "volta no tempo" para qualquer segunda-feira

Saída em JS (window.LEAD_SCORER = {...}) em vez de JSON para a página abrir
com duplo clique, sem servidor (navegadores bloqueiam fetch() em file://).
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import BACKTEST_DATES, rankings, run_backtest, scored_with_outcomes, summarize, top_per_agent
from .data import DEFAULT_DATA_DIR, load, reference_date
from .scoring import (HORIZON_DAYS, LANE_FOCUS, LANE_REVIEW, TIMING_POINTS, VALUE_POINTS, agent_summary,
                      score_pipeline)

SCORER = "Lead Scorer (valor + momento)"

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "app" / "data.js"


def _clean(v):
    """Converte valores do pandas/numpy para tipos JSON (NaN/NaT -> null)."""
    if v is None or pd.isna(v):
        return None
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return float(v)
    if isinstance(v, pd.Timestamp):
        return v.date().isoformat()
    return v


def build_payload(deals, teams, as_of, with_backtest=True):
    as_of = pd.Timestamp(as_of)
    scored, curves = score_pipeline(deals, as_of)

    deal_rows = [{
        "id": d.opportunity_id,
        "agent": d.sales_agent,
        "manager": d.manager,
        "region": d.regional_office,
        "product": d.product,
        "price": _clean(d.sales_price),
        "account": _clean(d.account),
        "sector": _clean(d.sector),
        "stage": d.stage,
        "engage": _clean(d.engage_date),
        "age": _clean(d.age_days),
        "score": int(d.score),
        "valuePts": round(float(d.value_pts), 1),
        "timingPts": round(float(d.timing_pts), 1),
        "lane": d.lane,
        "phase": d.phase,
        "action": d.action,
        "ripeness": round(float(d.ripeness), 4),
        "pWin": _clean(round(float(d.p_win), 4)),
        "deadline": d.deadline,
        "expected30d": round(float(d.expected_30d), 2),
        "reasons": list(d.reasons),
    } for d in scored.itertuples(index=False)]

    summary = agent_summary(scored)
    # vendedores sem nenhum deal também aparecem (são 5 no dataset)
    summary = teams.merge(summary, on=["sales_agent", "manager", "regional_office"], how="left").fillna(0)
    agents = [{
        "agent": r.sales_agent, "manager": r.manager, "region": r.regional_office,
        "focusDeals": int(r.focus_deals), "closingWindow": int(r.closing_window),
        "expected30d": round(float(r.expected_30d), 2), "reviewDeals": int(r.review_deals),
        "reviewValue": float(r.review_value), "prospects": int(r.prospects),
        "missingAccount": int(r.missing_account),
    } for r in summary.itertuples(index=False)]

    payload = {
        "meta": {
            "asOf": pd.Timestamp(as_of).date().isoformat(),
            "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "maxCycle": curves.max_cycle,
            "peakAge": curves.peak_age,
            "peakRipeness": round(curves.peak_ripeness, 4),
            "baseWinRate": round(curves.base_win_rate, 4),
            "horizonDays": HORIZON_DAYS,
            "valuePoints": VALUE_POINTS,
            "timingPoints": TIMING_POINTS,
        },
        "curves": {
            "ripeness": [round(float(x), 4) for x in curves.ripeness],
            "pWin": [round(float(x), 4) for x in curves.p_win],
            "sample": [int(x) for x in curves.sample],
        },
        "deals": deal_rows,
        "agents": agents,
    }
    payload["health"] = pipeline_health(deals, as_of)
    if with_backtest:
        # só datas cujo mês seguinte já aconteceu até `as_of` (sem olhar o futuro)
        dates = [d for d in BACKTEST_DATES if d + pd.Timedelta(days=HORIZON_DAYS) <= as_of]
        if dates:
            res = run_backtest(deals, dates)
            payload["backtest"] = {
                "summary": [{"ranking": k, "revenueCaptured": round(v.revenue_captured, 4),
                             "hitRate": round(v.hit_rate, 4)} for k, v in summarize(res).iterrows()],
                "snapshots": int(res["as_of"].nunique()),
            }
            payload["timeTravel"] = time_travel(deals, dates, res)
    return payload


def time_travel(deals, dates, results):
    """Para a aba "Funcionou?": o top 10 de cada vendedor em cada data passada + o que aconteceu."""
    snapshots = []
    for as_of in dates:
        scored = scored_with_outcomes(deals, as_of)
        top = top_per_agent(scored, rankings(scored)[SCORER])
        day = as_of.date().isoformat()
        compare = results[results["as_of"] == day].set_index("ranking")
        snapshots.append({
            "asOf": day,
            "compare": {k: {"captured": round(float(r.revenue_captured), 4), "hitRate": round(float(r.hit_rate), 4),
                            "revenue": round(float(r.revenue_top))} for k, r in compare.iterrows()},
            "revenueTotal": round(float(scored["revenue_30d"].sum())),
            # linhas compactas: [id, vendedor, produto, conta, preço, idade, score, fase, desfecho, dias até fechar, valor fechado]
            "rows": [[d.opportunity_id, d.sales_agent, d.product, _clean(d.account), _clean(d.sales_price),
                      _clean(d.age_days), int(d.score), d.phase, d.outcome, _clean(d.days_to_close),
                      _clean(d.close_value)] for d in top.itertuples(index=False)],
        })
    return snapshots


def pipeline_health(deals, as_of):
    """Fotografia do pipeline no fim de cada mês: vivo vs sem precedente, pipeline novo e forecast."""
    as_of = pd.Timestamp(as_of)
    first = deals["close_date"].min()  # antes do primeiro fechamento não há curva para calibrar
    ends = [d for d in pd.date_range(first, as_of, freq="ME")] + [as_of]
    months = []
    for end in sorted(set(ends)):
        scored, curves = score_pipeline(deals, end)
        live = scored[scored["lane"] == LANE_FOCUS]
        review = scored[scored["lane"] == LANE_REVIEW]
        engaging = scored[scored["stage"] == "Engaging"]
        month = end.to_period("M")
        months.append({
            "date": end.date().isoformat(),
            "live": int(len(live)),
            "review": int(len(review)),
            "newEngaged": int((deals["engage_date"].dt.to_period("M") == month).sum()),
            "wonInMonth": round(float(deals.loc[(deals["deal_stage"] == "Won")
                                                & (deals["close_date"].dt.to_period("M") == month), "close_value"].sum())),
            "expected30d": round(float(live["expected_30d"].sum())),
            "naiveForecast": round(float(engaging["sales_price"].sum() * curves.base_win_rate)),
            "ageAwareForecast": round(float((live["sales_price"] * live["p_win"]).sum())),
        })
    return months


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    ap.add_argument("--as-of", help="data de referência (AAAA-MM-DD). Padrão: último evento do CRM")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--skip-backtest", action="store_true")
    args = ap.parse_args(argv)

    deals, teams = load(args.data_dir)
    as_of = pd.Timestamp(args.as_of) if args.as_of else reference_date(deals)
    payload = build_payload(deals, teams, as_of, with_backtest=not args.skip_backtest)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("window.LEAD_SCORER = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    lanes = pd.Series([d["lane"] for d in payload["deals"]]).value_counts().to_dict()
    print(f"OK: {len(payload['deals'])} deals abertos em {payload['meta']['asOf']} -> {out}")
    print(f"   filas: {lanes}")


if __name__ == "__main__":
    main()
