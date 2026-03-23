import streamlit as st

pages = {
    "": [
        st.Page("pages/Navegacao.py", title="🗺️ Navegação"),
    ],
    "🏆 Challenge": [
        st.Page("pages/Challenge.py", title="Challenge-AI-master"),
    ],
    "📄 README": [
        st.Page("pages/README.py", title="README.md"),
    ],
    "📖 Fundamentos": [
        st.Page("pages/Macro.py", title="Macro"),
        st.Page("pages/Heuristica.py", title="Heurística"),
        st.Page("pages/Score_Model.py", title="Score-model"),
        st.Page("pages/Limitacoes.py", title="Limitações e Escalabilidade"),
    ],
    "🔑 Raw Data": [
        st.Page("pages/Raw_Pipeline.py", title="sales_pipeline.csv"),
        st.Page("pages/Raw_Accounts.py", title="accounts.csv"),
        st.Page("pages/Raw_Products.py", title="products.csv"),
        st.Page("pages/Raw_Teams.py", title="sales_teams.csv"),
    ],
    "📂 Primary-Data": [
        st.Page("pages/Deal_List.py", title="Pipeline"),
        st.Page("pages/Accounts_List.py", title="Accounts"),
        st.Page("pages/Products_List.py", title="Products"),
        st.Page("pages/Sellers_List.py", title="Sellers"),
        st.Page("pages/Managers_List.py", title="Managers"),
    ],
    "📊 Analysis": [
        st.Page("pages/Deals_Analysis.py", title="Pipeline Analysis"),
        st.Page("pages/Action_Analysis.py", title="Action Analysis"),
        st.Page("pages/Products_Analysis.py", title="Products Analysis"),
        st.Page("pages/Regional_Analysis.py", title="Regional Analysis"),
        st.Page("pages/Seller_Analysis.py", title="Seller Analysis"),
        st.Page("pages/Transfer_Analysis.py", title="Transfer Analysis"),
    ],
    "⚙️ Sistema": [
        st.Page("pages/Inicializacao.py", title="Inicialização"),
        st.Page("pages/Stack.py", title="Arquitetura & Stack"),
        st.Page("pages/API.py", title="API"),
    ],
}

pg = st.navigation(pages)
pg.run()

st.sidebar.markdown(
    '<p style="font-size:0.72rem;color:rgba(255,255,255,0.35);text-align:center;margin:0;">'
    "Desenvolvido por João Pedro Testa"
    "</p>",
    unsafe_allow_html=True,
)
