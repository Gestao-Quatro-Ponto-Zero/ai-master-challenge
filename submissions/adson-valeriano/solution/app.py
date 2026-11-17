"""
Protótipo: triagem inteligente de tickets.
Roda: streamlit run submissions/adson-valeriano/solution/app.py
"""
import pandas as pd
import streamlit as st

import triagem

st.set_page_config(page_title="Triagem de Tickets com IA", page_icon="🎫", layout="wide")


@st.cache_resource(show_spinner="Carregando o modelo (na primeira vez ele é treinado, leva ~1 min)...")
def modelo():
    return triagem.carregar_modelo()


@st.cache_data
def amostra_teste(n=200, seed=7):
    df = triagem.carregar_dados()
    return df.sample(n, random_state=seed)


pacote = modelo()

st.title("Triagem de tickets com IA")
st.caption(
    f"A IA classifica e encaminha sozinha só quando tem confiança ≥ {triagem.LIMIAR_CONFIANCA:.0%} "
    "e o ticket não envolve dinheiro, urgência, segurança ou acesso privilegiado. O resto vai para um humano."
)

aba1, aba2 = st.tabs(["Testar um ticket", "Rodar em lote (dados reais)"])

with aba1:
    exemplos = {
        "Escrever o meu": "",
        "Hardware": "hello my laptop screen is broken and the keyboard stopped working please send a replacement thanks",
        "Acesso": "hi i cannot access the shared drive folder please grant access to my user thanks",
        "Cobrança (vai para humano)": "i was charged twice on my invoice this month and i want a refund",
        "Ambíguo (confiança baixa)": "hi please help with the issue from yesterday thanks",
    }
    escolha = st.selectbox("Exemplo", list(exemplos))
    texto = st.text_area("Texto do ticket", value=exemplos[escolha], height=120)
    prioridade = st.selectbox("Prioridade informada", ["Low", "Medium", "High", "Critical"], index=1)

    if st.button("Triar ticket", type="primary") and texto.strip():
        r = triagem.triar(texto, prioridade=prioridade, pacote=pacote)
        c1, c2, c3 = st.columns(3)
        c1.metric("Categoria prevista", r["categoria"])
        c2.metric("Confiança", f"{r['confianca']:.0%}")
        c3.metric("Decisão", r["decisao"])

        if r["decisao"] == "HUMANO":
            st.warning("Vai para um humano porque: " + "; ".join(r["motivos_humano"]))
        else:
            st.success(f"Encaminhado automaticamente para a fila **{r['fila_destino']}**.")

        st.write("**Outras possibilidades:** " +
                 ", ".join(f"{c} ({p:.0%})" for c, p in r["alternativas"]))

        st.subheader("Tickets parecidos já classificados")
        st.caption("Dão contexto ao atendente e ajudam a conferir a sugestão da IA.")
        st.dataframe(pd.DataFrame(r["similares"]).assign(
            similaridade=lambda x: x["similaridade"].map("{:.0%}".format)), width="stretch")

with aba2:
    st.write("Roda a triagem em tickets reais do dataset de TI e compara com a categoria verdadeira.")
    n = st.slider("Quantidade de tickets", 50, 500, 200, step=50)
    if st.button("Rodar lote"):
        amostra = amostra_teste(n)
        res = [triagem.triar(t, pacote=pacote, k_similares=1) for t in amostra["Document"]]
        out = pd.DataFrame({
            "categoria_real": amostra["Topic_group"].values,
            "categoria_prevista": [r["categoria"] for r in res],
            "confianca": [r["confianca"] for r in res],
            "decisao": [r["decisao"] for r in res],
        })
        out["acertou"] = out["categoria_real"] == out["categoria_prevista"]
        auto = out[out["decisao"] == "AUTOMÁTICO"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Decididos pela IA", f"{len(auto) / len(out):.0%}")
        c2.metric("Acerto nos automáticos", f"{auto['acertou'].mean():.0%}" if len(auto) else "-")
        c3.metric("Foram para humano", f"{(out['decisao'] == 'HUMANO').mean():.0%}")
        st.caption("Observação: estes tickets podem ter sido usados no treino; o número honesto de acerto está "
                   "em resultados_avaliacao.md (teste com 20% separados).")
        st.dataframe(out.assign(confianca=out["confianca"].map("{:.0%}".format)), width="stretch")
