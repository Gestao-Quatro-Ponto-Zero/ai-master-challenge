import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triagem  # noqa: E402
from comum import OUT_DIR, SEED, ler_ds2  # noqa: E402

CATEGORIAS = ["Access", "Administrative rights", "HR Support", "Hardware", "Internal Project",
              "Miscellaneous", "Purchase", "Storage"]
TIPOS = ["", "Refund request", "Cancellation request", "Billing inquiry", "Technical issue", "Product inquiry"]

st.title("Triagem de tickets — protótipo")
st.caption("Clássico TF-IDF + LR; política por categoria da F4; reembolso e cancelamento sempre com humano.")
aba_ticket, aba_lote = st.tabs(["ticket", "lote"])

with aba_ticket:
    texto = st.text_area("Texto do ticket")
    canal = st.selectbox("Canal", ["Email", "Chat", "Phone", "Social media"])
    tipo = st.selectbox("Tipo (DS1, opcional)", TIPOS)
    if st.button("Triar"):
        st.session_state["res"] = triagem.triar({"texto": texto, "canal": canal, "tipo_ds1": tipo or None})
    r = st.session_state.get("res")
    if r:
        if r.get("duplicado"):
            st.warning("Evento duplicado: resultado anterior devolvido, nenhuma nova decisão registrada.")
        st.subheader(f"Faixa: {r['faixa']}")
        st.write({"categoria": r.get("categoria"), "p_max": r.get("p_max"), "duas mais prováveis": r.get("top2"),
                  "motivo": r.get("motivo"), "modo": r.get("modo"), "erro": r.get("erro")})
        if r.get("chave"):
            correta = st.selectbox("Corrigir para…", CATEGORIAS)
            if st.button("Registrar correção"):
                triagem.registrar_correcao(r["chave"], correta, atendente="demo")
                st.success("Correção registrada em runtime/correcoes.jsonl")

with aba_lote:
    @st.cache_data
    def lote():
        df = ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")
        amostra = df[df["split_grupo"] == "holdout"].sample(200, random_state=SEED)
        linhas = []
        for t in amostra.itertuples():
            r = triagem.triar({"event_id": f"lote-{t.id}", "texto": t.Document})
            linhas.append({"id": t.id, "rotulo": t.Topic_group, "categoria": r.get("categoria"), "faixa": r["faixa"]})
        return pd.DataFrame(linhas)

    st.write("200 tickets sorteados (seed 42) do holdout por grupo, passados por `triar`.")
    if st.button("Rodar lote"):
        d = lote()
        d["acerto"] = d["categoria"] == d["rotulo"]
        resumo = d.groupby("faixa").agg(n=("id", "size"), precisao=("acerto", "mean"))
        resumo["cobertura"] = resumo["n"] / len(d)
        st.dataframe(resumo)
        st.dataframe(d)
