# judge.py — LLM-as-judge for contextual deal actions.
#
# Each must-act deal gets a context-aware action via the Claude CLI.
# Context cited per deal: account, sector, other open deals at this account,
# rep's historical close rate, days remaining before ghost-flip.
#
# Cache layout: .judge_cache/{opp_id}_{input_hash}.json
# Cache invalidates when any input that determines the answer changes.

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

CACHE_DIR = Path(__file__).parent / ".judge_cache"
CACHE_DIR.mkdir(exist_ok=True)

CLAUDE_TIMEOUT = 60  # seconds per call

# Reject preamble/thinking leaks from the model.
BAD_PREFIXES = (
    "wait", "i'll", "i'd", "let me", "i will", "i would", "sure",
    "of course", "here's", "here is", "okay", "ok,", "got it",
    "looking at", "based on", "analyzing", "reviewing", "actually,",
)


def _extract_first_sentence(raw: str) -> str:
    """Model sometimes outputs answer + meta-talk. Take the first clean sentence."""
    if not raw:
        return ""
    # Strip surrounding whitespace and any leading "Action:" / quote / bullet
    s = raw.strip()
    for prefix in ('"', "'", "Action:", "ACTION:", "**", "- ", "* "):
        if s.startswith(prefix):
            s = s.removeprefix(prefix).strip(' "')
    # Cut at first paragraph break — model second-guessing usually lives after
    s = s.split("\n\n")[0].strip()
    # Take first line if there are line breaks
    s = s.split("\n")[0].strip()
    return s


def _is_clean_action(action: str) -> bool:
    """Filter outputs that look like model preamble/thinking, not the requested sentence."""
    if not action:
        return False
    a = action.strip()
    if len(a) < 20 or len(a) > 200:
        return False
    low = a.lower()
    if any(low.startswith(p) for p in BAD_PREFIXES):
        return False
    if not a.rstrip().endswith((".", "!", "?")):
        return False
    return True

CALL_PREP_PROMPT = """You are a Revenue Operations analyst generating a SHORT call-prep dossier for a salesperson going into a call on this specific deal. Structure the dossier as markdown for quick scanning.

REQUIREMENTS
- Max 200 words total across the whole dossier.
- Use these exact section headers in this order:
  **Account snapshot** — 1 line.
  **Why it matters today** — cite the score signal (high-score / time-critical / both) and days-to-ghost if relevant.
  **3 discovery questions** — bulleted, deal-specific (not generic).
  **Positioning angle** — cite ONE concrete leverage point (rep alpha in this sector, account context, product fit).
  **Likely objection + counter** — 1 specific objection given the data + 1-line counter.
- No fluff sentences. No "Hope this helps."
- Output ONLY the markdown dossier. No preamble like "Here's your prep:".

CONTEXT
- Rep: {rep_full_name}
- Account: {account}
- Sector: {sector}
- Account annual revenue: {account_revenue}
- Product in this deal: {product}
- Deal stage: {deal_stage} for {days_in_pipeline} days
- Score: {score} / Close prob: {close_pct}%
- Expected value: {expected_value}
- Why this is a must-act: {reason_explanation}
- Days remaining before ghost-flip: {days_remaining}
- Recommended action (from system): {recommended_action}
- Rep historical close rate (overall): {rep_close_rate_pct}%
- Rep's signal in THIS sector: {rep_sector_signal}
- Other open deals at this account: {other_open}

OUTPUT
"""


COACHING_NOTE_PROMPT = """You are a SALES MANAGER writing a SHORT coaching note to one of your reps. The system has flagged this rep as in critical state. Use the data to write a personalized message.

REQUIREMENTS
- 4-5 sentences, max 90 words total.
- Address the rep by first name. Sign off with "{manager_first_name}".
- Open with empathy or acknowledgment of what they're carrying (top deals + count).
- ONE specific tactical recommendation (e.g. "block 2h Tuesday for batch-call X account").
- ONE leverage point — cite their sector alpha (where they're strong).
- ONE coverage line — "you're not alone" / "I'm on the deals" / "Y will cover Z".
- Direct, not corporate. No "let's circle back".
- No bullet points. Continuous prose.
- No prefix like "Here's the note:" — just the message.

CONTEXT
- Rep: {rep_first_name} ({rep_full_name})
- Reports to manager: {manager_full_name}
- Critical state today: {tc_count} time-critical deals · {hs_count} high-score · {orphan_count} orphan deals to clean
- Top struggling deals: {top_deals}
- Sector alpha (rep is strong here, +pp vs team): {sector_alpha}
- Sector bleed (rep loses ground here): {sector_bleed}
- Pipeline value tied up in must-acts: {pipeline_value}

OUTPUT
"""


MANAGER_PROMPT_TEMPLATES = {
    "type_1_closer": """You are a Revenue Operations analyst advising a SALES MANAGER on a strategic deal where the MANAGER PERSONALLY leads the close. Write a SINGLE action sentence telling the manager what to do.

REQUIREMENTS
- Max 140 characters.
- Address the manager directly ("You lead...", "You take the call...").
- Cite ONE specific signal from the context (account name, value, rep weakness, sector).
- Make clear what MANAGER AUTHORITY adds that the rep alone cannot bring (executive equivalence, pricing exception, relationship).
- No "consider", no "perhaps". Imperative.
- No prefix. Just the sentence.

CONTEXT
- Account: {account}
- Sector: {sector}
- Product: {product}
- Deal value: {expected_value}
- Stage: {deal_stage} for {days_in_pipeline}d
- Rep on the deal: {rep_name}
- Rep's historical close rate (overall): {rep_close_rate_pct}%
- Rep's performance in this sector: {rep_sector_signal}
- Other open deals at this account: {other_open}
- Days remaining before ghost-flip: {days_remaining}
- Why this is a manager-level move: {rationale}

OUTPUT
""",
    "type_2_intervention": """You are a Revenue Operations analyst advising a SALES MANAGER to STEP INTO a stuck deal — not because the rep is bad, but because manager authority/relationship unlocks something the rep cannot. Write a SINGLE action sentence.

REQUIREMENTS
- Max 140 characters.
- Address the manager directly ("You call...", "You escalate...", "You intervene...").
- Cite ONE specific signal: why the rep is stuck (sector bleed, account complexity, days remaining).
- Make clear what MANAGER UNLOCKS the rep can't (decision-maker relationship, pricing authority, exec sponsor activation).
- Time-pressure where relevant.
- No "consider", no "maybe". Imperative.
- No prefix. Just the sentence.

CONTEXT
- Account: {account}
- Sector: {sector}
- Product: {product}
- Deal value: {expected_value}
- Stage: {deal_stage} for {days_in_pipeline}d
- Rep on the deal: {rep_name}
- Rep's performance in this sector: {rep_sector_signal}
- Other open deals at this account: {other_open}
- Days remaining before ghost-flip: {days_remaining}
- Why intervention is needed: {rationale}

OUTPUT
""",
}


PROMPT_TEMPLATE = """You are a Revenue Operations analyst advising ONE salesperson on ONE specific deal. Read the context, then write a SINGLE action sentence.

REQUIREMENTS
- Max 120 characters.
- Cite ONE specific signal from the context (an actual number, account, sector, or product). Generic advice is wrong.
- Imperative — tell the rep what to DO. No "consider", "you might", "perhaps".
- No prefix like "Action:" or quotes. Just the sentence.

CONTEXT
- Account: {account}
- Sector: {sector}
- Account annual revenue: {account_revenue}
- Product in this deal: {product}
- Stage: {deal_stage} for {days_in_pipeline}d
- Pipeline score (0-100): {score}
- Why this deal made the must-act list: {must_act_reason} ({reason_explanation})
- Other open deals at this account: {other_open}
- Rep's historical close rate (all-time): {rep_close_rate_pct}%
- Days remaining before this deal flips to ghost: {days_remaining}

OUTPUT
"""

REASON_EXPLANATION = {
    "high_score": "score above quality floor",
    "time_critical": "in final window before ghost-flip",
    "both": "high score AND time-critical",
}


def _build_input_payload(deal: pd.Series, ctx: dict) -> dict:
    """The cache key inputs — change any of these and we regen."""
    return {
        "deal_stage": deal["deal_stage"],
        "days_in_pipeline": int(deal["days_in_pipeline"]) if pd.notna(deal.get("days_in_pipeline")) else None,
        "score": round(float(deal["score"]), 1),
        "must_act_reason": deal["must_act_reason"],
        "product": deal["product"],
        "account": ctx.get("account"),
        "sector": ctx.get("sector"),
        "account_revenue": ctx.get("account_revenue"),
        "other_open": ctx["other_open"],
        "rep_close_rate_pct": ctx["rep_close_rate_pct"],
        "days_remaining": ctx["days_remaining"],
    }


def _payload_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:12]


def _cache_path(opp_id: str, payload_hash: str) -> Path:
    return CACHE_DIR / f"{opp_id}_{payload_hash}.json"


def _build_prompt(deal: pd.Series, ctx: dict) -> str:
    reason = deal["must_act_reason"]
    return PROMPT_TEMPLATE.format(
        account=ctx["account"],
        sector=ctx.get("sector") or "unknown",
        account_revenue=f"${ctx['account_revenue']:,.0f}" if ctx.get("account_revenue") else "unknown",
        product=deal["product"],
        deal_stage=deal["deal_stage"],
        days_in_pipeline=int(deal["days_in_pipeline"]) if pd.notna(deal["days_in_pipeline"]) else "—",
        score=round(deal["score"]),
        must_act_reason=reason,
        reason_explanation=REASON_EXPLANATION.get(reason, ""),
        other_open=ctx["other_open"],
        rep_close_rate_pct=ctx["rep_close_rate_pct"],
        days_remaining=ctx["days_remaining"] if ctx["days_remaining"] is not None else "—",
    )


def build_context(deal: pd.Series, scored_df: pd.DataFrame, ghost_threshold: int) -> dict:
    """Compute the context the prompt cites."""
    account = deal["account"]
    rep = deal["sales_agent"]

    other_open_at_acc = scored_df[
        (scored_df["account"] == account)
        & (scored_df["deal_stage"].isin(["Prospecting", "Engaging"]))
        & (scored_df["opportunity_id"] != deal["opportunity_id"])
    ]

    rep_closed = scored_df[
        (scored_df["sales_agent"] == rep)
        & (scored_df["deal_stage"].isin(["Won", "Lost"]))
    ]
    rep_close_rate = (rep_closed["deal_stage"] == "Won").mean() if len(rep_closed) else 0.0

    days_remaining = (
        int(ghost_threshold - deal["days_in_pipeline"])
        if pd.notna(deal["days_in_pipeline"])
        else None
    )

    return {
        "account": account,
        "sector": deal.get("sector") if pd.notna(deal.get("sector")) else None,
        "account_revenue": float(deal["revenue"]) if pd.notna(deal.get("revenue")) else None,
        "other_open": len(other_open_at_acc),
        "rep_close_rate_pct": round(rep_close_rate * 100),
        "days_remaining": days_remaining,
    }


def judge_action(deal: pd.Series, ctx: dict, use_cache: bool = True) -> Optional[str]:
    """Returns the LLM-judged action string, or None on failure / no claude CLI."""
    payload = _build_input_payload(deal, ctx)
    h = _payload_hash(payload)
    cache_p = _cache_path(str(deal["opportunity_id"]), h)

    if use_cache and cache_p.exists():
        try:
            return json.loads(cache_p.read_text())["action"]
        except (json.JSONDecodeError, KeyError):
            pass  # corrupted cache entry, regen

    prompt = _build_prompt(deal, ctx)
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=CLAUDE_TIMEOUT,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0:
        return None

    action = _extract_first_sentence(result.stdout)
    if not _is_clean_action(action):
        return None  # caller falls back to template

    cache_p.write_text(json.dumps({"action": action, "payload": payload}, indent=2))
    return action


def judge_all_must_acts(
    must_acts: pd.DataFrame,
    scored_df: pd.DataFrame,
    close_window: int,
    verbose: bool = False,
) -> dict:
    """Iterate must-acts, return {opp_id: judged_action}.
    Failures are silently dropped — caller falls back to template action."""
    ghost_threshold = close_window * 3
    out = {}
    total = len(must_acts)
    for i, (_, deal) in enumerate(must_acts.iterrows(), 1):
        ctx = build_context(deal, scored_df, ghost_threshold)
        if verbose:
            print(f"[{i}/{total}] {deal['opportunity_id']} ({deal['must_act_reason']}) ...", flush=True)
        action = judge_action(deal, ctx)
        if action:
            out[deal["opportunity_id"]] = action
            if verbose:
                print(f"          → {action}", flush=True)
        elif verbose:
            print(f"          → [FALLBACK]", flush=True)
    return out


def load_cache_into_dict(must_acts: pd.DataFrame, scored_df: pd.DataFrame, close_window: int) -> dict:
    """Read-only path used by Streamlit: looks up cache, never calls Claude."""
    ghost_threshold = close_window * 3
    out = {}
    for _, deal in must_acts.iterrows():
        ctx = build_context(deal, scored_df, ghost_threshold)
        payload = _build_input_payload(deal, ctx)
        h = _payload_hash(payload)
        cache_p = _cache_path(str(deal["opportunity_id"]), h)
        if cache_p.exists():
            try:
                raw = json.loads(cache_p.read_text())["action"]
                cleaned = _extract_first_sentence(raw)
                if _is_clean_action(cleaned):
                    out[deal["opportunity_id"]] = cleaned
                # otherwise skip — read-time validation rejects polluted cache entries
            except (json.JSONDecodeError, KeyError):
                continue
    return out


# ---------- Manager-level LLM judge ----------

def _manager_cache_path(opp_id: str, action_type: str, payload_hash: str) -> Path:
    return CACHE_DIR / f"manager_{action_type}_{opp_id}_{payload_hash}.json"


def _build_manager_input_payload(deal: pd.Series, ctx: dict, action_type: str) -> dict:
    return {
        "action_type": action_type,
        "deal_stage": deal["deal_stage"],
        "days_in_pipeline": int(deal["days_in_pipeline"]) if pd.notna(deal.get("days_in_pipeline")) else None,
        "expected_value": round(float(deal["expected_value"]), 2),
        "product": deal["product"],
        "account": ctx.get("account"),
        "sector": ctx.get("sector"),
        "rep_name": ctx.get("rep_name"),
        "rep_close_rate_pct": ctx.get("rep_close_rate_pct"),
        "rep_sector_signal": ctx.get("rep_sector_signal"),
        "other_open": ctx.get("other_open"),
        "days_remaining": ctx.get("days_remaining"),
        "rationale": ctx.get("rationale"),
    }


def _build_manager_prompt(deal: pd.Series, ctx: dict, action_type: str) -> str:
    tpl = MANAGER_PROMPT_TEMPLATES.get(action_type)
    if not tpl:
        return ""
    return tpl.format(
        account=ctx.get("account") or "unknown",
        sector=ctx.get("sector") or "unknown",
        product=deal["product"],
        expected_value=f"${deal['expected_value']:,.0f}",
        deal_stage=deal["deal_stage"],
        days_in_pipeline=int(deal["days_in_pipeline"]) if pd.notna(deal["days_in_pipeline"]) else "—",
        rep_name=ctx.get("rep_name") or "the rep",
        rep_close_rate_pct=ctx.get("rep_close_rate_pct") if ctx.get("rep_close_rate_pct") is not None else "—",
        rep_sector_signal=ctx.get("rep_sector_signal") or "no specific sector signal",
        other_open=ctx.get("other_open") if ctx.get("other_open") is not None else 0,
        days_remaining=ctx.get("days_remaining") if ctx.get("days_remaining") is not None else "—",
        rationale=ctx.get("rationale") or "strategic value warrants manager visibility",
    )


def build_manager_context(
    deal: pd.Series,
    scored_df: pd.DataFrame,
    rep_coach: dict,
    ghost_threshold: int,
    rationale: str,
) -> dict:
    """Context for a manager-level prompt — adds rep-side framing the rep prompt doesn't have."""
    account = deal["account"]
    rep = deal["sales_agent"]

    other_open_at_acc = scored_df[
        (scored_df["account"] == account)
        & (scored_df["deal_stage"].isin(["Prospecting", "Engaging"]))
        & (scored_df["opportunity_id"] != deal["opportunity_id"])
    ]

    rep_close_rate_pct = round((rep_coach.get("overall", {}).get("rep_wr", 0.5)) * 100) if rep_coach else 50

    # Rep's signal in this deal's sector — alpha, bleed, or neutral
    rep_sector_signal = "neutral"
    deal_sector = deal.get("sector")
    if pd.notna(deal_sector) and rep_coach:
        for a in rep_coach.get("sector_alpha", []):
            if a["label"] == deal_sector:
                rep_sector_signal = f"+{a['delta_pp']:.0f}pp alpha (rep is strong here)"
                break
        for b in rep_coach.get("sector_bleed", []):
            if b["label"] == deal_sector:
                rep_sector_signal = f"{b['delta_pp']:.0f}pp bleed (rep struggles here — manager equivalence helps)"
                break

    days_remaining = None
    if pd.notna(deal.get("days_in_pipeline")):
        days_remaining = max(0, ghost_threshold - int(deal["days_in_pipeline"]))

    return {
        "account": account if pd.notna(account) else None,
        "sector": deal_sector if pd.notna(deal_sector) else None,
        "rep_name": rep,
        "rep_close_rate_pct": rep_close_rate_pct,
        "rep_sector_signal": rep_sector_signal,
        "other_open": int(len(other_open_at_acc)),
        "days_remaining": days_remaining,
        "rationale": rationale,
    }


def judge_manager_action(
    deal: pd.Series,
    ctx: dict,
    action_type: str,
    use_cache: bool = True,
) -> Optional[str]:
    """LLM-judged manager-side action. Returns None on failure → caller fallbacks."""
    if action_type not in MANAGER_PROMPT_TEMPLATES:
        return None

    payload = _build_manager_input_payload(deal, ctx, action_type)
    h = _payload_hash(payload)
    cache_p = _manager_cache_path(str(deal["opportunity_id"]), action_type, h)

    if use_cache and cache_p.exists():
        try:
            raw = json.loads(cache_p.read_text())["action"]
            cleaned = _extract_first_sentence(raw)
            if _is_clean_action(cleaned):
                return cleaned
        except (json.JSONDecodeError, KeyError):
            pass

    prompt = _build_manager_prompt(deal, ctx, action_type)
    if not prompt:
        return None

    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=CLAUDE_TIMEOUT,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None

    action = _extract_first_sentence(result.stdout)
    if not _is_clean_action(action):
        return None

    cache_p.write_text(json.dumps({"action": action, "payload": payload}, indent=2))
    return action


def load_manager_cache_into_dict(
    manager_must_acts: pd.DataFrame,
    scored: pd.DataFrame,
    coaching_by_rep: dict,
    ghost_threshold: int,
) -> dict:
    """Read-only path for Streamlit. Returns {opp_id: action_str}."""
    out = {}
    for _, deal in manager_must_acts.iterrows():
        action_type = deal["manager_action_type"]
        if action_type == "type_3_system":  # Type 3 isn't LLM-judged
            continue
        rep_coach = coaching_by_rep.get(deal["sales_agent"], {})
        ctx = build_manager_context(deal, scored, rep_coach, ghost_threshold, deal.get("manager_action_rationale", ""))
        payload = _build_manager_input_payload(deal, ctx, action_type)
        h = _payload_hash(payload)
        cache_p = _manager_cache_path(str(deal["opportunity_id"]), action_type, h)
        if cache_p.exists():
            try:
                raw = json.loads(cache_p.read_text())["action"]
                cleaned = _extract_first_sentence(raw)
                if _is_clean_action(cleaned):
                    out[deal["opportunity_id"]] = cleaned
            except (json.JSONDecodeError, KeyError):
                continue
    return out


def judge_all_manager_must_acts(
    manager_must_acts: pd.DataFrame,
    scored: pd.DataFrame,
    coaching_by_rep: dict,
    close_window: int,
    verbose: bool = False,
) -> dict:
    """Generate cache for all manager must-acts. Returns {opp_id: judged_action}."""
    ghost_threshold = close_window * 3
    out = {}
    eligible = manager_must_acts[manager_must_acts["manager_action_type"] != "type_3_system"]
    total = len(eligible)
    for i, (_, deal) in enumerate(eligible.iterrows(), 1):
        action_type = deal["manager_action_type"]
        rep_coach = coaching_by_rep.get(deal["sales_agent"], {})
        ctx = build_manager_context(deal, scored, rep_coach, ghost_threshold, deal.get("manager_action_rationale", ""))
        if verbose:
            print(f"[manager {i}/{total}] {deal['opportunity_id']} ({action_type}) ...", flush=True)
        action = judge_manager_action(deal, ctx, action_type)
        if action:
            out[deal["opportunity_id"]] = action
            if verbose:
                print(f"             → {action}", flush=True)
        elif verbose:
            print(f"             → [FALLBACK]", flush=True)
    return out


# ---------- Coaching note generator (Manager → Rep) ----------

def _coaching_cache_path(rep: str, manager: str, payload_hash: str) -> Path:
    safe_rep = rep.replace(" ", "_").lower()
    safe_mgr = manager.replace(" ", "_").lower()
    return CACHE_DIR / f"coaching_{safe_mgr}_{safe_rep}_{payload_hash}.json"


def _build_coaching_payload(rep: str, manager: str, critical_rep_info: dict, rep_coach: dict) -> dict:
    """Inputs that determine the draft — change any and cache invalidates."""
    top_deals_brief = []
    for d in critical_rep_info.get("top_time_critical_deals", []):
        top_deals_brief.append(f"{d.get('account', '?')} ({d.get('product', '?')}, ${d.get('value', 0):.0f})")

    alpha = [f"{s['label']} (+{s['delta_pp']:.0f}pp)" for s in rep_coach.get("sector_alpha", [])[:2]]
    bleed = [f"{s['label']} ({s['delta_pp']:.0f}pp)" for s in rep_coach.get("sector_bleed", [])[:2]]

    return {
        "rep": rep,
        "manager": manager,
        "tc_count": critical_rep_info.get("time_critical_count", 0),
        "hs_count": critical_rep_info.get("high_score_count", 0),
        "orphan_count": critical_rep_info.get("orphan_count", 0),
        "top_deals": top_deals_brief,
        "sector_alpha": alpha,
        "sector_bleed": bleed,
        "pipeline_value": round(critical_rep_info.get("pipeline_value", 0), 0),
    }


def _format_for_prompt(items: list[str], fallback: str) -> str:
    return "; ".join(items) if items else fallback


def judge_coaching_note(
    rep: str,
    manager: str,
    critical_rep_info: dict,
    rep_coach: dict,
    use_cache: bool = True,
) -> Optional[str]:
    """Generate a personalized coaching-note draft. Manager edits before sending."""
    payload = _build_coaching_payload(rep, manager, critical_rep_info, rep_coach)
    h = _payload_hash(payload)
    cache_p = _coaching_cache_path(rep, manager, h)

    if use_cache and cache_p.exists():
        try:
            raw = json.loads(cache_p.read_text())["draft"]
            cleaned = _extract_first_sentence_or_paragraph(raw)
            if cleaned:
                return cleaned
        except (json.JSONDecodeError, KeyError):
            pass

    rep_first = rep.split()[0] if rep else "team"
    manager_first = manager.split()[0] if manager else "M."
    prompt = COACHING_NOTE_PROMPT.format(
        rep_first_name=rep_first,
        rep_full_name=rep,
        manager_first_name=manager_first,
        manager_full_name=manager,
        tc_count=payload["tc_count"],
        hs_count=payload["hs_count"],
        orphan_count=payload["orphan_count"],
        top_deals=_format_for_prompt(payload["top_deals"], "(no top deals listed)"),
        sector_alpha=_format_for_prompt(payload["sector_alpha"], "(no clear alpha yet)"),
        sector_bleed=_format_for_prompt(payload["sector_bleed"], "(no notable bleed)"),
        pipeline_value=f"${payload['pipeline_value']:,.0f}",
    )

    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=CLAUDE_TIMEOUT,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None

    draft = _extract_first_sentence_or_paragraph(result.stdout)
    if not draft or len(draft) < 50:
        return None

    cache_p.write_text(json.dumps({"draft": draft, "payload": payload}, indent=2))
    return draft


def _extract_first_sentence_or_paragraph(raw: str) -> str:
    """For coaching notes — preserve multi-sentence content but strip preamble/postscript."""
    if not raw:
        return ""
    s = raw.strip()
    # Strip common prefixes
    for prefix in ('"', "'", "Note:", "Here's the note:", "Draft:", "**"):
        if s.startswith(prefix):
            s = s.removeprefix(prefix).strip(' "')
    # If model added meta-talk after the message, cut at common leak markers
    for marker in ("\nNote:", "\nHere's", "\nAlternatively", "\n---", "\nP.S.:"):
        if marker in s:
            s = s.split(marker)[0].strip()
    # Reject if it starts with a known preamble pattern
    low = s.lower()
    if any(low.startswith(p) for p in BAD_PREFIXES):
        return ""
    return s


# ---------- Call Prep skill (per-deal dossier before a call) ----------

REASON_LABEL_LONG = {
    "high_score": "high score (above quality floor)",
    "time_critical": "time-critical (Engaging, near ghost-flip)",
    "both": "high score AND time-critical (top priority)",
}


def _call_prep_cache_path(opp_id: str, payload_hash: str) -> Path:
    return CACHE_DIR / f"call_prep_{opp_id}_{payload_hash}.json"


def _build_call_prep_payload(deal: pd.Series, ctx: dict) -> dict:
    return {
        "deal_stage": deal["deal_stage"],
        "days_in_pipeline": int(deal["days_in_pipeline"]) if pd.notna(deal.get("days_in_pipeline")) else None,
        "score": round(float(deal["score"]), 1),
        "close_probability": round(float(deal["close_probability"]), 3),
        "expected_value": round(float(deal["expected_value"]), 2),
        "must_act_reason": deal.get("must_act_reason"),
        "product": deal["product"],
        "account": ctx.get("account"),
        "sector": ctx.get("sector"),
        "account_revenue": ctx.get("account_revenue"),
        "rep_close_rate_pct": ctx.get("rep_close_rate_pct"),
        "rep_sector_signal": ctx.get("rep_sector_signal"),
        "other_open": ctx.get("other_open"),
        "days_remaining": ctx.get("days_remaining"),
        "recommended_action": deal.get("action", ""),
    }


def judge_call_prep(deal: pd.Series, ctx: dict, rep_name: str, use_cache: bool = True) -> Optional[str]:
    """Generate a structured call-prep dossier (markdown) for this deal."""
    payload = _build_call_prep_payload(deal, ctx)
    h = _payload_hash(payload)
    cache_p = _call_prep_cache_path(str(deal["opportunity_id"]), h)

    if use_cache and cache_p.exists():
        try:
            return json.loads(cache_p.read_text())["dossier"]
        except (json.JSONDecodeError, KeyError):
            pass

    prompt = CALL_PREP_PROMPT.format(
        rep_full_name=rep_name or "the rep",
        account=ctx.get("account") or "unknown account",
        sector=ctx.get("sector") or "unknown",
        account_revenue=f"${ctx['account_revenue']:,.0f}" if ctx.get("account_revenue") else "unknown",
        product=deal["product"],
        deal_stage=deal["deal_stage"],
        days_in_pipeline=int(deal["days_in_pipeline"]) if pd.notna(deal["days_in_pipeline"]) else "—",
        score=round(deal["score"]),
        close_pct=round(deal["close_probability"] * 100),
        expected_value=f"${deal['expected_value']:,.0f}",
        reason_explanation=REASON_LABEL_LONG.get(deal.get("must_act_reason"), "needs attention"),
        days_remaining=ctx.get("days_remaining") if ctx.get("days_remaining") is not None else "—",
        recommended_action=deal.get("action", "—"),
        rep_close_rate_pct=ctx.get("rep_close_rate_pct") if ctx.get("rep_close_rate_pct") is not None else "—",
        rep_sector_signal=ctx.get("rep_sector_signal") or "neutral",
        other_open=ctx.get("other_open") if ctx.get("other_open") is not None else 0,
    )

    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=CLAUDE_TIMEOUT,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None

    dossier = result.stdout.strip()
    # Strip a common preamble if any
    for prefix in ("Here's", "Here is", "Note:"):
        if dossier.startswith(prefix):
            # Try to recover by jumping to first header
            idx = dossier.find("**")
            if idx > 0:
                dossier = dossier[idx:].strip()
            break

    if len(dossier) < 80:
        return None

    cache_p.write_text(json.dumps({"dossier": dossier, "payload": payload}, indent=2))
    return dossier


# CLI entry — used by generate_judge_cache.py
if __name__ == "__main__":
    print("Use generate_judge_cache.py to populate the cache.", file=sys.stderr)
    sys.exit(1)
