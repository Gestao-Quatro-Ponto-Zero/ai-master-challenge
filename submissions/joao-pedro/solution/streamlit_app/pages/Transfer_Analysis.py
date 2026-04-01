"""
Transfer Analysis - Análise detalhada de transferências recomendadas
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

st.set_page_config(page_title="Análise de Transferências", page_icon="🔀", layout="wide")

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
st.title("🔀 Análise de Transferências")
st.markdown("""
Análise detalhada das transferências recomendadas, validando a hierarquia organizacional 
(same team → same region → other region) e identificando padrões.
""")

st.divider()

# =============================================================================
# FILTRAR TRANSFERS
# =============================================================================
transfer_results = [
    r for r in results 
    if r['action']['type'] in ['TRANSFER', 'CONSIDER_TRANSFER']
]

st.subheader(f"📊 Overview: {len(transfer_results):,} Transferências Recomendadas")

# KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    pct = (len(transfer_results) / len(results)) * 100
    st.metric("Total de Transfers", f"{len(transfer_results):,}", delta=f"{pct:.1f}% do pipeline")

with col2:
    transfer_count = len([r for r in transfer_results if r['action']['type'] == 'TRANSFER'])
    st.metric("TRANSFER (Crítico)", f"{transfer_count:,}")

with col3:
    consider_count = len([r for r in transfer_results if r['action']['type'] == 'CONSIDER_TRANSFER'])
    st.metric("CONSIDER_TRANSFER", f"{consider_count:,}")

with col4:
    avg_score = sum(r['score'] for r in transfer_results) / len(transfer_results) if transfer_results else 0
    st.metric("Score Médio", f"{avg_score:.1f}")

st.divider()

# =============================================================================
# HIERARQUIA DE TRANSFERÊNCIA
# =============================================================================
st.subheader("🏢 Hierarquia de Transferência")

st.markdown("""
O sistema respeita a hierarquia organizacional ao recomendar transferências:

1. **Same Team** (mesmo manager) → Minimiza atrito, manager já conhece o deal
2. **Same Region** (mesma região, outro time) → Proximidade geográfica/cultural
3. **Other Region** → Último recurso
""")

# Contar por hierarquia
hierarchy_counts = {'same_team': 0, 'same_region': 0, 'other_region': 0, 'escalate': 0}

for r in transfer_results:
    if 'details' in r['action'] and 'transfer_level' in r['action']['details']:
        level = r['action']['details']['transfer_level']
        hierarchy_counts[level] = hierarchy_counts.get(level, 0) + 1

# Criar DataFrame
hierarchy_df = pd.DataFrame([
    {
        'Nível': 'Same Team',
        'Quantidade': hierarchy_counts['same_team'],
        'Percentual': f"{(hierarchy_counts['same_team']/len(transfer_results)*100):.1f}%",
        'Prioridade': '1ª (Preferencial)'
    },
    {
        'Nível': 'Same Region',
        'Quantidade': hierarchy_counts['same_region'],
        'Percentual': f"{(hierarchy_counts['same_region']/len(transfer_results)*100):.1f}%",
        'Prioridade': '2ª'
    },
    {
        'Nível': 'Other Region',
        'Quantidade': hierarchy_counts['other_region'],
        'Percentual': f"{(hierarchy_counts['other_region']/len(transfer_results)*100):.1f}%",
        'Prioridade': '3ª (Último recurso)'
    },
    {
        'Nível': 'Escalate',
        'Quantidade': hierarchy_counts['escalate'],
        'Percentual': f"{(hierarchy_counts['escalate']/len(transfer_results)*100):.1f}%",
        'Prioridade': 'N/A (Nenhum disponível)'
    }
])

col1, col2 = st.columns([1, 1])

with col1:
    st.dataframe(hierarchy_df, use_container_width=True, hide_index=True)

with col2:
    # Gráfico de pizza
    fig = px.pie(
        hierarchy_df[hierarchy_df['Quantidade'] > 0],
        values='Quantidade',
        names='Nível',
        title='Distribuição por Hierarquia',
        color_discrete_sequence=['#2ecc71', '#3498db', '#e74c3c', '#95a5a6']
    )
    st.plotly_chart(fig, use_container_width=True)

# Insight
if hierarchy_counts['same_team'] > hierarchy_counts['other_region']:
    st.success(f"""
    ✅ **Boa alocação:** {hierarchy_counts['same_team']} transfers ({hierarchy_counts['same_team']/len(transfer_results)*100:.1f}%) 
    podem ser resolvidos dentro do mesmo time, minimizando atrito.
    """)
else:
    st.warning(f"""
    ⚠️ **Atenção:** Maioria dos transfers ({hierarchy_counts['other_region']}) precisa ir para outras regiões. 
    Isso pode indicar desbalanceamento de carga entre regiões.
    """)

st.divider()

# =============================================================================
# VENDEDORES: QUEM ENVIA vs QUEM RECEBE
# =============================================================================
st.subheader("👥 Vendedores: Quem Envia × Quem Recebe")

# Contar quem envia (vendedor atual)
senders = {}
receivers = {}

for r in transfer_results:
    sender = r['deal_info']['sales_agent']
    senders[sender] = senders.get(sender, 0) + 1
    
    # Pegar target (remover tags como "(same team)")
    if 'details' in r['action'] and 'target_seller' in r['action']['details']:
        receiver = r['action']['details']['target_seller']
        receivers[receiver] = receivers.get(receiver, 0) + 1

# Top 10 que mais enviam
top_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)[:10]
top_receivers = sorted(receivers.items(), key=lambda x: x[1], reverse=True)[:10]

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📤 Top 10 que Mais ENVIAM")
    
    senders_df = pd.DataFrame([
        {
            'Vendedor': seller,
            'Deals Enviados': count,
            'Viabilidade': benchmarks['seller_active_deals'].get(seller, 0),
            'Prospecting': benchmarks['seller_prospecting'].get(seller, 0)
        }
        for seller, count in top_senders
    ])
    
    st.dataframe(senders_df, use_container_width=True, hide_index=True)
    
    st.caption("💡 Vendedores que mais enviam geralmente têm baixa viabilidade (alta carga + sem prospecting)")

with col2:
    st.markdown("### 📥 Top 10 que Mais RECEBEM")
    
    receivers_df = pd.DataFrame([
        {
            'Vendedor': seller,
            'Deals Recebidos': count,
            'Carga Atual': benchmarks['seller_active_deals'].get(seller, 0),
            'Prospecting': benchmarks['seller_prospecting'].get(seller, 0)
        }
        for seller, count in top_receivers
    ])
    
    st.dataframe(receivers_df, use_container_width=True, hide_index=True)
    
    st.caption("💡 Vendedores que mais recebem têm alta viabilidade (carga leve + prospecting ativo)")

st.divider()

# =============================================================================
# IMPACTO DAS TRANSFERÊNCIAS
# =============================================================================
st.subheader("📈 Impacto Esperado das Transferências")

# Calcular impacto médio
impacts = []

for r in transfer_results:
    if 'details' in r['action']:
        details = r['action']['details']
        if 'your_context' in details and 'target_context' in details:
            your_viab = details['your_context']['viability']
            target_viab = details['target_context']['viability']
            delta = target_viab - your_viab
            
            impacts.append({
                'Deal': r['opportunity_id'],
                'Vendedor Atual': r['deal_info']['sales_agent'],
                'Target': details.get('target_seller', 'N/A'),
                'Viab Atual': your_viab,
                'Viab Target': target_viab,
                'Delta': delta,
                'Score': r['score']
            })

if impacts:
    impacts_df = pd.DataFrame(impacts)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_delta = impacts_df['Delta'].mean()
        st.metric("Δ Viabilidade Média", f"+{avg_delta:.1f}", delta="pontos")
    
    with col2:
        avg_your = impacts_df['Viab Atual'].mean()
        avg_target = impacts_df['Viab Target'].mean()
        st.metric("Viabilidade Média", f"{avg_your:.1f} → {avg_target:.1f}")
    
    with col3:
        positive_transfers = len(impacts_df[impacts_df['Delta'] > 20])
        st.metric("Transfers de Alto Impacto", f"{positive_transfers}", delta=f"+20 pts viabilidade")
    
    # Gráfico de distribuição de impacto
    fig = px.histogram(
        impacts_df,
        x='Delta',
        nbins=20,
        title='Distribuição do Impacto (Δ Viabilidade)',
        labels={'Delta': 'Δ Viabilidade (pontos)', 'count': 'Número de Transfers'},
        color_discrete_sequence=['#3498db']
    )
    fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Sem impacto")
    fig.add_vline(x=avg_delta, line_dash="dash", line_color="green", annotation_text=f"Média (+{avg_delta:.1f})")
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela com maiores impactos
    st.markdown("### 🔥 Top 10 Transfers de Maior Impacto")
    
    # Criar versão enriquecida da tabela
    top_impacts_enriched = []
    
    for _, row in impacts_df.nlargest(10, 'Delta').iterrows():
        # Encontrar o deal completo
        deal_result = next((r for r in transfer_results if r['opportunity_id'] == row['Deal']), None)
        
        if deal_result:
            icon = "🔥" if deal_result['score'] >= 80 else "⚡" if deal_result['score'] >= 60 else "✓"
            
            top_impacts_enriched.append({
                'Deal': f"{deal_result['deal_info']['product']} @ {deal_result['deal_info']['account']} ({int(deal_result['deal_info']['days_in_pipeline'])}d)",
                'De': row['Vendedor Atual'],
                'Para': row['Target'],
                'Viab Atual': row['Viab Atual'],
                'Viab Target': row['Viab Target'],
                'Δ Viab': row['Delta'],
                'Score': row['Score']
            })
    
    top_impacts_table = pd.DataFrame(top_impacts_enriched)
    
    st.dataframe(
        top_impacts_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Viab Atual': st.column_config.NumberColumn('Viab Atual', format="%.1f"),
            'Viab Target': st.column_config.NumberColumn('Viab Target', format="%.1f"),
            'Δ Viab': st.column_config.NumberColumn('Δ Viab', format="+%.1f"),
            'Score': st.column_config.NumberColumn('Score', format="%.1f")
        }
    )

st.divider()

# =============================================================================
# ANÁLISE POR RAZÃO DE TRANSFER
# =============================================================================
st.subheader("🔍 Por Que Transferir? Análise de Razões")

# Extrair razões
reasons_count = {}

for r in transfer_results:
    reason = r['action']['reason']
    
    # Classificar por palavra-chave
    if 'overloaded' in reason.lower() or 'high load' in reason.lower():
        key = 'Alta Carga'
    elif 'no new prospects' in reason.lower() or 'no pipeline growth' in reason.lower():
        key = 'Sem Prospecting'
    elif 'low capacity' in reason.lower() or 'limited capacity' in reason.lower():
        key = 'Capacidade Limitada'
    else:
        key = 'Outros'
    
    reasons_count[key] = reasons_count.get(key, 0) + 1

reasons_df = pd.DataFrame([
    {'Razão': reason, 'Quantidade': count, '%': f"{(count/len(transfer_results)*100):.1f}%"}
    for reason, count in sorted(reasons_count.items(), key=lambda x: x[1], reverse=True)
])

col1, col2 = st.columns([1, 1])

with col1:
    st.dataframe(reasons_df, use_container_width=True, hide_index=True)

with col2:
    fig = px.bar(
        reasons_df,
        x='Razão',
        y='Quantidade',
        title='Razões para Transferência',
        color='Quantidade',
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# =============================================================================
# TABELA COMPLETA DE TRANSFERS
# =============================================================================
st.subheader("📋 Lista Completa de Transferências")

transfers_table = pd.DataFrame([
    {
        'Deal ID': r['opportunity_id'],
        'Score': r['score'],
        'Tipo': r['action']['type'],
        'De': r['deal_info']['sales_agent'],
        'Para': r['action']['details'].get('target_seller', 'N/A') if 'details' in r['action'] else 'N/A',
        'Hierarquia': r['action']['details'].get('transfer_level', 'N/A') if 'details' in r['action'] else 'N/A',
        'Viab Atual': r['action']['details']['your_context']['viability'] if 'details' in r['action'] and 'your_context' in r['action']['details'] else 0,
        'Viab Target': r['action']['details']['target_context']['viability'] if 'details' in r['action'] and 'target_context' in r['action']['details'] else 0,
        'Produto': r['deal_info']['product'],
        'Dias': int(r['deal_info']['days_in_pipeline']),
        'Razão': r['action']['reason'][:80] + '...' if len(r['action']['reason']) > 80 else r['action']['reason']
    }
    for r in transfer_results
])

transfers_table = transfers_table.sort_values('Score', ascending=False)

st.dataframe(
    transfers_table,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Score': st.column_config.NumberColumn('Score', format="%.1f"),
        'Viab Atual': st.column_config.NumberColumn('Viab Atual', format="%.0f"),
        'Viab Target': st.column_config.NumberColumn('Viab Target', format="%.0f"),
        'Dias': st.column_config.NumberColumn('Dias')
    }
)

# Download CSV
csv = transfers_table.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Download Transferências (CSV)",
    data=csv,
    file_name=f'transfers_{len(transfer_results)}.csv',
    mime='text/csv'
)