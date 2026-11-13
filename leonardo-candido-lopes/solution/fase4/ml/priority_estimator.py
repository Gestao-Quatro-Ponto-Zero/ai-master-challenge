"""Fase 4 — Etapa 7: priorização por REGRAS explícitas (não ML).
Por que não ML: o D2 não tem rótulo de prioridade; a prioridade do D1 é sintética e independente do texto (Fase 2:
12/12 pares de variáveis independentes). Treinar um modelo de prioridade seria aprender ruído. Regras são auditáveis
e ajustáveis pelo time de operações até existir histórico real de prioridade/SLA.
Saída: LOW | MEDIUM | HIGH | CRITICAL + justificativa."""
import re

LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
# prioridade base por categoria (proposta para validação com o time de operações)
CATEGORY_BASE = {
    "Access": "MEDIUM",                 # bloqueio de acesso impede trabalho
    "Administrative rights": "MEDIUM",  # risco de segurança; sempre revisado por humano
    "Hardware": "MEDIUM",
    "Storage": "LOW",
    "Purchase": "LOW",
    "HR Support": "LOW",
    "Internal Project": "LOW",
    "Miscellaneous": "LOW",
}
# padrões (inglês + português) — escopo amplo / incidente
CRITICAL_PATTERNS = [
    r"\b(entire|whole|all)\b.{0,30}\b(network|system|systems|office|company|servers?)\b.{0,30}\b(down|outage|offline|unavailable)\b",
    r"\b(network|system|server|servers|site|production)\b.{0,15}\b(is |are )?(down|outage|offline)\b",
    r"\bno one can\b", r"\bnobody can\b", r"\beveryone\b.{0,20}\b(cannot|can't|unable)\b",
    r"\b(ransomware|data breach|security breach|vazamento de dados)\b",
    r"\b(fora do ar|rede caiu|sistema caiu|ningu[eé]m consegue)\b",
]
HIGH_PATTERNS = [
    r"\burgent(e|ly)?\b", r"\basap\b", r"\bcritical\b", r"\bcr[ií]tico\b", r"\bimmediately\b", r"\bemergency\b",
    r"\bcannot work\b", r"\bcan'?t work\b", r"\bunable to work\b", r"\bblocked\b", r"\bbloquead[oa]\b", r"\bn[aã]o consigo trabalhar\b",
    r"\b(hacked|compromised|unauthori[sz]ed access|invas[aã]o|atacad[oa]|credenciais vazadas)\b",
]
# palavras de urgência leves elevam LOW -> MEDIUM
MEDIUM_PATTERNS = [r"\btoday\b", r"\bdeadline\b", r"\bnot working\b", r"\bbroken\b", r"\bhoje\b", r"\bprazo\b", r"\bn[aã]o funciona\b"]


def _hits(text, pats):
    return [p for p in pats if re.search(p, text, flags=re.I)]


def estimate_priority(text, category=None):
    t = str(text)
    base = CATEGORY_BASE.get(category, "MEDIUM")
    reasons = [f"base por categoria '{category}' = {base}" if category in CATEGORY_BASE else "categoria desconhecida -> base MEDIUM"]
    lvl = LEVELS.index(base)
    c, h, m = _hits(t, CRITICAL_PATTERNS), _hits(t, HIGH_PATTERNS), _hits(t, MEDIUM_PATTERNS)
    if c:
        lvl = 3; reasons.append(f"padrão de incidente amplo/crítico: {c[0]}")
    elif h:
        lvl = max(lvl, 2); reasons.append(f"palavra de urgência/segurança: {h[0]}")
    elif m:
        lvl = max(lvl, 1); reasons.append(f"sinal leve de urgência: {m[0]}")
    return dict(priority=LEVELS[lvl], justification="; ".join(reasons), matched=dict(critical=c, high=h, medium=m))
