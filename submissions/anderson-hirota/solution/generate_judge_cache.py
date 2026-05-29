#!/usr/bin/env python3
"""Generate the LLM-as-judge action cache for all current must-acts.

Run this once before launching the app (or after data changes). Streamlit
reads the cache only — never calls Claude in the request path, so the app
loads instantly.

Cost: ~117 Claude CLI calls × ~500 input tokens ≈ $0.05 total.
Time: ~6 minutes sequential (no parallelism — keeps the CLI happy).

Usage:
    cd submission/
    python3 generate_judge_cache.py
"""
import sys
from datetime import datetime

import pandas as pd

import app as app_mod
import scoring
import coaching
import manager as mgr_mod
from judge import judge_all_must_acts, judge_all_manager_must_acts

DATA_DIR = "data"


def main():
    accounts = pd.read_csv(f"{DATA_DIR}/accounts.csv")
    products = pd.read_csv(f"{DATA_DIR}/products.csv")
    teams = pd.read_csv(f"{DATA_DIR}/sales_teams.csv")
    pipeline = pd.read_csv(f"{DATA_DIR}/sales_pipeline.csv")
    for col in ("engage_date", "close_date"):
        pipeline[col] = pd.to_datetime(pipeline[col], errors="coerce")
    df = (
        pipeline
        .merge(teams, on="sales_agent", how="left")
        .merge(accounts, on="account", how="left")
        .merge(products, on="product", how="left")
    )

    candidates = [df[c].max() for c in ("engage_date", "close_date") if df[c].notna().any()]
    ref_date = max(candidates) if candidates else pd.Timestamp(datetime.today().date())
    print(f"ref_date: {ref_date.date()}", flush=True)

    scored, _ = scoring.score_pipeline(df, accounts_df=accounts, ref_date=ref_date)
    close_window = app_mod.empirical_close_window.__wrapped__(scored)

    open_d = scored[scored["deal_stage"].isin(["Prospecting", "Engaging"])].copy()
    open_d["is_ghost"] = app_mod.classify_pipeline_ghost(open_d, close_window)
    active = open_d[~open_d["is_ghost"]]

    must_acts = app_mod.compute_must_acts(active, close_window)
    print(f"must-acts to judge: {len(must_acts)}", flush=True)
    print(f"close_window: {close_window}d | ghost_threshold: {close_window*3}d", flush=True)
    print()

    results = judge_all_must_acts(must_acts, scored, close_window, verbose=True)
    print()
    print(f"DONE rep cache — {len(results)}/{len(must_acts)} actions")
    print(f"Cache dir: .judge_cache/")

    # ---- Manager cache ----
    print()
    print("=" * 60)
    print("MANAGER CACHE")
    print("=" * 60)
    open_d = scored[scored["deal_stage"].isin(["Prospecting", "Engaging"])].copy()
    open_d["is_ghost"] = app_mod.classify_pipeline_ghost(open_d, close_window)
    open_d["is_orphan"] = open_d["account"].isna()
    active = open_d[~open_d["is_ghost"] & ~open_d["is_orphan"]]

    coaching_by_rep = {rep: coaching.rep_alpha_signals(rep, scored) for rep in must_acts["sales_agent"].unique()}

    managers = sorted(must_acts["manager"].dropna().unique())
    total_mgr_results = 0
    total_mgr_must_acts = 0
    for m in managers:
        mma = mgr_mod.classify_manager_must_acts(scored, must_acts, coaching_by_rep, m)
        eligible = mma[mma["manager_action_type"] != "type_3_system"]
        if eligible.empty:
            continue
        print(f"\n--- Manager: {m} ({len(eligible)} actions) ---")
        results = judge_all_manager_must_acts(mma, scored, coaching_by_rep, close_window, verbose=True)
        total_mgr_results += len(results)
        total_mgr_must_acts += len(eligible)

    print()
    print(f"DONE manager cache — {total_mgr_results}/{total_mgr_must_acts} actions")


if __name__ == "__main__":
    sys.exit(main())
