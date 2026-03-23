import streamlit as st
from scoring import calculate_score

st.set_page_config(page_title="Lead Scoring IA", layout="centered")

st.title("🚀 Lead Scoring Inteligente")
st.subheader("Priorize seus leads com base em impacto real de negócio")

st.divider()

# Inputs do usuário
st.header("📋 Dados do Lead")

icp_fit = st.selectbox(
    "Fit com ICP",
    ["high", "medium", "low"]
)

pain_level = st.selectbox(
    "Nível de dor do cliente",
    ["high", "medium", "low"]
)

urgency = st.selectbox(
    "Urgência / Timing",
    ["high", "medium", "low"]
)

stage = st.selectbox(
    "Estágio do funil",
    ["discovery", "engaging", "proposal", "negotiation"]
)

has_decision_maker = st.checkbox("Tem decisor envolvido?")

last_activity_days = st.slider(
    "Dias desde última interação",
    0, 30, 3
)

st.divider()

# Botão de análise
if st.button("🔥 Calcular Prioridade"):

    deal = {
        "icp_fit": icp_fit,
        "pain_level": pain_level,
        "urgency": urgency,
        "stage": stage,
        "has_decision_maker": has_decision_maker,
        "last_activity_days": last_activity_days
    }

    result = calculate_score(deal)

    st.header("📊 Resultado")

    st.metric("Score", result["score"])
    st.metric("Prioridade", result["priority"])

    st.subheader("📌 Motivos")
    for r in result["reasons"]:
        st.write(f"- {r}")

    st.subheader("🎯 Próximas ações")
    for a in result["actions"]:
        st.write(f"- {a}")
