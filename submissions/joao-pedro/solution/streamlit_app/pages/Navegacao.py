"""
Navegação - Visão geral do sistema
"""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Navegação", page_icon="🗺️", layout="wide")

st.title("🗺️ Navegue pelo Sistema")


# =============================================================================
# GUIA DE NAVEGAÇÃO
# =============================================================================
st.subheader("🎯 Guia de Navegação")

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    st.error("**🏆 Challenge**")
    st.page_link("pages/Challenge.py", label="🏆 Ver enunciado", icon=None)

with col2:
    st.markdown(
        '<div style="background-color:#1e3a5f;padding:0.6rem 0.75rem;border-radius:0.3rem;'
        'border-left:4px solid #93c5fd;margin-bottom:0.5rem;">'
        '<strong style="color:#dbeafe;">📄 README</strong></div>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/README.py", label="📄 README.md (repositório)", icon=None)

with col3:
    st.info("**📖 Fundamentos**")
    st.page_link("pages/Macro.py", label="📊 Macro", icon=None)
    st.page_link("pages/Heuristica.py", label="🧠 Heurística", icon=None)
    st.page_link("pages/Score_Model.py", label="⚙️ Score-model", icon=None)
    st.page_link("pages/Limitacoes.py", label="⚠️ Limitações e Escalabilidade", icon=None)

with col4:
    st.markdown(
        '<div style="background-color:#1a3a2a;padding:0.6rem 0.75rem;border-radius:0.3rem;'
        'border-left:4px solid #4ade80;margin-bottom:0.5rem;">'
        '<strong style="color:#bbf7d0;">🔑 Raw Data</strong></div>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/Raw_Pipeline.py", label="🗄️ sales_pipeline.csv", icon=None)
    st.page_link("pages/Raw_Accounts.py", label="🗄️ accounts.csv", icon=None)
    st.page_link("pages/Raw_Products.py", label="🗄️ products.csv", icon=None)
    st.page_link("pages/Raw_Teams.py", label="🗄️ sales_teams.csv", icon=None)

with col5:
    st.success("**📂 Primary-Data**")
    st.page_link("pages/Deal_List.py", label="📋 Pipeline", icon=None)
    st.page_link("pages/Accounts_List.py", label="🏢 Accounts", icon=None)
    st.page_link("pages/Products_List.py", label="📦 Products", icon=None)
    st.page_link("pages/Sellers_List.py", label="👤 Sellers", icon=None)
    st.page_link("pages/Managers_List.py", label="👥 Managers", icon=None)

with col6:
    st.warning("**📊 Analysis**")
    st.page_link("pages/Deals_Analysis.py", label="📊 Pipeline Analysis", icon=None)
    st.page_link("pages/Action_Analysis.py", label="🎯 Action Analysis", icon=None)
    st.page_link("pages/Products_Analysis.py", label="📦 Products Analysis", icon=None)
    st.page_link("pages/Regional_Analysis.py", label="🌍 Regional Analysis", icon=None)
    st.page_link("pages/Seller_Analysis.py", label="👥 Seller Analysis", icon=None)
    st.page_link("pages/Transfer_Analysis.py", label="🔀 Transfer Analysis", icon=None)

with col7:
    st.markdown(
        '<div style="background-color:#3b1f6e;padding:0.6rem 0.75rem;border-radius:0.3rem;'
        'border-left:4px solid #a78bfa;margin-bottom:0.5rem;">'
        '<strong style="color:#e9d5ff;">⚙️ Sistema</strong></div>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/Inicializacao.py", label="🚀 Inicialização", icon=None)
    st.page_link("pages/Stack.py", label="🛠️ Arquitetura & Stack", icon=None)
    st.page_link("pages/API.py", label="⚡ API", icon=None)

# =============================================================================
# CHALLENGE
# =============================================================================
st.subheader("🏆 Challenge")

challenge_data = {
    "Página": ["🏆 Challenge"],
    "O que você encontra": [
        "Enunciado completo do Challenge 003 — Lead Scorer",
    ],
    "Contexto": [
        "Área: Vendas / RevOps · Tipo: Build · Time budget: 4–6h · Dataset: ~8.800 oportunidades de CRM",
    ],
}

st.dataframe(pd.DataFrame(challenge_data), use_container_width=True, hide_index=True)

st.divider()

# =============================================================================
# README
# =============================================================================
st.subheader("📄 README")

readme_nav_data = {
    "Página": ["📄 README.md"],
    "O que você encontra": [
        "Conteúdo do README.md na raiz do repositório (entrega, stack, como rodar)",
    ],
    "Contexto": [
        "Documentação principal do projeto (mesmo arquivo do GitHub)",
    ],
}

st.dataframe(pd.DataFrame(readme_nav_data), use_container_width=True, hide_index=True)

st.divider()

# =============================================================================
# FUNDAMENTOS
# =============================================================================
st.subheader("📖 Fundamentos")

fund_data = {
    "Página": ["📊 Macro", "🧠 Heurística", "⚙️ Score-model"],
    "O que você encontra": [
        "Big picture do desafio e solução",
        "Como chegamos à tese (análise exploratória)",
        "Detalhamento técnico do modelo de scoring",
    ],
    "Comece aqui se...": [
        "Quer entender o contexto geral do projeto",
        "Quer saber como chegamos aos insights",
        "Quer entender a lógica do score e ações",
    ],
}

st.dataframe(pd.DataFrame(fund_data), use_container_width=True, hide_index=True)

st.divider()

# =============================================================================
# RAW DATA
# =============================================================================
st.subheader("🔑 Raw Data")

raw_data = {
    "Arquivo": [
        "🗄️ sales_pipeline.csv",
        "🗄️ accounts.csv",
        "🗄️ products.csv",
        "🗄️ sales_teams.csv",
    ],
    "O que você encontra": [
        "Tabela bruta com ~8.800 oportunidades do CRM (fonte central do modelo)",
        "Cadastro completo de contas — setor, receita, funcionários, localidade",
        "Catálogo de produtos com séries e preço de venda",
        "Equipes de vendas — agentes, gestores e escritórios regionais",
    ],
    "Linhas aprox.": ["~8.800", "~500", "~30", "~35"],
}

st.dataframe(pd.DataFrame(raw_data), use_container_width=True, hide_index=True)

st.divider()

# =============================================================================
# PRIMARY-DATA
# =============================================================================
st.subheader("📂 Primary-Data")

data_data = {
    "Página": ["📋 Pipeline", "🏢 Accounts", "📦 Products", "👤 Sellers", "👥 Managers"],
    "O que você encontra": [
        "Todos os deals do pipeline com filtro por stage e scores Engaging",
        "Análise de contas — win rate, volume, top 20",
        "Catálogo de produtos — ciclo, win rate, ticket médio",
        "Vendedores individuais — carga, prospecting, viabilidade",
        "Gestores — performance agregada do time",
    ],
    "Filtros disponíveis": [
        "Stage (Won/Lost/Engaging/Prospecting), vendedor, score mínimo, dias mínimo",
        "Setor, localidade, top 20, mínimo de deals",
        "Série, ordenação por win rate / ciclo / ticket",
        "Região, viabilidade, ordenação",
        "Região, viabilidade, ordenação",
    ],
}

st.dataframe(pd.DataFrame(data_data), use_container_width=True, hide_index=True)

st.divider()

# =============================================================================
# ANALYSIS
# =============================================================================
st.subheader("📊 Analysis (Análises Aprofundadas)")

analysis_data = {
    "Página": [
        "📊 Pipeline Analysis",
        "🎯 Action Analysis",
        "📦 Products Analysis",
        "🌍 Regional Analysis",
        "👥 Seller Analysis",
        "🔀 Transfer Analysis",
    ],
    "O que você encontra": [
        "Tempo no pipeline, win rate por faixa, score e saúde do funil",
        "Distribuição de ações recomendadas, padrões por vendedor e produto",
        "Performance e especialização por produto, mix de ações",
        "Comparação entre regiões — win rate, carga, capacidade",
        "Capacidade, carga, prospecting e viabilidade por vendedor",
        "Deals que precisam ser redistribuídos e destino recomendado",
    ],
    "Insight principal": [
        "Pipeline Engaging está 2.9× acima da mediana Won",
        "27.9% DISCARD + 26% TRANSFER → pipeline travado por falta de ação",
        "Quais produtos têm maior win rate e menor ciclo",
        "Qual região está sobrecarregada vs com capacidade disponível",
        "Quem tem 0 prospecting + alta carga (círculo vicioso)",
        "Hierarquia: mesmo time → mesma região → outra região",
    ],
}

st.dataframe(pd.DataFrame(analysis_data), use_container_width=True, hide_index=True)

st.divider()

# =============================================================================
# SISTEMA
# =============================================================================
st.subheader("⚙️ Sistema")

sistema_data = {
    "Página": ["🚀 Inicialização", "🛠️ Arquitetura & Stack", "⚡ API"],
    "O que você encontra": [
        "Como rodar todos os serviços — Streamlit, API e React",
        "Diagrama de arquitetura, estrutura de pastas e decisões de design",
        "Documentação dos endpoints REST + Swagger UI interativo",
    ],
    "Use quando...": [
        "For rodar o projeto pela primeira vez ou resolver problemas de startup",
        "Quiser entender como as camadas se conectam",
        "Quiser explorar ou testar os endpoints da API",
    ],
}

st.dataframe(pd.DataFrame(sistema_data), use_container_width=True, hide_index=True)
