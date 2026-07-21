"""
Demo Streamlit — Triagem e roteamento de tickets de suporte.
UI fina sobre router.py (o nucleo). Roda com:  streamlit run app.py
"""
import pandas as pd
import streamlit as st
from router import classify, load_samples, QUEUES, DEFAULT_THRESHOLD

st.set_page_config(page_title="Triagem de Tickets — IA", page_icon="🎫", layout="wide")

st.title("🎫 Triagem automática de tickets de suporte")
st.caption(
    "Classifica o ticket em 1 de 8 categorias, decide se **auto-roteia** para a fila certa "
    "ou **encaminha para um humano** conforme a confiança. Roda 100% local — modelo "
    "supervisionado, sem custo por chamada."
)

# ---- Barra lateral: o limiar de confianca (o "gate") ----
with st.sidebar:
    st.header("⚙️ Limiar de confiança")
    threshold = st.slider(
        "Auto-rotear só acima de:", min_value=0.50, max_value=0.99,
        value=DEFAULT_THRESHOLD, step=0.01,
        help="Acima do limiar → auto-roteia. Abaixo → vai para um humano.",
    )
    st.markdown(
        f"**Como ler:** quanto mais alto o limiar, mais **preciso** o auto-roteamento — "
        f"porém menos tickets são automatizados (mais vão para humano).\n\n"
        f"Padrão **{DEFAULT_THRESHOLD:.2f}** ≈ 95% de precisão nos auto-roteados "
        f"(74% de cobertura), calibrado nos dados de teste."
    )
    st.divider()
    st.caption("Em produção este limiar é um valor de *config* que o time de ops define — "
               "não um controle do agente.")

HUMAN_QUEUE = "Fila humana (baixa confiança)"
tab1, tab2 = st.tabs(["🎯 Ticket único", "📦 Lote (CSV)"])

# ============ TAB 1 — TICKET UNICO ============
with tab1:
    if "ticket_text" not in st.session_state:
        st.session_state["ticket_text"] = ""

    c_load, _ = st.columns([1, 3])
    with c_load:
        if st.button("🎲 Carregar ticket real do dataset"):
            row = load_samples().sample(1).iloc[0]
            st.session_state["ticket_text"] = str(row["Document"])
            st.session_state["loaded_text"] = str(row["Document"])
            st.session_state["loaded_label"] = str(row["Topic_group"])

    text = st.text_area("Texto do ticket", key="ticket_text", height=140,
                        placeholder="Cole aqui o texto de um ticket de suporte…")

    if st.button("Classificar", type="primary"):
        if not text.strip():
            st.session_state.pop("last_ticket", None)
            st.warning("Digite ou carregue um ticket primeiro.")
        else:
            st.session_state["last_ticket"] = text

    # Renderiza fora do bloco do botao: mover o slider re-avalia o gate AO VIVO
    last = st.session_state.get("last_ticket")
    if last:
        r = classify(last, threshold)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"📂 {r['category']}")
            st.progress(r["confidence"], text=f"Confiança: {r['confidence']*100:.0f}%")
            st.caption(f"2ª hipótese: {r['runner_up']} ({r['runner_up_confidence']*100:.0f}%)")
            if r["top_terms"]:
                st.markdown("**Por que essa categoria** (termos que mais pesaram): "
                            + "  ".join(f"`{t}`" for t in r["top_terms"]))
        with col2:
            if r["auto_route"]:
                st.success(f"✅ **Auto-roteado**\n\n→ {r['destination']}")
            else:
                st.warning(f"🧑 **Confiança baixa**\n\n→ {r['destination']}")

        if last == st.session_state.get("loaded_text"):
            true = st.session_state.get("loaded_label")
            ok = r["category"] == true
            st.caption(f"Rótulo real do dataset: **{true}** — "
                       f"{'✅ acertou' if ok else '❌ errou'} (o modelo nunca vê esse rótulo)")

# ============ TAB 2 — LOTE ============
with tab2:
    st.markdown("Classifica um lote inteiro e mostra **quanto seria automatizado vs. humano** "
                "no limiar atual — a leitura que um Diretor de Operações quer.")
    src = st.radio("Fonte dos tickets:",
                   ["Usar amostra inclusa (50 tickets reais)", "Enviar meu CSV"],
                   horizontal=True)

    df, textcol = None, "Document"
    if src.startswith("Usar"):
        df = load_samples()
    else:
        up = st.file_uploader("CSV com uma coluna de texto", type="csv")
        if up is not None:
            df = pd.read_csv(up)
            textcol = st.selectbox("Qual coluna tem o texto do ticket?", list(df.columns))

    if df is not None and st.button("Classificar lote", type="primary"):
        texts = df[textcol].fillna("").astype(str).tolist()
        results = [classify(t, threshold, with_terms=False) for t in texts]
        st.session_state["batch"] = {
            "texts": texts,
            "labels": df["Topic_group"].astype(str).tolist() if "Topic_group" in df.columns else None,
            "cats": [r["category"] for r in results],
            "confs": [r["confidence"] for r in results],
            "bundled": src.startswith("Usar"),
        }

    b = st.session_state.get("batch")
    if b:
        cats, confs = b["cats"], b["confs"]
        n = len(cats)
        autos = [c >= threshold for c in confs]           # re-avaliado no limiar atual
        auto_pct = sum(autos) / n if n else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tickets", n)
        m2.metric("Auto-roteados", f"{auto_pct*100:.0f}%")
        m3.metric("Para humano", f"{(1-auto_pct)*100:.0f}%")
        if b["labels"]:
            acc = sum(1 for c, l in zip(cats, b["labels"]) if c == l) / n
            m4.metric("Acurácia nesta amostra", f"{acc*100:.0f}%")
            nota = ("⚠️ Amostra pequena e balanceada (~7 por categoria) — infla a acurácia. "
                    if b["bundled"] else "⚠️ Acurácia calculada só nesta amostra. ")
            st.caption(nota + "Referência honesta no conjunto de teste completo "
                              "(distribuição natural): **86,5%**.")

        cA, cB = st.columns(2)
        with cA:
            st.caption("Volume por categoria prevista")
            st.bar_chart(pd.Series(cats).value_counts())
        with cB:
            st.caption("Auto-roteado vs. humano (no limiar atual)")
            st.bar_chart(pd.Series(["Auto" if a else "Humano" for a in autos]).value_counts())

        st.caption("Detalhe por ticket")
        table = pd.DataFrame({
            "ticket": [t[:90] for t in b["texts"]],
            "categoria": cats,
            "confiança %": [int(round(c * 100)) for c in confs],
            "decisão": ["auto" if a else "humano" for a in autos],
            "destino": [QUEUES[c] if a else HUMAN_QUEUE for c, a in zip(cats, autos)],
        })
        st.dataframe(table, use_container_width=True, height=340)
