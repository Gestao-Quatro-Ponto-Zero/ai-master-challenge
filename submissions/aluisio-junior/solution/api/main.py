from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sys
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

import pandas as pd

# 🔥 Permitir importar services corretamente
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 📦 Imports do projeto
from services.data_service import load_data, build_summary
from services.data_processing import build_analytical_dataset
from services.analysis import (
    pareto_analysis,
    revenue_segmentation_executive,
)
from services.ai_engine import ask_ai
from services.ml_model import run_ml_model

app = FastAPI(title="Churn Intelligence System API", version="2.0.0")

# 🌐 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 Inicializando Churn Intelligence System API v2...")


# =========================================================
# 📦 MODELOS Pydantic
# =========================================================
class QuestionRequest(BaseModel):
    question: str


class KanbanProjectCreate(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    impact_area: str = "retention"
    owner: str = "C-Level"
    squad: str = "Growth Squad"
    scrum_master: str = "AI Scrum Master"
    current_stage: str = "approved"
    sprint: str = "Sprint 1"
    expected_impact: str = "Redução de churn e proteção de receita"
    source: str = "manual"
    recommendation_id: Optional[str] = None


class KanbanProjectMove(BaseModel):
    new_stage: str = Field(..., description="Novo estágio do card")


class RecommendationApproveRequest(BaseModel):
    recommendation_id: str


class WhatsAppNotifyRequest(BaseModel):
    recommendation_id: Optional[str] = None
    message: Optional[str] = None
    target: str = "c-level"


class WhatsAppWebhookRequest(BaseModel):
    action: str
    recommendation_id: Optional[str] = None
    project_id: Optional[str] = None
    notes: Optional[str] = None


# =========================================================
# 📊 PIPELINE DE DADOS
# =========================================================
accounts, subscriptions, feature_usage, support_tickets, churn_events = load_data()

df = build_analytical_dataset(
    accounts,
    subscriptions,
    feature_usage,
    support_tickets,
    churn_events
)

print("✅ Dataset carregado com sucesso")
print(f"📐 Shape do dataset: {df.shape}")


# =========================================================
# 🤖 MODELO DE ML
# =========================================================
model, importance = run_ml_model(df)

features = [
    "avg_mrr",
    "avg_arr",
    "avg_seats",
    "avg_usage_count",
    "avg_usage_duration",
    "avg_errors",
    "avg_resolution_time",
    "avg_first_response",
    "avg_satisfaction",
    "total_escalations"
]

missing_features = [col for col in features if col not in df.columns]
if missing_features:
    raise ValueError(f"❌ Features ausentes no dataset: {missing_features}")

df["churn_score"] = model.predict_proba(df[features])[:, 1]

# Thresholds adaptativos por percentil
high_threshold = float(df["churn_score"].quantile(0.80))
medium_threshold = float(df["churn_score"].quantile(0.50))


def classify_risk(score: float) -> str:
    if score >= high_threshold:
        return "Alto"
    elif score >= medium_threshold:
        return "Médio"
    return "Baixo"


df["risk_level"] = df["churn_score"].apply(classify_risk)

print("✅ Modelo aplicado com sucesso")
print(f"📊 Threshold Alto: {high_threshold:.4f}")
print(f"📊 Threshold Médio: {medium_threshold:.4f}")


# =========================================================
# 📈 ANÁLISES EXECUTIVAS
# =========================================================
df_pareto, pareto_summary = pareto_analysis(df)
revenue_summary = revenue_segmentation_executive(df)
summary_cache = build_summary(df, pareto_summary, revenue_summary)

print("✅ KPIs executivos gerados")


# =========================================================
# 🧠 ESTRUTURAS EM MEMÓRIA
# =========================================================
KANBAN_PROJECTS: List[Dict[str, Any]] = []


# =========================================================
# 🛠 HELPERS
# =========================================================
def _safe_datetime_series(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def _get_reference_date() -> pd.Timestamp:
    candidates = []

    if "churn_date" in churn_events.columns:
        s = _safe_datetime_series(churn_events["churn_date"]).dropna()
        if not s.empty:
            candidates.append(s.max())

    if "end_date" in subscriptions.columns:
        s = _safe_datetime_series(subscriptions["end_date"]).dropna()
        if not s.empty:
            candidates.append(s.max())

    if "start_date" in subscriptions.columns:
        s = _safe_datetime_series(subscriptions["start_date"]).dropna()
        if not s.empty:
            candidates.append(s.max())

    if "usage_date" in feature_usage.columns:
        s = _safe_datetime_series(feature_usage["usage_date"]).dropna()
        if not s.empty:
            candidates.append(s.max())

    if "submitted_at" in support_tickets.columns:
        s = _safe_datetime_series(support_tickets["submitted_at"]).dropna()
        if not s.empty:
            candidates.append(s.max())

    if candidates:
        return max(candidates)

    return pd.Timestamp.today()


def _get_top_risk_accounts(limit: int = 10) -> List[Dict[str, Any]]:
    # Somente contas ativas
    active_df = df[df["churned"] == 0].copy()

    if active_df.empty:
        return []

    # Classificação ABC a partir do pareto (que já usa contas ativas)
    abc_map = {}
    if "account_id" in df_pareto.columns and "segment" in df_pareto.columns:
        abc_map = df_pareto.set_index("account_id")["segment"].to_dict()

    active_df["abc_segment"] = active_df["account_id"].map(abc_map).fillna("N/A")

    # Prioridade de risco: Alto primeiro, depois Médio, depois Baixo
    def risk_priority(level: str) -> int:
        if level == "Alto":
            return 0
        elif level == "Médio":
            return 1
        return 2

    active_df["risk_priority"] = active_df["risk_level"].apply(risk_priority)

    # Ordenação:
    # 1. Risk level (Alto, Médio, Baixo)
    # 2. MRR desc
    # 3. Churn score desc
    active_df = active_df.sort_values(
        by=["risk_priority", "mrr", "churn_score"],
        ascending=[True, False, False]
    ).copy()

    top_risk = active_df.head(limit)[
        ["account_id", "abc_segment", "mrr", "churn_score", "risk_level"]
    ].copy()

    top_risk["mrr"] = top_risk["mrr"].round(2)
    top_risk["churn_score"] = top_risk["churn_score"].round(4)

    return top_risk.to_dict(orient="records")


def _get_feature_importance_records() -> List[Dict[str, Any]]:
    if importance is None:
        return []

    if isinstance(importance, pd.DataFrame):
        cols = importance.columns.tolist()

        if len(cols) >= 2:
            imp = importance.copy()
            return imp.to_dict(orient="records")

        return importance.to_dict(orient="records")

    if isinstance(importance, dict):
        return [
            {"feature": k, "importance": v}
            for k, v in importance.items()
        ]

    return []


def _compute_temporal_kpis() -> Dict[str, Any]:
    ref_date = _get_reference_date()

    total_accounts = int(df.shape[0])
    total_revenue = float(df["mrr"].sum()) if "mrr" in df.columns else 0.0

    churn_df = churn_events.copy()

    if "churn_date" not in churn_df.columns:
        return {
            "reference_date": str(ref_date.date()),
            "historical_churn_rate": float(summary_cache.get("churn_rate", 0)),
            "period_churn_30d": 0.0,
            "period_churn_90d": 0.0,
            "revenue_churn_30d": 0.0,
            "revenue_churn_90d": 0.0,
        }

    churn_df["churn_date"] = pd.to_datetime(churn_df["churn_date"], errors="coerce")
    churn_df = churn_df.dropna(subset=["churn_date"])

    churn_30 = churn_df[churn_df["churn_date"] >= (ref_date - pd.Timedelta(days=30))]
    churn_90 = churn_df[churn_df["churn_date"] >= (ref_date - pd.Timedelta(days=90))]

    churn_30_accounts = set(churn_30["account_id"].unique().tolist())
    churn_90_accounts = set(churn_90["account_id"].unique().tolist())

    churn_30_rate = len(churn_30_accounts) / total_accounts if total_accounts > 0 else 0.0
    churn_90_rate = len(churn_90_accounts) / total_accounts if total_accounts > 0 else 0.0

    revenue_30 = float(df[df["account_id"].isin(churn_30_accounts)]["mrr"].sum()) if "mrr" in df.columns else 0.0
    revenue_90 = float(df[df["account_id"].isin(churn_90_accounts)]["mrr"].sum()) if "mrr" in df.columns else 0.0

    revenue_churn_30 = revenue_30 / total_revenue if total_revenue > 0 else 0.0
    revenue_churn_90 = revenue_90 / total_revenue if total_revenue > 0 else 0.0

    return {
        "reference_date": str(ref_date.date()),
        "historical_churn_rate": float(summary_cache.get("churn_rate", 0)),
        "period_churn_30d": float(churn_30_rate),
        "period_churn_90d": float(churn_90_rate),
        "revenue_churn_30d": float(revenue_churn_30),
        "revenue_churn_90d": float(revenue_churn_90),
    }


def _build_headlines() -> List[Dict[str, Any]]:
    total_revenue = float(summary_cache.get("total_revenue", 0))
    mrr_at_risk = float(summary_cache.get("mrr_at_risk", 0))
    high_risk_accounts = int(summary_cache.get("high_risk_accounts", 0))
    arpu = float(summary_cache.get("arpu", 0))
    churn_rate = float(summary_cache.get("churn_rate", 0))

    revenue_risk_pct = (mrr_at_risk / total_revenue) if total_revenue > 0 else 0

    headlines = [
        {
            "title": "Receita sob risco imediato",
            "message": f"{revenue_risk_pct:.1%} do MRR está concentrado em contas de alto risco.",
            "priority": "high",
            "metric": "mrr_at_risk"
        },
        {
            "title": "Contas críticas priorizadas",
            "message": f"{high_risk_accounts} contas foram classificadas como alto risco pelo modelo preditivo.",
            "priority": "high",
            "metric": "high_risk_accounts"
        },
        {
            "title": "Ticket médio enterprise",
            "message": f"ARPU médio estimado em ${arpu:,.2f}.",
            "priority": "medium",
            "metric": "arpu"
        },
        {
            "title": "Churn histórico elevado",
            "message": f"O churn histórico acumulado está em {churn_rate:.1%}; recomenda-se leitura temporal para contexto executivo.",
            "priority": "medium",
            "metric": "historical_churn_rate"
        }
    ]

    return headlines


def _build_root_causes() -> List[Dict[str, Any]]:
    causes = []

    if "avg_errors" in df.columns:
        error_risk = df.groupby("risk_level")["avg_errors"].mean().to_dict()
        causes.append({
            "driver": "Erros de produto",
            "detail": f"Contas de alto risco apresentam média maior de erros: {error_risk.get('Alto', 0):.2f}.",
            "severity": "high"
        })

    if "avg_resolution_time" in df.columns:
        resolution_risk = df.groupby("risk_level")["avg_resolution_time"].mean().to_dict()
        causes.append({
            "driver": "Suporte reativo",
            "detail": f"Tempo médio de resolução em contas de alto risco: {resolution_risk.get('Alto', 0):.2f}h.",
            "severity": "medium"
        })

    if "avg_usage_count" in df.columns:
        usage_risk = df.groupby("risk_level")["avg_usage_count"].mean().to_dict()
        causes.append({
            "driver": "Uso inconsistente",
            "detail": f"Contas em alto risco têm média de uso de {usage_risk.get('Alto', 0):.2f}.",
            "severity": "medium"
        })

    if "support_risk_score" in df.columns:
        support_score = df.groupby("risk_level")["support_risk_score"].mean().to_dict()
        causes.append({
            "driver": "Support risk score",
            "detail": f"Score médio de risco de suporte em alto risco: {support_score.get('Alto', 0):.2f}.",
            "severity": "high"
        })

    return causes[:4]


def _build_recommendations() -> List[Dict[str, Any]]:
    total_revenue = float(summary_cache.get("total_revenue", 0))
    mrr_at_risk = float(summary_cache.get("mrr_at_risk", 0))
    revenue_risk_pct = (mrr_at_risk / total_revenue) if total_revenue > 0 else 0

    recommendations = [
        {
            "recommendation_id": "REC-001",
            "title": "Priorizar onboarding para contas de alto MRR",
            "description": "Contas de alto valor churnam em níveis relevantes. Estruture um fluxo dedicado de onboarding e ativação orientado a time-to-value.",
            "priority": "high",
            "impact_area": "retention",
            "evidence": f"{revenue_risk_pct:.1%} do MRR está em risco imediato.",
            "expected_impact": "Redução de churn em contas enterprise e proteção de receita.",
            "suggested_owner": "Chief Revenue Officer",
            "suggested_squad": "Retention Squad",
            "source": "rules+ml"
        },
        {
            "recommendation_id": "REC-002",
            "title": "Investigar contas com alto uso e churn",
            "description": "Clientes com alto uso ainda churnam. Isso sugere fricção, desalinhamento de valor percebido ou experiência operacional inadequada.",
            "priority": "high",
            "impact_area": "product",
            "evidence": "Há contas com forte engajamento entre os perfis de risco alto.",
            "expected_impact": "Redução de silent churn e melhoria de retenção por jornada.",
            "suggested_owner": "Chief Product Officer",
            "suggested_squad": "Product Analytics Squad",
            "source": "rules+ml"
        },
        {
            "recommendation_id": "REC-003",
            "title": "Implantar gatilhos proativos de suporte",
            "description": "Escalar automaticamente contas com sinais críticos de suporte, erro e demora de atendimento para um plano de ação preventivo.",
            "priority": "medium",
            "impact_area": "support",
            "evidence": "Support risk score elevado em grupos de alto risco.",
            "expected_impact": "Menor fricção operacional e maior retenção.",
            "suggested_owner": "VP Customer Success",
            "suggested_squad": "CX Squad",
            "source": "rules+ml"
        },
        {
            "recommendation_id": "REC-004",
            "title": "Criar playbooks de retenção por segmento ABC",
            "description": "Montar estratégias específicas para segmentos A, B e C com mensagens, ofertas e abordagens distintas.",
            "priority": "medium",
            "impact_area": "strategy",
            "evidence": "Segmentos de receita apresentam churn materialmente relevante em diferentes faixas.",
            "expected_impact": "Maior eficiência de retenção por faixa de valor.",
            "suggested_owner": "Chief Strategy Officer",
            "suggested_squad": "Revenue Ops Squad",
            "source": "rules+ml"
        },
        {
            "recommendation_id": "REC-005",
            "title": "Reduzir time-to-value de novas contas",
            "description": "Mapear jornada inicial e encurtar o caminho até o primeiro valor percebido para reduzir churn inicial.",
            "priority": "medium",
            "impact_area": "onboarding",
            "evidence": "Parte relevante do churn histórico pode estar associada à jornada inicial.",
            "expected_impact": "Melhoria da ativação e retenção nos primeiros ciclos.",
            "suggested_owner": "Chief Operating Officer",
            "suggested_squad": "Growth Squad",
            "source": "rules+ml"
        }
    ]

    return recommendations


def _generate_ai_executive_summary(payload: Dict[str, Any]) -> str:
    try:
        question = (
            "Gere um resumo executivo em português para C-Level sobre churn, risco de receita, "
            "principais causas e ações prioritárias. Seja objetivo, estratégico e orientado à decisão."
        )
        return ask_ai(question, payload)
    except Exception as e:
        return f"Resumo executivo indisponível no momento. Detalhe técnico: {str(e)}"


def _build_insights_payload() -> Dict[str, Any]:
    temporal_kpis = _compute_temporal_kpis()
    top_risk = _get_top_risk_accounts(10)
    feature_importance = _get_feature_importance_records()

    payload = {
        "executive_summary": "",
        "headlines": _build_headlines(),
        "root_causes": _build_root_causes(),
        "recommended_actions": _build_recommendations(),
        "top_risk_accounts": top_risk,
        "feature_importance": feature_importance,
        "temporal_kpis": temporal_kpis
    }

    payload["executive_summary"] = _generate_ai_executive_summary(
        {
            "kpis": summary_cache,
            "temporal_kpis": temporal_kpis,
            "top_risk_accounts": top_risk,
            "headlines": payload["headlines"],
            "root_causes": payload["root_causes"]
        }
    )

    return payload


def _build_dashboard_validation() -> Dict[str, Any]:
    temporal_kpis = _compute_temporal_kpis()

    return {
        "cards": {
            "total_accounts": summary_cache["total_accounts"],
            "active_accounts": summary_cache["active_accounts"],
            "churned_accounts": summary_cache["churned_accounts"],
            "inactive_accounts": summary_cache.get("inactive_accounts", 0),
            "total_revenue": summary_cache["total_revenue"],
            "total_mrr": summary_cache.get("total_mrr", summary_cache["total_revenue"]),
            "active_mrr": summary_cache.get("active_mrr", 0),
            "inactive_mrr": summary_cache.get("inactive_mrr", 0),
            "risk_mrr": summary_cache.get("risk_mrr", summary_cache["mrr_at_risk"]),
            "mrr_at_risk": summary_cache["mrr_at_risk"],
            "churn_rate": summary_cache["churn_rate"],
            "historical_churn_rate": temporal_kpis["historical_churn_rate"],
            "period_churn_30d": temporal_kpis["period_churn_30d"],
            "period_churn_90d": temporal_kpis["period_churn_90d"],
            "revenue_churn": summary_cache["revenue_churn"],
            "revenue_churn_30d": temporal_kpis["revenue_churn_30d"],
            "revenue_churn_90d": temporal_kpis["revenue_churn_90d"],
            "arpu": summary_cache["arpu"],
            "arpu_total": summary_cache.get("arpu_total", summary_cache["arpu"]),
            "arpu_active": summary_cache.get("arpu_active", 0),
            "arpu_inactive": summary_cache.get("arpu_inactive", 0),
            "arpu_risk": summary_cache.get("arpu_risk", 0),
            "ltv": summary_cache["ltv"],
            "ltv_total": summary_cache.get("ltv_total", summary_cache["ltv"]),
            "ltv_active": summary_cache.get("ltv_active", 0),
            "ltv_inactive": summary_cache.get("ltv_inactive", 0),
            "ltv_risk": summary_cache.get("ltv_risk", 0),
        },
        "risk_distribution": {
            "high": summary_cache["high_risk_accounts"],
            "medium": summary_cache["medium_risk_accounts"],
            "low": summary_cache["low_risk_accounts"],
        },
        "top_risk_accounts": _get_top_risk_accounts(10),
        "pareto": summary_cache["pareto"],
        "segmentation": summary_cache["segmentation"],
        "recommendations": _build_recommendations()
    }


def _get_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    for project in KANBAN_PROJECTS:
        if project["project_id"] == project_id:
            return project
    return None


def _get_recommendation_by_id(recommendation_id: str) -> Optional[Dict[str, Any]]:
    recommendations = _build_recommendations()
    for rec in recommendations:
        if rec["recommendation_id"] == recommendation_id:
            return rec
    return None


def _create_project_from_recommendation(recommendation: Dict[str, Any]) -> Dict[str, Any]:
    project = {
        "project_id": f"PRJ-{uuid.uuid4().hex[:8].upper()}",
        "title": recommendation["title"],
        "description": recommendation["description"],
        "priority": recommendation.get("priority", "medium"),
        "impact_area": recommendation.get("impact_area", "retention"),
        "owner": recommendation.get("suggested_owner", "C-Level"),
        "squad": recommendation.get("suggested_squad", "Growth Squad"),
        "scrum_master": "AI Scrum Master",
        "current_stage": "approved",
        "sprint": "Sprint 1",
        "expected_impact": recommendation.get("expected_impact", "Proteção de receita"),
        "source": recommendation.get("source", "rules+ml"),
        "recommendation_id": recommendation.get("recommendation_id"),
        "created_at": datetime.utcnow().isoformat(),
        "history": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "created_from_recommendation",
                "details": recommendation.get("recommendation_id")
            }
        ]
    }
    KANBAN_PROJECTS.append(project)
    return project


# =========================================================
# 🌐 ROTAS BÁSICAS
# =========================================================
@app.get("/")
def root():
    return {"message": "Churn Intelligence System API v2 🚀"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "rows": int(df.shape[0]),
        "features_used": features,
        "thresholds": {
            "high": high_threshold,
            "medium": medium_threshold
        }
    }


# =========================================================
# 📊 KPIs E DASHBOARD
# =========================================================
@app.get("/kpis")
def get_kpis():
    temporal_kpis = _compute_temporal_kpis()

    return {
        **summary_cache,
        "temporal": temporal_kpis
    }


@app.get("/dashboard-validation")
def dashboard_validation():
    return _build_dashboard_validation()


@app.get("/churn-risk")
def churn_risk():
    return _get_top_risk_accounts(10)


# =========================================================
# 🧠 INSIGHTS E RECOMENDAÇÕES
# =========================================================
@app.get("/insights")
def get_insights():
    return _build_insights_payload()


@app.get("/recommendations")
def get_recommendations():
    return {
        "items": _build_recommendations(),
        "count": len(_build_recommendations())
    }


# =========================================================
# 🤖 IA GENERATIVA
# =========================================================
@app.post("/ask-ai")
def ask_ai_endpoint(req: QuestionRequest):
    context = {
        "kpis": summary_cache,
        "temporal_kpis": _compute_temporal_kpis(),
        "top_accounts_churn": _get_top_risk_accounts(10),
        "recommendations": _build_recommendations(),
        "kanban_projects": KANBAN_PROJECTS
    }

    resposta = ask_ai(req.question, context)

    return {
        "question": req.question,
        "answer": resposta
    }


# =========================================================
# 📌 KANBAN DE PROJETOS
# =========================================================
@app.get("/kanban/projects")
def get_kanban_projects():
    return {
        "items": KANBAN_PROJECTS,
        "count": len(KANBAN_PROJECTS),
        "stages": [
            "backlog",
            "approved",
            "discovery",
            "development",
            "testing",
            "go-live",
            "monitoring",
            "done"
        ]
    }


@app.post("/kanban/projects")
def create_kanban_project(project: KanbanProjectCreate):
    new_project = {
        "project_id": f"PRJ-{uuid.uuid4().hex[:8].upper()}",
        "title": project.title,
        "description": project.description,
        "priority": project.priority,
        "impact_area": project.impact_area,
        "owner": project.owner,
        "squad": project.squad,
        "scrum_master": project.scrum_master,
        "current_stage": project.current_stage,
        "sprint": project.sprint,
        "expected_impact": project.expected_impact,
        "source": project.source,
        "recommendation_id": project.recommendation_id,
        "created_at": datetime.utcnow().isoformat(),
        "history": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "created_manual",
                "details": project.source
            }
        ]
    }

    KANBAN_PROJECTS.append(new_project)
    return new_project


@app.post("/kanban/projects/approve")
def approve_recommendation(req: RecommendationApproveRequest):
    recommendation = _get_recommendation_by_id(req.recommendation_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    existing = [
        p for p in KANBAN_PROJECTS
        if p.get("recommendation_id") == req.recommendation_id
    ]
    if existing:
        return {
            "message": "Recommendation already approved",
            "project": existing[0]
        }

    project = _create_project_from_recommendation(recommendation)
    return {
        "message": "Recommendation approved and moved to Kanban",
        "project": project
    }


@app.patch("/kanban/projects/{project_id}/move")
def move_kanban_project(project_id: str, req: KanbanProjectMove):
    project = _get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    old_stage = project["current_stage"]
    project["current_stage"] = req.new_stage
    project["history"].append(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "moved_stage",
            "details": f"{old_stage} -> {req.new_stage}"
        }
    )

    return {
        "message": "Project moved successfully",
        "project": project
    }


# =========================================================
# 📲 WHATSAPP FLOW (SIMULAÇÃO DE PRODUÇÃO)
# =========================================================
@app.post("/whatsapp/notify")
def whatsapp_notify(req: WhatsAppNotifyRequest):
    recommendation = None
    if req.recommendation_id:
        recommendation = _get_recommendation_by_id(req.recommendation_id)

    payload = {
        "status": "queued",
        "channel": "whatsapp",
        "target": req.target,
        "recommendation": recommendation,
        "message": req.message or (
            f"Aprovar recomendação {req.recommendation_id} no Churn Intelligence System."
            if req.recommendation_id
            else "Nova atualização executiva disponível no Churn Intelligence System."
        ),
        "approval_options": ["approve", "reject", "details"],
        "timestamp": datetime.utcnow().isoformat()
    }

    return payload


@app.post("/whatsapp/webhook")
def whatsapp_webhook(req: WhatsAppWebhookRequest):
    action = req.action.lower().strip()

    if action == "approve" and req.recommendation_id:
        recommendation = _get_recommendation_by_id(req.recommendation_id)
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        project = _create_project_from_recommendation(recommendation)
        return {
            "status": "approved",
            "message": "Recommendation approved via WhatsApp and created in Kanban",
            "project": project
        }

    if action == "reject":
        return {
            "status": "rejected",
            "message": "Recommendation rejected via WhatsApp",
            "notes": req.notes
        }

    if action == "details":
        recommendation = _get_recommendation_by_id(req.recommendation_id) if req.recommendation_id else None
        return {
            "status": "details",
            "recommendation": recommendation,
            "notes": req.notes
        }

    if action == "move" and req.project_id:
        project = _get_project_by_id(req.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project["history"].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "whatsapp_interaction",
                "details": req.notes or "Move requested via WhatsApp"
            }
        )
        return {
            "status": "received",
            "message": "Project update received via WhatsApp",
            "project": project
        }

    raise HTTPException(status_code=400, detail="Unsupported WhatsApp action")