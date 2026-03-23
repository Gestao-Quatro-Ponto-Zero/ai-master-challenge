"""
Raw Data — sales_teams.csv
"""

from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="sales_teams.csv", page_icon="🔑", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

st.title("🔑 sales_teams.csv")
st.caption("Dados brutos — equipes de vendas (agentes, gestores e escritórios regionais).")

csv_path = Path(__file__).parent.parent.parent / "data" / "metrics" / "sales_teams.csv"
df = pd.read_csv(csv_path)

col1, col2 = st.columns(2)
col1.metric("Linhas", f"{len(df):,}")
col2.metric("Colunas", f"{len(df.columns)}")

st.divider()

if "regional_office" in df.columns:
    offices = df["regional_office"].value_counts().to_dict()
    ocols = st.columns(len(offices))
    for i, (office, count) in enumerate(offices.items()):
        ocols[i].metric(office, f"{count:,}")
    st.divider()

st.dataframe(df, use_container_width=True, height=600)
