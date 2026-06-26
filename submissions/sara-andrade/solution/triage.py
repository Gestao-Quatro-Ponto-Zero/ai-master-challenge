from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import re
import joblib
import numpy as np

MODEL_DIR = Path(__file__).resolve().parent / "models"

TopicRoute = Literal["AUTO_RESOLVE", "AGENT_ASSIST", "HUMAN_ESCALATION"]
SourceContext = Literal["auto", "b2e_it", "b2c_external"]

HIGH_RISK_TERMS = [
    "refund", "reembolso", "chargeback", "cancel", "cancellation", "cancelamento",
    "lawsuit", "legal", "attorney", "lawyer", "processo", "advogado",
    "fraud", "fraude", "privacy", "data breach", "vazamento", "lgpd",
    "angry", "furious", "complaint", "reclamação", "reclamacao", "supervisor",
    "manager", "churn", "leave", "leaving", "never again"
]

# Categorias que podem ser auto-roteadas quando o contexto é B2E/IT e a confiança é alta.
# Não é "auto-resolver tudo"; é auto-rotear ou sugerir procedimento padrão de baixa complexidade.
AUTO_ELIGIBLE_IT_CATEGORIES = {
    "Access",
    "Hardware",
    "Storage",
    "Purchase",
}

# Categorias com risco maior mesmo no domínio interno.
NEVER_AUTO_IT_CATEGORIES = {
    "Administrative rights",
    "HR Support",
    "Internal Project",
}


def _load_model(filename: str) -> Any:
    path = MODEL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Modelo não encontrado: {path}. Rode `python train_models.py` ou mantenha os arquivos .joblib em solution/models/."
        )
    return joblib.load(path)


_TOPIC_MODEL = None
_DOMAIN_MODEL = None


def get_topic_model() -> Any:
    global _TOPIC_MODEL
    if _TOPIC_MODEL is None:
        _TOPIC_MODEL = _load_model("topic_classifier_logreg.joblib")
    return _TOPIC_MODEL


def get_domain_model() -> Any:
    global _DOMAIN_MODEL
    if _DOMAIN_MODEL is None:
        _DOMAIN_MODEL = _load_model("domain_router_b2c_b2e.joblib")
    return _DOMAIN_MODEL


def contains_high_risk_terms(text: str) -> List[str]:
    text_low = text.lower()
    hits = []
    for term in HIGH_RISK_TERMS:
        if term.lower() in text_low:
            hits.append(term)
    return sorted(set(hits))


def _predict_with_confidence(model: Any, text: str) -> tuple[str, float, Dict[str, float]]:
    labels = list(model.classes_)
    probs = model.predict_proba([text])[0]
    idx = int(np.argmax(probs))
    top_label = labels[idx]
    top_conf = float(probs[idx])
    top3_idx = np.argsort(probs)[::-1][:3]
    top3 = {labels[i]: float(probs[i]) for i in top3_idx}
    return top_label, top_conf, top3


def detect_domain(text: str, source_context: SourceContext = "auto") -> tuple[str, float, Dict[str, float], List[str]]:
    notes: List[str] = []

    if source_context == "b2e_it":
        return "B2E_IT", 1.0, {"B2E_IT": 1.0}, ["Domínio informado explicitamente como B2E/IT."]
    if source_context == "b2c_external":
        return "B2C_EXTERNAL", 1.0, {"B2C_EXTERNAL": 1.0}, ["Domínio informado explicitamente como B2C externo."]

    model = get_domain_model()
    domain, conf, top = _predict_with_confidence(model, text)
    notes.append(
        "Domínio detectado automaticamente. Guardrail: a validação 100% ocorreu porque os datasets são muito diferentes; em produção, preferir metadado explícito da origem da fila."
    )
    return domain, conf, top, notes


def route_ticket(
    text: str,
    priority: str = "Medium",
    channel: Optional[str] = None,
    source_context: SourceContext = "auto",
    confidence_threshold_auto: float = 0.80,
    confidence_threshold_assist: float = 0.50,
) -> Dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("O texto do ticket não pode estar vazio.")

    priority_norm = (priority or "Medium").strip().title()
    channel_norm = (channel or "unknown").strip()

    risk_terms = contains_high_risk_terms(text)
    domain, domain_conf, domain_top3, domain_notes = detect_domain(text, source_context)

    rationale: List[str] = []
    rationale.extend(domain_notes)
    rationale.append(f"Prioridade recebida: {priority_norm}.")
    rationale.append(f"Canal recebido: {channel_norm}.")

    if risk_terms:
        rationale.append(f"Termos de risco encontrados: {', '.join(risk_terms)}.")

    # Hard guardrail global
    if priority_norm == "Critical":
        route: TopicRoute = "HUMAN_ESCALATION"
        return {
            "route": route,
            "domain": domain,
            "domain_confidence": domain_conf,
            "domain_top3": domain_top3,
            "predicted_topic": None,
            "topic_confidence": None,
            "topic_top3": {},
            "risk_terms": risk_terms,
            "rationale": rationale + ["Prioridade Critical nunca é auto-resolvida."],
            "suggested_action": "Escalar para humano sênior com resumo e evidências.",
            "suggested_reply": make_suggested_reply(route, domain, None),
        }

    # B2C external support: no full automation from this dataset.
    # The Dataset 1 text has weak predictive signal, and consumer cases often involve money/churn/emotion.
    if domain == "B2C_EXTERNAL":
        if risk_terms or priority_norm == "High":
            route = "HUMAN_ESCALATION"
            action = "Escalar para humano; IA pode apenas resumir e sugerir próximos passos."
            extra = "Domínio B2C externo + risco/alta prioridade."
        else:
            route = "AGENT_ASSIST"
            action = "Gerar resumo, resposta sugerida e checklist para o agente; não enviar automaticamente."
            extra = "Domínio B2C externo sem evidência suficiente para auto-resolução."
        return {
            "route": route,
            "domain": domain,
            "domain_confidence": domain_conf,
            "domain_top3": domain_top3,
            "predicted_topic": None,
            "topic_confidence": None,
            "topic_top3": {},
            "risk_terms": risk_terms,
            "rationale": rationale + [extra, "Dataset 1 foi tratado como insumo de guardrail/processo, não como base confiável para automação total."],
            "suggested_action": action,
            "suggested_reply": make_suggested_reply(route, domain, None),
        }

    # B2E/IT support: use validated classifier from Dataset 2.
    topic_model = get_topic_model()
    topic, topic_conf, topic_top3 = _predict_with_confidence(topic_model, text)
    rationale.append(f"Categoria IT prevista: {topic} ({topic_conf:.1%} de confiança).")

    if risk_terms:
        route = "HUMAN_ESCALATION"
        rationale.append("Termos de risco bloqueiam automação mesmo com boa confiança.")
    elif topic in NEVER_AUTO_IT_CATEGORIES:
        route = "AGENT_ASSIST"
        rationale.append(f"Categoria {topic} exige julgamento humano ou aprovação; nunca auto-resolver.")
    elif topic_conf >= confidence_threshold_auto and topic in AUTO_ELIGIBLE_IT_CATEGORIES and priority_norm in {"Low", "Medium"}:
        route = "AUTO_RESOLVE"
        rationale.append(f"Confiança >= {confidence_threshold_auto:.0%}, categoria elegível e prioridade baixa/média.")
    elif topic_conf >= confidence_threshold_assist:
        route = "AGENT_ASSIST"
        rationale.append(f"Confiança entre {confidence_threshold_assist:.0%} e {confidence_threshold_auto:.0%}, ou categoria/prioridade pede revisão.")
    else:
        route = "HUMAN_ESCALATION"
        rationale.append(f"Confiança < {confidence_threshold_assist:.0%}; fallback humano obrigatório.")

    return {
        "route": route,
        "domain": domain,
        "domain_confidence": domain_conf,
        "domain_top3": domain_top3,
        "predicted_topic": topic,
        "topic_confidence": topic_conf,
        "topic_top3": topic_top3,
        "risk_terms": risk_terms,
        "rationale": rationale,
        "suggested_action": action_for_route(route, topic),
        "suggested_reply": make_suggested_reply(route, domain, topic),
    }


def action_for_route(route: TopicRoute, topic: Optional[str]) -> str:
    if route == "AUTO_RESOLVE":
        return f"Auto-rotear para a fila/procedimento padrão de {topic}; registrar auditoria e amostrar revisões."
    if route == "AGENT_ASSIST":
        return "Enviar para agente com categoria sugerida, resumo, checklist e resposta rascunho."
    return "Escalar para humano; usar IA somente para resumo e preparação do contexto."


def make_suggested_reply(route: TopicRoute, domain: str, topic: Optional[str]) -> str:
    if route == "AUTO_RESOLVE":
        return (
            "Identifiquei o tipo de solicitação e vou encaminhar este chamado para o fluxo correto. "
            "Você receberá a atualização com os próximos passos assim que o procedimento padrão for aplicado."
        )
    if route == "AGENT_ASSIST":
        if domain == "B2C_EXTERNAL":
            return (
                "Obrigado por explicar o problema. Vou revisar os detalhes do seu caso e te responder com os próximos passos. "
                "Se houver informação de cobrança, cancelamento ou reembolso, um especialista humano fará a validação."
            )
        return (
            f"Classifiquei este chamado como {topic or 'categoria provável'} e preparei um rascunho para revisão do agente. "
            "Antes do envio, confirme se a categoria e o procedimento sugerido fazem sentido para o caso."
        )
    return (
        "Obrigado pelo contexto. Vou encaminhar este caso para um especialista humano, porque ele exige validação cuidadosa. "
        "Enquanto isso, registrei os principais pontos para acelerar o atendimento."
    )
