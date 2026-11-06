"""Política conservadora de sugestão, separada do modelo temático."""

import re

DOMAIN_IT = "TI interna em inglês"
DOMAIN_OTHER = "Outro ou desconhecido"
REVIEW = "revisao_humana"
SUGGEST = "sugestao_de_roteamento"
MAX_CHARS = 8000
MIN_TOKENS = 3
MIN_KNOWN = 2
MIN_OVERLAP = 0.45

WORDS = re.compile(r"(?u)\b[^\W\d_]+(?:['’-][^\W\d_]+)*\b")
RISK = re.compile(
    r"\b(?:fraud\w*|fraude|phishing|ransomware|data (?:leak|breach)|security incident|"
    r"malware|hacked|refund\w*|estorno|reembolso|chargeback|"
    r"grant (?:me |them )?(?:admin\w* |user )?(?:access|permission\w*)|"
    r"(?:admin\w*|root) (?:access|rights|permission\w*)|"
    r"delete (?:all |the )?(?:data|database|files)|"
    r"permiss[aã]o|vazamento|incidente de seguran[çc]a)\b",
    re.I,
)
RISK_CLASSES = frozenset({"Administrative rights"})


def input_reasons(text: str, domain: str, priority: str) -> list[str]:
    reasons = []
    if domain != DOMAIN_IT:
        reasons.append("Domínio ou idioma fora do escopo declarado.")
    if priority.casefold() in {"critical", "crítica", "critica"}:
        reasons.append("Prioridade crítica preservada.")
    if len(text) > MAX_CHARS:
        reasons.append(f"Texto excede {MAX_CHARS} caracteres.")
        return reasons
    if len(WORDS.findall(text)) < MIN_TOKENS:
        reasons.append("Texto insuficiente para classificação.")
    if RISK.search(text):
        reasons.append("Termo sensível identificado por regra.")
    return reasons


def model_reasons(category: str, overlap: float, known: int) -> list[str]:
    reasons = []
    if category in RISK_CLASSES:
        reasons.append("Categoria de acesso privilegiado exige revisão.")
    if known < MIN_KNOWN or overlap < MIN_OVERLAP:
        reasons.append("Vocabulário pouco compatível com o treino.")
    return reasons


def decide(reasons: list[str], score: float | None, threshold: float):
    reasons = list(reasons)
    if score is not None and score < threshold:
        reasons.append("Score abaixo do limiar de validação.")
    if reasons or score is None:
        return REVIEW, reasons
    return SUGGEST, ["Domínio declarado, guardas satisfeitas e score acima do corte."]
