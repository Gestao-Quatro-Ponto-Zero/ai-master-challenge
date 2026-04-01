"""
Inicialização — Como rodar todos os serviços do projeto
"""

from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Inicialização", page_icon="🚀", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

md_path = Path(__file__).parent.parent.parent / "docs" / "inicializacao.md"
st.markdown(md_path.read_text(encoding="utf-8"))
