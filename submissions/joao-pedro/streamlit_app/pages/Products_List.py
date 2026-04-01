"""
Products List - Catálogo de produtos com métricas calculadas do pipeline
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.data_loader import load_raw_data, load_benchmarks

st.set_page_config(page_title="Products List", page_icon="📦", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)


@st.cache_data(ttl=3600)
def load_data():
    pipeline_df, accounts_df, products_df, teams_df = load_raw_data()
    benchmarks = load_benchmarks()

    # Métricas por produto
    deal_counts = pipeline_df['product'].value_counts().rename('total_deals').rename_axis('product').reset_index()

    closed_df = pipeline_df[pipeline_df['deal_stage'].isin(['Won', 'Lost'])]
    closed_counts = closed_df['product'].value_counts().rename('closed_deals').rename_axis('product').reset_index()

    won_df = pipeline_df[pipeline_df['deal_stage'] == 'Won']
    won_counts = won_df['product'].value_counts().rename('won_deals').rename_axis('product').reset_index()
    avg_ticket = won_df.groupby('product')['close_value'].mean().rename('avg_ticket').reset_index()

    # Ciclo médio (dias) para Won — calculado direto das datas brutas
    won_dates = won_df.copy()
    won_dates['days_in_pipeline'] = (
        pd.to_datetime(won_dates['close_date']) - pd.to_datetime(won_dates['engage_date'])
    ).dt.days
    avg_cycle = won_dates.groupby('product')['days_in_pipeline'].mean().rename('avg_cycle_days').reset_index()

    df = products_df.copy()
    df = df.merge(deal_counts, on='product', how='left')
    df = df.merge(closed_counts, on='product', how='left')
    df = df.merge(won_counts, on='product', how='left')
    df = df.merge(avg_ticket, on='product', how='left')
    df = df.merge(avg_cycle, on='product', how='left')

    df['total_deals'] = df['total_deals'].fillna(0).astype(int)
    df['closed_deals'] = df['closed_deals'].fillna(0).astype(int)
    df['won_deals'] = df['won_deals'].fillna(0).astype(int)
    df['avg_ticket'] = df['avg_ticket'].fillna(0)
    df['avg_cycle_days'] = df['avg_cycle_days'].fillna(0)

    # Win rate do benchmarks (mais preciso, usa histórico completo)
    df['win_rate'] = df['product'].map(benchmarks['product_wr'])

    # Deals ativos (Engaging + Prospecting)
    active_df = pipeline_df[pipeline_df['deal_stage'].isin(['Engaging', 'Prospecting'])]
    active_counts = active_df['product'].value_counts().rename('active_deals').rename_axis('product').reset_index()
    df = df.merge(active_counts, on='product', how='left')
    df['active_deals'] = df['active_deals'].fillna(0).astype(int)

    return df


df = load_data()

# =============================================================================
# HEADER
# =============================================================================
st.title("📦 Products")
st.markdown(f"**{len(df):,} produtos** no catálogo")

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

col1, col2 = st.columns(4)[:2]

with col1:
    series_opts = ['Todas'] + sorted(df['series'].dropna().unique().tolist())
    selected_series = st.selectbox("Série", series_opts)

with col2:
    sort_by = st.selectbox("Ordenar por", ['Win Rate %', 'Deals Totais', 'Ticket Médio $', 'Deals Ativos'])

filtered = df.copy()

if selected_series != 'Todas':
    filtered = filtered[filtered['series'] == selected_series]

st.info(f"📊 Mostrando **{len(filtered):,} de {len(df):,}** produtos")

st.divider()

# =============================================================================
# TABELA
# =============================================================================
st.subheader("📊 Produtos")

sort_map = {
    'Win Rate %': 'win_rate',
    'Deals Totais': 'total_deals',
    'Ticket Médio $': 'avg_ticket',
    'Deals Ativos': 'active_deals',
}

table_df = filtered[[
    'product', 'series', 'sales_price',
    'active_deals', 'total_deals', 'won_deals', 'win_rate',
    'avg_ticket', 'avg_cycle_days'
]].copy()

table_df = table_df.sort_values(sort_map.get(sort_by, 'win_rate'), ascending=False)

table_df = table_df.rename(columns={
    'product': 'Produto',
    'series': 'Série',
    'sales_price': 'Preço Catálogo $',
    'active_deals': 'Deals Ativos',
    'total_deals': 'Deals Totais',
    'won_deals': 'Won',
    'win_rate': 'Win Rate %',
    'avg_ticket': 'Ticket Médio $',
    'avg_cycle_days': 'Ciclo Médio (dias)',
})

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Win Rate %': st.column_config.ProgressColumn(
            'Win Rate %', format="%.1f%%", min_value=0, max_value=100
        ),
        'Preço Catálogo $': st.column_config.NumberColumn('Preço Catálogo $', format="$%,.0f"),
        'Ticket Médio $': st.column_config.NumberColumn('Ticket Médio $', format="$%,.0f"),
        'Ciclo Médio (dias)': st.column_config.NumberColumn('Ciclo Médio (dias)', format="%.0f d"),
    }
)

# =============================================================================
# DOWNLOAD
# =============================================================================
st.divider()

csv = table_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name=f'products_{len(filtered)}.csv',
    mime='text/csv'
)

# =============================================================================
# ESTATÍSTICAS (preenchido no container acima dos filtros)
# =============================================================================
if len(filtered) > 0:
    with stats_container:
        st.subheader("📈 Estatísticas")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Produtos", len(filtered))
        with col2:
            avg_wr = filtered['win_rate'].dropna().mean()
            st.metric("Win Rate Médio", f"{avg_wr:.1f}%")
        with col3:
            avg_tk = filtered['avg_ticket'].mean()
            st.metric("Ticket Médio Geral", f"${avg_tk:,.0f}")
        with col4:
            total_active = int(filtered['active_deals'].sum())
            st.metric("Deals Ativos Total", total_active)
