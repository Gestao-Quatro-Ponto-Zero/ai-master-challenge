"""
Product Analysis - Análise detalhada por produto
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

st.set_page_config(page_title="Análise por Produto", page_icon="📦", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

# Cache
@st.cache_data(ttl=3600)
def load_data():
    benchmarks = load_benchmarks()
    deals = load_deals(deal_stage='Engaging')
    results = score_all_deals(deals, benchmarks)
    
    # Carregar pipeline completo para métricas históricas
    all_deals = load_deals()
    
    return benchmarks, results, all_deals

benchmarks, results, all_deals = load_data()

# =============================================================================
# HEADER
# =============================================================================
st.title("📦 Análise por Produto")
st.markdown(f"""
Análise detalhada dos **{len(benchmarks['product_wr'])} produtos** no pipeline, 
incluindo performance, especialização e padrões de ação.
""")

st.divider()

# =============================================================================
# OVERVIEW DOS PRODUTOS
# =============================================================================
st.subheader("📊 Overview dos Produtos")

# Agrupar deals por produto
product_stats = {}

for r in results:
    product = r['deal_info']['product']
    
    if product not in product_stats:
        product_stats[product] = {
            'deals_engaging': 0,
            'scores': [],
            'days': [],
            'values': [],
            'actions': {}
        }
    
    product_stats[product]['deals_engaging'] += 1
    product_stats[product]['scores'].append(r['score'])
    product_stats[product]['days'].append(r['deal_info']['days_in_pipeline'])
    product_stats[product]['values'].append(r['deal_info']['close_value'])
    
    action = r['action']['type']
    product_stats[product]['actions'][action] = product_stats[product]['actions'].get(action, 0) + 1

# Calcular ciclo médio dos deals FECHADOS (Won) por produto
import pandas as pd

all_deals_df = pd.DataFrame(all_deals)
won_by_product = all_deals_df[all_deals_df['deal_stage'] == 'Won'].groupby('product')['days_in_pipeline'].mean().to_dict()

# Criar DataFrame
products_df = pd.DataFrame([
    {
        'Produto': product,
        'Deals (Engaging)': stats['deals_engaging'],
        'Score Médio': sum(stats['scores']) / len(stats['scores']),
        'Win Rate (%)': benchmarks['product_wr'].get(product, 0),
        'Ticket Médio ($)': sum(stats['values']) / len(stats['values']),
        'Dias Médio (Engaging)': sum(stats['days']) / len(stats['days']),
        'Ciclo Médio Won (dias)': won_by_product.get(product, 0),
        'DISCARD (%)': (stats['actions'].get('DISCARD', 0) / stats['deals_engaging'] * 100),
        'TRANSFER (%)': ((stats['actions'].get('TRANSFER', 0) + stats['actions'].get('CONSIDER_TRANSFER', 0)) / stats['deals_engaging'] * 100)
    }
    for product, stats in product_stats.items()
]).sort_values('Deals (Engaging)', ascending=False)

st.dataframe(
    products_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Score Médio': st.column_config.NumberColumn('Score Médio', format="%.1f"),
        'Win Rate (%)': st.column_config.ProgressColumn('Win Rate', format="%.1f%%", min_value=0, max_value=100),
        'Ticket Médio ($)': st.column_config.NumberColumn('Ticket Médio', format="$%.0f"),
        'Dias Médio (Engaging)': st.column_config.NumberColumn('Dias Médio', format="%.0f"),
        'Ciclo Médio Won (dias)': st.column_config.NumberColumn('Ciclo Won', format="%.0f"),
        'DISCARD (%)': st.column_config.NumberColumn('DISCARD %', format="%.1f%%"),
        'TRANSFER (%)': st.column_config.NumberColumn('TRANSFER %', format="%.1f%%")
    }
)

st.divider()

# =============================================================================
# PERFORMANCE DOS PRODUTOS
# =============================================================================
st.subheader("📈 Performance: Win Rate vs Ticket Médio")

col1, col2 = st.columns(2)

with col1:
    # Scatter: Win Rate vs Ticket Médio
    fig = px.scatter(
        products_df,
        x='Win Rate (%)',
        y='Ticket Médio ($)',
        size='Deals (Engaging)',
        color='Score Médio',
        hover_name='Produto',
        title='Win Rate vs Ticket Médio',
        labels={'Win Rate (%)': 'Win Rate (%)', 'Ticket Médio ($)': 'Ticket Médio ($)'},
        color_continuous_scale='RdYlGn'
    )
    fig.add_hline(y=products_df['Ticket Médio ($)'].mean(), line_dash="dash", line_color="gray", annotation_text="Ticket Médio Geral")
    fig.add_vline(x=benchmarks['global_wr'], line_dash="dash", line_color="gray", annotation_text="WR Global")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Bar chart: Win Rate por produto
    products_sorted = products_df.sort_values('Win Rate (%)', ascending=True)
    
    fig = px.bar(
        products_sorted,
        x='Win Rate (%)',
        y='Produto',
        orientation='h',
        title='Win Rate por Produto',
        color='Win Rate (%)',
        color_continuous_scale='RdYlGn',
        text='Win Rate (%)'
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.add_vline(x=benchmarks['global_wr'], line_dash="dash", line_color="red", annotation_text=f"Global {benchmarks['global_wr']:.1f}%")
    st.plotly_chart(fig, use_container_width=True)

# Insights
best_wr = products_df.nlargest(1, 'Win Rate (%)').iloc[0]
worst_wr = products_df.nsmallest(1, 'Win Rate (%)').iloc[0]

col1, col2 = st.columns(2)

with col1:
    st.success(f"""
    ✅ **Melhor Win Rate:** {best_wr['Produto']} ({best_wr['Win Rate (%)']:.1f}%)
    
    Ticket Médio: ${best_wr['Ticket Médio ($)']:,.0f}  
    Deals em Engaging: {best_wr['Deals (Engaging)']}
    """)

with col2:
    st.error(f"""
    ⚠️ **Menor Win Rate:** {worst_wr['Produto']} ({worst_wr['Win Rate (%)']:.1f}%)
    
    Ticket Médio: ${worst_wr['Ticket Médio ($)']:,.0f}  
    Deals em Engaging: {worst_wr['Deals (Engaging)']}
    """)

st.divider()

# =============================================================================
# TEMPO DE CICLO
# =============================================================================
st.subheader("⏱️ Tempo de Ciclo: Engaging vs Won")

# Comparação Engaging vs Won
cycle_comparison = products_df[['Produto', 'Dias Médio (Engaging)', 'Ciclo Médio Won (dias)']].copy()
cycle_comparison['Ratio'] = cycle_comparison['Dias Médio (Engaging)'] / cycle_comparison['Ciclo Médio Won (dias)']

fig = go.Figure()

fig.add_trace(go.Bar(
    name='Engaging (atual)',
    x=cycle_comparison['Produto'],
    y=cycle_comparison['Dias Médio (Engaging)'],
    marker_color='#e74c3c'
))

fig.add_trace(go.Bar(
    name='Won (histórico)',
    x=cycle_comparison['Produto'],
    y=cycle_comparison['Ciclo Médio Won (dias)'],
    marker_color='#2ecc71'
))

fig.update_layout(
    barmode='group',
    title='Tempo de Ciclo: Engaging (atual) vs Won (histórico)',
    yaxis_title='Dias',
    xaxis_title='Produto'
)

st.plotly_chart(fig, use_container_width=True)

# Produto mais travado
most_stuck = cycle_comparison.nlargest(1, 'Ratio').iloc[0]

st.warning(f"""
⚠️ **Produto Mais Travado:** {most_stuck['Produto']}

- Engaging atual: {most_stuck['Dias Médio (Engaging)']:.0f} dias
- Won histórico: {most_stuck['Ciclo Médio Won (dias)']:.0f} dias
- **Ratio: {most_stuck['Ratio']:.1f}× mais lento**

Isso indica que deals deste produto em Engaging estão demorando muito mais que o normal para fechar.
""")

st.divider()

# =============================================================================
# ESPECIALISTAS POR PRODUTO
# =============================================================================
st.subheader("🎯 Especialistas por Produto")

# Identificar especialistas
specialists_data = []

for combo_key, combo_wr in benchmarks['product_seller_wr'].items():
    product, seller = combo_key.split('|')
    seller_avg = benchmarks['seller_wr'].get(seller, benchmarks['global_wr'])
    delta = combo_wr - seller_avg
    
    if delta > 5:  # Especialista
        specialists_data.append({
            'Produto': product,
            'Vendedor': seller,
            'WR Combinação': combo_wr,
            'WR Vendedor': seller_avg,
            'Delta': delta
        })

if specialists_data:
    specialists_df = pd.DataFrame(specialists_data).sort_values('Delta', ascending=False)
    
    # Agrupar por produto
    selected_product = st.selectbox(
        "Selecione um produto para ver especialistas:",
        ['Todos'] + sorted(products_df['Produto'].tolist())
    )
    
    if selected_product != 'Todos':
        specialists_df = specialists_df[specialists_df['Produto'] == selected_product]
    
    st.dataframe(
        specialists_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'WR Combinação': st.column_config.NumberColumn('WR Esp.', format="%.1f%%"),
            'WR Vendedor': st.column_config.NumberColumn('WR Médio', format="%.1f%%"),
            'Delta': st.column_config.NumberColumn('Δ', format="+%.1f pts")
        }
    )
    
    st.caption("💡 Especialistas têm win rate neste produto pelo menos 5 pontos acima de sua média geral")
else:
    st.info("Nenhum especialista detectado (necessário ≥3 deals no produto)")

st.divider()

# =============================================================================
# DISTRIBUIÇÃO DE AÇÕES POR PRODUTO
# =============================================================================
st.subheader("🎯 Distribuição de Ações por Produto")

# Criar dados para stacked bar
action_by_product = []

for product, stats in product_stats.items():
    total = stats['deals_engaging']
    
    for action, count in stats['actions'].items():
        action_by_product.append({
            'Produto': product,
            'Ação': action,
            'Quantidade': count,
            'Percentual': (count / total * 100)
        })

actions_df = pd.DataFrame(action_by_product)

# Pivot para gráfico
actions_pivot = actions_df.pivot(index='Produto', columns='Ação', values='Quantidade').fillna(0)

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
    title='Distribuição de Ações por Produto',
    xaxis_title='Produto',
    yaxis_title='Número de Deals'
)

st.plotly_chart(fig, use_container_width=True)

# Produto com mais DISCARD
product_discard = products_df.nlargest(1, 'DISCARD (%)').iloc[0]

if product_discard['DISCARD (%)'] > 30:
    st.error(f"""
    ⚠️ **Atenção: {product_discard['Produto']} tem {product_discard['DISCARD (%)']:.1f}% de DISCARD**
    
    Isso pode indicar:
    - Problemas de fit (produto não adequado para perfil de clientes)
    - Qualificação ruim (deals entrando sem fit adequado)
    - Pricing inadequado
    
    **Ação recomendada:** Revisar critérios de qualificação para este produto.
    """)

st.divider()

# =============================================================================
# DRILL-DOWN POR PRODUTO
# =============================================================================
st.subheader("🔍 Drill-Down por Produto")

selected_product_detail = st.selectbox(
    "Selecione um produto para análise detalhada:",
    products_df['Produto'].tolist()
)

# Filtrar deals do produto
product_deals = [r for r in results if r['deal_info']['product'] == selected_product_detail]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Deals em Engaging", len(product_deals))

with col2:
    avg_score = sum(d['score'] for d in product_deals) / len(product_deals)
    st.metric("Score Médio", f"{avg_score:.1f}")

with col3:
    product_wr = benchmarks['product_wr'].get(selected_product_detail, 0)
    global_wr = benchmarks['global_wr']
    st.metric("Win Rate", f"{product_wr:.1f}%", delta=f"{product_wr - global_wr:+.1f} pts")

with col4:
    avg_value = sum(d['deal_info']['close_value'] for d in product_deals) / len(product_deals)
    st.metric("Ticket Médio", f"${avg_value:,.0f}")

# Tabela de deals
st.markdown("### Deals deste Produto")

deals_table = pd.DataFrame([
    {
        'Deal': f"{d['deal_info']['product']} @ {d['deal_info']['account']} ({int(d['deal_info']['days_in_pipeline'])}d)",
        'Score': d['score'],
        'Vendedor': d['deal_info']['sales_agent'],
        'Dias': int(d['deal_info']['days_in_pipeline']),
        'Valor': d['deal_info']['close_value'],
        'Ação': d['action']['type']
    }
    for d in product_deals
]).sort_values('Score', ascending=False)

st.dataframe(
    deals_table,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Score': st.column_config.NumberColumn('Score', format="%.1f"),
        'Valor': st.column_config.NumberColumn('Valor', format="$%.0f"),
        'Dias': st.column_config.NumberColumn('Dias')
    }
)