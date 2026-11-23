"""Etapa 3: a tela do Lead Scorer. Rode com: streamlit run app.py"""

import pandas as pd
import streamlit as st

import decisoes
from dados import DATA_REFERENCIA, carregar_dados
from score import ordenar, pontuar

st.set_page_config(page_title="Lead Scorer", page_icon="🎯", layout="wide")


@st.cache_data
def dados_base() -> pd.DataFrame:
    return carregar_dados()


def dinheiro(v: float) -> str:
    return "US$ " + f"{v:,.0f}".replace(",", ".")


# ---------- Dados + decisões já tomadas ----------
historico_decisoes = decisoes.carregar()
r = pontuar(decisoes.aplicar(dados_base(), historico_decisoes))

# ---------- Filtros ----------
st.sidebar.header("Filtros")
escritorio = st.sidebar.selectbox("Escritório", ["Todos"] + sorted(r["regional_office"].unique()))
if escritorio != "Todos":
    r = r[r["regional_office"] == escritorio]
manager = st.sidebar.selectbox("Manager", ["Todos"] + sorted(r["manager"].unique()))
if manager != "Todos":
    r = r[r["manager"] == manager]
vendedor = st.sidebar.selectbox("Vendedor", ["Todos"] + sorted(r["sales_agent"].unique()))
if vendedor != "Todos":
    r = r[r["sales_agent"] == vendedor]

st.sidebar.divider()
st.sidebar.caption(f"Decisões registradas: **{len(historico_decisoes)}**")
if len(historico_decisoes):
    with st.sidebar.expander("Ver decisões"):
        st.dataframe(historico_decisoes, hide_index=True)
    if st.sidebar.button("Desfazer todas as decisões"):
        decisoes.apagar_tudo()
        st.rerun()

# ---------- Cabeçalho ----------
quem = vendedor if vendedor != "Todos" else (manager if manager != "Todos" else "time todo")
st.title("🎯 Onde focar hoje")
st.caption(
    f"Pipeline de **{quem}** · dados até {DATA_REFERENCIA:%d/%m/%Y}, "
    "que a ferramenta trata como \"hoje\""
)

focar = ordenar(r, "Focar")
prospectar = ordenar(r, "Prospectar")
limpar = ordenar(r, "Limpar")
total_abertos = len(focar) + len(prospectar) + len(limpar)

c1, c2, c3 = st.columns(3)
c1.metric("🎯 Focar", len(focar))
c1.caption(f"{dinheiro(focar['valor_esperado'].sum())} em valor esperado")
c2.metric("🌱 Prospectar", len(prospectar))
c2.caption("ainda sem negociação")
c3.metric("🧹 Limpar", len(limpar))
c3.caption(f"{len(limpar) / max(total_abertos, 1):.0%} do pipeline aberto")



def ir_para_limpar() -> None:
    st.session_state["aba"] = "Limpar"


if total_abertos and len(limpar) / total_abertos > 0.3:
    with st.container(border=True):
        st.markdown(
            f"⚠️ **{len(limpar)} deals estão parados há mais tempo do que qualquer deal já levou "
            "para fechar neste CRM.** Eles inflam o pipeline e escondem o que está vivo."
        )
        st.button("🧹 Revisar os deals parados agora", type="primary", on_click=ir_para_limpar)

with st.expander("Como esta tela funciona"):
    st.markdown(
        """
- **🎯 Focar:** deals em negociação há até 138 dias. Ordenados por **valor esperado** = chance de fechar × preço.
- **🌱 Prospectar:** deals que ainda não entraram em negociação. Ordenados pelo valor esperado.
- **🧹 Limpar:** deals parados há mais de 138 dias, mais tempo do que **qualquer** deal fechado
  neste CRM levou. A ferramenta não decide sozinha: você confirma com o cliente.

**De onde vem a chance de fechar?** Da idade do deal. No histórico, os deals perdidos morrem cedo
(metade em até 14 dias), então quem sobrevive mais tempo tende a ganhar mais, até 138 dias.

**Por que o histórico do vendedor não entra no cálculo?** Testamos: a taxa de ganho por
vendedor × produto não previu os resultados de deals novos. Ela aparece só como informação.
"""
    )


# ---------- Listas ----------
MENSAGENS = {
    decisoes.MANTER: "✅ **{rotulo}** foi para **Focar**, com o contato confirmado hoje.",
    decisoes.ENCERRAR: "❌ **{rotulo}** foi **encerrado** e saiu do pipeline.",
    decisoes.RECOMECAR: "♻️ **{rotulo}** foi para **Prospectar**, para uma nova abordagem.",
}


def decidir(oid: str, acao: str, idade: int, rotulo: str) -> None:
    decisoes.salvar(oid, acao, idade)
    st.session_state["ultima"] = {"oid": oid, "msg": MENSAGENS[acao].format(rotulo=rotulo)}


def desfazer(oid: str) -> None:
    decisoes.remover(oid)
    st.session_state["ultima"] = None
    st.toast("Decisão desfeita: o deal voltou para Limpar.")


def cartao(d: pd.Series, posicao: int, botoes: bool) -> None:
    with st.container(border=True):
        conta = d["account"] if pd.notna(d["account"]) else "Conta não informada no CRM"
        if botoes and posicao == 1:
            st.markdown("👉 **Comece por aqui**")
        a, b, c, e = st.columns([2.4, 1.6, 0.9, 1.6])
        a.markdown(f"**#{posicao} · {conta}**  \n{d['product']} · {d['sales_agent']}")
        b.metric("Valor", dinheiro(d["valor"]))
        if pd.notna(d["probabilidade"]):
            c.metric("Chance", f"{d['probabilidade']:.0%}")
            e.metric("Valor esperado", dinheiro(d["valor_esperado"]))
        else:
            c.metric("Chance", "?")
            e.metric("Parado há", f"{int(d['idade_dias'])} dias")
        st.caption("  \n".join(f"• {m}" for m in d["explicacao"]))

        if botoes:
            oid, idade = d["opportunity_id"], int(d["idade_dias"])
            rotulo = (f"{d['account']} ({d['product']}, {d['sales_agent']})" if pd.notna(d["account"])
                      else f"O deal de {d['product']} de {d['sales_agent']}")
            b1, b2, b3 = st.columns(3)
            b1.button("✅ Manter", key=f"m_{oid}", use_container_width=True,
                      help="O cliente ainda está negociando. O deal vai para Focar.",
                      on_click=decidir, args=(oid, decisoes.MANTER, idade, rotulo))
            b2.button("❌ Encerrar", key=f"e_{oid}", use_container_width=True,
                      help="O cliente desistiu. O deal sai do pipeline.",
                      on_click=decidir, args=(oid, decisoes.ENCERRAR, idade, rotulo))
            b3.button("♻️ Recomeçar", key=f"r_{oid}", use_container_width=True,
                      help="Vale tentar de novo com uma nova proposta. O deal vai para Prospectar.",
                      on_click=decidir, args=(oid, decisoes.RECOMECAR, idade, rotulo))


def mostrar(lista: pd.DataFrame, chave: str, botoes: bool = False) -> None:
    if lista.empty:
        st.info("Nenhum deal aqui com os filtros atuais.")
        return
    qtd = st.columns(4)[0].selectbox("Mostrar", [10, 25, 50, "Todos"], key=f"qtd_{chave}")
    lista = lista if qtd == "Todos" else lista.head(qtd)
    for i, (_, d) in enumerate(lista.iterrows(), start=1):
        cartao(d, i, botoes)


# Navegação com rádio (e não abas) para o botão do aviso conseguir levar direto à lista Limpar.
# Os nomes não levam a contagem: se o texto muda a cada clique, o Streamlit perde a seleção.
icones = {"Focar": "🎯", "Prospectar": "🌱", "Limpar": "🧹"}
st.session_state.setdefault("aba", "Focar")
aba = st.radio("Lista", list(icones), key="aba", horizontal=True, label_visibility="collapsed",
               format_func=lambda x: f"{icones[x]} {x}")
st.divider()

if aba == "Focar":
    st.caption("Deals vivos, do maior para o menor valor esperado. Comece pelo topo.")
    mostrar(focar, "focar")
elif aba == "Prospectar":
    st.caption(
        "Ainda sem negociação. O CRM não registra desde quando cada prospect existe, "
        "então a ordem é pelo valor do produto."
    )
    mostrar(prospectar, "prosp")
else:
    ultima = st.session_state.get("ultima")
    if ultima:
        with st.container(border=True):
            m, u = st.columns([5, 1])
            m.success(ultima["msg"])
            u.button("↩️ Desfazer", key="desfazer", use_container_width=True,
                     on_click=desfazer, args=(ultima["oid"],))
    st.info(
        "**Como revisar:** comece pelo primeiro deal. Pergunte ao cliente se ele ainda está "
        "negociando e escolha:  \n"
        "✅ **Manter**: ainda está negociando → vai para Focar  \n"
        "❌ **Encerrar**: desistiu → sai do pipeline  \n"
        "♻️ **Recomeçar**: vale tentar de novo com uma nova proposta → vai para Prospectar  \n"
        "Ordem: maior valor primeiro; empatados, o parado há menos tempo primeiro (mais chance de salvar)."
    )
    mostrar(limpar, "limpar", botoes=True)
