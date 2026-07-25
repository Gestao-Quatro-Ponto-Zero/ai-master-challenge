from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CustomerCareAssessment:
    level: str
    requires_human: bool
    signal_codes: tuple[str, ...]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


CUSTOMER_CARE_RULES = (
    (
        "UNRESOLVED_OR_REPEAT_CONTACT",
        (
            r"\bsem solucao\b",
            r"\bnao resolv",
            r"\bninguem responde\b",
            r"\bja (?:entrei|falei|liguei|procurei)\b",
            r"\bvarias vezes\b",
            r"\bstill unresolved\b",
            r"\bno response\b",
            r"\bmultiple times\b",
        ),
        "O cliente relata repetição de contato ou problema ainda não resolvido.",
    ),
    (
        "FINANCIAL_HARM",
        (
            r"\bcobranca indevida\b",
            r"\bcobrad[oa] duas vezes\b",
            r"\bcobranca duplicada\b",
            r"\breembolso\b",
            r"\bduplicate charge\b",
            r"\bcharged twice\b",
            r"\brefund\b",
        ),
        "Existe possível prejuízo financeiro ou pedido de devolução.",
    ),
    (
        "CANCELLATION_OR_CHURN",
        (
            r"\bcancelar\b",
            r"\bcancelamento\b",
            r"\bnao quero mais\b",
            r"\bcancel my\b",
            r"\bcancellation\b",
        ),
        "O cliente sinaliza cancelamento ou risco de encerramento da relação.",
    ),
    (
        "LEGAL_OR_PUBLIC_ESCALATION",
        (
            r"\bprocon\b",
            r"\breclame aqui\b",
            r"\badvogad",
            r"\bprocesso\b",
            r"\blawsuit\b",
            r"\blegal action\b",
        ),
        "A mensagem contém possível escalonamento jurídico ou público.",
    ),
    (
        "SAFETY_PRIVACY_OR_ABUSE",
        (
            r"\bassedio\b",
            r"\bdiscriminacao\b",
            r"\bameaca\b",
            r"\bvazamento de dados\b",
            r"\bfraude\b",
            r"\bharassment\b",
            r"\bdiscrimination\b",
            r"\bthreat\b",
            r"\bdata leak\b",
            r"\bfraud\b",
        ),
        "Há possível risco de segurança, privacidade, abuso ou discriminação.",
    ),
    (
        "STRONG_DISSATISFACTION",
        (
            r"\babsurdo\b",
            r"\bpessim",
            r"\binsatisfeit",
            r"\bdecepcionad",
            r"\binaceitavel\b",
            r"\bunacceptable\b",
            r"\bterrible\b",
            r"\bvery disappointed\b",
        ),
        "O cliente demonstra insatisfação forte e precisa de cuidado humano.",
    ),
)


def _normalize(value: str) -> str:
    without_accents = "".join(
        character
        for character in unicodedata.normalize("NFKD", value.lower())
        if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", without_accents).strip()


def assess_customer_care(text: str) -> CustomerCareAssessment:
    normalized = _normalize(text)
    codes = []
    reasons = []
    for code, patterns, reason in CUSTOMER_CARE_RULES:
        if any(re.search(pattern, normalized) for pattern in patterns):
            codes.append(code)
            reasons.append(reason)

    return CustomerCareAssessment(
        level="critical" if codes else "standard",
        requires_human=bool(codes),
        signal_codes=tuple(codes),
        reasons=tuple(reasons),
    )
