"""
Motor de triagem: pipeline completo com Gemini (RAG + LLM) e fallback local.

Pipeline principal (Gemini ativo):
  1. Gerar embedding do ticket (Gemini Embedding 2)
  2. Buscar top-5 tickets similares na base RAG
  3. Verificar duplicatas entre tickets abertos
  4. Classificar, resumir, avaliar severidade e gerar soluções via Gemini Flash Lite
  5. Aplicar lógica de 3 níveis com auto-assignment

Fallback (sem API key):
  Usa templates fixos + keywords (comportamento anterior).
"""

from datetime import datetime
import uuid
import logging

from schemas import NivelSeveridade, StatusTicket, DetalheTicket, TriagemResponse
from config import SEVERITY_RULES, SEVERITY_THRESHOLDS, ALERT_THRESHOLDS, LABEL_MAP_EN_TO_PT
from database import db

logger = logging.getLogger(__name__)

RESPOSTAS_SOP = {
    "Hardware": (
        "Identificamos que seu ticket está relacionado a hardware. "
        "Por favor, verifique: 1) O equipamento está conectado corretamente; "
        "2) Tente reiniciar o dispositivo; 3) Verifique se há danos físicos visíveis."
    ),
    "Acesso / Login": (
        "Seu pedido de acesso foi recebido. Para questões de login/senha: "
        "1) Tente resetar sua senha pelo portal de autoatendimento; "
        "2) Verifique se o Caps Lock está desativado; 3) Limpe o cache do navegador."
    ),
    "Suporte RH": (
        "Sua solicitação de RH foi registrada. "
        "Consulte o portal do colaborador para questões frequentes. "
        "Processamento em até 48h úteis."
    ),
    "Armazenamento": (
        "Detectamos um problema de armazenamento. "
        "Recomendações: 1) Limpe arquivos temporários; "
        "2) Mova arquivos grandes para o drive compartilhado."
    ),
    "Compras": (
        "Sua requisição de compra foi registrada. "
        "Pedidos abaixo de R$5.000 são aprovados em até 3 dias úteis."
    ),
    "Diversos": (
        "Sua solicitação foi recebida e categorizada. "
        "Um analista revisará o pedido em breve."
    ),
    "Projeto Interno": (
        "Sua solicitação de projetos internos foi registrada. "
        "A equipe avaliará a demanda e retornará com um prazo estimado."
    ),
    "Direitos Administrativos": (
        "Seu pedido de direitos administrativos foi recebido. "
        "Requer aprovação do gestor. Tempo médio: 24h úteis."
    ),
}

SOLUCOES_FALLBACK = {
    "Hardware": [
        "Substituir o equipamento defeituoso por um reserva",
        "Agendar visita técnica presencial para diagnóstico",
        "Verificar garantia do fabricante e acionar suporte externo",
    ],
    "Acesso / Login": [
        "Resetar credenciais via painel administrativo",
        "Verificar se a conta está bloqueada por tentativas excessivas",
        "Revisar permissões de grupo e políticas de acesso",
    ],
    "Suporte RH": [
        "Encaminhar para o analista de RH responsável",
        "Consultar política interna e responder com base no regulamento",
        "Agendar reunião entre colaborador e BP de RH",
    ],
    "Diversos": [
        "Escalar para equipe especializada",
        "Reunir mais informações com o solicitante",
        "Consultar base de conhecimento para casos similares",
    ],
}


def _detectar_severidade_keywords(texto: str, confianca: float) -> NivelSeveridade:
    texto_lower = texto.lower()
    hits_critico = sum(1 for kw in SEVERITY_RULES["critical_keywords"] if kw in texto_lower)
    hits_medio = sum(1 for kw in SEVERITY_RULES["medium_keywords"] if kw in texto_lower)

    if hits_critico >= 2 or (hits_critico >= 1 and confianca < SEVERITY_THRESHOLDS["confidence_low"]):
        return NivelSeveridade.CRITICO
    if confianca < SEVERITY_THRESHOLDS["confidence_low"]:
        return NivelSeveridade.CRITICO
    if hits_medio >= 2 or hits_critico == 1:
        return NivelSeveridade.MEDIO
    if confianca < SEVERITY_THRESHOLDS["confidence_high"]:
        return NivelSeveridade.MEDIO
    return NivelSeveridade.BAIXO


def _gerar_resumo_local(texto: str, categoria: str) -> str:
    sentencas = texto.replace("\n", " ").split(".")
    sentencas_chave = [s.strip() for s in sentencas if len(s.strip()) > 20][:3]
    resumo = ". ".join(sentencas_chave)
    if resumo:
        return f"[{categoria}] {resumo}."
    return f"[{categoria}] Ticket requer análise detalhada."


def _processar_com_gemini(texto: str, nome_cliente: str, canal: str) -> TriagemResponse | None:
    """Pipeline completo usando RAG + Gemini LLM."""
    try:
        from rag import rag_store
        from llm import llm_disponivel, classificar_ticket, resumir_ticket, avaliar_severidade, gerar_solucoes, gerar_resposta_cliente

        if not llm_disponivel() or not rag_store.ready:
            return None

        similares = rag_store.buscar_similares(texto)

        classificacao = classificar_ticket(texto, similares)
        categoria = classificacao["categoria"]
        confianca = classificacao["confianca"]

        sev_result = avaliar_severidade(texto, categoria)
        sev_str = sev_result["severidade"]
        severidade = NivelSeveridade(sev_str)

        tickets_abertos = [
            {"id": t.id, "texto": t.texto}
            for t in db.tickets.values()
            if t.status not in (StatusTicket.RESOLVIDO,)
        ]
        duplicatas = rag_store.verificar_duplicatas(texto, tickets_abertos)

        ticket_id = str(uuid.uuid4())[:8]
        resposta_ia = None
        resumo_ia = None
        solucoes = None
        notificar_agente = False
        encaminhar_humano = False
        status_inicial = StatusTicket.NOVO

        if severidade == NivelSeveridade.BAIXO:
            resposta_ia = gerar_resposta_cliente(texto, categoria, "baixo")
            status_inicial = StatusTicket.RESOLVIDO
            acao = "Resposta automática gerada pelo Gemini. Ticket resolvido."
        elif severidade == NivelSeveridade.MEDIO:
            resposta_ia = gerar_resposta_cliente(texto, categoria, "medio")
            notificar_agente = True
            acao = "Resposta sugerida pelo Gemini. Agente notificado para monitoramento."
        else:
            resumo_ia = resumir_ticket(texto)
            solucoes = gerar_solucoes(texto, categoria, similares)
            encaminhar_humano = True
            acao = "Ticket crítico encaminhado para agente humano com resumo e soluções do Gemini."

        ticket = DetalheTicket(
            id=ticket_id,
            texto=texto,
            nome_cliente=nome_cliente,
            canal=canal,
            categoria=categoria,
            confianca=confianca,
            severidade=severidade,
            status=status_inicial,
            resposta_ia=resposta_ia,
            resumo_ia=resumo_ia,
            solucoes_sugeridas=solucoes,
            duplicatas_possiveis=[d["ticket_id"] for d in duplicatas] if duplicatas else None,
            criado_em=datetime.utcnow(),
            resolvido_em=datetime.utcnow() if status_inicial == StatusTicket.RESOLVIDO else None,
        )
        db.adicionar_ticket(ticket)
        db.verificar_limites_alerta(ALERT_THRESHOLDS)

        return TriagemResponse(
            ticket_id=ticket_id,
            categoria=categoria,
            confianca=confianca,
            severidade=severidade,
            acao=acao,
            resposta_ia=resposta_ia,
            resumo_ia=resumo_ia,
            solucoes_sugeridas=solucoes,
            notificar_agente=notificar_agente,
            encaminhar_humano=encaminhar_humano,
            duplicatas_possiveis=[d["ticket_id"] for d in duplicatas] if duplicatas else None,
        )

    except Exception as e:
        logger.error("Falha no pipeline Gemini, usando fallback: %s", e)
        return None


def _processar_fallback(texto: str, nome_cliente: str, canal: str) -> TriagemResponse:
    """Pipeline local com DeBERTa + templates (fallback)."""
    from classifier import get_classifier

    classificador = get_classifier()
    resultado = classificador.classify(texto)

    categoria_en = resultado["category"]
    categoria = LABEL_MAP_EN_TO_PT.get(categoria_en, categoria_en)
    confianca = resultado["confidence"]
    severidade = _detectar_severidade_keywords(texto, confianca)

    ticket_id = str(uuid.uuid4())[:8]
    resumo_ia = None
    solucoes = None

    resposta_ia = None
    notificar_agente = False
    encaminhar_humano = False
    status_inicial = StatusTicket.NOVO

    if severidade == NivelSeveridade.BAIXO:
        resposta_ia = RESPOSTAS_SOP.get(categoria, RESPOSTAS_SOP["Diversos"])
        status_inicial = StatusTicket.RESOLVIDO
        acao = "Resposta automática (template). Ticket resolvido."
    elif severidade == NivelSeveridade.MEDIO:
        resposta_ia = RESPOSTAS_SOP.get(categoria, RESPOSTAS_SOP["Diversos"])
        notificar_agente = True
        acao = "Resposta enviada (template). Agente notificado."
    else:
        resumo_ia = _gerar_resumo_local(texto, categoria)
        solucoes = SOLUCOES_FALLBACK.get(categoria, SOLUCOES_FALLBACK["Diversos"])
        encaminhar_humano = True
        acao = "Ticket encaminhado para agente humano com resumo e soluções."

    ticket = DetalheTicket(
        id=ticket_id,
        texto=texto,
        nome_cliente=nome_cliente,
        canal=canal,
        categoria=categoria,
        confianca=confianca,
        severidade=severidade,
        status=status_inicial,
        resposta_ia=resposta_ia,
        resumo_ia=resumo_ia,
        solucoes_sugeridas=solucoes,
        criado_em=datetime.utcnow(),
        resolvido_em=datetime.utcnow() if status_inicial == StatusTicket.RESOLVIDO else None,
    )
    db.adicionar_ticket(ticket)
    db.verificar_limites_alerta(ALERT_THRESHOLDS)

    return TriagemResponse(
        ticket_id=ticket_id,
        categoria=categoria,
        confianca=confianca,
        severidade=severidade,
        acao=acao,
        resposta_ia=resposta_ia,
        resumo_ia=resumo_ia,
        solucoes_sugeridas=solucoes,
        notificar_agente=notificar_agente,
        encaminhar_humano=encaminhar_humano,
    )


def processar_triagem(texto: str, nome_cliente: str = "Cliente", canal: str = "chat") -> TriagemResponse:
    result = _processar_com_gemini(texto, nome_cliente, canal)
    if result is not None:
        logger.info("Ticket %s processado via Gemini", result.ticket_id)
    else:
        logger.info("Usando fallback local para triagem")
        result = _processar_fallback(texto, nome_cliente, canal)

    if result.severidade in (NivelSeveridade.MEDIO, NivelSeveridade.CRITICO):
        from assignment import atribuir_automaticamente
        agente = atribuir_automaticamente(result.ticket_id)
        if agente:
            result.acao += f" Atribuído automaticamente a {agente}."

    return result
