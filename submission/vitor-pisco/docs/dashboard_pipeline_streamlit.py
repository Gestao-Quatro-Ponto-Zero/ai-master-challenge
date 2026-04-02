import streamlit as st
import pandas as pd

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Sales Pipeline Dashboard", layout="wide")

st.title("📊 Dashboard de Prioridade Comercial – Pipeline de Vendas")

# ==============================
# LOAD DATA
# ==============================

@st.cache_data

def load_data():
    df = pd.read_csv("sales_pipeline.csv")
    return df

try:
    df = load_data()
except:
    st.error("Coloque o arquivo sales_pipeline.csv na mesma pasta do app.")
    st.stop()


# ==============================
# PREP DATA
# ==============================

stage_summary = (
    df.groupby(["sales_agent", "deal_stage"])
    .size()
    .unstack(fill_value=0)
)

product_summary = (
    df.groupby(["sales_agent", "product"])
    .size()
    .unstack(fill_value=0)
)

summary = stage_summary.copy()

summary["TOTAL"] = summary.sum(axis=1)

# SCORE HEURÍSTICO
summary["PIPELINE_SCORE"] = (
    summary.get("Prospecting", 0) * 1.5
    + summary.get("Engaging", 0) * 2
    + summary.get("Won", 0) * 3
    - summary.get("Lost", 0) * 1
)

summary = summary.sort_values("PIPELINE_SCORE", ascending=False)


# ==============================
# SIDEBAR FILTER
# ==============================

st.sidebar.header("Filtros")

selected_agent = st.sidebar.selectbox(
    "Selecionar vendedor",
    ["Todos"] + sorted(df["sales_agent"].unique().tolist())
)


# ==============================
# MAIN DASHBOARD
# ==============================

if selected_agent == "Todos":

    st.subheader("Ranking de Prioridade Comercial")

    st.dataframe(summary)

else:

    st.subheader(f"Visão detalhada – {selected_agent}")

    agent_stage = stage_summary.loc[selected_agent]
    agent_product = product_summary.loc[selected_agent]

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Funil por estágio")
        st.bar_chart(agent_stage)

    with col2:
        st.write("### Distribuição por produto")
        st.bar_chart(agent_product)


# ==============================
# INSIGHTS AUTOMÁTICOS
# ==============================

st.divider()
st.subheader("Insights automáticos")

alerts = []

for agent, row in summary.iterrows():

    if row.get("Prospecting", 0) == 0:
        alerts.append(f"⚠️ {agent} está sem novas oportunidades em prospecção")

    if row.get("Lost", 0) > row.get("Won", 0):
        alerts.append(f"📉 {agent} tem mais perdas do que ganhos")

    if row.get("Won", 0) > 20:
        alerts.append(f"🚀 {agent} apresenta alta performance de fechamento")


for alert in alerts:
    st.write(alert)


# ==============================
# EXPORT OPTION
# ==============================

st.divider()

csv = summary.to_csv().encode("utf-8")

st.download_button(
    label="Baixar ranking em CSV",
    data=csv,
    file_name="ranking_pipeline.csv",
    mime="text/csv",
)
