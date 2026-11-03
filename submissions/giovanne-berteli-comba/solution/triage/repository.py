"""Atomic SQLite runs/metrics, idempotent requests and append-only review events."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import uuid

from .core import CLASSES, METRICS


def now():
    return datetime.now(timezone.utc).isoformat()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


class RequestConflict(ValueError):
    pass


class Repository:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY, text_hash TEXT NOT NULL, original_text TEXT,
                    raw_chars INTEGER, normalized_chars INTEGER);
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY, request_id TEXT NOT NULL UNIQUE,
                    case_id TEXT NOT NULL REFERENCES cases(case_id), created_at TEXT NOT NULL,
                    fingerprint TEXT NOT NULL, result_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS metrics (
                    run_id TEXT NOT NULL REFERENCES runs(run_id), metric TEXT NOT NULL,
                    status TEXT NOT NULL, direction TEXT, reason TEXT NOT NULL, category TEXT,
                    model_version TEXT, initial_review TEXT NOT NULL, record_json TEXT NOT NULL,
                    PRIMARY KEY (run_id, metric));
                CREATE TABLE IF NOT EXISTS reviews (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
                    run_id TEXT NOT NULL REFERENCES runs(run_id), metric TEXT,
                    decision TEXT NOT NULL, corrected_category TEXT, reviewer TEXT NOT NULL,
                    reviewer_type TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS review_target ON reviews(run_id, metric, seq);
            """)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=3)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def lookup(self, request_id, fingerprint):
        with self.connect() as connection:
            row = connection.execute("SELECT fingerprint,result_json FROM runs WHERE request_id=?", (request_id,)).fetchone()
        if row is None:
            return None
        if row["fingerprint"] != fingerprint:
            raise RequestConflict("Request ID already belongs to a different input")
        return json.loads(row["result_json"])

    def save(self, result, original_text, raw_chars, normalized_chars, fingerprint):
        if {item["metric"] for item in result["metrics"]} != set(METRICS) or len(result["metrics"]) != 2:
            raise ValueError("Exactly two metric records required")
        saved = {**result, "persisted": True}
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            previous = connection.execute("SELECT fingerprint,result_json FROM runs WHERE request_id=?", (result["request_id"],)).fetchone()
            if previous:
                if previous["fingerprint"] != fingerprint:
                    raise RequestConflict("Conflicting request delivery")
                return json.loads(previous["result_json"])
            case = connection.execute("SELECT text_hash FROM cases WHERE case_id=?", (result["case_id"],)).fetchone()
            if case and case["text_hash"] != result["text_sha256"]:
                raise RequestConflict("Case ID already belongs to different text")
            if not case:
                connection.execute("INSERT INTO cases VALUES (?,?,?,?,?)",
                                   (result["case_id"], result["text_sha256"], original_text, raw_chars, normalized_chars))
            connection.execute("INSERT INTO runs VALUES (?,?,?,?,?,?)",
                               (result["run_id"], result["request_id"], result["case_id"], result["created_at"], fingerprint, encode(saved)))
            for item in result["metrics"]:
                connection.execute("INSERT INTO metrics VALUES (?,?,?,?,?,?,?,?,?)",
                                   (result["run_id"], item["metric"], item["status"], item["direction"], item["reason"],
                                    item["category"], result["model_version"],
                                    "not_required" if item["status"] == "ordinary" else "pending", encode(item)))
        return saved

    def list_runs(self, limit=100):
        if not 1 <= limit <= 1000:
            raise ValueError("Limit must be 1..1000")
        with self.connect() as connection:
            return [json.loads(row[0]) for row in connection.execute("SELECT result_json FROM runs ORDER BY rowid DESC LIMIT ?", (limit,))]

    def get_run(self, run_id):
        with self.connect() as connection:
            row = connection.execute("SELECT r.result_json,c.original_text FROM runs r JOIN cases c USING(case_id) WHERE run_id=?", (run_id,)).fetchone()
            if row is None:
                raise ValueError("Unknown run")
            events = [json.loads(item[0]) for item in connection.execute("SELECT payload_json FROM reviews WHERE run_id=? ORDER BY seq", (run_id,))]
        return {"result": json.loads(row["result_json"]), "original_text": row["original_text"], "reviews": events}

    def filter_metrics(self, **filters):
        allowed = {"status": "m.status", "direction": "m.direction", "reason": "m.reason",
                   "category": "m.category", "metric": "m.metric", "model_version": "m.model_version",
                   "review_state": "latest_review"}
        if set(filters) - set(allowed):
            raise ValueError("Unknown filter")
        query = """SELECT m.*, r.case_id, r.created_at,
                   COALESCE((SELECT decision FROM reviews v WHERE v.run_id=m.run_id AND v.metric=m.metric ORDER BY seq DESC LIMIT 1),m.initial_review) AS latest_review
                   FROM metrics m JOIN runs r USING(run_id)"""
        clauses, values = [], []
        for name, value in filters.items():
            if value is not None:
                clauses.append(f"{allowed[name]}=?")
                values.append(value)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY r.rowid DESC,m.metric"
        with self.connect() as connection:
            return [{**json.loads(row["record_json"]), "run_id": row["run_id"], "case_id": row["case_id"],
                     "created_at": row["created_at"], "model_version": row["model_version"],
                     "review_state": row["latest_review"]} for row in connection.execute(query, values)]

    def review(self, run_id, decision, reviewer, reason, metric=None, corrected_category=None,
               reviewer_type="operator_declared", event_id=None):
        if reviewer_type not in {"operator_declared", "automated_test"} or not reviewer.strip() or not reason.strip():
            raise ValueError("Reviewer type, label and reason required")
        if len(reviewer) > 120 or len(reason) > 2000:
            raise ValueError("Review fields too long")
        allowed = {"pending", "accepted", "corrected", "deferred"} if metric is None else {"pending", "confirmed_valid", "confirmed_issue", "deferred"}
        if metric not in (None, *METRICS) or decision not in allowed:
            raise ValueError("Invalid review target/decision")
        run = self.get_run(run_id)["result"]
        if decision == "corrected":
            if run["context"] != "it_service_en" or corrected_category not in CLASSES:
                raise ValueError("Correction requires an IT category and context")
        elif corrected_category is not None:
            raise ValueError("Only corrections may carry a corrected category")
        payload = {"event_id": event_id or str(uuid.uuid4()), "run_id": run_id, "metric": metric,
                   "decision": decision, "corrected_category": corrected_category, "reviewer": reviewer.strip(),
                   "reviewer_type": reviewer_type, "reason": reason.strip()}
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            previous = connection.execute("SELECT payload_json FROM reviews WHERE event_id=?", (payload["event_id"],)).fetchone()
            if previous:
                saved = json.loads(previous[0])
                if {k: v for k, v in saved.items() if k != "created_at"} != payload:
                    raise RequestConflict("Review event ID conflict")
                return saved
            payload["created_at"] = now()
            connection.execute("INSERT INTO reviews(event_id,run_id,metric,decision,corrected_category,reviewer,reviewer_type,reason,created_at,payload_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                               tuple(payload[key] for key in ("event_id", "run_id", "metric", "decision", "corrected_category", "reviewer", "reviewer_type", "reason", "created_at")) + (encode(payload),))
        return payload
