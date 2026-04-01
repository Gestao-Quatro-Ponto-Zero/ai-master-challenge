"""
Macro - Visão macro do sistema
"""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Macro", page_icon="📊", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

md_path = Path(__file__).parent.parent.parent / "docs" / "macro.md"
st.markdown(md_path.read_text(encoding="utf-8"))
