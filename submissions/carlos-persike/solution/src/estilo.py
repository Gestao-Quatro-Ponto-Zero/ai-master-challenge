"""CSS do app — visual mais trabalhado que o padrão do Streamlit.
Alvo são os data-testid do Streamlit 1.62, que costumam ser estáveis entre versões
menores; se a lib for atualizada e o visual quebrar, é o primeiro lugar a checar.
"""

CSS = """
<style>
:root {
    --cor-acento: #4F8EF7;
    --cor-borda: rgba(255, 255, 255, 0.08);
    --cor-fundo-card: rgba(255, 255, 255, 0.025);
}

/* título e legenda de topo */
h1 { letter-spacing: -0.02em; }
[data-testid="stCaptionContainer"] { font-size: 0.95rem; opacity: 0.75; }

/* cards do Top 5 e qualquer container com borda */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    border: 1px solid var(--cor-borda) !important;
    background: var(--cor-fundo-card);
    padding: 0.25rem 0.25rem;
    transition: border-color 0.15s ease, transform 0.15s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(79, 142, 247, 0.45) !important;
}

/* expander "Como o placar é calculado" */
div[data-testid="stExpander"] {
    border-radius: 12px !important;
    border: 1px solid var(--cor-borda) !important;
    background: var(--cor-fundo-card);
}
div[data-testid="stExpander"] summary {
    font-weight: 600;
    font-size: 0.95rem;
}
div[data-testid="stExpander"] summary:hover {
    color: var(--cor-acento);
}

/* métricas — número mais forte, label mais discreto */
div[data-testid="stMetricValue"] {
    font-weight: 700;
    font-size: 1.5rem;
}
div[data-testid="stMetricLabel"] {
    opacity: 0.7;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

/* barra de progresso — cantos arredondados, mais fina */
div[data-testid="stProgress"] > div > div {
    border-radius: 6px !important;
    height: 8px !important;
}
div[data-testid="stProgress"] {
    margin-top: 0.15rem;
}

/* espaçamento entre seções */
h2, h3 { margin-top: 1.8rem !important; }

/* tabela — cabeçalho mais discreto */
div[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid var(--cor-borda);
}
</style>
"""
