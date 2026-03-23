"""
Sellers List - Cadastro de vendedores com métricas e viabilidade calculadas
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.data_loader import load_raw_data, load_benchmarks

st.set_page_config(page_title="Sellers List", page_icon="👤", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)


def calc_viability(seller: str, benchmarks: dict) -> float:
    prosp = benchmarks['seller_prospecting'].get(seller, 0)
    active = benchmarks['seller_active_deals'].get(seller, 0)

    if prosp == 0:
        prosp_factor = 0.5
    elif prosp < 10:
        prosp_factor = 0.8
    elif prosp <= 30:
        prosp_factor = 1.0
    else:
        prosp_factor = 1.3

    if active > 150:
        load_factor = 0.6
    elif active > 100:
        load_factor = 0.8
    elif active >= 40:
        load_factor = 1.0
    else:
        load_factor = 1.3

    return round(min(50 * prosp_factor * load_factor, 100), 1)


def viability_label(v: float) -> str:
    if v >= 60:
        return 'Alta'
    elif v >= 40:
        return 'Média'
    return 'Baixa'


@st.cache_data(ttl=3600)
def load_data():
    pipeline_df, accounts_df, products_df, teams_df = load_raw_data()
    benchmarks = load_benchmarks()

    df = teams_df.copy()

    # Win rate
    df['win_rate'] = df['sales_agent'].map(benchmarks['seller_wr'])

    # Métricas de carga
    df['active_deals'] = df['sales_agent'].map(benchmarks['seller_active_deals']).fillna(0).astype(int)
    df['prospecting'] = df['sales_agent'].map(benchmarks['seller_prospecting']).fillna(0).astype(int)
    df['avg_ticket'] = df['sales_agent'].map(benchmarks['seller_avg_ticket']).fillna(0)

    # Deals fechados totais
    closed_df = pipeline_df[pipeline_df['deal_stage'].isin(['Won', 'Lost'])]
    closed_counts = closed_df['sales_agent'].value_counts().rename('closed_deals')
    won_counts = pipeline_df[pipeline_df['deal_stage'] == 'Won']['sales_agent'].value_counts().rename('won_deals')

    df = df.merge(closed_counts, left_on='sales_agent', right_index=True, how='left')
    df = df.merge(won_counts, left_on='sales_agent', right_index=True, how='left')
    df['closed_deals'] = df['closed_deals'].fillna(0).astype(int)
    df['won_deals'] = df['won_deals'].fillna(0).astype(int)

    # Viabilidade
    df['viability'] = df['sales_agent'].apply(lambda s: calc_viability(s, benchmarks))
    df['viability_label'] = df['viability'].apply(viability_label)

    return df, benchmarks


df, benchmarks = load_data()

# =============================================================================
# HEADER
# =============================================================================
st.title("👤 Sellers")
st.markdown(f"**{len(df):,} vendedores** em {df['regional_office'].nunique()} regiões")

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
    regions = ['Todas'] + sorted(df['regional_office'].dropna().unique().tolist())
    selected_region = st.selectbox("Região", regions)

with col2:
    managers = ['Todos'] + sorted(df['manager'].dropna().unique().tolist())
    selected_manager = st.selectbox("Manager", managers)

with col3:
    viab_opts = ['Todas', 'Alta', 'Média', 'Baixa']
    selected_viab = st.selectbox("Viabilidade", viab_opts)

with col4:
    sort_by = st.selectbox("Ordenar por", ['Viabilidade', 'Win Rate %', 'Deals Ativos', 'Prospecting'])

# Aplicar filtros
filtered = df.copy()

if selected_region != 'Todas':
    filtered = filtered[filtered['regional_office'] == selected_region]

if selected_manager != 'Todos':
    filtered = filtered[filtered['manager'] == selected_manager]

if selected_viab != 'Todas':
    filtered = filtered[filtered['viability_label'] == selected_viab]

sort_map = {
    'Viabilidade': 'viability',
    'Win Rate %': 'win_rate',
    'Deals Ativos': 'active_deals',
    'Prospecting': 'prospecting',
}

st.info(f"📊 Mostrando **{len(filtered):,} de {len(df):,}** vendedores")

st.divider()

# =============================================================================
# TABELA
# =============================================================================
st.subheader("📊 Vendedores")

table_df = filtered[[
    'sales_agent', 'manager', 'regional_office',
    'win_rate', 'active_deals', 'prospecting',
    'avg_ticket', 'closed_deals', 'won_deals',
    'viability', 'viability_label'
]].copy()

table_df = table_df.sort_values(sort_map.get(sort_by, 'viability'), ascending=False)

table_df = table_df.rename(columns={
    'sales_agent': 'Vendedor',
    'manager': 'Manager',
    'regional_office': 'Região',
    'win_rate': 'Win Rate %',
    'active_deals': 'Deals Ativos',
    'prospecting': 'Prospecting',
    'avg_ticket': 'Ticket Médio $',
    'closed_deals': 'Fechados',
    'won_deals': 'Won',
    'viability': 'Viabilidade',
    'viability_label': 'Faixa',
})

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Win Rate %': st.column_config.ProgressColumn(
            'Win Rate %', format="%.1f%%", min_value=0, max_value=100
        ),
        'Viabilidade': st.column_config.ProgressColumn(
            'Viabilidade', format="%.0f", min_value=0, max_value=100
        ),
        'Ticket Médio $': st.column_config.NumberColumn('Ticket Médio $', format="$%,.0f"),
        'Deals Ativos': st.column_config.NumberColumn('Deals Ativos'),
        'Prospecting': st.column_config.NumberColumn('Prospecting'),
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
    file_name=f'sellers_{len(filtered)}.csv',
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
            st.metric("Vendedores", len(filtered))
        with col2:
            avg_wr = filtered['win_rate'].dropna().mean()
            st.metric("Win Rate Médio", f"{avg_wr:.1f}%")
        with col3:
            avg_viab = filtered['viability'].mean()
            st.metric("Viabilidade Média", f"{avg_viab:.1f}")
        with col4:
            n_alta = (filtered['viability_label'] == 'Alta').sum()
            n_baixa = (filtered['viability_label'] == 'Baixa').sum()
            st.metric("Alta / Baixa Viab.", f"{n_alta} / {n_baixa}")
