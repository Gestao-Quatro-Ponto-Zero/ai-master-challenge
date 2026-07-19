# -*- coding: utf-8 -*-
"""Challenge 002 — Redesign de Suporte · Protótipo funcional (FASE 6, v2).

Rodar:  python app.py            (ou: uvicorn app:app --port 8502)
Abrir:  http://localhost:8502
Preparação completa: python bootstrap.py (dados, baseline inglês e modelo
multilíngue servido). Depois: python app.py.

Arquitetura da v2 (D-017, process-log/decisions.md): o protótipo v1 em
Streamlit atingiu o teto visual da ferramenta; esta versão troca APENAS a
camada de apresentação — FastAPI servindo uma API JSON fina sobre os mesmos
módulos testados (data_prep FASE 2 · roi_model FASE 3 · automation FASE 4 ·
ticket_ai/copilot FASES 5-6) + front artesanal em web/ (HTML/CSS/JS, sem
build, sem CDN em runtime). A primeira versão em Streamlit foi retirada do
pacote final por não participar da execução vigente.

Honestidade herdada: features sintéticas NÃO alimentam nenhum número
(D-005/D-009/D-011); o card de SLA mostra o mecanismo aguardando
instrumentação. Nenhum número é redigitado aqui — tudo é computado dos
módulos-fonte ou dos artefatos de treino (`models/metrics.json` para o
baseline e `models/metrics_ml.json`/`metadata.json` para o modelo servido).
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from src.automation import AUTOMATION_MATRIX_D1, D2_CLASS_ROUTING, NEVER_AUTOMATE_RULES
from src.data_prep import (AGENT_COST_BRL_PER_HOUR, AHT_MIN_BY_CHANNEL,
                           SLA_TARGET_HOURS_BY_PRIORITY, TICKETS_PER_YEAR)
from src.roi_model import (ASSIST_AHT_REDUCTION, DEFLECTION_BY_TYPE, RAMP_UP_YEAR1,
                           SOLUTION_RUN_COST_PER_TICKET_BRL,
                           break_even_deflection, roi_business_scenario, roi_scenario,
                           sensitivity_tornado, workload_by_segment)

ROOT = Path(__file__).resolve().parent
SAT = "Customer Satisfaction Rating"

app = FastAPI(title="Redesign de Suporte — Protótipo", docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware,
                   secret_key=os.getenv("PAUTA_SECRET", "demo-secret-trocar-no-deploy"),
                   same_site="lax")

# Perfis de demonstração (trocar via env no deploy) — D-018
DEMO_PASSWORDS = {
    "admin": os.getenv("ADMIN_PASSWORD", "admin123"),
    "cliente": os.getenv("CLIENT_PASSWORD", "cliente123"),
}


def _require(request: Request, *roles: str) -> str:
    role = request.session.get("role")
    if role not in roles:
        raise HTTPException(status_code=401, detail="não autenticado para este perfil")
    return role

# ===========================================================================
# Dados e modelos (carga na inicialização; IA aquecida em thread)
# ===========================================================================

D1 = pd.read_parquet(ROOT / "data/processed/tickets_features.parquet")
CLOSED = D1[D1["is_closed"]]
METRICS = json.loads((ROOT / "models/metrics.json").read_text(encoding="utf-8"))

_AI = None
_AI_READY = threading.Event()

# ---------------------------------------------------------------------------
# Chamados + base de conhecimento (SQLite) — loop de aprendizado do portal
# ---------------------------------------------------------------------------
DB_PATH = ROOT / "data" / "app.db"

_KB_LOCK = threading.Lock()
_KB_VECS: np.ndarray | None = None    # (n, dim) embeddings das resoluções validadas
_KB_ROWS: list[dict] = []


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    with _db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT, question TEXT, extra TEXT, answer_shown TEXT,
            category TEXT, confidence REAL, priority TEXT,
            status TEXT DEFAULT 'Aberto', resolution TEXT, resolved_at TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT, problem TEXT, resolution TEXT, category TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT, kind TEXT, category TEXT)""")


_init_db()


def _kb_append(problem: str, resolution: str, category: str) -> None:
    """Resolução humana validada → vetor no espaço da busca (aprendizado)."""
    global _KB_VECS
    vec = _AI.embed(f"{problem}\n{resolution}")
    with _KB_LOCK:
        _KB_ROWS.append({"problem": problem, "resolution": resolution,
                         "category": category})
        _KB_VECS = vec if _KB_VECS is None else np.vstack([_KB_VECS, vec])


def _kb_search(vec: np.ndarray, k: int = 2, min_sim: float = 0.50) -> list[dict]:
    with _KB_LOCK:
        if _KB_VECS is None or not len(_KB_ROWS):
            return []
        sims = (_KB_VECS @ vec.T).ravel()
        order = np.argsort(sims)[::-1][:k]
        return [{**_KB_ROWS[i], "similarity": round(float(sims[i]), 3)}
                for i in order if sims[i] >= min_sim]


def _warm_ai() -> None:
    """Carrega classificador + FAISS + embedder fora do request path e
    re-embeda a base de conhecimento persistida (SQLite)."""
    global _AI
    from src.ticket_ai import load_ticket_ai
    ai = load_ticket_ai()
    ai.find_similar("warm up query", k=1)  # força a carga do sentence-transformer
    _AI = ai
    rows = _db().execute(
        "SELECT problem, resolution, category FROM knowledge ORDER BY id").fetchall()
    for r in rows:
        _kb_append(r["problem"], r["resolution"], r["category"])
    _AI_READY.set()


threading.Thread(target=_warm_ai, daemon=True).start()


def _clean(x):
    """JSON não tem inf/NaN — converte para None (o front exibe 'nunca'/'—')."""
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    return x


def _scenario_dict(r) -> dict:
    return _clean({k: (float(v) if isinstance(v, (int, float)) else v)
                   for k, v in r.as_dict().items()})


# ===========================================================================
# Payloads pré-computados (dados estáticos da sessão)
# ===========================================================================

def _satisfaction_by(seg: str) -> list[dict]:
    g = (CLOSED.groupby(seg, observed=True)[SAT]
         .agg(["mean", "sem", "count"]).reset_index())
    return [{"label": str(row[seg]), "mean": round(float(row["mean"]), 2),
             "ci95": round(float(row["sem"]) * 1.96, 3), "n": int(row["count"])}
            for _, row in g.iterrows()]


def _automation_table(df: pd.DataFrame) -> list[dict]:
    if not len(df):
        return []
    w = workload_by_segment(df, by=["Ticket Type"])
    rows = []
    for _, r in w.iterrows():
        t = str(r["Ticket Type"])
        defl = DEFLECTION_BY_TYPE[t]["base"]
        defl_hours = float(r["hours_year"]) * defl
        rows.append({
            "type": t,
            "tier": AUTOMATION_MATRIX_D1[t]["tier"],
            "tickets_year": round(float(r["tickets_year"])),
            "hours_year": round(float(r["hours_year"])),
            "deflection_base": defl,
            "deflectable_hours": round(defl_hours),
            "deflectable_brl": round(defl_hours * AGENT_COST_BRL_PER_HOUR["base"]),
        })
    return rows


_WINNER = next(r for r in METRICS["results"] if r["model"] == METRICS["winner"])
_SERVE_META = json.loads((ROOT / "models/metadata.json").read_text(encoding="utf-8"))
_ML_METRICS_FILE = ROOT / "models/metrics_ml.json"
_ML_METRICS = (json.loads(_ML_METRICS_FILE.read_text(encoding="utf-8"))
               if _ML_METRICS_FILE.exists() else None)

BOOTSTRAP = _clean({
    "kpis": {
        "tickets_year": TICKETS_PER_YEAR,
        "sample_size": int(len(D1)),
        "pct_open": round(float(D1["is_open"].mean()) * 100, 1),
        "pct_pending": round(float(D1["is_pending"].mean()) * 100, 1),
        "pct_backlog": round(float(D1["is_unresolved"].mean()) * 100, 1),
        "satisfaction": round(float(CLOSED[SAT].mean()), 2),
        "n_rated": int(len(CLOSED)),
        "pct_detractors": round(float(CLOSED["is_dissatisfied"].mean()) * 100, 1),
    },
    "base_scenario": _scenario_dict(roi_business_scenario(D1, "base")),
    "funnel": [
        {"stage": "Open — sem 1ª resposta", "n": int(D1["is_open"].sum()),
         "tone": "crit", "lever": "triagem + resposta automática"},
        {"stage": "Pending — esperando cliente", "n": int(D1["is_pending"].sum()),
         "tone": "warn", "lever": "follow-up automático + auto-close"},
        {"stage": "Closed — resolvido", "n": int(D1["is_closed"].sum()),
         "tone": "good", "lever": None},
    ],
    "satisfaction_by": {
        "Ticket Channel": _satisfaction_by("Ticket Channel"),
        "Ticket Type": _satisfaction_by("Ticket Type"),
        "Ticket Priority": _satisfaction_by("Ticket Priority"),
    },
    "scenarios": {name: _scenario_dict(roi_business_scenario(D1, name))
                  for name in ("conservador", "base", "otimista")},
    # Cenários de ECONOMIA (D-019): variam só a performance da automação
    # (deflexão + assistência low/base/high); operação e custo/h ficam no base.
    # Sem implantação: construção interna pelo AI Master (premissa desta proposta).
    "savings_scenarios": {
        name: _scenario_dict(roi_scenario(
            D1, "base",
            deflection_by_type={t: v[lvl] for t, v in DEFLECTION_BY_TYPE.items()},
            assist_reduction=ASSIST_AHT_REDUCTION[lvl],
        )) for name, lvl in (("conservador", "low"), ("base", "base"),
                             ("otimista", "high"))
    },
    "automation_table": _automation_table(D1),
    "automation_matrix": {t: {"tier": m["tier"], "automatiza": m["automatiza"],
                              "nunca_automatiza": m["nunca_automatiza"],
                              "justificativa": m["justificativa"],
                              "criteria": m["criteria"],
                              "deflection": DEFLECTION_BY_TYPE[t]}
                          for t, m in AUTOMATION_MATRIX_D1.items()},
    "veto_rules": NEVER_AUTOMATE_RULES,
    "sla_targets": SLA_TARGET_HOURS_BY_PRIORITY,
    "tornado": sensitivity_tornado(D1).to_dict(orient="records"),
    "break_even_deflection": round(break_even_deflection(D1), 3),
    "roi_defaults": {
        "tickets_year": TICKETS_PER_YEAR,
        "agent_cost_hour": AGENT_COST_BRL_PER_HOUR["base"],
        "assist_reduction": ASSIST_AHT_REDUCTION["base"],
        "ramp_up_year1": RAMP_UP_YEAR1["base"],
        "run_cost_per_ticket": SOLUTION_RUN_COST_PER_TICKET_BRL["base"],
        "deflection_by_type": {t: v["base"] for t, v in DEFLECTION_BY_TYPE.items()},
        "aht_by_channel": {c: v["base"] for c, v in AHT_MIN_BY_CHANNEL.items()},
    },
    "model_card": {
        "serving": {
            "type": _SERVE_META.get("classifier_type", "tfidf_logreg"),
            "embedder": _SERVE_META.get("embedder"),
            "threshold": _SERVE_META.get("threshold"),
            "f1_macro": (_ML_METRICS or {}).get("f1_macro"),
            "multilingual": "multilingual" in str(_SERVE_META.get("embedder", "")),
        },
        "winner": METRICS["winner"],
        "accuracy": round(_WINNER["accuracy"], 4),
        "f1_macro": round(_WINNER["f1_macro"], 4),
        "precision_macro": round(_WINNER["precision_macro"], 4),
        "recall_macro": round(_WINNER["recall_macro"], 4),
        "threshold": METRICS["threshold"],
        "corpus_size": 47_823,
        "comparison": [{k: (round(v, 4) if isinstance(v, float) else v)
                        for k, v in r.items() if k in
                        ("model", "accuracy", "f1_macro", "precision_macro", "recall_macro")}
                       for r in METRICS["results"]],
        "per_class": {cls: {"f1": round(d["f1-score"], 3), "support": int(d["support"])}
                      for cls, d in _WINNER["per_class"].items()
                      if cls in D2_CLASS_ROUTING},
    },
    "routing": D2_CLASS_ROUTING,
    "filters": {
        "channel": sorted(D1["Ticket Channel"].astype(str).unique().tolist()),
        "type": sorted(D1["Ticket Type"].astype(str).unique().tolist()),
        "priority": ["Low", "Medium", "High", "Critical"],
        "status": sorted(D1["Ticket Status"].astype(str).unique().tolist()),
    },
    "copilot_examples": [
        {"label": "Reset de senha — automação plena (Access)",
         "text": "Não consigo entrar na minha conta desde hoje cedo, parece que a senha "
                 "expirou. Preciso do reset o quanto antes, tenho um prazo hoje."},
        {"label": "Status de compra — confiança baixa (Purchase)",
         "text": "Qual o status do pedido de compra 4512? A cotação já foi aprovada "
                 "pelo financeiro?"},
        {"label": "Disco cheio — self-healing (Storage)",
         "text": "Estou sem espaço no drive compartilhado, preciso de mais cota para "
                 "salvar os arquivos do projeto."},
        {"label": "Cliente irritado + advogado — VETO (humano)",
         "text": "Isso é inaceitável. Terceira vez que reporto essa cobrança não autorizada "
                 "e ninguém resolve. Se não resolverem hoje vou procurar meu advogado."},
        {"label": "Pedido vago — gate de confiança",
         "text": "oi, sobre aquilo que a gente conversou, consegue dar uma olhada?"},
    ],
})


# ===========================================================================
# API
# ===========================================================================

@app.get("/api/bootstrap")
def bootstrap(request: Request) -> dict:
    _require(request, "admin")
    return BOOTSTRAP


@app.get("/api/health")
def health() -> dict:
    return {"ready": _AI_READY.is_set()}


@app.get("/api/operational")
def operational(request: Request,
                channel: list[str] = Query(default=[]),
                type: list[str] = Query(default=[]),
                priority: list[str] = Query(default=[]),
                status: list[str] = Query(default=[])) -> dict:
    _require(request, "admin")
    df = D1
    if channel:
        df = df[df["Ticket Channel"].astype(str).isin(channel)]
    if type:
        df = df[df["Ticket Type"].astype(str).isin(type)]
    if priority:
        df = df[df["Ticket Priority"].astype(str).isin(priority)]
    if status:
        df = df[df["Ticket Status"].astype(str).isin(status)]
    rated = df[df["is_closed"]]

    vol = df.groupby("Ticket Type", observed=True).size()
    backlog = (df.groupby("Ticket Channel", observed=True)[["is_open", "is_pending"]]
               .mean() * 100) if len(df) else pd.DataFrame(columns=["is_open", "is_pending"])

    sample_cols = ["Ticket ID", "Ticket Type", "Ticket Channel", "Ticket Priority",
                   "Ticket Status", "Ticket Subject", SAT]
    sample = [{"id": int(r["Ticket ID"]), "type": str(r["Ticket Type"]),
               "channel": str(r["Ticket Channel"]), "priority": str(r["Ticket Priority"]),
               "status": str(r["Ticket Status"]), "subject": str(r["Ticket Subject"]),
               "satisfaction": (None if pd.isna(r[SAT]) else int(r[SAT]))}
              for _, r in df[sample_cols].head(200).iterrows()]

    return _clean({
        "n": int(len(df)),
        "n_total": int(len(D1)),
        "pct_backlog": round(float(df["is_unresolved"].mean()) * 100, 1) if len(df) else None,
        "satisfaction": round(float(rated[SAT].mean()), 2) if len(rated) else None,
        "n_rated": int(len(rated)),
        "hours_year": round(float(df["est_handle_minutes"].sum()) / 60
                            * (TICKETS_PER_YEAR / len(D1))) if len(df) else 0,
        "volume_by_type": [{"label": str(k), "n": int(v)} for k, v in vol.items()],
        "backlog_by_channel": [{"label": str(k), "open": round(float(r["is_open"]), 1),
                                "pending": round(float(r["is_pending"]), 1)}
                               for k, r in backlog.iterrows()],
        "automation_table": _automation_table(df),
        "tickets": sample,
    })


class CopilotIn(BaseModel):
    text: str


@app.post("/api/copilot")
def copilot(inp: CopilotIn, request: Request) -> dict:
    _require(request, "admin")
    if not _AI_READY.is_set():
        return {"warming": True}
    from src.copilot import analyze
    r = analyze(inp.text, _AI)
    return _clean({
        "warming": False,
        "classification": {
            "label": r["classification"]["label"],
            "confidence": float(r["classification"]["confidence"]),
            "auto_ok": bool(r["classification"]["auto_ok"]),
            "conf_ok": bool(r["classification"]["conf_ok"]),
            "evidence": float(r["classification"]["evidence"]),
            "evidence_ok": bool(r["classification"]["evidence_ok"]),
            "top3": [[c, float(p)] for c, p in r["classification"]["top3"]],
        },
        "priority": r["priority"],
        "vetoes": r["vetoes"],
        "routing": r["routing"],
        "recommendation": r["recommendation"],
        "similar": [{"doc_id": int(s["doc_id"]), "text": str(s["Document"]),
                     "topic": str(s["Topic_group"]), "similarity": round(float(s["similarity"]), 3)}
                    for _, s in r["similar"].iterrows()],
        "suggested_response": r["suggested_response"],
        "threshold": float(_AI.threshold),
    })


class RoiIn(BaseModel):
    tickets_year: float = TICKETS_PER_YEAR
    agent_cost_hour: float = AGENT_COST_BRL_PER_HOUR["base"]
    deflection_scale: float = 1.0     # 1.0 = matriz FASE 4 no nível base
    assist_reduction: float = ASSIST_AHT_REDUCTION["base"]
    ramp_up_year1: float = RAMP_UP_YEAR1["base"]
    run_cost_per_ticket: float = SOLUTION_RUN_COST_PER_TICKET_BRL["base"]


@app.post("/api/roi")
def roi(inp: RoiIn, request: Request) -> dict:
    _require(request, "admin")
    defl = {t: min(0.95, v["base"] * inp.deflection_scale)
            for t, v in DEFLECTION_BY_TYPE.items()}
    r = roi_scenario(
        D1, "base",
        tickets_year=inp.tickets_year,
        agent_cost_hour=inp.agent_cost_hour,
        deflection_by_type=defl,
        assist_reduction=inp.assist_reduction,
        ramp_up_year1=inp.ramp_up_year1,
        run_cost_per_ticket=inp.run_cost_per_ticket,
    )
    out = _scenario_dict(r)
    out["deflection_applied"] = {t: round(v, 3) for t, v in defl.items()}
    return out


# ===========================================================================
# Autenticação — perfis de demonstração (D-018)
# ===========================================================================

class LoginIn(BaseModel):
    role: str
    password: str


@app.post("/api/login")
def login(inp: LoginIn, request: Request) -> dict:
    if inp.role not in DEMO_PASSWORDS or inp.password != DEMO_PASSWORDS[inp.role]:
        raise HTTPException(status_code=401, detail="perfil ou senha inválidos")
    request.session.clear()
    request.session["role"] = inp.role
    return {"role": inp.role}


@app.post("/api/logout")
def logout(request: Request) -> dict:
    request.session.clear()
    return {"ok": True}


@app.get("/api/me")
def me(request: Request) -> dict:
    return {"role": request.session.get("role")}


# ===========================================================================
# Portal do cliente — pergunta → resposta assistida → chamado qualificado
# ===========================================================================

MAX_INPUT_CHARS = 900


class AskIn(BaseModel):
    text: str


@app.post("/api/portal/ask")
def portal_ask(inp: AskIn, request: Request) -> dict:
    _require(request, "cliente", "admin")
    text = inp.text.strip()[:MAX_INPUT_CHARS]
    if not text:
        raise HTTPException(status_code=422, detail="descreva o problema antes de enviar")
    if not _AI_READY.is_set():
        return {"warming": True}
    from src.copilot import (PORTAL_PLAYBOOK, SIM_EVIDENCE_FLOOR, detect_vetoes,
                             suggest_priority)
    cls = _AI.classify(text)
    vetoes = detect_vetoes(text)
    prio = suggest_priority(text)
    if vetoes and prio["priority"] in ("Low", "Medium"):
        prio = {"priority": "High", "reason": "elevada por regra de veto (FASE 4 §3)",
                "method": "regra"}
    vec = _AI.embed(text)
    kb = _kb_search(vec, k=2)
    scores, idx = _AI.index.search(vec, 3)
    similar = [{"text": str(_AI.corpus.iloc[i]["Document"])[:180],
                "topic": str(_AI.corpus.iloc[i]["Topic_group"]),
                "similarity": round(float(s), 3)}
               for s, i in zip(scores[0], idx[0])]
    evidence = similar[0]["similarity"] if similar else 0.0

    if vetoes:
        mode = "veto"           # humano com prioridade — sem autoatendimento
    elif not cls["auto_ok"] or evidence < SIM_EVIDENCE_FLOOR:
        mode = "low_conf"       # dupla trava: gate de confiança + piso de evidência
    else:
        mode = "selfservice"
    playbook = PORTAL_PLAYBOOK.get(cls["label"], PORTAL_PLAYBOOK["Miscellaneous"])

    request.session["last_ask"] = {
        "question": text,
        "category": cls["label"],
        "confidence": round(float(cls["confidence"]), 3),
        "priority": prio["priority"],
        "answer": playbook if mode == "selfservice" else "",
    }
    return _clean({
        "warming": False,
        "mode": mode,
        "category": cls["label"],
        "confidence": float(cls["confidence"]),
        "threshold": float(_AI.threshold),
        "priority": prio["priority"],
        "vetoes": vetoes,
        "playbook": playbook,
        "kb": kb,
        "similar": similar,
    })


class TicketIn(BaseModel):
    extra: str = ""


@app.post("/api/portal/ticket")
def portal_ticket(inp: TicketIn, request: Request) -> dict:
    _require(request, "cliente", "admin")
    last = request.session.get("last_ask")
    if not last:
        raise HTTPException(status_code=422,
                            detail="descreva o problema antes de abrir o chamado")
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO tickets (created_at, question, extra, answer_shown, "
            "category, confidence, priority) VALUES (?,?,?,?,?,?,?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), last["question"],
             inp.extra.strip()[:MAX_INPUT_CHARS], last.get("answer", ""),
             last["category"], last["confidence"], last["priority"]))
        tid = cur.lastrowid
    return {"id": int(tid), "category": last["category"], "priority": last["priority"]}


class FeedbackIn(BaseModel):
    helped: bool = True


@app.post("/api/portal/feedback")
def portal_feedback(inp: FeedbackIn, request: Request) -> dict:
    _require(request, "cliente", "admin")
    if inp.helped:
        last = request.session.get("last_ask") or {}
        with _db() as conn:
            conn.execute("INSERT INTO events (created_at, kind, category) VALUES (?,?,?)",
                         (datetime.now().strftime("%Y-%m-%d %H:%M"), "deflected",
                          last.get("category")))
    return {"ok": True}


# ===========================================================================
# Fila de chamados (admin) — resolução humana alimenta a base de conhecimento
# ===========================================================================

@app.get("/api/admin/queue")
def admin_queue(request: Request) -> dict:
    _require(request, "admin")
    conn = _db()
    tickets = [dict(r) for r in conn.execute(
        "SELECT * FROM tickets ORDER BY (status = 'Aberto') DESC, id DESC LIMIT 100")]
    kb = [dict(r) for r in conn.execute(
        "SELECT * FROM knowledge ORDER BY id DESC LIMIT 50")]
    deflected = conn.execute(
        "SELECT COUNT(*) c FROM events WHERE kind = 'deflected'").fetchone()["c"]
    open_n = conn.execute(
        "SELECT COUNT(*) c FROM tickets WHERE status = 'Aberto'").fetchone()["c"]
    closed_n = conn.execute(
        "SELECT COUNT(*) c FROM tickets WHERE status = 'Resolvido'").fetchone()["c"]
    conn.close()
    return {"tickets": tickets, "kb": kb,
            "stats": {"open": int(open_n), "resolved": int(closed_n),
                      "deflected": int(deflected), "kb_count": len(kb)}}


class ResolveIn(BaseModel):
    ticket_id: int
    resolution: str


@app.post("/api/admin/resolve")
def admin_resolve(inp: ResolveIn, request: Request) -> dict:
    _require(request, "admin")
    resolution = inp.resolution.strip()
    if len(resolution) < 10:
        raise HTTPException(status_code=422,
                            detail="descreva a resolução com mais detalhe (mín. 10 caracteres)")
    row = _db().execute("SELECT question, category, status FROM tickets WHERE id = ?",
                        (inp.ticket_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="chamado não encontrado")
    if row["status"] != "Aberto":
        raise HTTPException(status_code=409, detail="chamado já resolvido")
    with _db() as conn:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn.execute("UPDATE tickets SET status='Resolvido', resolution=?, resolved_at=? "
                     "WHERE id=?", (resolution, now, inp.ticket_id))
        conn.execute("INSERT INTO knowledge (created_at, problem, resolution, category) "
                     "VALUES (?,?,?,?)", (now, row["question"], resolution, row["category"]))
    if _AI_READY.is_set():
        _kb_append(row["question"], resolution, row["category"])
    return {"ok": True}


# Front estático (depois das rotas /api para não capturá-las)
app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")


@app.exception_handler(404)
async def spa_fallback(request, exc):
    """Rotas de view caem no index; 404 real só para /api."""
    if request.url.path.startswith("/api"):
        return JSONResponse({"detail": "not found"}, status_code=404)
    return FileResponse(ROOT / "web/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8502)
