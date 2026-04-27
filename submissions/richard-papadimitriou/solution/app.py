import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_loader import load_data
from src.scoring import calculate_scores

# Page Config
st.set_page_config(page_title="Sales Priority OS", page_icon="🎯", layout="wide")

# Version: 4.0 (Destaque Edition - Revenue Impact)

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .reality-box { background-color: #fff1f0; padding: 20px; border-radius: 10px; border: 2px solid #ff4d4f; margin-bottom: 20px; }
    .loss-box { background-color: #f6ffed; padding: 20px; border-radius: 10px; border: 2px solid #52c41a; margin-bottom: 20px; }
    .insight-text { font-size: 1.1rem; font-weight: 500; color: #1f1f1f; }
    .deal-card { background-color: white; padding: 1.5rem; border-radius: 0.5rem; border-left: 5px solid #007bff; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .zombie-card { border-left: 5px solid #ff4d4f !important; }
    .closing-card { border-left: 5px solid #52c41a !important; background-color: #f6ffed; }
    .message-box { background-color: #f1f3f5; padding: 1rem; border-radius: 0.5rem; font-family: monospace; border-left: 4px solid #28a745; margin-top: 0.5rem; }
    </style>
    """, unsafe_allow_html=True)

# Data Loading
@st.cache_data
def get_processed_data(version_bust=4.0):
    raw_df = load_data()
    scored_df = calculate_scores(raw_df)
    return raw_df, scored_df

try:
    raw_df, df_open = get_processed_data()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# --- Header ---
st.title("🎯 Sales Priority OS")
st.subheader("Foco em Execução Comercial e Recuperação de Receita")

# --- Tabs ---
tab_monday, tab_manager, tab_ranking, tab_charts, tab_table = st.tabs([
    "📅 Monday Morning Plan", "👔 Manager Command Center", "🔝 Ranking Global", "📊 Analytics", "📋 Tabela Detalhada"
])

# --- TAB: Monday Morning Plan ---
with tab_monday:
    st.markdown("### ☕ Plano de Execução do Vendedor")
    selected_agent_mm = st.selectbox(
        "👤 Selecione seu nome:",
        options=["Selecione um vendedor..."] + sorted(df_open['sales_agent'].unique().tolist()),
        index=0, key="mm_agent_select"
    )
    
    if selected_agent_mm != "Selecione um vendedor...":
        agent_df = df_open[df_open['sales_agent'] == selected_agent_mm].head(10)
        
        # Pipeline Insight per Agent
        st.info(f"💡 **Insight para {selected_agent_mm}:** O maior valor do seu pipeline está em deals de ticket premium que aguardam follow-up executivo.")
        
        col_plan, col_deals = st.columns([1, 2])
        with col_plan:
            st.markdown("#### 📝 Próximos Passos")
            st.markdown(f"""
            <div class="reality-box">
                <b>1. Fechamento Imediato:</b> Deals com flag 'Should Be Closing'.<br>
                <b>2. Recuperação de Atenção:</b> Deals com alta probabilidade ignorados.<br>
                <b>3. Limpeza de Pipeline:</b> Arquivar Zombie Deals.
            </div>
            """, unsafe_allow_html=True)
            st.metric("ROI Potencial em Mãos", f"${agent_df['roi_potential'].sum():,.0f}")
            
        with col_deals:
            for _, deal in agent_df.iterrows():
                card_class = "deal-card"
                if deal['is_zombie']: card_class += " zombie-card"
                if deal['should_be_closing_now']: card_class += " closing-card"
                
                with st.expander(f"📌 {deal['account']} - {deal['product']} ({deal['score']} pts)", expanded=deal['should_be_closing_now']):
                    st.markdown(f"""
                    <div class="{card_class}">
                        <b>Status:</b> {deal['classification']} | <b>ROI Est.:</b> ${deal['roi_potential']:,.0f}
                        <br><b>Memo Executivo:</b> {deal['ai_decision_memo']}
                        <br><b>Insight:</b> {deal['strategic_insight']}
                        <div class="message-box">{deal['suggested_message']}</div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning("Selecione um vendedor.")

# --- TAB: Manager Command Center ---
with tab_manager:
    st.markdown("### 👔 Manager Command Center (Destaque Edition)")
    
    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1: sel_manager = st.multiselect("Filtrar por Manager", options=df_open['manager'].unique())
    with col_f2: sel_office = st.multiselect("Filtrar por Escritório", options=df_open['regional_office'].unique())
    
    m_df = df_open.copy()
    if sel_manager: m_df = m_df[m_df['manager'].isin(sel_manager)]
    if sel_office: m_df = m_df[m_df['regional_office'].isin(sel_office)]
    
    # NEW SECTION: Reality Check & Loss
    col_real1, col_real2 = st.columns(2)
    
    with col_real1:
        st.markdown("### 🚨 Realidade do Pipeline")
        val_closing = m_df[m_df['should_be_closing_now'] == True]['sales_price'].sum()
        ignored_count = len(m_df[m_df['lost_attention_flag'] == True])
        
        st.markdown(f"""
        <div class="reality-box">
            <span style='font-size: 1.5rem; font-weight: bold;'>${val_closing:,.0f}</span><br>
            Receita que deveria estar fechando AGORA (Engaging + Alta Probabilidade).<br><br>
            <span style='font-size: 1.2rem; font-weight: bold;'>{ignored_count} deals</span> sendo ignorados pelo time.
        </div>
        """, unsafe_allow_html=True)
        
    with col_real2:
        st.markdown("### 💸 Onde estamos perdendo dinheiro")
        val_risk = m_df[m_df['lost_attention_flag'] == True]['roi_potential'].sum()
        val_zombie = m_df[m_df['is_zombie'] == True]['sales_price'].sum()
        
        st.markdown(f"""
        <div class="loss-box">
            <b>Valor sob Risco de Inércia:</b> ${val_risk:,.0f}<br>
            <b>Capital Preso em Zombie Deals:</b> ${val_zombie:,.0f}<br><br>
            <p class="insight-text">"Identificamos ${val_risk:,.0f} em oportunidades de alta probabilidade que estão estagnadas. Isso indica falha de <b>execução comercial</b>, não falta de pipeline."</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    # Critical Deals List
    st.markdown("#### 🔝 Top 5 Deals Críticos (Ação Requerida Hoje)")
    critical_df = m_df[m_df['should_be_closing_now'] == True].sort_values('roi_potential', ascending=False).head(5)
    if not critical_df.empty:
        st.dataframe(critical_df[['account', 'product', 'sales_agent', 'roi_potential', 'deal_age']], hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum deal crítico identificado com os filtros atuais.")

    st.divider()
    
    # Manager Insights per Seller
    st.markdown("#### 🏆 Performance de Execução por Vendedor")
    seller_stats = m_df.groupby('sales_agent').agg({
        'roi_potential': 'sum',
        'lost_attention_flag': 'sum',
        'should_be_closing_now': 'sum',
        'is_zombie': 'sum'
    }).rename(columns={
        'roi_potential': 'ROI Total',
        'lost_attention_flag': 'Deals Ignorados',
        'should_be_closing_now': 'Ready to Close',
        'is_zombie': 'Zombies'
    })
    
    def get_pipeline_insight(row):
        if row['Deals Ignorados'] > 2: return "Execução Crítica: Alto volume de oportunidades boas paradas."
        if row['Ready to Close'] > 0: return "Foco em Fechamento: Deals prontos para assinatura."
        if row['Zombies'] > 5: return "Higiene de Pipeline: Vendedor com pipeline inflado por deals mortos."
        return "Execução Saudável: Pipeline fluindo normalmente."

    seller_stats['Insight de Execução'] = seller_stats.apply(get_pipeline_insight, axis=1)
    st.dataframe(seller_stats.sort_values('ROI Total', ascending=False), use_container_width=True)

# --- Other Tabs (kept for consistency) ---
with tab_ranking:
    st.write("### 🔝 Ranking Global (Probabilidade e Valor)")
    st.dataframe(df_open[['account', 'product', 'sales_agent', 'score', 'roi_potential', 'classification']].head(20), hide_index=True, use_container_width=True)

with tab_charts:
    col_a, col_b = st.columns(2)
    with col_a: st.plotly_chart(px.pie(df_open, names='classification', title='Composição do Pipeline'), use_container_width=True)
    with col_b: st.plotly_chart(px.bar(df_open.groupby('classification')['roi_potential'].sum().reset_index(), x='classification', y='roi_potential', title='Valor em Risco por Categoria'), use_container_width=True)

with tab_table:
    st.dataframe(df_open, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.caption("Sales Priority OS v4.0 - Destaque Edition")
