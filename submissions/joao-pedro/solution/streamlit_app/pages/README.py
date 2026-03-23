"""
README — conteúdo do repositório (README.md na raiz do projeto)
"""

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="README", page_icon="📄", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)

readme_path = Path(__file__).resolve().parent.parent.parent / "README.md"
if not readme_path.is_file():
    st.error(f"Arquivo não encontrado: `{readme_path}`")
    st.stop()

st.markdown(readme_path.read_text(encoding="utf-8"))
