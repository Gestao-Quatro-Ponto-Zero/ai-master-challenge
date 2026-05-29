# app.py — opinionated Lead Scorer.
# Inverts the pipeline-browser pattern: brief-first, table as drilldown.

import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from scoring import (
    score_pipeline,
    build_breakdown,
    FEATURE_DESCRIPTIONS,
    STALE_DAYS,
    PROSPECT_STALE_DAYS,
)
from judge import (
    load_cache_into_dict as load_judge_cache,
    load_manager_cache_into_dict as load_manager_judge_cache,
    judge_coaching_note,
    judge_call_prep,
    build_context as build_judge_context,
)
from coaching import rep_alpha_signals, team_alpha_signals, benchmark_for_rep, benchmark_for_team
import manager as mgr_mod
import actions

DATA_DIR = "data"
MUST_ACT_SCORE_FLOOR = 65          # high-score = top ~15% of active pool
MUST_ACT_TC_SCORE_FLOOR = 45       # time-critical also needs minimum quality (not "dead and old")
MUST_ACT_MAX_PER_REP = 5           # cognitive cap for a daily focus list
GHOST_WARN_RATIO = 0.92            # final 8% of window = ~14d before ghost-flip (act this week or lose)
MUST_ACT_TEAM_PREVIEW = 10         # global preview in Manager mode

st.set_page_config(
    page_title="Lead Scorer — Morning Brief",
    layout="wide",
    page_icon="🎯",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #e6e6e6;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
        padding: 12px 24px;
        background-color: #f8f9fb;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #fff3bf !important;
        color: #1a1a1a !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Data ----------

@st.cache_data
def load_data():
    accounts = pd.read_csv(os.path.join(DATA_DIR, "accounts.csv"))
    products = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
    teams = pd.read_csv(os.path.join(DATA_DIR, "sales_teams.csv"))
    pipeline = pd.read_csv(os.path.join(DATA_DIR, "sales_pipeline.csv"))

    for col in ("engage_date", "close_date"):
        if col in pipeline.columns:
            pipeline[col] = pd.to_datetime(pipeline[col], errors="coerce")

    df = (
        pipeline
        .merge(teams, on="sales_agent", how="left")
        .merge(accounts, on="account", how="left")
        .merge(products, on="product", how="left")
    )
    return df, accounts


@st.cache_data
def empirical_close_window(df: pd.DataFrame) -> int:
    """Median days from engage to close among Won deals.
    Anchors what 'reasonable pipeline age' means for THIS dataset.
    """
    won = df[(df["deal_stage"] == "Won") & df["engage_date"].notna() & df["close_date"].notna()].copy()
    if not len(won):
        return 90
    won["cycle"] = (won["close_date"] - won["engage_date"]).dt.days
    return int(max(30, won["cycle"].median()))


def classify_pipeline_ghost(df: pd.DataFrame, close_window: int) -> pd.Series:
    """A deal is 'ghost' when it's been open more than 3× a typical cycle.
    Empirically derived from this dataset — not an arbitrary cutoff.
    """
    threshold = close_window * 3
    return df["days_in_pipeline"].fillna(threshold + 1) > threshold


def classify_time_critical(df: pd.DataFrame, close_window: int) -> pd.Series:
    """Engaging deals in the FINAL stretch before ghost-flip — and with enough
    quality signal to be worth rescuing.

    Restricted to Engaging (Prospecting in long pipeline is usually dead data,
    not real urgency). Score floor (TC_SCORE_FLOOR) prevents the panel from
    being flooded with dead deals that happen to be old.
    """
    ghost_threshold = close_window * 3
    warn_threshold = ghost_threshold * GHOST_WARN_RATIO
    return (
        (df["deal_stage"] == "Engaging")
        & (df["days_in_pipeline"].notna())
        & (df["days_in_pipeline"] >= warn_threshold)
        & (df["days_in_pipeline"] <= ghost_threshold)
        & (df["score"] >= MUST_ACT_TC_SCORE_FLOOR)
    )


def compute_must_acts(active: pd.DataFrame, close_window: int) -> pd.DataFrame:
    """Variable per-rep must-act list combining quality and temporal urgency.

    Selection logic (per rep, cap at MUST_ACT_MAX_PER_REP):
      1. high_score = active deals with score >= FLOOR
      2. time_critical = Engaging deals near ghost threshold
      3. union, dedup, prefer (high_score & time_critical) > time_critical > high_score
      4. cap at MAX, keeping top by score

    Adds column `must_act_reason` ∈ {"both", "time_critical", "high_score"}.
    Returns the union — sort/select happens here, render layer just reads.
    """
    if active.empty:
        return active.assign(must_act_reason=pd.Series(dtype=str))

    base = active.copy()
    base["_is_high"] = base["score"] >= MUST_ACT_SCORE_FLOOR
    base["_is_tc"] = classify_time_critical(base, close_window)
    candidates = base[base["_is_high"] | base["_is_tc"]].copy()
    if candidates.empty:
        return candidates.assign(must_act_reason=pd.Series(dtype=str))

    candidates["must_act_reason"] = candidates.apply(
        lambda r: "both" if (r["_is_high"] and r["_is_tc"])
                  else ("time_critical" if r["_is_tc"] else "high_score"),
        axis=1,
    )
    # priority order for keeping when capping: both > time_critical > high_score, then score
    priority = {"both": 0, "time_critical": 1, "high_score": 2}
    candidates["_priority"] = candidates["must_act_reason"].map(priority)
    candidates = candidates.sort_values(
        ["_priority", "score"], ascending=[True, False]
    )

    capped = candidates.groupby("sales_agent", as_index=False).head(MUST_ACT_MAX_PER_REP)
    return capped.drop(columns=["_is_high", "_is_tc", "_priority"]).sort_values(
        ["sales_agent", "score"], ascending=[True, False]
    )


def fmt_money(v):
    if pd.isna(v):
        return "—"
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:,.0f}"


def score_color(s):
    if s >= 70: return "🟢"
    if s >= 50: return "🟡"
    return "🔴"


# ---------- Manager mode ----------

def reason_badge(reason: str) -> str:
    return {"both": "🔥⭐", "time_critical": "🔥", "high_score": "⭐"}.get(reason, "")


def compute_data_quality(scored: pd.DataFrame, close_window: int) -> dict:
    """Surfaces problems the rule-based scorer silently averages away."""
    n_total = len(scored)
    open_mask = scored["deal_stage"].isin(["Prospecting", "Engaging"])
    open_d = scored[open_mask]

    # Unmapped accounts (sector NaN means account-level enrichment failed for these deals)
    unmapped = scored[scored["sector"].isna()]

    # Orphan deals: open, account literally NaN — worst hygiene problem
    orphan_open = open_d[open_d["account"].isna()]

    # Ghost share of open pipeline
    ghost_n = (open_d["days_in_pipeline"].fillna(0) > close_window * 3).sum()

    # Rep workload imbalance: top/bottom rep open pipeline value
    rep_pipe = open_d.groupby("sales_agent")["expected_value"].sum().sort_values(ascending=False)
    rep_imb = None
    if len(rep_pipe) >= 5:
        top5_mean = rep_pipe.head(5).mean()
        bot5_mean = rep_pipe.tail(5).mean()
        rep_imb = {
            "top5_mean_usd": top5_mean,
            "bot5_mean_usd": bot5_mean,
            "ratio": (top5_mean / bot5_mean) if bot5_mean > 0 else None,
        }

    # close_value vs sales_price discrepancy on Won — sanity
    won = scored[scored["deal_stage"] == "Won"].copy()
    won_neg = won[(won["close_value"] <= 0) | won["close_value"].isna()]

    # Deals open without account mapping
    open_unmapped = open_d[open_d["sector"].isna()]

    return {
        "n_total_deals": int(n_total),
        "orphan_open_n": int(len(orphan_open)),
        "orphan_open_pct": round(len(orphan_open) / max(len(open_d), 1) * 100, 1),
        "unmapped_accounts_n": int(len(unmapped)),
        "unmapped_accounts_pct": round(len(unmapped) / max(n_total, 1) * 100, 1),
        "open_unmapped_n": int(len(open_unmapped)),
        "open_unmapped_pct": round(len(open_unmapped) / max(len(open_d), 1) * 100, 1),
        "ghost_n": int(ghost_n),
        "ghost_pct_of_open": round(ghost_n / max(len(open_d), 1) * 100, 1),
        "rep_imbalance": rep_imb,
        "won_with_no_value_n": int(len(won_neg)),
        "won_with_no_value_pct": round(len(won_neg) / max(len(won), 1) * 100, 1),
    }


def render_data_quality_panel(scored: pd.DataFrame, close_window: int):
    with st.expander("🧪 Data quality — what the rule-based scorer silently averages away"):
        dq = compute_data_quality(scored, close_window)
        st.caption(
            "Honest disclosure of dataset issues. In production this panel drives "
            "a CRM cleanup workflow before pipeline review meetings."
        )

        rows = [
            {
                "Flag": "🚨 Orphan open deals (account NaN)",
                "Count": f"{dq['orphan_open_n']:,}",
                "% of all deals": f"{dq['orphan_open_pct']}% of open",
                "Why it matters": "Deal exists with no company linked. Rep cannot act — needs CRM cleanup (link to account record) before this deal is workable.",
            },
            {
                "Flag": "Unmapped accounts (sector/revenue NaN)",
                "Count": f"{dq['unmapped_accounts_n']:,}",
                "% of all deals": f"{dq['unmapped_accounts_pct']}%",
                "Why it matters": "Firmographic enrichment failed — scoring defaults these to neutral, hiding the gap.",
            },
            {
                "Flag": "Pipeline ghosts (>3× empirical cycle)",
                "Count": f"{dq['ghost_n']:,}",
                "% of all deals": f"{dq['ghost_pct_of_open']}% of open",
                "Why it matters": "Deals carried but not worked. Inflates pipeline value, distorts forecast.",
            },
            {
                "Flag": "Won deals with $0/NaN close value",
                "Count": f"{dq['won_with_no_value_n']:,}",
                "% of all deals": f"{dq['won_with_no_value_pct']}% of Won",
                "Why it matters": "Revenue recognition gap — these wins are uncountable in $ terms.",
            },
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        imb = dq.get("rep_imbalance")
        if imb and imb.get("ratio"):
            st.markdown(
                f"**Workload imbalance**: top 5 reps carry an avg pipeline of "
                f"{fmt_money(imb['top5_mean_usd'])} vs bottom 5 at {fmt_money(imb['bot5_mean_usd'])} "
                f"— a {imb['ratio']:.1f}× spread. Worth a manager conversation about routing."
            )


def apply_judge_actions(must_acts: pd.DataFrame, scored: pd.DataFrame, close_window: int) -> pd.DataFrame:
    """Override the template `action` column with LLM-judged actions where cached.
    Adds `is_judged` boolean column for visual differentiation in render.
    Pure cache read — no Claude calls in the request path.
    """
    if must_acts.empty:
        return must_acts.assign(is_judged=False)
    judged = load_judge_cache(must_acts, scored, close_window)
    out = must_acts.copy()
    out["is_judged"] = out["opportunity_id"].isin(judged)
    out.loc[out["is_judged"], "action"] = out.loc[out["is_judged"], "opportunity_id"].map(judged)
    return out


def render_manager_mode(active: pd.DataFrame, ghost: pd.DataFrame, orphan: pd.DataFrame, close_window: int, scored: pd.DataFrame, stage_probs: dict, manager: str | None = None):
    """Manager mode = opinionated brief, mirroring Rep mode at higher altitude.

    Manager has THEIR OWN must-acts in three flavors:
      Type 1 — Top-value deal where manager visibility/sponsorship matters (top-decile by value)
      Type 2 — Executive intervention (rep stuck, manager breaks the wall)
      Type 3 — System decision (triage 1:1, redistribute load, fix systemic issue)
    """
    # `manager` is selected in the sidebar (main()) and passed in. Compute everything for this manager.
    must_acts_global = compute_must_acts(active, close_window)
    if manager is None:
        # Defensive fallback (shouldn't happen — sidebar always provides selection)
        st.warning("No manager selected.")
        return

    must_acts = must_acts_global  # already includes manager column
    coaching_by_rep = {rep: rep_alpha_signals(rep, scored) for rep in must_acts["sales_agent"].unique()}

    mgr_must_acts = mgr_mod.classify_manager_must_acts(scored, must_acts, coaching_by_rep, manager)
    critical_reps = mgr_mod.identify_critical_reps(must_acts, orphan, manager)
    patterns = mgr_mod.detect_systemic_patterns(scored, must_acts, orphan, active, manager)
    type_3_actions = mgr_mod.build_type_3_actions(critical_reps, patterns, manager)
    team_coach = team_alpha_signals(manager, scored)

    # Overlay LLM-judged manager actions where cached
    if not mgr_must_acts.empty:
        ghost_threshold = close_window * 3
        mgr_judged = load_manager_judge_cache(mgr_must_acts, scored, coaching_by_rep, ghost_threshold)
        mgr_must_acts["is_judged"] = mgr_must_acts["opportunity_id"].isin(mgr_judged)
        mgr_must_acts.loc[mgr_must_acts["is_judged"], "action"] = mgr_must_acts.loc[mgr_must_acts["is_judged"], "opportunity_id"].map(mgr_judged)

    # ---- Apply action layer: filter out must-acts the manager already acted on
    acted = actions.acted_opp_ids(manager)
    if acted and not mgr_must_acts.empty:
        mgr_must_acts = mgr_must_acts[~mgr_must_acts["opportunity_id"].isin(acted)]
    redistribution_state = actions.redistribution_decisions(manager)
    coaching_sent = actions.coaching_note_sent_for(manager)
    action_summary = actions.summary_today(manager)

    # Header
    n_reps = active[active["manager"] == manager]["sales_agent"].nunique() + \
             orphan[orphan["manager"] == manager]["sales_agent"].nunique()
    st.subheader(f"{manager} — today's brief")
    st.caption(
        f"Manages **{n_reps}** reps. "
        f"Brief: {len(mgr_must_acts)} must-acts of your own, "
        f"{len(critical_reps)} rep(s) in critical state, "
        f"{len(patterns)} systemic alert(s)."
    )

    # KPI row (above tabs — always-visible action context)
    team_active = active[active["manager"] == manager]
    team_must_acts = must_acts[must_acts["manager"] == manager]
    team_value = team_active["expected_value"].sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "🎯 Your must-acts", f"{len(mgr_must_acts)}",
        help="Up to 5 per manager. Mix of 🚨 executive intervention (rep needs you to unblock), 👑 top-value (manager visibility/sponsorship on strategic deals), and 🔧 system decisions (triage, redistribute).",
    )
    c2.metric(
        "🚨 Reps in critical state", f"{len(critical_reps)}/{n_reps}",
        help="Reps with ≥2 time-critical deals. These need 1:1 attention before tomorrow.",
    )
    c3.metric(
        "📊 Team must-acts", f"{len(team_must_acts):,}",
        help="All must-acts across your team's reps. Each rep sees their own subset in Rep mode.",
    )
    c4.metric(
        "💰 Active pipeline value", fmt_money(team_value),
        help="Sum of expected value across non-ghost, non-orphan open deals on your team.",
    )

    st.caption(
        "**📋 Brief** = what to act on today · **📊 Dashboard** = how the team is performing"
    )

    tab_brief, tab_dash = st.tabs(["📋 Today's brief", "📊 Performance dashboard"])

    with tab_brief:
        _render_manager_must_acts(mgr_must_acts, type_3_actions, action_summary, manager)
        st.divider()
        _render_help_requests(manager)
        st.divider()
        _render_critical_reps(critical_reps, must_acts, active, coaching_by_rep, manager, coaching_sent)
        st.divider()
        _render_redistribution(critical_reps, must_acts, active, coaching_by_rep, manager)
        if patterns:
            st.divider()
            _render_systemic_patterns(patterns, manager)
        st.divider()
        _render_audit_log(manager, role_label="manager")

    with tab_dash:
        _render_benchmark(benchmark_for_team(manager, scored), scope="team")
        st.divider()
        _render_team_coaching(team_coach)
        st.divider()
        with st.expander("🔍 Leaderboard — full team-level breakdown across all managers", expanded=True):
            render_manager_leaderboard_drilldown(active, ghost, orphan, close_window, scored)
        st.divider()
        render_pipeline_drilldown(scored, scope={"kind": "manager", "name": manager} if manager else None)
        st.divider()
        render_data_quality_panel(scored, close_window)
        st.divider()
        _render_how_scoring_works(stage_probs)
        st.divider()
        # JSON export — composability hook for downstream agents
        n_reps_count = active[active["manager"] == manager]["sales_agent"].nunique() + \
                       orphan[orphan["manager"] == manager]["sales_agent"].nunique()
        pipeline_health = {
            "ghost_threshold_days": close_window * 3,
            "ghost_count": int((ghost["manager"] == manager).sum()),
            "orphan_count": int((orphan["manager"] == manager).sum()),
            "active_count": int((active["manager"] == manager).sum()),
            "n_reps": int(n_reps_count),
        }
        ref_for_json = scored["close_date"].max() if scored["close_date"].notna().any() else pd.Timestamp(datetime.today().date())
        mgr_brief = build_manager_brief_json(
            manager=manager,
            ref_date=ref_for_json,
            mgr_must_acts=mgr_must_acts,
            type_3_actions=type_3_actions,
            critical_reps=critical_reps,
            systemic_patterns=patterns,
            team_coaching=team_coach,
            pipeline_health=pipeline_health,
            close_window=close_window,
        )
        _render_json_export(mgr_brief, kind="manager", name=manager)


def _render_manager_must_acts(mma: pd.DataFrame, type_3_actions: list, action_summary: dict, manager: str):
    st.markdown("### 🎯 Your must-acts today")

    # Action counter — brief shrinks as manager acts
    done = action_summary.get("done", 0)
    defer = action_summary.get("defer", 0)
    skip = action_summary.get("skip", 0)
    if done or defer or skip:
        st.caption(
            f"✓ {done} done · ⏰ {defer} deferred · ✗ {skip} skipped today. Brief shrinks as you act."
        )

    if mma.empty and not type_3_actions:
        if done or defer or skip:
            st.success("✅ All must-acts handled today. Brief cleared.")
        else:
            st.success(
                "No manager-level moves today. Your team can run on autopilot — "
                "no strategic deals at risk, no rep in crisis."
            )
        return

    judged_count = int(mma["is_judged"].sum()) if not mma.empty and "is_judged" in mma.columns else 0
    legend_parts = [
        "🚨 executive intervention",
        "👑 top-value (manager visibility)",
        "🔧 system decision",
    ]
    st.caption(" · ".join(legend_parts))
    if judged_count or not mma.empty:
        fallback = len(mma) - judged_count
        st.caption(
            f"**✨ = LLM-judged action** (cites deal-specific facts from account/sector/rep history). "
            f"**{judged_count}/{len(mma)} here use LLM**; {fallback} fell back to rule-based template "
            "(LLM output failed validation or not cached — graceful fallback)."
        )

    # Build unified rows — Type 2 first (most urgent), then Type 1, then Type 3
    rows = []
    type_2 = mma[mma["manager_action_type"] == "type_2_intervention"]
    type_1 = mma[mma["manager_action_type"] == "type_1_closer"]

    for _, d in type_2.iterrows():
        rows.append(_build_must_act_row(d, "🚨"))
    for _, d in type_1.iterrows():
        rows.append(_build_must_act_row(d, "👑"))
    for t3 in type_3_actions[:5]:
        rows.append(_build_type_3_row(t3, "🔧"))

    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
            height=38 + 35 * len(rows) + 4,
            column_config={
                "Type": st.column_config.TextColumn(
                    width="small",
                    help="🚨 executive intervention (rep needs you to unblock) · 👑 top-value (manager visibility on strategic deals) · 🔧 system decision (triage, redistribute)",
                ),
                "Deal / Decision": st.column_config.TextColumn(width="medium"),
                "Context": st.column_config.TextColumn(width="medium"),
                "Action": st.column_config.TextColumn(
                    width="large",
                    help="Recommended next step. **✨ in the Deal cell** = LLM-judged: action text generated by Claude reading the deal's full context (account, sector, days remaining, rep historical close rate, other open deals at account). Without ✨ = rule-based template fallback (used when LLM output failed validation or isn't cached).",
                ),
            },
        )

        # ---- Action toolbar: log a decision on one must-act
        if not mma.empty:
            with st.expander("🎬 Take action on a must-act", expanded=False):
                opp_options = {
                    f"{d['account'] if pd.notna(d.get('account')) else '(unmapped)'} — {d['product']} ({d['sales_agent']})": d["opportunity_id"]
                    for _, d in mma.iterrows()
                }
                if opp_options:
                    selected_label = st.selectbox(
                        "Pick must-act",
                        list(opp_options.keys()),
                        key=f"action_select_{manager}",
                    )
                    chosen_opp = opp_options[selected_label]

                    # Preview of the selected must-act for visual confirmation before logging
                    deal_row = mma[mma["opportunity_id"] == chosen_opp].iloc[0]
                    badge_for_type = {
                        "type_2_intervention": "🚨",
                        "type_1_closer": "👑",
                    }.get(deal_row["manager_action_type"], "🎯")
                    judged_mark = " ✨" if deal_row.get("is_judged") else ""
                    deal_label = (
                        f"{deal_row['account'] if pd.notna(deal_row.get('account')) else '(unmapped)'}"
                        f" — {deal_row['product']}{judged_mark}"
                    )
                    days_n = deal_row.get("days_in_pipeline")
                    days_str = f"{int(days_n)}d" if pd.notna(days_n) else "—"
                    rationale = deal_row.get("manager_action_rationale", "")
                    context_parts = [fmt_money(deal_row["expected_value"]), deal_row["sales_agent"], days_str]
                    if rationale:
                        context_parts.append(rationale)
                    with st.container(border=True):
                        st.markdown(f"{badge_for_type} **{deal_label}**")
                        st.caption(" · ".join(context_parts))
                        st.markdown(f"▸ {deal_row['action']}")

                    action_kind = st.radio(
                        "Action",
                        ["✓ Done", "⏰ Defer", "✗ Skip"],
                        horizontal=True,
                        key=f"action_kind_{manager}",
                    )
                    note = ""
                    if action_kind.startswith("⏰") or action_kind.startswith("✗"):
                        note = st.text_input(
                            "Reason (required)",
                            placeholder="e.g. waiting for CFO callback / not worth my time because...",
                            key=f"action_note_{manager}",
                        )
                    button_label = {
                        "✓ Done": "Mark as Done",
                        "⏰ Defer": "Defer must-act",
                        "✗ Skip": "Skip & log reason",
                    }.get(action_kind, "Log action")
                    if st.button(button_label, key=f"action_submit_{manager}", type="primary"):
                        if action_kind.startswith("✓"):
                            actions.log_action(manager, actions.ACTION_MUST_ACT_DONE, {"opp_id": chosen_opp})
                            st.success("Logged: must-act marked done.")
                            st.rerun()
                        elif note.strip():
                            atype = actions.ACTION_MUST_ACT_DEFER if action_kind.startswith("⏰") else actions.ACTION_MUST_ACT_SKIP
                            actions.log_action(manager, atype, {"opp_id": chosen_opp, "note": note.strip()})
                            st.success("Logged with reason.")
                            st.rerun()
                        else:
                            st.warning("Provide a reason for Defer / Skip.")


def _build_must_act_row(deal: pd.Series, badge: str) -> dict:
    account = deal["account"] if pd.notna(deal["account"]) else "(unmapped)"
    days_n = deal.get("days_in_pipeline")
    days_str = f"{int(days_n)}d" if pd.notna(days_n) else "—"
    rationale = deal.get("manager_action_rationale", "")
    judged_mark = " ✨" if deal.get("is_judged") else ""

    deal_label = f"{account} — {deal['product']}{judged_mark}"
    context_parts = [fmt_money(deal["expected_value"]), deal["sales_agent"], days_str]
    if rationale:
        context_parts.append(rationale)
    context = " · ".join(context_parts)

    return {
        "Type": badge,
        "Deal / Decision": deal_label,
        "Context": context,
        "Action": deal["action"],
    }


def _build_type_3_row(t3: dict, badge: str) -> dict:
    category = t3.get("category", "action").replace("_", " ").title()
    rep = t3.get("rep")
    title = f"{category}" + (f" — {rep}" if rep else "")
    deal_count = t3.get("deal_count", 0)
    context = f"{deal_count} deals affected" if deal_count else "team-wide signal"
    return {
        "Type": badge,
        "Deal / Decision": title,
        "Context": context,
        "Action": t3["label"],
    }


def _render_critical_reps(critical_reps: list, must_acts: pd.DataFrame, active: pd.DataFrame, coaching_by_rep: dict, manager: str, coaching_sent: dict):
    st.markdown("### 🚨 Reps in critical state")
    if not critical_reps:
        st.success("No rep on your team is in critical state today. Good day for forward-looking coaching, not firefighting.")
        return

    redist_state = actions.redistribution_decisions(manager)

    for cr in critical_reps:
        rep = cr["rep"]
        with st.expander(
            f"🔴 **{rep}** · 🔥 {cr['time_critical_count']} · ⭐ {cr['high_score_count']} · "
            f"🚨 {cr['orphan_count']} orphans · {fmt_money(cr['pipeline_value'])} at stake",
            expanded=(critical_reps.index(cr) == 0),
        ):
            cols = st.columns([2, 1])
            with cols[0]:
                st.markdown("**🔥 Top time-critical deals**")
                td_rows = []
                for d in cr["top_time_critical_deals"]:
                    days_val = d["days_in_pipeline"] if d["days_in_pipeline"] is not None else None
                    td_rows.append({
                        "Account": d["account"],
                        "Product": d["product"],
                        "Days": days_val,
                        "Value": f"${d['value']:,.0f}",
                        "Score": int(round(d["score"])),
                    })
                if td_rows:
                    st.dataframe(
                        pd.DataFrame(td_rows),
                        use_container_width=True, hide_index=True,
                        height=38 + 35 * len(td_rows) + 4,
                        column_config={
                            "Account": st.column_config.TextColumn(width="medium"),
                            "Product": st.column_config.TextColumn(width="medium"),
                            "Days": st.column_config.NumberColumn(width="small"),
                            "Value": st.column_config.TextColumn(width="small"),
                            "Score": st.column_config.NumberColumn(width="small"),
                        },
                    )

            with cols[1]:
                rep_coach = coaching_by_rep.get(rep, {})
                delta_help = "Win rate of this rep in this slice minus team average, in percentage points (pp). 'n' is sample size."
                if rep_coach.get("sector_bleed"):
                    st.markdown("**🔴 Where they bleed**")
                    bleed_rows = [
                        {"Slice": b["label"], "Δ": f"{b['delta_pp']:.0f}pp", "n": int(b["n_total"])}
                        for b in rep_coach["sector_bleed"][:2]
                    ]
                    st.dataframe(
                        pd.DataFrame(bleed_rows),
                        use_container_width=True, hide_index=True,
                        height=38 + 35 * len(bleed_rows) + 4,
                        column_config={
                            "Slice": st.column_config.TextColumn(width="medium"),
                            "Δ": st.column_config.TextColumn(width="small", help=delta_help),
                            "n": st.column_config.NumberColumn(width="small"),
                        },
                    )
                if rep_coach.get("sector_alpha"):
                    st.markdown("**🟢 Where they have alpha**")
                    alpha_rows = [
                        {"Slice": a["label"], "Δ": f"+{a['delta_pp']:.0f}pp", "n": int(a["n_total"])}
                        for a in rep_coach["sector_alpha"][:2]
                    ]
                    st.dataframe(
                        pd.DataFrame(alpha_rows),
                        use_container_width=True, hide_index=True,
                        height=38 + 35 * len(alpha_rows) + 4,
                        column_config={
                            "Slice": st.column_config.TextColumn(width="medium"),
                            "Δ": st.column_config.TextColumn(width="small", help=delta_help),
                            "n": st.column_config.NumberColumn(width="small"),
                        },
                    )

            # ---- Coaching note (LLM-pre-filled draft, manager edits, logs send)
            st.markdown("---")
            sent_state = coaching_sent.get(rep)
            if sent_state:
                st.success(f"✅ Coaching note sent at {sent_state['ts'][:16]} UTC")
                with st.expander("Show sent note"):
                    st.write(sent_state["note"])
            else:
                st.markdown("**📝 Coaching note draft** — LLM-pre-filled from this rep's signals, edit and send")
                rep_coach_local = coaching_by_rep.get(rep, {})
                regen_key = f"regen_{rep}"
                if regen_key not in st.session_state:
                    st.session_state[regen_key] = 0
                regen_count = st.session_state[regen_key]
                draft_key = f"draft_{rep}_{regen_count}"
                if draft_key not in st.session_state:
                    # Bypass disk cache on regenerate so a new draft actually comes from LLM
                    use_cache = (regen_count == 0)
                    with st.spinner(f"Generating draft for {rep}..."):
                        draft = judge_coaching_note(rep, manager, cr, rep_coach_local, use_cache=use_cache)
                    st.session_state[draft_key] = draft or (
                        f"{rep.split()[0]}, you're carrying {cr['time_critical_count']} time-critical deals "
                        f"and {cr['orphan_count']} orphan records. Block focused time this week on the top "
                        f"deals — I'm covering escalation. — {manager.split()[0]}"
                    )
                edited = st.text_area(
                    "Edit before sending",
                    value=st.session_state[draft_key],
                    height=160,
                    key=f"note_textarea_{rep}_{regen_count}",
                )
                bcols = st.columns([1, 1, 4])
                with bcols[0]:
                    rep_first_name = rep.split()[0] if rep else "rep"
                    if st.button(f"✓ Send to {rep_first_name}", key=f"send_{rep}", type="primary"):
                        actions.log_action(manager, actions.ACTION_COACHING_NOTE_SENT, {"rep": rep, "note": edited.strip()})
                        st.success("Logged.")
                        st.rerun()
                with bcols[1]:
                    if st.button("↻ Regenerate", key=f"regen_btn_{rep}"):
                        st.session_state[regen_key] += 1
                        st.rerun()
                if regen_count > 0:
                    st.caption(f"_Regenerated {regen_count}× — bypassing cache for fresh LLM output._")

            # Redistribution lives in its own top-level section now — see _render_redistribution


def _render_benchmark(b: dict, scope: str):
    """Benchmark using metric widgets — same visual weight as the top KPI row."""
    st.markdown("### 📊 Where you stand")
    if not b.get("has_data"):
        st.caption(f"_Not enough closed-deal history to benchmark reliably ({b.get('reason', '')})._")
        return

    cr = b.get("close_rate", {})
    cy = b.get("cycle")
    ref_close_label = "top quartile of reps" if scope == "rep" else "top-3 teams avg"
    ref_cycle_label = "top decile" if scope == "rep" else "top-3 teams avg"
    ref_close_value = cr.get("top_quartile") if scope == "rep" else cr.get("top3_avg")
    ref_cycle_value = cy.get("top_decile_days") if cy and scope == "rep" else (cy.get("top3_avg_days") if cy else None)

    c1, c2 = st.columns(2)
    with c1:
        if cr.get("you_are_top"):
            c1.metric(
                "🏆 Close rate (top tier)",
                f"{cr['you']*100:.0f}%",
                delta=f"+{abs(cr['delta_pp']):.0f}pp ahead",
                delta_color="normal",
                help=f"You're in the {ref_close_label}. Benchmark: {ref_close_value*100:.0f}%.",
            )
        else:
            c1.metric(
                "Close rate",
                f"{cr['you']*100:.0f}%",
                delta=f"{cr['delta_pp']:+.0f}pp vs top",
                delta_color="normal",
                help=f"{ref_close_label.capitalize()}: {ref_close_value*100:.0f}%. Gap = {abs(cr['delta_pp']):.0f}pp to close.",
            )
    with c2:
        if not cy:
            c2.metric("Cycle speed", "—", help="Not enough Won deals with engage+close dates to compute median cycle.")
        elif cy.get("you_are_top"):
            c2.metric(
                "🏆 Cycle speed (top tier)",
                f"{cy['you_days']}d",
                delta=f"-{abs(cy['delta_days']):.0f}d faster",
                delta_color="inverse",
                help=f"Median days from engage to close on Won deals. You're at the {ref_cycle_label}.",
            )
        else:
            c2.metric(
                "Cycle speed",
                f"{cy['you_days']}d",
                delta=f"{cy['delta_days']:+.0f}d vs top",
                delta_color="inverse",
                help=f"Median days from engage to close on Won deals. {ref_cycle_label.capitalize()}: {int(ref_cycle_value)}d. Lower is better.",
            )

    # Leaderboard
    lb = b.get("leaderboard")
    if lb and lb.get("top5"):
        entity_label = "reps" if scope == "rep" else "teams"
        you_name = b.get("rep") if scope == "rep" else b.get("manager")
        total = lb.get("total_ranked", 0)
        # If pool is small (≤6), drop "top 5" framing and just show full leaderboard
        show_full = total <= 6
        header = (
            f"**🏆 Leaderboard — {total} {entity_label} by close rate**"
            if show_full
            else f"**🏆 Top 5 {entity_label} by close rate**"
        )
        st.markdown(header)
        rows = []
        for i, item in enumerate(lb["top5"], start=1):
            is_you = item["name"] == you_name
            rows.append({
                "#": str(i),
                "Name": f"👤 {item['name']} ← YOU" if is_you else item["name"],
                "Close rate": f"{item['close_rate']*100:.0f}%",
            })
        # Append the "you" row when out of top 5 (and pool is big enough to warrant the gap)
        if not lb["you_in_top5"] and not show_full:
            rows.append({"#": "⋮", "Name": "⋮", "Close rate": "⋮"})
            you_pct = (b.get("close_rate", {}).get("you", 0)) * 100
            rows.append({
                "#": str(lb["ahead"] + 1) if lb.get("ahead") is not None else "—",
                "Name": f"👤 {you_name} ← YOU",
                "Close rate": f"{you_pct:.0f}%",
            })
        lb_df = pd.DataFrame(rows)

        def _highlight_you(row):
            is_you_row = "← YOU" in str(row["Name"])
            style = "background-color: #fff3bf; font-weight: 600;" if is_you_row else ""
            return [style for _ in row]

        st.dataframe(
            lb_df.style.apply(_highlight_you, axis=1),
            use_container_width=True,
            hide_index=True,
            height=38 + 35 * len(rows) + 4,
            column_config={
                "#": st.column_config.TextColumn(width="small"),
                "Name": st.column_config.TextColumn(width="medium"),
                "Close rate": st.column_config.TextColumn(width="small"),
            },
        )
        if lb.get("ahead") is not None and lb.get("behind") is not None:
            if lb["you_in_top5"]:
                st.caption(
                    f"_You're in the top 5 of {total} ranked {entity_label}. "
                    f"{lb['behind']} behind you._"
                )
            else:
                st.caption(
                    f"_{lb['ahead']} {entity_label} ahead of you, {lb['behind']} behind. "
                    f"{total} ranked total (only those with enough closed deals to qualify)._"
                )

    st.caption(
        "_Gap to top, not exact rank — focus is on ambition, not punishment. "
        "Coaching panel below has the breakdown by sector / product._"
    )


def _render_help_requests(manager: str):
    """🆘 Bidirectional flow — reps escalate deals to the manager.
    Lives between Must-acts and Critical reps because help requests ARE
    must-acts the rep can't handle alone. Manager decides: take it on or push back.
    """
    pending = actions.pending_help_requests_for_manager(manager)
    st.markdown("### 🆘 Help requests from your team")
    if not pending:
        st.caption(
            "_No pending help requests today. Reps escalate from their Rep mode brief when they need "
            "your authority/relationship/intel to unlock a deal — they appear here in real time._"
        )
        return

    st.caption(
        f"**{len(pending)} request(s)** waiting on your decision. Each rep flagged "
        "a deal they cannot move without you."
    )

    for rec in pending:
        opp_id = rec.get("opp_id")
        from_rep = rec.get("actor", "(unknown rep)")
        account = rec.get("account") or "(unmapped)"
        product = rec.get("product", "—")
        value = rec.get("value", 0)
        ask = rec.get("ask", "(no detail)")
        ts = rec.get("ts", "")[:19].replace("T", " ")

        with st.container():
            st.markdown(
                f"🆘 **{from_rep}** on **{account} — {product}** "
                f"(${value:,.0f}) · _raised {ts} UTC_"
            )
            st.info(f"**Ask:** {ask}")
            bcols = st.columns([1.5, 1, 4])
            with bcols[0]:
                if st.button("✓ Acknowledge & take", key=f"help_ack_{opp_id}", type="primary"):
                    actions.log_action(manager, actions.ACTION_MANAGER_HELP_ACK, {
                        "opp_id": opp_id, "from_rep": from_rep, "account": account,
                    })
                    st.rerun()
            with bcols[1]:
                # Dismiss requires a reason — use session_state to toggle a reason input
                dismiss_key = f"dismiss_open_{opp_id}"
                if st.button("✗ Dismiss", key=f"help_dismiss_btn_{opp_id}"):
                    st.session_state[dismiss_key] = True
            if st.session_state.get(dismiss_key, False):
                reason = st.text_input(
                    "Reason for dismissal (rep will see this)",
                    key=f"help_dismiss_reason_{opp_id}",
                )
                if st.button("Confirm dismiss", key=f"help_dismiss_confirm_{opp_id}"):
                    if reason.strip():
                        actions.log_action(manager, actions.ACTION_MANAGER_HELP_DISMISSED, {
                            "opp_id": opp_id, "from_rep": from_rep, "account": account, "note": reason.strip(),
                        })
                        st.session_state[dismiss_key] = False
                        st.rerun()
                    else:
                        st.warning("Reason is required so the rep understands and can re-plan.")
            st.markdown("")


def _render_redistribution(critical_reps: list, must_acts: pd.DataFrame, active: pd.DataFrame, coaching_by_rep: dict, manager: str):
    """Top-level manager move: reallocate load across reps.
    Lives at manager altitude (not embedded inside critical rep card) because the
    decision is cross-rep — manager is choosing who absorbs what.
    """
    st.markdown("### 🔄 Redistribution opportunities")
    if not critical_reps:
        st.caption("_No reps in critical state — no redistribution needed today._")
        return

    redist_state = actions.redistribution_decisions(manager)

    # Compute all suggestions across critical reps, grouped by donor
    suggestions_by_donor = []
    total_open = 0
    total_resolved = 0
    for cr in critical_reps:
        sug = mgr_mod.suggest_redistribution(cr, must_acts, active, coaching_by_rep, manager)
        if sug:
            open_in_group = sum(1 for s in sug if s["deal"]["opportunity_id"] not in redist_state)
            resolved_in_group = len(sug) - open_in_group
            total_open += open_in_group
            total_resolved += resolved_in_group
            suggestions_by_donor.append({
                "donor": cr["rep"],
                "donor_tc": cr["time_critical_count"],
                "suggestions": sug,
            })

    if not suggestions_by_donor:
        st.info(
            "**No internal capacity today** — all your reps are at or near critical load. "
            "Consider cross-team escalation or temporary support to relieve pressure."
        )
        return

    st.caption(
        f"**{total_open} pending decision** · {total_resolved} already decided. "
        "Each suggestion = a peer with capacity + sector alpha to absorb load."
    )

    for group in suggestions_by_donor:
        donor = group["donor"]
        donor_tc = group["donor_tc"]
        st.markdown(f"**🔻 From {donor}** · {donor_tc} time-critical")
        for s in group["suggestions"]:
            d = s["deal"]
            opp_id = d["opportunity_id"]
            decision = redist_state.get(opp_id)
            to_rep = s["to_rep"]
            account = d["account"]
            product = d["product"]
            value = d["value"]
            rationale = s["rationale"]
            to_first = to_rep.split()[0] if to_rep else "peer"

            if decision == "approved":
                st.success(
                    f"✅ **Approved**: {account} ({product}, ${value:,.0f}) → 🔺 **{to_rep}** — _{rationale}_"
                )
                continue
            if decision == "rejected":
                st.warning(
                    f"❌ **Rejected**: {account} ({product}, ${value:,.0f}) → 🔺 **{to_rep}**"
                )
                continue

            with st.container(border=True):
                st.markdown(f"🔻 **{donor}** → 🔺 **{to_rep}**")
                st.markdown(f"**Deal:** {account} ({product}) — ${value:,.0f}")
                st.markdown(f"**Receiver:** 🟢 {rationale}")
                bcols = st.columns([2, 1, 3])
                with bcols[0]:
                    if st.button(f"✓ Approve transfer to {to_first}",
                                 key=f"approve_redist_{opp_id}", type="primary"):
                        actions.log_action(manager, actions.ACTION_REDISTRIBUTION_APPROVED, {
                            "opp_id": opp_id, "from": donor, "to": to_rep, "account": account,
                        })
                        st.rerun()
                with bcols[1]:
                    if st.button("✗ Reject",
                                 key=f"reject_redist_{opp_id}"):
                        actions.log_action(manager, actions.ACTION_REDISTRIBUTION_REJECTED, {
                            "opp_id": opp_id, "from": donor, "to": to_rep, "account": account,
                        })
                        st.rerun()
        st.markdown("")


def _render_systemic_patterns(patterns: list, manager: str):
    st.markdown("### 📊 Systemic patterns — cross-rep signals")
    decisions = actions.pattern_decisions(manager)

    # Counter for ack/escalate/dismiss today
    summary = actions.summary_today(manager)
    ack_n = summary.get("patterns_acknowledged", 0)
    esc_n = summary.get("patterns_escalated", 0)
    dis_n = summary.get("patterns_dismissed", 0)
    if ack_n or esc_n or dis_n:
        st.caption(
            f"✓ {ack_n} acknowledged · ⬆️ {esc_n} escalated · ✗ {dis_n} dismissed today. "
            "Patterns shrink as you respond."
        )

    pending = [p for p in patterns if p.get("category") not in decisions]
    if not pending and (ack_n or esc_n or dis_n):
        st.success("✅ All patterns addressed today.")
        return

    severity_emoji = {"high": "🚨", "medium": "⚠️", "low": "💡"}

    for p in pending:
        category = p.get("category", "unknown")
        title = category.replace("_", " ").title()
        emoji = severity_emoji.get(p.get("severity", "medium"), "💡")

        with st.container(border=True):
            st.markdown(f"{emoji} **{title}**")
            st.markdown(p["action"])

            bcols = st.columns([1.5, 1.3, 1.3, 4])
            with bcols[0]:
                if st.button("✓ Acknowledge", key=f"pattern_ack_{category}", type="primary"):
                    actions.log_action(manager, actions.ACTION_PATTERN_ACK, {
                        "category": category, "title": title,
                    })
                    st.rerun()
            with bcols[1]:
                escalate_open = f"pattern_escalate_open_{category}"
                if st.button("⬆️ Escalate", key=f"pattern_escalate_btn_{category}"):
                    st.session_state[escalate_open] = True
            with bcols[2]:
                dismiss_open = f"pattern_dismiss_open_{category}"
                if st.button("✗ Dismiss", key=f"pattern_dismiss_btn_{category}"):
                    st.session_state[dismiss_open] = True

            # Inline expansion for escalate/dismiss reason
            if st.session_state.get(escalate_open, False):
                note = st.text_input(
                    "Escalate to whom + context (required) — visible in audit log",
                    placeholder="e.g. Head of Sales — Q3 marketing inflow exceeding team capacity",
                    key=f"pattern_escalate_note_{category}",
                )
                if st.button("Confirm escalate", key=f"pattern_escalate_confirm_{category}"):
                    if note.strip():
                        actions.log_action(manager, actions.ACTION_PATTERN_ESCALATE, {
                            "category": category, "title": title, "note": note.strip(),
                        })
                        st.session_state[escalate_open] = False
                        st.rerun()
                    else:
                        st.warning("Required so the trail is meaningful.")

            if st.session_state.get(dismiss_open, False):
                note = st.text_input(
                    "Reason for dismissal (required) — feedback signal for the system",
                    placeholder="e.g. Q4 inflow normalization expected; not actionable this sprint",
                    key=f"pattern_dismiss_note_{category}",
                )
                if st.button("Confirm dismiss", key=f"pattern_dismiss_confirm_{category}"):
                    if note.strip():
                        actions.log_action(manager, actions.ACTION_PATTERN_DISMISS, {
                            "category": category, "title": title, "note": note.strip(),
                        })
                        st.session_state[dismiss_open] = False
                        st.rerun()
                    else:
                        st.warning("Required so the system learns what isn't actionable.")


def _render_how_scoring_works(stage_probs: dict):
    """Reference: scoring methodology — feature weights + stage close rates."""
    with st.expander("ℹ️ How scoring works"):
        st.markdown("**Feature weights** (sum to 100% when all features apply):")
        st.caption(
            "_Domain priors tuned by judgment, not statistical fit. Stage is the strongest signal "
            "(cohort close-rate baseline); freshness was calibrated in baseline-v3 once it became clear "
            "that deals >30d lose predictive value; `agent_winrate` was dropped in v2 because it leaked "
            "the label. Full reasoning in the README **process log**._"
        )
        st.table(pd.DataFrame([
            {"Feature": k, "Weight": f"{v['weight']:.0%}", "Rationale": v["desc"]}
            for k, v in FEATURE_DESCRIPTIONS.items()
        ]))
        st.markdown("**Stage close-rate (cohort-derived)**:")
        st.table(pd.DataFrame([
            {"Stage": s, "Close rate": f"{p:.0%}"} for s, p in stage_probs.items()
        ]))
        st.info(
            "ℹ️ **Dataset limitation — Prospecting and Engaging compute to the same rate.** "
            "Both formulas use `Won / (Won + Lost)` as numerator/denominator. In this dataset every closed "
            "deal has an `engage_date`, so the Engaging denominator equals the Prospecting denominator → "
            "identical rates. A production CRM with **stage-transition history** would let us compute "
            "*\"% of deals that REACHED Engaging and won\"* separately — typically ~30% / ~55% / ... — "
            "but that data doesn't exist here. Honest disclosure beats fake differentiation."
        )


def _render_json_export(payload: dict, kind: str, name: str):
    """Composable JSON export — schema versioned for downstream agents."""
    payload_str = json.dumps(payload, indent=2, default=str, ensure_ascii=False)
    cols = st.columns([3, 1])
    with cols[0]:
        if kind == "manager":
            st.markdown(
                "**🔌 Manager brief as JSON** — composable contract for downstream agents "
                "(manager-morning-brief skill, Slack/email digest, manager cockpit)."
            )
            file_name = f"manager_brief_{name.replace(' ', '_').lower()}.json"
        else:
            st.markdown(
                "**🔌 Brief as JSON** — composable contract for downstream agents "
                "(e.g. WhatsApp/Slack morning-brief skill, voice copilot, weekly retro generator)."
            )
            file_name = f"brief_{name.replace(' ', '_').lower()}.json"
    with cols[1]:
        st.download_button(
            "Download brief (JSON)",
            data=payload_str,
            file_name=file_name,
            mime="application/json",
            use_container_width=True,
            key=f"json_download_{kind}_{name}",
        )
    with st.expander("Preview JSON schema", expanded=False):
        st.code(payload_str, language="json")


def _render_audit_log(actor: str, role_label: str = "manager"):
    """Render audit log for `actor` (manager OR rep)."""
    today_actions = actions.load_actions(actor)
    summary = actions.summary_today(actor)
    n_total = len(today_actions)

    # Header tailored to role — coaching/redistribution are manager-only signals
    header_parts = [
        f"🧾 Audit log — {n_total} action(s) today",
        f"✓ {summary['done']} done",
        f"⏰ {summary['defer']} deferred",
        f"✗ {summary['skip']} skipped",
    ]
    if role_label == "manager":
        rd_total = summary["redistribution_approved"] + summary["redistribution_rejected"]
        header_parts.extend([
            f"📝 {summary['coaching_notes_sent']} notes sent",
            f"🔄 {summary['redistribution_approved']}/{rd_total} redistribution approved",
        ])
    header = f"{header_parts[0]} ({' · '.join(header_parts[1:])})"

    with st.expander(header, expanded=False):
        if not today_actions:
            empty_msg = (
                "_No actions logged today yet. Take action on must-acts, send coaching notes, "
                "or approve redistribution to populate._"
                if role_label == "manager"
                else "_No actions logged today yet. Mark a must-act as done, defer, or skip to populate._"
            )
            st.caption(empty_msg)
            return
        rows = []
        for a in today_actions[-50:]:
            ts = a.get("ts", "").replace("T", " ")[:19]
            type_label = a.get("type", "?").replace("_", " ").title()
            target = a.get("opp_id") or a.get("rep") or "—"
            note = a.get("note") or a.get("from", "")
            if a.get("type", "").startswith("redistribution"):
                note = f"{a.get('from', '?')} → {a.get('to', '?')} · {a.get('account', '')}"
            rows.append({"Time": ts, "Action": type_label, "Target": target, "Detail": (note[:120] + "…") if isinstance(note, str) and len(note) > 120 else note})
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True, hide_index=True,
            height=38 + 35 * len(rows) + 4,
            column_config={
                "Time": st.column_config.TextColumn(width="small"),
                "Action": st.column_config.TextColumn(width="medium"),
                "Target": st.column_config.TextColumn(width="medium"),
                "Detail": st.column_config.TextColumn(width="large"),
            },
        )
        st.download_button(
            "Export today's audit (JSON)",
            data=json.dumps(today_actions, indent=2, default=str),
            file_name=f"audit_{role_label}_{actor.replace(' ', '_').lower()}_today.json",
            mime="application/json",
            key=f"audit_download_{role_label}_{actor}",
        )


def _render_team_coaching(team_coach: dict):
    with st.expander("📈 Team coaching — where this team has leverage, where it bleeds", expanded=True):
        overall = team_coach.get("overall", {})
        if not overall:
            st.caption("_Not enough closed-deal history for this team._")
            return
        c1, c2 = st.columns(2)
        delta = overall["delta_pp"]
        c1.metric(
            "Team close rate",
            f"{overall['team_wr']*100:.0f}%",
            delta=f"{delta:+.0f}pp vs company",
            help=f"Based on {overall['n']:,} closed deals across {overall['n_reps']} reps.",
        )
        if team_coach.get("rep_load_imbalance"):
            imb = team_coach["rep_load_imbalance"]
            ratio_str = f"{imb['ratio']:.1f}×" if imb.get("ratio") else "n/a"
            c2.metric(
                "Pipeline load spread",
                ratio_str,
                help=f"{imb['top_rep']} (top) vs {imb['bottom_rep']} (bottom).",
            )
            if imb.get("ratio") and imb["ratio"] >= 2.0:
                st.caption(
                    f"_{imb['top_rep']} carries {imb['ratio']:.1f}× the open-deal load of {imb['bottom_rep']}. "
                    "≥2× usually warrants redistribution — see **🔄 Redistribution suggestions** in the Brief tab._"
                )

        impact_help = (
            "Impact ≈ extra deals/year above (alpha) or below (bleed) the company benchmark, "
            "given this team's sample size in the slice. Computed as n × |Δ|. "
            "Higher impact = bigger lever for coaching / redistribution priorities."
        )

        left, right = st.columns(2)
        with left:
            st.markdown("**🟢 Team alpha (sectors/products)**")
            rows = []
            for s in team_coach.get("sector_alpha", []):
                impact = round(int(s["n_total"]) * abs(s["delta_pp"]) / 100)
                rows.append({"Segment": f"Sector · {s['label']}",
                             "Team win": f"{s['team_wr']*100:.0f}%",
                             "Company": f"{s['company_wr']*100:.0f}%",
                             "Δ": f"+{s['delta_pp']:.0f}pp",
                             "n": int(s["n_total"]),
                             "Impact": impact})
            for p in team_coach.get("product_alpha", []):
                impact = round(int(p["n_total"]) * abs(p["delta_pp"]) / 100)
                rows.append({"Segment": f"Product · {p['label']}",
                             "Team win": f"{p['team_wr']*100:.0f}%",
                             "Company": f"{p['company_wr']*100:.0f}%",
                             "Δ": f"+{p['delta_pp']:.0f}pp",
                             "n": int(p["n_total"]),
                             "Impact": impact})
            rows.sort(key=lambda r: r["Impact"], reverse=True)
            if rows:
                st.dataframe(
                    pd.DataFrame(rows), use_container_width=True, hide_index=True,
                    column_config={
                        "Δ": st.column_config.TextColumn(
                            help="Team win rate minus company average in this slice, in percentage points (pp). Positive = team performs above company avg. 'n' is sample size of closed deals in this slice.",
                        ),
                        "Impact": st.column_config.NumberColumn(help=impact_help),
                    },
                )
            else:
                st.caption("_No team-level alpha vs company average._")
        with right:
            st.markdown("**🔴 Team bleed**")
            rows = []
            for s in team_coach.get("sector_bleed", []):
                impact = round(int(s["n_total"]) * abs(s["delta_pp"]) / 100)
                rows.append({"Segment": f"Sector · {s['label']}",
                             "Team win": f"{s['team_wr']*100:.0f}%",
                             "Company": f"{s['company_wr']*100:.0f}%",
                             "Δ": f"{s['delta_pp']:.0f}pp",
                             "n": int(s["n_total"]),
                             "Impact": impact})
            for p in team_coach.get("product_bleed", []):
                impact = round(int(p["n_total"]) * abs(p["delta_pp"]) / 100)
                rows.append({"Segment": f"Product · {p['label']}",
                             "Team win": f"{p['team_wr']*100:.0f}%",
                             "Company": f"{p['company_wr']*100:.0f}%",
                             "Δ": f"{p['delta_pp']:.0f}pp",
                             "n": int(p["n_total"]),
                             "Impact": impact})
            rows.sort(key=lambda r: r["Impact"], reverse=True)
            if rows:
                st.dataframe(
                    pd.DataFrame(rows), use_container_width=True, hide_index=True,
                    column_config={
                        "Δ": st.column_config.TextColumn(
                            help="Team win rate minus company average in this slice, in percentage points (pp). Negative = team performs below company avg. 'n' is sample size of closed deals in this slice.",
                        ),
                        "Impact": st.column_config.NumberColumn(help=impact_help),
                    },
                )
            else:
                st.caption("_No team-level bleed vs company average._")

        st.caption(
            "**How to use this:** alpha segments are redistribution receivers (peers strong here can absorb "
            "struggling deals from this team) — see **🔄 Redistribution** in Brief tab. Bleed segments are "
            "coaching priorities for next 1:1s — work the highest-Impact rows first, not the highest-Δ ones."
        )


def render_manager_leaderboard_drilldown(active: pd.DataFrame, ghost: pd.DataFrame, orphan: pd.DataFrame, close_window: int, scored: pd.DataFrame):
    """The old manager view — kept as drilldown for ad-hoc inspection across all teams."""
    must_acts = compute_must_acts(active, close_window)
    if must_acts.empty:
        st.info("No must-acts globally — no leaderboard to render.")
        return

    # Original subheader removed
    st.caption(
        f"Of {len(active) + len(ghost) + len(orphan):,} open opportunities, "
        f"**{len(active):,} are actionable** today. "
        f"{len(ghost):,} are pipeline ghosts (>3× the {close_window}d median cycle). "
        f"{len(orphan):,} are orphans (no account record — need CRM cleanup before any action)."
    )

    must_acts = compute_must_acts(active, close_window)
    must_acts = apply_judge_actions(must_acts, scored, close_window)
    if must_acts.empty:
        st.success(
            "No must-acts today across the team. Good day for prospecting "
            "or CRM cleanup — no high-quality deals near closure, no Engaging "
            "deals at ghost threshold."
        )
        return

    judged_count = int(must_acts["is_judged"].sum())
    if judged_count:
        st.caption(
            f"✨ {judged_count}/{len(must_acts)} actions are LLM-judged contextual recommendations "
            f"(cite specific facts about the deal). The remaining {len(must_acts)-judged_count} "
            f"fall back to the rule-based template."
        )
    else:
        st.caption(
            "⚠️ LLM-judged actions not cached. Run `python generate_judge_cache.py` to populate. "
            "Showing rule-based template actions."
        )

    n_must = len(must_acts)
    reps_high = must_acts[must_acts["must_act_reason"].isin(["high_score", "both"])]["sales_agent"].nunique()
    reps_tc = must_acts[must_acts["must_act_reason"].isin(["time_critical", "both"])]["sales_agent"].nunique()
    total_value = must_acts["expected_value"].sum()
    prob_weighted = (must_acts["close_probability"] * must_acts["expected_value"]).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Must-acts today", f"{n_must:,}")
    c2.metric(
        "Reps engaged",
        f"{must_acts['sales_agent'].nunique()}/{active['sales_agent'].nunique()}",
        help=f"⭐ {reps_high} with high-score work · 🔥 {reps_tc} with time-critical deals",
    )
    c3.metric("Combined value", fmt_money(total_value))
    c4.metric("Prob-weighted $", fmt_money(prob_weighted))

    st.divider()
    st.markdown("### Rep leaderboard — where attention should land today")

    by_rep = (
        must_acts.assign(
            high_count=must_acts["must_act_reason"].isin(["high_score", "both"]).astype(int),
            tc_count=must_acts["must_act_reason"].isin(["time_critical", "both"]).astype(int),
        )
        .groupby(["sales_agent", "manager", "regional_office"])
        .agg(
            must_act_count=("opportunity_id", "count"),
            high_count=("high_count", "sum"),
            tc_count=("tc_count", "sum"),
            pipeline_value=("expected_value", "sum"),
            avg_score=("score", "mean"),
        )
        .reset_index()
        .sort_values(["tc_count", "high_count", "avg_score"], ascending=[False, False, False])
    )

    def tc_urgency(n: int) -> str:
        # More time-critical = WORSE. Red = danger.
        if n >= 2:
            return f"🔴 act now ({n})"
        if n == 1:
            return f"🟡 watch ({n})"
        return "🟢 quiet (0)"

    def hs_urgency(n: int) -> str:
        # More high-score = BETTER. Green = loaded with quality.
        if n >= 2:
            return f"🟢 loaded ({n})"
        if n == 1:
            return f"🟡 ok ({n})"
        return "⚪ none (0)"

    leaderboard = pd.DataFrame({
        "Rep": by_rep["sales_agent"],
        "Manager": by_rep["manager"],
        "Region": by_rep["regional_office"],
        "Must-acts": by_rep["must_act_count"].astype(int),
        "🔥 Time-critical": by_rep["tc_count"].apply(tc_urgency),
        "⭐ High-score": by_rep["high_count"].apply(hs_urgency),
        "Avg score": by_rep["avg_score"].round(0).astype(int),
        "Pipeline value": by_rep["pipeline_value"].apply(fmt_money),
    })
    st.dataframe(leaderboard, use_container_width=True, hide_index=True, height=420)
    st.caption(
        "**🔴 act now** = ≥2 deals about to flip ghost — your attention needed. "
        "**🟢 loaded** = ≥2 high-quality deals primed to close — celebrate, don't panic. "
        "Sort: time-critical first (danger), then high-score, then avg score."
    )

    st.divider()
    st.markdown(f"### Top {MUST_ACT_TEAM_PREVIEW} must-acts globally")
    # Sort by priority (time_critical > high_score) then score for the global preview
    priority = {"both": 0, "time_critical": 1, "high_score": 2}
    top = must_acts.assign(_p=must_acts["must_act_reason"].map(priority)) \
                   .sort_values(["_p", "score"], ascending=[True, False]) \
                   .head(MUST_ACT_TEAM_PREVIEW)
    preview = pd.DataFrame({
        "Type": top["must_act_reason"].apply(reason_badge),
        "Score": top["score"].round(0).astype(int),
        "Stage": top["deal_stage"],
        "Account": top["account"],
        "Product": top["product"],
        "Rep": top["sales_agent"],
        "Days": top["days_in_pipeline"].round(0).astype("Int64"),
        "Expected $": top["expected_value"].apply(fmt_money),
        "Recommended action": top.apply(
            lambda r: ("✨ " if r["is_judged"] else "") + r["action"], axis=1
        ),
    })
    st.dataframe(
        preview, use_container_width=True, hide_index=True, height=420,
        column_config={
            "Type": st.column_config.TextColumn(
                width="small",
                help="🔥 time-critical · ⭐ high-score · 🔥⭐ both",
            ),
            "Score": st.column_config.NumberColumn(width="small"),
            "Stage": st.column_config.TextColumn(width="small"),
            "Account": st.column_config.TextColumn(width="small"),
            "Product": st.column_config.TextColumn(width="small"),
            "Rep": st.column_config.TextColumn(width="small"),
            "Days": st.column_config.NumberColumn(width="small"),
            "Expected $": st.column_config.TextColumn(width="small"),
            "Recommended action": st.column_config.TextColumn(
                width="large",
                help="Recommended next step for the deal owner. ✨ prefix = LLM-judged (cites deal-specific facts) vs rule-based template.",
            ),
        },
    )
    st.caption(
        "**🔥** = time-critical (Engaging deal near ghost threshold — act now). "
        "**⭐** = high-score (above quality floor). **🔥⭐** = both. "
        "**✨** = LLM-judged contextual action (cites deal-specific facts) vs rule-based template."
    )


# ---------- Rep mode ----------

def build_manager_brief_json(
    *,
    manager: str,
    ref_date: pd.Timestamp,
    mgr_must_acts: pd.DataFrame,
    type_3_actions: list,
    critical_reps: list,
    systemic_patterns: list,
    team_coaching: dict,
    pipeline_health: dict,
    close_window: int,
) -> dict:
    """Composable schema — what a downstream manager-morning-brief skill consumes.

    Mirrors the Rep mode JSON shape but at higher altitude: must_acts are
    manager-level moves (Type 1 + Type 2), system_decisions are Type 3,
    plus critical reps with embedded playbooks, systemic patterns,
    and team-level coaching.
    """
    ghost_threshold = close_window * 3

    def must_act_payload(deal: pd.Series) -> dict:
        return {
            "opportunity_id": deal["opportunity_id"],
            "type": deal["manager_action_type"],  # type_1_closer | type_2_intervention
            "account": _none_if_nan(deal.get("account")),
            "sector": _none_if_nan(deal.get("sector")),
            "product": deal["product"],
            "stage": deal["deal_stage"],
            "days_in_pipeline": _none_if_nan(deal.get("days_in_pipeline")),
            "expected_value_usd": round(float(deal["expected_value"]), 2),
            "close_probability": round(float(deal["close_probability"]), 3),
            "rep": deal["sales_agent"],
            "action": deal["action"],
            "action_source": "llm_judge" if deal.get("is_judged", False) else "rule_template",
            "rationale": deal.get("manager_action_rationale", ""),
            "days_to_ghost_flip": int(ghost_threshold - deal["days_in_pipeline"]) if pd.notna(deal.get("days_in_pipeline")) else None,
        }

    return {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "as_of_data": ref_date.strftime("%Y-%m-%d"),
        "manager": manager,
        "pipeline_health": pipeline_health,
        "must_acts": [must_act_payload(d) for _, d in mgr_must_acts.iterrows()] if not mgr_must_acts.empty else [],
        "system_decisions": [
            {
                "category": t3.get("category"),
                "label": t3["label"],
                "affects_rep": t3.get("rep"),
                "deal_count": t3.get("deal_count", 0),
            }
            for t3 in type_3_actions[:5]
        ],
        "critical_reps": critical_reps,
        "systemic_patterns": systemic_patterns,
        "team_coaching": team_coaching,
        "downstream_hints": {
            "primary_skill": "manager-morning-brief",
            "delivery_channels_suggested": ["slack", "email", "manager-cockpit"],
            "use_pattern": (
                "Render must_acts as bounded daily focus for the manager (≤5). "
                "system_decisions are non-deal actions (triage, redistribute). "
                "critical_reps embeds per-rep playbooks. systemic_patterns surface "
                "cross-rep issues for upstream review. team_coaching powers weekly retros."
            ),
        },
    }


def _rep_sector_signal_for_call_prep(rep_coach: dict, sector) -> str:
    """Format rep's signal in a specific sector for the call-prep prompt context."""
    if not sector or pd.isna(sector) or not rep_coach:
        return "neutral"
    for a in rep_coach.get("sector_alpha", []):
        if a["label"] == sector:
            return f"+{a['delta_pp']:.0f}pp alpha (rep is strong here)"
    for b in rep_coach.get("sector_bleed", []):
        if b["label"] == sector:
            return f"{b['delta_pp']:.0f}pp bleed (rep struggles here)"
    return "neutral"


def _none_if_nan(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def build_brief_json(
    *,
    rep: str,
    manager: str | None,
    region: str | None,
    ref_date: pd.Timestamp,
    rep_must: pd.DataFrame,
    rep_stay_close: pd.DataFrame,
    rep_ghost: pd.DataFrame,
    rep_orphan: pd.DataFrame,
    coaching_signals: dict,
    close_window: int,
) -> dict:
    """Composable schema — what a downstream Morning-Brief skill would consume.

    Stable contract: any field's absence is meaningful (rep has no signal there).
    Versioned via `schema_version` so consumers can adapt.
    """
    ghost_threshold = close_window * 3

    def deal_payload(deal: pd.Series, include_judge_meta: bool = True) -> dict:
        d = {
            "opportunity_id": deal["opportunity_id"],
            "account": _none_if_nan(deal.get("account")),
            "sector": _none_if_nan(deal.get("sector")),
            "product": deal["product"],
            "stage": deal["deal_stage"],
            "days_in_pipeline": _none_if_nan(deal.get("days_in_pipeline")),
            "score": round(float(deal["score"]), 1),
            "close_probability": round(float(deal["close_probability"]), 3),
            "expected_value_usd": round(float(deal["expected_value"]), 2),
            "action": deal["action"],
        }
        if include_judge_meta:
            d["must_act_reason"] = deal.get("must_act_reason")
            d["action_source"] = "llm_judge" if deal.get("is_judged", False) else "rule_template"
            if pd.notna(deal.get("days_in_pipeline")):
                d["days_to_ghost_flip"] = int(ghost_threshold - deal["days_in_pipeline"])
        return d

    return {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "as_of_data": ref_date.strftime("%Y-%m-%d"),
        "rep": rep,
        "manager": manager,
        "region": region,
        "pipeline_health": {
            "ghost_threshold_days": ghost_threshold,
            "ghost_count": int(len(rep_ghost)),
            "orphan_count": int(len(rep_orphan)),
            "active_count": int(len(rep_must) + len(rep_stay_close)),
        },
        "must_acts": [deal_payload(d) for _, d in rep_must.iterrows()],
        "stay_close": [deal_payload(d, include_judge_meta=False) for _, d in rep_stay_close.iterrows()],
        "coaching_signals": coaching_signals,
        "downstream_hints": {
            "primary_skill": "morning-brief",
            "delivery_channels_suggested": ["whatsapp", "slack", "email"],
            "use_pattern": (
                "Render must_acts as bounded daily focus (≤5 items). Each item has its own action. "
                "coaching_signals power weekly retro narrative."
            ),
        },
    }


def render_coaching_panel(rep: str, scored: pd.DataFrame):
    """Where this rep has leverage, where they bleed. Pure data, no LLM."""
    with st.expander("📊 Coaching — where you have leverage, where you bleed", expanded=True):
        signals = rep_alpha_signals(rep, scored)
        overall = signals.get("overall", {})
        if not overall:
            st.caption(f"_Not enough closed-deal history for {rep} to surface coaching signals._")
            return

        c1, c2, c3 = st.columns(3)
        delta = overall["delta_pp"]
        delta_str = f"{delta:+.0f}pp vs team"
        c1.metric(
            "Your overall close rate",
            f"{overall['rep_wr']*100:.0f}%",
            delta=delta_str,
            help=f"Based on {overall['n']:,} closed deals. Team average: {overall['team_wr']*100:.0f}%.",
        )
        cs = signals.get("closing_speed")
        if cs:
            c2.metric(
                "Median days to close",
                f"{cs['rep_median_days']}d",
                delta=f"{cs['delta']:+d}d vs team",
                delta_color="inverse",
                help=f"Team median: {cs['team_median_days']}d. Negative = faster than team.",
            )
        tv = signals.get("temporal_verdict")
        if tv:
            c3.info(tv)
        else:
            c3.empty()

        rep_impact_help = (
            "Impact ≈ extra deals/year above (alpha) or below (bleed) the team average, given your sample "
            "size in the slice. Computed as n × |Δ|. Higher Impact = bigger lever for where to focus your 1:1."
        )

        # Sector / product alpha + bleed
        left, right = st.columns(2)
        with left:
            st.markdown("**🟢 Where you have alpha**")
            rows = []
            for s in signals.get("sector_alpha", []):
                impact = round(int(s["n_total"]) * abs(s["delta_pp"]) / 100)
                rows.append({
                    "Segment": f"Sector · {s['label']}",
                    "Your win": f"{s['rep_wr']*100:.0f}%",
                    "Team": f"{s['team_wr']*100:.0f}%",
                    "Δ": f"+{s['delta_pp']:.0f}pp",
                    "n": int(s["n_total"]),
                    "Impact": impact,
                })
            for p in signals.get("product_alpha", []):
                impact = round(int(p["n_total"]) * abs(p["delta_pp"]) / 100)
                rows.append({
                    "Segment": f"Product · {p['label']}",
                    "Your win": f"{p['rep_wr']*100:.0f}%",
                    "Team": f"{p['team_wr']*100:.0f}%",
                    "Δ": f"+{p['delta_pp']:.0f}pp",
                    "n": int(p["n_total"]),
                    "Impact": impact,
                })
            rows.sort(key=lambda r: r["Impact"], reverse=True)
            if rows:
                st.dataframe(
                    pd.DataFrame(rows), use_container_width=True, hide_index=True,
                    column_config={
                        "Δ": st.column_config.TextColumn(
                            help="Your win rate minus team average in this slice, in percentage points (pp). Positive = you perform above the team. 'n' is sample size of closed deals in this slice.",
                        ),
                        "Impact": st.column_config.NumberColumn(help=rep_impact_help),
                    },
                )
                st.caption("Prioritize deals matching these slices — your hit rate is meaningfully above the team's.")
            else:
                st.caption("_No sector/product slices where you outperform by ≥10pp with sample ≥5._")

        with right:
            st.markdown("**🔴 Where you bleed**")
            rows = []
            for s in signals.get("sector_bleed", []):
                impact = round(int(s["n_total"]) * abs(s["delta_pp"]) / 100)
                rows.append({
                    "Segment": f"Sector · {s['label']}",
                    "Your win": f"{s['rep_wr']*100:.0f}%",
                    "Team": f"{s['team_wr']*100:.0f}%",
                    "Δ": f"{s['delta_pp']:.0f}pp",
                    "n": int(s["n_total"]),
                    "Impact": impact,
                })
            for p in signals.get("product_bleed", []):
                impact = round(int(p["n_total"]) * abs(p["delta_pp"]) / 100)
                rows.append({
                    "Segment": f"Product · {p['label']}",
                    "Your win": f"{p['rep_wr']*100:.0f}%",
                    "Team": f"{p['team_wr']*100:.0f}%",
                    "Δ": f"{p['delta_pp']:.0f}pp",
                    "n": int(p["n_total"]),
                    "Impact": impact,
                })
            rows.sort(key=lambda r: r["Impact"], reverse=True)
            if rows:
                st.dataframe(
                    pd.DataFrame(rows), use_container_width=True, hide_index=True,
                    column_config={
                        "Δ": st.column_config.TextColumn(
                            help="Your win rate minus team average in this slice, in percentage points (pp). Negative = you perform below the team. 'n' is sample size of closed deals in this slice.",
                        ),
                        "Impact": st.column_config.NumberColumn(help=rep_impact_help),
                    },
                )
                st.caption("Consider co-selling, asking for help, or deprioritizing deals in these slices.")
            else:
                st.caption("_No sector/product slices where you underperform by ≥10pp with sample ≥5._")

        # Temporal breakdown
        temporal = signals.get("temporal", {})
        if temporal:
            st.markdown("**⏱ Cycle-length win rate**")
            tdf = pd.DataFrame([
                {"Cycle bucket": k, "Your win rate": f"{v['wr']*100:.0f}%", "Sample": int(v["n"])}
                for k, v in temporal.items()
            ])
            st.dataframe(tdf, use_container_width=True, hide_index=True)


def render_rep_mode(active: pd.DataFrame, ghost: pd.DataFrame, orphan: pd.DataFrame, close_window: int, scored: pd.DataFrame, stage_probs: dict, rep: str | None = None):
    # `rep` is selected in the sidebar (main()) and passed in.
    if rep is None:
        st.warning("No rep selected.")
        return

    rep_active = active[active["sales_agent"] == rep].sort_values("score", ascending=False)
    rep_ghost = ghost[ghost["sales_agent"] == rep]
    rep_orphan = orphan[orphan["sales_agent"] == rep]
    if rep_active.empty:
        st.warning(f"No active deals for {rep}.")
        return

    manager = rep_active["manager"].iloc[0]
    region = rep_active["regional_office"].iloc[0]

    st.subheader(f"{rep} — today's brief")
    st.caption(f"Manager: **{manager}** · Region: **{region}**")

    # Compute must-acts via the shared logic (so single-rep slice respects floor + temporal)
    rep_must = compute_must_acts(rep_active, close_window)
    rep_must = apply_judge_actions(rep_must, scored, close_window)

    # ---- Apply rep action layer: filter out must-acts already acted on today
    rep_acted = actions.acted_opp_ids(rep)
    if rep_acted and not rep_must.empty:
        rep_must = rep_must[~rep_must["opportunity_id"].isin(rep_acted)]
    rep_summary = actions.summary_today(rep)

    must_ids = set(rep_must["opportunity_id"])
    remaining = rep_active[~rep_active["opportunity_id"].isin(must_ids)]
    stay_close = remaining.head(7)
    rest_active = remaining.iloc[7:]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "🎯 Must-act today", f"{len(rep_must)}",
        help=f"Bounded at {MUST_ACT_MAX_PER_REP}. Combines high-score (score ≥ {MUST_ACT_SCORE_FLOOR}) with time-critical (Engaging deals in final 8% of window before ghost flip).",
    )
    c2.metric(
        "👀 Stay close (this week)", f"{len(stay_close)}",
        help="Top 7 non-must-act open deals for this rep. Watch these — don't let them cool further.",
    )
    c3.metric(
        "🧊 Ghost (deprioritized)", f"{len(rep_ghost)}",
        help=f"Deals open >3× the median Won sales cycle ({close_window}d). Treated as dead pipeline — listed separately for CRM cleanup, excluded from today's brief.",
    )
    c4.metric("🚨 Orphan (CRM cleanup)", f"{len(rep_orphan)}",
              help="Open deals with no account record. Can't be acted on until linked to a company.")

    st.caption(
        "**📋 Brief** = what to act on today · **📊 Dashboard** = how you're performing"
    )

    tab_brief, tab_dash = st.tabs(["📋 Today's brief", "📊 Performance dashboard"])

    with tab_brief:
        _render_rep_brief_tab(
            rep=rep, manager=manager, rep_must=rep_must, rep_active=rep_active,
            rep_ghost=rep_ghost, rep_orphan=rep_orphan, stay_close=stay_close,
            rest_active=rest_active, rep_summary=rep_summary, scored=scored, close_window=close_window,
        )

    with tab_dash:
        _render_benchmark(benchmark_for_rep(rep, scored), scope="rep")
        st.divider()
        render_coaching_panel(rep, scored)
        st.divider()
        render_pipeline_drilldown(scored, scope={"kind": "rep", "name": rep} if rep else None)
        st.divider()
        _render_how_scoring_works(stage_probs)
        st.divider()
        ref_for_json = scored["close_date"].max() if scored["close_date"].notna().any() else pd.Timestamp(datetime.today().date())
        rep_brief_payload = build_brief_json(
            rep=rep, manager=manager, region=region, ref_date=ref_for_json,
            rep_must=rep_must, rep_stay_close=stay_close, rep_ghost=rep_ghost, rep_orphan=rep_orphan,
            coaching_signals=rep_alpha_signals(rep, scored), close_window=close_window,
        )
        _render_json_export(rep_brief_payload, kind="rep", name=rep)


def _render_rep_brief_tab(
    *, rep: str, manager: str, rep_must: pd.DataFrame, rep_active: pd.DataFrame,
    rep_ghost: pd.DataFrame, rep_orphan: pd.DataFrame, stay_close: pd.DataFrame,
    rest_active: pd.DataFrame, rep_summary: dict, scored: pd.DataFrame, close_window: int,
):
    if rep_must.empty:
        st.success(
            f"**No must-acts for {rep} today.** "
            f"No deals above the quality floor (score ≥ {MUST_ACT_SCORE_FLOOR}) and "
            f"no Engaging deals near the ghost threshold ({int(close_window*3*GHOST_WARN_RATIO)}d–{close_window*3}d). "
            "Good day for prospecting, qualifying lower-tier deals, or CRM cleanup."
        )
    else:
        st.markdown("### 🎯 Today")

        # Action counter — brief shrinks as rep acts
        if rep_summary["done"] or rep_summary["defer"] or rep_summary["skip"]:
            st.caption(
                f"✓ {rep_summary['done']} done · ⏰ {rep_summary['defer']} deferred · "
                f"✗ {rep_summary['skip']} skipped today. Brief shrinks as you act."
            )

        legend_parts = [
            "🔥 time-critical",
            "⭐ high-score",
            "🔥⭐ both",
        ]
        judged_count = int(rep_must["is_judged"].sum()) if "is_judged" in rep_must.columns else 0
        st.caption(
            f"Bounded list — up to {MUST_ACT_MAX_PER_REP}, currently **{len(rep_must)}**. "
            + " · ".join(legend_parts)
        )
        if not rep_must.empty:
            fallback = len(rep_must) - judged_count
            st.caption(
                f"**✨ = LLM-judged action** (cites deal-specific facts from account/sector/rep history). "
                f"**{judged_count}/{len(rep_must)} here use LLM**; {fallback} fell back to rule-based template "
                "(LLM output failed validation or not cached — graceful fallback)."
            )

        ghost_threshold = close_window * 3
        rows = []
        for _, deal in rep_must.iterrows():
            account = deal["account"] if pd.notna(deal["account"]) else "(unmapped)"
            judged_mark = " ✨" if deal.get("is_judged") else ""
            context_parts = [
                deal["deal_stage"],
                f"{deal['days_in_pipeline']:.0f}d",
                fmt_money(deal["expected_value"]),
                f"close {deal['close_probability']*100:.0f}%",
            ]
            if deal["must_act_reason"] in ("time_critical", "both"):
                days_left = int(ghost_threshold - deal["days_in_pipeline"])
                context_parts.append(f"⏰ {days_left}d to ghost")
            rows.append({
                "Type": reason_badge(deal["must_act_reason"]),
                "Deal": f"{account} — {deal['product']}{judged_mark}",
                "Score": int(round(deal["score"])),
                "Context": " · ".join(context_parts),
                "Action": deal["action"],
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
            height=38 + 35 * len(rows) + 4,
            column_config={
                "Type": st.column_config.TextColumn(
                    width="small",
                    help="🔥 time-critical (Engaging near ghost flip) · ⭐ high-score (above quality floor) · 🔥⭐ both",
                ),
                "Deal": st.column_config.TextColumn(width="medium"),
                "Score": st.column_config.NumberColumn(
                    width="small",
                    help="Weighted combination of stage close-rate, freshness, account size, deal value, product win rate, and sector win rate. See 'How scoring works' in the Dashboard tab. Close prob in Context is the cohort close rate for the deal's stage.",
                ),
                "Context": st.column_config.TextColumn(width="small"),
                "Action": st.column_config.TextColumn(
                    width="large",
                    help="Recommended next step. **✨ in the Deal cell** = LLM-judged: action text generated by Claude reading the deal's full context (account, sector, days remaining, your historical close rate, sector alpha/bleed, other open deals at account). Without ✨ = rule-based template fallback (used when LLM output failed validation or isn't cached).",
                ),
            },
        )

        # ---- Call Prep: generate dossier for a deal before the call
        with st.expander("🎤 Generate call prep for a must-act", expanded=False):
            cp_opp_options = {
                f"{d['account'] if pd.notna(d.get('account')) else '(unmapped)'} — {d['product']}": d["opportunity_id"]
                for _, d in rep_must.iterrows()
            }
            if cp_opp_options:
                cp_selected = st.selectbox(
                    "Pick deal for prep",
                    list(cp_opp_options.keys()),
                    key=f"call_prep_select_{rep}",
                )
                cp_opp_id = cp_opp_options[cp_selected]
                cp_regen_key = f"cp_regen_{rep}_{cp_opp_id}"
                if cp_regen_key not in st.session_state:
                    st.session_state[cp_regen_key] = 0
                cp_regen_count = st.session_state[cp_regen_key]

                bcols = st.columns([1, 1, 4])
                with bcols[0]:
                    generate_clicked = st.button(
                        "🎤 Generate" if cp_regen_count == 0 else "🎤 Generate fresh",
                        key=f"call_prep_gen_{rep}_{cp_opp_id}",
                        type="primary",
                    )
                with bcols[1]:
                    if cp_regen_count > 0 and st.button("↻ Regenerate", key=f"call_prep_regen_{rep}_{cp_opp_id}"):
                        st.session_state[cp_regen_key] += 1
                        st.rerun()

                cp_state_key = f"cp_dossier_{rep}_{cp_opp_id}_{cp_regen_count}"
                if generate_clicked and cp_state_key not in st.session_state:
                    deal_row = rep_must[rep_must["opportunity_id"] == cp_opp_id].iloc[0]
                    rep_coach_local = rep_alpha_signals(rep, scored)
                    ghost_threshold = close_window * 3
                    ctx = build_judge_context(deal_row, scored, ghost_threshold)
                    # Override rep-side ctx fields needed for the call prep prompt
                    ctx_for_cp = {
                        "account": ctx.get("account"),
                        "sector": ctx.get("sector"),
                        "account_revenue": float(deal_row["revenue"]) if pd.notna(deal_row.get("revenue")) else None,
                        "rep_close_rate_pct": round(rep_coach_local.get("overall", {}).get("rep_wr", 0.5) * 100),
                        "rep_sector_signal": _rep_sector_signal_for_call_prep(rep_coach_local, deal_row.get("sector")),
                        "other_open": ctx.get("other_open"),
                        "days_remaining": ctx.get("days_remaining"),
                    }
                    use_cache = (cp_regen_count == 0)
                    with st.spinner("Generating call prep dossier..."):
                        dossier = judge_call_prep(deal_row, ctx_for_cp, rep, use_cache=use_cache)
                    st.session_state[cp_state_key] = dossier or "_LLM failed to generate dossier. Try Regenerate._"

                if cp_state_key in st.session_state:
                    dossier_text = st.session_state[cp_state_key]
                    with st.container(border=True):
                        st.markdown(f"### 📋 Call prep — {cp_selected}")
                        if cp_regen_count > 0:
                            st.caption(f"↻ Regenerated {cp_regen_count}× (cache bypassed) · paste into your CRM notes or send to yourself before the call.")
                        else:
                            st.caption("Generated from cache · paste into your CRM notes or send to yourself before the call.")
                        st.markdown(dossier_text)
                        safe_slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in cp_selected.lower())[:60].strip("-")
                        st.download_button(
                            "📥 Download as Markdown",
                            data=f"# Call prep — {cp_selected}\n\n_Rep: {rep}_\n\n{dossier_text}\n",
                            file_name=f"call-prep-{safe_slug}.md",
                            mime="text/markdown",
                            key=f"cp_download_{rep}_{cp_opp_id}_{cp_regen_count}",
                        )

        # ---- Action toolbar: rep logs a decision on one must-act
        with st.expander("🎬 Take action on a must-act", expanded=False):
            opp_options = {
                f"{d['account'] if pd.notna(d.get('account')) else '(unmapped)'} — {d['product']}": d["opportunity_id"]
                for _, d in rep_must.iterrows()
            }
            if opp_options:
                selected_label = st.selectbox(
                    "Pick must-act",
                    list(opp_options.keys()),
                    key=f"rep_action_select_{rep}",
                )
                chosen_opp = opp_options[selected_label]

                # Preview of selected must-act — visual confirmation before logging
                deal_row = rep_must[rep_must["opportunity_id"] == chosen_opp].iloc[0]
                badge = reason_badge(deal_row["must_act_reason"])
                judged_mark = " ✨" if deal_row.get("is_judged") else ""
                preview_account = deal_row["account"] if pd.notna(deal_row.get("account")) else "(unmapped)"
                ctx_parts = [
                    deal_row["deal_stage"],
                    f"{deal_row['days_in_pipeline']:.0f}d",
                    fmt_money(deal_row["expected_value"]),
                    f"close {deal_row['close_probability']*100:.0f}%",
                ]
                with st.container(border=True):
                    st.markdown(f"{badge} **{preview_account} — {deal_row['product']}{judged_mark}** · score {deal_row['score']:.0f}")
                    st.caption(" · ".join(ctx_parts))
                    st.markdown(f"▸ {deal_row['action']}")

                action_kind = st.radio(
                    "Action",
                    ["✓ Done", "⏰ Defer", "✗ Skip", "🆘 Request manager help"],
                    horizontal=True,
                    key=f"rep_action_kind_{rep}",
                )
                button_label = {
                    "✓ Done": "Mark as Done",
                    "⏰ Defer": "Defer must-act",
                    "✗ Skip": "Skip & log reason",
                    "🆘 Request manager help": "🆘 Send help request",
                }.get(action_kind, "Log action")

                if action_kind.startswith("✓"):
                    outcome = st.text_input(
                        "Outcome note (optional)",
                        placeholder="e.g. DM agreed to proposal review next Tuesday",
                        key=f"rep_outcome_{rep}",
                    )
                    if st.button(button_label, key=f"rep_action_submit_{rep}", type="primary"):
                        actions.log_action(rep, actions.ACTION_MUST_ACT_DONE, {
                            "opp_id": chosen_opp,
                            "note": outcome.strip() if outcome.strip() else None,
                        })
                        st.success("Logged: must-act marked done.")
                        st.rerun()
                elif action_kind.startswith("🆘"):
                    ask = st.text_area(
                        "What kind of help do you need? (required)",
                        placeholder=(
                            "e.g. CFO wants to speak with someone of equivalent seniority before signing / "
                            "pricing exception needed / competitive intel — buyer mentioned competitor X / "
                            "strategic account, manager should lead next call"
                        ),
                        height=80,
                        key=f"rep_help_ask_{rep}",
                    )
                    st.caption(
                        f"This will surface in **{manager}**'s brief as a 🆘 Help request. "
                        "The must-act leaves your list once you submit."
                    )
                    if st.button(button_label, key=f"rep_action_submit_{rep}", type="primary"):
                        if ask.strip():
                            actions.log_action(rep, actions.ACTION_REP_HELP_REQUEST, {
                                "opp_id": chosen_opp,
                                "ask": ask.strip(),
                                "manager": manager,
                                "account": deal_row["account"] if pd.notna(deal_row.get("account")) else None,
                                "product": deal_row["product"],
                                "value": float(deal_row["expected_value"]),
                            })
                            st.success(f"Help request sent to {manager}.")
                            st.rerun()
                        else:
                            st.warning("Describe the help you need (be specific — manager needs to know what to unlock).")
                else:
                    note = st.text_input(
                        "Reason (required)",
                        placeholder="e.g. awaiting buyer response / lost to competitor / not worth pursuing because...",
                        key=f"rep_action_note_{rep}",
                    )
                    if st.button(button_label, key=f"rep_action_submit_{rep}", type="primary"):
                        if note.strip():
                            atype = actions.ACTION_MUST_ACT_DEFER if action_kind.startswith("⏰") else actions.ACTION_MUST_ACT_SKIP
                            actions.log_action(rep, atype, {"opp_id": chosen_opp, "note": note.strip()})
                            st.success("Logged with reason.")
                            st.rerun()
                        else:
                            st.warning("Provide a reason for Defer / Skip.")

    if len(stay_close):
        st.markdown("### 👀 Stay close")
        st.caption("Not today's fire, but don't let these cool further.")
        watch = pd.DataFrame({
            "Health": stay_close["score"].apply(score_color),
            "Score": stay_close["score"].round(0).astype(int),
            "Stage": stay_close["deal_stage"],
            "Account": stay_close["account"],
            "Product": stay_close["product"],
            "Days": stay_close["days_in_pipeline"].round(0).astype("Int64"),
            "Expected $": stay_close["expected_value"].apply(fmt_money),
            "Action": stay_close["action"],
        })
        st.dataframe(
            watch, use_container_width=True, hide_index=True, height=280,
            column_config={
                "Health": st.column_config.TextColumn(
                    width="small",
                    help="🟢 score ≥ 70 · 🟡 score 50–69 · 🔴 score < 50",
                ),
                "Score": st.column_config.NumberColumn(width="small"),
                "Stage": st.column_config.TextColumn(width="small"),
                "Account": st.column_config.TextColumn(width="medium"),
                "Product": st.column_config.TextColumn(width="medium"),
                "Days": st.column_config.NumberColumn(width="small"),
                "Expected $": st.column_config.TextColumn(width="small"),
                "Action": st.column_config.TextColumn(width="large"),
            },
        )

    if len(rest_active):
        with st.expander(f"📋 Other active deals ({len(rest_active):,}) — explicitly deprioritized today"):
            other = pd.DataFrame({
                "Score": rest_active["score"].round(0).astype(int),
                "Stage": rest_active["deal_stage"],
                "Account": rest_active["account"],
                "Product": rest_active["product"],
                "Days": rest_active["days_in_pipeline"].round(0).astype("Int64"),
                "Action": rest_active["action"],
            })
            st.dataframe(other, use_container_width=True, hide_index=True, height=300)

    if len(rep_ghost):
        with st.expander(f"🧊 Pipeline ghosts ({len(rep_ghost):,}) — likely dead, consider CRM cleanup"):
            ghosts = pd.DataFrame({
                "Stage": rep_ghost["deal_stage"],
                "Account": rep_ghost["account"],
                "Product": rep_ghost["product"],
                "Days": rep_ghost["days_in_pipeline"].round(0).astype("Int64"),
                "Expected $": rep_ghost["expected_value"].apply(fmt_money),
            })
            st.dataframe(ghosts, use_container_width=True, hide_index=True, height=240)

    if len(rep_orphan):
        with st.expander(f"🚨 Orphan deals ({len(rep_orphan):,}) — no account record, need CRM cleanup before any action"):
            st.caption(
                "These deals have a product, stage, and dates — but no account is linked. "
                "Recommend a single batch action: pair each opportunity_id with the correct account "
                "record, then re-import. After cleanup they'll surface in the normal brief."
            )
            orphans = pd.DataFrame({
                "Opp ID": rep_orphan["opportunity_id"],
                "Stage": rep_orphan["deal_stage"],
                "Product": rep_orphan["product"],
                "Days": rep_orphan["days_in_pipeline"].round(0).astype("Int64"),
                "Expected $": rep_orphan["expected_value"].apply(fmt_money),
            })
            st.dataframe(orphans, use_container_width=True, hide_index=True, height=240)

    # ---- Audit log (today's actions by this rep) — closes the Brief tab
    st.divider()
    _render_audit_log(rep, role_label="rep")


# ---------- Pipeline drilldown ----------

def render_pipeline_drilldown(scored: pd.DataFrame, scope: dict | None = None):
    """Pipeline drilldown — full inspection mode.

    `scope` enforces role-based visibility:
      - {"kind": "manager", "name": "..."} → filters to that manager's team
      - {"kind": "rep", "name": "..."} → filters to that rep's own pipeline
      - None → full org view (VP/Director surface)
    """
    scope_suffix = ""
    if scope:
        if scope["kind"] == "manager":
            scored = scored[scored["manager"] == scope["name"]]
            scope_suffix = f" — scoped to {scope['name']}'s team"
            key_suffix = f"_{scope['name']}"
        elif scope["kind"] == "rep":
            scored = scored[scored["sales_agent"] == scope["name"]]
            scope_suffix = " — scoped to your pipeline"
            key_suffix = f"_{scope['name']}"
        else:
            key_suffix = ""
    else:
        key_suffix = ""

    with st.expander(f"🔍 Pipeline detalhado — full inspection mode{scope_suffix}", expanded=True):
        if scope and scope["kind"] == "manager":
            st.caption(
                f"Scoped to **{scope['name']}**'s team. In production, RBAC enforces this — "
                "cross-team view is a separate VP/Director surface."
            )
        elif scope and scope["kind"] == "rep":
            st.caption(
                f"Scoped to **{scope['name']}**'s own pipeline. In production, RBAC enforces this."
            )
        else:
            st.caption(
                "Lower-priority surface. The opinionated brief above is the primary view. "
                "Use this for ad-hoc inspection or audit."
            )
        open_deals = scored[scored["deal_stage"].isin(["Prospecting", "Engaging"])].copy()

        f_mgr = []
        if scope:
            col1, col2, col3 = st.columns(3)
            with col1:
                sectors = sorted(open_deals["sector"].dropna().unique().tolist())
                f_sec = st.multiselect("Sector", sectors, key=f"dd_sec{key_suffix}")
            with col2:
                stages = ["Prospecting", "Engaging"]
                f_stage = st.multiselect("Stage", stages, default=stages, key=f"dd_stage{key_suffix}")
            with col3:
                min_score = st.slider("Min score", 0, 100, 0, 5, key=f"dd_min{key_suffix}")
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                managers = sorted(open_deals["manager"].dropna().unique().tolist())
                f_mgr = st.multiselect("Manager", managers, key="dd_mgr")
            with col2:
                sectors = sorted(open_deals["sector"].dropna().unique().tolist())
                f_sec = st.multiselect("Sector", sectors, key="dd_sec")
            with col3:
                stages = ["Prospecting", "Engaging"]
                f_stage = st.multiselect("Stage", stages, default=stages, key="dd_stage")
            with col4:
                min_score = st.slider("Min score", 0, 100, 0, 5, key="dd_min")

        f = open_deals
        if f_mgr: f = f[f["manager"].isin(f_mgr)]
        if f_sec: f = f[f["sector"].isin(f_sec)]
        if f_stage: f = f[f["deal_stage"].isin(f_stage)]
        f = f[f["score"] >= min_score].sort_values("score", ascending=False)

        view = pd.DataFrame({
            "Health": f["score"].apply(score_color),
            "Score": f["score"].round(0).astype(int),
            "Stage": f["deal_stage"],
            "Account": f["account"],
            "Sector": f["sector"],
            "Product": f["product"],
            "Rep": f["sales_agent"],
            "Days": f["days_in_pipeline"].round(0).astype("Int64"),
            "Expected $": f["expected_value"].apply(fmt_money),
            "Action": f["action"],
        })
        st.dataframe(
            view, use_container_width=True, hide_index=True, height=420,
            column_config={
                "Health": st.column_config.TextColumn(
                    width="small",
                    help="🟢 score ≥ 70 · 🟡 score 50–69 · 🔴 score < 50",
                ),
                "Score": st.column_config.NumberColumn(width="small"),
                "Stage": st.column_config.TextColumn(width="small"),
                "Account": st.column_config.TextColumn(width="medium"),
                "Sector": st.column_config.TextColumn(width="small"),
                "Product": st.column_config.TextColumn(width="medium"),
                "Rep": st.column_config.TextColumn(width="medium"),
                "Days": st.column_config.NumberColumn(width="small"),
                "Expected $": st.column_config.TextColumn(width="small"),
                "Action": st.column_config.TextColumn(width="large"),
            },
        )
        st.caption(f"{len(f):,} of {len(open_deals):,} open deals shown.")


# ---------- Main ----------

def main():
    st.title("🎯 Lead Scorer — opinionated Morning Brief")
    st.caption(
        "_3 must-acts today, not 2,000 rows to browse._ "
        "Brief-first; pipeline table is a secondary drilldown."
    )

    try:
        df, accounts = load_data()
    except FileNotFoundError as e:
        st.error(
            f"Missing CSV files in `{DATA_DIR}/`. Expected: accounts.csv, "
            f"products.csv, sales_teams.csv, sales_pipeline.csv. ({e})"
        )
        st.stop()

    # Data-anchored "today": use the dataset's latest activity, not real-wall-clock.
    # Rationale: this is a 2017 vintage CRM dump. Anchoring to wall-clock makes every
    # open deal look ~9 years stale and the entire brief collapses to "all dead".
    # In production: replace with datetime.today(). The substitution is one line.
    date_candidates = []
    for col in ("engage_date", "close_date"):
        if col in df.columns and df[col].notna().any():
            date_candidates.append(df[col].max())
    ref_date = max(date_candidates) if date_candidates else pd.Timestamp(datetime.today().date())

    scored, stage_probs = score_pipeline(df, accounts_df=accounts, ref_date=ref_date)
    open_mask = scored["deal_stage"].isin(["Prospecting", "Engaging"])
    open_deals = scored[open_mask].copy()

    close_window = empirical_close_window(scored)
    open_deals["is_ghost"] = classify_pipeline_ghost(open_deals, close_window)
    open_deals["is_orphan"] = open_deals["account"].isna()
    ghost_deals = open_deals[open_deals["is_ghost"]]
    orphan_deals = open_deals[~open_deals["is_ghost"] & open_deals["is_orphan"]]
    # active pool = open AND not ghost AND has account record
    active_deals = open_deals[~open_deals["is_ghost"] & ~open_deals["is_orphan"]]

    # ---- Reframe disclosure: how we treat the dataset honestly
    st.info(
        f"📅 **Reference date:** {ref_date.strftime('%Y-%m-%d')} "
        f"(anchored to the latest activity in the dataset, not wall-clock). "
        f"This is a 2017 CRM dump — using real today would make every open deal "
        f"~9 years stale. In production: anchor to `datetime.now()` instead "
        f"(one-line change in `main()`)."
    )

    # ---- Ghost banner: the reframe
    if len(ghost_deals):
        st.warning(
            f"⚠️ **Pipeline ghost detected:** {len(ghost_deals):,} open deals "
            f"({len(ghost_deals)/len(open_deals)*100:.0f}% of open pipeline) "
            f"have been open longer than 3× the median sales cycle ({close_window}d). "
            "In a real CRM this signals stale records, not opportunities. "
            "Today's brief works only on the active pool — ghosts surfaced separately."
        )

    # ---- Orphan banner: deals with no account record
    if len(orphan_deals):
        st.error(
            f"🚨 **Orphan deals — CRM hygiene problem:** {len(orphan_deals):,} open deals "
            f"({len(orphan_deals)/len(open_deals)*100:.0f}% of open pipeline) "
            "have no account record linked. A rep cannot act on a deal that doesn't say "
            "*who* to call. These are excluded from today's brief and listed separately for cleanup."
        )

    # ---- Sidebar: brand + mode toggle + context selector + dataset snapshot
    with st.sidebar:
        st.markdown("## 🎯 Lead Scorer")
        st.caption("Morning Brief — opinionated decision system")
        st.divider()

        mode = st.radio(
            "Brief mode",
            ["📋 Manager (team view)", "👤 Rep (individual view)"],
            key="sidebar_mode",
        )

        st.divider()

        if mode.startswith("📋"):
            managers = sorted(active_deals["manager"].dropna().unique().tolist())
            # Default to manager with most time-critical reps (demo lands hot)
            must_acts_for_default = compute_must_acts(active_deals, close_window)
            tc_by_mgr = (must_acts_for_default[must_acts_for_default["must_act_reason"].isin(["time_critical", "both"])]
                         .groupby("manager").size().sort_values(ascending=False))
            default_mgr_idx = 0
            if not tc_by_mgr.empty:
                default_mgr = tc_by_mgr.index[0]
                if default_mgr in managers:
                    default_mgr_idx = managers.index(default_mgr)
            selected_manager = st.selectbox("Choose a manager", managers, index=default_mgr_idx, key="sidebar_mgr_selector")
            selected_rep = None
        else:
            reps = sorted(
                set(active_deals["sales_agent"].dropna())
                | set(orphan_deals["sales_agent"].dropna())
                | set(ghost_deals["sales_agent"].dropna())
            )
            selected_rep = st.selectbox("Choose a rep", reps, index=0, key="sidebar_rep_selector")
            selected_manager = None

        st.divider()

        st.markdown("**📊 Dataset snapshot**")
        ghost_days = int(close_window * 3)
        st.markdown(
            f'Open <span title="Prospecting + Engaging stages — all not-closed deals in the pipeline" style="cursor:help;color:#888;">ⓘ</span>: **{len(open_deals):,}** deals  \n'
            f'Active <span title="Open AND not ghost AND not orphan — the actionable pool today (where the brief draws from)" style="cursor:help;color:#888;">ⓘ</span>: **{len(active_deals):,}**  \n'
            f'Ghost <span title="days_in_pipeline > 3× empirical close cycle ({ghost_days}d) — likely dead, needs CRM cleanup" style="cursor:help;color:#888;">ⓘ</span>: **{len(ghost_deals):,}**  \n'
            f'Orphan <span title="account record missing (account=NaN) — rep cannot act without CRM cleanup" style="cursor:help;color:#888;">ⓘ</span>: **{len(orphan_deals):,}**',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<small><i>Ref date <span title="Anchored to max(close_date) in the dataset — not wall-clock. Dataset is from 2017; without this anchor every open deal would classify as ghost." style="cursor:help;color:#888;">ⓘ</span>: <b>{ref_date.strftime("%Y-%m-%d")}</b></i></small>',
            unsafe_allow_html=True,
        )

        st.divider()
        st.caption(
            "_Built with Streamlit + Claude Code._  \n"
            "Source: Anderson Hirota for G4 AI Master challenge 003."
        )

    st.divider()
    if mode.startswith("📋"):
        render_manager_mode(active_deals, ghost_deals, orphan_deals, close_window, scored, stage_probs, manager=selected_manager)
    else:
        render_rep_mode(active_deals, ghost_deals, orphan_deals, close_window, scored, stage_probs, rep=selected_rep)


if __name__ == "__main__":
    main()
