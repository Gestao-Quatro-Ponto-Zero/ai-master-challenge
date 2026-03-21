"""
generate_diagnostic.py
Gera data/diagnostic_output.json a partir do Dataset 1 (customer_support_tickets.csv).
Versão de produção dos notebooks/01_diagnostic.ipynb — sem visualizações, só análise.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

def main() -> None:
    csv_path = DATA / "customer_support_tickets.csv"
    if not csv_path.exists():
        print(f"[generate_diagnostic] ERRO: {csv_path} não encontrado.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(csv_path)

    # ── Timestamps ────────────────────────────────────────────────────────────
    df["First Response Time"] = pd.to_datetime(df["First Response Time"], errors="coerce")
    df["Time to Resolution"]  = pd.to_datetime(df["Time to Resolution"],  errors="coerce")
    df["resolution_hours"] = (
        (df["Time to Resolution"] - df["First Response Time"])
        .dt.total_seconds().abs() / 3600
    )

    closed = df[df["Ticket Status"] == "Closed"].copy()

    # ── Prioridade ─────────────────────────────────────────────────────────────
    priority_order = ["Critical", "High", "Medium", "Low"]
    priority_stats = (
        df.groupby("Ticket Priority")
        .agg(
            volume=("Ticket ID", "count"),
            avg_csat=("Customer Satisfaction Rating", "mean"),
            resolution_rate=("Ticket Status", lambda x: (x == "Closed").mean() * 100),
        )
        .join(
            closed.groupby("Ticket Priority")["resolution_hours"].mean().rename("avg_resolution_h")
        )
    )

    priority_list = [
        {
            "priority": p,
            "volume": int(priority_stats.loc[p, "volume"]),
            "avg_csat": round(float(priority_stats.loc[p, "avg_csat"]), 2),
            "resolution_rate": round(float(priority_stats.loc[p, "resolution_rate"]), 1),
            "avg_resolution_h": round(float(priority_stats.loc[p, "avg_resolution_h"]), 2),
        }
        for p in priority_order
        if p in priority_stats.index
    ]

    # ── CSAT drivers ──────────────────────────────────────────────────────────
    valid = closed.dropna(subset=["resolution_hours", "Customer Satisfaction Rating"])
    r, p = stats.pearsonr(valid["resolution_hours"], valid["Customer Satisfaction Rating"])

    def kruskal_by(group_col: str):
        groups = [g["Customer Satisfaction Rating"].dropna().values
                  for _, g in df.groupby(group_col)]
        groups = [g for g in groups if len(g) > 1]
        return stats.kruskal(*groups) if len(groups) >= 2 else (float("nan"), float("nan"))

    kw_ch  = kruskal_by("Ticket Channel")
    kw_ty  = kruskal_by("Ticket Type")
    kw_pr  = kruskal_by("Ticket Priority")

    df["priority_num"] = df["Ticket Priority"].map({"Low": 1, "Medium": 2, "High": 3, "Critical": 4})
    df["channel_num"]  = df["Ticket Channel"].astype("category").cat.codes
    df["type_num"]     = df["Ticket Type"].astype("category").cat.codes

    corr_cols = ["Customer Satisfaction Rating", "resolution_hours", "priority_num", "channel_num", "type_num"]
    csat_corrs = (
        df[corr_cols].corr()["Customer Satisfaction Rating"]
        .drop("Customer Satisfaction Rating")
        .sort_values(key=abs, ascending=False)
    )

    top_driver   = csat_corrs.index[0]
    top_driver_r = float(csat_corrs.iloc[0])
    if all(abs(v) < 0.1 for v in csat_corrs.values):
        conclusion = "Nenhuma variável tem correlação significativa com CSAT — dataset sintético com CSAT uniformemente distribuído."
    else:
        conclusion = f"O principal correlato do CSAT é {top_driver} (r={top_driver_r:.3f})."

    csat_drivers = {
        "pearson_r": round(float(r), 4),
        "pearson_p": round(float(p), 4),
        "kruskal_channel_h": round(float(kw_ch[0]), 2), "kruskal_channel_p": round(float(kw_ch[1]), 4),
        "kruskal_type_h":    round(float(kw_ty[0]), 2), "kruskal_type_p":    round(float(kw_ty[1]), 4),
        "kruskal_priority_h":round(float(kw_pr[0]), 2), "kruskal_priority_p":round(float(kw_pr[1]), 4),
        "top_driver": top_driver,
        "top_driver_r": round(top_driver_r, 4),
        "conclusion": conclusion,
    }

    # ── Desperdício ───────────────────────────────────────────────────────────
    ANNUAL_VOLUME = 30_000
    COST_PER_HOUR = 35.0

    median_res = closed["resolution_hours"].median()
    mean_res   = closed["resolution_hours"].mean()
    above      = closed[closed["resolution_hours"] > median_res]
    above_frac = len(above) / len(closed)
    avg_excess = (above["resolution_hours"] - median_res).mean()

    annual_above   = ANNUAL_VOLUME * above_frac
    annual_excess  = annual_above * avg_excess
    annual_cost    = annual_excess * COST_PER_HOUR

    waste = {
        "median_hours": round(float(median_res), 2),
        "mean_hours":   round(float(mean_res), 2),
        "above_median_pct": round(float(above_frac * 100), 1),
        "avg_excess_hours": round(float(avg_excess), 2),
        "annual_volume": ANNUAL_VOLUME,
        "annual_excess_tickets": round(float(annual_above)),
        "annual_excess_hours":   round(float(annual_excess)),
        "annual_cost_brl":       round(float(annual_cost), 2),
    }

    # ── Heatmap canal × tipo ──────────────────────────────────────────────────
    pivot = (
        closed.groupby(["Ticket Channel", "Ticket Type"])["resolution_hours"]
        .mean()
        .unstack("Ticket Type")
    )
    heatmap = sorted(
        [
            {"channel": ch, "type": tp, "avg_hours": round(float(v), 1)}
            for (ch, tp), v in pivot.stack().items()
        ],
        key=lambda x: -x["avg_hours"],
    )

    # ── Qualidade dos dados ───────────────────────────────────────────────────
    same_day = (
        df["First Response Time"].dt.date == df["Time to Resolution"].dt.date
    ).sum()

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "priority": priority_list,
        "csat_drivers": csat_drivers,
        "waste": waste,
        "bottleneck_heatmap": heatmap,
        "data_quality": {
            "same_day_timestamps_pct": round(float(same_day / len(df) * 100), 1),
            "csat_is_uniform": True,
            "has_placeholder_text": True,
        },
    }

    out_path = DATA / "diagnostic_output.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"[generate_diagnostic] ✅ {out_path} ({len(priority_list)} prioridades, {len(heatmap)} células no heatmap)")

if __name__ == "__main__":
    main()
