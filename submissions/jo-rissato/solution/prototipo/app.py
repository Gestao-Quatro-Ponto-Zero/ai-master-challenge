"""Protótipo do fluxo de suporte: conversa, painel do atendente e dashboard.

Uso: streamlit run app.py
"""
from __future__ import annotations

import json

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from datetime import datetime, timezone

from config import CONVERSAS, DATASET1, LIMITE_CONFIANCA, LOTE, TRADUCOES, VERSAO_ROBO
from conversa import (ASSISTENCIA, ATENDENDO, CANAIS, COLETA, DETALHE, ENCERRADA, ESPECIALISTA, EXECUCAO,
                      IDENTIFICACAO, INCERTO, REDES, RESOLVIDA, TRIAGEM, Conversa, registrar_posicionamento)
from lote import rodar
from modelo import carregar
from registro import (CANAL_ROTULO, ORIGEM, ROBO_ANTERIOR, SITUACAO, canal_de, hora_brt, literal, normalizar_busca,
                      pendente_posicionamento, sem_link)
from roteador import ROTULOS, comando_restrito
import voz

st.set_page_config(page_title="Suporte com IA", page_icon=":material/support_agent:", layout="wide")

AZUL, AZUL_CLARO, AMBAR, CINZA = "#1E40AF", "#93C5FD", "#B45309", "#64748B"
COR_SITUACAO = {"Em atendimento pela IA": "blue", "Resolvida pela IA": "green", "Encaminhada à assistência técnica": "violet",
                "Reembolso ou cancelamento (time decide)": "orange",
                "Com o time (assunto incerto)": "red", "Departamento especializado (atenção)": "red",
                "Com o time (IA fora do ar)": "red", "Cliente desistiu": "gray", ROBO_ANTERIOR: "gray"}
ETAPA = {ASSISTENCIA: "Assistência técnica", ATENDENDO: "IA atendendo", RESOLVIDA: "Resolvida pela IA", EXECUCAO: "Reembolso ou cancelamento (time decide)",
         TRIAGEM: "Com o time (IA fora do ar)", ENCERRADA: "Cliente desistiu", DETALHE: "Detalhes do pedido",
         COLETA: "Coleta de contato", IDENTIFICACAO: "Identificação", INCERTO: "Com o time (assunto incerto)",
         ESPECIALISTA: "Departamento especializado (atenção)"}
STATUS = {"Open": "Sem resposta", "Pending Customer Response": "Aguardando o cliente", "Closed": "Fechado"}
ORDEM_STATUS = ["Sem resposta", "Aguardando o cliente", "Fechado"]
CANAL = {"Phone": "Telefone", "Chat": "Chat", "Email": "E-mail", "Social media": "Redes sociais"}
PRIORIDADE = {"Low": "Baixa", "Medium": "Média", "High": "Alta", "Critical": "Crítica"}
TIPO = {"Refund request": "Reembolso", "Cancellation request": "Cancelamento", "Billing inquiry": "Cobrança",
        "Technical issue": "Problema técnico", "Product inquiry": "Dúvida de produto"}
ASSUNTO_D1 = {"Refund request": "Pedido de reembolso", "Software bug": "Erro de software",
              "Product compatibility": "Compatibilidade do produto", "Delivery problem": "Problema na entrega",
              "Hardware issue": "Problema de hardware", "Battery life": "Duração da bateria",
              "Network problem": "Problema de rede", "Installation support": "Ajuda na instalação",
              "Product setup": "Configuração do produto", "Payment issue": "Problema de pagamento",
              "Product recommendation": "Recomendação de produto", "Account access": "Acesso à conta",
              "Peripheral compatibility": "Compatibilidade de periférico", "Data loss": "Perda de dados",
              "Cancellation request": "Pedido de cancelamento", "Display issue": "Problema na tela"}
CORES_NOTA = ["#B91C1C", "#F59E0B", "#CBD5E1", "#60A5FA", "#1E40AF"]
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


def situacao(x: dict, refeitas: set | None = None) -> str:
    """Chamada de uma versão anterior das regras é do robô anterior: fica no registro e no process log, mas não
    aparece no painel nem no dashboard (Jó, 2026-11-16)."""
    if x.get("versao") != VERSAO_ROBO:
        return ROBO_ANTERIOR
    return SITUACAO.get(x["destino"], x["destino"])


def horas_desde(iso: str) -> float:
    return (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds() / 3600


def posicionamento_txt(x: dict) -> str:
    if x.get("posicionamento"):
        return "Dado"
    if pendente_posicionamento(x):
        return f"Pendente há {horas_desde(x['fim']):.0f} h"
    return ""


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
                         "assunto": d["Ticket Subject"].map(ASSUNTO_D1), "nota": d["Customer Satisfaction Rating"]})


def todas_chamadas() -> list[dict]:
    if not CONVERSAS.exists():
        return []
    return [json.loads(x) for x in CONVERSAS.read_text().splitlines() if x.strip()]


def chamadas() -> list[dict]:
    """Só as chamadas do robô em apresentação (versão atual das regras)."""
    return [x for x in todas_chamadas() if x.get("versao") == VERSAO_ROBO]


def anteriores() -> int:
    return sum(1 for x in todas_chamadas() if x.get("versao") != VERSAO_ROBO)


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
def falar(texto: str) -> None:
    """Põe a fala da atendente para tocar. Se a voz falhar, a resposta continua escrita na tela."""
    try:
        st.session_state.fala_nova = voz.sintetizar(texto)
    except Exception as erro:  # noqa: BLE001
        st.session_state.aviso_voz = f"A voz da atendente falhou ({type(erro).__name__}); a resposta está escrita acima."


with aba_conversa:
    if "conversa" not in st.session_state:
        st.session_state.conversa = Conversa(modelo())
    c: Conversa = st.session_state.conversa
    voz_ok = voz.disponivel()
    if not c.rodadas and not c.voz:
        e1, e2, _ = st.columns([2, 2, 3])
        canal = e1.selectbox("Canal da simulação", CANAIS, format_func=CANAL_ROTULO.get,
                             help="As regras são as mesmas em todo canal; muda só a forma da resposta.")
        c.canal = canal
        c.rede = e2.selectbox("Rede social de entrada", REDES) if canal == "rede social" else None
    col_chat, col_bastidor = st.columns([3, 2], gap="large")
    with col_chat:
        st.caption(("Atendimento por IA" if c.com_ia else "Atendimento sem IA") + f" · {canal_de({'canal': c.canal, 'rede': c.rede})}"
                   " · a IA atende até resolver; reembolso, cancelamento, assunto incerto e comando restrito passam "
                   "para uma pessoa")
        for r in c.rodadas:
            st.chat_message("user").write(sem_link(r.cliente))
            st.chat_message("assistant").write(sem_link(r.resposta))
        if c.voz:
            # Ligação simulada (Jó, 2026-11-16): a fala do atendente toca sozinha uma vez; o player fica para ouvir de novo.
            if fala := st.session_state.pop("fala_nova", None):
                st.session_state.fala_ultima = fala
                st.audio(fala, format="audio/wav", autoplay=True)
            elif fala := st.session_state.get("fala_ultima"):
                st.audio(fala, format="audio/wav")
            if aviso := st.session_state.pop("aviso_voz", None):
                st.warning(aviso, icon=":material/mic_off:")
        if c.encerrada:
            st.success(f"{'Ligação encerrada · ' if c.voz else ''}Chamada **{c.id}** · {SITUACAO.get(c.destino_final, '')}",
                       icon=":material/task_alt:")
            if st.button("Nova conversa", icon=":material/add_comment:", type="primary"):
                st.session_state.conversa = Conversa(modelo())
                for k in ("fala_nova", "fala_ultima", "aviso_voz"):
                    st.session_state.pop(k, None)
                st.rerun()
        elif c.canal == "telefone" and voz_ok and not c.voz:
            st.info("Ligação simulada: a atendente fala e você responde pelo microfone do navegador. A voz é transcrita "
                    "nesta máquina, não é gravada e não vai para a IA externa.", icon=":material/call:")
            if st.button("Ligar", icon=":material/call:", type="primary"):
                c.voz = True
                voz.aquecer()
                falar(voz.SAUDACAO)
                st.rerun()
            st.caption("Sem microfone? Digite abaixo a fala do cliente e a conversa segue como transcrição.")
        if c.voz and not c.encerrada:
            n = st.session_state.get("tentativa_voz", 0)
            if gravado := st.audio_input("Fale com a atendente: clique no microfone, fale e clique de novo para enviar",
                                         key=f"fala_{len(c.rodadas)}_{n}"):
                try:
                    with st.spinner("Transcrevendo..."):
                        texto = voz.transcrever(gravado.getvalue(), etapa=c.etapa)
                    if not texto:
                        raise voz.AudioInvalido("não deu para entender a fala")
                    with st.spinner("Atendente respondendo..."):
                        c.receber(voz.ditado(texto, c.etapa))
                    falar(c.rodadas[-1].resposta)
                except voz.AudioInvalido as erro:
                    st.session_state.aviso_voz = f"Áudio não aproveitado ({erro}). Fale de novo."
                    st.session_state.tentativa_voz = n + 1
                except ValueError:
                    pass
                except Exception as erro:  # noqa: BLE001
                    st.session_state.aviso_voz = f"Falha no atendimento ({type(erro).__name__}). Fale de novo."
                    st.session_state.tentativa_voz = n + 1
                st.rerun()
        if not c.encerrada and (msg := st.chat_input("Ou digite a fala do cliente" if c.voz else
                                  "Fale como cliente (transcrição)" if c.canal == "telefone" else "Escreva como cliente")):
            try:
                with st.spinner("Digitando..."):
                    c.receber(msg)
                if c.voz:
                    falar(c.rodadas[-1].resposta)
            except ValueError:
                pass
            except Exception as erro:  # noqa: BLE001
                st.error(f"Falha no atendimento ({type(erro).__name__}). Tente de novo.")
            st.rerun()
    with col_bastidor:
        st.subheader("Bastidor da decisão")
        st.caption("O que o sistema entendeu a cada mensagem. O cliente não vê esta coluna.")
        if c.voz:
            st.caption(f"Ligação por voz: fala transcrita nesta máquina (Whisper {voz.WHISPER_MODELO}), sem gravar o áudio "
                       "e sem enviá-lo à IA externa. O que a IA recebe é o texto, com os dados pessoais mascarados.")
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
def mostrar_conversa(x: dict) -> None:
    """A conversa na forma do canal: chat, troca de e-mails, mensagem direta ou transcrição da ligação."""
    canal = x.get("canal") or "chat"
    if canal == "e-mail":
        assunto = f"Re: {x.get('resumo_pt') or 'Atendimento ' + x.get('id', '')}"
        for m in x["conversa"]:
            with st.container(border=True):
                st.caption(f"De: cliente · Para: suporte · Assunto: {sem_link(assunto)}")
                st.write(sem_link(m["cliente"]))
            with st.container(border=True):
                st.caption(f"De: suporte · Para: cliente · Assunto: {sem_link(assunto)}")
                st.text(m["ia"])
    elif canal == "telefone":
        st.caption("Transcrição da ligação por voz" if x.get("voz") else "Transcrição da ligação")
        linhas = []
        for m in x["conversa"]:
            linhas += [f"**Cliente:** {sem_link(m['cliente'])}", f"**Atendente (IA):** {sem_link(m['ia'])}"]
        st.markdown("  \n".join(linhas))
    else:
        if canal == "rede social" and x.get("rede"):
            st.markdown(f":violet-badge[{x['rede']}] mensagem direta")
        for m in x["conversa"]:
            st.chat_message("user").write(sem_link(m["cliente"]))
            st.chat_message("assistant").write(sem_link(m["ia"]))


with aba_painel:
    conv = chamadas()
    st.subheader("Chamadas")
    st.caption("Toda conversa vira uma chamada com ID desde a primeira mensagem, em qualquer canal. Clique numa linha "
               "para ver a conversa. Chamada que passa para uma pessoa só fecha com o posicionamento do caso. "
               f"As {num(anteriores())} chamadas das versões anteriores do robô ficam registradas no processo e fora "
               "desta apresentação.")
    if not conv:
        st.info("Nenhuma chamada ainda. Faça um atendimento na aba Conversa.", icon=":material/info:")
    else:
        df = pd.DataFrame([{
            "ID": x.get("id"), "Data": hora_brt(x["fim"]), "Canal": canal_de(x),
            "Cliente": x.get("nome") or "não informado", "Situação": situacao(x),
            "Posicionamento": posicionamento_txt(x), "Assunto": x.get("categoria") or "",
            "Pedido": x.get("resumo_pt") or "", "Origem": ORIGEM.get(x.get("origem"), "Atendimento"),
            "_canal": CANAL_ROTULO.get(x.get("canal") or "chat"), "_i": i} for i, x in enumerate(conv)]).iloc[::-1]
        f1, f2, f3, f4, f5 = st.columns([1.1, 1.6, 2, 1.8, 1.8])
        busca = f1.text_input("ID da chamada", placeholder="ex.: 160", help="Aceita ATD-00160, atd160 ou só 160")
        can = f2.multiselect("Canal", list(CANAL_ROTULO.values()), placeholder="Todos")
        sit = f3.multiselect("Situação", [s for s in COR_SITUACAO if s in set(df["Situação"])], placeholder="Todas")
        ass = f4.multiselect("Assunto", sorted(x for x in df["Assunto"].unique() if x), placeholder="Todos")
        orig = f5.segmented_control("Quem gerou a chamada", ORIGENS, default="Todas", help=AJUDA_ORIGEM)
        v = por_origem(df, orig)
        if busca.strip():
            alvo = normalizar_busca(busca)
            v = df[df["ID"] == alvo]
            if v.empty:
                st.warning(f"Nenhuma chamada com o ID {alvo or busca}.", icon=":material/search_off:")
        if can:
            v = v[v["_canal"].isin(can)]
        if sit:
            v = v[v["Situação"].isin(sit)]
        if ass:
            v = v[v["Assunto"].isin(ass)]
        if st.toggle("Só as que aguardam posicionamento", key="so_pendentes"):
            v = v[v["Posicionamento"].str.startswith("Pendente")]

        pend = v[v["Posicionamento"].str.startswith("Pendente")]
        k = st.columns(4)
        k[0].metric("Chamadas", num(len(v)))
        k[1].metric("Resolvidas pela IA", num((v["Situação"] == "Resolvida pela IA").sum()))
        k[2].metric("Aguardando posicionamento", num(len(pend)),
                    help="Passaram para uma pessoa e ainda não têm o posicionamento do caso. O prazo é a definir com o "
                         "diretor; a coluna mostra há quanto tempo cada uma espera.")
        k[3].metric("Com etiqueta de atenção", num((v["Situação"] == "Departamento especializado (atenção)").sum()))

        lista, detalhe = st.columns([3, 2], gap="large")
        with lista:
            sel = st.dataframe(v.drop(columns=["_i", "_canal"]), hide_index=True, width="stretch", height=560,
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
                st.markdown(f"**Conversa da chamada {x.get('id')}** · {canal_de(x)}")
                # Uma caixa nova por chamada: ao trocar de chamada, a conversa abre do começo.
                with st.container(height=420, key=f"conversa_{x.get('id')}", autoscroll=False):
                    mostrar_conversa(x)
                with st.container(border=True):
                    etiqueta = " :red-badge[ATENÇÃO]" if (x.get("detalhes") or {}).get("etiqueta") else ""
                    st.markdown(f"#### {x.get('id')}  {selo(escolhida['Situação'])}{etiqueta}")
                    st.caption(f"{hora_brt(x['fim'])} · {escolhida['Origem']} · {canal_de(x)} · "
                               f"{x.get('modo', 'Atendimento por IA')} · {x.get('mensagens', '')} mensagens")
                    titulo = "Resultado da ligação" if x.get("canal") == "telefone" else "Motivo"
                    st.markdown(f"**{titulo}**  \n{sem_link(x.get('motivo'))}")
                    a, b = st.columns(2)
                    a.markdown(f"**Cliente**  \n{x.get('nome') or 'não informado'}")
                    b.markdown(f"**Assunto**  \n{x.get('categoria')} (confiança {dec(x.get('confianca') or 0)})")
                    a.markdown(f"**CPF**  \n{literal(x.get('cpf')) or 'não coletado'}")
                    b.markdown(f"**Telefone**  \n{literal(x.get('telefone')) or 'não coletado'}")
                    st.markdown(f"**E-mail**  \n{literal(x.get('email')) or 'não coletado'}")
                    for campo, rot in (("pedido", "Pedido"), ("valor", "Valor"), ("cep", "CEP usado"),
                                       ("assistencia", "Assistência indicada"), ("departamento", "Departamento")):
                        if campo in (x.get("detalhes") or {}):
                            st.markdown(f"**{rot}**  \n{literal(x['detalhes'][campo]) or 'não informado'}")
                    if x.get("posicionamento"):
                        st.success(f"**Posicionamento** ({hora_brt(x['posicionado_em'])})  \n"
                                   f"{literal(x['posicionamento'])}", icon=":material/task_alt:")
                    elif pendente_posicionamento(x):
                        st.warning(f"Aguarda o posicionamento de uma pessoa há {horas_desde(x['fim']):.0f} h. A chamada "
                                   "só fecha com ele.", icon=":material/pending_actions:")
                        with st.form(f"pos_{x['id']}", clear_on_submit=True):
                            texto = st.text_area("Posicionamento do caso", max_chars=2000,
                                                 placeholder="O que foi decidido, o que foi feito e o que foi dito ao cliente.")
                            if st.form_submit_button("Fechar com posicionamento", type="primary"):
                                try:
                                    registrar_posicionamento(x["id"], texto)
                                    st.rerun()
                                except ValueError as erro:
                                    st.error(str(erro).capitalize() + ".")

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
        grupo = f4.segmented_control("Comparar por", ["Canal", "Prioridade", "Tipo", "Assunto"], default="Canal") or "Canal"
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
            col = {"Canal": "canal", "Prioridade": "prioridade", "Tipo": "tipo", "Assunto": "assunto"}[grupo]
            g1 = st.container()
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
            st.markdown(f"**Notas de satisfação por {grupo.lower()} (só tickets fechados)**")
            fech = d.dropna(subset=["nota"])
            if len(fech):
                tn = fech.groupby([col, "nota"]).size().rename("n").reset_index()
                tn["pct"] = tn["n"] / tn.groupby(col)["n"].transform("sum")
                tn["Nota"] = tn["nota"].astype(int).astype(str)
                tn["_t"] = tn["pct"].map(pc)
                medias = fech.groupby(col)["nota"].agg(["mean", "size"]).reset_index()
                medias["rot"] = medias.apply(lambda r: f"média {dec(r['mean'])} · {num(r['size'])} notas", axis=1)
                ordem = medias.sort_values("mean")[col].tolist()
                barra = alt.Chart(tn).mark_bar().encode(
                    y=alt.Y(f"{col}:N", sort=ordem, title=None),
                    x=alt.X("pct:Q", stack="normalize", title="% das notas", axis=alt.Axis(format="%")),
                    color=alt.Color("Nota:N", sort=["1", "2", "3", "4", "5"], title="Nota",
                                    scale=alt.Scale(domain=["1", "2", "3", "4", "5"], range=CORES_NOTA),
                                    legend=alt.Legend(orient="bottom")),
                    order=alt.Order("nota:Q"),
                    tooltip=[alt.Tooltip(f"{col}:N", title=grupo), "Nota", alt.Tooltip("_t:N", title="%"),
                             alt.Tooltip("n:Q", title="Tickets")])
                rotulo = alt.Chart(medias).mark_text(align="left", dx=6, color="#0F172A").encode(
                    y=alt.Y(f"{col}:N", sort=ordem), x=alt.value(0), text="rot:N")
                c1, c2 = st.columns([3, 2], gap="large")
                c1.altair_chart(barra.properties(height=alt.Step(30)), width="stretch")
                with c2:
                    st.dataframe(medias.sort_values("mean").rename(columns={col: grupo, "mean": "Nota média",
                                                                           "size": "Notas"})[[grupo, "Nota média", "Notas"]]
                                 .assign(**{"Nota média": lambda t: t["Nota média"].map(dec)}),
                                 hide_index=True, width="stretch")
                st.caption(f"Cada barra é um {grupo.lower()}, dividido pelas notas de 1 (vermelho) a 5 (azul escuro). "
                           f"{num(len(fech))} notas; {pc(1 - len(fech) / len(d))} dos tickets deste recorte nunca foram "
                           f"avaliados, porque a nota só existe no fechamento. A nota média vai de "
                           f"{dec(medias['mean'].min())} a {dec(medias['mean'].max())} entre os grupos.")
            else:
                st.info("Nenhum ticket fechado neste recorte.", icon=":material/info:")

    with sim:
        lt = lote()
        st.caption(f"O classificador de assunto rodando sobre {num(len(lt))} tickets reais (Dataset 2) que ele nunca viu no "
                   "treino, cada um com o assunto verdadeiro conhecido. Para cada ticket, a IA dá um assunto e uma "
                   "confiança de 0 a 1. Se a confiança passa do limite, a IA define o assunto sozinha e segue o "
                   "atendimento; se não passa, o assunto fica incerto e uma pessoa assume (regra de 2026-11-16). Mova "
                   "o limite para ver a troca: limite alto acerta mais, mas manda mais tickets para uma pessoa.")
        f1, f2 = st.columns([2, 3])
        lim = f1.slider("Limite de confiança", 0.50, 0.95, LIMITE_CONFIANCA, 0.05,
                        help=f"Abaixo do limite, o ticket vai para uma pessoa. Decisão atual do Jó: {dec(LIMITE_CONFIANCA)}.")
        assuntos = f2.multiselect("Assunto real do ticket", sorted(lt["assunto_real"].unique()), placeholder="Todos")
        s = lt[lt["assunto_real"].isin(assuntos)] if assuntos else lt
        auto = s[s["confianca"] >= lim]
        k = st.columns(4)
        k[0].metric("IA define o assunto sozinha", pc(len(auto) / len(s)),
                    help="% dos tickets em que a confiança passou do limite.")
        k[1].metric("Desses, assunto certo", pc(auto["acertou"].mean()) if len(auto) else "sem dado")
        k[2].metric("Assunto incerto: vai para uma pessoa", pc(1 - len(auto) / len(s)))
        k[3].metric("Assunto errado a cada 1.000 tickets", num(round((~auto["acertou"]).sum() / len(s) * 1000)))
        g1, g2 = st.columns(2, gap="large")
        with g1:
            st.markdown("**Quanto a IA define sozinha e quanto acerta, por limite**")
            grade = []
            for L in np.round(np.arange(0.5, 0.96, 0.05), 2):
                a = s[s["confianca"] >= L]
                grade.append({"Limite": L, "Medida": "IA define o assunto sozinha", "v": len(a) / len(s)})
                if len(a):
                    grade.append({"Limite": L, "Medida": "Desses, assunto certo", "v": a["acertou"].mean()})
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
            st.markdown(f"**% definido pela IA sozinha, por assunto, no limite {dec(lim)}**")
            pa = (s["confianca"] >= lim).groupby(s["assunto_real"]).mean().rename("pct").reset_index()
            st.altair_chart(barras(pa, "assunto_real", "pct", "% definido pela IA"), width="stretch")

    with fila_t:
        lt = lote()
        st.caption(f"Simulação: tickets reais do Dataset 2 em que a confiança fica abaixo do limite {dec(LIMITE_CONFIANCA)}. "
                   "Regra de 2026-11-16: todo assunto incerto vai para uma pessoa, que só fecha a chamada com o "
                   "posicionamento do caso. Comando para mudar política, excluir site ou mexer na infraestrutura não "
                   "é executado nem altera dado: vai ao departamento especializado com etiqueta de atenção. A lista "
                   "mostra os 200 de menor confiança, traduzidos do inglês.")
        tri = lt[lt["confianca"] < LIMITE_CONFIANCA]
        restritos = lt["texto"].map(comando_restrito)
        k = st.columns(4)
        k[0].metric("Tickets com assunto incerto", num(len(tri)), help="Vão para uma pessoa.")
        k[1].metric("% do total", pc(len(tri) / len(lt)))
        k[2].metric("Acerto da IA nesses tickets", pc(tri["acertou"].mean()),
                    help="Prova de que o limite separa: abaixo dele a IA erra o assunto em 1 de cada 3.")
        k[3].metric("Comando restrito (trava por regra)", num(restritos.notna().sum()),
                    help="Tickets do teste que a trava por regra manda ao departamento especializado. O texto do "
                         "Dataset 2 vem sem pontuação nem palavras curtas, então a regra acha pouco aqui; na conversa, "
                         "a IA também sinaliza o comando restrito.")
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
        st.caption(f"As chamadas do robô em apresentação (regras de {VERSAO_ROBO}), em todos os canais. As "
                   f"{num(anteriores())} chamadas das versões anteriores ficam registradas no processo e fora destes "
                   "números.")
        if not conv:
            st.info("Nenhuma chamada ainda.", icon=":material/info:")
        else:
            cp = pd.DataFrame([{"Situação": situacao(x), "Assunto": x.get("categoria") or "", "Canal": canal_de(x),
                                "_canal": CANAL_ROTULO.get(x.get("canal") or "chat"),
                                "Origem": ORIGEM.get(x.get("origem"), "Atendimento"), "tokens": x.get("tokens") or 0,
                                "pendente": pendente_posicionamento(x)} for x in conv])
            cp = por_origem(cp, st.segmented_control("Quem gerou a chamada", ORIGENS, default="Todas", key="origem_dash",
                                                     help=AJUDA_ORIGEM))
            if cp.empty:
                st.info("Nenhuma chamada com esse filtro.", icon=":material/filter_alt_off:")
            else:
                k = st.columns(4)
                k[0].metric("Chamadas", num(len(cp)))
                k[1].metric("Resolvidas pela IA", pc((cp["Situação"] == "Resolvida pela IA").mean()))
                k[2].metric("Aguardando posicionamento", num(cp["pendente"].sum()))
                k[3].metric("Tokens de IA por chamada (média)", num(cp["tokens"].mean()))
                g1, g2 = st.columns(2, gap="large")
                with g1:
                    st.markdown("**Situação das chamadas**")
                    st.altair_chart(barras(cp["Situação"].value_counts().rename("n").reset_index(), "Situação", "n",
                                           "Chamadas", fmt=num), width="stretch")
                with g2:
                    st.markdown("**Situação por canal**")
                    tc = cp.groupby(["_canal", "Situação"]).size().rename("n").reset_index()
                    tc["pct"] = tc["n"] / tc.groupby("_canal")["n"].transform("sum")
                    tc["_t"] = tc["pct"].map(pc)
                    st.altair_chart(alt.Chart(tc).mark_bar().encode(
                        y=alt.Y("_canal:N", title=None),
                        x=alt.X("pct:Q", stack="normalize", title="% das chamadas do canal", axis=alt.Axis(format="%")),
                        color=alt.Color("Situação:N", legend=alt.Legend(orient="bottom", columns=2, title=None)),
                        tooltip=[alt.Tooltip("_canal:N", title="Canal"), "Situação", alt.Tooltip("_t:N", title="%"),
                                 alt.Tooltip("n:Q", title="Chamadas")]).properties(height=alt.Step(40)),
                        width="stretch")
                st.markdown("**Assunto das chamadas**")
                st.altair_chart(barras(cp["Assunto"].value_counts().rename("n").reset_index(), "Assunto", "n",
                                       "Chamadas", fmt=num), width="stretch")
