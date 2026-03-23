"""
Accounts List - Cadastro de contas com métricas calculadas do pipeline
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.data_loader import load_raw_data, load_benchmarks

st.set_page_config(page_title="Accounts List", page_icon="🏢", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)


@st.cache_data(ttl=3600)
def load_data():
    pipeline_df, accounts_df, products_df, teams_df = load_raw_data()
    benchmarks = load_benchmarks()

    # Calcular métricas do pipeline por conta
    deal_counts = pipeline_df['account'].value_counts().rename('total_deals')

    won_df = pipeline_df[pipeline_df['deal_stage'] == 'Won']
    won_counts = won_df['account'].value_counts().rename('won_deals')
    total_value = won_df.groupby('account')['close_value'].sum().rename('total_won_value')

    # Juntar tudo
    df = accounts_df.copy()
    df = df.merge(deal_counts, left_on='account', right_index=True, how='left')
    df = df.merge(won_counts, left_on='account', right_index=True, how='left')
    df = df.merge(total_value, left_on='account', right_index=True, how='left')

    df['total_deals'] = df['total_deals'].fillna(0).astype(int)
    df['won_deals'] = df['won_deals'].fillna(0).astype(int)
    df['total_won_value'] = df['total_won_value'].fillna(0)

    # Win rate calculado (usa benchmarks para contas com >= 3 deals, senão calcula direto)
    def get_wr(account, won, total):
        if account in benchmarks['account_wr']:
            return benchmarks['account_wr'][account]
        if total >= 1:
            return round(won / total * 100, 1)
        return None

    df['win_rate'] = df.apply(
        lambda r: get_wr(r['account'], r['won_deals'], r['total_deals']), axis=1
    )

    # Flag top 20
    df['top_20'] = df['account'].isin(benchmarks['top_20_accounts'])

    return df


df = load_data()

# =============================================================================
# HEADER
# =============================================================================
st.title("🏢 Accounts")
st.markdown(f"**{len(df):,} contas** cadastradas")

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
    sectors = ['Todos'] + sorted(df['sector'].dropna().unique().tolist())
    selected_sector = st.selectbox("Setor", sectors)

with col2:
    locations = ['Todos'] + sorted(df['office_location'].dropna().unique().tolist())
    selected_location = st.selectbox("Localização", locations)

with col3:
    top20_filter = st.selectbox("Top 20 Contas", ['Todas', 'Somente Top 20', 'Excluir Top 20'])

with col4:
    min_deals = st.slider("Deals Mínimos", 0, int(df['total_deals'].max()), 0)

# Aplicar filtros
filtered = df.copy()

if selected_sector != 'Todos':
    filtered = filtered[filtered['sector'] == selected_sector]

if selected_location != 'Todos':
    filtered = filtered[filtered['office_location'] == selected_location]

if top20_filter == 'Somente Top 20':
    filtered = filtered[filtered['top_20'] == True]
elif top20_filter == 'Excluir Top 20':
    filtered = filtered[filtered['top_20'] == False]

filtered = filtered[filtered['total_deals'] >= min_deals]

st.info(f"📊 Mostrando **{len(filtered):,} de {len(df):,}** contas")

st.divider()

# =============================================================================
# TABELA
# =============================================================================
st.subheader("📊 Contas")

table_df = filtered[[
    'account', 'sector', 'office_location', 'revenue', 'employees',
    'total_deals', 'won_deals', 'win_rate', 'total_won_value', 'top_20', 'subsidiary_of'
]].copy()

table_df = table_df.rename(columns={
    'account': 'Conta',
    'sector': 'Setor',
    'office_location': 'Localização',
    'revenue': 'Receita (M$)',
    'employees': 'Funcionários',
    'total_deals': 'Deals',
    'won_deals': 'Won',
    'win_rate': 'Win Rate %',
    'total_won_value': 'Valor Won $',
    'top_20': 'Top 20',
    'subsidiary_of': 'Subsidiária de',
})

table_df = table_df.sort_values('Deals', ascending=False)

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Win Rate %': st.column_config.NumberColumn('Win Rate %', format="%.1f%%"),
        'Receita (M$)': st.column_config.NumberColumn('Receita (M$)', format="$%.1fM"),
        'Valor Won $': st.column_config.NumberColumn('Valor Won $', format="$%,.0f"),
        'Top 20': st.column_config.CheckboxColumn('Top 20'),
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
    file_name=f'accounts_{len(filtered)}.csv',
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
            st.metric("Total de Contas", len(filtered))
        with col2:
            avg_wr = filtered['win_rate'].dropna().mean()
            st.metric("Win Rate Médio", f"{avg_wr:.1f}%")
        with col3:
            total_val = filtered['total_won_value'].sum()
            st.metric("Valor Total Won", f"${total_val:,.0f}")
        with col4:
            n_sectors = filtered['sector'].nunique()
            st.metric("Setores", n_sectors)
