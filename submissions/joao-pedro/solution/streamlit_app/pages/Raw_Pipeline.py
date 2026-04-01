"""
Raw Data — sales_pipeline.csv
"""

from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="sales_pipeline.csv", page_icon="🔑", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

st.title("🔑 sales_pipeline.csv")
st.caption("Dados brutos — ~8.800 oportunidades (tabela central do CRM).")

csv_path = Path(__file__).parent.parent.parent / "data" / "metrics" / "sales_pipeline.csv"
df = pd.read_csv(csv_path)

col1, col2 = st.columns(2)
col1.metric("Linhas", f"{len(df):,}")
col2.metric("Colunas", f"{len(df.columns)}")

st.divider()

stages = df["deal_stage"].value_counts().to_dict() if "deal_stage" in df.columns else {}
if stages:
    scols = st.columns(len(stages))
    for i, (stage, count) in enumerate(stages.items()):
        scols[i].metric(stage, f"{count:,}")
    st.divider()

st.dataframe(df, use_container_width=True, height=600)
