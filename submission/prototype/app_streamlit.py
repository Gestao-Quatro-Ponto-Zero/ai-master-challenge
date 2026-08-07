"""
Interface simples do protótipo (Streamlit)
Para rodar: streamlit run app_streamlit.py
"""

import streamlit as st
from ticket_ai_assistant import classify_ticket

st.set_page_config(page_title="AI Ticket Assistant", page_icon="🎫", layout="centered")

st.title("🎫 AI Ticket Assistant")
st.caption("Protótipo — Challenge 002 | Redesign de Suporte (G4)")

st.markdown("""
Este protótipo demonstra a proposta de automação:
1. Classifica o ticket
2. Calcula confiança
3. Sugere prioridade
4. Decide se deve ir para agente sênior
5. Oferece resposta sugerida quando o risco é baixo
""")

ticket_text = st.text_area(
    "Cole o texto do ticket aqui:",
    height=150,
    placeholder="Ex: My mailbox is almost full and I cannot receive new emails..."
)

if st.button("Analisar Ticket", type="primary"):
    if not ticket_text.strip():
        st.warning("Por favor, cole o texto de um ticket.")
    else:
        with st.spinner("Analisando..."):
            result = classify_ticket(ticket_text)
        
        if "error" in result:
            st.error(result["error"])
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Categoria", result["category"])
            col2.metric("Confiança", f"{result['confidence']:.1%}")
            col3.metric("Prioridade", result["suggested_priority"])
            
            st.markdown("---")
            
            if result["send_to_senior"]:
                st.error("🚨 **Enviar para agente sênior**")
            else:
                st.success("✅ Pode seguir fluxo normal / N1")
            
            if result["high_emotion_detected"]:
                st.warning("⚠️ Linguagem emocional forte detectada")
            
            st.info(f"**Regra aplicada:** {result['reasoning']}")
            
            with st.expander("Top 3 categorias (probabilidades)"):
                for cat, prob in result["top_3_categories"]:
                    st.write(f"- **{cat}**: {prob:.1%}")
            
            if result.get("suggested_response"):
                st.markdown("### Resposta sugerida")
                st.code(result["suggested_response"], language=None)
                st.caption("O agente pode aceitar, editar ou descartar esta sugestão.")
            else:
                st.markdown("### Resposta sugerida")
                st.write("_Nenhuma resposta automática recomendada para este ticket._")

st.markdown("---")
st.caption("Modelo: TF-IDF + Logistic Regression | Acurácia validação ≈ 85.3%")
