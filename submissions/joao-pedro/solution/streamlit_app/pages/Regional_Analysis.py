"""
Regional Analysis - Análise detalhada por região
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.data_loader import load_benchmarks, load_deals
from core.scoring_engine import score_all_deals

st.set_page_config(page_title="Análise Regional", page_icon="🌍", layout="wide")

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
st.title("🌍 Análise Regional")
st.markdown(f"""
Análise comparativa das **{len(benchmarks['region_wr'])} regiões**, incluindo performance, 
capacidade e padrões de transferência.
""")

st.divider()

# =============================================================================
# OVERVIEW DAS REGIÕES
# =============================================================================
st.subheader("📊 Overview das Regiões")

# Agrupar por região
region_stats = {}

for r in results:
    region = r['deal_info'].get('regional_office', 'Unknown')
    
    if region not in region_stats:
        region_stats[region] = {
            'deals': 0,
            'scores': [],
            'viabilities': [],
            'sellers': set(),
            'active_deals_total': 0,
            'prospecting_total': 0,
            'actions': {}
        }
    
    region_stats[region]['deals'] += 1
    region_stats[region]['scores'].append(r['score'])
    region_stats[region]['viabilities'].append(r['viability'])
    region_stats[region]['sellers'].add(r['deal_info']['sales_agent'])
    
    action = r['action']['type']
    region_stats[region]['actions'][action] = region_stats[region]['actions'].get(action, 0) + 1

# Calcular carga e prospecting por região
for region, stats in region_stats.items():
    for seller in stats['sellers']:
        stats['active_deals_total'] += benchmarks['seller_active_deals'].get(seller, 0)
        stats['prospecting_total'] += benchmarks['seller_prospecting'].get(seller, 0)

# Criar DataFrame
regions_data = []

for region, stats in region_stats.items():
    if region == 'Unknown' or not stats['sellers']:
        continue
    
    regions_data.append({
        'Região': region,
        'Deals (Engaging)': stats['deals'],
        'Vendedores': len(stats['sellers']),
        'Score Médio': sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0,
        'Viabilidade Média': sum(stats['viabilities']) / len(stats['viabilities']) if stats['viabilities'] else 0,
        'Win Rate (%)': benchmarks['region_wr'].get(region, 0),
        'Carga Total': stats['active_deals_total'],
        'Carga Média/Vendedor': stats['active_deals_total'] / len(stats['sellers']) if stats['sellers'] else 0,
        'Prospecting Total': stats['prospecting_total'],
        'Prosp Médio/Vendedor': stats['prospecting_total'] / len(stats['sellers']) if stats['sellers'] else 0,
        'DISCARD (%)': (stats['actions'].get('DISCARD', 0) / stats['deals'] * 100) if stats['deals'] > 0 else 0,
        'TRANSFER (%)': ((stats['actions'].get('TRANSFER', 0) + stats['actions'].get('CONSIDER_TRANSFER', 0)) / stats['deals'] * 100) if stats['deals'] > 0 else 0
    })

if not regions_data:
    st.error("❌ Não há dados regionais disponíveis para análise.")
    st.stop()

regions_df = pd.DataFrame(regions_data).sort_values('Deals (Engaging)', ascending=False)

st.dataframe(
    regions_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Score Médio': st.column_config.NumberColumn('Score Médio', format="%.1f"),
        'Viabilidade Média': st.column_config.NumberColumn('Viab Média', format="%.1f"),
        'Win Rate (%)': st.column_config.ProgressColumn('Win Rate', format="%.1f%%", min_value=0, max_value=100),
        'Carga Média/Vendedor': st.column_config.NumberColumn('Carga/Vend', format="%.0f"),
        'Prosp Médio/Vendedor': st.column_config.NumberColumn('Prosp/Vend', format="%.0f"),
        'DISCARD (%)': st.column_config.NumberColumn('DISCARD %', format="%.1f%%"),
        'TRANSFER (%)': st.column_config.NumberColumn('TRANSFER %', format="%.1f%%")
    }
)

st.divider()

# =============================================================================
# COMPARAÇÃO DE PERFORMANCE
# =============================================================================
st.subheader("📈 Comparação de Performance")

col1, col2 = st.columns(2)

with col1:
    # Win Rate por região
    fig = px.bar(
        regions_df,
        x='Região',
        y='Win Rate (%)',
        title='Win Rate por Região',
        color='Win Rate (%)',
        color_continuous_scale='RdYlGn',
        text='Win Rate (%)'
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.add_hline(y=benchmarks['global_wr'], line_dash="dash", line_color="red", annotation_text=f"Global {benchmarks['global_wr']:.1f}%")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Scatter: Viabilidade vs Score
    fig = px.scatter(
        regions_df,
        x='Viabilidade Média',
        y='Score Médio',
        size='Deals (Engaging)',
        color='Win Rate (%)',
        hover_name='Região',
        title='Viabilidade vs Score por Região',
        labels={'Viabilidade Média': 'Viabilidade Média', 'Score Médio': 'Score Médio'},
        color_continuous_scale='RdYlGn'
    )
    st.plotly_chart(fig, use_container_width=True)

# Insights
best_region = regions_df.nlargest(1, 'Win Rate (%)').iloc[0]
worst_region = regions_df.nsmallest(1, 'Win Rate (%)').iloc[0]

col1, col2 = st.columns(2)

with col1:
    st.success(f"""
    ✅ **Melhor Performance:** {best_region['Região']}
    
    - Win Rate: {best_region['Win Rate (%)']:.1f}%
    - Score Médio: {best_region['Score Médio']:.1f}
    - Viabilidade Média: {best_region['Viabilidade Média']:.1f}
    - Vendedores: {best_region['Vendedores']}
    """)

with col2:
    st.error(f"""
    ⚠️ **Precisa Atenção:** {worst_region['Região']}
    
    - Win Rate: {worst_region['Win Rate (%)']:.1f}%
    - Score Médio: {worst_region['Score Médio']:.1f}
    - Viabilidade Média: {worst_region['Viabilidade Média']:.1f}
    - Vendedores: {worst_region['Vendedores']}
    """)

st.divider()

# =============================================================================
# CAPACIDADE E CARGA
# =============================================================================
st.subheader("⚙️ Capacidade e Carga por Região")

col1, col2 = st.columns(2)

with col1:
    # Carga média por vendedor
    fig = px.bar(
        regions_df,
        x='Região',
        y='Carga Média/Vendedor',
        title='Carga Média por Vendedor',
        color='Carga Média/Vendedor',
        color_continuous_scale='RdYlGn_r',
        text='Carga Média/Vendedor'
    )
    fig.update_traces(texttemplate='%.0f deals', textposition='outside')
    fig.add_hline(y=100, line_dash="dash", line_color="orange", annotation_text="Threshold Alta Carga")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Prospecting médio por vendedor
    fig = px.bar(
        regions_df,
        x='Região',
        y='Prosp Médio/Vendedor',
        title='Prospecting Médio por Vendedor',
        color='Prosp Médio/Vendedor',
        color_continuous_scale='RdYlGn',
        text='Prosp Médio/Vendedor'
    )
    fig.update_traces(texttemplate='%.0f', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# Análise de desbalanceamento
max_carga = regions_df['Carga Média/Vendedor'].max()
min_carga = regions_df['Carga Média/Vendedor'].min()
ratio_carga = max_carga / min_carga if min_carga > 0 else 0

if ratio_carga > 1.5:
    st.warning(f"""
    ⚠️ **Desbalanceamento de Carga Detectado**
    
    - Região mais carregada: {regions_df.nlargest(1, 'Carga Média/Vendedor').iloc[0]['Região']} ({max_carga:.0f} deals/vendedor)
    - Região menos carregada: {regions_df.nsmallest(1, 'Carga Média/Vendedor').iloc[0]['Região']} ({min_carga:.0f} deals/vendedor)
    - **Ratio: {ratio_carga:.1f}×**
    
    **Ação recomendada:** Considerar redistribuir deals entre regiões ou contratar na região sobrecarregada.
    """)

st.divider()

# =============================================================================
# TRANSFERÊNCIAS INTER-REGIONAIS
# =============================================================================
st.subheader("🔀 Transferências Inter-Regionais")

# Filtrar transfers
transfer_results = [r for r in results if r['action']['type'] in ['TRANSFER', 'CONSIDER_TRANSFER']]

# Contar transfers entre regiões
inter_regional_transfers = []

for r in transfer_results:
    current_region = r['deal_info'].get('regional_office', 'Unknown')
    
    if 'details' in r['action'] and 'transfer_level' in r['action']['details']:
        transfer_level = r['action']['details']['transfer_level']
        
        if transfer_level == 'other_region':
            # Pegar região do target (se disponível no context)
            inter_regional_transfers.append({
                'De': current_region,
                'Para': 'Other',  # Simplificado
                'Deal': r['opportunity_id'],
                'Score': r['score']
            })

st.markdown(f"**Total de Transfers Inter-Regionais:** {len(inter_regional_transfers)}")

if len(inter_regional_transfers) > 0:
    pct_inter = (len(inter_regional_transfers) / len(transfer_results)) * 100
    
    st.info(f"""
    📊 **{pct_inter:.1f}% das transferências** são inter-regionais (entre diferentes regiões).
    
    Isso pode indicar:
    - Desbalanceamento de capacidade entre regiões
    - Necessidade de contratação em regiões específicas
    - Oportunidade de redistribuição estratégica
    """)
else:
    st.success("✅ Não há transferências inter-regionais. Capacidade está bem distribuída dentro das regiões.")

st.divider()

# =============================================================================
# DISTRIBUIÇÃO DE AÇÕES POR REGIÃO
# =============================================================================
st.subheader("🎯 Distribuição de Ações por Região")

# Criar dados para stacked bar
action_by_region = []

for region, stats in region_stats.items():
    if region == 'Unknown':
        continue
    
    total = stats['deals']
    
    for action, count in stats['actions'].items():
        action_by_region.append({
            'Região': region,
            'Ação': action,
            'Quantidade': count
        })

actions_df = pd.DataFrame(action_by_region)

# Pivot para gráfico
actions_pivot = actions_df.pivot(index='Região', columns='Ação', values='Quantidade').fillna(0)

# Gráfico de barras empilhadas
fig = go.Figure()

for action in actions_pivot.columns:
    fig.add_trace(go.Bar(
        name=action,
        x=actions_pivot.index,
        y=actions_pivot[action]
    ))

fig.update_layout(
    barmode='stack',
    title='Distribuição de Ações por Região',
    xaxis_title='Região',
    yaxis_title='Número de Deals'
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# =============================================================================
# DRILL-DOWN POR REGIÃO
# =============================================================================
st.subheader("🔍 Drill-Down por Região")

selected_region = st.selectbox(
    "Selecione uma região:",
    regions_df['Região'].tolist()
)

# Filtrar deals e vendedores da região
region_deals = [r for r in results if r['deal_info'].get('regional_office') == selected_region]
region_sellers = list(set([r['deal_info']['sales_agent'] for r in region_deals]))

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Deals em Engaging", len(region_deals))

with col2:
    st.metric("Vendedores", len(region_sellers))

with col3:
    avg_score = sum(d['score'] for d in region_deals) / len(region_deals)
    st.metric("Score Médio", f"{avg_score:.1f}")

with col4:
    avg_viab = sum(d['viability'] for d in region_deals) / len(region_deals)
    st.metric("Viabilidade Média", f"{avg_viab:.1f}")

# Vendedores da região
st.markdown("### Vendedores desta Região")

sellers_table = []

for seller in region_sellers:
    seller_deals = [d for d in region_deals if d['deal_info']['sales_agent'] == seller]
    
    sellers_table.append({
        'Vendedor': seller,
        'Deals': len(seller_deals),
        'Score Médio': sum(d['score'] for d in seller_deals) / len(seller_deals),
        'Viabilidade': sum(d['viability'] for d in seller_deals) / len(seller_deals),
        'Carga Total': benchmarks['seller_active_deals'].get(seller, 0),
        'Prospecting': benchmarks['seller_prospecting'].get(seller, 0),
        'Win Rate': benchmarks['seller_wr'].get(seller, 0)
    })

sellers_df = pd.DataFrame(sellers_table).sort_values('Deals', ascending=False)

st.dataframe(
    sellers_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Score Médio': st.column_config.NumberColumn('Score Médio', format="%.1f"),
        'Viabilidade': st.column_config.NumberColumn('Viabilidade', format="%.1f"),
        'Win Rate': st.column_config.NumberColumn('Win Rate', format="%.1f%%")
    }
)