"""Model/data-download-free aggregate review entry point."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import streamlit as st
from management_ui import render_capacity, render_company, render_future, render_instructor_guide, render_overview, select_audience

st.set_page_config(page_title="Suporte · resultados e decisões", page_icon="📊", layout="wide")
st.title("Suporte · resultados e decisões")
audience = select_audience()
if audience == "company":
    st.caption("Visão Empresa · resultados de atendimento, ações propostas e capacidade")
    render_company()
else:
    st.caption("Visão Instrutor · consulta de agregados; para a demonstração completa use bash run.sh")
    guide, overview, capacity, future = st.tabs(["Guia do instrutor", "Diagnóstico e resultados", "Capacidade", "Evoluções planejadas"])
    with guide:
        render_instructor_guide(aggregate_only=True)
    with overview:
        render_overview()
    with capacity:
        render_capacity()
    with future:
        render_future()
