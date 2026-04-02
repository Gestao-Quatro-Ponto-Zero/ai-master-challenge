import streamlit as st
import pandas as pd
from model import run_engine
import os

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data")

st.set_page_config(page_title="AI Sales Prioritization Engine", layout="wide")

# =========================
# STYLE
# =========================
st.markdown("""
<style>
h1 { font-size: 28px !important; }
h2 { font-size: 22px !important; }
h3 { font-size: 18px !important; }
</style>
""", unsafe_allow_html=True)

st.title(" AI Sales Prioritization Engine")
st.caption("Priorize leads com maior probabilidade de fechamento e retorno")

# =========================
# LOAD BASE COMPLETA
# =========================
sales = pd.read_csv(os.path.join(DATA_PATH, "sales_pipeline.csv"))
accounts = pd.read_csv(os.path.join(DATA_PATH, "accounts.csv"))
products = pd.read_csv(os.path.join(DATA_PATH, "products.csv"))
teams = pd.read_csv(os.path.join(DATA_PATH, "sales_teams.csv"))

df_full = sales.merge(accounts, on="account", how="left")
df_full = df_full.merge(products, on="product", how="left")
df_full = df_full.merge(teams, on="sales_agent", how="left")

for col in ["sales_agent", "manager", "regional_office", "deal_stage", "sector", "office_location"]:
    if col in df_full.columns:
        df_full[col] = df_full[col].astype(str).str.lower().str.strip()

df_full = df_full[df_full["deal_stage"].isin(["engaging", "prospecting"])]

# =========================
# ENGINE
# =========================
df = run_engine()

# =========================
# FILTROS
# =========================
st.sidebar.header("🔎 Filtros")

sales_agents = ["Todos"] + sorted(df["sales_agent"].dropna().unique())
managers = ["Todos"] + sorted(df["manager"].dropna().unique())
regions = ["Todos"] + sorted(df["regional_office"].dropna().unique())

selected_agent = st.sidebar.selectbox("Sales Agent", sales_agents)
selected_manager = st.sidebar.selectbox("Manager", managers)
selected_region = st.sidebar.selectbox("Region", regions)

# =========================
# FILTRO BASE
# =========================
df_base = df_full.copy()

if selected_agent != "Todos":
    df_base = df_base[df_base["sales_agent"] == selected_agent]

if selected_manager != "Todos":
    df_base = df_base[df_base["manager"] == selected_manager]

if selected_region != "Todos":
    df_base = df_base[df_base["regional_office"] == selected_region]

# =========================
# FILTRO ENGINE
# =========================
df_filtered = df.copy()

if selected_agent != "Todos":
    df_filtered = df_filtered[df_filtered["sales_agent"] == selected_agent]

if selected_manager != "Todos":
    df_filtered = df_filtered[df_filtered["manager"] == selected_manager]

if selected_region != "Todos":
    df_filtered = df_filtered[df_filtered["regional_office"] == selected_region]

# =========================
# CONTEXTO
# =========================
if selected_agent != "Todos":
    st.write(f"👤 Vendedor: {selected_agent.title()}")
elif selected_manager != "Todos":
    st.write(f"👨‍💼 Gerente: {selected_manager.title()}")
elif selected_region != "Todos":
    st.write(f"🌎 Região: {selected_region.title()}")

# =========================
# TEXTO
# =========================
st.markdown("## COMO USAR ESTE RELATÓRIO")

st.markdown("""
Este ranking foi gerado a partir de análise estatística do seu histórico de vendas.  
O score combina taxa de conversão, ciclo de venda e qualidade de preço por cliente e produto.

Siga a ordem da lista para focar nos leads com maior probabilidade de fechamento e retorno.
""")

# =========================
# QUALIDADE
# =========================
st.markdown("## QUALIDADE DOS DADOS")

col1, col2, col3 = st.columns(3)
col1.metric("🔍 Leads Ativos", len(df_base))
col2.metric("✔ Completo", len(df_filtered))
col3.metric("⚠ Incompleto", len(df_base) - len(df_filtered))

# =========================
# RANK
# =========================
df_final = df_filtered.sort_values(
    by=["score", "sales_cycle"],
    ascending=[False, True]
).copy()

df_final["rank"] = range(1, len(df_final) + 1)

# =========================
# DISPLAY
# =========================
st.markdown("## 🏆 Ranking de Prioridade")

df_display = df_final.rename(columns={
    "account": "Conta",
    "product": "Produto",
    "stage": "Stage",
    "sales_cycle": "Ciclo (dias)",  # 🔥 ajuste aqui
    "sales_price": "Valor",
    "price_target": "Preço Alvo (%)",
    "win_rate": "WinRate",
    "score": "Score",
    "rank": "Rank",
    "sales_agent": "Vendedor",
    "manager": "Gerente",
    "sector": "Setor",
    "office_location": "Região"
})

# =========================
# COLUNAS BASE
# =========================
columns = [
    "Rank",
    "Conta",
    "Produto",
    "Stage",
    "Setor",
    "Região",
    "Ciclo (dias)",
    "Valor",
    "Preço Alvo (%)",
    "WinRate",
    "Score"
]

if selected_manager != "Todos":
    columns.insert(2, "Vendedor")

if selected_region != "Todos":
    columns.insert(2, "Gerente")

df_display = df_display[columns]

# =========================
# FORMATOS
# =========================
df_display["Valor"] = df_display["Valor"].apply(lambda x: f"${x:,.0f}")
df_display["Preço Alvo (%)"] = df_display["Preço Alvo (%)"].apply(lambda x: f"{x}%")
df_display["WinRate"] = df_display["WinRate"].apply(lambda x: f"{x}%")
df_display["Score"] = df_display["Score"].apply(lambda x: f"{x:.2f}")
df_display["Ciclo (dias)"] = df_display["Ciclo (dias)"].astype("Int64")  # 🔥 remove decimal

# =========================
# OUTPUT (sem índice)
# =========================
st.dataframe(
    df_display.style.background_gradient(subset=["Score"], cmap="Greens"),
    use_container_width=True,
    hide_index=True  # 🔥 remove primeira coluna
)
