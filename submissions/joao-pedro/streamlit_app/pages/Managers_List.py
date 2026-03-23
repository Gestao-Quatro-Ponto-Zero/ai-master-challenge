"""
Managers List - Visão agregada por manager com métricas dos vendedores sob gestão
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.data_loader import load_raw_data, load_benchmarks

st.set_page_config(page_title="Managers List", page_icon="👔", layout="wide")

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
    _, _, _, teams_df = load_raw_data()
    benchmarks = load_benchmarks()

    sellers = teams_df.copy()
    sellers['win_rate'] = sellers['sales_agent'].map(benchmarks['seller_wr']).fillna(0)
    sellers['active_deals'] = sellers['sales_agent'].map(benchmarks['seller_active_deals']).fillna(0)
    sellers['prospecting'] = sellers['sales_agent'].map(benchmarks['seller_prospecting']).fillna(0)
    sellers['avg_ticket'] = sellers['sales_agent'].map(benchmarks['seller_avg_ticket']).fillna(0)
    sellers['viability'] = sellers['sales_agent'].apply(lambda s: calc_viability(s, benchmarks))

    # Região do manager = primeira região encontrada para aquele manager
    region_map = sellers.groupby('manager')['regional_office'].first()

    df = sellers.groupby('manager').agg(
        n_sellers=('sales_agent', 'count'),
        avg_win_rate=('win_rate', 'mean'),
        total_active_deals=('active_deals', 'sum'),
        total_prospecting=('prospecting', 'sum'),
        avg_ticket=('avg_ticket', 'mean'),
        avg_viability=('viability', 'mean'),
    ).reset_index()

    df['avg_win_rate'] = df['avg_win_rate'].round(1)
    df['avg_viability'] = df['avg_viability'].round(1)
    df['avg_ticket'] = df['avg_ticket'].round(0)
    df['viability_label'] = df['avg_viability'].apply(viability_label)
    df = df.merge(region_map, on='manager', how='left')

    return df


df = load_data()

# =============================================================================
# HEADER
# =============================================================================
st.title("👔 Managers")
st.markdown(f"**{len(df):,} managers** em {df['regional_office'].nunique()} regiões")

st.divider()

# =============================================================================
# FILTROS
# =============================================================================
st.subheader("🔍 Filtros")

col1, col2, col3 = st.columns(3)

with col1:
    regions = ['Todas'] + sorted(df['regional_office'].dropna().unique().tolist())
    selected_region = st.selectbox("Região", regions)

with col2:
    viab_opts = ['Todas', 'Alta', 'Média', 'Baixa']
    selected_viab = st.selectbox("Viabilidade", viab_opts)

with col3:
    sort_by = st.selectbox("Ordenar por", ['Viabilidade', 'Win Rate %', 'Deals Ativos', 'Prospecting'])

# Aplicar filtros
filtered = df.copy()

if selected_region != 'Todas':
    filtered = filtered[filtered['regional_office'] == selected_region]

if selected_viab != 'Todas':
    filtered = filtered[filtered['viability_label'] == selected_viab]

sort_map = {
    'Viabilidade': 'avg_viability',
    'Win Rate %': 'avg_win_rate',
    'Deals Ativos': 'total_active_deals',
    'Prospecting': 'total_prospecting',
}

st.info(f"📊 Mostrando **{len(filtered):,} de {len(df):,}** managers")

st.divider()

# =============================================================================
# TABELA
# =============================================================================
st.subheader("📊 Managers")

table_df = filtered[[
    'manager', 'regional_office', 'n_sellers',
    'avg_win_rate', 'total_active_deals', 'total_prospecting',
    'avg_ticket', 'avg_viability', 'viability_label'
]].copy()

table_df = table_df.sort_values(sort_map.get(sort_by, 'avg_viability'), ascending=False)

table_df = table_df.rename(columns={
    'manager': 'Manager',
    'regional_office': 'Região',
    'n_sellers': 'Vendedores',
    'avg_win_rate': 'Win Rate Médio %',
    'total_active_deals': 'Deals Ativos',
    'total_prospecting': 'Prospecting',
    'avg_ticket': 'Ticket Médio $',
    'avg_viability': 'Viabilidade',
    'viability_label': 'Faixa',
})

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Win Rate Médio %': st.column_config.ProgressColumn(
            'Win Rate Médio %',
            min_value=0,
            max_value=100,
            format='%.1f%%',
        ),
        'Viabilidade': st.column_config.ProgressColumn(
            'Viabilidade',
            min_value=0,
            max_value=100,
            format='%.1f',
        ),
        'Ticket Médio $': st.column_config.NumberColumn(
            'Ticket Médio $',
            format='$%.0f',
        ),
    },
)
