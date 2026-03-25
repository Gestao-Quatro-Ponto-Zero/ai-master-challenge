#!/usr/bin/env python3
"""Flask UI para o protótipo de triagem assistida (Challenge 002).

Stack simples: Flask + HTML/CSS/JS estático.
Carrega Dataset 2, treina o classificador existente e expõe endpoints
para listar tickets, detalhar, testar texto manual e registrar ações locais.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, render_template, request

from ticket_intelligence import (
    build_similarity_index,
    clean_text_data,
    load_dataset2,
    predict_ticket,
    recommend_next_action,
    train_baseline_classifier,
)

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parents[1]

# Configuração de categorias sensíveis e grupos com confusão recorrente
SENSITIVE_CATEGORIES = {"Access", "Administrative rights", "Purchase"}
CONFUSION_PRONE = {"Hardware", "HR Support", "Miscellaneous"}

# Sugerir donos/squads por categoria para roteamento
OWNER_MAP = {
    "Hardware": "Workplace / Devices",
    "HR Support": "People Ops",
    "Access": "Security / IAM",
    "Administrative rights": "Security / IAM",
    "Purchase": "Procurement / Finance Ops",
    "Storage": "Infra / Storage",
    "Internal Project": "PMO",
    "Miscellaneous": "L1 General Support",
}


@dataclass
class TicketView:
    id: int
    text: str
    summary: str
    predicted: str
    confidence: float
    action: str
    sensitivity: bool
    risk_reason: str
    owner: str
    similar: List[Dict[str, str]]


def choose_action(pred_label: str, confidence: float, sensitivity: bool) -> str:
    """Regra operacional pedida: >=0.75 auto-route se não sensível; 0.55-0.75 review; <0.55 escalate."""
    if confidence < 0.55:
        return "Escalate"
    if sensitivity:
        return "Human review"
    if confidence >= 0.75:
        return "Auto-route"
    return "Human review"


def risk_flag(pred_label: str, confidence: float) -> (bool, str):
    if pred_label in SENSITIVE_CATEGORIES:
        return True, "Categoria sensível (acesso/permissão/financeiro)."
    if pred_label in CONFUSION_PRONE and confidence < 0.8:
        return True, "Classe com confusão histórica; revisar."
    return False, ""


def build_ticket_store(df, model, sim_index, sample_size: int = 50) -> Dict[int, TicketView]:
    sample_idx = random.Random(42).sample(range(len(df)), k=min(sample_size, len(df)))
    store: Dict[int, TicketView] = {}
    for idx in sample_idx:
        text = df.loc[idx, "text"]
        res = predict_ticket(text, model, sim_index, top_k=3)
        sensitive, reason = risk_flag(res["prediction"], res["confidence"])
        action = choose_action(res["prediction"], res["confidence"], sensitive)
        owner = OWNER_MAP.get(res["prediction"], "L1 Support")
        summary = text[:140] + ("..." if len(text) > 140 else "")
        store[idx] = TicketView(
            id=idx,
            text=text,
            summary=summary,
            predicted=res["prediction"],
            confidence=res["confidence"],
            action=action,
            sensitivity=sensitive,
            risk_reason=reason,
            owner=owner,
            similar=res["similar"],
        )
    return store


# ---------- Bootstrap do modelo e dados ----------
print("[UI] Carregando dataset e treinando modelo...")
df_raw = load_dataset2()
df = clean_text_data(df_raw)
model, _, _ = train_baseline_classifier(df)
sim_index = build_similarity_index(model, corpus=df["text"].tolist(), labels=df["label"].tolist())
ticket_store = build_ticket_store(df, model, sim_index, sample_size=100)
print(f"[UI] Tickets pré-carregados para UI: {len(ticket_store)}")


app = Flask(__name__, template_folder=str(APP_DIR / "templates"), static_folder=str(APP_DIR / "static"))


@app.route("/")
def home():
    stats = {
        "total": len(df),
        "classes": df["label"].nunique(),
        "macro_f1": 0.853,
        "accuracy": 0.855,
    }
    return render_template("index.html", stats=stats)


@app.route("/api/stats")
def api_stats():
    action_counts = {}
    cat_counts = {}
    for t in ticket_store.values():
        action_counts[t.action] = action_counts.get(t.action, 0) + 1
        cat_counts[t.predicted] = cat_counts.get(t.predicted, 0) + 1
    return jsonify({
        "total": len(ticket_store),
        "by_action": action_counts,
        "by_category": cat_counts,
    })


@app.route("/api/tickets")
def list_tickets():
    tickets = []
    for t in ticket_store.values():
        payload = {
            "id": t.id,
            "summary": t.summary,
            "predicted": t.predicted,
            "confidence": t.confidence,
            "action": t.action,
            "sensitivity": t.sensitivity,
            "risk_reason": t.risk_reason,
            "owner": t.owner,
        }
        tickets.append(payload)
    # ordenar por ação (escalate > review > auto) e confiança desc
    priority = {"Escalate": 0, "Human review": 1, "Auto-route": 2}
    tickets = sorted(tickets, key=lambda x: (priority[x["action"]], -x["confidence"]))
    return jsonify(tickets)


@app.route("/api/tickets/<int:ticket_id>")
def ticket_detail(ticket_id: int):
    t = ticket_store.get(ticket_id)
    if not t:
        return jsonify({"error": "ticket not found"}), 404
    rec = recommend_next_action(t.predicted, t.confidence)
    return jsonify(
        {
            "id": t.id,
            "text": t.text,
            "predicted": t.predicted,
            "confidence": t.confidence,
            "action": t.action,
            "sensitivity": t.sensitivity,
            "risk_reason": t.risk_reason,
            "owner": t.owner,
            "recommendation": rec,
            "justification": f"{t.predicted} com confiança {t.confidence:.0%}. {t.risk_reason or 'Aplicar regra padrão de limiar.'}",
            "similar": t.similar,
        }
    )


@app.route("/api/predict", methods=["POST"])
def manual_predict():
    data = request.get_json() or {}
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"error": "texto vazio"}), 400
    res = predict_ticket(text, model, sim_index, top_k=5)
    sensitive, reason = risk_flag(res["prediction"], res["confidence"])
    action = choose_action(res["prediction"], res["confidence"], sensitive)
    owner = OWNER_MAP.get(res["prediction"], "L1 Support")
    return jsonify(
        {
            "predicted": res["prediction"],
            "confidence": res["confidence"],
            "action": action,
            "sensitivity": sensitive,
            "risk_reason": reason,
            "owner": owner,
            "recommendation": recommend_next_action(res["prediction"], res["confidence"]),
            "similar": res["similar"],
        }
    )


@app.route("/api/tickets/<int:ticket_id>/action", methods=["POST"])
def update_action(ticket_id: int):
    t = ticket_store.get(ticket_id)
    if not t:
        return jsonify({"error": "ticket not found"}), 404
    data = request.get_json() or {}
    action = data.get("action")
    if action:
        t.action = action
    sensitive = data.get("sensitivity")
    if sensitive is not None:
        t.sensitivity = bool(sensitive)
    return jsonify({"status": "ok", "action": t.action, "sensitivity": t.sensitivity})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
