"""
Motor LLM com Gemini 3.1 Flash Lite via google-genai SDK.

Encapsula todas as chamadas ao Gemini para classificação, resumo,
avaliação de severidade, geração de soluções e respostas ao cliente.
"""

import json
import logging

from google import genai
from google.genai.types import GenerateContentConfig

from config import GOOGLE_API_KEY, GEMINI_LLM_MODEL, TOPIC_LABELS

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

SYSTEM_PROMPT = """Você é o motor de inteligência artificial do sistema "G4 IA Inteligência de Suporte", \
uma ferramenta de triagem automática de tickets de suporte técnico.

Seu papel dentro da ferramenta:
1. CLASSIFICAR cada ticket recebido em uma das categorias pré-definidas, baseando-se no conteúdo do texto e em casos similares já resolvidos (fornecidos via RAG).
2. AVALIAR A SEVERIDADE do ticket (baixo, médio ou crítico) para que o sistema decida se resolve automaticamente, encaminha para monitoramento ou escala para um agente humano.
3. RESUMIR o problema do cliente em 1-2 frases objetivas para que agentes e gestores entendam rapidamente o caso.
4. GERAR 3 SOLUÇÕES PRÁTICAS baseadas no contexto do ticket e em resoluções de casos similares anteriores.
5. REDIGIR RESPOSTAS profissionais e empáticas ao cliente, adequadas à severidade do caso.

Diretrizes:
- Sempre responda em português do Brasil.
- Seja objetivo e direto — agentes de suporte precisam de respostas rápidas.
- Quando receber casos similares do RAG, use-os como referência para fundamentar suas respostas, não os ignore.
- Para classificação e severidade, responda SEMPRE em JSON válido conforme solicitado.
- Nunca invente informações técnicas que não estejam no contexto fornecido.
- Em caso de dúvida entre severidades, prefira a mais alta (princípio da precaução)."""


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY não configurada")
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


def _call_llm(prompt: str, json_mode: bool = False) -> str:
    client = _get_client()
    try:
        config = GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=1024,
        )
        if json_mode:
            config = GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
                max_output_tokens=1024,
                response_mime_type="application/json",
            )

        response = client.models.generate_content(
            model=GEMINI_LLM_MODEL,
            contents=prompt,
            config=config,
        )
        return response.text.strip()
    except Exception as e:
        logger.error("Erro na chamada LLM: %s", e)
        return ""


CATEGORIAS_DESCRICAO = {
    "Hardware": "Problemas com equipamentos físicos: computadores, monitores, impressoras, teclados, mouses, periféricos, notebooks defeituosos",
    "Suporte RH": "Solicitações de recursos humanos: folha de pagamento, férias, benefícios, admissão, demissão, contratos, ponto",
    "Acesso / Login": "Problemas de acesso a sistemas: senha esquecida, conta bloqueada, permissões, VPN, autenticação, login, credenciais",
    "Diversos": "Solicitações gerais que não se encaixam nas outras categorias: dúvidas, informações, orientações diversas",
    "Armazenamento": "Problemas com armazenamento de dados: disco cheio, backup, nuvem, compartilhamento de arquivos, pastas, drives",
    "Compras": "Requisições de compra: software, licenças, equipamentos novos, materiais, orçamentos, pedidos de aquisição",
    "Projeto Interno": "Demandas de projetos internos: desenvolvimento, implementação, migração, mudanças de sistema, melhorias",
    "Direitos Administrativos": "Solicitações de privilégios: acesso admin, instalação de software, permissões elevadas, liberação de portas",
}


def classificar_ticket(texto: str, contexto_rag: list[dict] | None = None) -> dict:
    categorias_detalhadas = "\n".join(
        f"- \"{cat}\": {desc}" for cat, desc in CATEGORIAS_DESCRICAO.items()
    )

    contexto = ""
    if contexto_rag:
        exemplos = []
        for i, doc in enumerate(contexto_rag[:3], 1):
            exemplos.append(
                f"  Caso {i}: Categoria=\"{doc['categoria']}\", "
                f"Texto=\"{doc['texto'][:150]}\""
            )
        contexto = (
            "Casos similares já resolvidos (recuperados da base RAG):\n"
            + "\n".join(exemplos)
            + "\n\nUse esses casos como referência para sua classificação.\n\n"
        )

    prompt = f"""TAREFA: Classificar o ticket abaixo em UMA das 8 categorias de problemas da operação de suporte.

As 8 categorias e seus significados:
{categorias_detalhadas}

{contexto}Ticket do cliente:
\"{texto[:500]}\"

Analise o conteúdo do ticket e identifique qual das 8 categorias acima melhor descreve o problema. Responda em JSON:
{{
  "categoria": "nome exato de uma das 8 categorias acima",
  "confianca": 0.0 a 1.0,
  "justificativa": "explicação curta em português de por que esta categoria foi escolhida"
}}"""

    raw = _call_llm(prompt, json_mode=True)
    try:
        data = json.loads(raw)
        cat = data.get("categoria", TOPIC_LABELS[3])
        if cat not in TOPIC_LABELS:
            cat = TOPIC_LABELS[3]
        return {
            "categoria": cat,
            "confianca": min(max(float(data.get("confianca", 0.5)), 0.0), 1.0),
            "justificativa": data.get("justificativa", ""),
        }
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.warning("Falha ao parsear resposta do LLM para classificação")
        return {"categoria": TOPIC_LABELS[3], "confianca": 0.3, "justificativa": "Fallback"}


def resumir_ticket(texto: str) -> str:
    prompt = f"""TAREFA: Gerar um resumo executivo do ticket abaixo para que agentes e gestores \
entendam o problema do cliente em segundos.

Regras:
- Máximo 2 frases curtas e objetivas
- Foque no problema principal e no impacto para o cliente
- Não repita o texto do ticket literalmente, sintetize

Ticket do cliente:
\"{texto[:800]}\"

Resumo:"""

    result = _call_llm(prompt)
    return result if result else "Ticket requer análise detalhada."


def avaliar_severidade(texto: str, categoria: str) -> dict:
    prompt = f"""TAREFA: Avaliar a severidade deste ticket para definir o nível de automação da resposta.

O sistema usa 3 níveis que determinam a ação automática:
- "baixo": A IA resolve e fecha o ticket automaticamente (dúvidas simples, consultas, problemas com soluções conhecidas)
- "medio": A IA responde e notifica um agente para acompanhar (problemas que afetam produtividade, erros recorrentes, atrasos)
- "critico": A IA resume e sugere soluções, mas um agente humano resolve (sistemas fora do ar, perda de dados, falhas de segurança, impacto em produção)

Categoria do ticket: {categoria}

Ticket do cliente:
\"{texto[:500]}\"

Avalie com base no impacto operacional e urgência. Responda em JSON:
{{
  "severidade": "baixo", "medio" ou "critico",
  "justificativa": "explicação curta em português do motivo da severidade escolhida"
}}"""

    raw = _call_llm(prompt, json_mode=True)
    try:
        data = json.loads(raw)
        sev = data.get("severidade", "medio")
        if sev not in ("baixo", "medio", "critico"):
            sev = "medio"
        return {"severidade": sev, "justificativa": data.get("justificativa", "")}
    except (json.JSONDecodeError, KeyError, TypeError):
        return {"severidade": "medio", "justificativa": "Fallback"}


def gerar_solucoes(texto: str, categoria: str, tickets_similares: list[dict] | None = None) -> list[str]:
    contexto = ""
    if tickets_similares:
        exemplos = []
        for i, t in enumerate(tickets_similares[:3], 1):
            res = t.get("resolucao", "")
            if res:
                exemplos.append(
                    f"  Caso {i} (categoria={t['categoria']}): "
                    f"Resolução aplicada=\"{res[:200]}\""
                )
        if exemplos:
            contexto = (
                "Resoluções de casos similares já resolvidos (base RAG):\n"
                + "\n".join(exemplos)
                + "\n\nUse essas resoluções como referência, adaptando ao caso atual.\n\n"
            )

    prompt = f"""TAREFA: Gerar 3 soluções práticas para o problema do cliente.

Estas soluções serão exibidas ao agente de suporte como sugestões da IA.
Cada solução deve ser acionável, específica ao problema, e ter 1-2 frases.

Categoria: {categoria}
{contexto}Problema do cliente:
\"{texto[:500]}\"

Responda em JSON — uma lista com exatamente 3 strings:
["solução 1", "solução 2", "solução 3"]"""

    raw = _call_llm(prompt, json_mode=True)
    try:
        solucoes = json.loads(raw)
        if isinstance(solucoes, list) and len(solucoes) >= 3:
            return [str(s) for s in solucoes[:3]]
    except (json.JSONDecodeError, TypeError):
        pass

    return [
        f"Verificar e diagnosticar o problema de {categoria} reportado",
        "Escalar para equipe especializada se necessário",
        "Consultar base de conhecimento para casos similares",
    ]


def gerar_resposta_cliente(texto: str, categoria: str, severidade: str) -> str:
    niveis = {
        "baixo": "Este ticket foi classificado como baixa severidade e será resolvido automaticamente.",
        "medio": "Este ticket foi classificado como média severidade e um agente acompanhará o caso.",
        "critico": "Este ticket foi classificado como crítico e foi escalado para um agente especializado.",
    }
    contexto_nivel = niveis.get(severidade, niveis["medio"])

    prompt = f"""TAREFA: Redigir uma resposta ao cliente que abriu este ticket.

A resposta será enviada automaticamente pelo sistema. Ela deve:
- Ser profissional, empática e em português
- Confirmar o recebimento do ticket
- Informar o que será feito de acordo com a severidade
- Ter no máximo 3 frases

Contexto interno (não incluir na resposta): {contexto_nivel}
Categoria: {categoria}
Severidade: {severidade}

Ticket do cliente:
\"{texto[:500]}\"

Resposta ao cliente:"""

    result = _call_llm(prompt)
    if result:
        return result

    return (
        f"Sua solicitação referente a {categoria} foi recebida e está sendo processada. "
        "Um analista revisará o caso e retornará em breve."
    )


def llm_disponivel() -> bool:
    return bool(GOOGLE_API_KEY)
