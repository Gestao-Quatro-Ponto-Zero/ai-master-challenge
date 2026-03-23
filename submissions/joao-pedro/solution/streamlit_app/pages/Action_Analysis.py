"""
Action Analysis - Análise detalhada da distribuição de ações recomendadas
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

st.set_page_config(page_title="Análise de Ações", page_icon="🎯", layout="wide")

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
st.title("🎯 Análise de Ações Recomendadas")
st.markdown("""
Análise detalhada da distribuição de ações, validando a tese de pipeline travado 
e identificando padrões por vendedor, produto, e tempo.
""")

st.divider()

# =============================================================================
# DISTRIBUIÇÃO GERAL
# =============================================================================
st.subheader("📊 Distribuição Geral de Ações")

# Contar ações
action_counts = {}
for r in results:
    action_type = r['action']['type']
    action_counts[action_type] = action_counts.get(action_type, 0) + 1

# Criar DataFrame ordenado
action_df = pd.DataFrame([
    {
        'Ação': action,
        'Quantidade': count,
        'Percentual': (count / len(results)) * 100,
        '%_str': f"{(count/len(results)*100):.1f}%"
    }
    for action, count in action_counts.items()
]).sort_values('Quantidade', ascending=False)

col1, col2 = st.columns([1, 1])

with col1:
    st.dataframe(
        action_df[['Ação', 'Quantidade', '%_str']],
        use_container_width=True,
        hide_index=True,
        column_config={
            '%_str': st.column_config.TextColumn('Percentual')
        }
    )

with col2:
    # Gráfico de barras horizontal
    fig = px.bar(
        action_df,
        y='Ação',
        x='Quantidade',
        orientation='h',
        title='Distribuição de Ações',
        color='Quantidade',
        color_continuous_scale='RdYlGn_r',
        text='%_str'
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# =============================================================================
# VALIDAÇÃO DA TESE
# =============================================================================
st.subheader("💡 Validação da Tese: Pipeline Travado")

discard_count = action_counts.get('DISCARD', 0)
discard_pct = (discard_count / len(results)) * 100

monitor_count = action_counts.get('MONITOR', 0)
monitor_pct = (monitor_count / len(results)) * 100

transfer_count = action_counts.get('TRANSFER', 0) + action_counts.get('CONSIDER_TRANSFER', 0)
transfer_pct = (transfer_count / len(results)) * 100

push_count = action_counts.get('PUSH_HARD', 0) + action_counts.get('ACCELERATE', 0)
push_pct = (push_count / len(results)) * 100

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("❌ DISCARD", f"{discard_count}", delta=f"{discard_pct:.1f}%")

with col2:
    st.metric("🔀 TRANSFER", f"{transfer_count}", delta=f"{transfer_pct:.1f}%")

with col3:
    st.metric("🔥 AÇÃO IMEDIATA", f"{push_count}", delta=f"{push_pct:.1f}%")

with col4:
    st.metric("⏸ MONITOR", f"{monitor_count}", delta=f"{monitor_pct:.1f}%")

# Insights
if discard_pct > 25:
    st.error(f"""
    🔥 **CRÍTICO: {discard_pct:.1f}% dos deals devem ser DESCARTADOS**
    
    Isso valida a tese de **pipeline travado**:
    - Deals com baixa probabilidade (<60%) + baixa viabilidade (<40%)
    - Vendedores sem capacidade de resolver (sem prospecting + alta carga)
    - Melhor descartar e liberar atenção para deals viáveis
    
    **Ação recomendada:** Revisar processo de qualificação para evitar deals ruins entrarem no pipeline.
    """)

if transfer_pct > 20:
    st.warning(f"""
    🔀 **{transfer_pct:.1f}% dos deals precisam de TRANSFERÊNCIA**
    
    Indica desbalanceamento de capacidade:
    - Vendedores sobrecarregados (>100 deals) + sem prospecting
    - Outros vendedores com capacidade disponível
    
    **Ação recomendada:** Redistribuir carga entre vendedores para otimizar resultados.
    """)

if push_pct < 10:
    st.info(f"""
    ⚠️ **Apenas {push_pct:.1f}% dos deals têm ação imediata (PUSH_HARD/ACCELERATE)**
    
    Isso indica que poucos vendedores têm capacidade para fechar deals críticos.
    
    **Ação recomendada:** Reduzir carga ou contratar para aumentar capacidade.
    """)

st.divider()

# =============================================================================
# AÇÕES POR VENDEDOR
# =============================================================================
st.subheader("👥 Ações por Vendedor")

# Agrupar por vendedor
seller_actions = {}

for r in results:
    seller = r['deal_info']['sales_agent']
    action = r['action']['type']
    
    if seller not in seller_actions:
        seller_actions[seller] = {'total': 0}
    
    seller_actions[seller]['total'] += 1
    seller_actions[seller][action] = seller_actions[seller].get(action, 0) + 1

# Criar DataFrame
seller_actions_data = []

for seller, actions in seller_actions.items():
    total = actions['total']
    
    row = {
        'Vendedor': seller,
        'Total Deals': total,
        'DISCARD': actions.get('DISCARD', 0),
        'DISCARD%': (actions.get('DISCARD', 0) / total * 100),
        'TRANSFER': actions.get('TRANSFER', 0) + actions.get('CONSIDER_TRANSFER', 0),
        'TRANSFER%': ((actions.get('TRANSFER', 0) + actions.get('CONSIDER_TRANSFER', 0)) / total * 100),
        'PUSH': actions.get('PUSH_HARD', 0) + actions.get('ACCELERATE', 0),
        'PUSH%': ((actions.get('PUSH_HARD', 0) + actions.get('ACCELERATE', 0)) / total * 100),
        'MONITOR': actions.get('MONITOR', 0),
        'MONITOR%': (actions.get('MONITOR', 0) / total * 100),
        'Prospecting': benchmarks['seller_prospecting'].get(seller, 0),
        'Carga': benchmarks['seller_active_deals'].get(seller, 0)
    }
    
    seller_actions_data.append(row)

seller_actions_df = pd.DataFrame(seller_actions_data).sort_values('DISCARD%', ascending=False)

st.markdown("### Top 10 Vendedores com Mais DISCARD (%)")

top_discard = seller_actions_df.head(10)

st.dataframe(
    top_discard[['Vendedor', 'Total Deals', 'DISCARD', 'DISCARD%', 'Prospecting', 'Carga']],
    use_container_width=True,
    hide_index=True,
    column_config={
        'DISCARD%': st.column_config.NumberColumn('DISCARD %', format="%.1f%%")
    }
)

st.caption("💡 Vendedores com alto % de DISCARD geralmente têm 0 prospecting + alta carga")

# Gráfico scatter: Prospecting vs % DISCARD
fig = px.scatter(
    seller_actions_df,
    x='Prospecting',
    y='DISCARD%',
    size='Total Deals',
    color='Carga',
    hover_name='Vendedor',
    title='Prospecting vs % DISCARD',
    labels={'Prospecting': 'Prospecting (novos deals)', 'DISCARD%': '% de Deals para DISCARD'},
    color_continuous_scale='RdYlGn_r'
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# =============================================================================
# AÇÕES POR PRODUTO
# =============================================================================
st.subheader("📦 Ações por Produto")

# Agrupar por produto
product_actions = {}

for r in results:
    product = r['deal_info']['product']
    action = r['action']['type']
    
    if product not in product_actions:
        product_actions[product] = {'total': 0}
    
    product_actions[product]['total'] += 1
    product_actions[product][action] = product_actions[product].get(action, 0) + 1

# Criar DataFrame
product_actions_data = []

for product, actions in product_actions.items():
    total = actions['total']
    
    row = {
        'Produto': product,
        'Total Deals': total,
        'DISCARD': actions.get('DISCARD', 0),
        'DISCARD%': (actions.get('DISCARD', 0) / total * 100),
        'TRANSFER': actions.get('TRANSFER', 0) + actions.get('CONSIDER_TRANSFER', 0),
        'PUSH': actions.get('PUSH_HARD', 0) + actions.get('ACCELERATE', 0),
        'MONITOR': actions.get('MONITOR', 0),
        'Win Rate': benchmarks['product_wr'].get(product, 0)
    }
    
    product_actions_data.append(row)

product_actions_df = pd.DataFrame(product_actions_data).sort_values('DISCARD%', ascending=False)

col1, col2 = st.columns([1, 1])

with col1:
    st.dataframe(
        product_actions_df[['Produto', 'Total Deals', 'DISCARD', 'DISCARD%', 'Win Rate']],
        use_container_width=True,
        hide_index=True,
        column_config={
            'DISCARD%': st.column_config.NumberColumn('DISCARD %', format="%.1f%%"),
            'Win Rate': st.column_config.NumberColumn('Win Rate', format="%.1f%%")
        }
    )

with col2:
    # Gráfico de barras empilhadas
    fig = go.Figure(data=[
        go.Bar(name='DISCARD', y=product_actions_df['Produto'], x=product_actions_df['DISCARD'], orientation='h', marker_color='#e74c3c'),
        go.Bar(name='TRANSFER', y=product_actions_df['Produto'], x=product_actions_df['TRANSFER'], orientation='h', marker_color='#3498db'),
        go.Bar(name='PUSH', y=product_actions_df['Produto'], x=product_actions_df['PUSH'], orientation='h', marker_color='#2ecc71'),
        go.Bar(name='MONITOR', y=product_actions_df['Produto'], x=product_actions_df['MONITOR'], orientation='h', marker_color='#95a5a6')
    ])
    
    fig.update_layout(barmode='stack', title='Distribuição de Ações por Produto')
    st.plotly_chart(fig, use_container_width=True)

st.caption("💡 Produtos com alto % de DISCARD podem ter problemas de fit ou qualificação")

st.divider()

# =============================================================================
# AÇÕES POR TEMPO NO PIPELINE
# =============================================================================
st.subheader("⏱️ Ações vs Tempo no Pipeline")

# Criar buckets de tempo
time_actions = []

for r in results:
    days = r['deal_info']['days_in_pipeline']
    action = r['action']['type']
    
    if days >= 200:
        bucket = '≥200d (Frozen)'
    elif days >= 165:
        bucket = '165-199d (Congelado)'
    elif days >= 85:
        bucket = '85-164d (Atrasado)'
    elif days >= 57:
        bucket = '57-84d (Limite)'
    elif days >= 28:
        bucket = '28-56d (Normal)'
    else:
        bucket = '<28d (Recente)'
    
    time_actions.append({'Bucket': bucket, 'Ação': action, 'Dias': days})

time_actions_df = pd.DataFrame(time_actions)

# Contar por bucket e ação
time_action_counts = time_actions_df.groupby(['Bucket', 'Ação']).size().reset_index(name='Count')

# Pivot para stacked bar
time_pivot = time_action_counts.pivot(index='Bucket', columns='Ação', values='Count').fillna(0)

# Ordenar buckets
bucket_order = ['<28d (Recente)', '28-56d (Normal)', '57-84d (Limite)', '85-164d (Atrasado)', '165-199d (Congelado)', '≥200d (Frozen)']
time_pivot = time_pivot.reindex(bucket_order)

# Gráfico de barras empilhadas
fig = go.Figure()

for action in time_pivot.columns:
    fig.add_trace(go.Bar(
        name=action,
        x=time_pivot.index,
        y=time_pivot[action]
    ))

fig.update_layout(
    barmode='stack',
    title='Distribuição de Ações por Tempo no Pipeline',
    xaxis_title='Tempo no Pipeline',
    yaxis_title='Número de Deals'
)

st.plotly_chart(fig, use_container_width=True)

# Análise
st.markdown("### 💡 Insights por Tempo:")

frozen_deals = time_actions_df[time_actions_df['Bucket'] == '≥200d (Frozen)']
frozen_actions = frozen_deals['Ação'].value_counts()

st.markdown(f"""
**Deals Frozen (≥200 dias):**
- Total: {len(frozen_deals)} deals
- DISCARD: {frozen_actions.get('DISCARD', 0)} ({frozen_actions.get('DISCARD', 0)/len(frozen_deals)*100:.1f}%)
- TRANSFER: {frozen_actions.get('TRANSFER', 0) + frozen_actions.get('CONSIDER_TRANSFER', 0)}

**Conclusão:** Deals travados há muito tempo (>200d) são majoritariamente DISCARD, validando que 
tempo excessivo indica baixa probabilidade de fechamento.
""")

st.divider()

# =============================================================================
# CORRELAÇÕES
# =============================================================================
st.subheader("📊 Correlações: Capacidade × Ações")

# Criar dataset de correlação
correlation_data = []

for seller in seller_actions.keys():
    prospecting = benchmarks['seller_prospecting'].get(seller, 0)
    carga = benchmarks['seller_active_deals'].get(seller, 0)
    
    actions = seller_actions[seller]
    total = actions['total']
    
    correlation_data.append({
        'Vendedor': seller,
        'Prospecting': prospecting,
        'Carga': carga,
        '% MONITOR': (actions.get('MONITOR', 0) / total * 100),
        '% DISCARD': (actions.get('DISCARD', 0) / total * 100),
        '% TRANSFER': ((actions.get('TRANSFER', 0) + actions.get('CONSIDER_TRANSFER', 0)) / total * 100),
        '% PUSH': ((actions.get('PUSH_HARD', 0) + actions.get('ACCELERATE', 0)) / total * 100)
    })

corr_df = pd.DataFrame(correlation_data)

col1, col2 = st.columns(2)

with col1:
    # Scatter: Prospecting vs % MONITOR
    fig = px.scatter(
        corr_df,
        x='Prospecting',
        y='% MONITOR',
        title='Prospecting vs % MONITOR',
        labels={'Prospecting': 'Prospecting (novos)', '% MONITOR': '% Deals em MONITOR'},
        hover_name='Vendedor'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("💡 Mais prospecting → Mais MONITOR (pipeline saudável, sem urgência)")

with col2:
    # Scatter: Carga vs % TRANSFER
    fig = px.scatter(
        corr_df,
        x='Carga',
        y='% TRANSFER',
        title='Carga vs % TRANSFER',
        labels={'Carga': 'Deals Ativos', '% TRANSFER': '% Deals para TRANSFER'},
        hover_name='Vendedor'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("💡 Mais carga → Mais TRANSFER (sobrecarga gera necessidade de redistribuição)")