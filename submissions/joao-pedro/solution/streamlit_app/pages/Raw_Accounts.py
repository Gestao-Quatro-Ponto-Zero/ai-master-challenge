"""
Raw Data — accounts.csv
"""

from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="accounts.csv", page_icon="🔑", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

st.title("🔑 accounts.csv")
st.caption("Dados brutos — ~85 contas clientes com setor, receita, funcionários e localização.")

csv_path = Path(__file__).parent.parent.parent / "data" / "metrics" / "accounts.csv"
df = pd.read_csv(csv_path)

col1, col2 = st.columns(2)
col1.metric("Linhas", f"{len(df):,}")
col2.metric("Colunas", f"{len(df.columns)}")

st.divider()
st.dataframe(df, use_container_width=True, height=600)
