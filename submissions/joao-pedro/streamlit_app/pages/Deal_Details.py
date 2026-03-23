"""
Deal Details - Drill-down detalhado em um deal específico
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.data_loader import load_benchmarks, load_deals
from core.scoring_engine import calculate_score, explain_score

st.set_page_config(page_title="Deal Details", page_icon="🔍", layout="wide")

# Cache
@st.cache_data(ttl=3600)
def load_data():
    benchmarks = load_benchmarks()
    deals = load_deals(deal_stage='Engaging')
    return benchmarks, deals

benchmarks, deals = load_data()

# =============================================================================
# HEADER
# =============================================================================
st.title("🔍 Detalhes do Deal")

# Seletor de deal
# Criar opções descritivas
deal_options = {}
for d in deals:
    # Calcular score para ordenar
    temp_result = calculate_score(d, benchmarks)
    
    # Formato descritivo
    icon = "🔥" if temp_result['score'] >= 80 else "⚡" if temp_result['score'] >= 60 else "✓"
    label = f"{icon} [{temp_result['score']:.1f}] {d['sales_agent']} → {d['product']} @ {d['account']} ({int(d['days_in_pipeline'])}d)"
    
    deal_options[label] = d['opportunity_id']

# Ordenar por score (maior primeiro)
sorted_labels = sorted(deal_options.keys(), reverse=True)

selected_label = st.selectbox("Selecione um Deal:", sorted_labels, index=0)

# Pegar ID do deal selecionado
selected_deal_id = deal_options[selected_label]

# Encontrar deal selecionado
selected_deal = next((d for d in deals if d['opportunity_id'] == selected_deal_id), None)

if selected_deal is None:
    st.error("❌ Deal não encontrado!")
    st.stop()

# Calcular score
result = calculate_score(selected_deal, benchmarks)

st.divider()

# =============================================================================
# OVERVIEW DO DEAL
# =============================================================================
st.subheader("📊 Overview")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    score_color = "🔥" if result['score'] >= 80 else "⚡" if result['score'] >= 60 else "✓"
    st.metric(f"{score_color} Score", f"{result['score']:.1f}")

with col2:
    st.metric("Urgência", f"{result['urgency']:.1f}")

with col3:
    st.metric("Probabilidade", f"{result['probability']:.1f}%")

with col4:
    st.metric("Valor", f"{result['value']:.1f}")

with col5:
    st.metric("Viabilidade", f"{result['viability']:.1f}")

st.divider()

# =============================================================================
# INFORMAÇÕES DO DEAL
# =============================================================================
st.subheader("📋 Informações do Deal")

col1, col2 = st.columns(2)

with col1:
    info = result['deal_info']
    st.markdown(f"""
    **Deal ID:** {result['opportunity_id']}  
    **Vendedor:** {info['sales_agent']}  
    **Produto:** {info['product']}  
    **Conta:** {info['account']}  
    """)

with col2:
    st.markdown(f"""
    **Valor:** ${info['close_value']:,.0f}  
    **Dias no Pipeline:** {info['days_in_pipeline']:.0f}  
    **Estágio:** {info['deal_stage']}  
    **Região:** {selected_deal.get('regional_office', 'N/A')}
    """)

st.divider()

# =============================================================================
# AÇÃO RECOMENDADA
# =============================================================================
action = result['action']

st.subheader(f"{action['icon']} Ação Recomendada: {action['type']}")

st.info(f"""
**Mensagem:** {action['message']}

**Razão:** {action['reason']}
""")

# Detalhes da ação
if 'details' in action:
    details = action['details']
    
    # Para TRANSFER e CONSIDER_TRANSFER
    if action['type'] in ['TRANSFER', 'CONSIDER_TRANSFER']:
        st.markdown("### 🔀 Contexto da Transferência")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Sua Situação")
            your = details['your_context']
            st.markdown(f"""
            - **Viabilidade:** {your['viability']}/100 ({your['capacity_assessment']})
            - **Deals Ativos:** {your['active_deals']}
            - **Prospecting:** {your['prospecting']} novos
            """)
        
        with col2:
            st.markdown(f"#### Target: {details['target_seller']}")
            target = details['target_context']
            st.markdown(f"""
            - **Viabilidade:** {target['viability']}/100 ({target['capacity_assessment']})
            - **Deals Ativos:** {target['active_deals']}
            - **Prospecting:** {target['prospecting']} novos
            """)
        
        st.markdown("#### 💡 Por que isso ajuda:")
        for benefit in details['why_this_helps']:
            st.markdown(f"- {benefit}")
        
        if 'hierarchy_explanation' in details:
            st.markdown("#### 🏢 Hierarquia de Transferência:")
            st.markdown(f"_{details['hierarchy_explanation']}_")
        
        st.markdown(f"**Impacto Esperado:** {details['expected_impact']}")
    
    # Action steps
    if 'action_steps' in details:
        st.markdown("### 📝 Próximos Passos")
        for i, step in enumerate(details['action_steps'], 1):
            st.markdown(f"{i}. {step}")

st.divider()

# =============================================================================
# BREAKDOWN DETALHADO
# =============================================================================
st.subheader("🔬 Breakdown Detalhado do Score")

# Pesos
st.markdown("""
**Fórmula:**  
Score = 50% Urgência + 30% Probabilidade + 20% Valor  
Viabilidade = Separada (capacidade do vendedor)
""")

# Tabela de componentes
import pandas as pd

breakdown_df = pd.DataFrame([
    {'Componente': 'Urgência', 'Valor': result['urgency'], 'Peso': '50%', 'Contribuição': result['urgency'] * 0.5},
    {'Componente': 'Probabilidade', 'Valor': result['probability'], 'Peso': '30%', 'Contribuição': result['probability'] * 0.3},
    {'Componente': 'Valor', 'Valor': result['value'], 'Peso': '20%', 'Contribuição': result['value'] * 0.2},
    {'Componente': 'Viabilidade', 'Valor': result['viability'], 'Peso': 'Separado', 'Contribuição': 0}
])

st.dataframe(
    breakdown_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Valor': st.column_config.ProgressColumn(
            'Valor',
            format="%.1f",
            min_value=0,
            max_value=100
        ),
        'Contribuição': st.column_config.NumberColumn(
            'Contribuição',
            format="%.1f"
        )
    }
)

st.caption(f"**Score Final:** {result['score']:.1f} = {result['urgency'] * 0.5:.1f} + {result['probability'] * 0.3:.1f} + {result['value'] * 0.2:.1f}")

st.divider()

# =============================================================================
# CONTEXTO vs BENCHMARKS
# =============================================================================
st.subheader("📊 Comparação com Benchmarks")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### ⏱️ Tempo")
    days = info['days_in_pipeline']
    won_median = benchmarks['won_median']
    engaging_median = benchmarks['engaging_median']
    
    st.markdown(f"""
    **Este deal:** {days:.0f} dias  
    **Won mediana:** {won_median:.0f} dias  
    **Engaging mediana:** {engaging_median:.0f} dias  
    
    Relação: **{days/won_median:.1f}× Won** | **{days/engaging_median:.1f}× Engaging**
    """)

with col2:
    st.markdown("#### 🎯 Probabilidade")
    prob = result['probability']
    global_wr = benchmarks['global_wr']
    
    st.markdown(f"""
    **Este deal:** {prob:.1f}%  
    **Global:** {global_wr:.1f}%  
    
    Delta: **{prob - global_wr:+.1f} pontos**
    """)

with col3:
    st.markdown("#### 👤 Vendedor")
    seller = info['sales_agent']
    seller_wr = benchmarks['seller_wr'].get(seller, global_wr)
    seller_active = benchmarks['seller_active_deals'].get(seller, 0)
    seller_prosp = benchmarks['seller_prospecting'].get(seller, 0)
    
    st.markdown(f"""
    **Win Rate:** {seller_wr:.1f}% (global: {global_wr:.1f}%)  
    **Deals Ativos:** {seller_active}  
    **Prospecting:** {seller_prosp}  
    """)

st.divider()

# =============================================================================
# EXPLICAÇÃO TEXTUAL COMPLETA
# =============================================================================
with st.expander("📄 Ver Explicação Textual Completa"):
    explanation = explain_score(result, benchmarks)
    st.text(explanation)