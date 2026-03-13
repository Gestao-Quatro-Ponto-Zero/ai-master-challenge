# app.py
# Lead Scorer Application - Streamlit
# Baseado no diagnóstico de RevOps e Ciência de Dados

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Lead Scorer Inteligente",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CARREGAMENTO DE DADOS
# ============================================================================
@st.cache_data
@st.cache_data
def load_data():
    """Carrega os arquivos CSV garantindo o caminho correto no deploy"""
    import os
    # Detecta o diretório onde o app.py está localizado
    base_path = os.path.dirname(__file__)
    
    files = {
        'accounts': 'accounts.csv',
        'sales_teams': 'sales_teams.csv',
        'products': 'products.csv',
        'sales_pipeline': 'sales_pipeline.csv'
    }
    
    try:
        data = {name: pd.read_csv(os.path.join(base_path, path)) for name, path in files.items()}
        return data['accounts'], data['sales_teams'], data['products'], data['sales_pipeline']
    except FileNotFoundError as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None, None, None

# ============================================================================
# LÓGICA DE SCORING - BASEADA NO DIAGNÓSTICO
# ============================================================================

def calculate_days_in_deal(engage_date, close_date, deal_stage, reference_date=None):
    """
    Calcula dias no deal considerando as descobertas do diagnóstico:
    - Deals em Prospecting não têm engage_date (500 deals identificados)
    - Zona da Morte: 0-15 dias (56% conversão)
    - Zona de Maturidade: 16-120 dias (71-75% conversão)
    - Morte após 150 dias (0% conversão)
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    if deal_stage == 'Prospecting':
        # Deals em Prospecting não contam tempo (engage_date vazio)
        return 0, 'prospecting'
    
    if pd.isna(engage_date):
        return 0, 'no_date'
    
    try:
        engage = pd.to_datetime(engage_date)
        days = (reference_date - engage).days
        
        if days <= 15:
            zone = 'death_zone'  # Zona da Morte
        elif days <= 120:
            zone = 'maturity'  # Zona de Maturidade (melhor conversão)
        elif days <= 150:
            zone = 'late'  # Zona Tardia
        else:
            zone = 'expired'  # Após 150 dias (0% conversão)
        
        return max(0, days), zone
    except:
        return 0, 'error'


def calculate_maturity_score(days, zone, deal_stage):
    """
    Score de Maturidade (35% do peso total)
    Baseado nas descobertas do diagnóstico:
    - 0-15 dias: 20 pontos (alto risco - Zona da Morte)
    - 16-30 dias: 70 pontos (salto para 71.3% conversão)
    - 31-120 dias: 95 pontos (pico de maturidade)
    - 121-150 dias: 85 pontos (ainda bom, mas declinando)
    - 150+ dias: 0 pontos (morte súbita)
    - Prospecting: 50 pontos (neutro, aguardando engajamento)
    """
    if deal_stage == 'Prospecting':
        return 50, "Deal em Prospecting - aguardando início do engajamento"
    
    if zone == 'death_zone':
        score = 20 + (days / 15) * 30  # 20-50 pontos nos primeiros 15 dias
        explanation = f"⚠️ ZONA DE RISCO: {days} dias - 56% de conversão histórica nesta fase"
    elif zone == 'maturity':
        if days <= 30:
            score = 50 + ((days - 15) / 15) * 25  # 50-75 pontos
            explanation = f"✅ EM DESENVOLVIMENTO: {days} dias - Conversão subindo para 71%"
        else:
            score = 75 + ((days - 30) / 90) * 20  # 75-95 pontos
            explanation = f"🎯 ZONA DE OURO: {days} dias - Alta probabilidade de fechamento"
    elif zone == 'late':
        score = 95 - ((days - 120) / 30) * 25  # 95-70 pontos
        explanation = f"⏰ ATENÇÃO: {days} dias - Ainda viável, mas requer ação"
    elif zone == 'expired':
        score = 0
        explanation = f"❌ EXPIRADO: {days} dias - 0% de conversão após 5 meses"
    else:
        score = 50
        explanation = "Dados insuficientes para cálculo de maturidade"
    
    return min(100, max(0, score)), explanation


def calculate_agent_score(sales_agent, sales_teams, sales_pipeline):
    """
    Score do Agente (30% do peso total)
    Baseado na taxa de conversão histórica do agente
    Diagnóstico: variação de 55% a 70% entre agentes
    """
    if pd.isna(sales_agent) or sales_agent not in sales_teams['sales_agent'].values:
        return 50, "Agente não identificado - score neutro aplicado"
    
    # Filtra deals históricos do agente
    agent_deals = sales_pipeline[sales_pipeline['sales_agent'] == sales_agent]
    total_deals = len(agent_deals[agent_deals['deal_stage'].isin(['Won', 'Lost'])])
    won_deals = len(agent_deals[agent_deals['deal_stage'] == 'Won'])
    
    if total_deals == 0:
        return 50, "Agente novo - sem histórico suficiente"
    
    conversion_rate = won_deals / total_deals
    
    # Normaliza para score 0-100 (baseado na faixa 55%-70% do diagnóstico)
    min_rate, max_rate = 0.55, 0.70
    if conversion_rate < min_rate:
        score = 30 + (conversion_rate / min_rate) * 20
    elif conversion_rate > max_rate:
        score = 90 + min(10, (conversion_rate - max_rate) * 100)
    else:
        score = 50 + ((conversion_rate - min_rate) / (max_rate - min_rate)) * 40
    
    explanation = f"👤 {sales_agent}: {conversion_rate:.1%} de conversão ({won_deals}/{total_deals} deals)"
    
    return min(100, max(0, score)), explanation


def calculate_product_score(product, products, close_value):
    """
    Score de Produto (20% do peso total)
    Baseado no fit de produto e valor esperado
    Diagnóstico: volatilidade agressiva entre sales_price e close_value
    """
    if pd.isna(product) or product not in products['product'].values:
        return 50, "Produto não identificado - score neutro aplicado"
    
    product_info = products[products['product'] == product].iloc[0]
    sales_price = product_info['sales_price']
    series = product_info['series']
    
    # Analisa o desconto/upside
    if pd.isna(close_value) or close_value == 0:
        # Deal ainda não fechado - usa preço de tabela
        discount_rate = 0
        value_tier = 'standard'
    else:
        discount_rate = (sales_price - close_value) / sales_price if sales_price > 0 else 0
        if discount_rate < 0:
            value_tier = 'upsell'  # Cliente pagou mais
        elif discount_rate < 0.1:
            value_tier = 'premium'  # Desconto mínimo
        elif discount_rate < 0.25:
            value_tier = 'standard'  # Desconto normal
        else:
            value_tier = 'discount'  # Desconto agressivo
    
    # Score baseado no tier de valor
    tier_scores = {
        'upsell': 95,      # Cliente viu valor e pagou mais
        'premium': 85,     # Quase preço cheio
        'standard': 70,    # Dentro do esperado
        'discount': 45     # Desconto agressivo = menor probabilidade
    }
    
    base_score = tier_scores.get(value_tier, 70)
    
    # Bônus por série de produto (GTX Pro e Plus Pro têm maior valor)
    series_bonus = {
        'GTX': 5,
        'MG': 0,
        'GTK': 10  # Produto enterprise, maior compromisso
    }
    
    score = base_score + series_bonus.get(series, 0)
    
    explanation = f"📦 {product} ({series}): {value_tier.upper()} - R$ {sales_price:,.0f}"
    if discount_rate != 0:
        explanation += f" ({discount_rate:+.1%} vs tabela)"
    
    return min(100, max(0, score)), explanation


def calculate_firmographics_score(account, accounts):
    """
    Score de Firmographics (15% do peso total)
    Diagnóstico: setor é preditor FRACO (apenas 3.7% de gap)
    IMPORTANTE: 68% do pipeline não tem account linkado!
    """
    if pd.isna(account) or account not in accounts['account'].values:
        # 68% dos deals sem account - não penalizar, score neutro
        return 60, "⚠️ Account não vinculado - 68% do pipeline nesta situação (não penalizado)"
    
    account_info = accounts[accounts['account'] == account].iloc[0]
    sector = account_info['sector']
    employees = account_info['employees']
    revenue = account_info['revenue']
    
    # Score de setor (peso baixo conforme diagnóstico)
    sector_scores = {
        'marketing': 85,
        'entertainment': 84,
        'software': 82,
        'technolgy': 81,  # Note: typo no CSV original
        'services': 80,
        'retail': 79,
        'employment': 78,
        'telecommunications': 77,
        'medical': 76,
        'finance': 74
    }
    
    base_sector_score = sector_scores.get(sector.lower() if sector else '', 75)
    
    # Score de tamanho da empresa
    if employees >= 5000:
        size_score = 90  # Enterprise
        size_label = "Enterprise"
    elif employees >= 1000:
        size_score = 80  # Large
        size_label = "Grande"
    elif employees >= 100:
        size_score = 70  # Medium
        size_label = "Média"
    else:
        size_score = 60  # Small
        size_label = "Pequena"
    
    # Combina setor (peso menor) e tamanho (peso maior)
    score = base_sector_score * 0.4 + size_score * 0.6
    
    explanation = f"🏢 {account}: {size_label} ({employees:,} func.) - Setor: {sector}"
    
    return min(100, max(0, score)), explanation


def calculate_deal_score(row, accounts, sales_teams, products, sales_pipeline, reference_date=None):
    """
    Calcula o score final do deal combinando todos os fatores
    Pesos conforme diagnóstico:
    - Maturidade: 35%
    - Agente: 30%
    - Produto: 20%
    - Firmographics: 15%
    """
    # 1. Score de Maturidade (35%)
    days, zone = calculate_days_in_deal(
        row['engage_date'], 
        row['close_date'], 
        row['deal_stage'],
        reference_date
    )
    maturity_score, maturity_exp = calculate_maturity_score(days, zone, row['deal_stage'])
    
    # 2. Score do Agente (30%)
    agent_score, agent_exp = calculate_agent_score(
        row['sales_agent'],
        sales_teams,
        sales_pipeline
    )
    
    # 3. Score do Produto (20%)
    product_score, product_exp = calculate_product_score(
        row['product'],
        products,
        row['close_value']
    )
    
    # 4. Score de Firmographics (15%)
    firmo_score, firmo_exp = calculate_firmographics_score(
        row['account'],
        accounts
    )
    
    # Score final ponderado
    final_score = (
        maturity_score * 0.35 +
        agent_score * 0.30 +
        product_score * 0.20 +
        firmo_score * 0.15
    )
    
    # Explicação consolidada
    full_explanation = {
        'score': round(final_score, 1),
        'maturity': {'score': round(maturity_score, 1), 'explanation': maturity_exp, 'weight': '35%'},
        'agent': {'score': round(agent_score, 1), 'explanation': agent_exp, 'weight': '30%'},
        'product': {'score': round(product_score, 1), 'explanation': product_exp, 'weight': '20%'},
        'firmographics': {'score': round(firmo_score, 1), 'explanation': firmo_exp, 'weight': '15%'},
        'days_in_deal': days,
        'zone': zone
    }
    
    return final_score, full_explanation


# ============================================================================
# FUNÇÕES DE VISUALIZAÇÃO
# ============================================================================

def create_probability_distribution_chart(scores):
    """Cria gráfico de distribuição de probabilidade dos scores"""
    fig = go.Figure()
    
    # Histograma de distribuição
    fig.add_trace(go.Histogram(
        x=scores,
        nbinsx=20,
        name='Distribuição',
        marker_color='#3b82f6',
        opacity=0.7
    ))
    
    # Linhas de referência
    fig.add_vline(x=50, line_dash="dash", line_color="#fbbf24", 
                  annotation_text="Score Médio", annotation_position="top")
    fig.add_vline(x=75, line_dash="dash", line_color="#22c55e",
                  annotation_text="Alta Prioridade", annotation_position="top")
    fig.add_vline(x=30, line_dash="dash", line_color="#ef4444",
                  annotation_text="Atenção", annotation_position="top")
    
    fig.update_layout(
        title="📊 Distribuição de Probabilidade do Pipeline",
        xaxis_title="Score do Deal (0-100)",
        yaxis_title="Quantidade de Deals",
        showlegend=False,
        height=400,
        template="plotly_white"
    )
    
    return fig


def create_score_breakdown_chart(explanation):
    """Cria gráfico de breakdown dos componentes do score"""
    categories = ['Maturidade\n(35%)', 'Agente\n(30%)', 'Produto\n(20%)', 'Firmographics\n(15%)']
    scores = [
        explanation['maturity']['score'],
        explanation['agent']['score'],
        explanation['product']['score'],
        explanation['firmographics']['score']
    ]
    weights = [35, 30, 20, 15]
    
    fig = go.Figure(data=[
        go.Bar(
            name='Score',
            x=categories,
            y=scores,
            marker_color=['#3b82f6', '#8b5cf6', '#22c55e', '#f59e0b'],
            text=scores,
            textposition='outside'
        )
    ])
    
    fig.add_hline(y=explanation['score'], line_dash="dash", line_color="#ef4444",
                  annotation_text=f"Score Final: {explanation['score']}", 
                  annotation_position="top")
    
    fig.update_layout(
        title="🎯 Composição do Score",
        yaxis_range=[0, 100],
        showlegend=False,
        height=350,
        template="plotly_white"
    )
    
    return fig


def get_priority_color(score):
    """Retorna cor e ícone baseado no score"""
    if score >= 75:
        return "🟢", "#22c55e", "Alta Prioridade"
    elif score >= 50:
        return "🟡", "#fbbf24", "Prioridade Média"
    elif score >= 30:
        return "🟠", "#f97316", "Atenção"
    else:
        return "🔴", "#ef4444", "Baixa Prioridade"


# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def main():
    # Injeção de CSS Adaptativo (Light/Dark Mode)
    st.markdown("""
        <style>
            /* Detecta a preferência do sistema e ajusta variáveis */
            :root {
                --g4-blue: #1E293B;
                --g4-accent: #476382;
                --g4-text-light: #F8FAFC;
                --g4-text-dim: #94A3B8;
            }

            /* Estilização Geral Adaptativa */
            .main {
                transition: background-color 0.3s ease;
            }
            
            /* Customização do Banner para Sobreviver a Qualquer Tema */
            .banner-container {
                background-color: var(--g4-blue);
                padding: 40px;
                border-radius: 15px;
                border-left: 12px solid var(--g4-accent);
                margin-bottom: 35px;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            }

            .g4-title { 
                color: #FFFFFF !important; 
                font-size: 36px; 
                font-weight: 700; 
                margin: 0; 
                letter-spacing: -1px;
            }

            .g4-subtitle { 
                color: var(--g4-text-dim) !important; 
                font-size: 19px; 
                margin-top: 8px; 
                font-weight: 400; 
            }

            /* Ajuste de métricas para não "sumirem" no modo escuro */
            [data-testid="stMetricValue"] {
                color: var(--g4-accent) !important;
            }
        </style>
        
        <div class="banner-container">
            <p class="g4-title">G4 AI MASTER</p>
            <p class="g4-subtitle">Lead Scorer: Priorização Estratégica para Escala de Vendas</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Carregar dados
    accounts, sales_teams, products, sales_pipeline = load_data()
    
    if accounts is None:
        st.stop()
    
    # =========================================================================
    # SIDEBAR - FILTROS
    # =========================================================================
    st.sidebar.header("🔍 Filtros")
    
    # Filtro de Vendedor
    all_agents = ['Todos'] + sorted(sales_teams['sales_agent'].unique().tolist())
    selected_agent = st.sidebar.selectbox(
        "👤 Selecione o Vendedor",
        options=all_agents,
        index=0
    )
    
    # Filtro de Stage
    stage_options = ['Todos', 'Engaging', 'Prospecting', 'Won', 'Lost']
    selected_stage = st.sidebar.selectbox(
        "📍 Stage do Deal",
        options=stage_options,
        index=0
    )
    
    # Filtro de Score Mínimo
    min_score = st.sidebar.slider(
        "📊 Score Mínimo",
        min_value=0,
        max_value=100,
        value=0,
        step=5
    )
    
    # =========================================================================
    # PROCESSAMENTO DOS DADOS
    # =========================================================================
    
    # Filtra pipeline ativo (exclui Won/Lost se não for para visualização histórica)
    if selected_stage in ['Engaging', 'Prospecting']:
        pipeline_filtered = sales_pipeline[sales_pipeline['deal_stage'] == selected_stage].copy()
    elif selected_stage == 'Todos':
        # Mostra apenas deals ativos por padrão
        pipeline_filtered = sales_pipeline[
            sales_pipeline['deal_stage'].isin(['Engaging', 'Prospecting'])
        ].copy()
    else:
        pipeline_filtered = sales_pipeline[sales_pipeline['deal_stage'] == selected_stage].copy()
    
    # Filtro por vendedor
    if selected_agent != 'Todos':
        pipeline_filtered = pipeline_filtered[pipeline_filtered['sales_agent'] == selected_agent]
    
    # =========================================================================
    # CÁLCULO DE SCORES
    # =========================================================================
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Pesos do Algoritmo")
    st.sidebar.markdown("""
    - **Maturidade**: 35%
    - **Agente**: 30%
    - **Produto**: 20%
    - **Firmographics**: 15%
    """)
    
    # Calcula scores para todos os deals
    scores = []
    explanations = []
    
    for idx, row in pipeline_filtered.iterrows():
        score, explanation = calculate_deal_score(
            row, accounts, sales_teams, products, sales_pipeline
        )
        scores.append(score)
        explanations.append(explanation)
    
    pipeline_filtered['score'] = scores
    pipeline_filtered['explanation'] = explanations
    
    # Filtra por score mínimo
    pipeline_filtered = pipeline_filtered[pipeline_filtered['score'] >= min_score]
    
    # Ordena por score (maior primeiro)
    pipeline_filtered = pipeline_filtered.sort_values('score', ascending=False)
    
    # =========================================================================
    # MÉTRICAS PRINCIPAIS
    # =========================================================================
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📦 Total de Deals",
            len(pipeline_filtered),
            delta=None
        )
    
    with col2:
        avg_score = pipeline_filtered['score'].mean() if len(pipeline_filtered) > 0 else 0
        st.metric(
            "📈 Score Médio",
            f"{avg_score:.1f}",
            delta=None
        )
    
    with col3:
        high_priority = len(pipeline_filtered[pipeline_filtered['score'] >= 75])
        st.metric(
            "🟢 Alta Prioridade",
            high_priority,
            delta=None
        )
    
    with col4:
        attention = len(pipeline_filtered[pipeline_filtered['score'] < 30])
        st.metric(
            "🔴 Requer Atenção",
            attention,
            delta=None
        )
    
    st.markdown("---")
    
    # =========================================================================
    # GRÁFICOS
    # =========================================================================
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        if len(pipeline_filtered) > 0:
            fig_dist = create_probability_distribution_chart(pipeline_filtered['score'].values)
            st.plotly_chart(fig_dist, use_container_width=True)
    
    with col_chart2:
        # Gráfico de deals por stage refinado
        stage_counts = pipeline_filtered['deal_stage'].value_counts()
        fig_stage = px.pie(
            values=stage_counts.values,
            names=stage_counts.index,
            title="📍 Distribuição por Stage",
            color_discrete_sequence=['#476382', '#94A3B8', '#1E293B', '#CBD5E1'] # Paleta G4
        )
        
        # Ajuste de traços e remoção do "label" indesejado no hover
        fig_stage.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<extra></extra>"
        )

        # A LINHA QUE FALTAVA: Manda o gráfico para a tela
        st.plotly_chart(fig_stage, use_container_width=True)
    
    # =========================================================================
    # TOP 10 DEALS PARA FOCAR
    # =========================================================================
    
    st.markdown("## 🏆 Top 10 Deals para Focar Hoje")
    st.markdown("*Ordenados pelo score de probabilidade de fechamento*")
    
    top_10 = pipeline_filtered.head(10)
    
    for idx, row in top_10.iterrows():
        exp = row['explanation']
        icon, color, priority = get_priority_color(exp['score'])
        
        with st.expander(f"{icon} **{row['opportunity_id']}** - {row['product']} | Score: {exp['score']:.1f} ({priority})"):
            col_exp1, col_exp2 = st.columns([2, 1])
            
            with col_exp1:
                st.markdown("### 📋 Detalhes do Deal")
                # Definimos o valor formatado antes, para a f-string não quebrar
                val_raw = row['close_value']
                valor_formatado = f"R$ {val_raw:,.0f}" if pd.notna(val_raw) and val_raw > 0 else "Não informado"
                
                # Agora a exibição fica limpa e segura
                st.markdown(f"""
                - **Cliente**: {row['account'] if pd.notna(row['account']) else 'Não vinculado'}
                - **Produto**: {row['product']}
                - **Vendedor**: {row['sales_agent']}
                - **Stage**: {row['deal_stage']}
                - **Valor**: {valor_formatado}
                - **Dias no Deal**: {exp['days_in_deal']}
                """)
                
                st.markdown("### 🧠 Explicação do Score (Explainability)")
                st.markdown(f"""
                **Score Final: {exp['score']:.1f}/100**
                
                | Componente | Score | Peso | Explicação |
                |------------|-------|------|------------|
                | Maturidade | {exp['maturity']['score']} | {exp['maturity']['weight']} | {exp['maturity']['explanation']} |
                | Agente | {exp['agent']['score']} | {exp['agent']['weight']} | {exp['agent']['explanation']} |
                | Produto | {exp['product']['score']} | {exp['product']['weight']} | {exp['product']['explanation']} |
                | Firmographics | {exp['firmographics']['score']} | {exp['firmographics']['weight']} | {exp['firmographics']['explanation']} |
                """)
            
            with col_exp2:
                st.markdown("### 📊 Composição")
                fig_breakdown = create_score_breakdown_chart(exp)
                
                # A CORREÇÃO: Passamos um 'key' único baseado no ID do deal
                st.plotly_chart(fig_breakdown, use_container_width=True, key=f"chart_{row['opportunity_id']}")
    
    # =========================================================================
    # TABELA COMPLETA
    # =========================================================================
    
    st.markdown("---")
    st.markdown("## 📋 Todos os Deals")
    
    display_df = pipeline_filtered.copy()
    display_df['icon'] = display_df['score'].apply(lambda x: get_priority_color(x)[0])
    display_df['priority'] = display_df['score'].apply(lambda x: get_priority_color(x)[2])
    
    st.dataframe(
        display_df[[
            'icon', 'opportunity_id', 'sales_agent', 'product', 'account',
            'deal_stage', 'score', 'priority', 'close_value'
        ]],
        use_container_width=True,
        column_config={
            'icon': 'Prioridade',
            'opportunity_id': 'ID',
            'sales_agent': 'Vendedor',
            'product': 'Produto',
            'account': 'Cliente',
            'deal_stage': 'Stage',
            'score': st.column_config.NumberColumn('Score', format='%.1f'),
            'priority': 'Classificação',
            'close_value': st.column_config.NumberColumn('Valor', format='R$ %,.0f')
        }
    )
    
    # =========================================================================
    # RODAPÉ
    # =========================================================================
    
    st.markdown("---")
    
    # Criamos a variável de data de forma simples
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    # Usamos o f-string fechando corretamente as aspas triplas no final
    metodologia_texto = f"""
    ### 📌 Metodologia
    
    Este Lead Scorer foi desenvolvido com base em análise exploratória de dados do seu CRM, identificando:
    
    1. **Zona da Morte (0-15 dias)**: 56% de conversão - maior volume de perdas.
    2. **Zona de Maturidade (16-120 dias)**: 71-75% de conversão - melhor performance.
    3. **Morte Súbita (150+ dias)**: 0% de conversão - nenhum deal histórico ganhou após 5 meses.
    4. **Account Fantasma**: 68% do pipeline sem account linkado - não penalizado no score.
    5. **Variação por Agente**: 55%-70% de conversão - fator de alto peso (30%).
    
    *Última atualização: {agora}*
    """
    
    st.markdown(metodologia_texto)

if __name__ == "__main__":
    main()