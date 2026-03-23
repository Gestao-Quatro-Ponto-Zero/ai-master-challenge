"""
Deal List - Tabela completa de deals com filtros e ordenação
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.data_loader import load_benchmarks, load_deals, load_raw_data, preprocess_pipeline
from core.scoring_engine import score_all_deals

st.set_page_config(page_title="Deal List", page_icon="💰", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

# Cache
@st.cache_data(ttl=3600)
def load_data():
    benchmarks = load_benchmarks()
    pipeline_df, _, products_df, _ = load_raw_data()
    pipeline_df = preprocess_pipeline(pipeline_df, products_df)
    engaging_deals = load_deals(deal_stage='Engaging')
    scored = score_all_deals(engaging_deals, benchmarks)
    score_lookup = {r['opportunity_id']: r for r in scored}
    return benchmarks, pipeline_df, score_lookup

benchmarks, pipeline_df, score_lookup = load_data()

# =============================================================================
# HEADER
# =============================================================================
st.title("💰 Pipeline")
st.markdown(f"**{len(pipeline_df):,} deals** no pipeline")

st.divider()

# =============================================================================
# ESTATÍSTICAS (placeholder — preenchido após aplicar filtros)
# =============================================================================
stats_container = st.container()

st.divider()

# =============================================================================
# FILTROS
# =============================================================================
st.subheader("🔍 Filtros")

col1, col2, col3, col4 = st.columns(4)

with col1:
    stage_opts = ['Todos', 'Engaging', 'Won', 'Lost', 'Prospecting']
    selected_stage = st.selectbox("Stage", stage_opts)

with col2:
    sellers = ['Todos'] + sorted(pipeline_df['sales_agent'].dropna().unique().tolist())
    selected_seller = st.selectbox("Vendedor", sellers)

with col3:
    min_score = st.slider("Score Mínimo", 0, 100, 0)

with col4:
    min_days = st.slider("Dias Mínimo", 0, 300, 0)

# Aplicar filtros
filtered_df = pipeline_df.copy()

if selected_stage != 'Todos':
    filtered_df = filtered_df[filtered_df['deal_stage'] == selected_stage]

if selected_seller != 'Todos':
    filtered_df = filtered_df[filtered_df['sales_agent'] == selected_seller]

filtered_df = filtered_df[filtered_df['days_in_pipeline'] >= min_days]

# Enriquecer com scores (disponível apenas para Engaging)
rows = []
for _, row in filtered_df.iterrows():
    opp_id = row['opportunity_id']
    s = score_lookup.get(opp_id)
    record = {
        'Deal ID': opp_id,
        'Stage': row['deal_stage'],
        'Vendedor': row['sales_agent'],
        'Produto': row['product'],
        'Conta': row['account'],
        'Close Value': row['close_value'],
        'Dias': int(row['days_in_pipeline']) if pd.notna(row['days_in_pipeline']) else 0,
        'Score': s['score'] if s else None,
        'Urgência': s['urgency'] if s else None,
        'Prob': s['probability'] if s else None,
        'Valor': s['value'] if s else None,
        'Viab': s['viability'] if s else None,
        'Ação': s['action']['type'] if s else None,
    }
    rows.append(record)

deals_df = pd.DataFrame(rows) if rows else pd.DataFrame()

# Filtro de score mínimo (só aplica onde Score existe)
if min_score > 0 and len(deals_df) > 0:
    deals_df = deals_df[deals_df['Score'].fillna(0) >= min_score]

# Ordenar por Score (decrescente), não-scored vai pro final
if len(deals_df) > 0:
    deals_df = deals_df.sort_values('Score', ascending=False, na_position='last')

st.info(f"📊 Mostrando **{len(deals_df):,} de {len(pipeline_df):,}** deals")

st.divider()

# =============================================================================
# TABELA DE DEALS
# =============================================================================
st.subheader("📊 Deals")

col_order = ['Deal ID', 'Stage', 'Score', 'Urgência', 'Prob', 'Valor', 'Viab',
             'Vendedor', 'Produto', 'Conta', 'Close Value', 'Dias', 'Ação']

if len(deals_df) > 0:
    deals_df_display = deals_df[[c for c in col_order if c in deals_df.columns]]
    st.dataframe(
        deals_df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Score': st.column_config.NumberColumn('Score', format="%.1f", help="Score final (0-100)"),
            'Urgência': st.column_config.ProgressColumn('Urgência', format="%.0f", min_value=0, max_value=100),
            'Prob': st.column_config.ProgressColumn('Prob%', format="%.0f", min_value=0, max_value=100),
            'Valor': st.column_config.ProgressColumn('Valor', format="%.0f", min_value=0, max_value=100),
            'Viab': st.column_config.ProgressColumn('Viab', format="%.0f", min_value=0, max_value=100),
            'Close Value': st.column_config.NumberColumn('Valor $', format="$%d"),
            'Dias': st.column_config.NumberColumn('Dias', help="Dias no pipeline"),
        }
    )
else:
    st.warning("Nenhum deal encontrado com os filtros aplicados.")
    deals_df_display = pd.DataFrame()

# =============================================================================
# DOWNLOAD CSV
# =============================================================================
st.divider()

if len(deals_df_display) > 0:
    csv = deals_df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f'deals_filtered_{len(deals_df)}.csv',
        mime='text/csv'
    )

# =============================================================================
# ESTATÍSTICAS (preenchido no container acima dos filtros)
# =============================================================================
if len(deals_df) > 0:
    with stats_container:
        st.subheader("📈 Estatísticas")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            scored_rows = deals_df['Score'].dropna()
            avg_score_val = scored_rows.mean() if len(scored_rows) > 0 else None
            st.metric("Score Médio", f"{avg_score_val:.1f}" if avg_score_val is not None else "—")
        with col2:
            avg_days = deals_df['Dias'].mean()
            st.metric("Dias Médio", f"{avg_days:.0f}")
        with col3:
            total_value = deals_df['Close Value'].fillna(0).sum()
            st.metric("Valor Total", f"${total_value:,.0f}")
        with col4:
            prob_rows = deals_df['Prob'].dropna()
            avg_prob_val = prob_rows.mean() if len(prob_rows) > 0 else None
            st.metric("Prob. Média", f"{avg_prob_val:.1f}%" if avg_prob_val is not None else "—")
