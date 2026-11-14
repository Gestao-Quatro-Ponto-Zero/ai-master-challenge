"""Protótipo do fluxo de suporte: conversa, painel do atendente e dashboard.

Uso: streamlit run app.py
"""
from __future__ import annotations

import json

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from config import CONVERSAS, DATASET1, LIMITE_CONFIANCA, LOTE, TRADUCOES
from conversa import ASSISTENCIA, ATENDENDO, COLETA, DETALHE, ENCERRADA, EXECUCAO, IDENTIFICACAO, RESOLVIDA, TRIAGEM, Conversa
from lote import rodar
from modelo import carregar
from registro import ORIGEM, ROBO_ANTERIOR, SITUACAO, hora_brt, literal, normalizar_busca, sem_link
from roteador import ROTULOS

st.set_page_config(page_title="Suporte com IA", page_icon=":material/support_agent:", layout="wide")

AZUL, AZUL_CLARO, AMBAR, CINZA = "#1E40AF", "#93C5FD", "#B45309", "#64748B"
COR_SITUACAO = {"Em atendimento pela IA": "blue", "Resolvida pela IA": "green", "Encaminhada à assistência técnica": "violet",
                "Reembolso ou cancelamento (time decide)": "orange",
                "Com o time (IA fora do ar)": "red", "Cliente desistiu": "gray", ROBO_ANTERIOR: "gray"}
ETAPA = {ASSISTENCIA: "Assistência técnica", ATENDENDO: "IA atendendo", RESOLVIDA: "Resolvida pela IA", EXECUCAO: "Reembolso ou cancelamento (time decide)",
         TRIAGEM: "Com o time (IA fora do ar)", ENCERRADA: "Cliente desistiu", DETALHE: "Detalhes do pedido",
         COLETA: "Coleta de contato", IDENTIFICACAO: "Identificação"}
STATUS = {"Open": "Sem resposta", "Pending Customer Response": "Aguardando o cliente", "Closed": "Fechado"}
ORDEM_STATUS = ["Sem resposta", "Aguardando o cliente", "Fechado"]
CANAL = {"Phone": "Telefone", "Chat": "Chat", "Email": "E-mail", "Social media": "Redes sociais"}
PRIORIDADE = {"Low": "Baixa", "Medium": "Média", "High": "Alta", "Critical": "Crítica"}
TIPO = {"Refund request": "Reembolso", "Cancellation request": "Cancelamento", "Billing inquiry": "Cobrança",
        "Technical issue": "Problema técnico", "Product inquiry": "Dúvida de produto"}
ORIGENS = ["Todas", "Atendimentos", "Testes"]
AJUDA_ORIGEM = ("Atendimentos: conversas feitas na página. Testes: conversas que o Claude rodou por script "
                "para validar o robô.")


def pc(x: float) -> str:
    return f"{x * 100:.1f}%".replace(".", ",")


def num(x: float) -> str:
    return f"{int(x):,}".replace(",", ".")


def dec(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def selo(situacao: str) -> str:
    return f":{COR_SITUACAO.get(situacao, 'gray')}-background[{situacao}]"


def situacao(x: dict, refeitas: set) -> str:
    """Chamada gravada antes das correções de 11/11 (sem o campo em_andamento) ou já refeita por uma chamada
    nova é do robô anterior."""
    if "em_andamento" not in x or x.get("id") in refeitas:
        return ROBO_ANTERIOR
    return SITUACAO.get(x["destino"], x["destino"])


def linha_escolhida(sel) -> int | None:
    """Linha escolhida na lista: clique em qualquer célula ou na caixa de seleção; vale o último clique."""
    if sel is None or not hasattr(sel, "selection"):
        return None
    linhas = list(sel.selection.rows)
    celulas = [c[0] if isinstance(c, (list, tuple)) else c.get("row") for c in sel.selection.get("cells", [])]
    atual = (tuple(linhas), tuple(celulas))
    antes = st.session_state.get("_selecao_antes", ((), ()))
    st.session_state["_selecao_antes"] = atual
    if celulas and (not linhas or atual[1] != antes[1]):
        return celulas[0]
    return linhas[0] if linhas else None


def por_origem(df: pd.DataFrame, escolha: str | None) -> pd.DataFrame:
    if escolha == "Atendimentos":
        return df[df["Origem"] == "Atendimento"]
    if escolha == "Testes":
        return df[df["Origem"] != "Atendimento"]
    return df


@st.cache_resource
def modelo():
    return carregar()


@st.cache_data
def lote() -> pd.DataFrame:
    df = pd.read_csv(LOTE) if LOTE.exists() else rodar()
    df["assunto"] = df["categoria_prevista"].map(ROTULOS)
    df["assunto_real"] = df["categoria_real"].map(ROTULOS)
    return df


@st.cache_data
def traducoes() -> dict:
    return json.loads(TRADUCOES.read_text()) if TRADUCOES.exists() else {}


@st.cache_data
def dataset1() -> pd.DataFrame:
    d = pd.read_csv(DATASET1)
    return pd.DataFrame({"status": d["Ticket Status"].map(STATUS), "canal": d["Ticket Channel"].map(CANAL),
                         "prioridade": d["Ticket Priority"].map(PRIORIDADE), "tipo": d["Ticket Type"].map(TIPO),
                         "nota": d["Customer Satisfaction Rating"]})


def chamadas() -> list[dict]:
    if not CONVERSAS.exists():
        return []
    return [json.loads(x) for x in CONVERSAS.read_text().splitlines() if x.strip()]


def barras(df: pd.DataFrame, cat: str, val: str, rotulo: str, fmt=pc):
    """Barras horizontais ordenadas da maior para a menor, com o valor escrito em cada barra."""
    df = df.assign(_texto=df[val].map(fmt))
    eixo = alt.Axis(format="%") if fmt is pc else alt.Axis(format="d")
    base = alt.Chart(df).encode(y=alt.Y(f"{cat}:N", sort="-x", title=None), x=alt.X(f"{val}:Q", title=rotulo, axis=eixo),
                                tooltip=[alt.Tooltip(f"{cat}:N", title="Categoria"), alt.Tooltip("_texto:N", title=rotulo)])
    graf = base.mark_bar(color=AZUL, cornerRadiusEnd=3) + base.mark_text(align="left", dx=4, color="#0F172A").encode(
        text="_texto:N")
    return graf.properties(height=alt.Step(34))


st.title("Suporte com IA")
st.caption("Protótipo do case 002 do G4: atendimento ao cliente, painel do time e indicadores da operação.")
aba_conversa, aba_painel, aba_dash = st.tabs([":material/chat: Conversa", ":material/support_agent: Painel do atendente",
                                              ":material/monitoring: Dashboard"])

# Conversa --------------------------------------------------------------------------------------
with aba_conversa:
    if "conversa" not in st.session_state:
        st.session_state.conversa = Conversa(modelo())
    c: Conversa = st.session_state.conversa
    col_chat, col_bastidor = st.columns([3, 2], gap="large")
    with col_chat:
        st.caption(("Atendimento por IA" if c.com_ia else "Atendimento sem IA") + " · a IA atende até resolver; "
                   "só reembolso e cancelamento passam para o time")
        for r in c.rodadas:
            st.chat_message("user").write(sem_link(r.cliente))
            st.chat_message("assistant").write(sem_link(r.resposta))
        if c.encerrada:
            st.success(f"Chamada **{c.id}** · {SITUACAO.get(c.destino_final, '')}",
                       icon=":material/task_alt:")
            if st.button("Nova conversa", icon=":material/add_comment:", type="primary"):
                st.session_state.conversa = Conversa(modelo())
                st.rerun()
        elif msg := st.chat_input("Escreva como cliente"):
            try:
                with st.spinner("Digitando..."):
                    c.receber(msg)
            except ValueError:
                pass
            except Exception as erro:  # noqa: BLE001
                st.error(f"Falha no atendimento ({type(erro).__name__}). Tente de novo.")
            st.rerun()
    with col_bastidor:
        st.subheader("Bastidor da decisão")
        st.caption("O que o sistema entendeu a cada mensagem. O cliente não vê esta coluna.")
        for i, r in enumerate(c.rodadas, 1):
            with st.expander(f"Mensagem {i} · {ETAPA.get(r.decisao.destino, r.decisao.destino)}",
                             expanded=i == len(c.rodadas)):
                if r.tipo == "contato":
                    st.write("Dado de contato: validado aqui e nunca enviado à IA externa.")
                elif r.tipo == "detalhe":
                    st.write("Detalhe do pedido para o time: registrado pelo sistema, sem passar pela IA externa.")
                elif r.top3:
                    st.write(f"**Texto lido pelo classificador:** {sem_link(r.resumo_en)}")
                    st.dataframe(pd.DataFrame([(ROTULOS[k], dec(v)) for k, v in r.top3],
                                              columns=["Assunto", "Confiança"]), hide_index=True)
                st.caption(r.decisao.motivo)

# Painel ----------------------------------------------------------------------------------------
with aba_painel:
    conv = chamadas()
    st.subheader("Chamadas")
    st.caption("Toda conversa vira uma chamada com ID desde a primeira mensagem. Clique numa linha da lista para ver a "
               "conversa inteira. Chamadas do robô anterior (antes das correções de 11/11, ou já refeitas) ficam com a situação "
               f"\"{ROBO_ANTERIOR}\".")
    if not conv:
        st.info("Nenhuma chamada ainda. Faça um atendimento na aba Conversa.", icon=":material/info:")
    else:
        df = pd.DataFrame([{
            "ID": x.get("id"), "Data": hora_brt(x["fim"]), "Cliente": x.get("nome") or "não informado",
            "Situação": situacao(x, {y['refaz'] for y in conv if y.get('refaz')}), "Assunto": x.get("categoria") or "",
            "Pedido": x.get("resumo_pt") or "", "Origem": ORIGEM.get(x.get("origem"), "Atendimento"),
            "_i": i} for i, x in enumerate(conv)]).iloc[::-1]
        f1, f2, f3, f4 = st.columns([1.2, 2, 2, 1.8])
        busca = f1.text_input("ID da chamada", placeholder="ex.: 44", help="Aceita ATD-00044, atd44 ou só 44")
        sit = f2.multiselect("Situação", [s for s in COR_SITUACAO if s in set(df["Situação"])], placeholder="Todas")
        ass = f3.multiselect("Assunto", sorted(x for x in df["Assunto"].unique() if x), placeholder="Todos")
        orig = f4.segmented_control("Quem gerou a chamada", ORIGENS, default="Todas", help=AJUDA_ORIGEM)
        v = por_origem(df, orig)
        if busca.strip():
            alvo = normalizar_busca(busca)
            v = df[df["ID"] == alvo]
            if v.empty:
                st.warning(f"Nenhuma chamada com o ID {alvo or busca}.", icon=":material/search_off:")
        if sit:
            v = v[v["Situação"].isin(sit)]
        if ass:
            v = v[v["Assunto"].isin(ass)]

        presentes = [s for s in COR_SITUACAO if (v["Situação"] == s).any()]
        k = st.columns(1 + max(len(presentes), 1))
        k[0].metric("Chamadas", num(len(v)))
        for col, nome in zip(k[1:], presentes):
            col.metric(nome, num((v["Situação"] == nome).sum()))

        lista, detalhe = st.columns([3, 2], gap="large")
        with lista:
            sel = st.dataframe(v.drop(columns=["_i"]), hide_index=True, width="stretch", height=560,
                               on_select="rerun", selection_mode=["single-row", "single-cell"], key="lista_chamadas",
                               column_config={"ID": st.column_config.TextColumn(width="small"),
                                              "Data": st.column_config.TextColumn(width="small"),
                                              "Pedido": st.column_config.TextColumn(width="large")})
        escolhida = None
        if len(v):
            i = linha_escolhida(sel)
            escolhida = v.iloc[i] if i is not None and i < len(v) else v.iloc[0]
        with detalhe:
            if escolhida is None:
                st.info("Nenhuma chamada com esses filtros.", icon=":material/filter_alt_off:")
            else:
                x = conv[int(escolhida["_i"])]
                st.markdown(f"**Conversa da chamada {x.get('id')}**")
                # Uma caixa nova por chamada: ao trocar de chamada, a conversa abre do começo.
                with st.container(height=420, key=f"conversa_{x.get('id')}", autoscroll=False):
                    for m in x["conversa"]:
                        st.chat_message("user").write(sem_link(m["cliente"]))
                        st.chat_message("assistant").write(sem_link(m["ia"]))
                with st.container(border=True):
                    st.markdown(f"#### {x.get('id')}  {selo(escolhida['Situação'])}")
                    st.caption(f"{hora_brt(x['fim'])} · {escolhida['Origem']} · "
                               f"{x.get('modo', 'Atendimento por IA')} · {x.get('mensagens', '')} mensagens")
                    refeita = next((y["id"] for y in conv if y.get("refaz") == x.get("id")), None)
                    if refeita:
                        st.caption(f"Conversa refeita com o robô corrigido na chamada {refeita}.")
                    if x.get("refaz"):
                        st.caption(f"Refaz a chamada {x['refaz']} com o robô corrigido.")
                    st.markdown(f"**Motivo**  \n{sem_link(x.get('motivo'))}")
                    a, b = st.columns(2)
                    a.markdown(f"**Cliente**  \n{x.get('nome') or 'não informado'}")
                    b.markdown(f"**Assunto**  \n{x.get('categoria')}")
                    a.markdown(f"**CPF**  \n{literal(x.get('cpf')) or 'não coletado'}")
                    b.markdown(f"**Telefone**  \n{literal(x.get('telefone')) or 'não coletado'}")
                    st.markdown(f"**E-mail**  \n{literal(x.get('email')) or 'não coletado'}")
                    for campo, rot in (("pedido", "Pedido"), ("valor", "Valor"), ("cep", "CEP usado"),
                                       ("assistencia", "Assistência indicada")):
                        if campo in (x.get("detalhes") or {}):
                            st.markdown(f"**{rot}**  \n{literal(x['detalhes'][campo]) or 'não informado'}")

# Dashboard -------------------------------------------------------------------------------------
with aba_dash:
    op, sim, fila_t, prot = st.tabs(["Operação hoje", "Classificador de assunto", "Assunto incerto (simulação)",
                                     "Chamadas do protótipo"])

    with op:
        d1 = dataset1()
        st.caption(f"Base: {num(len(d1))} tickets do Dataset 1, a operação de hoje, antes da IA. "
                   "Use os filtros para recortar.")
        f1, f2, f3, f4 = st.columns(4)
        canais = f1.multiselect("Canal", list(CANAL.values()), placeholder="Todos")
        prios = f2.multiselect("Prioridade", list(PRIORIDADE.values()), placeholder="Todas")
        tipos = f3.multiselect("Tipo de pedido", list(TIPO.values()), placeholder="Todos")
        grupo = f4.segmented_control("Comparar por", ["Canal", "Prioridade", "Tipo"], default="Canal") or "Canal"
        d = d1
        if canais:
            d = d[d["canal"].isin(canais)]
        if prios:
            d = d[d["prioridade"].isin(prios)]
        if tipos:
            d = d[d["tipo"].isin(tipos)]
        if d.empty:
            st.info("Nenhum ticket com esses filtros.", icon=":material/filter_alt_off:")
        else:
            notas = d["nota"].dropna()
            k = st.columns(5)
            k[0].metric("Tickets", num(len(d)))
            k[1].metric("Sem nenhuma resposta", pc((d["status"] == "Sem resposta").mean()))
            k[2].metric("Aguardando o cliente", pc((d["status"] == "Aguardando o cliente").mean()))
            k[3].metric("Fechados", pc((d["status"] == "Fechado").mean()))
            k[4].metric("Nota média (fechados)", dec(notas.mean()) if len(notas) else "sem nota")
            col = {"Canal": "canal", "Prioridade": "prioridade", "Tipo": "tipo"}[grupo]
            g1, g2 = st.columns([3, 2], gap="large")
            with g1:
                st.markdown(f"**Situação dos tickets por {grupo.lower()}**")
                t = d.groupby([col, "status"]).size().rename("n").reset_index()
                t["pct"] = t["n"] / t.groupby(col)["n"].transform("sum")
                t["rotulo"] = t["pct"].map(pc)
                t["ordem"] = t["status"].map(ORDEM_STATUS.index)
                graf = alt.Chart(t).mark_bar().encode(
                    y=alt.Y(f"{col}:N", title=None),
                    x=alt.X("pct:Q", stack="normalize", title="% dos tickets", axis=alt.Axis(format="%")),
                    color=alt.Color("status:N", sort=ORDEM_STATUS, title="Situação",
                                    scale=alt.Scale(domain=ORDEM_STATUS, range=[AMBAR, AZUL_CLARO, AZUL]),
                                    legend=alt.Legend(orient="bottom")),
                    order=alt.Order("ordem:Q"),
                    tooltip=[alt.Tooltip(f"{col}:N", title=grupo), alt.Tooltip("status:N", title="Situação"),
                             alt.Tooltip("rotulo:N", title="%"), alt.Tooltip("n:Q", title="Tickets")])
                texto = alt.Chart(t[t["status"] == "Sem resposta"]).mark_text(align="left", dx=4, color="white").encode(
                    y=alt.Y(f"{col}:N"), x=alt.value(0), text="rotulo:N")
                st.altair_chart((graf + texto).properties(height=alt.Step(40)), width="stretch")
                sem = (d["status"] == "Sem resposta").groupby(d[col]).mean()
                if len(sem) > 1:
                    st.caption(f"Sem resposta vai de {pc(sem.min())} ({sem.idxmin()}) a {pc(sem.max())} "
                               f"({sem.idxmax()}): diferença de {dec((sem.max() - sem.min()) * 100)[:-1]} pontos.")
            with g2:
                st.markdown("**Notas de satisfação (só tickets fechados)**")
                if len(notas):
                    n = notas.astype(int).value_counts(normalize=True).reindex(range(1, 6), fill_value=0)
                    tn = pd.DataFrame({"Nota": [str(i) for i in n.index], "pct": n.values})
                    tn["_t"] = tn["pct"].map(pc)
                    base = alt.Chart(tn).encode(x=alt.X("Nota:N", title="Nota", axis=alt.Axis(labelAngle=0)),
                                                y=alt.Y("pct:Q", title="% dos fechados", axis=alt.Axis(format="%")),
                                                tooltip=["Nota", alt.Tooltip("_t:N", title="%")])
                    st.altair_chart((base.mark_bar(color=AZUL, cornerRadiusEnd=3)
                                     + base.mark_text(dy=-8, color="#0F172A").encode(text="_t:N")).properties(height=260),
                                    width="stretch")
                    st.caption(f"{num(len(notas))} notas. {pc(1 - len(notas) / len(d))} dos tickets deste recorte "
                               "nunca foram avaliados.")
                else:
                    st.info("Nenhum ticket fechado neste recorte.", icon=":material/info:")

    with sim:
        lt = lote()
        st.caption(f"O classificador de assunto rodando sobre {num(len(lt))} tickets reais (Dataset 2) que ele nunca viu no "
                   "treino. Na conversa, a IA atende tudo até resolver e o assunto só marca a chamada para o painel e o "
                   "dashboard (rodada 59); aqui se mede o quanto essa marcação acerta. Mova o limite para ver a troca "
                   "entre o que sai marcado com segurança e o que fica com assunto incerto.")
        f1, f2 = st.columns([2, 3])
        lim = f1.slider("Limite de confiança", 0.50, 0.95, LIMITE_CONFIANCA, 0.05,
                        help=f"Abaixo do limite, o ticket vai para uma pessoa. Decisão atual do Jó: {dec(LIMITE_CONFIANCA)}.")
        assuntos = f2.multiselect("Assunto real do ticket", sorted(lt["assunto_real"].unique()), placeholder="Todos")
        s = lt[lt["assunto_real"].isin(assuntos)] if assuntos else lt
        auto = s[s["confianca"] >= lim]
        k = st.columns(4)
        k[0].metric("IA marca com segurança", pc(len(auto) / len(s)))
        k[1].metric("Acerto quando marca", pc(auto["acertou"].mean()) if len(auto) else "sem dado")
        k[2].metric("Assunto incerto", pc(1 - len(auto) / len(s)))
        k[3].metric("Marcados errado a cada 1.000", num(round((~auto["acertou"]).sum() / len(s) * 1000)))
        g1, g2 = st.columns(2, gap="large")
        with g1:
            st.markdown("**Quanto a IA marca com segurança e quanto acerta, por limite**")
            grade = []
            for L in np.round(np.arange(0.5, 0.96, 0.05), 2):
                a = s[s["confianca"] >= L]
                grade.append({"Limite": L, "Medida": "IA marca com segurança", "v": len(a) / len(s)})
                if len(a):
                    grade.append({"Limite": L, "Medida": "Acerto quando marca", "v": a["acertou"].mean()})
            gr = pd.DataFrame(grade)
            gr["_t"] = gr["v"].map(pc)
            linhas_g = alt.Chart(gr).mark_line(point=True).encode(
                x=alt.X("Limite:Q", scale=alt.Scale(domain=[0.5, 0.95]), title="Limite de confiança"),
                y=alt.Y("v:Q", title=None, axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0.3, 1])),
                color=alt.Color("Medida:N", scale=alt.Scale(range=[AMBAR, AZUL]), legend=alt.Legend(orient="bottom", title=None)),
                tooltip=[alt.Tooltip("Limite:Q", format=".2f"), "Medida:N", alt.Tooltip("_t:N", title="%")])
            regra = alt.Chart(pd.DataFrame({"Limite": [lim]})).mark_rule(color=CINZA, strokeDash=[4, 4]).encode(x="Limite:Q")
            st.altair_chart((linhas_g + regra).properties(height=300), width="stretch")
            st.caption("A linha tracejada é o limite escolhido no controle acima.")
        with g2:
            st.markdown(f"**% marcado com segurança por assunto, no limite {dec(lim)}**")
            pa = (s["confianca"] >= lim).groupby(s["assunto_real"]).mean().rename("pct").reset_index()
            st.altair_chart(barras(pa, "assunto_real", "pct", "% marcado com segurança"), width="stretch")

    with fila_t:
        lt = lote()
        st.caption(f"Simulação: tickets reais do Dataset 2 em que o classificador fica abaixo do limite {dec(LIMITE_CONFIANCA)}. "
                   "No fluxo atual a IA segue atendendo esses clientes normalmente; só o assunto marcado na chamada é "
                   "menos confiável. A lista mostra os 200 de menor confiança, "
                   "traduzidos do inglês.")
        tri = lt[lt["confianca"] < LIMITE_CONFIANCA]
        k = st.columns(3)
        k[0].metric("Tickets com assunto incerto", num(len(tri)))
        k[1].metric("% do total", pc(len(tri) / len(lt)))
        k[2].metric("Confiança média da IA nesses tickets", dec(tri["confianca"].mean()))
        g1, g2 = st.columns([2, 3], gap="large")
        with g1:
            st.markdown("**Assunto mais provável desses tickets**")
            st.altair_chart(barras(tri["assunto"].value_counts().rename("n").reset_index(), "assunto", "n",
                                   "Tickets", fmt=num), width="stretch")
        with g2:
            mostra = tri.sort_values("confianca").head(200).copy()
            filtro = st.multiselect("Filtrar a lista por assunto", sorted(mostra["assunto"].unique()), placeholder="Todos")
            if filtro:
                mostra = mostra[mostra["assunto"].isin(filtro)]
            trad = traducoes()
            st.dataframe(pd.DataFrame({"Ticket": mostra["texto"].map(trad).fillna("tradução pendente"),
                                       "Assunto mais provável": mostra["assunto"], "Confiança": mostra["confianca"].map(dec)}),
                         hide_index=True, width="stretch", height=420,
                         column_config={"Ticket": st.column_config.TextColumn(width="large")})

    with prot:
        conv = chamadas()
        if not conv:
            st.info("Nenhuma chamada ainda.", icon=":material/info:")
        else:
            cp = pd.DataFrame([{"Situação": situacao(x, {y['refaz'] for y in conv if y.get('refaz')}), "Assunto": x.get("categoria") or "",
                                "Origem": ORIGEM.get(x.get("origem"), "Atendimento"), "tokens": x.get("tokens") or 0}
                               for x in conv])
            st.caption("As chamadas feitas no protótipo, para acompanhar como o atendimento por IA está se saindo.")
            cp = por_origem(cp, st.segmented_control("Quem gerou a chamada", ORIGENS, default="Todas", key="origem_dash",
                                                     help=AJUDA_ORIGEM))
            if cp.empty:
                st.info("Nenhuma chamada com esse filtro.", icon=":material/filter_alt_off:")
            else:
                k = st.columns(3)
                k[0].metric("Chamadas", num(len(cp)))
                k[1].metric("Resolvidas pela IA", pc((cp["Situação"] == "Resolvida pela IA").mean()))
                k[2].metric("Tokens de IA por chamada (média)", num(cp["tokens"].mean()))
                g1, g2 = st.columns(2, gap="large")
                with g1:
                    st.markdown("**Situação das chamadas**")
                    st.altair_chart(barras(cp["Situação"].value_counts().rename("n").reset_index(), "Situação", "n",
                                           "Chamadas", fmt=num), width="stretch")
                with g2:
                    st.markdown("**Assunto das chamadas**")
                    st.altair_chart(barras(cp["Assunto"].value_counts().rename("n").reset_index(), "Assunto", "n",
                                           "Chamadas", fmt=num), width="stretch")
