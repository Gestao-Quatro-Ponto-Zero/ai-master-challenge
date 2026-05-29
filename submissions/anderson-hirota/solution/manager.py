# manager.py — Manager mode classification + systemic detection.
#
# Pure data — no LLM. The manager brief mirrors the rep brief structure:
# instead of "your 3 deals today", it's "your manager-level moves today".
#
# Three types of manager must-act:
#   Type 1 — TOP-VALUE deal where manager visibility/sponsorship matters (top-decile by expected value)
#   Type 2 — Intervention (rep is stuck, your relationship/authority breaks the wall)
#   Type 3 — System decision (triage 1:1, redistribute load, coaching call)

from __future__ import annotations

from typing import Optional

import pandas as pd

# Thresholds for manager-level signals
TYPE_1_VALUE_PERCENTILE = 90       # top decile of value = candidates for manager visibility/sponsorship
TYPE_2_DAYS_REMAINING = 14         # time-critical with <=14 days = candidate for executive intervention
MANAGER_MUST_ACT_CAP = 5           # cognitive cap for manager's own daily focus
CRITICAL_REP_TC_COUNT = 2          # rep with ≥2 time-critical = needs manager attention
CRITICAL_REPS_DISPLAY_CAP = 3      # top N critical reps surfaced in the brief
CRITICAL_MANAGER_REPS = 2          # manager with ≥2 critical reps = systemic problem
SECTOR_CONCENTRATION_THRESHOLD = 0.40  # ≥40% of time-critical in one sector = market signal
REGION_IMBALANCE_RATIO = 2.0       # top region has 2× bottom region's tc load
ORPHAN_DENSITY_THRESHOLD = 0.20    # ≥20% of team's pipeline is orphan = CRM cleanup drive


# ---------- Manager must-act classification ----------

def classify_manager_must_acts(
    scored: pd.DataFrame,
    must_acts: pd.DataFrame,
    coaching_by_rep: dict,
    manager: str,
) -> pd.DataFrame:
    """Return deals from this manager's team classified into Type 1 / Type 2 / Type 3 (Type 3 stays empty here — see build_type_3_actions).

    Type 1 — Top-value deal (manager visibility):
      - Must-act with deal value in top quartile across the team
      - Rep has low historical close rate in this sector (manager's authority adds value)

    Type 2 — Executive intervention:
      - Time-critical must-act with days-remaining ≤ 14
      - Rep is in critical state OR rep bleeds in this sector
      - Account has multiple open deals (account-level escalation pays off)
    """
    if must_acts.empty:
        return must_acts.assign(manager_action_type=pd.Series(dtype=str))

    team = must_acts[must_acts["manager"] == manager].copy()
    if team.empty:
        return team.assign(manager_action_type=pd.Series(dtype=str))

    team_value_threshold = team["expected_value"].quantile(TYPE_1_VALUE_PERCENTILE / 100)

    # First pass: classify each deal independently
    type_labels = []
    rationales = []
    for _, deal in team.iterrows():
        rep = deal["sales_agent"]
        rep_coach = coaching_by_rep.get(rep, {})

        # --- Type 2 (intervention) — narrowly defined
        is_tc = deal["must_act_reason"] in ("time_critical", "both")
        days_remaining = _days_remaining_before_ghost(deal, scored)
        rep_bleeds_sector = _rep_bleeds_in_sector(rep_coach, deal.get("sector"))
        other_open_at_acc = _other_open_at_account(scored, deal["account"], deal["opportunity_id"])

        type_2 = (
            is_tc
            and days_remaining is not None
            and days_remaining <= TYPE_2_DAYS_REMAINING
            and (rep_bleeds_sector or other_open_at_acc >= 3)
        )

        # --- Type 1 (top-value deal — manager visibility/sponsorship): top decile by expected value
        is_top_value = deal["expected_value"] >= team_value_threshold
        type_1 = is_top_value and not type_2

        if type_2:
            type_labels.append("type_2_intervention")
            why = []
            if rep_bleeds_sector:
                why.append(f"rep bleeds in {deal.get('sector')}")
            if other_open_at_acc >= 3:
                why.append(f"{other_open_at_acc} other open deals at this account")
            if days_remaining is not None:
                why.append(f"only {days_remaining}d before ghost-flip")
            rationales.append(" · ".join(why))
        elif type_1:
            type_labels.append("type_1_closer")
            rationales.append(f"top-value strategic deal (${deal['expected_value']:,.0f})")
        else:
            type_labels.append("")
            rationales.append("")

    team["manager_action_type"] = type_labels
    team["manager_action_rationale"] = rationales

    classified = team[team["manager_action_type"] != ""].copy()
    if classified.empty:
        return classified

    # Cap total at MANAGER_MUST_ACT_CAP, prioritizing type_2 then highest value
    priority = {"type_2_intervention": 0, "type_1_closer": 1}
    classified["_p"] = classified["manager_action_type"].map(priority)
    classified = classified.sort_values(["_p", "expected_value"], ascending=[True, False]).head(MANAGER_MUST_ACT_CAP)
    return classified.drop(columns=["_p"])


def build_type_3_actions(
    critical_reps: list[dict],
    systemic_patterns: list[dict],
    manager: str,
) -> list[dict]:
    """Type 3 — system decisions. Pure rules, no LLM. Returns list of action dicts."""
    actions = []

    # One triage action per critical rep (capped at top 3 most critical)
    for rep_info in critical_reps[:3]:
        rep = rep_info["rep"]
        tc_count = rep_info["time_critical_count"]
        hs_count = rep_info["high_score_count"]
        orphan_count = rep_info.get("orphan_count", 0)
        label = f"1:1 triage with {rep} — review {tc_count} time-critical deal{'s' if tc_count > 1 else ''}"
        if orphan_count > 5:
            label += f". Also clear {orphan_count} orphan deals."
        actions.append({
            "type": "type_3_system",
            "label": label,
            "category": "triage",
            "rep": rep,
            "deal_count": tc_count,
        })

    # One action per systemic pattern affecting this manager
    for pattern in systemic_patterns:
        if pattern.get("affects_manager") == manager or pattern.get("scope") == "team":
            actions.append({
                "type": "type_3_system",
                "label": pattern["action"],
                "category": pattern["category"],
                "rep": None,
                "deal_count": pattern.get("affected_count", 0),
            })

    return actions


# ---------- Helpers for must-act classification ----------

def _days_remaining_before_ghost(deal: pd.Series, scored: pd.DataFrame) -> Optional[int]:
    """Estimate days remaining before this deal would flip to ghost.
    Uses 171 (3× empirical close window) — same threshold the app uses.
    """
    if pd.isna(deal.get("days_in_pipeline")):
        return None
    won = scored[(scored["deal_stage"] == "Won")
                & scored["engage_date"].notna()
                & scored["close_date"].notna()]
    if won.empty:
        ghost_threshold = 171
    else:
        cycle = (won["close_date"] - won["engage_date"]).dt.days
        ghost_threshold = int(cycle.median() * 3) if not cycle.empty else 171
    return max(0, ghost_threshold - int(deal["days_in_pipeline"]))


def _rep_bleeds_in_sector(rep_coach: dict, sector: Optional[str]) -> bool:
    if not sector or not rep_coach:
        return False
    for bleed in rep_coach.get("sector_bleed", []):
        if bleed["label"] == sector:
            return True
    return False


def _rep_close_rate_in_sector(rep_coach: dict, sector: Optional[str]) -> float:
    if not sector or not rep_coach:
        return rep_coach.get("overall", {}).get("rep_wr", 0.5) if rep_coach else 0.5
    # Check alpha/bleed for this sector
    for s in rep_coach.get("sector_alpha", []) + rep_coach.get("sector_bleed", []):
        if s["label"] == sector:
            return s["rep_wr"]
    return rep_coach.get("overall", {}).get("rep_wr", 0.5)


def _other_open_at_account(scored: pd.DataFrame, account, exclude_opp_id) -> int:
    if pd.isna(account):
        return 0
    mask = (
        (scored["account"] == account)
        & (scored["deal_stage"].isin(["Prospecting", "Engaging"]))
        & (scored["opportunity_id"] != exclude_opp_id)
    )
    return int(mask.sum())


# ---------- Critical reps identification ----------

def identify_critical_reps(
    must_acts: pd.DataFrame,
    orphan: pd.DataFrame,
    manager: str,
) -> list[dict]:
    """Reps under this manager who are in critical state (≥CRITICAL_REP_TC_COUNT time-critical).
    Sorted by urgency: more time-critical first, then less high-score support.
    """
    if must_acts.empty:
        return []

    team = must_acts[must_acts["manager"] == manager].copy()
    if team.empty:
        return []

    team["is_tc"] = team["must_act_reason"].isin(["time_critical", "both"]).astype(int)
    team["is_hs"] = team["must_act_reason"].isin(["high_score", "both"]).astype(int)

    by_rep = team.groupby("sales_agent").agg(
        time_critical_count=("is_tc", "sum"),
        high_score_count=("is_hs", "sum"),
        must_act_count=("opportunity_id", "count"),
        pipeline_value=("expected_value", "sum"),
    ).reset_index()

    critical = by_rep[by_rep["time_critical_count"] >= CRITICAL_REP_TC_COUNT].copy()
    critical = critical.sort_values(
        ["time_critical_count", "high_score_count"],
        ascending=[False, True],  # more TC = worse; less HS = worse (no backup)
    ).head(CRITICAL_REPS_DISPLAY_CAP)

    out = []
    for _, row in critical.iterrows():
        rep = row["sales_agent"]
        rep_orphans = int((orphan["sales_agent"] == rep).sum()) if not orphan.empty else 0
        # Top 2 time-critical deals for this rep (named)
        rep_tc = team[(team["sales_agent"] == rep) & (team["is_tc"] == 1)].nlargest(2, "expected_value")
        top_deals = [
            {
                "account": d["account"] if pd.notna(d.get("account")) else "(unmapped)",
                "product": d["product"],
                "value": float(d["expected_value"]),
                "days_in_pipeline": int(d["days_in_pipeline"]) if pd.notna(d.get("days_in_pipeline")) else None,
                "score": float(d["score"]),
            }
            for _, d in rep_tc.iterrows()
        ]
        out.append({
            "rep": rep,
            "time_critical_count": int(row["time_critical_count"]),
            "high_score_count": int(row["high_score_count"]),
            "must_act_count": int(row["must_act_count"]),
            "pipeline_value": float(row["pipeline_value"]),
            "orphan_count": rep_orphans,
            "top_time_critical_deals": top_deals,
        })
    return out


# ---------- Systemic patterns ----------

def detect_systemic_patterns(
    scored: pd.DataFrame,
    must_acts: pd.DataFrame,
    orphan: pd.DataFrame,
    active: pd.DataFrame,
    manager: str,
) -> list[dict]:
    """Cross-cutting signals that span reps or accounts. Pure data."""
    patterns = []
    team_active = active[active["manager"] == manager]
    team_must_acts = must_acts[must_acts["manager"] == manager]

    # Pattern A — Manager has ≥CRITICAL_MANAGER_REPS critical reps → "problem is the manager/process"
    if not team_must_acts.empty:
        team_must_acts_tc = team_must_acts.copy()
        team_must_acts_tc["is_tc"] = team_must_acts_tc["must_act_reason"].isin(["time_critical", "both"])
        tc_by_rep = team_must_acts_tc.groupby("sales_agent")["is_tc"].sum()
        critical_reps_under_mgr = int((tc_by_rep >= CRITICAL_REP_TC_COUNT).sum())
        if critical_reps_under_mgr >= CRITICAL_MANAGER_REPS:
            patterns.append({
                "category": "manager_load",
                "severity": "high",
                "action": (
                    f"{critical_reps_under_mgr} reps under you are in critical state. "
                    "Before any individual 1:1: check inflow, territory, and process — "
                    "concentrated rep stress usually points upstream."
                ),
                "scope": "team",
                "affected_count": critical_reps_under_mgr,
                "affects_manager": manager,
            })

    # Pattern B — Sector concentration: ≥SECTOR_CONCENTRATION_THRESHOLD of TC in one sector
    tc_deals = team_must_acts[team_must_acts["must_act_reason"].isin(["time_critical", "both"])]
    if not tc_deals.empty and tc_deals["sector"].notna().any():
        sector_share = tc_deals["sector"].value_counts(normalize=True)
        if sector_share.iloc[0] >= SECTOR_CONCENTRATION_THRESHOLD:
            top_sector = sector_share.index[0]
            pct = int(sector_share.iloc[0] * 100)
            patterns.append({
                "category": "sector_concentration",
                "severity": "medium",
                "action": (
                    f"{pct}% of your team's time-critical deals are in **{top_sector}**. "
                    "This is a sector-level signal, not a per-rep issue — "
                    "look at product-market fit, pricing, or competitive pressure in that vertical."
                ),
                "scope": "team",
                "affected_count": int(tc_deals[tc_deals["sector"] == top_sector].shape[0]),
                "affects_manager": manager,
                "sector": top_sector,
            })

    # Pattern C — Orphan density: ≥ORPHAN_DENSITY_THRESHOLD of team open pipeline is orphan
    team_open_count = len(team_active) + (orphan["manager"] == manager).sum()
    team_orphan_count = int((orphan["manager"] == manager).sum())
    if team_open_count > 0:
        orphan_density = team_orphan_count / team_open_count
        if orphan_density >= ORPHAN_DENSITY_THRESHOLD:
            patterns.append({
                "category": "orphan_density",
                "severity": "high",
                "action": (
                    f"{int(orphan_density * 100)}% of your team's open pipeline ({team_orphan_count} deals) "
                    "has no account record. Drive CRM cleanup this sprint — without it, scoring and brief are blind to those deals."
                ),
                "scope": "team",
                "affected_count": team_orphan_count,
                "affects_manager": manager,
            })

    # Pattern D — Region imbalance (single-manager case usually trivial, but kept for completeness)
    if "regional_office" in team_must_acts.columns and not team_must_acts.empty:
        region_tc = tc_deals.groupby("regional_office").size() if not tc_deals.empty else pd.Series(dtype=int)
        if len(region_tc) >= 2:
            top, bottom = region_tc.max(), region_tc.min()
            if bottom > 0 and (top / bottom) >= REGION_IMBALANCE_RATIO:
                top_region = region_tc.idxmax()
                bottom_region = region_tc.idxmin()
                patterns.append({
                    "category": "region_imbalance",
                    "severity": "low",
                    "action": (
                        f"Region {top_region} carries {top} time-critical deals vs {bottom} in {bottom_region} "
                        f"({top/bottom:.1f}× spread). Consider territory rebalance."
                    ),
                    "scope": "team",
                    "affected_count": int(top),
                    "affects_manager": manager,
                })

    return patterns


# ---------- Redistribution suggestions ----------

def suggest_redistribution(
    critical_rep: dict,
    must_acts: pd.DataFrame,
    active: pd.DataFrame,
    coaching_by_rep: dict,
    manager: str,
) -> list[dict]:
    """For a critical rep, find healthier peers under the same manager who could absorb load.

    Match logic (tiered, surfaces SOMETHING when peers exist):
      1. PRIMARY: peer has sector alpha ≥+5pp in this deal's sector + tc_count ≤ 1
      2. FALLBACK: peer has overall close rate ≥ team average + tc_count ≤ 1
                   (no sector match — safe peer with capacity)

    Empty result = honestly no internal capacity (e.g. all peers in crisis too).
    """
    rep_in_crisis = critical_rep["rep"]
    team_must_acts = must_acts[must_acts["manager"] == manager]

    by_rep = team_must_acts.assign(
        is_tc=team_must_acts["must_act_reason"].isin(["time_critical", "both"]).astype(int),
    ).groupby("sales_agent").agg(
        tc_count=("is_tc", "sum"),
        must_act_count=("opportunity_id", "count"),
    ).reset_index()
    # Relaxed: peers with at most 1 time-critical deal are eligible
    quiet_reps = by_rep[
        (by_rep["tc_count"] <= 1) & (by_rep["sales_agent"] != rep_in_crisis)
    ]["sales_agent"].tolist()

    if not quiet_reps:
        return []

    crisis_deals = team_must_acts[
        (team_must_acts["sales_agent"] == rep_in_crisis)
        & team_must_acts["must_act_reason"].isin(["time_critical", "both"])
    ].nlargest(5, "expected_value")

    # Pre-compute peers' team-avg overall for fallback
    peer_overall = {}
    for cand in quiet_reps:
        coach = coaching_by_rep.get(cand, {})
        peer_overall[cand] = {
            "rep_wr": coach.get("overall", {}).get("rep_wr", 0.0),
            "team_wr": coach.get("overall", {}).get("team_wr", 0.6),
        }

    suggestions = []
    used_receivers = set()  # don't suggest the same peer for every deal — distribute load
    for _, deal in crisis_deals.iterrows():
        deal_sector = deal.get("sector")

        best_receiver = None
        best_alpha = 0
        # Tier 1: sector alpha (relaxed to ≥+5pp)
        if pd.notna(deal_sector):
            for candidate in quiet_reps:
                if candidate in used_receivers:
                    continue
                cand_coach = coaching_by_rep.get(candidate, {})
                for alpha in cand_coach.get("sector_alpha", []):
                    if alpha["label"] == deal_sector and alpha["delta_pp"] >= 5 and alpha["delta_pp"] > best_alpha:
                        best_alpha = alpha["delta_pp"]
                        best_receiver = candidate

        rationale = None
        if best_receiver:
            rationale = f"{best_receiver} has +{best_alpha:.0f}pp alpha in {deal_sector} — meaningfully above team average"
        else:
            # Tier 2: fallback — any quiet peer who isn't bleeding in this sector + above team avg overall
            for candidate in quiet_reps:
                if candidate in used_receivers:
                    continue
                cand_coach = coaching_by_rep.get(candidate, {})
                # Skip if peer bleeds in this sector
                bleeds_here = any(
                    b["label"] == deal_sector for b in cand_coach.get("sector_bleed", [])
                ) if pd.notna(deal_sector) else False
                if bleeds_here:
                    continue
                overall = peer_overall[candidate]
                if overall["rep_wr"] >= overall["team_wr"]:
                    best_receiver = candidate
                    rationale = (
                        f"{best_receiver} has 0–1 time-critical (capacity) and "
                        f"{overall['rep_wr']*100:.0f}% overall close rate "
                        f"({(overall['rep_wr']-overall['team_wr'])*100:+.0f}pp vs team)"
                    )
                    break

        if best_receiver:
            used_receivers.add(best_receiver)
            suggestions.append({
                "deal": {
                    "opportunity_id": deal["opportunity_id"],
                    "account": deal["account"] if pd.notna(deal["account"]) else "(unmapped)",
                    "product": deal["product"],
                    "sector": deal_sector if pd.notna(deal_sector) else "(unmapped)",
                    "value": float(deal["expected_value"]),
                    "days_in_pipeline": int(deal["days_in_pipeline"]) if pd.notna(deal["days_in_pipeline"]) else None,
                },
                "from_rep": rep_in_crisis,
                "to_rep": best_receiver,
                "rationale": rationale,
            })

    return suggestions[:3]
