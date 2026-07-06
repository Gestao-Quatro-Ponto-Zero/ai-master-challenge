"""Biblioteca de ganchos comerciais por perfil DISC."""
from __future__ import annotations

from typing import Any


def _base_hooks() -> list[dict[str, str]]:
    return [
        {
            "hook": "Reforcar prioridade de negocio da semana",
            "why_it_works": "Traz foco pratico e reduz dispersao no follow-up.",
            "opening_question": "Se voce tivesse que priorizar um resultado ate sexta, qual seria?",
            "risk_if_badly_used": "Pode soar generico se nao conectar com o contexto do deal.",
        },
        {
            "hook": "Ancorar em proximo passo objetivo",
            "why_it_works": "Transforma conversa em acao concreta e mensuravel.",
            "opening_question": "Podemos definir agora um proximo passo com data e responsavel?",
            "risk_if_badly_used": "Sem empatia, pode parecer pressao excessiva.",
        },
        {
            "hook": "Validar risco de inercia",
            "why_it_works": "Ajuda o lead a perceber custo de adiar a decisao.",
            "opening_question": "Se nada mudar nas proximas 4 semanas, qual impacto voce espera?",
            "risk_if_badly_used": "Tom alarmista pode gerar resistencia.",
        },
    ]


PROFILE_HOOKS: dict[str, list[dict[str, str]]] = {
    "D": [
        {
            "hook": "Ganhos rapidos com marco de 15 dias",
            "why_it_works": "Perfil D valoriza velocidade e resultado tangivel.",
            "opening_question": "Qual metrica precisa melhorar ja nos proximos 15 dias?",
            "risk_if_badly_used": "Prometer resultado sem condicao real quebra confianca.",
        },
        {
            "hook": "Comparativo antes e depois",
            "why_it_works": "Facilita decisao com contraste direto de impacto.",
            "opening_question": "Hoje, qual gargalo mais pesa no seu resultado comercial?",
            "risk_if_badly_used": "Comparacao vaga enfraquece a proposta.",
        },
        {
            "hook": "Plano enxuto com dono e prazo",
            "why_it_works": "D responde bem a clareza de execucao.",
            "opening_question": "Topa alinharmos um plano de 3 passos com prazo de inicio?",
            "risk_if_badly_used": "Excesso de detalhe pode tirar ritmo da conversa.",
        },
    ],
    "I": [
        {
            "hook": "Historia curta de resultado parecido",
            "why_it_works": "Perfil I tende a engajar com narrativa social.",
            "opening_question": "Faz sentido eu te mostrar um caso curto parecido com seu contexto?",
            "risk_if_badly_used": "Case longo demais pode cansar.",
        },
        {
            "hook": "Cocricao de proximo passo",
            "why_it_works": "Aumenta adesao quando o lead participa da construcao.",
            "opening_question": "Qual formato de avancar seria mais confortavel para voce?",
            "risk_if_badly_used": "Sem direcionamento, a conversa perde objetividade.",
        },
        {
            "hook": "Energia no beneficio imediato",
            "why_it_works": "I responde bem a visao de ganho pratico e motivador.",
            "opening_question": "Qual vitoria rapida mais te animaria neste trimestre?",
            "risk_if_badly_used": "Tom informal em excesso reduz credibilidade.",
        },
    ],
    "S": [
        {
            "hook": "Plano de transicao sem ruptura",
            "why_it_works": "Perfil S prioriza seguranca e previsibilidade.",
            "opening_question": "Que condicao precisa existir para voce avancar com tranquilidade?",
            "risk_if_badly_used": "Acelerar demais gera bloqueio.",
        },
        {
            "hook": "Reducao de risco operacional",
            "why_it_works": "Mostra cuidado com continuidade do processo atual.",
            "opening_question": "Qual risco operacional voce mais quer evitar nessa decisao?",
            "risk_if_badly_used": "Focar so em risco pode deixar a proposta defensiva.",
        },
        {
            "hook": "Ritmo combinado de implementacao",
            "why_it_works": "Acordo de cadencia reduz ansiedade de mudanca.",
            "opening_question": "Faz sentido definirmos um ritmo semanal simples de acompanhamento?",
            "risk_if_badly_used": "Cadencia vaga nao transmite seguranca.",
        },
    ],
    "C": [
        {
            "hook": "Criterios objetivos de decisao",
            "why_it_works": "Perfil C precisa de base racional para aprovar.",
            "opening_question": "Quais 3 criterios tecnicos vao pesar mais na sua decisao final?",
            "risk_if_badly_used": "Argumento sem dado concreto perde forca.",
        },
        {
            "hook": "Hipotese + metrica de validacao",
            "why_it_works": "Conecta proposta com metodo e verificacao.",
            "opening_question": "Podemos validar juntos uma hipotese com metrica clara em 2 semanas?",
            "risk_if_badly_used": "Detalhe tecnico excessivo trava a conversa.",
        },
        {
            "hook": "Comparativo estruturado de opcoes",
            "why_it_works": "Facilita analise sem ruida emocional.",
            "opening_question": "Prefere que eu organize um comparativo simples entre as alternativas?",
            "risk_if_badly_used": "Comparativo enviesado pode gerar desconfianca.",
        },
    ],
}


def get_sales_hooks(lead_profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Retorna 3-5 ganchos priorizados por DISC.

    Se DISC indefinido, usa estrategia neutra baseada no contexto.
    """
    disc_profile = str(lead_profile.get("disc_profile", "indefinido"))
    profile_hooks = PROFILE_HOOKS.get(disc_profile, _base_hooks())

    selected = profile_hooks[:3]
    if len(selected) < 3:
        selected = (selected + _base_hooks())[:3]

    hooks: list[dict[str, Any]] = []
    for idx, item in enumerate(selected, start=1):
        hooks.append(
            {
                "priority": idx,
                "hook": item["hook"],
                "why_it_works": item["why_it_works"],
                "opening_question": item["opening_question"],
                "risk_if_badly_used": item["risk_if_badly_used"],
            }
        )
    return hooks


def get_next_best_action(lead_profile: dict[str, Any], hooks: list[dict[str, Any]]) -> str:
    """Recomenda proxima melhor acao com base em DISC + contexto."""
    disc_profile = str(lead_profile.get("disc_profile", "indefinido"))
    owner = lead_profile.get("owner") or "vendedor responsavel"
    stage = lead_profile.get("deal_stage") or "estagio atual"

    if hooks:
        top_question = hooks[0].get("opening_question", "")
    else:
        top_question = "Podemos alinhar o proximo passo com data?"

    action_map = {
        "D": f"{owner}: abrir contato hoje com proposta de decisao rapida e fechar proximo passo em 48h. Pergunta-chave: {top_question}",
        "I": f"{owner}: conduzir follow-up relacional com CTA claro para conversa curta ainda esta semana. Pergunta-chave: {top_question}",
        "S": f"{owner}: conduzir follow-up com plano previsivel e foco em seguranca de implementacao no estagio {stage}. Pergunta-chave: {top_question}",
        "C": f"{owner}: enviar comparativo objetivo + criterio de validacao antes da proxima reuniao. Pergunta-chave: {top_question}",
        "indefinido": f"{owner}: validar contexto do lead e confirmar dor principal antes da proposta final. Pergunta-chave: {top_question}",
    }
    return action_map.get(disc_profile, action_map["indefinido"])
