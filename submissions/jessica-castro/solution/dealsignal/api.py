"""
DealSignal — REST API

POST /score        — recebe dados de um deal e retorna rating, win_probability,
                     friction, next_action e explanation.
POST /notify-email — envia email com os deals prioritários do pipeline.
GET  /health       — status do servidor e modelo.

Run:
    pip install fastapi uvicorn
    uvicorn api:app --reload --port 8000

Docs interativas: http://localhost:8000/docs
"""

import math
import os
import smtplib
import sys
from contextlib import asynccontextmanager
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr, Field

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from config.constants import RATING_ORDER  # noqa: E402
from engine.next_best_action import (  # noqa: E402
    identify_friction,
    choose_next_action,
    build_deal_narrative,
)
from model.rating_engine import assign_rating, compute_expected_revenue  # noqa: E402
from utils.cache import load_artifact  # noqa: E402
from utils.signals import compute_engine_scores  # noqa: E402


# ── Schemas ────────────────────────────────────────────────────────────────────

class DealInput(BaseModel):
    # Campos obrigatórios
    sales_agent:     str   = Field(..., example="Diego Ferreira")
    product:         str   = Field(..., example="Finance Management")
    effective_value: float = Field(..., gt=0, example=25000.0)
    engage_date:     str   = Field(..., example="2024-10-01",
                                   description="Data do último engajamento (ISO 8601)")
    deal_stage:      str   = Field(..., example="Engaging",
                                   description="Prospecting | Engaging")

    # Overrides opcionais — melhoram a precisão quando disponíveis
    seller_win_rate:         Optional[float] = Field(None, ge=0, le=1)
    product_win_rate:        Optional[float] = Field(None, ge=0, le=1)
    digital_maturity_index:  Optional[float] = Field(None, ge=0, le=1)
    account_size_percentile: Optional[float] = Field(None, ge=0, le=1)
    revenue_per_employee:    Optional[float] = None
    company_age_score:       Optional[float] = None

    # Campos categóricos (target encoding — None usa prior global ~0.40)
    city:               Optional[str] = None
    country:            Optional[str] = None
    lead_source:        Optional[str] = None
    lead_origin:        Optional[str] = None
    lead_quality:       Optional[str] = None
    lead_tag:           Optional[str] = None
    last_activity_type: Optional[str] = None
    office:             Optional[str] = None
    manager:            Optional[str] = None

    # Sinais de engajamento (padrão: scaler mean / neutro)
    lead_quality_score:        Optional[float] = Field(None, ge=0, le=1)
    lead_source_wr:            Optional[float] = Field(None, ge=0, le=1)
    lead_origin_wr:            Optional[float] = Field(None, ge=0, le=1)
    lead_tag_wr:               Optional[float] = Field(None, ge=0, le=1)
    activity_count:            Optional[int]   = None
    has_activity:              Optional[int]   = Field(None, ge=0, le=1)
    last_activity_is_positive: Optional[int]   = Field(None, ge=0, le=1)


class ScoreResponse(BaseModel):
    rating:           str
    win_probability:  float
    expected_revenue: float
    friction:         str
    friction_label:   str
    next_action_key:  str
    next_action:      str
    explanation:      str
    confidence:       str
    engine_scores:    dict


# ── Schemas: /notify-email ──────────────────────────────────────────────────────

class DealSummary(BaseModel):
    account_name:    str
    final_score:     float   = Field(..., ge=0, le=100)
    rating:          str
    friction:        str     = Field(..., description="high | medium | low")
    win_probability: float   = Field(..., ge=0, le=1)
    days_in_stage:   int     = Field(..., ge=0)
    next_action:     str


class NotifyEmailRequest(BaseModel):
    recipients: List[EmailStr]
    deals:      List[DealSummary]


class NotifyEmailResponse(BaseModel):
    status:               str
    priority_deals_count: int
    recipients:           List[str]


class NotifyPreviewRequest(BaseModel):
    deals: List[DealSummary]


# ── Lifespan: carrega artefatos uma vez ao iniciar ─────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    artifacts = ROOT / "model" / "artifacts"
    app.state.model      = load_artifact(str(artifacts / "model.pkl"))
    app.state.scaler     = load_artifact(str(artifacts / "scaler.pkl"))
    app.state.encoder    = load_artifact(str(artifacts / "target_encoder.pkl"))
    app.state.feat_cols  = load_artifact(str(artifacts / "feature_cols.pkl"))
    app.state.ref_df     = pd.read_csv(ROOT / "data" / "results.csv")

    ref = app.state.ref_df
    scaler = app.state.scaler

    # Fallbacks = training means from the scaler (one per feature)
    app.state.fallbacks = dict(zip(scaler.feature_names_in_, scaler.mean_))

    # Reference quantiles for risk flags
    days = ref["days_since_engage"]
    app.state.ref_stats = {
        "p75_days":              days.quantile(0.75),
        "p90_days":              days.quantile(0.90),
        "p95_days":              days.quantile(0.95),
        "p75_load":              ref["seller_pipeline_load"].quantile(0.75),
        "mean_product_win_rate": ref["product_win_rate"].mean(),
        "global_win_rate":       0.40,
        "eff_p33":               ref["effective_value"].quantile(0.33),
        "eff_p67":               ref["effective_value"].quantile(0.67),
    }
    yield


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="DealSignal API",
    description="Score de oportunidades de vendas: recebe dados de um deal e retorna "
                "rating, probabilidade de fechamento, diagnóstico de fricção e próximo passo.",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Feature builder ────────────────────────────────────────────────────────────

def _fb(fallbacks: dict, key: str) -> float:
    """Retorna o training mean do scaler como fallback."""
    return float(fallbacks.get(key, 0.5))


def _build_feature_row(
    inp: DealInput,
    ref_df: pd.DataFrame,
    encoder,
    scaler,
    fallbacks: dict,
    stats: dict,
) -> pd.DataFrame:
    """
    Constrói um DataFrame de 1 linha com os 79 features que o scaler espera:
    V3_V4_NUMERIC (48) + TE (31).
    Computa o que for possível a partir do input; usa training means para o restante.
    """

    # ── Tempo ─────────────────────────────────────────────────────────────────
    try:
        engage = date.fromisoformat(inp.engage_date)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="engage_date deve estar no formato ISO 8601 (ex: 2024-10-01)",
        )
    days         = max(0, (date.today() - engage).days)
    log_days     = math.log1p(days)
    deal_age_pct = float((ref_df["days_since_engage"] < days).mean())

    is_stale          = int(days >= stats["p75_days"])
    is_very_old       = int(days >= stats["p90_days"])
    deal_estagnado    = int(days >= stats["p90_days"])
    deal_muito_antigo = int(days >= stats["p95_days"])

    # bucket_deal_age: 0–30d=0, 30–90d=1, 90–180d=2, >180d=3
    if   days <= 30:  bucket_age = 0.0
    elif days <= 90:  bucket_age = 1.0
    elif days <= 180: bucket_age = 2.0
    else:             bucket_age = 3.0

    # ── Valor ─────────────────────────────────────────────────────────────────
    log_deal_value = math.log1p(inp.effective_value)
    deal_val_pct   = float((ref_df["effective_value"] < inp.effective_value).mean())

    # bucket_deal_value: tertis 0/1/2
    if   inp.effective_value <= stats["eff_p33"]: bucket_val = 0.0
    elif inp.effective_value <= stats["eff_p67"]: bucket_val = 1.0
    else:                                          bucket_val = 2.0

    # ── Vendedor ──────────────────────────────────────────────────────────────
    ag = ref_df[ref_df["sales_agent"] == inp.sales_agent]
    swr = inp.seller_win_rate if inp.seller_win_rate is not None else (
        float(ag["seller_win_rate"].median()) if not ag.empty
        else _fb(fallbacks, "seller_win_rate")
    )
    srp = float(ag["seller_rank_percentile"].median()) if not ag.empty \
        else _fb(fallbacks, "seller_rank_percentile")
    sl  = float(ag["seller_pipeline_load"].median()) if not ag.empty \
        else _fb(fallbacks, "seller_pipeline_load")

    ag_prod = ref_df[
        (ref_df["sales_agent"] == inp.sales_agent) & (ref_df["product"] == inp.product)
    ]
    spe  = float(len(ag_prod))                                  # seller_product_experience
    spwr = swr                                                   # proxy seller_product_win_rate

    # deal_value_percentile_within_seller
    dvps = float((ag["effective_value"] < inp.effective_value).mean()) if not ag.empty else 0.5

    # seller_overloaded_flag
    seller_overloaded = int(sl >= stats["p75_load"])

    # ── Produto ───────────────────────────────────────────────────────────────
    pr = ref_df[ref_df["product"] == inp.product]
    pwr = inp.product_win_rate if inp.product_win_rate is not None else (
        float(pr["product_win_rate"].median()) if not pr.empty
        else _fb(fallbacks, "product_win_rate")
    )
    prp = float(pr["product_rank_percentile"].median()) if not pr.empty \
        else _fb(fallbacks, "product_rank_percentile")

    # deal_value_percentile_within_product
    dvpp = float((pr["effective_value"] < inp.effective_value).mean()) if not pr.empty else 0.5

    # product_avg_sales_cycle — não em results.csv, usa training mean
    pasc = _fb(fallbacks, "product_avg_sales_cycle")

    # product_relative_performance
    prelprf = pwr / (stats["global_win_rate"] + 1e-9)

    # produto_fraco, low_product_performance_flag
    produto_fraco     = int(pwr < stats["mean_product_win_rate"])
    low_prod_perf     = int(prp < 0.33)

    # ── Conta / account ───────────────────────────────────────────────────────
    asp = inp.account_size_percentile if inp.account_size_percentile is not None \
        else _fb(fallbacks, "account_size_percentile")
    dmi = inp.digital_maturity_index if inp.digital_maturity_index is not None \
        else _fb(fallbacks, "digital_maturity_index")
    rpe = inp.revenue_per_employee if inp.revenue_per_employee is not None \
        else _fb(fallbacks, "revenue_per_employee")
    cas = inp.company_age_score if inp.company_age_score is not None \
        else _fb(fallbacks, "company_age_score")

    conta_fraca      = int(asp < 0.33)
    bucket_acct_size = 0.0 if asp < 0.33 else (1.0 if asp < 0.66 else 2.0)
    deal_val_vs_acc  = _fb(fallbacks, "deal_value_vs_account_size")  # sem revenue → proxy

    # ── Interações ────────────────────────────────────────────────────────────
    interact_sp  = swr * pwr
    interact_sv  = swr * deal_val_pct
    interact_pa  = pwr * deal_age_pct
    interact_av  = asp * deal_val_pct

    # ── Lead / engajamento ────────────────────────────────────────────────────
    lead_src_wr   = inp.lead_source_wr      if inp.lead_source_wr      is not None else _fb(fallbacks, "lead_source_wr")
    lead_orig_wr  = inp.lead_origin_wr      if inp.lead_origin_wr      is not None else _fb(fallbacks, "lead_origin_wr")
    lead_tag_wr   = inp.lead_tag_wr         if inp.lead_tag_wr         is not None else _fb(fallbacks, "lead_tag_wr")
    lqs           = inp.lead_quality_score  if inp.lead_quality_score  is not None else _fb(fallbacks, "lead_quality_score")
    act_count     = inp.activity_count      if inp.activity_count      is not None else _fb(fallbacks, "activity_count")
    has_act       = inp.has_activity        if inp.has_activity        is not None else _fb(fallbacks, "has_activity")
    last_act_pos  = inp.last_activity_is_positive if inp.last_activity_is_positive is not None \
        else _fb(fallbacks, "last_activity_is_positive")

    # ── Montar DataFrame numérico (48 colunas) ────────────────────────────────
    numeric_row = {
        # GROUP_SELLER
        "seller_win_rate":                      swr,
        "seller_rank_percentile":               srp,
        "seller_close_speed":                   _fb(fallbacks, "seller_close_speed"),
        "seller_product_experience":            spe,
        "seller_pipeline_load":                 sl,
        "seller_product_win_rate":              spwr,
        # GROUP_DEAL
        "log_days_since_engage":                log_days,
        "deal_age_percentile":                  deal_age_pct,
        "log_deal_value":                       log_deal_value,
        "deal_value_percentile":                deal_val_pct,
        "deal_value_percentile_within_seller":  dvps,
        "deal_value_percentile_within_product": dvpp,
        "deal_value_vs_account_size":           deal_val_vs_acc,
        # GROUP_PRODUCT
        "product_win_rate":                     pwr,
        "product_rank_percentile":              prp,
        "product_avg_sales_cycle":              pasc,
        "product_relative_performance":         prelprf,
        # GROUP_ACCOUNT
        "account_size_percentile":              asp,
        "digital_maturity_index":               dmi,
        "revenue_per_employee":                 rpe,
        "company_age_score":                    cas,
        # GROUP_RISK
        "is_stale_flag":                        is_stale,
        "is_very_old_deal":                     is_very_old,
        "seller_overloaded_flag":               seller_overloaded,
        "low_product_performance_flag":         low_prod_perf,
        "deal_estagnado":                       deal_estagnado,
        "deal_muito_antigo":                    deal_muito_antigo,
        "produto_fraco":                        produto_fraco,
        "conta_fraca":                          conta_fraca,
        # GROUP_BUCKETS
        "bucket_deal_age":                      bucket_age,
        "bucket_deal_value":                    bucket_val,
        "bucket_account_size":                  bucket_acct_size,
        # GROUP_INTERACTIONS
        "interact_seller_product":              interact_sp,
        "interact_seller_value":                interact_sv,
        "interact_product_age":                 interact_pa,
        "interact_account_value":               interact_av,
        # V4 lead / geo
        "lead_source_wr":                       lead_src_wr,
        "lead_origin_wr":                       lead_orig_wr,
        "contact_role_wr":                      _fb(fallbacks, "contact_role_wr"),
        "last_activity_type_wr":                _fb(fallbacks, "last_activity_type_wr"),
        "lead_quality_score":                   lqs,
        "activity_count":                       act_count,
        "page_views_per_visit":                 _fb(fallbacks, "page_views_per_visit"),
        "has_activity":                         has_act,
        "last_activity_is_positive":            last_act_pos,
        "lead_tag_wr":                          lead_tag_wr,
        "country_wr":                           _fb(fallbacks, "country_wr"),
        "is_india":                             0.0,
        # Categorical passthrough for encoder + extra fields for engine scores
        "product":                              inp.product,
        "sales_agent":                          inp.sales_agent,
        "city":                                 inp.city,
        "country":                              inp.country,
        "lead_source":                          inp.lead_source,
        "lead_origin":                          inp.lead_origin,
        "contact_role":                         None,
        "lead_quality":                         inp.lead_quality,
        "lead_tag":                             inp.lead_tag,
        "last_activity_type":                   inp.last_activity_type,
        "last_notable_activity":                None,
        "office":                               inp.office,
        "manager":                              inp.manager,
        # Para compute_engine_scores (não entram no modelo, mas usados pelos motores)
        "days_since_engage":                    float(days),
        "product_rank_percentile":              prp,
        "seller_rank_percentile_signal":        srp,
    }

    row_df = pd.DataFrame([numeric_row])

    # ── Target encode + montar matriz completa (79 cols na ordem do scaler) ───
    te_df        = encoder.transform(row_df)
    numeric_cols = [c for c in scaler.feature_names_in_ if not c.startswith("te_")]
    row_full     = pd.concat(
        [row_df[numeric_cols].reset_index(drop=True), te_df.reset_index(drop=True)],
        axis=1,
    )

    return row_df, row_full


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health(request: Request):
    feat_cols = request.app.state.feat_cols
    return {
        "status":   "ok",
        "model":    "LogisticRegression",
        "features": len(feat_cols),
        "cv_auc":   0.6742,
    }


@app.post("/score", response_model=ScoreResponse)
async def score(inp: DealInput, request: Request):
    model     = request.app.state.model
    scaler    = request.app.state.scaler
    encoder   = request.app.state.encoder
    feat_cols = request.app.state.feat_cols
    ref_df    = request.app.state.ref_df
    fallbacks = request.app.state.fallbacks
    stats     = request.app.state.ref_stats

    # 1. Construir features
    row_df, row_full = _build_feature_row(inp, ref_df, encoder, scaler, fallbacks, stats)

    # 2. Escalar todos os 79 features → selecionar 29 → prever
    X_scaled = pd.DataFrame(
        scaler.transform(row_full),
        columns=scaler.feature_names_in_,
    )
    win_prob = float(model.predict_proba(X_scaled[feat_cols])[0, 1])

    # 3. Rating e receita
    rating           = assign_rating(win_prob)
    expected_revenue = compute_expected_revenue(win_prob, inp.effective_value)

    # 4. Engine scores (usa row_df + ref_df)
    engine_scores = compute_engine_scores(row_df.iloc[0], ref_df)

    # 5. Contexto para friction + NBA
    ctx = {
        "win_prob":          win_prob,
        "sp":                engine_scores.get("Seller Power",        50),
        "dm":                engine_scores.get("Deal Momentum",       50),
        "pp":                engine_scores.get("Product Performance", 50),
        "stagnation_health": engine_scores.get("Stagnation Risk",     50),
        "is_stale":          int(row_df["is_stale_flag"].iloc[0]),
        "seller_rank_pct":   float(row_df["seller_rank_percentile"].iloc[0]),
        "digital_maturity":  inp.digital_maturity_index,
        "engine_scores":     engine_scores,
        "sales_agent":       inp.sales_agent,
        "product":           inp.product,
        "deal_stage":        inp.deal_stage,
        "effective_value":   inp.effective_value,
    }

    friction_payload = identify_friction(ctx)
    action_payload   = choose_next_action(friction_payload["friction"], ctx)
    explanation      = build_deal_narrative(ctx, friction_payload)

    return ScoreResponse(
        rating           = rating,
        win_probability  = round(win_prob, 4),
        expected_revenue = expected_revenue,
        friction         = friction_payload["friction"],
        friction_label   = friction_payload["label"],
        next_action_key  = action_payload["action_key"],
        next_action      = action_payload["action_text"],
        explanation      = explanation,
        confidence       = friction_payload["confidence"],
        engine_scores    = {k: int(v) for k, v in engine_scores.items()},
    )


# ── Helpers: /notify-email ──────────────────────────────────────────────────────

def is_priority_deal(deal: DealSummary) -> bool:
    """Retorna True se o deal atende ao menos um critério de prioridade."""
    return (
        deal.rating == "C"
        or deal.friction == "high"
        or deal.days_in_stage > 20
        or deal.win_probability < 0.55
    )


def calculate_priority_score(deal: DealSummary) -> float:
    """Calcula o priority_score para ordenação dos deals prioritários."""
    friction_weight = {"high": 20, "medium": 10}.get(deal.friction, 0)
    return (100 - deal.final_score) + (deal.days_in_stage * 1.5) + friction_weight


def get_priority_deals(deals: List[DealSummary]) -> List[DealSummary]:
    """Filtra deals prioritários e retorna os 5 com maior priority_score."""
    priority = [d for d in deals if is_priority_deal(d)]
    priority.sort(key=calculate_priority_score, reverse=True)
    return priority[:5]


def build_email_html(deals: List[DealSummary]) -> str:
    """Gera o HTML do email com tabela de deals prioritários."""
    rows = ""
    for d in deals:
        rows += f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{d.account_name}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:center;">{d.rating}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:center;">{d.friction}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:center;">{d.win_probability:.0%}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:center;">{d.days_in_stage}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{d.next_action}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f9fafb;padding:24px;">
  <div style="max-width:700px;margin:0 auto;background:#fff;border-radius:8px;
              box-shadow:0 1px 4px rgba(0,0,0,.08);overflow:hidden;">
    <div style="background:#1e3a5f;padding:20px 24px;">
      <h1 style="margin:0;color:#fff;font-size:18px;">
        Prioridades do Pipeline - Deal Scoring
      </h1>
    </div>
    <div style="padding:24px;">
      <p style="color:#6b7280;margin-top:0;">
        Os <strong>{len(deals)}</strong> deals abaixo foram identificados como prioritários
        e requerem atenção imediata.
      </p>
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <thead>
          <tr style="background:#f3f4f6;">
            <th style="padding:10px 12px;text-align:left;color:#374151;">Conta</th>
            <th style="padding:10px 12px;text-align:center;color:#374151;">Rating</th>
            <th style="padding:10px 12px;text-align:center;color:#374151;">Friction</th>
            <th style="padding:10px 12px;text-align:center;color:#374151;">Win Probability</th>
            <th style="padding:10px 12px;text-align:center;color:#374151;">Dias no estágio</th>
            <th style="padding:10px 12px;text-align:left;color:#374151;">Próxima ação</th>
          </tr>
        </thead>
        <tbody>{rows}
        </tbody>
      </table>
    </div>
    <div style="padding:12px 24px;background:#f3f4f6;color:#9ca3af;font-size:12px;">
      Enviado automaticamente pelo DealSignal &mdash; Deal Scoring Platform
    </div>
  </div>
</body>
</html>"""


def send_email(recipients: List[str], html_body: str) -> None:
    """Envia o email via SMTP usando variáveis de ambiente."""
    smtp_host     = os.environ.get("SMTP_HOST", "")
    smtp_port     = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user     = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    smtp_sender   = os.environ.get("SMTP_SENDER", smtp_user)

    if not smtp_host:
        raise HTTPException(status_code=500, detail="SMTP_HOST não configurado.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Prioridades do Pipeline - Deal Scoring"
    msg["From"]    = smtp_sender
    msg["To"]      = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_sender, recipients, msg.as_string())


@app.post("/notify-email", response_model=NotifyEmailResponse)
async def notify_email(body: NotifyEmailRequest):
    """
    Identifica os deals prioritários do pipeline e envia um resumo por email.

    Critérios de prioridade: rating == 'C', friction == 'high',
    days_in_stage > 20, win_probability < 0.55.
    Envia os 5 deals com maior priority_score.
    """
    if not body.recipients:
        raise HTTPException(status_code=422, detail="A lista de destinatários não pode ser vazia.")
    if not body.deals:
        raise HTTPException(status_code=422, detail="A lista de deals não pode ser vazia.")

    priority_deals = get_priority_deals(body.deals)

    if not priority_deals:
        return NotifyEmailResponse(
            status="no_priority_deals",
            priority_deals_count=0,
            recipients=[str(r) for r in body.recipients],
        )

    html_body = build_email_html(priority_deals)
    send_email([str(r) for r in body.recipients], html_body)

    return NotifyEmailResponse(
        status="sent",
        priority_deals_count=len(priority_deals),
        recipients=[str(r) for r in body.recipients],
    )


@app.post("/notify-email/preview", response_class=HTMLResponse)
async def notify_email_preview(body: NotifyPreviewRequest):
    """
    Retorna o HTML do email de prioridades sem enviar.
    Use para visualizar o layout do email diretamente no navegador — sem SMTP necessário.
    """
    if not body.deals:
        raise HTTPException(status_code=422, detail="A lista de deals não pode ser vazia.")

    priority_deals = get_priority_deals(body.deals)

    if not priority_deals:
        return HTMLResponse("<p>Nenhum deal prioritário encontrado.</p>")

    return HTMLResponse(build_email_html(priority_deals))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
