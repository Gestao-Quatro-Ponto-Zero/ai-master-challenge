"""
Seller Analysis - Análise detalhada por vendedor
"""
 
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path
 
sys.path.append(str(Path(__file__).parent.parent.parent))
 
from core.data_loader import load_benchmarks, load_deals
from core.scoring_engine import score_all_deals
 
st.set_page_config(page_title="Análise por Vendedor", page_icon="👥", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)
 
# Cache
@st.cache_data(ttl=3600)
def load_data():
    benchmarks = load_benchmarks()
    deals = load_deals(deal_stage='Engaging')
    results = score_all_deals(deals, benchmarks)
    return benchmarks, results
 
benchmarks, results = load_data()
 
# =============================================================================
# HEADER
# =============================================================================
st.title("👥 Análise por Vendedor")
st.markdown(f"Análise detalhada dos **{len(benchmarks['seller_wr'])} vendedores** com deals em Engaging")
 
st.divider()
 
# =============================================================================
# TABELA DE VENDEDORES
# =============================================================================
st.subheader("📊 Overview dos Vendedores")
 
# Agrupar deals por vendedor
seller_stats = {}
for r in results:
    seller = r['deal_info']['sales_agent']
    if seller not in seller_stats:
        seller_stats[seller] = {
            'deals': [],
            'scores': [],
            'actions': {}
        }
    
    seller_stats[seller]['deals'].append(r)
    seller_stats[seller]['scores'].append(r['score'])
    
    action_type = r['action']['type']
    seller_stats[seller]['actions'][action_type] = seller_stats[seller]['actions'].get(action_type, 0) + 1
 
# Criar DataFrame
sellers_df = pd.DataFrame([
    {
        'Vendedor': seller,
        'Deals': len(stats['deals']),
        'Score Médio': sum(stats['scores']) / len(stats['scores']),
        'Win Rate': benchmarks['seller_wr'].get(seller, 0),
        'Deals Ativos': benchmarks['seller_active_deals'].get(seller, 0),
        'Prospecting': benchmarks['seller_prospecting'].get(seller, 0),
        'Viab Média': sum(d['viability'] for d in stats['deals']) / len(stats['deals']),
        'PUSH_HARD': stats['actions'].get('PUSH_HARD', 0),
        'TRANSFER': stats['actions'].get('TRANSFER', 0) + stats['actions'].get('CONSIDER_TRANSFER', 0),
        'DISCARD': stats['actions'].get('DISCARD', 0),
        'MONITOR': stats['actions'].get('MONITOR', 0)
    }
    for seller, stats in seller_stats.items()
])
 
# Ordenar por deals (decrescente)
sellers_df = sellers_df.sort_values('Deals', ascending=False)
 
st.dataframe(
    sellers_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Score Médio': st.column_config.NumberColumn(
            'Score Médio',
            format="%.1f"
        ),
        'Win Rate': st.column_config.ProgressColumn(
            'Win Rate %',
            format="%.1f",
            min_value=0,
            max_value=100
        ),
        'Viab Média': st.column_config.ProgressColumn(
            'Viab Média',
            format="%.1f",
            min_value=0,
            max_value=100
        ),
        'Deals Ativos': st.column_config.NumberColumn(
            'Deals Ativos'
        ),
        'Prospecting': st.column_config.NumberColumn(
            'Prospecting'
        )
    }
)
 
st.divider()
 
# =============================================================================
# GRÁFICOS
# =============================================================================
st.subheader("📈 Visualizações")
 
col1, col2 = st.columns(2)
 
with col1:
    # Scatter: Prospecting vs Viabilidade
    fig = px.scatter(
        sellers_df,
        x='Prospecting',
        y='Viab Média',
        size='Deals',
        color='Win Rate',
        hover_name='Vendedor',
        title='Prospecting vs Viabilidade Média',
        labels={'Prospecting': 'Prospecting (novos deals)', 'Viab Média': 'Viabilidade Média'},
        color_continuous_scale='RdYlGn'
    )
    st.plotly_chart(fig, use_container_width=True)
 
with col2:
    # Scatter: Deals Ativos vs Score Médio
    fig = px.scatter(
        sellers_df,
        x='Deals Ativos',
        y='Score Médio',
        size='Prospecting',
        color='Viab Média',
        hover_name='Vendedor',
        title='Carga vs Score Médio',
        labels={'Deals Ativos': 'Deals Ativos', 'Score Médio': 'Score Médio'},
        color_continuous_scale='RdYlGn'
    )
    st.plotly_chart(fig, use_container_width=True)
 
st.divider()
 
# =============================================================================
# DRILL-DOWN POR VENDEDOR
# =============================================================================
st.subheader("🔍 Drill-Down por Vendedor")
 
selected_seller = st.selectbox(
    "Selecione um vendedor:",
    sellers_df['Vendedor'].tolist()
)
 
# Filtrar deals do vendedor
seller_deals = [r for r in results if r['deal_info']['sales_agent'] == selected_seller]
 
col1, col2, col3, col4, col5 = st.columns(5)
 
with col1:
    st.metric("Deals em Engaging", len(seller_deals))
 
with col2:
    avg_score = sum(d['score'] for d in seller_deals) / len(seller_deals)
    st.metric("Score Médio", f"{avg_score:.1f}")
 
with col3:
    seller_wr = benchmarks['seller_wr'].get(selected_seller, 0)
    global_wr = benchmarks['global_wr']
    st.metric("Win Rate", f"{seller_wr:.1f}%", delta=f"{seller_wr - global_wr:+.1f} vs global")
 
with col4:
    active = benchmarks['seller_active_deals'].get(selected_seller, 0)
    st.metric("Deals Ativos", active)
 
with col5:
    prosp = benchmarks['seller_prospecting'].get(selected_seller, 0)
    st.metric("Prospecting", prosp)
 
# Deals do vendedor
st.markdown("### Deals deste Vendedor")
 
deals_df = pd.DataFrame([
    {
        'Deal ID': d['opportunity_id'],
        'Score': d['score'],
        'Urgência': d['urgency'],
        'Prob': d['probability'],
        'Valor': d['value'],
        'Viab': d['viability'],
        'Produto': d['deal_info']['product'],
        'Dias': int(d['deal_info']['days_in_pipeline']),
        'Ação': d['action']['type'],
        'Mensagem': d['action']['message']
    }
    for d in seller_deals
])
 
deals_df = deals_df.sort_values('Score', ascending=False)
 
st.dataframe(
    deals_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Score': st.column_config.NumberColumn('Score', format="%.1f"),
        'Urgência': st.column_config.ProgressColumn('Urg', format="%.0f", min_value=0, max_value=100),
        'Prob': st.column_config.ProgressColumn('Prob%', format="%.0f", min_value=0, max_value=100),
        'Valor': st.column_config.ProgressColumn('Val', format="%.0f", min_value=0, max_value=100),
        'Viab': st.column_config.ProgressColumn('Viab', format="%.0f", min_value=0, max_value=100)
    }
)
 
# Distribuição de ações
st.markdown("### Distribuição de Ações Recomendadas")
 
action_counts = {}
for d in seller_deals:
    action_type = d['action']['type']
    action_counts[action_type] = action_counts.get(action_type, 0) + 1
 
action_df = pd.DataFrame([
    {'Ação': action, 'Quantidade': count, '%': f"{(count/len(seller_deals)*100):.1f}%"}
    for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
])
 
col1, col2 = st.columns([1, 1])
 
with col1:
    st.dataframe(action_df, use_container_width=True, hide_index=True)
 
with col2:
    fig = px.pie(
        action_df,
        values='Quantidade',
        names='Ação',
        title=f'Ações - {selected_seller}'
    )
    st.plotly_chart(fig, use_container_width=True)
 
# Insights
st.markdown("### 💡 Insights")
 
if prosp == 0:
    st.warning(f"⚠️ **{selected_seller} não tem prospecting!** Isso indica proteção de deals e reduz viabilidade.")
 
if active > 150:
    st.error(f"🔥 **{selected_seller} está sobrecarregado** com {active} deals ativos (>150)!")
elif active > 100:
    st.warning(f"⚠️ **{selected_seller} tem alta carga** com {active} deals ativos (>100).")
 
discard_count = action_counts.get('DISCARD', 0)
if discard_count > len(seller_deals) * 0.3:
    st.info(f"📊 **{discard_count} deals ({discard_count/len(seller_deals)*100:.1f}%) devem ser descartados.** Considere revisar qualificação.")
 