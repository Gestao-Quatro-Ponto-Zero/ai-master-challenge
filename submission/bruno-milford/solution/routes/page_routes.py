from __future__ import annotations

from flask import Blueprint, abort, render_template

from services.account_service import get_account_detail


page_bp = Blueprint("pages", __name__)


@page_bp.get("/")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")


@page_bp.get("/accounts")
def accounts():
    return render_template("accounts.html", active_page="accounts")


@page_bp.get("/accounts/<account_id>")
def account_detail(account_id: str):
    detail = get_account_detail(account_id)
    if not detail:
        abort(404)
    return render_template("account_detail.html", active_page="accounts", detail=detail)
