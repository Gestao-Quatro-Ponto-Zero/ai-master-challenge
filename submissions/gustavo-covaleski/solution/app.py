import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triagem  # noqa: E402
from comum import OUT_DIR, SEED, SUBMISSAO, ler_ds2  # noqa: E402

TIPOS = ["Refund request", "Cancellation request", "Billing inquiry", "Technical issue", "Product inquiry"]
CAIXA = {"IA decide": st.success, "IA sugere": st.warning, "humano decide": st.error}

st.set_page_config(page_title="Triagem de tickets", layout="centered")
st.title("Triagem de tickets — protótipo")
st.caption("Clássico TF-IDF + LR; limiar e política escolhidos fora do conjunto de teste e confirmados nele; "
           "reembolso e cancelamento sempre com humano.")


def por_que(r: dict) -> str:
    """Explica a faixa pelo caminho real da decisão em triagem.triar."""
    if r.get("duplicado"):
        return "evento duplicado: devolvido o resultado da 1ª chamada, sem nova decisão" + (
            " (a 1ª ainda está em processamento)" if r.get("status") == "em_processamento" else "")
    motivo = r.get("motivo") or ""
    if motivo == "texto insuficiente":
        return "texto com menos de 3 palavras: vai para humano"
    if motivo.startswith("falha"):
        return f"{motivo}: fallback para humano"
    pol = triagem.carregar_politica()
    p, cat = r["p_max"], r["categoria"]
    if p >= pol["t_decide"]:
        g = f"confiança {p:.1%} ≥ limiar de IA decide ({pol['t_decide']:.1%})"
    elif p >= pol["t_sugere"]:
        g = f"confiança {p:.1%} entre os limiares ({pol['t_sugere']:.1%}–{pol['t_decide']:.1%}): IA sugere"
    else:
        g = f"confiança {p:.1%} < limiar de IA sugere ({pol['t_sugere']:.1%}): humano"
    teto = pol["por_categoria"].get(cat, "humano decide")
    partes = [g, f"teto da política para {cat}: {teto}"]
    if motivo.startswith("regra de ação"):
        partes.append(motivo.split(";")[0] + " → humano decide")
    if "possível injeção" in motivo:
        partes.append("possível injeção → humano decide")
    if r.get("modo") == "sombra":
        partes.append(f"modo sombra: a faixa real seria {r.get('faixa_sem_sombra')}, devolvido humano decide")
    return "; ".join(partes)


TRECHO = 120


@st.cache_data
def exemplos():
    # só os ids sorteados na F4, cujos trechos de até 120 caracteres já estão em docs/politica.md
    ids = pd.read_csv(OUT_DIR / "f4_exemplos_ids.csv")[["id", "rotulo"]].drop_duplicates("id")
    docs = ler_ds2().set_index("id")["Document"]
    return {f"{r.id} · {r.rotulo}": (str(docs[r.id])[:TRECHO].rstrip(), len(str(docs[r.id])) > TRECHO)
            for r in ids.itertuples()}


def carregar_exemplo():
    escolha = st.session_state.get("exemplo")
    if escolha:
        st.session_state["texto"] = exemplos()[escolha][0]


aba_ticket, aba_politica, aba_lote = st.tabs(["ticket", "Política", "lote"])

with aba_ticket:
    st.selectbox("Exemplo real (opcional)", list(exemplos()), index=None, placeholder="—", key="exemplo",
                 on_change=carregar_exemplo)
    texto = st.text_area("Texto do ticket", key="texto")
    escolha = st.session_state.get("exemplo")
    if escolha and exemplos()[escolha][1] and texto == exemplos()[escolha][0]:
        st.caption(f"{texto}… (trecho)")
    c1, c2 = st.columns(2)
    canal = c1.selectbox("Canal", ["Email", "Chat", "Phone", "Social media"])
    tipo = c2.selectbox("Tipo (DS1, opcional)", TIPOS, index=None, placeholder="—")
    event_id = st.text_input("event_id (opcional)")
    if st.button("Triar"):
        st.session_state["res"] = triagem.triar({"texto": texto, "canal": canal, "tipo_ds1": tipo,
                                                 "event_id": event_id or None})
    r = st.session_state.get("res")
    if r:
        if r.get("duplicado"):
            st.info("Evento duplicado: resultado anterior devolvido, nenhuma nova decisão registrada.")
        CAIXA.get(r["faixa"], st.error)(f"**Faixa: {r['faixa']}**")
        m1, m2 = st.columns(2)
        m1.metric("Categoria", r.get("categoria") or "—")
        m2.metric("Confiança", f"{r['p_max']:.1%}" if r.get("p_max") is not None else "—")
        st.markdown(f"**Por que esta faixa:** {por_que(r)}")
        if r.get("top2"):
            st.table(pd.DataFrame([{"categoria": t["categoria"], "probabilidade": f"{t['p']:.1%}"} for t in r["top2"]]))
        if (r.get("motivo") or "").find("termos:") >= 0:
            st.markdown("**Termos que mais pesaram:** " + r["motivo"].split("termos:")[1].strip())
        with st.expander("detalhe técnico"):
            st.json(r)
        if r.get("chave") and not r.get("duplicado"):
            correta = st.selectbox("Corrigir para…", triagem.CATEGORIAS)
            if st.button("Registrar correção"):
                if triagem.registrar_correcao(r["chave"], correta, atendente="demo"):
                    st.success("Correção registrada em runtime/correcoes.jsonl")
                else:
                    st.error("Correção não registrada (categoria inválida ou falha ao gravar).")

with aba_politica:
    tab = pd.read_csv(OUT_DIR / "f8_politica_por_categoria.csv")
    lim = json.loads((OUT_DIR / "f8_faixas.json").read_text(encoding="utf-8"))["limiares"]
    st.write(f"Limiares escolhidos com predições fora da dobra no treino: IA decide ≥ {lim['t_decide']:.0%}, "
             f"IA sugere ≥ {lim['t_sugere']:.0%}. A política implantada é a mais restritiva entre a seleção fora da dobra "
             "e a confirmação por categoria no holdout (F9; só rebaixa).")
    fmt = lambda p, li, ls: "—" if pd.isna(p) else f"{p:.1%} ({li:.1%}–{ls:.1%})"
    st.dataframe(pd.DataFrame({
        "categoria": tab["categoria_prevista"],
        "seleção fora da dobra": tab["politica"],
        "confirmação no holdout": tab["politica_confirmada_holdout"],
        "implantada": tab["politica_implantada"],
        "precisão em IA decide no holdout (IC 95%)": [fmt(p, a, b) for p, a, b in zip(tab["precisao_ia_decide"], tab["li_ia_decide"], tab["ls_ia_decide"])],
        "n no holdout": tab["n_holdout"]}), hide_index=True)

with aba_lote:
    @st.cache_data
    def lote():
        # runtime separado para a demonstração não poluir o log real
        antes = os.environ.get("TRIAGEM_RUNTIME_DIR")
        os.environ["TRIAGEM_RUNTIME_DIR"] = str(SUBMISSAO / "runtime" / "demo")
        try:
            df = ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")
            amostra = df[df["split_grupo"] == "holdout"].sample(200, random_state=SEED)
            linhas = []
            for t in amostra.itertuples():
                r = triagem.triar({"event_id": f"lote-{t.id}", "texto": t.Document})
                linhas.append({"id": t.id, "rotulo": t.Topic_group, "categoria": r.get("categoria"), "faixa": r["faixa"]})
            return pd.DataFrame(linhas)
        finally:
            if antes is None:
                os.environ.pop("TRIAGEM_RUNTIME_DIR", None)
            else:
                os.environ["TRIAGEM_RUNTIME_DIR"] = antes

    st.write("200 tickets sorteados (seed 42) do holdout por grupo, passados por `triar`.")
    if st.button("Rodar lote"):
        d = lote()
        d["acerto"] = d["categoria"] == d["rotulo"]
        ref = json.loads((OUT_DIR / "f8_faixas.json").read_text(encoding="utf-8"))["implantada"]["faixas"]
        res = d.groupby("faixa").agg(n=("id", "size"), acerto=("acerto", "mean")).reindex(["IA decide", "IA sugere", "humano decide"]).fillna(0)
        res["cobertura"] = res["n"] / len(d)
        st.dataframe(pd.DataFrame({
            "faixa": res.index, "n": res["n"].astype(int),
            "cobertura": [f"{v:.1%}" for v in res["cobertura"]], "precisão": [f"{v:.1%}" for v in res["acerto"]],
            "referência holdout, política implantada (cobertura / precisão)": [f"{ref[f]['cobertura_pct']:.1f}% / {ref[f]['precisao']:.1%}" for f in res.index]}),
            hide_index=True)
        st.bar_chart(res["cobertura"] * 100, y_label="cobertura (%)")
        with st.expander("linhas do lote"):
            st.dataframe(d, hide_index=True)
