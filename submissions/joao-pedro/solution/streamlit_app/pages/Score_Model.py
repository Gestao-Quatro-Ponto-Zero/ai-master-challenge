"""
Score-model - Lógica do modelo de scoring
"""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Score-model", page_icon="📐", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

md_path = Path(__file__).parent.parent.parent / "docs" / "logica.md"
st.markdown(md_path.read_text(encoding="utf-8"))
