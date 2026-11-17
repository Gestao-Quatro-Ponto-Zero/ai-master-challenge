"""
Protótipo: triagem inteligente de tickets.
Roda: python -m streamlit run app.py   (de dentro da pasta solution)
"""
import pandas as pd
import streamlit as st

import triagem

st.set_page_config(page_title="Triagem de Tickets com IA", layout="wide")

CATEGORIAS_PT = {
    "Access": "Acesso",
    "Administrative rights": "Permissões administrativas",
    "HR Support": "Suporte de RH",
    "Hardware": "Hardware",
    "Internal Project": "Projeto interno",
    "Miscellaneous": "Diversos",
    "Purchase": "Compras",
    "Storage": "Armazenamento",
}


def pt(categoria: str) -> str:
    br = CATEGORIAS_PT.get(categoria, categoria)
    return br if br == categoria else f"{br} ({categoria})"


def motivo_pt(motivo: str) -> str:
    for en in CATEGORIAS_PT:
        if f"({en})" in motivo:
            return motivo.replace(f"({en})", f"({pt(en)})")
    return motivo


@st.cache_resource(show_spinner="Preparando o modelo (na primeira vez leva cerca de 30 segundos)...")
def modelo():
    return triagem.carregar_modelo()


@st.cache_data
def amostra(n=200, seed=7):
    return triagem.carregar_dados().sample(n, random_state=seed)


pacote = modelo()

# ---------- Lateral: como o modelo foi testado ----------
with st.sidebar:
    st.header("Resultado do teste")
    st.caption("Teste com 9.568 chamados de TI de um dataset público (Kaggle), que o modelo nunca viu.")
    st.metric("Acerto geral", "86,6%")
    st.metric("Tickets que a IA resolve sozinha", "72%")
    st.metric("Acerto nesses tickets", "95,6%")
    st.divider()
    st.subheader("Sempre vai para um atendente")
    st.markdown(
        "- Prioridade **crítica**\n"
        "- **Dinheiro**: cobrança, reembolso, cancelamento\n"
        "- **Segurança**: fraude, vazamento, invasão\n"
        "- **Permissões administrativas** (Administrative rights)\n"
        f"- Confiança da IA **abaixo de {triagem.LIMIAR_CONFIANCA:.0%}**"
    )
    st.divider()
    st.markdown("**Próximo passo:** treinar com os tickets da própria empresa e rodar 2 semanas "
                "em paralelo com a equipe antes de ligar.")

# ---------- Topo ----------
st.title("Triagem de tickets com IA")
st.write("A IA lê o ticket, decide para qual fila ele vai e **sabe quando não deve decidir sozinha**.")

p1, p2, p3 = st.columns(3)
with p1:
    with st.container(border=True):
        st.markdown("**1. A IA lê e classifica**")
        st.caption("Identifica o assunto do ticket e o quanto tem certeza disso.")
with p2:
    with st.container(border=True):
        st.markdown("**2. As regras conferem**")
        st.caption("Dinheiro, urgência, segurança ou dúvida da IA? Vai para um atendente.")
with p3:
    with st.container(border=True):
        st.markdown("**3. O ticket é encaminhado**")
        st.caption("Direto para a fila certa, ou para triagem humana com uma sugestão.")

st.write("")
aba1, aba2 = st.tabs(["Testar um ticket", "Testar com 200 chamados"])

# ---------- Aba 1 ----------
with aba1:
    exemplos = {
        "Hardware":
            "hello my laptop screen is broken and the keyboard stopped working please send a replacement thanks",
        "Acesso":
            "hi i cannot access the shared drive folder please grant access to my user thanks",
        "Cobrança (vai para humano)":
            "i was charged twice on my invoice this month and i want a refund",
        "Ambíguo (confiança baixa)":
            "hi please help with the issue from yesterday thanks",
        "Escrever o meu": "",
    }
    col_a, col_b = st.columns([3, 1])
    with col_a:
        escolha = st.selectbox("Escolha um exemplo ou escreva o seu", list(exemplos))
    with col_b:
        prioridade_pt = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Crítica"], index=1)
    prioridade = {"Baixa": "Low", "Média": "Medium", "Alta": "High", "Crítica": "Critical"}[prioridade_pt]
    texto = st.text_area("Texto do ticket (em inglês, como no dataset de treino)",
                         value=exemplos[escolha], height=100)

    if st.button("Analisar ticket", type="primary") and texto.strip():
        r = triagem.triar(texto, prioridade=prioridade, pacote=pacote)
        automatico = r["decisao"] == "AUTOMÁTICO"

        with st.container(border=True):
            if automatico:
                st.success(f"### Resolvido pela IA\nEncaminhado direto para a fila **{pt(r['categoria'])}**.")
            else:
                st.warning(f"### Enviado para um atendente\nSugestão da IA: fila **{pt(r['categoria'])}**.")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Assunto identificado:** {pt(r['categoria'])}")
                st.markdown(f"**Certeza da IA:** {r['confianca']:.0%}")
                st.progress(min(r["confianca"], 1.0))
                st.caption(f"A IA só decide sozinha a partir de {triagem.LIMIAR_CONFIANCA:.0%}.")
            with c2:
                st.markdown("**Por que essa decisão?**")
                if automatico:
                    st.markdown("- A IA tem certeza suficiente\n- Não envolve dinheiro, urgência, "
                                "segurança nem permissões")
                else:
                    st.markdown("\n".join(f"- {motivo_pt(m).capitalize()}" for m in r["motivos_humano"]))
                outras = ", ".join(f"{pt(c)} ({p:.0%})" for c, p in r["alternativas"])
                st.caption(f"Outras possibilidades: {outras}")

        with st.expander("Ver tickets parecidos já resolvidos (contexto para o atendente)"):
            st.dataframe(
                pd.DataFrame({
                    "Ticket parecido": [s["texto"] for s in r["similares"]],
                    "Fila": [pt(s["categoria"]) for s in r["similares"]],
                    "Semelhança": [f"{s['similaridade']:.0%}" for s in r["similares"]],
                }),
                hide_index=True, width="stretch",
            )

# ---------- Aba 2 ----------
with aba2:
    st.write("Roda a triagem em **200 chamados do dataset de TI** e compara com a fila correta de cada um.")
    if st.button("Rodar teste", type="primary"):
        base = amostra()
        res = [triagem.triar(t, pacote=pacote, k_similares=1) for t in base["Document"]]
        out = pd.DataFrame({
            "Fila correta": [pt(c) for c in base["Topic_group"]],
            "Fila da IA": [pt(r["categoria"]) for r in res],
            "Certeza": [r["confianca"] for r in res],
            "Quem decidiu": ["IA" if r["decisao"] == "AUTOMÁTICO" else "Atendente" for r in res],
        })
        out["IA acertou?"] = (out["Fila correta"] == out["Fila da IA"]).map({True: "Sim", False: "Não"})
        auto = out[out["Quem decidiu"] == "IA"]
        erros_barrados = ((out["Quem decidiu"] == "Atendente") & (out["IA acertou?"] == "Não")).sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Resolvidos pela IA", f"{len(auto) / len(out):.0%}")
        m2.metric("Acerto da IA nesses", f"{(auto['IA acertou?'] == 'Sim').mean():.0%}")
        m3.metric("Erros barrados antes do cliente", int(erros_barrados),
                  help="Tickets em que a IA erraria, mas a regra de confiança mandou para um atendente.")
        st.info("Quando a IA não tem certeza, o ticket vai para um atendente. É isso que segura os erros "
                "antes de chegarem ao cliente.")
        st.caption("Esta amostra pode incluir tickets usados no treino. O número honesto de acerto está em "
                   "resultados_avaliacao.md (teste com 20% dos dados separados).")
        st.dataframe(out.assign(Certeza=out["Certeza"].map("{:.0%}".format)), hide_index=True, width="stretch")
