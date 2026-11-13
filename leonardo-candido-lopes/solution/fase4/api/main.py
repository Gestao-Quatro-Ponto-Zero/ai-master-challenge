"""Backend FastAPI — Triagem Inteligente de Suporte (G4 AI Master Challenge, Desafio 002).
Carrega os modelos sklearn treinados e expõe endpoints de classificação."""
import sys, os, json, datetime
from pathlib import Path

# Adicionar path do ML para imports
ML_DIR = Path(__file__).resolve().parent.parent / "ml"
sys.path.insert(0, str(ML_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import joblib
import numpy as np

# Imports dos módulos ML
from security_rules import decide, load_thresholds, UNRELIABLE_CATEGORY_RULES
from priority_estimator import estimate_priority

app = FastAPI(title="Triagem Inteligente API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Carregar modelos ao iniciar ──
MODEL_DIR = ML_DIR / "model"
classifier = None
domain_detector = None
metadata = None
th_low, th_high = None, None


def load_models():
    global classifier, domain_detector, metadata, th_low, th_high
    classifier = joblib.load(str(MODEL_DIR / "classifier_pipeline.pkl"))
    domain_detector = joblib.load(str(MODEL_DIR / "domain_detector.pkl"))
    with open(str(MODEL_DIR / "model_metadata.json")) as f:
        metadata = json.load(f)
    th_low, th_high = load_thresholds(str(MODEL_DIR / "model_metadata.json"))
    print(f"[OK] Modelos carregados. Thresholds: baixo={th_low}, alto={th_high}")


@app.on_event("startup")
async def startup():
    load_models()


# ── Schemas ──
class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1)
    channel: Optional[str] = "Email"


class ClassifyResponse(BaseModel):
    domain: str
    category: Optional[str]
    category_raw: Optional[str] = None
    category_reliable: bool = True
    category_reliability_reason: Optional[str] = None
    confidence: float
    priority: str
    decision: str
    queue: str
    justification: str
    top3: list
    rule_triggered: Optional[str]
    rule_reason: Optional[str]
    model_version: str
    timestamp: str
    priority_detail: Optional[dict] = None
    domain_detail: Optional[dict] = None


# ── Funções de classificação ──
def classify_ticket(text: str, channel: str = "Email") -> dict:
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1) Detecção de domínio
    try:
        domain_result = domain_detector.predict(text)
        domain = domain_result.get("domain", "INDETERMINATE")
        domain_detail = domain_result
    except Exception:
        domain = "INDETERMINATE"
        domain_detail = {"error": "falha no detector de domínio"}

    # 2) Classificação de categoria
    try:
        proba = classifier.predict_proba([text])[0]
        classes = list(classifier.classes_)
        top_idx = int(np.argmax(proba))
        category = classes[top_idx]
        confidence = float(proba[top_idx])

        # Top 3
        sorted_idx = np.argsort(proba)[::-1][:3]
        top3 = [[classes[i], round(float(proba[i]), 4)] for i in sorted_idx]
    except Exception as e:
        category = None
        confidence = 0.0
        top3 = []
        domain = "INDETERMINATE"
        domain_detail = {"error": str(e)}

    # 3) Prioridade
    prio_result = estimate_priority(text, category)
    priority = prio_result["priority"]

    # 4) Decisão operacional (regras de segurança)
    # Nota: max_sim_train (similaridade com o treino) permanece em domain_detail apenas para rastreabilidade,
    # mas NÃO é usado como critério de decisão — a auditoria mostrou que ele não discrimina domínio.
    decision, rule_triggered, rule_reason = decide(
        text, domain, category, confidence, priority, th_low, th_high
    )
    # Confiabilidade da categoria: quando uma regra de segurança sobrepõe o classificador,
    # a categoria prevista NÃO deve ser tratada como orientação válida (mas é preservada para rastreabilidade).
    category_reliable = rule_triggered not in UNRELIABLE_CATEGORY_RULES
    category_reliability_reason = (
        None if category_reliable
        else f"categoria sobreposta pela regra de segurança {rule_triggered}; não tratar como orientação válida"
    )

    # 5) Fila sugerida
    queue = _suggest_queue(domain, category, decision, priority)

    # 6) Justificativa
    justification = _build_justification(domain, category, confidence, priority, decision, rule_reason)

    return {
        "domain": domain,
        "category": category if domain == "IT_INTERNAL" else None,
        "category_raw": category,
        "category_reliable": category_reliable,
        "category_reliability_reason": category_reliability_reason,
        "confidence": round(confidence, 4),
        "priority": priority,
        "decision": decision,
        "queue": queue,
        "justification": justification,
        "top3": top3,
        "rule_triggered": rule_triggered,
        "rule_reason": rule_reason,
        "model_version": metadata.get("version", "1.0.0") if metadata else "1.0.0",
        "timestamp": ts,
        "priority_detail": prio_result,
        "domain_detail": domain_detail,
    }


def _suggest_queue(domain: str, category: str | None, decision: str, priority: str) -> str:
    if decision == "ESCALATE":
        return "Escalação Imediata — Supervisão de Segurança"
    if domain == "FINANCIAL_COMMERCIAL":
        return "Fila Financeiro/Comercial — Atendimento Especializado"
    if domain in ("OUT_OF_SCOPE", "INDETERMINATE"):
        return "Triagem Manual — Domínio Não Identificado"
    if decision == "HUMAN_REQUIRED":
        return f"Revisão Humana — {category or 'Categoria Indefinida'}"
    if decision == "ASSISTED":
        return f"Sugestão para Agente — {category or 'N/A'} (confirmar antes de executar)"
    # AUTOMATIC
    return f"Roteamento Automático — {category}"


def _build_justification(domain, category, confidence, priority, decision, rule_reason):
    parts = []
    if domain != "IT_INTERNAL":
        parts.append(f"Domínio identificado: {domain}. Chamado fora do escopo do classificador IT.")
    else:
        parts.append(f"Domínio IT identificado. Categoria sugerida: {category} (confiança: {confidence:.1%}).")
    parts.append(f"Prioridade estimada: {priority}.")
    if rule_reason:
        parts.append(f"Regra aplicada: {rule_reason}.")
    if decision == "AUTOMATIC":
        parts.append("Confiança alta — roteamento automático sugerido.")
    elif decision == "ASSISTED":
        parts.append("Confiança moderada — sugestão para agente confirmar.")
    elif decision == "HUMAN_REQUIRED":
        parts.append("Revisão humana necessária antes de qualquer ação.")
    elif decision == "ESCALATE":
        parts.append("ATENÇÃO: Escalação imediata requerida. Supervisão deve avaliar.")
    return " ".join(parts)


# ── Endpoints ──
@app.post("/classify", response_model=ClassifyResponse)
async def classify(req: ClassifyRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Texto do chamado não pode ser vazio.")
    try:
        result = classify_ticket(req.text.strip(), req.channel or "Email")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na classificação: {str(e)}")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": classifier is not None,
        "domain_detector_loaded": domain_detector is not None,
        "model_version": metadata.get("version", "unknown") if metadata else "unknown",
        "thresholds": {"low": th_low, "high": th_high},
    }


@app.get("/test-cases")
async def test_cases():
    tc_path = ML_DIR / "test_cases.json"
    tr_path = ML_DIR / "test_results_pos_ajuste.json"
    cases = json.load(open(tc_path)) if tc_path.exists() else []
    results = json.load(open(tr_path)) if tr_path.exists() else []
    return {"test_cases": cases, "test_results": results}


@app.get("/model-metadata")
async def model_metadata():
    return metadata or {}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
