from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from triage import route_ticket
except ImportError:
    from .triage import route_ticket


class TicketRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Texto completo do ticket.")
    priority: Literal["Low", "Medium", "High", "Critical"] = Field("Medium", description="Prioridade informada ou estimada.")
    channel: Optional[Literal["Email", "Phone", "Chat", "Social media", "Internal portal", "Other"]] = Field(
        "Other", description="Canal de entrada."
    )
    source_context: Literal["auto", "b2e_it", "b2c_external"] = Field(
        "auto",
        description="Use b2e_it para suporte interno/IT, b2c_external para cliente externo, ou auto para roteamento automático.",
    )


class TriageResponse(BaseModel):
    route: str
    domain: str
    domain_confidence: float
    domain_top3: Dict[str, float]
    predicted_topic: Optional[str]
    topic_confidence: Optional[float]
    topic_top3: Dict[str, float]
    risk_terms: list[str]
    rationale: list[str]
    suggested_action: str
    suggested_reply: str


app = FastAPI(
    title="CX Triage Copilot — Challenge 002",
    description=(
        "Protótipo FastAPI para triagem de tickets com IA. "
        "A solução automatiza apenas onde há evidência: suporte interno/IT com alta confiança. "
        "Casos B2C externos, críticos, financeiros ou ambíguos ficam em Agent Assist ou Human Escalation."
    ),
    version="1.0.0",
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/model-card")
def model_card() -> Dict[str, Any]:
    return {
        "selected_model": "TF-IDF + LogisticRegression",
        "baseline_model": "TF-IDF + ComplementNB",
        "validated_on": "Dataset 2 — IT Service Ticket Classification",
        "selected_model_accuracy": 0.8643,
        "selected_model_f1_macro": 0.8627,
        "recommended_confidence_gate": 0.80,
        "gate_at_0_80": {
            "coverage": 0.6152,
            "accuracy_inside_gate": 0.9726,
        },
        "guardrails": [
            "Critical nunca é AUTO_RESOLVE.",
            "B2C externo não é auto-resolvido com este dataset.",
            "Administrative rights, HR Support e Internal Project exigem humano/agent assist.",
            "Refund, cancellation, legal, fraud, privacy e termos emocionais bloqueiam automação.",
            "Baixa confiança aciona fallback humano.",
        ],
        "data_quality_notes": [
            "Dataset 1 tem 8.469 registros, não ~30.000 tickets reais.",
            "100% das descrições do Dataset 1 contêm placeholder {product_purchased}.",
            "49,3% dos tickets fechados têm resolução antes da primeira resposta.",
            "Os tempos positivos remanescentes não diferem por canal de forma significativa (Kruskal p=0,791).",
            "Dataset 1 é usado para guardrails/processo; Dataset 2 é usado para classificador textual.",
        ],
    }


@app.post("/triage", response_model=TriageResponse)
def triage(req: TicketRequest) -> Dict[str, Any]:
    try:
        return route_ticket(
            text=req.text,
            priority=req.priority,
            channel=req.channel,
            source_context=req.source_context,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/examples")
def examples() -> Dict[str, list[Dict[str, Any]]]:
    return {
        "b2e_it_examples": [
            {
                "text": "Please reset my password. I cannot login to my account or access the internal system.",
                "priority": "Medium",
                "channel": "Internal portal",
                "source_context": "b2e_it",
            },
            {
                "text": "Need a new monitor and docking station for a new hire starting next Monday.",
                "priority": "Low",
                "channel": "Internal portal",
                "source_context": "b2e_it",
            },
        ],
        "b2c_external_examples": [
            {
                "text": "I want a refund because my GoPro is not working and I am very angry.",
                "priority": "High",
                "channel": "Email",
                "source_context": "b2c_external",
            },
            {
                "text": "I need help setting up my Philips Hue lights with the mobile app.",
                "priority": "Medium",
                "channel": "Chat",
                "source_context": "b2c_external",
            },
        ],
    }
