"""Fase 4 — Etapa 6: regras de segurança EXPLÍCITAS (não ML) que convertem classificação -> decisão operacional.
Saídas: AUTOMATIC | ASSISTED | HUMAN_REQUIRED | ESCALATE.
Ordem de avaliação = ordem de severidade (a primeira regra que dispara decide). Thresholds vêm de model/model_metadata.json
(empíricos, definidos no conjunto de validação — Etapa 4), não de valores fixos."""
import json, re, os

_META = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "model_metadata.json")

COMPROMISE_PATTERNS = [
    r"\bcompromised?\b", r"\bunauthori[sz]ed (access|login|charges?|transactions?)\b", r"\bhack(ed|er|ing)?\b",
    r"\bphishing\b", r"\bleaked credentials?\b", r"\bstolen (password|credentials?|account)\b",
    r"\batacad[oa]s?\b", r"\binvas[aã]o\b", r"\binvadid[oa]\b", r"\bcredenciais vazadas\b", r"\bcomprometid[oa]s?\b", r"\bsenha vazada\b",
]

PRIVILEGE_PATTERNS = [
    r"\badmin(istrator|istrative)?\b", r"\bsudo\b", r"\broot (access|password|privileges?)\b", r"\bprivileges?\b", r"\belevated (access|rights|permissions?)\b",
    r"\blocal admin\b", r"\bdomain admin\b", r"\bpermiss[aã]o de administrador\b", r"\bacesso (de )?admin(istrador)?\b", r"\bprivil[eé]gios?\b",
]

RULES_DOC = {
    "R1_ACCOUNT_COMPROMISE": "Texto indica comprometimento de conta/credencial -> ESCALATE (segurança da informação; independe do domínio e da confiança).",
    "R2_DOMAIN_NOT_IT": "Domínio != IT_INTERNAL (FINANCIAL_COMMERCIAL, OUT_OF_SCOPE, INDETERMINATE) -> HUMAN_REQUIRED (fila dedicada / triagem humana).",
    "R3_CRITICAL_LOW_CONF": "Prioridade CRITICAL e confiança < threshold_alto -> ESCALATE (incidente grave sem certeza da categoria).",
    "R4_ADMIN_RIGHTS": "Categoria Administrative rights OU texto com termos de privilégio (admin, sudo, root, privilege, elevated access) -> HUMAN_REQUIRED. Regra textual protege contra erro do classificador (v2, após falha do caso 5).",
    "R5_LOW_CONFIDENCE": "Confiança < threshold_baixo -> HUMAN_REQUIRED ('sem confiança suficiente — encaminhar para revisão humana').",
    "R6_CRITICAL_NEVER_AUTO": "Prioridade CRITICAL (com confiança >= threshold_alto) -> ASSISTED no máximo (nunca AUTOMATIC).",
    "R7_MID_CONFIDENCE": "threshold_baixo <= confiança < threshold_alto -> ASSISTED (agente confirma a sugestão).",
    "R8_HIGH_CONFIDENCE": "Confiança >= threshold_alto, sem nenhuma regra acima -> seria AUTOMATIC (roteamento automático). ATUALMENTE INALCANÇÁVEL: a R9 (abaixo) sempre intercepta este ramo e rebaixa para ASSISTED, porque o detector de domínio não é validado. Mantido na documentação para registrar a intenção de projeto; nenhum caso atinge AUTOMATIC enquanto a R9 estiver ativa.",
    "R9_DOMAIN_NOT_VALIDATED": "Barreira conservadora antes da automação (v4). O detector de domínio NÃO é validado (treinado só com negativos sintéticos; não há sinal validado que comprove pertencimento ao domínio). Logo, confiança elevada da CATEGORIA NÃO autoriza ação automática. No ramo que iria para AUTOMATIC, rebaixa para ASSISTED (mantém o humano no loop). Só RESTRINGE, nunca afrouxa. Nota: na v3 usava-se um limiar de similaridade mínima (AUTO_MIN_SIM=0.49), REMOVIDO — a auditoria de 10/11/2026 mostrou que o 0.49 vinha de uma população MISTA (IT in-domain + FC fora de domínio), não da mediana in-domain, e que a similaridade com o treino NÃO discrimina domínio (textos FC fora de escopo pontuam mais alto que chamados de TI legítimos).",
}

# Regras que SOBREPÕEM a decisão do classificador: quando uma delas dispara, a CATEGORIA prevista pelo modelo
# NÃO deve ser tratada como orientação confiável (a decisão operacional foi corrigida, mas a categoria pode estar errada).
# A categoria crua é SEMPRE preservada para rastreabilidade; apenas sinalizada como não confiável.
UNRELIABLE_CATEGORY_RULES = {
    "R1_ACCOUNT_COMPROMISE",
    "R3_CRITICAL_LOW_CONF",
    "R4_ADMIN_RIGHTS",
    "R5_LOW_CONFIDENCE",
    "R9_DOMAIN_NOT_VALIDATED",
}


def load_thresholds(path=_META):
    m = json.load(open(path))
    return m["thresholds"]["threshold_baixo"], m["thresholds"]["threshold_alto"]


def decide(text, domain, category, confidence, priority, th_low=None, th_high=None):
    if th_low is None or th_high is None:
        th_low, th_high = load_thresholds()
    hits = [p for p in COMPROMISE_PATTERNS if re.search(p, str(text), flags=re.I)]
    if hits:
        return "ESCALATE", "R1_ACCOUNT_COMPROMISE", f"padrão de comprometimento: {hits[0]}"
    if domain != "IT_INTERNAL":
        return "HUMAN_REQUIRED", "R2_DOMAIN_NOT_IT", f"domínio {domain}"
    if priority == "CRITICAL" and confidence < th_high:
        return "ESCALATE", "R3_CRITICAL_LOW_CONF", f"CRITICAL com confiança {confidence:.3f} < {th_high}"
    priv = [p for p in PRIVILEGE_PATTERNS if re.search(p, str(text), flags=re.I)]
    if category == "Administrative rights" or priv:
        src = "categoria prevista" if category == "Administrative rights" else f"termo de privilégio no texto ({priv[0]})"
        return "HUMAN_REQUIRED", "R4_ADMIN_RIGHTS", f"privilégios administrativos exigem aprovação humana — {src}"
    if confidence < th_low:
        return "HUMAN_REQUIRED", "R5_LOW_CONFIDENCE", f"sem confiança suficiente ({confidence:.3f} < {th_low}) — encaminhar para revisão humana"
    if priority == "CRITICAL":
        return "ASSISTED", "R6_CRITICAL_NEVER_AUTO", "incidente crítico nunca é automático"
    if confidence < th_high:
        return "ASSISTED", "R7_MID_CONFIDENCE", f"confiança {confidence:.3f} entre {th_low} e {th_high}"
    # R9: barreira conservadora antes da automação. O detector de domínio NÃO é validado e não há
    # sinal validado que comprove pertencimento ao domínio; confiança alta da categoria NÃO a substitui.
    # Sem evidência suficiente para liberar automação com segurança -> ASSISTED (mantém o humano no loop).
    return "ASSISTED", "R9_DOMAIN_NOT_VALIDATED", f"detector de domínio não validado — confiança da categoria ({confidence:.3f}) não autoriza ação automática; mantém revisão assistida"
