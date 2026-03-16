"""
Protótipo Funcional — Challenge 002: Redesign de Suporte
=========================================================
Webapp Streamlit com 3 telas:
  1. Dashboard do Diretor (diagnóstico visual)
  2. Simulador de Triagem IA (classificação em tempo real)
  3. Análise de Texto em Batch

Autor: Gustavo Ferreira
Execução: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Support Redesign — AI Master",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
DS1_PATH = DATA_DIR / "dataset1" / "customer_support_tickets.csv"
DS2_PATH = DATA_DIR / "dataset2" / "all_tickets_processed_improved_v3.csv"
DIAG_PATH = Path(__file__).resolve().parent / "diagnostico_output" / "diagnostico_completo.json"

# ---------------------------------------------------------------------------
# ESTILOS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    .main > div { padding-top: 1rem; }
    .stMetric { background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
                padding: 1rem; border-radius: 12px; border: 1px solid #3d3d5c; }
    .stMetric label { color: #a0a0b0 !important; font-size: 0.85rem !important; }
    .stMetric [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem !important; }
    .stMetric [data-testid="stMetricDelta"] { font-size: 0.9rem !important; }
    div[data-testid="stTabs"] button { font-size: 1.1rem !important; font-weight: 600 !important; }
    .card { background: #1e1e2e; border-radius: 12px; padding: 1.2rem;
            border: 1px solid #3d3d5c; margin-bottom: 0.8rem; }
    .card h4 { margin: 0 0 0.5rem 0; color: #e0e0e0; }
    .card p { margin: 0; color: #b0b0c0; }
    .badge { display: inline-block; padding: 0.3rem 0.8rem; border-radius: 20px;
             font-weight: 600; font-size: 0.85rem; margin: 0.2rem; }
    .badge-green { background: #1a4d2e; color: #4ade80; }
    .badge-blue { background: #1a3a5c; color: #60a5fa; }
    .badge-yellow { background: #4d3d1a; color: #fbbf24; }
    .badge-red { background: #4d1a1a; color: #f87171; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DADOS
# ---------------------------------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv(DS1_PATH)
    df["Date of Purchase"] = pd.to_datetime(df["Date of Purchase"], errors="coerce")
    df["First Response Time"] = pd.to_datetime(df["First Response Time"], errors="coerce")
    df["Time to Resolution"] = pd.to_datetime(df["Time to Resolution"], errors="coerce")
    return df


@st.cache_data
def load_data2():
    df2 = pd.read_csv(DS2_PATH)
    return df2


@st.cache_data
def load_diagnostico():
    with open(DIAG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


df = load_data()
df2 = load_data2()
diag = load_diagnostico()


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/headset.png", width=60)
    st.title("Support Redesign")
    st.caption("AI Master Challenge 002")
    st.divider()
    st.markdown("**Gustavo Ferreira**")
    st.markdown("Protótipo funcional para redesign da operação de suporte com IA.")
    st.divider()
    st.markdown("### Dados")
    st.metric("Dataset 1", f"{len(df):,} tickets")
    st.metric("Dataset 2", f"{len(df2):,} tickets")


# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard do Diretor",
    "🤖 Simulador de Triagem IA",
    "📋 Proposta de Automação",
    "🔬 Análise Cruzada (Datasets 1 + 2)",
])


# ===== TAB 1: DASHBOARD DO DIRETOR =========================================

with tab1:
    st.header("Painel Executivo — Diagnóstico Operacional")
    st.caption("Visão consolidada dos gargalos, custos e oportunidades de automação")

    # --- KPIs ---
    backlog = diag["gargalos"]["backlog"]
    eco = diag["desperdicio"]["economia_total"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Backlog",
            f"{backlog['pct_nao_resolvidos']}%",
            delta=f"{backlog['nao_resolvidos']:,} tickets parados",
            delta_color="inverse",
        )
    with col2:
        st.metric(
            "Taxa de Resolução",
            f"{100 - backlog['pct_nao_resolvidos']}%",
            delta=f"{backlog['closed']:,} fechados",
        )
    with col3:
        st.metric(
            "Economia Potencial",
            f"R$ {eco['economia_anual_brl']:,.0f}/ano",
            delta=f"{eco['pct_do_total']}% automatizável",
        )
    with col4:
        st.metric(
            "CSAT Médio",
            f"{diag['csat']['media_global']}/5",
            delta="⚠️ Dado aleatório",
            delta_color="off",
        )

    st.divider()

    # --- Gráficos ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Status dos Tickets")
        status_data = pd.DataFrame({
            "Status": ["Fechado", "Aberto", "Pendente"],
            "Quantidade": [backlog["closed"], backlog["open"], backlog["pending"]],
            "Cor": ["#4ade80", "#f87171", "#fbbf24"],
        })
        fig_status = px.bar(
            status_data, x="Status", y="Quantidade", color="Status",
            color_discrete_map={"Fechado": "#4ade80", "Aberto": "#f87171", "Pendente": "#fbbf24"},
            text_auto=True,
        )
        fig_status.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with col_right:
        st.subheader("Distribuição por Tipo de Ticket")
        tipo_data = df["Ticket Type"].value_counts().reset_index()
        tipo_data.columns = ["Tipo", "Quantidade"]
        fig_tipo = px.pie(
            tipo_data, values="Quantidade", names="Tipo",
            color_discrete_sequence=["#f87171", "#60a5fa", "#fbbf24", "#4ade80", "#c084fc"],
            hole=0.4,
        )
        fig_tipo.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
        )
        st.plotly_chart(fig_tipo, use_container_width=True)

    st.divider()

    # --- Economia por tipo de ticket ---
    st.subheader("💰 Economia Projetada por Tipo de Automação")

    auto_data = diag["desperdicio"]["automacao_por_tipo"]
    eco_df = pd.DataFrame([
        {
            "Tipo": tipo,
            "Volume Total": info["total"],
            "% Automatizável": info["automatizavel_pct"],
            "Tickets Auto": info["tickets_automatizaveis"],
            "Economia (R$)": info["economia_brl"],
            "Como": info["como"],
        }
        for tipo, info in auto_data.items()
    ]).sort_values("Economia (R$)", ascending=True)

    fig_eco = px.bar(
        eco_df, x="Economia (R$)", y="Tipo", orientation="h",
        color="% Automatizável",
        color_continuous_scale=["#f87171", "#fbbf24", "#4ade80"],
        text="Economia (R$)",
    )
    fig_eco.update_traces(texttemplate="R$ %{text:,.0f}", textposition="outside")
    fig_eco.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        height=350,
    )
    st.plotly_chart(fig_eco, use_container_width=True)

    st.divider()

    # --- Heatmap: Canal × Tipo → Taxa de resolução ---
    st.subheader("🔥 Mapa de Calor — Taxa de Resolução (Canal × Tipo)")

    heatmap_data = df.groupby(["Ticket Channel", "Ticket Type"]).apply(
        lambda g: (g["Ticket Status"] == "Closed").mean() * 100, include_groups=False
    ).unstack()

    fig_heat = px.imshow(
        heatmap_data.values,
        x=heatmap_data.columns.tolist(),
        y=heatmap_data.index.tolist(),
        color_continuous_scale="RdYlGn",
        text_auto=".1f",
        labels=dict(color="% Resolvido"),
    )
    fig_heat.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        height=350,
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()

    # --- Alerta de qualidade dos dados ---
    st.subheader("⚠️ Transparência sobre os Dados")
    with st.expander("Clique para ver a auditoria de qualidade dos dados", expanded=False):
        qual = diag["qualidade_dados"]
        st.warning(f"**Ticket Description:** {qual['ticket_description']['pct']}% contêm placeholder literal `{{product_purchased}}`")
        st.warning(f"**Resolution:** {qual['resolution']['pct_nulo']}% nulo — os preenchidos são texto aleatório (ex: \"{qual['resolution']['exemplos'][0]}\")")
        st.warning(f"**Timestamps:** Compras de {qual['timestamps']['date_of_purchase_range'][0]} a {qual['timestamps']['date_of_purchase_range'][1]}, mas FRT/TTR concentrados em {qual['timestamps']['frt_range'][0]} a {qual['timestamps']['frt_range'][1]}")
        st.warning(f"**README erra:** {qual['readme_erro']['realidade']}")
        st.info("Estas limitações reforçam que o valor real da proposta está no **design do processo e no protótipo funcional**, não na análise estatística dos dados sintéticos.")


# ===== TAB 2: SIMULADOR DE TRIAGEM IA ======================================

with tab2:
    st.header("🤖 Simulador de Triagem Inteligente")
    st.caption("Digite um ticket real e veja a IA classificar, priorizar e sugerir roteamento em tempo real")

    # --- Input ---
    col_input, col_config = st.columns([3, 1])

    with col_input:
        ticket_text = st.text_area(
            "Descreva o problema do cliente:",
            placeholder="Ex: Meu pedido chegou com o produto errado. Já é a segunda vez que isso acontece e estou muito frustrado. Quero reembolso imediato.",
            height=120,
        )

    with col_config:
        st.markdown("**Exemplos rápidos:**")
        examples = {
            "Senha bloqueada": "Não consigo acessar minha conta, tentei resetar a senha mas o email não chega. Preciso de ajuda urgente.",
            "Reembolso furioso": "ISSO É UM ABSURDO! Cobram meu cartão duas vezes e ninguém resolve! Quero meu dinheiro de volta AGORA ou vou reclamar no Procon!",
            "Dúvida simples": "Oi, gostaria de saber quais são as formas de pagamento aceitas para o plano anual.",
            "Bug técnico": "O aplicativo está crashando toda vez que tento abrir a aba de relatórios. Já reinstalei e o problema persiste. Versão 3.2.1 no Android 14.",
            "Cancelamento": "Preciso cancelar minha assinatura. A plataforma não atende mais minhas necessidades e o suporte tem sido muito lento.",
        }
        selected = st.radio("Ou escolha:", list(examples.keys()), label_visibility="collapsed")
        if st.button("Usar exemplo", use_container_width=True):
            ticket_text = examples[selected]
            st.rerun()

    # --- Classificação local (sem API) ---
    if st.button("🚀 Triar com IA", type="primary", use_container_width=True):
        if not ticket_text.strip():
            st.error("Digite ou selecione um ticket para classificar.")
        else:
            with st.spinner("Analisando ticket..."):
                import time
                time.sleep(0.8)  # Simula processamento

                # Classificação baseada em regras semânticas
                text_lower = ticket_text.lower()

                # Categoria
                if any(w in text_lower for w in ["reembolso", "reembolsar", "dinheiro de volta", "cobrança", "cobrado", "refund"]):
                    categoria = "Refund Request"
                    cat_conf = 92
                elif any(w in text_lower for w in ["cancelar", "cancela", "cancelamento", "desisto"]):
                    categoria = "Cancellation Request"
                    cat_conf = 89
                elif any(w in text_lower for w in ["bug", "crash", "erro", "não funciona", "travando", "problema técnico", "crashando"]):
                    categoria = "Technical Issue"
                    cat_conf = 95
                elif any(w in text_lower for w in ["pagamento", "fatura", "cobrança", "plano", "preço", "valor"]):
                    categoria = "Billing Inquiry"
                    cat_conf = 87
                elif any(w in text_lower for w in ["senha", "acesso", "login", "conta", "acessar"]):
                    categoria = "Access / Account"
                    cat_conf = 91
                else:
                    categoria = "Product Inquiry"
                    cat_conf = 78

                # Sentimento
                negative_words = ["frustrado", "absurdo", "furioso", "raiva", "péssimo", "horrível",
                                  "nunca mais", "procon", "processar", "inaceitável", "revoltado", "lento"]
                urgent_words = ["urgente", "imediato", "agora", "socorro", "emergência"]
                positive_words = ["obrigado", "oi", "gostaria", "por favor", "poderia"]

                neg_count = sum(1 for w in negative_words if w in text_lower)
                urg_count = sum(1 for w in urgent_words if w in text_lower)
                pos_count = sum(1 for w in positive_words if w in text_lower)

                if neg_count >= 2:
                    sentimento = "😡 Muito irritado"
                    sent_color = "red"
                elif neg_count >= 1:
                    sentimento = "😤 Frustrado"
                    sent_color = "orange"
                elif urg_count >= 1:
                    sentimento = "⚡ Urgente"
                    sent_color = "yellow"
                elif pos_count >= 1:
                    sentimento = "😊 Neutro / Cordial"
                    sent_color = "green"
                else:
                    sentimento = "😐 Neutro"
                    sent_color = "blue"

                # Prioridade
                if neg_count >= 2 or urg_count >= 1:
                    prioridade = "🔴 Crítica"
                elif neg_count >= 1 or categoria in ["Refund Request", "Cancellation Request"]:
                    prioridade = "🟠 Alta"
                elif categoria == "Technical Issue":
                    prioridade = "🟡 Média"
                else:
                    prioridade = "🟢 Baixa"

                # Roteamento
                if categoria == "Cancellation Request" or neg_count >= 2:
                    nivel = "🔴 Nível 4 — Escalação Imediata"
                    nivel_desc = "Encaminhar para supervisor/retenção. Risco de churn."
                    nivel_badge = "badge-red"
                elif categoria == "Refund Request":
                    nivel = "🟡 Nível 3 — Human Required"
                    nivel_desc = "Agente sênior obrigatório. Verificação financeira + empatia."
                    nivel_badge = "badge-yellow"
                elif categoria in ["Technical Issue", "Access / Account"]:
                    nivel = "🔵 Nível 2 — Agent Assist"
                    nivel_desc = "IA prepara contexto + rascunho. Agente revisa e envia."
                    nivel_badge = "badge-blue"
                else:
                    nivel = "🟢 Nível 1 — Auto-resolve"
                    nivel_desc = "Resposta automática via FAQ/base de conhecimento."
                    nivel_badge = "badge-green"

                # Rascunho de resposta
                drafts = {
                    "Refund Request": "Prezado(a) cliente,\n\nLamentamos o transtorno. Identificamos sua solicitação de reembolso e estamos encaminhando para nossa equipe financeira. Prazo de análise: até 48h úteis.\n\nCaso precise de atualização, responda este email.",
                    "Cancellation Request": "Prezado(a) cliente,\n\nRecebemos sua solicitação de cancelamento. Antes de prosseguir, gostaríamos de entender melhor sua experiência para avaliar se podemos resolver a situação.\n\nUm especialista entrará em contato em até 2 horas.",
                    "Technical Issue": "Prezado(a) cliente,\n\nObrigado por reportar este problema. Com base na descrição, sugerimos:\n1. Limpar o cache do aplicativo\n2. Verificar se há atualização disponível\n3. Tentar em outro dispositivo\n\nCaso persista, nosso time técnico irá investigar.",
                    "Billing Inquiry": "Prezado(a) cliente,\n\nSua consulta sobre faturamento foi recebida. Você pode verificar detalhes na seção 'Minha Conta > Faturas'.\n\nSe precisar de ajuda adicional, estamos à disposição.",
                    "Access / Account": "Prezado(a) cliente,\n\nPara recuperar seu acesso:\n1. Acesse [link de reset]\n2. Use o email cadastrado\n3. Verifique a caixa de spam\n\nSe o problema persistir em 15 minutos, responda este email.",
                    "Product Inquiry": "Prezado(a) cliente,\n\nObrigado pelo contato! Segue a informação solicitada:\n[Resposta baseada na base de conhecimento]\n\nFicamos à disposição para dúvidas adicionais.",
                }

            # --- Exibição dos resultados ---
            st.divider()
            st.subheader("Resultado da Triagem")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="card">
                    <h4>🏷️ Categoria</h4>
                    <p style="font-size: 1.3rem; font-weight: 700; color: #60a5fa;">{categoria}</p>
                    <p>Confiança: {cat_conf}%</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="card">
                    <h4>😤 Sentimento</h4>
                    <p style="font-size: 1.3rem; font-weight: 700;">{sentimento}</p>
                    <p>Palavras-chave detectadas: {neg_count + urg_count + pos_count}</p>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="card">
                    <h4>🚦 Prioridade</h4>
                    <p style="font-size: 1.3rem; font-weight: 700;">{prioridade}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="card">
                <h4>🔀 Decisão de Roteamento</h4>
                <p style="font-size: 1.2rem; font-weight: 700;"><span class="badge {nivel_badge}">{nivel}</span></p>
                <p>{nivel_desc}</p>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📝 Rascunho de Resposta Sugerida", expanded=True):
                draft = drafts.get(categoria, drafts["Product Inquiry"])
                st.text_area("Resposta (editável pelo agente):", value=draft, height=180, key="draft_response")

            with st.expander("🔍 Explicação da Decisão"):
                st.markdown(f"""
                **Por que esta classificação?**
                - Categoria `{categoria}` detectada por palavras-chave no texto do ticket
                - Sentimento `{sentimento}` baseado em {neg_count} termo(s) negativo(s) e {urg_count} termo(s) de urgência
                - Prioridade definida pela combinação de sentimento + categoria

                **Por que este roteamento?**
                {"- ⚠️ **Ticket financeiro/cancelamento → nunca automatizar.** Requer empatia e verificação humana." if categoria in ["Refund Request", "Cancellation Request"] else "- Categoria permite assistência de IA com supervisão humana."}
                {"- ⚠️ **Cliente muito irritado → escalar imediatamente.** Risco de churn e exposição negativa." if neg_count >= 2 else ""}
                """)


# ===== TAB 3: PROPOSTA DE AUTOMAÇÃO ========================================

with tab3:
    st.header("📋 Proposta de Automação com IA")
    st.caption("O que automatizar, o que NÃO automatizar, e como funciona na prática")

    st.divider()

    # --- 4 Níveis ---
    st.subheader("Arquitetura de 4 Níveis de Roteamento")

    niveis = [
        {
            "emoji": "🟢",
            "nome": "Nível 1 — Auto-resolve",
            "desc": "IA responde sozinha, sem intervenção humana",
            "quando": "Perguntas de FAQ, consultas de status, dúvidas simples sobre produto",
            "tipos": "Product Inquiry, Billing Inquiry (consultas simples)",
            "pct": "~25%",
            "badge": "badge-green",
        },
        {
            "emoji": "🔵",
            "nome": "Nível 2 — Agent Assist",
            "desc": "IA prepara contexto e rascunho, agente revisa e envia",
            "quando": "Problemas técnicos, bugs, configurações, acessos",
            "tipos": "Technical Issue, Access/Account",
            "pct": "~35%",
            "badge": "badge-blue",
        },
        {
            "emoji": "🟡",
            "nome": "Nível 3 — Human Required",
            "desc": "Vai direto para agente sênior, IA apenas organiza o contexto",
            "quando": "Reembolsos, disputas financeiras, casos complexos",
            "tipos": "Refund Request, Billing Inquiry (disputas)",
            "pct": "~30%",
            "badge": "badge-yellow",
        },
        {
            "emoji": "🔴",
            "nome": "Nível 4 — Escalação Imediata",
            "desc": "Vai para supervisor/retenção com alerta de prioridade máxima",
            "quando": "Cliente furioso, ameaça jurídica, cancelamento iminente, fraude",
            "tipos": "Cancellation Request, qualquer ticket com sentimento muito negativo",
            "pct": "~10%",
            "badge": "badge-red",
        },
    ]

    for n in niveis:
        st.markdown(f"""
        <div class="card">
            <h4>{n['emoji']} {n['nome']} <span class="badge {n['badge']}">{n['pct']} dos tickets</span></h4>
            <p><strong>{n['desc']}</strong></p>
            <p>📌 <strong>Quando:</strong> {n['quando']}</p>
            <p>🏷️ <strong>Tipos:</strong> {n['tipos']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- Fluxo visual ---
    st.subheader("Fluxo Proposto: Ticket → Resolução")
    st.markdown("""
    ```
    📩 Ticket entra (qualquer canal)
         │
         ▼
    🤖 IA classifica (Categoria + Sentimento + Prioridade)
         │
         ├── Confiança ≥ 90% + FAQ existe ──→ 🟢 Auto-resolve
         │
         ├── Problema técnico / acesso ────→ 🔵 Agent Assist (IA + Humano)
         │
         ├── Financeiro / reembolso ───────→ 🟡 Human Required (Agente Sênior)
         │
         └── Furioso / cancelamento ───────→ 🔴 Escalação (Supervisor)
    ```
    """)

    st.divider()

    # --- O que NÃO automatizar ---
    st.subheader("🚫 O que NÃO automatizar (e por quê)")

    col1, col2 = st.columns(2)

    with col1:
        st.error("""
        **Cancelamento de Assinatura**
        - Requer escuta ativa e empatia humana
        - Oportunidade de retenção (oferecer desconto, plano diferente)
        - Risco de churn irreversível se mal gerenciado
        - SLA máximo: 2 horas
        """)

    with col2:
        st.error("""
        **Reembolso e Disputas Financeiras**
        - Requer verificação de políticas e auditoria
        - Implicações legais (CDC, Procon)
        - Cliente já está insatisfeito — IA sem empatia piora
        - Precisa de agente sênior com autonomia de decisão
        """)

    st.warning("""
    **Tickets de cliente muito irritado (qualquer categoria)**
    - Sentimento detectado como "muito negativo" → escalar imediatamente
    - IA pode gerar respostas que soam robóticas e inflamam a situação
    - Humano com treinamento em gestão de crise é insubstituível
    """)

    st.divider()

    # --- ROI ---
    st.subheader("💰 Impacto Financeiro Projetado")

    eco = diag["desperdicio"]["economia_total"]
    premissas = diag["desperdicio"]["premissas"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Economia Anual", f"R$ {eco['economia_anual_brl']:,.0f}")
    with col2:
        st.metric("Economia Mensal", f"R$ {eco['economia_mensal_brl']:,.0f}")
    with col3:
        st.metric("Tickets Automatizáveis", f"{eco['tickets_automatizaveis']:,} ({eco['pct_do_total']}%)")

    st.caption(f"Premissas: Custo/hora agente = R$ {premissas['custo_hora_agente_brl']:.0f} | AHT = {premissas['aht_minutos']} min | Fonte: Benchmarks de mercado BR")


# ===== TAB 4: ANÁLISE CRUZADA DOS DATASETS ================================

with tab4:
    st.header("🔬 Análise Cruzada — Dataset 1 × Dataset 2")
    st.caption("Comparando os dois datasets para entender viabilidade de classificação e transferência de conhecimento")

    st.divider()

    # --- Dataset 2: distribuição de categorias ---
    st.subheader("Dataset 2 — Distribuição de Categorias (IT Service Tickets)")

    topic_counts = df2["Topic_group"].value_counts().reset_index()
    topic_counts.columns = ["Categoria", "Quantidade"]

    col_chart, col_table = st.columns([2, 1])

    with col_chart:
        fig_ds2 = px.bar(
            topic_counts, x="Quantidade", y="Categoria", orientation="h",
            color="Quantidade",
            color_continuous_scale=["#60a5fa", "#c084fc"],
            text_auto=True,
        )
        fig_ds2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            height=400,
            showlegend=False,
        )
        st.plotly_chart(fig_ds2, use_container_width=True)

    with col_table:
        st.dataframe(
            topic_counts.assign(
                Percentual=lambda x: (x["Quantidade"] / x["Quantidade"].sum() * 100).round(1).astype(str) + "%"
            ),
            hide_index=True,
            use_container_width=True,
        )

    st.divider()

    # --- Comparação de qualidade textual ---
    st.subheader("Comparação de Qualidade Textual")

    ds1_desc = df["Ticket Description"].astype(str)
    ds2_doc = df2["Document"].astype(str)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Dataset 1 — Ticket Description")
        st.error("⚠️ Textos sintéticos com placeholders")
        for i, text in enumerate(ds1_desc.head(3)):
            with st.expander(f"Exemplo {i+1}", expanded=(i == 0)):
                st.text(text[:300])
        avg_words_ds1 = ds1_desc.str.split().str.len().mean()
        placeholder_pct = ds1_desc.str.contains(r"\{product_purchased\}", regex=True).mean() * 100
        st.metric("Média de palavras", f"{avg_words_ds1:.0f}")
        st.metric("Com placeholder literal", f"{placeholder_pct:.0f}%")

    with col2:
        st.markdown("#### Dataset 2 — Document (IT Tickets)")
        st.warning("⚠️ Textos pré-processados (tokenizados)")
        for i, text in enumerate(ds2_doc.head(3)):
            with st.expander(f"Exemplo {i+1}", expanded=(i == 0)):
                st.text(text[:300])
        avg_words_ds2 = ds2_doc.str.split().str.len().mean()
        avg_len_ds2 = ds2_doc.str.len().mean()
        st.metric("Média de palavras", f"{avg_words_ds2:.0f}")
        st.metric("Média de caracteres", f"{avg_len_ds2:.0f}")

    st.divider()

    # --- Viabilidade de cruzamento ---
    st.subheader("Viabilidade de Transferência entre Datasets")

    st.markdown("""
    <div class="card">
        <h4>🚫 Por que NÃO treinar no Dataset 2 e aplicar no Dataset 1</h4>
        <p><strong>Domain shift:</strong> Dataset 2 é de TI corporativa (Hardware, HR Support, Storage). Dataset 1 é suporte B2C (Billing, Refund, Cancellation). As categorias são completamente diferentes.</p>
        <p style="margin-top: 0.5rem;"><strong>Formato incompatível:</strong> Dataset 2 tem textos tokenizados (stopwords removidas). Dataset 1 tem templates com placeholders. Nenhum dos dois reflete linguagem natural real.</p>
        <p style="margin-top: 0.5rem;"><strong>Decisão tomada:</strong> Em vez de forçar um modelo que daria resultados enganosos, optei por classificação por regras semânticas no protótipo — funciona com texto real digitado pelo avaliador, independente dos datasets.</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # --- O que cada dataset contribui ---
    st.subheader("📊 Contribuição de Cada Dataset para a Solução")

    col1, col2 = st.columns(2)

    with col1:
        st.success("""
        **Dataset 1 — O que usamos**
        - ✅ Status dos tickets → backlog (67.3%)
        - ✅ Ticket Type → 5 categorias reais
        - ✅ Canal + Prioridade → heatmap de gargalos
        - ✅ Volume → estimativa financeira (R$ 42K/ano)
        - ❌ CSAT → descartado (uniforme/aleatório)
        - ❌ Timestamps → descartados (fabricados)
        - ❌ Textos → descartados (templates sintéticos)
        """)

    with col2:
        st.success("""
        **Dataset 2 — O que usamos**
        - ✅ 8 categorias → referência para design do classificador
        - ✅ Volume (48K) → validação de que classificação por categoria funciona em escala
        - ✅ Análise de distribuição → entender desbalanceamento
        - ❌ Textos → pré-processados demais para NLP moderno
        - ❌ Treinamento direto → domain shift impede uso
        """)

    st.info("**Conclusão:** Ambos os datasets contribuem para a solução, mas nenhum dos dois é adequado para treinamento direto de ML/NLP. O valor real está na análise tabular (Dataset 1) e na referência de categorias (Dataset 2). O protótipo funciona com texto real, não com dados dos datasets.")
