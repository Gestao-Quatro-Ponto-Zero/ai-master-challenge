# -*- coding: utf-8 -*-
"""FASE 6 — AI Support Copilot: orquestra classificador, busca, matriz e regras.

Junta as peças já testadas em uma única análise por ticket:
- categoria + confiança + gate (src/ticket_ai.py — FASE 5)
- prioridade sugerida (HEURÍSTICA de demonstração — ver nota abaixo)
- vetos de automação (regras da FASE 4, detecção por palavras-chave — demo)
- recomendação de automação + equipe sugerida (src/automation.py)
- tickets semelhantes (FAISS) + resposta sugerida (template por classe)

NOTAS DE HONESTIDADE (exibidas no app):
- A prioridade é heurística por palavras-chave: o dataset de treino (D2) não
  tem rótulo de prioridade. Em produção: modelo treinado com rótulos reais.
- A resposta sugerida é template por classe + casos semelhantes. Em produção:
  LLM com RAG sobre a base de conhecimento, atrás dos mesmos vetos e gate.
"""
from __future__ import annotations

import re

import pandas as pd

from src.automation import D2_CLASS_ROUTING, NEVER_AUTOMATE_RULES

# ---------------------------------------------------------------------------
# Prioridade sugerida (heurística demo)
# ---------------------------------------------------------------------------
_PRIORITY_PATTERNS: list[tuple[str, str, str]] = [
    # (prioridade, padrão regex, razão exibida) — bilíngue en/pt-BR (D-018)
    ("Critical", r"\b(urgent|urgently|asap|immediately|critical|emergency|outage|"
                 r"production down|all users|cannot work|blocked completely|"
                 r"urgente|urg[êe]ncia|imediatamente|cr[íi]tico|emerg[êe]ncia|"
                 r"parou tudo|todos os usu[áa]rios|n[ãa]o consigo trabalhar|"
                 r"totalmente bloqueado|fora do ar)\b",
     "linguagem de urgência/bloqueio total"),
    ("High", r"\b(cannot|can't|unable|broken|error|fail(ed|ing)?|not working|"
             r"deadline|today|expired?|"
             r"n[ãa]o consigo|n[ãa]o funciona|quebrado|erro|falha(ndo|s)?|"
             r"prazo|hoje|expirou|expirad[oa]|travad[oa]|bloquead[oa])\b",
     "impedimento funcional ou prazo"),
    ("Low", r"\b(question|how to|wondering|when possible|no rush|whenever|fyi|"
            r"d[úu]vida|como fa[çc]o|quando poss[íi]vel|sem pressa|"
            r"quando puder|curiosidade)\b",
     "consulta sem urgência"),
]


def suggest_priority(text: str) -> dict:
    """Prioridade heurística por palavras-chave (demo). Default: Medium."""
    t = text.lower()
    for prio, pat, reason in _PRIORITY_PATTERNS:
        if re.search(pat, t):
            return {"priority": prio, "reason": reason, "method": "heurística (demo)"}
    return {"priority": "Medium", "reason": "sem marcadores de urgência ou trivialidade",
            "method": "heurística (demo)"}


# ---------------------------------------------------------------------------
# Vetos de automação (FASE 4 §3) — detecção textual de demonstração
# ---------------------------------------------------------------------------
_VETO_PATTERNS: dict[str, str] = {
    "Menção a advogado, Procon, órgão regulador ou imprensa":
        r"\b(lawyer|attorney|legal action|lawsuit|sue|procon|regulator|press|media|"
        r"advogad[oa]|justi[çc]a|processo judicial|processar|a[çc][ãa]o judicial|"
        r"[óo]rg[ãa]o regulador|imprensa|jornalista)\b",
    "Sentimento negativo forte / cliente irritado":
        r"\b(furious|outraged|unacceptable|disgusted|worst|terrible service|"
        r"angry|fed up|ridiculous|"
        r"inaceit[áa]vel|absurdo|rid[íi]culo|indignad[oa]|revoltad[oa]|"
        r"p[ée]ssimo (atendimento|servi[çc]o)|vergonha|cansei|de saco cheio)\b",
    "Suspeita de fraude ou dados pessoais sensíveis":
        r"\b(fraud|fraudulent|stolen|identity theft|unauthorized (charge|access)|"
        r"fraude|fraudulent[oa]|roubad[oa]|roubo|clonad[oa]|"
        r"cobran[çc]a (indevida|n[ãa]o (reconhecida|autorizada))|"
        r"acesso (indevido|n[ãa]o autorizado)|vazamento de dados)\b",
}


def detect_vetoes(text: str) -> list[dict]:
    """Regras de veto disparadas pelo texto (subset textual das 6 da FASE 4)."""
    t = text.lower()
    hits = []
    rules = {r["regra"]: r for r in NEVER_AUTOMATE_RULES}
    for rule_name, pat in _VETO_PATTERNS.items():
        if re.search(pat, t):
            hits.append(rules[rule_name])
    return hits


# ---------------------------------------------------------------------------
# Resposta sugerida (template por classe — demo)
# ---------------------------------------------------------------------------
_RESPONSE_PLAYBOOK: dict[str, str] = {
    "Access": "confirmar a conta/sistema afetado, verificar a identidade pelo canal "
              "padrão e disparar o procedimento de reset de senha/acesso",
    "Administrative rights": "registrar o pedido de privilégio, identificar o aprovador "
                             "do sistema-alvo e encaminhar para aprovação humana de segurança",
    "HR Support": "confirmar o colaborador e o módulo de RH envolvido e rotear para "
                  "People Ops com o resumo do pedido",
    "Hardware": "coletar o patrimônio e os sintomas, executar o checklist básico (cabos, "
                "reinicialização, atualizações) e agendar suporte de campo se não resolver",
    "Internal Project": "identificar o projeto e encaminhar ao responsável no PMO "
                        "com o contexto completo",
    "Miscellaneous": "confirmar o recebimento e rotear para triagem humana para "
                     "categorização correta",
    "Purchase": "confirmar item/especificações e centro de custo e abrir a requisição "
                "de compra para aprovação",
    "Storage": "verificar a cota atual, aplicar a expansão padrão (dentro dos limites "
               "de política) e confirmar com o usuário",
}

#: Autoatendimento do PORTAL (D-018): passos que o PRÓPRIO CLIENTE consegue
#: executar, por classe — tom de produto, sem jargão interno.
PORTAL_PLAYBOOK: dict[str, str] = {
    "Access": "Use a recuperação de senha ('esqueci minha senha'), confirme se o e-mail "
              "de login está correto e aguarde alguns minutos antes de tentar de novo — "
              "bloqueios temporários expiram sozinhos. Se suspeitar de acesso indevido, "
              "abra um chamado imediatamente.",
    "Administrative rights": "Pedidos de permissão ou privilégio passam por aprovação "
              "humana de segurança — não são liberados automaticamente. Abra um chamado "
              "informando o sistema e a permissão necessária; seu pedido já vai "
              "qualificado para o aprovador.",
    "HR Support": "Consultas padrão (férias, folha, benefícios) costumam estar no portal "
              "de RH. Se o seu caso é pessoal ou sensível, abra um chamado — ele vai "
              "direto para People Ops, com sigilo.",
    "Hardware": "Teste o básico primeiro: cabos e conexões, reiniciar o equipamento e "
              "verificar atualizações pendentes. Se a falha continuar ou for recorrente, "
              "abra um chamado com o modelo do equipamento e o que você já tentou.",
    "Internal Project": "Assuntos de projeto dependem do contexto do time responsável. "
              "Abra um chamado citando o nome do projeto — ele será roteado ao "
              "responsável direto, com seu texto como contexto.",
    "Miscellaneous": "Seu caso não se encaixa com segurança em nenhuma categoria comum. "
              "Para não te dar uma resposta errada, o melhor caminho é abrir um chamado — "
              "a triagem humana categoriza e prioriza rapidinho.",
    "Purchase": "Consulta de status ou cotação: tenha em mãos o número do pedido. "
              "Aprovações de compra são sempre humanas — abra um chamado com item, "
              "quantidade e justificativa que ele já chega qualificado ao aprovador.",
    "Storage": "Espaço cheio costuma se resolver liberando arquivos temporários ou "
              "esvaziando a lixeira. Se a cota estourou mesmo assim, abra um chamado — "
              "expansões padrão são aplicadas com rapidez.",
}


def suggest_response(label: str, similar: pd.DataFrame) -> str:
    """Template por classe + referência aos semelhantes (demo; produção = LLM+RAG)."""
    action = _RESPONSE_PLAYBOOK.get(label, _RESPONSE_PLAYBOOK["Miscellaneous"])
    n_sim = len(similar)
    same = int((similar["Topic_group"].astype(str) == label).sum()) if n_sim else 0
    return (
        f"Olá! Obrigado pelo contato — entendi seu caso como **{label}**.\n\n"
        f"Próximos passos: {action}.\n\n"
        f"_Baseado em {n_sim} tickets semelhantes já resolvidos "
        f"({same} da mesma categoria). Template de demonstração — em produção, "
        f"gerado por LLM+RAG sob os mesmos vetos e gate de confiança._"
    )


# ---------------------------------------------------------------------------
# Análise completa (contrato do app)
# ---------------------------------------------------------------------------

#: Piso de EVIDÊNCIA (D-018): além do gate de confiança do classificador, a
#: ação automática exige que a busca semântica encontre caso suficientemente
#: parecido no arquivo. Pega o modo de falha do cross-lingual em texto vago /
#: fora de domínio: o classificador fica superconfiante na classe majoritária,
#: mas a similaridade máxima denuncia a ausência de casos de apoio.
SIM_EVIDENCE_FLOOR = 0.55


def analyze(text: str, ai) -> dict:
    """Análise completa de um ticket — tudo que o plano exige do Copilot."""
    cls = ai.classify(text)
    vetoes = detect_vetoes(text)
    prio = suggest_priority(text)
    if vetoes and prio["priority"] in ("Low", "Medium"):
        prio = {"priority": "High", "reason": "elevada por regra de veto (FASE 4 §3)",
                "method": "regra"}
    similar = ai.find_similar(text, k=5)
    routing = D2_CLASS_ROUTING[cls["label"]]

    evidence = float(similar["similarity"].iloc[0]) if len(similar) else 0.0
    cls["evidence"] = round(evidence, 3)
    cls["evidence_ok"] = evidence >= SIM_EVIDENCE_FLOOR
    cls["conf_ok"] = cls["auto_ok"]                      # gate do classificador, isolado
    cls["auto_ok"] = cls["conf_ok"] and cls["evidence_ok"]  # dupla trava efetiva

    if vetoes:
        recommendation = "NÃO automatizar — regra de veto disparada (humano com prioridade)"
    elif not cls["conf_ok"]:
        recommendation = "Triagem humana — confiança abaixo do gate (IA apenas sugere)"
    elif not cls["evidence_ok"]:
        recommendation = ("Triagem humana — sem casos suficientemente parecidos no arquivo "
                          "(evidência abaixo do piso)")
    elif routing["tier"] == "automatizar":
        recommendation = "Automação plena elegível (com escape hatch)"
    elif routing["tier"] == "parcial":
        recommendation = "Automação parcial — agente com Copilot (resposta sugerida + contexto)"
    else:
        recommendation = "Não automatizar resolução — IA faz triagem e roteamento apenas"

    return {
        "classification": cls,
        "priority": prio,
        "vetoes": vetoes,
        "routing": routing,
        "recommendation": recommendation,
        "similar": similar,
        "suggested_response": suggest_response(cls["label"], similar),
    }
