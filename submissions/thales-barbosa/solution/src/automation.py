# -*- coding: utf-8 -*-
"""FASE 4 — Matriz de automação (fonte única).

Consumida por docs/automation_strategy.md (tabelas GERADAS por
``render_matrix_markdown``/``render_routing_markdown``), pelo protótipo da
FASE 6 (recomendação de automação e equipe sugerida no AI Copilot) e testada
contra as premissas de deflexão do ROI em tests/test_automation.py.

Regra de coerência (D-012/D-013): os percentuais de deflexão NÃO são
redigitados aqui — são importados de src/roi_model.py. Tier e deflexão têm
ordenação consistente, coberta por teste.

Critérios do plano mestre, avaliados por tipo/classe em escala 1-5:
- repetitividade: o mesmo pedido se repete com pouca variação?
- previsibilidade: a resposta correta é determinável por regra/consulta?
- risco: dano potencial de uma resposta errada (financeiro/legal/reputação).
- criticidade: urgência/impacto quando o caso é grave.
- julgamento_humano: quanto a resolução exige empatia/negociação/contexto.
"""
from __future__ import annotations

from src.roi_model import DEFLECTION_BY_TYPE

TIERS = ("automatizar", "parcial", "nao_automatizar")

#: Matriz principal — taxonomia B2C do Dataset 1 (5 tipos).
#: "tier" é a decisão para a RESOLUÇÃO do ticket; a TRIAGEM (classificar,
#: priorizar, rotear) é automatizada em 100% dos casos, em todos os tiers.
AUTOMATION_MATRIX_D1: dict[str, dict] = {
    "Product inquiry": {
        "tier": "automatizar",
        "criteria": {"repetitividade": 5, "previsibilidade": 5, "risco": 1,
                     "criticidade": 1, "julgamento_humano": 1},
        "automatiza": "respostas informacionais (compatibilidade, recomendação, "
                      "setup, specs) via base de conhecimento + RAG; FAQ dinâmico",
        "nunca_automatiza": "aconselhamento de compra com reclamação implícita; "
                            "cliente que já teve resposta automática e reabriu",
        "justificativa": "intent informacional puro: máxima repetição, resposta "
                         "verificável na base de produto, dano baixo se errar "
                         "(cliente corrige), zero negociação.",
    },
    "Billing inquiry": {
        "tier": "parcial",
        "criteria": {"repetitividade": 4, "previsibilidade": 4, "risco": 3,
                     "criticidade": 3, "julgamento_humano": 2},
        "automatiza": "consulta de cobrança/fatura, explicação de itens, 2ª via, "
                      "atualização de forma de pagamento com verificação",
        "nunca_automatiza": "disputa/contestação de cobrança, suspeita de fraude, "
                            "cobrança em duplicidade acima do limite definido",
        "justificativa": "consultas são previsíveis (dados no sistema), mas "
                         "disputas envolvem dinheiro e confiança — erro aqui "
                         "gera detrator e risco legal.",
    },
    "Refund request": {
        "tier": "parcial",
        "criteria": {"repetitividade": 4, "previsibilidade": 3, "risco": 4,
                     "criticidade": 3, "julgamento_humano": 3},
        "automatiza": "status do reembolso, elegibilidade por política clara, "
                      "processamento de casos dentro da política e abaixo do teto de valor",
        "nunca_automatiza": "exceções à política, valores acima do teto, cliente "
                            "reincidente ou com histórico de disputa",
        "justificativa": "movimenta dinheiro: automação só onde a política é "
                         "binária e o valor é baixo; o resto é decisão humana "
                         "com recomendação da IA.",
    },
    "Cancellation request": {
        "tier": "parcial",
        "criteria": {"repetitividade": 4, "previsibilidade": 3, "risco": 4,
                     "criticidade": 4, "julgamento_humano": 5},
        "automatiza": "confirmação de recebimento, coleta de motivo, execução "
                      "do cancelamento JÁ decidido, instruções pós-cancelamento",
        "nunca_automatiza": "a conversa de retenção — é negociação humana de "
                            "alto valor; IA prepara o contexto (motivo, LTV, "
                            "histórico), humano conduz",
        "justificativa": "o momento de maior valor em jogo por ticket; "
                         "automatizar a retenção destrói a última chance de "
                         "manter o cliente.",
    },
    "Technical issue": {
        "tier": "parcial",
        "criteria": {"repetitividade": 3, "previsibilidade": 2, "risco": 3,
                     "criticidade": 4, "julgamento_humano": 4},
        "automatiza": "triagem + coleta estruturada de sintomas, sugestões de "
                      "troubleshooting L1 (reiniciar/atualizar/verificar), "
                      "artigos relevantes; detecção de incidente em massa",
        "nunca_automatiza": "diagnóstico além de L1, perda de dados, segurança, "
                            "qualquer caso Critical — vai direto ao especialista "
                            "com contexto montado pela IA",
        "justificativa": "menor deflexão da matriz (premissa 10-30%): cada caso "
                         "varia; o ganho principal é ASSISTÊNCIA ao agente, não "
                         "substituição.",
    },
}

#: Regras TRANSVERSAIS de não-automação — valem para todos os tipos e têm
#: precedência sobre o tier (o fluxo as avalia ANTES da deflexão).
NEVER_AUTOMATE_RULES: list[dict] = [
    {"regra": "Sentimento negativo forte / cliente irritado",
     "motivo": "empatia é o produto; resposta automática a raiva fabrica detrator",
     "acao": "rotear a humano com prioridade elevada + contexto da IA"},
    {"regra": "Menção a advogado, Procon, órgão regulador ou imprensa",
     "motivo": "risco legal/reputacional supera qualquer economia",
     "acao": "fila especializada, resposta 100% humana, registro de auditoria"},
    {"regra": "Disputa financeira acima do teto (parâmetro do negócio)",
     "motivo": "erro tem custo direto e mina confiança",
     "acao": "humano decide; IA anexa política e histórico"},
    {"regra": "Cliente reabriu ticket após resposta automática",
     "motivo": "segunda tentativa automática = loop de frustração",
     "acao": "escalação obrigatória a humano (sem nova deflexão)"},
    {"regra": "Prioridade Critical",
     "motivo": "criticidade alta exige responsabilização humana imediata",
     "acao": "triagem automática apenas; resolução sempre humana"},
    {"regra": "Suspeita de fraude ou dados pessoais sensíveis",
     "motivo": "compliance/LGPD; IA não deve decidir nem expor",
     "acao": "fila restrita; mascaramento de PII no log"},
]

#: Roteamento por classe do Dataset 2 (taxonomia TI real — 47.823 docs).
#: Fundamenta o classificador da FASE 5 e a "equipe sugerida" do Copilot.
D2_CLASS_ROUTING: dict[str, dict] = {
    "Hardware": {"team": "Suporte de campo / TI local", "tier": "parcial",
                 "nota": "triagem + coleta de sintomas automáticas; troca física é humana"},
    "HR Support": {"team": "RH / People Ops", "tier": "parcial",
                   "nota": "consultas padrão (férias, folha) automatizáveis; casos pessoais são humanos"},
    "Access": {"team": "IAM / Segurança", "tier": "automatizar",
               "nota": "reset de senha/acesso padrão = automação clássica COM verificação de identidade"},
    "Administrative rights": {"team": "IAM / Segurança", "tier": "nao_automatizar",
                              "nota": "concessão de privilégio é decisão de segurança — aprovação humana sempre; IA só triagem"},
    "Storage": {"team": "Infraestrutura", "tier": "automatizar",
                "nota": "quota/mailbox cheio = self-healing (expansão automática com limites e log)"},
    "Purchase": {"team": "Compras / Procurement", "tier": "parcial",
                 "nota": "cotação/status automatizáveis; aprovação de gasto é humana"},
    "Internal Project": {"team": "PMO / responsável do projeto", "tier": "nao_automatizar",
                         "nota": "contexto de projeto específico; IA apenas classifica e roteia"},
    "Miscellaneous": {"team": "Triagem humana", "tier": "nao_automatizar",
                      "nota": "classe guarda-chuva (14,8%): confusão esperada do classificador — "
                              "threshold de confiança manda para humano (D-007)"},
}


def render_matrix_markdown() -> str:
    """Tabela da matriz D1 em markdown — GERADA do código (fonte única)."""
    lines = [
        "| Tipo (D1) | Decisão (resolução) | Deflexão (low/base/high) | R | P | Ri | C | J | O que automatiza | O que NUNCA automatiza |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    labels = {"automatizar": "**Automatizar**", "parcial": "**Parcial**",
              "nao_automatizar": "**Não automatizar**"}
    for t, m in AUTOMATION_MATRIX_D1.items():
        d = DEFLECTION_BY_TYPE[t]
        c = m["criteria"]
        lines.append(
            f"| {t} | {labels[m['tier']]} | {d['low']:.0%} / **{d['base']:.0%}** / {d['high']:.0%} "
            f"| {c['repetitividade']} | {c['previsibilidade']} | {c['risco']} | {c['criticidade']} "
            f"| {c['julgamento_humano']} | {m['automatiza']} | {m['nunca_automatiza']} |"
        )
    return "\n".join(lines)


def render_routing_markdown() -> str:
    """Tabela de roteamento D2 em markdown — GERADA do código."""
    labels = {"automatizar": "Automatizar", "parcial": "Parcial",
              "nao_automatizar": "Não automatizar"}
    lines = ["| Classe (D2) | Equipe sugerida | Decisão | Nota |", "|---|---|---|---|"]
    for cls, r in D2_CLASS_ROUTING.items():
        lines.append(f"| {cls} | {r['team']} | {labels[r['tier']]} | {r['nota']} |")
    return "\n".join(lines)
