"""
app.py — Protótipo de Demonstração do Pipeline SIM / TALVEZ / NÃO
Challenge 002 · G4 Tech · Arthur Reis

Demonstra o pipeline de decisão da plataforma de suporte com IA:
  1. Regras fixas (cancelamento, crítico) → NÃO imediato
  2. Classificação Nível 1 → Ticket Type (5 categorias)
  3. Classificação Nível 2 → Sub-área técnica (só se Technical issue)
  4. Decisão: SIM / TALVEZ / NÃO com output estruturado

Nota: classificação via regras semânticas PT/EN — explícita e auditável.
Em produção, o classificador seria treinado nos tickets reais da empresa.
Os datasets do challenge foram gerados sinteticamente para análise de métricas
operacionais — não possuem sinal semântico adequado para treino de NLP.
"""

import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pipeline de Suporte IA — G4 Tech",
    page_icon="🤖",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────────────────────
# EXEMPLOS REALISTAS (PT-BR)
# ─────────────────────────────────────────────────────────────────────────────
EXEMPLOS = {
    "💳 Cobrança duplicada": "Meu cartão foi cobrado duas vezes este mês. Preciso de um estorno urgente.",
    "📦 Dúvida sobre produto": "Como faço para configurar as notificações no aplicativo? Não estou recebendo alertas.",
    "🖥️ Problema técnico": "Meu computador não liga. A tela fica preta e não aparece nada depois que aperto o botão.",
    "🔐 Acesso bloqueado": "Não consigo fazer login no sistema desde ontem. Aparece 'usuário ou senha incorretos' mas tenho certeza que estão certos.",
    "💰 Pedido de reembolso": "Paguei por um produto que nunca chegou. Já faz 3 semanas. Quero meu dinheiro de volta.",
    "❌ Cancelamento": "Quero cancelar minha assinatura. Não estou usando mais o serviço.",
}

# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICAÇÃO — Nível 1: Ticket Type
# ─────────────────────────────────────────────────────────────────────────────
REGRAS_NIVEL1 = {
    "Cancellation request": {
        "pt": ["cancelar", "cancelamento", "cancela", "encerrar", "desativar", "desativação", "encerramento", "não quero mais"],
        "en": ["cancel", "cancellation", "terminate", "close account", "unsubscribe"],
    },
    "Billing inquiry": {
        "pt": ["cobrado", "cobrança", "fatura", "pagamento", "cartão", "mensalidade", "plano", "assinatura", "valor", "preço", "nota fiscal", "boleto", "duplicado", "duplicada", "dois vezes"],
        "en": ["charged", "billing", "invoice", "payment", "card", "subscription", "plan", "price", "receipt", "double charge"],
    },
    "Refund request": {
        "pt": ["reembolso", "estorno", "devolução", "devolver", "ressarcimento", "não chegou", "nunca chegou", "não recebi", "dinheiro de volta"],
        "en": ["refund", "chargeback", "money back", "return", "reimbursement", "never arrived", "not received"],
    },
    "Technical issue": {
        "pt": ["não funciona", "não liga", "não abre", "erro", "problema técnico", "travando", "trava", "lento", "falha", "bugado", "reinicia", "preta", "tela preta", "não responde", "login", "senha", "acesso", "sistema", "bloqueado"],
        "en": ["not working", "won't turn on", "error", "technical", "crash", "slow", "bug", "frozen", "black screen", "login", "password", "access"],
    },
    "Product inquiry": {
        "pt": ["como", "como faço", "configurar", "configuração", "usar", "funciona", "recurso", "funcionalidade", "tutorial", "ajuda com", "informação", "notificação", "integração"],
        "en": ["how to", "configure", "setup", "feature", "use", "tutorial", "help with", "notification", "integration"],
    },
}


def classificar_nivel1(texto: str):
    """Retorna (tipo, confiança %, scores_dict)."""
    t = texto.lower()
    scores = {tipo: 0 for tipo in REGRAS_NIVEL1}

    for tipo, kws in REGRAS_NIVEL1.items():
        for kw in kws.get("pt", []) + kws.get("en", []):
            if kw in t:
                scores[tipo] += 1

    melhor = max(scores, key=scores.get)
    total = sum(scores.values()) or 1
    confianca = min(int((scores[melhor] / total) * 100 + 30), 95)

    if scores[melhor] == 0:
        melhor = "Product inquiry"
        confianca = 35

    return melhor, confianca, scores


# ─────────────────────────────────────────────────────────────────────────────
# CLASSIFICAÇÃO — Nível 2: Sub-área técnica
# ─────────────────────────────────────────────────────────────────────────────
REGRAS_NIVEL2 = {
    "Hardware": {
        "pt": ["não liga", "tela", "preta", "monitor", "teclado", "mouse", "impressora", "fonte", "bateria", "cabo"],
        "en": ["won't turn on", "screen", "monitor", "keyboard", "battery", "hardware"],
    },
    "Access & Login": {
        "pt": ["login", "senha", "acesso", "bloqueado", "usuário", "autenticação", "credencial"],
        "en": ["login", "password", "access", "locked", "authentication", "credentials"],
    },
    "Network & Connectivity": {
        "pt": ["internet", "rede", "conexão", "wifi", "sem sinal", "lento", "instável"],
        "en": ["internet", "network", "connection", "wifi", "slow", "unstable"],
    },
    "Software & App": {
        "pt": ["aplicativo", "app", "programa", "software", "instalar", "atualizar", "travando", "erro", "falha", "não abre"],
        "en": ["app", "software", "program", "install", "update", "crash", "error", "won't open"],
    },
    "Storage & Data": {
        "pt": ["arquivo", "dados", "backup", "disco", "memória", "armazenamento", "espaço"],
        "en": ["file", "data", "backup", "disk", "storage", "space"],
    },
}


def classificar_nivel2(texto: str):
    """Retorna (sub_area, confiança %)."""
    t = texto.lower()
    scores = {sub: 0 for sub in REGRAS_NIVEL2}

    for sub, kws in REGRAS_NIVEL2.items():
        for kw in kws.get("pt", []) + kws.get("en", []):
            if kw in t:
                scores[sub] += 1

    melhor = max(scores, key=scores.get)
    if scores[melhor] == 0:
        melhor = "Software & App"
    total = sum(scores.values()) or 1
    confianca = min(int((scores[melhor] / total) * 100 + 35), 92)
    return melhor, confianca


# ─────────────────────────────────────────────────────────────────────────────
# REGRAS FIXAS
# ─────────────────────────────────────────────────────────────────────────────
KWS_CANCEL  = ["cancelar", "cancelamento", "cancela", "encerrar", "unsubscribe", "cancel"]
KWS_CRITICO = ["urgente", "emergência", "crítico", "crítica", "urgent", "critical", "emergency"]


def checar_regras_fixas(texto: str):
    t = texto.lower()
    for kw in KWS_CANCEL:
        if kw in t:
            return True, "cancelamento"
    for kw in KWS_CRITICO:
        if kw in t:
            return True, "crítico"
    return False, ""


# ─────────────────────────────────────────────────────────────────────────────
# DECISÃO
# ─────────────────────────────────────────────────────────────────────────────
def decidir(ticket_type: str, confianca: int, bloqueado: bool) -> str:
    if bloqueado or ticket_type == "Cancellation request":
        return "NÃO"
    if confianca >= 70:
        return "SIM"
    if confianca >= 45:
        return "TALVEZ"
    return "NÃO"


# ─────────────────────────────────────────────────────────────────────────────
# OUTPUTS
# ─────────────────────────────────────────────────────────────────────────────
RESPOSTAS_SIM = {
    "Billing inquiry": (
        "Olá! Identificamos que sua solicitação é referente à sua cobrança.\n\n"
        "Nossa equipe já está analisando o caso. Em até **2 horas úteis** você receberá um retorno com o detalhamento do ocorrido.\n\n"
        "Caso a cobrança duplicada seja confirmada, o estorno será processado em **3 a 5 dias úteis** na fatura do seu cartão.\n\n"
        "Precisando de algo mais, estamos aqui 😊"
    ),
    "Refund request": (
        "Olá! Recebemos sua solicitação de reembolso.\n\n"
        "Nossa equipe iniciará a análise imediatamente. O prazo para retorno é de **1 dia útil**.\n\n"
        "Caso aprovado, o valor será estornado em **3 a 5 dias úteis** dependendo do método de pagamento.\n\n"
        "Acompanhe o status pelo nosso portal ou aguarde nosso contato."
    ),
    "Product inquiry": (
        "Olá! Que bom que entrou em contato 😊\n\n"
        "Para configurar as notificações no aplicativo:\n"
        "1. Acesse **Configurações → Notificações**\n"
        "2. Ative as categorias que deseja receber\n"
        "3. Verifique se as permissões do app estão habilitadas no seu dispositivo\n\n"
        "Se o problema persistir, nos informe o modelo do dispositivo e versão do sistema. Estamos à disposição!"
    ),
    "Technical issue": (
        "Olá! Recebemos seu chamado técnico.\n\n"
        "Nossa equipe de suporte foi notificada e entrará em contato em até **4 horas úteis** com diagnóstico e próximos passos.\n\n"
        "Enquanto isso, se possível:\n"
        "- Registre quando o problema começou\n"
        "- Anote qualquer mensagem de erro que apareça\n"
        "- Tente reiniciar o equipamento\n\n"
        "Essas informações agilizarão a resolução."
    ),
}

PERGUNTAS_TALVEZ = {
    "Billing inquiry": [
        "Qual o valor cobrado e a data da transação que você identificou como incorreta?",
        "A cobrança aparece como duplicada ou como valor diferente do esperado?",
        "Você tem o número do pedido ou protocolo relacionado a essa cobrança?",
    ],
    "Refund request": [
        "Qual o número do pedido e a data da compra?",
        "O produto foi entregue com defeito, ou não foi entregue?",
        "Já realizou algum contato anterior sobre este caso? Se sim, tem número de protocolo?",
    ],
    "Technical issue": [
        "O problema ocorre em todos os momentos ou em situações específicas?",
        "Qual o modelo do equipamento e a versão do sistema operacional/aplicativo?",
        "O problema começou após alguma atualização ou mudança recente?",
    ],
    "Product inquiry": [
        "Qual dispositivo e sistema operacional você está usando?",
        "Qual versão do aplicativo está instalada? (visível em Configurações → Sobre)",
        "O problema ocorre sempre ou em situações específicas?",
    ],
    "Cancellation request": [
        "Qual o motivo do cancelamento? (Preço / Não usa mais / Insatisfação / Outro)",
        "Você estaria interessado em uma pausa no serviço em vez do cancelamento?",
        "Há algo que pudéssemos melhorar para que você continuasse conosco?",
    ],
}

RESUMO_AGENTE = {
    "Cancellation request": {
        "flag": "🔴 RISCO DE CHURN",
        "instrucao": "⚠️ RETENÇÃO HUMANA OBRIGATÓRIA — nunca automatizar",
        "sla": "2 horas",
        "contexto": "Cliente com intenção de cancelamento. Aplicar protocolo de retenção: ouvir o motivo, oferecer pausa ou desconto se aplicável, escalar para especialista em retenção se necessário.",
    },
    "crítico": {
        "flag": "🔴 PRIORIDADE MÁXIMA",
        "instrucao": "🚨 TICKET CRÍTICO — escalonamento imediato",
        "sla": "30 minutos",
        "contexto": "Ticket marcado como urgente/crítico. Prioridade máxima na fila.",
    },
    "default": {
        "flag": "🟡 REVISÃO NECESSÁRIA",
        "instrucao": "Confiança insuficiente para resposta automática. Revisão humana necessária.",
        "sla": "4 horas",
        "contexto": "Classificação com confiança abaixo do threshold. Verifique o tipo correto e responda com base no histórico do cliente.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE COMPLETO
# ─────────────────────────────────────────────────────────────────────────────
def rodar_pipeline(texto: str) -> dict:
    r = {"texto": texto, "etapas": []}

    # Etapa 1 — Regras fixas
    bloqueado, motivo = checar_regras_fixas(texto)
    r["bloqueado"] = bloqueado
    r["motivo_bloqueio"] = motivo
    r["etapas"].append({
        "nome": "① Regras fixas",
        "status": "⚠️ Bloqueado" if bloqueado else "✅ Sem bloqueio",
        "detalhe": f"Motivo: {motivo}" if bloqueado else "Nenhuma palavra de bloqueio encontrada",
        "cor": "vermelho" if bloqueado else "verde",
    })

    # Etapa 2 — Classificação Nível 1
    tipo, conf1, scores = classificar_nivel1(texto)
    r["ticket_type"] = tipo
    r["confianca_n1"] = conf1
    r["etapas"].append({
        "nome": "② Classificação Nível 1",
        "status": tipo,
        "detalhe": f"Confiança: {conf1}%",
        "cor": "verde" if conf1 >= 70 else "amarelo" if conf1 >= 45 else "cinza",
    })

    # Etapa 3 — Nível 2 (só Technical issue)
    if tipo == "Technical issue":
        sub_area, conf2 = classificar_nivel2(texto)
        r["sub_area"] = sub_area
        r["etapas"].append({
            "nome": "③ Sub-área técnica",
            "status": sub_area,
            "detalhe": f"Confiança: {conf2}%",
            "cor": "verde",
        })
    else:
        r["sub_area"] = None
        r["etapas"].append({
            "nome": "③ Sub-área técnica",
            "status": "— Não aplicável",
            "detalhe": "Ativado apenas para Technical issue",
            "cor": "cinza",
        })

    # Etapa 4 — Decisão
    decisao = decidir(tipo, conf1, bloqueado)
    r["decisao"] = decisao
    r["etapas"].append({
        "nome": "④ Decisão",
        "status": decisao,
        "detalhe": (
            "Alta confiança → resposta automática"   if decisao == "SIM"
            else "Confiança moderada → triagem adicional" if decisao == "TALVEZ"
            else "Bloqueio ou baixa confiança → fila humana"
        ),
        "cor": "verde" if decisao == "SIM" else "amarelo" if decisao == "TALVEZ" else "vermelho",
    })

    # Output
    if decisao == "SIM":
        r["output_tipo"] = "resposta"
        r["output"] = RESPOSTAS_SIM.get(tipo, RESPOSTAS_SIM["Product inquiry"])
    elif decisao == "TALVEZ":
        r["output_tipo"] = "perguntas"
        r["output"] = PERGUNTAS_TALVEZ.get(tipo, PERGUNTAS_TALVEZ["Technical issue"])
    else:
        r["output_tipo"] = "resumo_agente"
        chave = motivo if motivo == "crítico" else ("Cancellation request" if tipo == "Cancellation request" else "default")
        out = RESUMO_AGENTE.get(chave, RESUMO_AGENTE["default"]).copy()
        out["ticket_type"] = tipo
        out["sub_area"] = r.get("sub_area") or "—"
        r["output"] = out

    return r


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .bloco-etapa {
    background: #F8F9FA; border-radius: 8px;
    padding: 14px 18px; margin-bottom: 10px;
    border-left: 5px solid #CCC;
  }
  .bloco-etapa.verde   { border-left-color: #27AE60; }
  .bloco-etapa.amarelo { border-left-color: #F5A623; }
  .bloco-etapa.vermelho{ border-left-color: #E84040; }
  .bloco-etapa.cinza   { border-left-color: #BDC3C7; opacity: .6; }
  .etapa-nome   { font-size: 12px; color: #888; font-weight: 600; letter-spacing: .5px; }
  .etapa-status { font-size: 18px; font-weight: 700; margin: 4px 0; }
  .etapa-detalhe{ font-size: 13px; color: #555; }
  .badge-sim    { background:#E8F5E9; color:#27AE60; font-weight:700; padding:4px 16px; border-radius:20px; font-size:16px; }
  .badge-talvez { background:#FFF8E1; color:#E67E00; font-weight:700; padding:4px 16px; border-radius:20px; font-size:16px; }
  .badge-nao    { background:#FFEBEE; color:#E84040; font-weight:700; padding:4px 16px; border-radius:20px; font-size:16px; }
  .output-box {
    background: white; border: 1px solid #E0E0E0; border-radius: 10px;
    padding: 20px 24px; margin-top: 16px; font-size: 14px; line-height: 1.8;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#1A1A2E;color:white;padding:26px 32px 20px;border-radius:10px;margin-bottom:24px;">
  <div style="font-size:22px;font-weight:700;margin-bottom:4px;">🤖 Pipeline de Suporte IA — G4 Tech</div>
  <div style="opacity:.7;font-size:13px;">Protótipo · Challenge 002 · Demonstração do pipeline SIM / TALVEZ / NÃO</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
col_esq, col_dir = st.columns([1, 1.2], gap="large")

with col_esq:
    st.markdown("#### Ticket de entrada")
    st.markdown(
        "<p style='font-size:13px;color:#666;margin-top:-8px;margin-bottom:16px;'>"
        "Selecione um exemplo ou escreva o texto do ticket abaixo.</p>",
        unsafe_allow_html=True,
    )

    exemplo_sel = st.selectbox(
        "Exemplos",
        options=["— Escreva seu próprio —"] + list(EXEMPLOS.keys()),
        label_visibility="collapsed",
    )

    texto_inicial = EXEMPLOS[exemplo_sel] if exemplo_sel != "— Escreva seu próprio —" else ""

    ticket_texto = st.text_area(
        "Texto",
        value=texto_inicial,
        height=150,
        placeholder="Digite ou cole o texto do ticket aqui...",
        label_visibility="collapsed",
    )

    analisar = st.button("▶  Analisar ticket", type="primary", use_container_width=True)

    st.markdown("""
    <div style='background:#F8F9FA;border-radius:8px;padding:16px 18px;margin-top:20px;font-size:13px;line-height:1.9;'>
      <b>Como funciona o pipeline:</b><br>
      <b>①</b> Verifica palavras de bloqueio (cancelamento, crítico)<br>
      <b>②</b> Classifica o tipo do ticket (5 categorias)<br>
      <b>③</b> Sub-área técnica <i>(só para Technical issue)</i><br>
      <b>④</b> Decide com base na confiança<br><br>
      <span style='color:#27AE60;font-weight:600;'>✅ SIM ≥ 70%</span> → resposta automática ao cliente<br>
      <span style='color:#E67E00;font-weight:600;'>🟡 TALVEZ 45–69%</span> → perguntas de triagem ao cliente<br>
      <span style='color:#E84040;font-weight:600;'>🔴 NÃO &lt; 45% ou bloqueio</span> → resumo para agente humano
    </div>
    """, unsafe_allow_html=True)

with col_dir:
    st.markdown("#### Pipeline de decisão")

    if not analisar or not ticket_texto.strip():
        st.markdown("""
        <div style='background:#F8F9FA;border-radius:10px;padding:48px 32px;text-align:center;color:#AAA;margin-top:8px;'>
          <div style='font-size:42px;margin-bottom:12px;'>⬅</div>
          <div style='font-size:15px;'>Selecione um exemplo ou escreva um ticket<br>e clique em <b>Analisar</b></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        r = rodar_pipeline(ticket_texto.strip())

        # Ticket resumido
        trecho = ticket_texto.strip()[:120] + ("..." if len(ticket_texto.strip()) > 120 else "")
        st.markdown(f"""
        <div style='background:#EEF2FF;border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:13px;'>
          <b>Ticket:</b> "{trecho}"
        </div>
        """, unsafe_allow_html=True)

        # Etapas
        for etapa in r["etapas"]:
            st.markdown(f"""
            <div class="bloco-etapa {etapa['cor']}">
              <div class="etapa-nome">{etapa['nome']}</div>
              <div class="etapa-status">{etapa['status']}</div>
              <div class="etapa-detalhe">{etapa['detalhe']}</div>
            </div>
            """, unsafe_allow_html=True)

        # Badge decisão
        decisao = r["decisao"]
        bc = {"SIM": "badge-sim", "TALVEZ": "badge-talvez", "NÃO": "badge-nao"}[decisao]
        em = {"SIM": "✅", "TALVEZ": "🟡", "NÃO": "🔴"}[decisao]
        st.markdown(f"""
        <div style='margin:16px 0 8px;font-size:12px;color:#888;font-weight:600;letter-spacing:.5px;'>DECISÃO FINAL</div>
        <span class="{bc}">{em} {decisao}</span>
        """, unsafe_allow_html=True)

        # Output
        st.markdown("<div style='margin-top:20px;font-size:12px;color:#888;font-weight:600;letter-spacing:.5px;'>OUTPUT</div>", unsafe_allow_html=True)

        if r["output_tipo"] == "resposta":
            corpo = r["output"].replace("\n", "<br>").replace("**", "<b>", 1)
            # replace paired ** with bold tags
            import re
            corpo_final = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", r["output"]).replace("\n", "<br>")
            st.markdown(f"""
            <div class='output-box'>
              <div style='font-size:11px;color:#27AE60;font-weight:700;letter-spacing:.8px;margin-bottom:12px;'>
                ✅ RESPOSTA AUTOMÁTICA → ENVIADA AO CLIENTE
              </div>
              {corpo_final}
            </div>
            """, unsafe_allow_html=True)

        elif r["output_tipo"] == "perguntas":
            itens = "".join(
                f"<div style='padding:8px 0;border-bottom:1px solid #F0F0F0;'>{i+1}. {p}</div>"
                for i, p in enumerate(r["output"])
            )
            st.markdown(f"""
            <div class='output-box'>
              <div style='font-size:11px;color:#E67E00;font-weight:700;letter-spacing:.8px;margin-bottom:12px;'>
                🟡 PERGUNTAS DE TRIAGEM → ENVIADAS AO CLIENTE
              </div>
              {itens}
            </div>
            """, unsafe_allow_html=True)

        else:  # resumo_agente
            out = r["output"]
            st.markdown(f"""
            <div class='output-box'>
              <div style='font-size:11px;color:#E84040;font-weight:700;letter-spacing:.8px;margin-bottom:12px;'>
                🔴 RESUMO PARA AGENTE HUMANO → FILA INTERNA
              </div>
              <div style='font-size:16px;font-weight:700;margin-bottom:14px;'>{out.get('flag','')}</div>
              <table style='font-size:13px;width:100%;border-collapse:collapse;'>
                <tr>
                  <td style='color:#888;font-weight:600;padding:5px 12px 5px 0;width:90px;'>Tipo</td>
                  <td style='padding:5px 0;'>{out.get('ticket_type','—')}</td>
                </tr>
                <tr>
                  <td style='color:#888;font-weight:600;padding:5px 12px 5px 0;'>Sub-área</td>
                  <td style='padding:5px 0;'>{out.get('sub_area','—')}</td>
                </tr>
                <tr>
                  <td style='color:#888;font-weight:600;padding:5px 12px 5px 0;'>SLA</td>
                  <td style='padding:5px 0;'>{out.get('sla','—')}</td>
                </tr>
              </table>
              <div style='margin-top:14px;background:#FFF8E1;border-radius:6px;padding:12px 16px;font-size:13px;line-height:1.7;'>
                <b>Instrução:</b> {out.get('instrucao','')}<br><br>
                <b>Contexto:</b> {out.get('contexto','')}
              </div>
            </div>
            """, unsafe_allow_html=True)
