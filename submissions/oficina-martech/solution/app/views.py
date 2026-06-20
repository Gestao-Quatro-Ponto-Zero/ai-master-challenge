"""Views do app Foco — uma função por papel (vendedor / manager / RevOps).

Separado de `main.py` (orquestração + sidebar) para manter cada tela testável e
legível isoladamente. As views recebem os dados como parâmetros explícitos
(DataFrame já filtrado por regional, health, outcome) — sem depender de globais.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from scoring.model import brief_do_dia, brief_must_acts
from scoring.config import STALE_DAYS
from scoring.data import outcome_from_df
from scoring.actions import (
    log_action, discarded_ids, contacted_today_ids, action_log,
)
from app.theme import (
    deal_card_html, deal_card_compact_html, breakdown_html, brief_panel_html,
    kanban_head_html, rep_card_html, funnel_html, COLORS,
)

# --- constantes de apresentação (compartilhadas com main.py via import) ---
ICON = {"Foco Agora": "🔥", "Trabalhar": "⭐", "Baixa Prioridade": "⏳"}
METRIC_LABEL = {"Foco Agora": "🔥 Foco Agora", "Trabalhar": "⭐ Trabalhar",
                "Baixa Prioridade": "⏳ Baixa Prioridade"}
ALL_REGIONS = "Todas"
REGION_LABEL = {ALL_REGIONS: "Todas", "Central": "Centro", "East": "Leste", "West": "Oeste"}

# Foco do Dia = top-N RELATIVO ao rep (sempre há uma lista de "atacar hoje",
# mesmo com pipeline jovem/envelhecido — evita o rep abrir e ver "0 / nada").
FOCO_DIA_MIN = 5   # mínimo de deals no "atacar hoje" (completa com Trabalhar)
FOCO_DIA_MAX = 8   # cap de exibição da lista do dia

COLORS_WIN = COLORS["positive"]    # verde — Won
COLORS_LOST = COLORS["danger"]     # vermelho — Lost
COLORS_OPEN = COLORS["brand"]      # indigo — Aberto


def _moeda(v: float) -> str:
    return f"R$ {v:,.0f}".replace(",", ".")


def _moeda_curta(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"R$ {v / 1_000_000:.1f} mi".replace(".", ",")
    if abs(v) >= 1_000:
        return f"R$ {v / 1_000:.1f} mil".replace(".", ",")
    return _moeda(v)


# ---------------- Foco do Dia (vendedor) ----------------
def _deal_actions(r: pd.Series, agent: str, feito: bool, compact: bool = False) -> None:
    """Ações do deal: Contatado/Descartar + breakdown. compact=True para colunas estreitas."""
    label_ok = "✓ Contatado" if compact else "✓ Contatado hoje"
    exp_label = "↳ Por que esse score?" if compact else "Por que esse score?"
    c1, c2 = st.columns(2)
    if not feito and c1.button(label_ok, key=f"c-{r['opportunity_id']}",
                               type="primary", use_container_width=True):
        log_action(r["opportunity_id"], "contacted", agent)
        st.rerun()
    if c2.button("✕ Descartar", key=f"d-{r['opportunity_id']}", use_container_width=True):
        log_action(r["opportunity_id"], "discarded", agent)
        st.rerun()
    with st.expander(exp_label):
        st.markdown(breakdown_html(r), unsafe_allow_html=True)


def _deal_card(r: pd.Series, agent: str, contacted: set) -> None:
    """Card (lista) + ação visível + 'porquê' no expander."""
    feito = r["opportunity_id"] in contacted
    st.markdown(deal_card_html(r, done=feito), unsafe_allow_html=True)
    _deal_actions(r, agent, feito)


def _foco_do_dia(vivos: pd.DataFrame, contacted: set) -> pd.DataFrame:
    """Top deals do rep para atacar hoje — RELATIVO ao pipeline dele.

    Sempre começa pelos Foco Agora; se faltar, completa com Trabalhar; se ainda
    faltar, com Baixa. Assim TODO rep tem uma lista de ação (mesmo com pipeline
    jovem/fraco). O pill de tier em cada card segue honesto sobre o tier real
    (🔥 Foco Agora / ⭐ Trabalhar / ⏳ Baixa). Exclui contatados hoje.
    """
    rest = vivos[~vivos["opportunity_id"].isin(contacted)]
    foco = rest[rest["tier"] == "Foco Agora"].sort_values("score", ascending=False)
    for tier in ["Trabalhar", "Baixa Prioridade"]:
        if len(foco) >= FOCO_DIA_MIN:
            break
        extra = rest[rest["tier"] == tier].sort_values("score", ascending=False)
        foco = pd.concat([foco, extra]).head(FOCO_DIA_MIN)
    return foco


def _render_lista(vivos: pd.DataFrame, agent: str, contacted: set) -> None:
    """Lista: começa pelo Foco do Dia (top-N relativo do rep), depois o restante."""
    foco = _foco_do_dia(vivos, contacted)
    shown = set(foco.head(FOCO_DIA_MAX)["opportunity_id"])

    # 1) 🎯 Foco do Dia — atacar hoje (sempre presente, relativo ao rep)
    if not foco.empty:
        st.markdown(
            f"<div class='sectionhdr'>🎯 Foco do Dia — atacar hoje"
            f"<span class='count'>{len(foco)}</span></div>",
            unsafe_allow_html=True,
        )
        # contatados hoje vão para o fim da lista (já tratados)
        foco = pd.concat([foco[~foco["opportunity_id"].isin(contacted)],
                          foco[foco["opportunity_id"].isin(contacted)]])
        for _, r in foco.head(FOCO_DIA_MAX).iterrows():
            _deal_card(r, agent, contacted)

    # 2) Foco Agora excedente (além do top do dia, quando o rep tem muitos quentes)
    fa_extra = vivos[(vivos["tier"] == "Foco Agora") & (~vivos["opportunity_id"].isin(shown))
                     & (~vivos["opportunity_id"].isin(contacted))]
    if not fa_extra.empty:
        st.markdown(
            f"<div class='sectionhdr'>{ICON['Foco Agora']} Mais Foco Agora"
            f"<span class='count'>{len(fa_extra)}</span></div>",
            unsafe_allow_html=True,
        )
        for _, r in fa_extra.head(7).iterrows():
            _deal_card(r, agent, contacted)

    # 3) Trabalhar restante (não promovido ao Foco do Dia)
    trab = vivos[(vivos["tier"] == "Trabalhar") & (~vivos["opportunity_id"].isin(shown))]
    if not trab.empty:
        st.markdown(
            f"<div class='sectionhdr'>{ICON['Trabalhar']} Trabalhar"
            f"<span class='count'>{len(trab)}</span></div>",
            unsafe_allow_html=True,
        )
        trab = pd.concat([trab[~trab["opportunity_id"].isin(contacted)],
                          trab[trab["opportunity_id"].isin(contacted)]])
        for _, r in trab.head(7).iterrows():
            _deal_card(r, agent, contacted)


def _render_kanban(vivos: pd.DataFrame, agent: str, contacted: set) -> None:
    """Visualização Kanban: pipeline do vendedor por coluna de prioridade."""
    cols = st.columns(3, gap="medium")
    for col, tier in zip(cols, ["Foco Agora", "Trabalhar", "Baixa Prioridade"]):
        sub_df = vivos[vivos["tier"] == tier]
        sub_df = pd.concat([sub_df[~sub_df["opportunity_id"].isin(contacted)],
                            sub_df[sub_df["opportunity_id"].isin(contacted)]])
        with col:
            st.markdown(kanban_head_html(tier, len(sub_df)), unsafe_allow_html=True)
            if sub_df.empty:
                st.markdown(
                    "<div class='kanban-body'><div class='kanban-empty'>Nada aqui agora.</div></div>",
                    unsafe_allow_html=True,
                )
                continue
            for _, r in sub_df.head(8).iterrows():
                feito = r["opportunity_id"] in contacted
                st.markdown(deal_card_compact_html(r, done=feito), unsafe_allow_html=True)
                _deal_actions(r, agent, feito, compact=True)


def view_foco(df: pd.DataFrame, agent: str) -> None:
    """Tela do vendedor: o que atacar hoje, por quê, e ação por deal."""
    # camada de ação: estado persistido (fora do cache — leitura leve)
    discarded = discarded_ids()
    contacted = contacted_today_ids()

    d = df[(df["sales_agent"] == agent) & (~df["opportunity_id"].isin(discarded))].copy()
    vivos = d[~d["is_stale"]]
    stale = d[d["is_stale"]]

    n_foco = int(((vivos["tier"] == "Foco Agora")
                  & (~vivos["opportunity_id"].isin(contacted))).sum())
    n_atacar = len(_foco_do_dia(vivos, contacted))  # top-N relativo ao rep

    # hero — saudação: sempre conduz com o que atacar hoje (relativo ao rep)
    if n_atacar > 0:
        if n_foco > 0 and n_foco == n_atacar:
            sub = f"Você tem <b>{n_atacar} deal{'s' if n_atacar != 1 else ''} quente{'s' if n_atacar != 1 else ''} para atacar hoje</b>."
        elif n_foco > 0:
            sub = (f"Seus <b>{n_atacar} melhores deals para atacar hoje</b> "
                   f"({n_foco} no pico de prioridade).")
        else:
            sub = (f"Seus <b>{n_atacar} melhores deals para atacar hoje</b> — "
                   "sem nenhum no pico, mas são suas melhores chances agora.")
    else:
        sub = "Pipeline limpo hoje. Bom trabalho."
    st.markdown(
        f"<div class='foco-hero'><h2>Bom dia, {agent.split()[0]}.</h2><p>{sub}</p></div>",
        unsafe_allow_html=True,
    )

    # métricas — "Atacar hoje" lidera (número acionável); tiers = composição
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎯 Atacar hoje", n_atacar,
              help="Seus melhores deals para trabalhar hoje (top do SEU pipeline). "
                   "Quando não há Foco Agora suficiente, completa com os melhores Trabalhar — "
                   "todo rep tem uma lista.")
    c2.metric(METRIC_LABEL["Foco Agora"], int((vivos['tier'] == "Foco Agora").sum()))
    c3.metric(METRIC_LABEL["Trabalhar"], int((vivos['tier'] == "Trabalhar").sum()))
    c4.metric(METRIC_LABEL["Baixa Prioridade"], int((vivos['tier'] == "Baixa Prioridade").sum()))

    # higiene: deals priorizados sem conta não são atacáveis (não dá para
    # priorizar quem o rep não identifica) — viram alerta de RevOps, não brief.
    sem_conta = d[d["account"].isna() & d["tier"].isin(["Foco Agora", "Trabalhar"])]
    if not sem_conta.empty:
        st.markdown(
            f"""
            <div class="hygiene-alert">
              <div>⚠</div>
              <span><strong>{len(sem_conta)} deal(s) priorizado(s) sem conta no CRM</strong> — peça ao RevOps
              para atribuir antes de atacar. Eles saem do brief do dia porque não dá para agir sem saber
              quem é o cliente.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # brief visual + download .txt — MESMA fonte (brief_must_acts), nunca divergem:
    # o painel estiliza os must-acts em HTML; o .txt renderiza os mesmos em texto.
    must_acts = brief_must_acts(df, agent, exclude=discarded | contacted)
    brief = brief_do_dia(df, agent, exclude=discarded | contacted)
    n_brief = must_acts["count"]
    rotulo = "deals quentes" if n_brief != 1 else "deal quente"
    with st.expander(f"📋 Brief do dia — {n_brief} {rotulo} pra atacar", expanded=False):
        st.markdown(brief_panel_html(must_acts, show_header=False), unsafe_allow_html=True)
        st.download_button("⬇ Baixar brief (.txt)", brief,
                           file_name=f"foco-{agent.split()[0].lower()}.txt")

    # toggle de visualização — segmented_control (pill nativo, sem emoji problem)
    layout = st.segmented_control(
        "Visualização", ["Lista", "Kanban"], default="Lista",
        label_visibility="collapsed",
        help="Lista: trabalhe deal a deal. Kanban: pipeline por prioridade.",
    )

    if layout == "Kanban":
        _render_kanban(vivos, agent, contacted)
    else:
        _render_lista(vivos, agent, contacted)

    # deals muito além do ciclo — em expander para não poluir o foco principal
    if not stale.empty:
        with st.expander(f"🩺 Revisar / Descartar — {len(stale)} deals esfriados (>{STALE_DAYS}d)"):
            st.caption("Mais velhos que qualquer fechamento histórico (138d = deal Won mais velho já observado). "
                       "Provavelmente mortos — revisar com o cliente ou liberar espaço.")
            for _, r in stale.head(5).iterrows():
                _deal_card(r, agent, contacted)

    # descartados: reversível + auditável
    desc_meus = df[(df["sales_agent"] == agent)
                   & (df["opportunity_id"].isin(discarded))]
    if not desc_meus.empty:
        with st.expander(f"🗑 Descartados ({len(desc_meus)}) — reativar se necessário"):
            for _, r in desc_meus.iterrows():
                acc = r["account"] if r.get("account") else "(sem conta)"
                col1, col2 = st.columns([3, 1])
                col1.write(f"{r['product']} · {acc} — score {r['score']}")
                if col2.button("↩ Reativar", key=f"r-{r['opportunity_id']}"):
                    log_action(r["opportunity_id"], "reactivated", agent)
                    st.rerun()

    if n_atacar == 0 and stale.empty:
        st.success("Pipeline limpo hoje. Bom trabalho. 👏")


# ---------------- Time (manager) ----------------
def view_time(df: pd.DataFrame, mgr: str) -> None:
    """Tela do manager: onde está o valor e quem precisa de apoio em priorização."""
    d = df[df["manager"] == mgr]
    em_risco = d.loc[d["severity"] == "alerta", "expected_value"].sum()

    st.markdown(
        f"<div class='foco-hero'><h2>Time de {mgr}</h2>"
        f"<p>{d['sales_agent'].nunique()} vendedores no recorte · onde está o valor e quem precisa de apoio.</p></div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Vendedores", d["sales_agent"].nunique())
    c2.metric("🔥 Foco Agora", int((d["tier"] == "Foco Agora").sum()))
    c3.metric("⚠ Receita em risco", _moeda(em_risco),
              help="Valor esperado (prob × valor) na janela de risco (88–138d): deals "
                   "esfriando mas AINDA recuperáveis. O manager age aqui antes de virarem "
                   "óbito — stale (>138d) ficam em 'Revisar/Descartar'.")

    # por vendedor — cards de decisão, ordenados por onde o manager age primeiro
    reps = []
    for agent, g in d.groupby("sales_agent"):
        reps.append({
            "agent": agent,
            "foco_agora": int((g["tier"] == "Foco Agora").sum()),
            "pipeline": float(g["expected_value"].sum()),
            "em_risco": float(
                g.loc[g["severity"] == "alerta", "expected_value"].sum()),
            "revisar": int(g["is_stale"].sum()),
        })
    reps.sort(key=lambda x: (x["em_risco"], x["foco_agora"]), reverse=True)

    st.markdown(
        f"<div class='sectionhdr'>Vendedores · onde agir primeiro"
        f"<span class='count'>{len(reps)}</span></div>",
        unsafe_allow_html=True,
    )
    if not reps:
        st.info("Nenhum vendedor com deals abertos neste recorte.")
    for rep in reps:
        st.markdown(rep_card_html(rep), unsafe_allow_html=True)
        _, btn_col = st.columns([4, 1])
        if btn_col.button("Ver deals →", key=f"drill-{rep['agent']}",
                          use_container_width=True,
                          help=f"Abrir o Foco do Dia de {rep['agent']}"):
            # flags de INTENÇÃO: o main.py as consome ANTES de instanciar o
            # selectbox de Visão. Setar 'view_select' aqui (após o widget já
            # existir nesta run) lançaria StreamlitAPIException.
            st.session_state["_drill_agent"] = rep["agent"]
            st.session_state["_go_foco"] = True
            st.rerun()
    st.caption("Ordenado por receita em risco: o topo precisa de apoio em priorização; "
               "muitos a revisar/descartar = pipeline inflado.")

    # tabela densa, sob demanda (mesmos números, formato de planilha)
    with st.expander("📊 Tabela completa do time"):
        agg = (d.groupby("sales_agent")
                 .apply(lambda g: pd.Series({
                     "Foco Agora": int((g["tier"] == "Foco Agora").sum()),
                     "Pipeline esperado": _moeda(g['expected_value'].sum()),
                     "Em risco (88–138d)": _moeda(
                         g.loc[g["severity"] == "alerta", "expected_value"].sum()),
                     "Revisar/Descartar": int(g["is_stale"].sum()),
                 }), include_groups=False)
                 .reset_index()
                 .rename(columns={"sales_agent": "Vendedor"})
                 .sort_values("Foco Agora", ascending=False))
        st.dataframe(agg, hide_index=True, width='stretch')

    # export CRM-ready: leva a priorização para o fluxo real do time (fora do app)
    cols = ["opportunity_id", "sales_agent", "account", "product", "deal_stage",
            "score", "tier", "days_open", "expected_value", "action"]
    foco_csv = (d[d["tier"] == "Foco Agora"]
                .sort_values("score", ascending=False)[cols]
                .to_csv(index=False))
    st.download_button(
        f"⬇ Exportar Foco Agora do time ({int((d['tier']=='Foco Agora').sum())} deals, CSV)",
        foco_csv, file_name=f"foco-agora-{mgr.split()[0].lower()}.csv", mime="text/csv",
        help="Colunas prontas para importar/conciliar no CRM ou distribuir ao time.")


# ---------------- Saúde (RevOps) ----------------
def _tabela_outcome(o: dict, show_region: bool) -> None:
    """Tabelas de outcome histórico: por produto, por regional (opcional), ranking."""
    if show_region:
        col_p, col_r = st.columns([1, 1], gap="medium")
    else:
        col_p = st.container()
        col_r = None
    with col_p:
        st.markdown("<div class='table-title'>Por produto</div>", unsafe_allow_html=True)
        prod = o["by_product"][["product", "fechados", "won", "lost",
                                "win_rate", "receita", "ticket"]].rename(columns={
            "product": "Produto", "fechados": "Fech.", "won": "Won", "lost": "Lost",
            "win_rate": "Win rate", "receita": "Receita", "ticket": "Ticket",
        })
        prod["Win rate"] = (prod["Win rate"] * 100).round(1)
        st.dataframe(prod,
            column_config={
                "Produto": st.column_config.TextColumn("Produto", width="medium"),
                "Win rate": st.column_config.ProgressColumn(
                    "Win %", format="%.1f%%", min_value=0, max_value=100, width="medium"),
                "Receita": st.column_config.NumberColumn("Receita", format="R$ %.0f", width="medium"),
                "Ticket": st.column_config.NumberColumn("Ticket", format="R$ %.0f", width="medium"),
                "Fech.": st.column_config.NumberColumn("Fech.", format="%d", width="small"),
                "Won": st.column_config.NumberColumn("Won", format="%d", width="small"),
                "Lost": st.column_config.NumberColumn("Lost", format="%d", width="small"),
            },
            column_order=["Produto", "Fech.", "Won", "Lost", "Win rate", "Receita", "Ticket"],
            hide_index=True, use_container_width=True, height=250)
    if col_r:
        with col_r:
            st.markdown("<div class='table-title'>Por regional</div>", unsafe_allow_html=True)
            reg = o["by_region"][["regional_office", "fechados", "won", "lost",
                                  "win_rate", "receita"]].rename(columns={
                "regional_office": "Regional", "fechados": "Fech.", "won": "Won", "lost": "Lost",
                "win_rate": "Win rate", "receita": "Receita",
            })
            reg["Regional"] = reg["Regional"].map(lambda r: REGION_LABEL.get(r, r))
            reg["Win rate"] = (reg["Win rate"] * 100).round(1)
            st.dataframe(reg,
                column_config={
                    "Regional": st.column_config.TextColumn("Regional", width="small"),
                    "Win rate": st.column_config.ProgressColumn(
                        "Win %", format="%.1f%%", min_value=0, max_value=100, width="medium"),
                    "Receita": st.column_config.NumberColumn("Receita", format="R$ %.0f", width="medium"),
                    "Fech.": st.column_config.NumberColumn("Fech.", format="%d", width="small"),
                    "Won": st.column_config.NumberColumn("Won", format="%d", width="small"),
                    "Lost": st.column_config.NumberColumn("Lost", format="%d", width="small"),
                },
                column_order=["Regional", "Fech.", "Won", "Lost", "Win rate", "Receita"],
                hide_index=True, use_container_width=True, height=250)

    st.markdown("<div class='table-title'>Ranking de vendedores</div>", unsafe_allow_html=True)
    ag = o["by_agent"].sort_values("win_rate", ascending=False)[
        ["sales_agent", "fechados", "won", "lost", "win_rate", "receita"]
    ].rename(columns={
        "sales_agent": "Vendedor", "fechados": "Fech.", "won": "Won", "lost": "Lost",
        "win_rate": "Win rate", "receita": "Receita",
    })
    ag["Win rate"] = (ag["Win rate"] * 100).round(1)
    st.dataframe(ag,
        column_config={
            "Vendedor": st.column_config.TextColumn("Vendedor", width="medium"),
            "Win rate": st.column_config.ProgressColumn(
                "Win %", format="%.1f%%", min_value=0, max_value=100, width="medium"),
            "Receita": st.column_config.NumberColumn("Receita", format="R$ %.0f", width="medium"),
            "Fech.": st.column_config.NumberColumn("Fech.", format="%d", width="small"),
            "Won": st.column_config.NumberColumn("Won", format="%d", width="small"),
            "Lost": st.column_config.NumberColumn("Lost", format="%d", width="small"),
        },
        column_order=["Vendedor", "Fech.", "Won", "Lost", "Win rate", "Receita"],
        hide_index=True, use_container_width=True, height=360)


def view_saude(df: pd.DataFrame, health: dict, outcome: dict, selected_region: str) -> None:
    """Tela do RevOps: higiene/risco em destaque + scoreboard histórico."""
    if selected_region != ALL_REGIONS:
        raw_f = outcome["_raw"][outcome["_raw"]["regional_office"] == selected_region]
        o = outcome_from_df(raw_f)
        region_tag = f" — {REGION_LABEL.get(selected_region, selected_region)}"
    else:
        o = outcome
        region_tag = ""
    g = o["global"]
    st.markdown(
        "<div class='foco-hero'><h2>Saúde do pipeline</h2>"
        "<p>Higiene e risco em destaque — scoreboard histórico abaixo.</p></div>",
        unsafe_allow_html=True,
    )

    # =================== Higiene e risco (TOPO — o que precisa de ação agora) ===================
    st.markdown("<div class='sectionhdr'>🛡 Higiene e risco</div>", unsafe_allow_html=True)
    # denominador correto: deals ABERTOS (2089), não total (8800)
    pct = health["deals_sem_conta"] / health["open_deals"]
    sem_conta_ev = df.loc[df["account"].isna(), "expected_value"].sum()
    em_risco_total = df.loc[df["severity"] == "alerta", "expected_value"].sum()

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Deals abertos", int(health["open_deals"]))
    h2.metric("⚠ Sem conta", int(health["deals_sem_conta"]),
              delta=f"{pct:.0%} dos abertos",
              delta_color="inverse",
              help="% calculado sobre deals ABERTOS (2089) — é o que impacta a priorização")
    h3.metric("🔻 Receita em risco", _moeda_curta(em_risco_total),
              help="Valor esperado na janela 88–138d: esfriando mas ainda recuperável")
    h4.metric("Avaliado em", str(health["as_of_date"]),
              help="Base histórica — ponto de congelamento do dataset.")

    st.warning(f"⚠ **{pct:.0%}** dos deals **abertos** sem conta no CRM "
               f"({int(health['deals_sem_conta'])} de {int(health['open_deals'])} abertos) — "
               f"**{_moeda(sem_conta_ev)}** em valor esperado sem contexto de conta.")
    st.error(f"🔻 **{_moeda(em_risco_total)}** em receita na janela de risco (88–138d) — "
             "esfriando mas recuperável com priorização diária.")
    st.markdown("**Ação imediata:** tornar `conta` obrigatório no CRM na abertura do deal.")

    # Breakdown sem conta por vendedor — onde cobrar a atribuição
    sem_conta_df = (
        df[df["account"].isna()]
        .groupby("sales_agent")
        .agg(sem_conta=("opportunity_id", "count"),
             ev_perdido=("expected_value", "sum"))
        .reset_index()
        .rename(columns={"sales_agent": "Vendedor",
                         "sem_conta": "Sem conta",
                         "ev_perdido": "Valor esperado sem contexto"})
        .sort_values("Sem conta", ascending=False)
    )
    if not sem_conta_df.empty:
        with st.expander(f"📋 Deals sem conta por vendedor — {len(sem_conta_df)} afetados"):
            st.caption("Priorize o topo: mais deals sem conta = maior degradação de precisão.")
            st.dataframe(
                sem_conta_df,
                column_config={
                    "Vendedor": st.column_config.TextColumn("Vendedor", width="medium"),
                    "Sem conta": st.column_config.NumberColumn("Sem conta", format="%d", width="small"),
                    "Valor esperado sem contexto": st.column_config.NumberColumn(
                        "Valor esperado s/ conta", format="R$ %.0f", width="medium"),
                },
                hide_index=True, use_container_width=True,
                height=min(400, 36 * len(sem_conta_df) + 38),
            )

    # log de auditoria
    log = action_log(limit=30)
    if log:
        with st.expander(f"📜 Ações recentes dos vendedores ({len(log)})"):
            st.dataframe(pd.DataFrame(
                log, columns=["Quando", "Deal", "Ação", "Vendedor", "Nota"]),
                hide_index=True, use_container_width=True)

    st.divider()

    # =================== Resultado histórico (contexto secundário) ===================
    st.markdown(
        f"<div class='sectionhdr'>📊 Resultado histórico "
        f"<span class='count'>{g['total']:,} deals</span></div>".replace(",", "."),
        unsafe_allow_html=True,
    )
    st.caption(
        f"Base avaliada em **{health['as_of_date']}**{region_tag}. "
        f"Os {g['won']+g['lost']:,} deals fechados calibram o scoring.".replace(",", ".")
    )

    k1, k2, k3, k4, k5 = st.columns(5, gap="small")
    k1.metric("🏆 Conversão", f"{g['win_rate']:.1%}",
              help="Won ÷ (Won + Lost). Probabilidade base do modelo.")
    k2.metric("💰 Receita", _moeda_curta(g['receita_ganha']),
              help=_moeda(g['receita_ganha']))
    k3.metric("📦 Ticket médio", _moeda(g['ticket_medio']))
    k4.metric("✅ Fechados", f"{g['won']+g['lost']:,}".replace(",", "."),
              help=f"Won {g['won']:,} · Lost {g['lost']:,}".replace(",", "."))
    k5.metric("⏱ Ciclo médio", f"{g['ciclo_medio']:.0f}d",
              help=f"mediana {g['ciclo_p50']:.0f}d · p90 {g['ciclo_p90']:.0f}d")

    st.markdown(
        funnel_html([
            ("🏆 Ganhos",    g['won'],  100*g['won']/g['total'],  COLORS_WIN),
            ("🔻 Perdidos",  g['lost'], 100*g['lost']/g['total'], COLORS_LOST),
            ("📂 Em aberto", g['open'], 100*g['open']/g['total'], COLORS_OPEN),
        ]),
        unsafe_allow_html=True,
    )

    _tabela_outcome(o, show_region=selected_region == ALL_REGIONS)
