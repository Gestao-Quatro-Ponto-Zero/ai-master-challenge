"""
Limitações e Escalabilidade
"""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Limitações e Escalabilidade", page_icon="⚠️", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

md_path = Path(__file__).parent.parent.parent / "docs" / "limitacoes.md"
st.markdown(md_path.read_text(encoding="utf-8"))
