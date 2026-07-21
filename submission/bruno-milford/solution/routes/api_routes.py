from __future__ import annotations

import csv
from io import StringIO

from flask import Blueprint, Response, jsonify, request

from services.account_service import get_account_detail, list_accounts
from services.churn_service import get_churn_reasons, get_churn_segments, get_churn_timeline
from services.dashboard_service import (
    get_filter_options,
    get_kpis,
    get_reactivation,
    get_revenue,
    get_support,
    get_usage,
    normalize_filters,
)
from services.database_service import response_payload, validate_database
from services.risk_service import get_risk_accounts


api_bp = Blueprint("api", __name__)


def _filters():
    return request.args.to_dict(flat=True)


@api_bp.get("/health")
def health():
    validate_database()
    return jsonify(response_payload({"status": "ok", "database": "available"}))


@api_bp.get("/filters")
def filters():
    return jsonify(response_payload(get_filter_options()))


@api_bp.get("/kpis")
def kpis():
    filters = normalize_filters(_filters())
    data = get_kpis(filters)
    risks = get_risk_accounts(filters)
    data["high_risk_accounts"] = sum(1 for item in risks if item["risk_score"] >= 60 and item["status"] == "ativa")
    return jsonify(response_payload(data, filters))


@api_bp.get("/churn/timeline")
def churn_timeline():
    filters = normalize_filters(_filters())
    return jsonify(response_payload(get_churn_timeline(filters), filters))


@api_bp.get("/churn/reasons")
def churn_reasons():
    filters = normalize_filters(_filters())
    return jsonify(response_payload(get_churn_reasons(filters), filters))


@api_bp.get("/churn/segments")
def churn_segments():
    filters = normalize_filters(_filters())
    return jsonify(response_payload(get_churn_segments(filters), filters))


@api_bp.get("/revenue")
def revenue():
    filters = normalize_filters(_filters())
    return jsonify(response_payload(get_revenue(filters), filters))


@api_bp.get("/usage")
def usage():
    filters = normalize_filters(_filters())
    return jsonify(response_payload(get_usage(filters), filters))


@api_bp.get("/support")
def support():
    filters = normalize_filters(_filters())
    return jsonify(response_payload(get_support(filters), filters))


@api_bp.get("/reactivation")
def reactivation():
    filters = normalize_filters(_filters())
    return jsonify(response_payload(get_reactivation(filters), filters))


@api_bp.get("/risk-accounts")
def risk_accounts():
    filters = normalize_filters(_filters())
    data = get_risk_accounts(filters)
    return jsonify(response_payload({"accounts": data}, filters))


@api_bp.get("/accounts")
def accounts():
    filters = normalize_filters(_filters())
    return jsonify(response_payload({"accounts": list_accounts(_filters())}, filters))


@api_bp.get("/accounts/<account_id>")
def account_detail(account_id: str):
    detail = get_account_detail(account_id)
    if not detail:
        return jsonify({"success": False, "error": "Conta nao encontrada."}), 404
    return jsonify(response_payload(detail))


@api_bp.get("/export/risk-accounts.csv")
def export_risk_accounts():
    filters = normalize_filters(_filters())
    accounts = get_risk_accounts(filters)
    output = StringIO()
    fieldnames = [
        "account_name", "account_id", "industry", "country", "plan_tier", "mrr", "arr",
        "ticket_count", "urgent_tickets", "avg_first_response_minutes", "avg_satisfaction",
        "usage_volume", "errors", "days_since_last_usage", "auto_renew_flag", "downgrade_flag",
        "risk_score", "value_score", "priority_score", "risk_classification", "risk_signals", "status",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(accounts)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=ravenstack_risk_accounts.csv"},
    )
