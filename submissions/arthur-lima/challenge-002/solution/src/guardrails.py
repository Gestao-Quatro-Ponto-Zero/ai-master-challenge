"""Deterministic Guardrails for PII Sanitization, Prompt Injection, Business Policy & Domain Shift.

Implements H3: explicit separation between statistical confidence and operational
safety boundaries (what MUST NOT be automated in Tier 1).
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List


# --- 1. PII Masking Patterns (LGPD / GDPR Basic Hygiene) ---
CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}\b")
CNPJ_RE = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}[-.]?\d{2}\b")
CARD_RE = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(
    r"(?:\+?55\s?)?(?:\(?\d{2,3}\)?[\s-]?)?\d{4,5}[-\s]\d{4}\b|\(\d{3}\)\s*\d{3}[-\s]\d{4}\b"
)

# --- 2. Prompt Injection & Jailbreak Patterns ---
PROMPT_INJECTION_RE = re.compile(
    r"(ignore\s+(?:all\s+)?(?:(?:previous|prior|above)\s+)?(?:instructions|rules|prompts)|"
    r"esque[cç]a\s+(?:todas\s+as\s+)?(?:instru[cç][oõ]es|regras)|"
    r"system\s*prompt|developer\s*mode|jailbreak|"
    r"voc[eê]\s+agora\s+[eé]\s+um|you\s+are\s+now\s+an?\s+unrestricted|"
    r"bypass\s+(?:security|policy|approval)|"
    r"emita\s+(?:imediatamente\s+)?(?:o\s+)?(?:reembolso|voucher|estorno)|"
    r"approve\s+immediate\s+refund|"
    r"<\s*script\b|drop\s+table\s+)",
    re.IGNORECASE,
)

# --- 3. High-Risk Business Categories (What NOT to Automate in Tier 1) ---
HIGH_RISK_FINANCIAL_LEGAL_RE = re.compile(
    r"(\brefund\s+request\b|\bchargeback\b|\bestorno\b|\breembolso\b|"
    r"\bcancellation\s+request\b|\bcancel\s+my\s+subscription\b|\bcancelamento\b|"
    r"\blawsuit\b|\bprocon\b|\badvogado\b|\blegal\s+action\b|\bprocesso\s+judicial\b|"
    r"\bdata\s+loss\b|\bransomware\b|\bsecurity\s+breach\b|\bvazamento\s+de\s+dados\b|"
    r"\bunauthorized\s+charge\b|\bfraude?\b|\bcobran[cç]a\s+indevida\b)",
    re.IGNORECASE,
)

# --- 4. Template Corruption & Consumer Retail Out-of-Domain Markers ---
UNINTERPOLATED_TEMPLATE_RE = re.compile(r"\{[a-zA-Z0-9_]+\}")

CONSUMER_BOILERPLATE_RE = re.compile(
    r"(i'm\s+having\s+an\s+issue\s+with\s+the\b|"
    r"i'm\s+facing\s+a\s+problem\s+with\s+my\b|"
    r"your\s+billing\s+zip\s+code\s+is|"
    r"\bgopro\s+hero\b|\bxbox\b|\bplaystation\b|\bnintendo\s+switch\b|"
    r"\bsmart\s*tv\b|\bphilips\s+hue\b|\bkitchenaid\b|\bdyson\b|\broomba\b|"
    r"\bfitbit\b|\bkindle\b|\bnest\s+thermostat\b|\bbose\s+quietcomfort\b)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GuardrailAssessment:
    sanitized_text: str
    pii_types_detected: List[str]
    pii_count: int
    prompt_injection_detected: bool
    high_risk_policy_triggered: bool
    template_artifact_detected: bool
    consumer_domain_shift_detected: bool
    force_human_tier3: bool
    guardrail_reasons: List[str]


def mask_pii(text: str) -> Dict[str, object]:
    """Masks structured PII patterns before model inference or logging."""
    raw = str(text or "")
    detected: List[str] = []
    count = 0

    def _sub(pattern: re.Pattern, token: str, label: str, current: str) -> str:
        nonlocal count
        matches = pattern.findall(current)
        if matches:
            detected.append(label)
            count += len(matches)
            return pattern.sub(token, current)
        return current

    masked = raw
    masked = _sub(CARD_RE, "[CARD_REDACTED]", "credit_card", masked)
    masked = _sub(CPF_RE, "[CPF_REDACTED]", "cpf", masked)
    masked = _sub(CNPJ_RE, "[CNPJ_REDACTED]", "cnpj", masked)
    masked = _sub(EMAIL_RE, "[EMAIL_REDACTED]", "email", masked)
    masked = _sub(PHONE_RE, "[PHONE_REDACTED]", "phone", masked)

    return {
        "sanitized_text": masked,
        "pii_types_detected": detected,
        "pii_count": count,
    }


# H3 — Separação explícita entre score estatístico e barreiras determinísticas de
# segurança, alçada financeira/jurídica e mudança de domínio (Dataset 1 vs Dataset 2).
def evaluate_guardrails(
    text: str,
    centroid_similarity: float | None = None,
    min_domain_similarity: float = 0.065,
) -> GuardrailAssessment:
    """
    Evaluates deterministic safety, business-policy, and domain-shift guardrails.
    Any critical trigger forces `force_human_tier3 = True` regardless of classifier confidence.
    """
    raw = str(text or "")
    pii_info = mask_pii(raw)
    sanitized = str(pii_info["sanitized_text"])
    pii_types = list(pii_info["pii_types_detected"])
    pii_count = int(pii_info["pii_count"])

    reasons: List[str] = []

    inj = bool(PROMPT_INJECTION_RE.search(raw))
    if inj:
        reasons.append("🚨 Tentativa de Prompt Injection / Subversão de Instruções")

    high_risk = bool(HIGH_RISK_FINANCIAL_LEGAL_RE.search(raw))
    if high_risk:
        reasons.append("⚖️ Demanda Sensível (Reembolso / Cancelamento / Perda de Dados / Jurídico)")

    tmpl = bool(UNINTERPOLATED_TEMPLATE_RE.search(raw))
    if tmpl:
        reasons.append("🧩 Template Sintético Não Interpolado ({product_purchased} / variável bruta)")

    consumer_boiler = bool(CONSUMER_BOILERPLATE_RE.search(raw))
    low_lex_sim = (centroid_similarity is not None) and (centroid_similarity < min_domain_similarity)
    domain_shift = tmpl or consumer_boiler or low_lex_sim
    if consumer_boiler:
        reasons.append("🌐 Fora de Domínio TI (Padrão Consumidor / Varejo E-commerce)")
    elif low_lex_sim and not tmpl:
        reasons.append(f"🌐 Baixa Aderência Lexical ao Domínio de TI (sim={centroid_similarity:.3f} < {min_domain_similarity:.3f})")

    if pii_count > 0:
        reasons.append(f"🔒 PII Sanitizada ({', '.join(pii_types)})")

    force_tier3 = bool(inj or high_risk or domain_shift)

    return GuardrailAssessment(
        sanitized_text=sanitized,
        pii_types_detected=pii_types,
        pii_count=pii_count,
        prompt_injection_detected=inj,
        high_risk_policy_triggered=high_risk,
        template_artifact_detected=tmpl,
        consumer_domain_shift_detected=domain_shift,
        force_human_tier3=force_tier3,
        guardrail_reasons=reasons,
    )
