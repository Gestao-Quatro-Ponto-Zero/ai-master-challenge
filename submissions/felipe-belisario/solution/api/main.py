"""
main.py — FastAPI app Pulse Revenue Intelligence

Endpoints:
  GET  /pipeline                 Todos os deals abertos com scores
  GET  /pipeline/summary         Visão financeira agregada
  GET  /alerts                   Deals sem score + deadline risk em 7 dias
  GET  /manager/{manager_name}   Pipeline do time + sugestões de redistribuição
  POST /copilot                  Pergunta contextual via Claude API
"""

import json
import math
import os
import sys
from typing import Optional

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scorer import flag_deadline_risk, score_pipeline

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_coefficients.json")

app = FastAPI(title="Pulse Revenue Intelligence", version="2.0.0")


@app.on_event("startup")
async def startup_event():
    gemini_key = os.getenv("GEMINI_API_KEY")
    print(f"[COPILOT] Gemini API key configurada: {bool(gemini_key)}")
    if gemini_key:
        print(f"[COPILOT] Key prefix: {gemini_key[:12]}...")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# ap_stats cache — WR histórico por agente x produto
# ---------------------------------------------------------------------------

_ap_stats_dict: dict = {}


def _load_ap_stats() -> dict:
    global _ap_stats_dict
    if not _ap_stats_dict:
        with open(MODEL_PATH, encoding="utf-8") as f:
            model = json.load(f)
        for row in model["ap_stats"]:
            key = (row["sales_agent"], row["product"])
            _ap_stats_dict[key] = row["wr_agent_product"]
    return _ap_stats_dict


# ---------------------------------------------------------------------------
# Data loading (feita uma vez no startup)
# ---------------------------------------------------------------------------

_pipeline_df: Optional[pd.DataFrame] = None


def get_pipeline() -> pd.DataFrame:
    global _pipeline_df
    if _pipeline_df is None:
        _pipeline_df = _load_pipeline()
    return _pipeline_df


def _load_pipeline() -> pd.DataFrame:
    pipeline = pd.read_csv(f"{DATA_DIR}/sales_pipeline.csv")
    accounts = pd.read_csv(f"{DATA_DIR}/accounts.csv")
    teams = pd.read_csv(f"{DATA_DIR}/sales_teams.csv")
    products = pd.read_csv(f"{DATA_DIR}/products.csv")

    pipeline["product"] = pipeline["product"].str.replace("GTXPro", "GTX Pro", regex=False)

    pipeline = pipeline.merge(accounts[["account", "sector"]], on="account", how="left")
    pipeline = pipeline.merge(
        teams[["sales_agent", "manager", "regional_office"]], on="sales_agent", how="left"
    )
    # Valor proxy dos deals: close_value se disponível, senão sales_price do produto
    pipeline = pipeline.merge(products[["product", "sales_price"]], on="product", how="left")
    pipeline["deal_value"] = pipeline["close_value"].fillna(pipeline["sales_price"])

    # Apenas deals abertos
    open_deals = pipeline[pipeline["deal_stage"].isin(["Engaging", "Prospecting"])].copy()

    # Scoring (inclui conversão para percentil)
    scored = score_pipeline(open_deals)
    scored = flag_deadline_risk(scored)

    return scored


# ---------------------------------------------------------------------------
# Redistribuição com impacto financeiro real
# ---------------------------------------------------------------------------

def _compute_redistribution(team: pd.DataFrame) -> list[dict]:
    """
    Para cada deal do time no bottom 30% de score:
      - Busca WR histórico real do agente atual (via ap_stats)
      - Busca candidatos do time com WR >= agente_atual + 0.10
      - Calcula financial_impact = deal_value * (wr_candidato - wr_atual)
      - Só sugere se ganho >= 10pp E financial_impact > 0
    """
    ap = _load_ap_stats()
    agents_in_team = team["sales_agent"].unique().tolist()

    scored = team[team["has_score"] == True]
    if scored.empty:
        return []

    threshold = scored["score"].quantile(0.30)
    low_deals = team[team["score"] <= threshold].copy()

    suggestions = []
    for _, deal in low_deals.iterrows():
        agent = deal["sales_agent"]
        product = deal["product"]
        deal_value = float(deal.get("deal_value") or 0)

        current_wr = ap.get((agent, product))
        if current_wr is None:
            continue

        best_candidate = None
        best_impact = 0.0
        for candidate in agents_in_team:
            if candidate == agent:
                continue
            candidate_wr = ap.get((candidate, product))
            if candidate_wr is None:
                continue
            wr_gain = candidate_wr - current_wr
            if wr_gain < 0.10:
                continue
            financial_impact = deal_value * wr_gain
            if financial_impact > best_impact:
                best_impact = financial_impact
                best_candidate = {
                    "agent": candidate,
                    "suggested_wr": round(candidate_wr, 4),
                    "wr_gain": round(wr_gain, 4),
                    "financial_impact": round(financial_impact, 2),
                }

        if best_candidate:
            suggestions.append({
                "opportunity_id": deal["opportunity_id"],
                "account": deal.get("account"),
                "product": product,
                "deal_value": round(deal_value, 2),
                "current_agent": agent,
                "current_wr": round(current_wr, 4),
                "suggested_agent": best_candidate["agent"],
                "suggested_wr": best_candidate["suggested_wr"],
                "wr_gain": best_candidate["wr_gain"],
                "financial_impact": best_candidate["financial_impact"],
            })

    return suggestions[:20]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(obj):
    """Recursively replace NaN/inf with None and numpy scalars with Python types."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        v = float(obj)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    return _clean(df.to_dict(orient="records"))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/pipeline")
def get_all_pipeline():
    """Retorna todos os deals abertos com scores, tiers e alertas."""
    df = get_pipeline()

    summary = {
        "total": len(df),
        "scored": int(df["has_score"].sum()),
        "unscored_alerts": int(df["alert"].sum()),
        "deadline_risks": int(df["deadline_risk"].sum()),
        "tier_breakdown": df["tier"].value_counts(dropna=False).to_dict(),
        "total_pipeline_value": _clean(float(df["deal_value"].sum())) if "deal_value" in df.columns else 0,
        "revenue_alta": _clean(float(df[df["tier"] == "Alta"]["deal_value"].sum())) if "deal_value" in df.columns else 0,
        "revenue_media": _clean(float(df[df["tier"] == "Média"]["deal_value"].sum())) if "deal_value" in df.columns else 0,
        "revenue_baixa": _clean(float(df[df["tier"] == "Baixa"]["deal_value"].sum())) if "deal_value" in df.columns else 0,
        "revenue_at_risk": _clean(float(df[(df["tier"] == "Baixa") | (df["alert"] == True)]["deal_value"].sum())) if "deal_value" in df.columns else 0,
    }

    return {"summary": summary, "deals": _df_to_records(df)}


@app.get("/pipeline/summary")
def get_pipeline_summary():
    """Visão financeira agregada do pipeline completo."""
    df = get_pipeline()

    dv = "deal_value" in df.columns
    total_value = float(df["deal_value"].sum()) if dv else 0
    revenue_alta = float(df[df["tier"] == "Alta"]["deal_value"].sum()) if dv else 0
    revenue_media = float(df[df["tier"] == "Média"]["deal_value"].sum()) if dv else 0
    revenue_baixa = float(df[df["tier"] == "Baixa"]["deal_value"].sum()) if dv else 0
    revenue_at_risk = float(
        df[(df["tier"] == "Baixa") | (df["alert"] == True)]["deal_value"].sum()
    ) if dv else 0

    # Estimativa global de ganho com redistribuições (por manager)
    total_redist_impact = 0.0
    for manager in df["manager"].dropna().unique():
        team = df[df["manager"] == manager]
        suggestions = _compute_redistribution(team)
        total_redist_impact += sum(s["financial_impact"] for s in suggestions)

    return _clean({
        "total_pipeline_value": total_value,
        "revenue_alta": revenue_alta,
        "revenue_media": revenue_media,
        "revenue_baixa": revenue_baixa,
        "revenue_at_risk": revenue_at_risk,
        "gap_performance": 390637,
        "total_redistribution_impact": round(total_redist_impact, 2),
    })


@app.get("/alerts")
def get_alerts():
    """
    Retorna:
      - unscored: deals sem dados suficientes (alerta máximo)
      - deadline_risk: deals fechando em 7 dias com score Baixo ou sem score
    """
    df = get_pipeline()

    unscored = df[df["alert"] == True].copy()
    deadline = df[(df["deadline_risk"] == True) & (df["alert"] == False)].copy()

    return {
        "unscored": {
            "count": len(unscored),
            "deals": _df_to_records(unscored),
        },
        "deadline_risk": {
            "count": len(deadline),
            "deals": _df_to_records(deadline),
        },
    }


@app.get("/manager/{manager_name}")
def get_manager_pipeline(manager_name: str):
    """
    Retorna pipeline do time com:
      - agent_summary: resumo por agente com deal_value
      - redistribution_suggestions: com current_wr, suggested_wr, financial_impact
      - deals: todos os deals do time
    """
    df = get_pipeline()

    team = df[df["manager"].str.lower() == manager_name.lower()].copy()
    if team.empty:
        raise HTTPException(status_code=404, detail=f"Manager '{manager_name}' não encontrado.")

    # Resumo por agente
    agent_summary = (
        team.groupby("sales_agent")
        .agg(
            total_deals=("opportunity_id", "count"),
            scored_deals=("has_score", "sum"),
            avg_score=("score", "mean"),
            total_value=("deal_value", "sum"),
            alta=("tier", lambda x: (x == "Alta").sum()),
            media=("tier", lambda x: (x == "Média").sum()),
            baixa=("tier", lambda x: (x == "Baixa").sum()),
            alerts=("alert", "sum"),
        )
        .reset_index()
    )
    agent_summary["avg_score"] = agent_summary["avg_score"].round(2)

    # Redistribuições com impacto financeiro real
    suggestions = _compute_redistribution(team)

    return _clean({
        "manager": manager_name,
        "team_size": int(team["sales_agent"].nunique()),
        "total_deals": len(team),
        "total_pipeline_value": float(team["deal_value"].sum()) if "deal_value" in team.columns else 0,
        "agent_summary": _df_to_records(agent_summary),
        "redistribution_suggestions": suggestions,
        "deals": _df_to_records(team),
    })


# ---------------------------------------------------------------------------
# Copilot via Claude API
# ---------------------------------------------------------------------------

class CopilotRequest(BaseModel):
    question: str
    manager: Optional[str] = None


def _copilot_context(scope: pd.DataFrame, scope_label: str) -> str:
    total = len(scope)
    alta = int((scope["tier"] == "Alta").sum())
    media = int((scope["tier"] == "Média").sum())
    baixa = int((scope["tier"] == "Baixa").sum())
    unscored = int(scope["alert"].sum())
    total_value = float(scope["deal_value"].sum()) if "deal_value" in scope.columns else 0

    agent_scores = scope[scope["has_score"]].groupby("sales_agent")["score"].mean()
    top3 = agent_scores.nlargest(3)
    bottom3 = agent_scores.nsmallest(3)
    top3_str = ", ".join([f"{a} ({s:.1f})" for a, s in top3.items()])
    bottom3_str = ", ".join([f"{a} ({s:.1f})" for a, s in bottom3.items()])

    return (
        f"Pipeline {scope_label}:\n"
        f"- Total de negócios abertos: {total}\n"
        f"- Alta Prioridade: {alta} | Média Prioridade: {media} | Baixa Prioridade: {baixa}\n"
        f"- Sem análise (dados insuficientes): {unscored}\n"
        f"- Valor total do pipeline: ${total_value:,.0f}\n"
        f"- Top 3 responsáveis: {top3_str}\n"
        f"- Bottom 3 responsáveis: {bottom3_str}"
    )


@app.post("/copilot")
def copilot(req: CopilotRequest):
    """Responde perguntas sobre o pipeline via Claude API."""
    df = get_pipeline()

    if req.manager:
        scope = df[df["manager"].str.lower() == req.manager.lower()]
        scope_label = f"do time de {req.manager}"
    else:
        scope = df
        scope_label = "de todo o pipeline"

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "answer": "⚠ Copilot não configurado. Configure GEMINI_API_KEY.",
            "configured": False,
        }

    try:
        import google.generativeai as genai
        context = _copilot_context(scope, scope_label)
        genai.configure(api_key=api_key)
        prompt = (
            "Você é um assistente de Revenue Operations para um time de vendas B2B brasileiro.\n"
            "Responda sempre em português, linguagem comercial direta e acionável.\n"
            "Máximo 3 parágrafos curtos. Nunca use termos técnicos de ML.\n"
            "Quando mencionar números, traduza para impacto financeiro.\n\n"
            f"Contexto do pipeline:\n{context}\n\n"
            f"Pergunta: {req.question}"
        )
        MODELOS = [
            "models/gemini-2.5-flash",
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-lite",
        ]
        last_error = None
        for model_name in MODELOS:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return {"answer": response.text, "configured": True, "model_used": model_name}
            except Exception as e:
                print(f"[COPILOT] Modelo {model_name} falhou: {type(e).__name__}: {e}")
                last_error = e
                continue
        return {
            "answer": (
                f"⚠ Todos os modelos Gemini indisponíveis. "
                f"Erro: {str(last_error)}. "
                "Tente novamente amanhã — a cota gratuita renova diariamente."
            ),
            "configured": True,
            "error": str(last_error),
        }
    except Exception as e:
        print(f"[COPILOT ERROR] {type(e).__name__}: {e}")
        return {
            "answer": (
                f"Erro ao consultar o Gemini: {str(e)}. "
                "Verifique se a GEMINI_API_KEY está correta e se há créditos na conta."
            ),
            "configured": True,
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/models")
def list_models():
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY não configurada"}
    genai.configure(api_key=api_key)
    models = [m.name for m in genai.list_models()
              if "generateContent" in m.supported_generation_methods]
    return {"models": models}


@app.get("/health")
def health():
    return {"status": "ok"}
