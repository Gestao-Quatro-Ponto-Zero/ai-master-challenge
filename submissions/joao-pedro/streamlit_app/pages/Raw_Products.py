"""
Raw Data — products.csv
"""

from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="products.csv", page_icon="🔑", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

st.title("🔑 products.csv")
st.caption("Dados brutos — 7 produtos com série e preço.")

csv_path = Path(__file__).parent.parent.parent / "data" / "metrics" / "products.csv"
df = pd.read_csv(csv_path)

col1, col2 = st.columns(2)
col1.metric("Linhas", f"{len(df):,}")
col2.metric("Colunas", f"{len(df.columns)}")

st.divider()
st.dataframe(df, use_container_width=True, height=400)
