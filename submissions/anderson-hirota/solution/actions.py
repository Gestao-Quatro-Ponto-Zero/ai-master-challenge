# actions.py — File-based audit log for manager actions in the app.
#
# This module persists actions taken from inside the Manager mode brief.
# The brief shrinks as the manager acts: must-acts marked done/deferred/skipped
# disappear, redistribution decisions log, coaching notes track sent state.
#
# Storage: .action_log/manager_actions.jsonl (append-only, gitignored).

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ACTION_LOG_DIR = Path(__file__).parent / ".action_log"
ACTION_LOG_DIR.mkdir(exist_ok=True)
ACTION_LOG_FILE = ACTION_LOG_DIR / "manager_actions.jsonl"

# Action types
ACTION_MUST_ACT_DONE = "must_act_done"
ACTION_MUST_ACT_DEFER = "must_act_defer"
ACTION_MUST_ACT_SKIP = "must_act_skip"
ACTION_COACHING_NOTE_SENT = "coaching_note_sent"
ACTION_REDISTRIBUTION_APPROVED = "redistribution_approved"
ACTION_REDISTRIBUTION_REJECTED = "redistribution_rejected"
# Cross-tier flow: rep escalates to manager
ACTION_REP_HELP_REQUEST = "rep_help_request"
ACTION_MANAGER_HELP_ACK = "manager_help_acknowledged"
ACTION_MANAGER_HELP_DISMISSED = "manager_help_dismissed"
# Manager response to systemic patterns
ACTION_PATTERN_ACK = "pattern_acknowledged"
ACTION_PATTERN_ESCALATE = "pattern_escalated"
ACTION_PATTERN_DISMISS = "pattern_dismissed"


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def log_action(actor: str, action_type: str, payload: dict) -> None:
    """Append a single action to the audit log. `actor` = manager name OR rep name."""
    record = {
        "ts": _now_iso(),
        "date": _today_str(),
        "actor": actor,
        "type": action_type,
        **payload,
    }
    with ACTION_LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_actions(actor: str, today_only: bool = True) -> list[dict]:
    """Read actions for this actor (manager or rep), default to today only.
    Backward-compat: reads legacy records that used `manager` key as `actor`.
    """
    if not ACTION_LOG_FILE.exists():
        return []
    today = _today_str() if today_only else None
    out = []
    with ACTION_LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            record_actor = record.get("actor") or record.get("manager")
            if record_actor != actor:
                continue
            if today and record.get("date") != today:
                continue
            out.append(record)
    return out


def acted_opp_ids(actor: str) -> set[str]:
    """Set of opportunity_ids the actor has acted on today (done/defer/skip/help_request).
    Help requests count as "acted" — rep escalated, brief moves on, manager picks it up.
    """
    out = set()
    for a in load_actions(actor):
        if a["type"] in (ACTION_MUST_ACT_DONE, ACTION_MUST_ACT_DEFER, ACTION_MUST_ACT_SKIP, ACTION_REP_HELP_REQUEST):
            opp = a.get("opp_id")
            if opp:
                out.add(opp)
    return out


def pending_help_requests_for_manager(manager: str, today_only: bool = True) -> list[dict]:
    """Cross-actor query — find rep help requests routed to this manager
    that haven't been acknowledged or dismissed yet.

    Reads ALL actions (not filtered by actor), then matches by `manager` field
    on the request payload and checks for subsequent ACK/DISMISS records.
    """
    if not ACTION_LOG_FILE.exists():
        return []
    today = _today_str() if today_only else None

    requests = []
    resolutions = set()  # opp_ids that have been ACK'd or DISMISSED

    with ACTION_LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if today and rec.get("date") != today:
                continue
            t = rec.get("type")
            if t == ACTION_REP_HELP_REQUEST and rec.get("manager") == manager:
                requests.append(rec)
            elif t in (ACTION_MANAGER_HELP_ACK, ACTION_MANAGER_HELP_DISMISSED):
                opp = rec.get("opp_id")
                if opp:
                    resolutions.add(opp)

    return [r for r in requests if r.get("opp_id") not in resolutions]


def coaching_note_sent_for(actor: str) -> dict[str, dict]:
    """Map rep_name → {ts, note} for coaching notes already sent today."""
    out = {}
    for a in load_actions(actor):
        if a["type"] == ACTION_COACHING_NOTE_SENT:
            rep = a.get("rep")
            if rep:
                out[rep] = {"ts": a["ts"], "note": a.get("note", "")}
    return out


def redistribution_decisions(actor: str) -> dict[str, str]:
    """Map opp_id → decision ('approved' | 'rejected') for redistribution suggestions."""
    out = {}
    for a in load_actions(actor):
        if a["type"] == ACTION_REDISTRIBUTION_APPROVED:
            out[a.get("opp_id")] = "approved"
        elif a["type"] == ACTION_REDISTRIBUTION_REJECTED:
            out[a.get("opp_id")] = "rejected"
    return out


def pattern_decisions(actor: str) -> dict[str, str]:
    """Map pattern category → decision ('ack' | 'escalate' | 'dismiss') for today's responses."""
    out = {}
    for a in load_actions(actor):
        if a["type"] == ACTION_PATTERN_ACK:
            out[a.get("category")] = "ack"
        elif a["type"] == ACTION_PATTERN_ESCALATE:
            out[a.get("category")] = "escalate"
        elif a["type"] == ACTION_PATTERN_DISMISS:
            out[a.get("category")] = "dismiss"
    return out


def summary_today(actor: str) -> dict[str, int]:
    """Counter for must-act actions taken today, for the brief header."""
    actions = load_actions(actor)
    return {
        "done": sum(1 for a in actions if a["type"] == ACTION_MUST_ACT_DONE),
        "defer": sum(1 for a in actions if a["type"] == ACTION_MUST_ACT_DEFER),
        "skip": sum(1 for a in actions if a["type"] == ACTION_MUST_ACT_SKIP),
        "help_requested": sum(1 for a in actions if a["type"] == ACTION_REP_HELP_REQUEST),
        "coaching_notes_sent": sum(1 for a in actions if a["type"] == ACTION_COACHING_NOTE_SENT),
        "redistribution_approved": sum(1 for a in actions if a["type"] == ACTION_REDISTRIBUTION_APPROVED),
        "redistribution_rejected": sum(1 for a in actions if a["type"] == ACTION_REDISTRIBUTION_REJECTED),
        "help_acknowledged": sum(1 for a in actions if a["type"] == ACTION_MANAGER_HELP_ACK),
        "help_dismissed": sum(1 for a in actions if a["type"] == ACTION_MANAGER_HELP_DISMISSED),
        "patterns_acknowledged": sum(1 for a in actions if a["type"] == ACTION_PATTERN_ACK),
        "patterns_escalated": sum(1 for a in actions if a["type"] == ACTION_PATTERN_ESCALATE),
        "patterns_dismissed": sum(1 for a in actions if a["type"] == ACTION_PATTERN_DISMISS),
    }
