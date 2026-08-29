"""Lead Scorer — prioriza o pipeline aberto pra RevOps.

Roda: streamlit run src/app.py (a partir de submissions/carlos-persike/solution/)
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from formatacao import moeda_brl, moeda_brl_milhoes
from ingestao import carregar_pipeline_enriquecido
from priorizacao import priorizar_pipeline_aberto
from probabilidade import calcular_tabela_sobrevivencia

OUTPUTS_DIR = Path(__file__).resolve().parents[1] / "outputs"

COR_ESTAGIO = {"Engaging": "blue", "Prospecting": "gray"}

st.set_page_config(page_title="Lead Scorer — Prioridade de Pipeline", layout="wide")


@st.cache_data
def carregar_pipeline_priorizado() -> pd.DataFrame:
    df = carregar_pipeline_enriquecido()
    fechados = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    fechados["ganhou"] = (fechados["deal_stage"] == "Won").astype(int)
    fechados["dias_ciclo"] = (fechados["close_date"] - fechados["engage_date"]).dt.days
    tabela = calcular_tabela_sobrevivencia(fechados)
    return priorizar_pipeline_aberto(df, tabela)


@st.cache_data
def carregar_metricas_validacao() -> dict:
    caminho = OUTPUTS_DIR / "validacao_modelo.json"
    if caminho.exists():
        return json.loads(caminho.read_text(encoding="utf-8"))
    return {}


pipeline = carregar_pipeline_priorizado()
metricas = carregar_metricas_validacao()

st.title("📋 Prioridade de Pipeline")
st.caption(
    "Ordenado por **Valor Esperado** = probabilidade histórica de fechar (pelo tempo desde "
    "o engajamento) × valor do produto — não por valor bruto, não por feeling."
)

with st.sidebar:
    st.header("Filtros")
    vendedores = sorted(pipeline["sales_agent"].dropna().unique())
    managers = sorted(pipeline["manager"].dropna().unique())
    regioes = sorted(pipeline["regional_office"].dropna().unique())

    filtro_regiao = st.multiselect("Escritório regional", regioes)
    filtro_manager = st.multiselect("Manager", managers)
    filtro_vendedor = st.multiselect("Vendedor", vendedores)

    if metricas:
        st.divider()
        st.caption("Validação do sinal (holdout 20%)")
        st.metric("AUC", metricas.get("auc_holdout", "—"))
        st.caption(
            f"Baseline (classe majoritária): {metricas.get('acuracia_baseline_classe_majoritaria', '—')} · "
            "sinal real, porém modesto — ver Limitações no README."
        )

filtrado = pipeline.copy()
if filtro_regiao:
    filtrado = filtrado[filtrado["regional_office"].isin(filtro_regiao)]
if filtro_manager:
    filtrado = filtrado[filtrado["manager"].isin(filtro_manager)]
if filtro_vendedor:
    filtrado = filtrado[filtrado["sales_agent"].isin(filtro_vendedor)]

col1, col2, col3 = st.columns(3)
col1.metric("Negócios abertos", f"{len(filtrado):,}".replace(",", "."))
col2.metric("Valor esperado total", moeda_brl(filtrado["valor_esperado"].sum()))
col3.metric("Sem conta vinculada", f"{filtrado['conta_desconhecida'].mean():.0%}")

st.subheader("🎯 Top 5 pra focar hoje")
if filtrado.empty:
    st.info("Nenhum negócio nesse filtro.")
else:
    for _, linha in filtrado.head(5).iterrows():
        conta = linha["account"] if not linha["conta_desconhecida"] else "conta não preenchida no CRM"
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1.4, 1.2])
            with c1:
                st.markdown(f"**{linha['product']}** — {conta}")
                st.caption(f"`{linha['opportunity_id']}` · {linha['sales_agent']}")
            with c2:
                st.badge(linha["deal_stage"], color=COR_ESTAGIO.get(linha["deal_stage"], "gray"))
                st.progress(
                    linha["probabilidade_historica"],
                    text=f"{linha['probabilidade_historica']:.0%} chance histórica",
                )
            c3.metric("Valor esperado", moeda_brl(linha["valor_esperado"]))

st.subheader("Fila completa")
tabela_exibicao = filtrado[
    [
        "opportunity_id",
        "sales_agent",
        "manager",
        "regional_office",
        "deal_stage",
        "product",
        "dias_desde_engajamento",
        "probabilidade_historica",
        "valor_produto",
        "valor_esperado",
    ]
].copy()
tabela_exibicao["dias_desde_engajamento"] = tabela_exibicao["dias_desde_engajamento"].astype(int)
tabela_exibicao["probabilidade_historica"] = tabela_exibicao["probabilidade_historica"] * 100
tabela_exibicao["valor_produto"] = tabela_exibicao["valor_produto"].apply(moeda_brl)
tabela_exibicao["valor_esperado_fmt"] = tabela_exibicao["valor_esperado"].apply(moeda_brl)
tabela_exibicao = tabela_exibicao.rename(
    columns={
        "opportunity_id": "Oportunidade",
        "sales_agent": "Vendedor",
        "manager": "Manager",
        "regional_office": "Região",
        "deal_stage": "Estágio",
        "product": "Produto",
        "dias_desde_engajamento": "Dias",
        "probabilidade_historica": "Probabilidade",
        "valor_produto": "Valor do produto",
        "valor_esperado_fmt": "Valor esperado",
    }
).drop(columns=["valor_esperado"])
st.dataframe(
    tabela_exibicao,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Probabilidade": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
        "Valor esperado": st.column_config.TextColumn(pinned=True),
    },
)
st.caption("Clique em uma oportunidade abaixo pra ver o detalhe completo, incluindo dados da conta.")

st.subheader("🔍 Detalhe de um negócio")
if not filtrado.empty:
    escolhido_id = st.selectbox("Oportunidade", filtrado["opportunity_id"])
    negocio = filtrado[filtrado["opportunity_id"] == escolhido_id].iloc[0]

    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown("**Negócio**")
        st.badge(negocio["deal_stage"], color=COR_ESTAGIO.get(negocio["deal_stage"], "gray"))
        st.write(f"Vendedor: {negocio['sales_agent']} ({negocio['manager']}, {negocio['regional_office']})")
        st.write(f"Produto: {negocio['product']} — {moeda_brl(negocio['valor_produto'])}")
        st.progress(
            negocio["probabilidade_historica"],
            text=f"{negocio['probabilidade_historica']:.0%} de chance histórica de fechar",
        )
        st.metric("Valor esperado", moeda_brl(negocio["valor_esperado"]))
    with dc2:
        st.markdown("**Conta**")
        if negocio["conta_desconhecida"]:
            st.info("Conta não preenchida no CRM — sem dados de setor/porte disponíveis.")
        else:
            st.write(f"Nome: {negocio['account']}")
            st.write(f"Setor: {negocio.get('sector', '—')}")
            st.write(f"Receita anual: {moeda_brl_milhoes(negocio.get('revenue', 0))}")
            st.write(f"Funcionários: {int(negocio.get('employees', 0)):,}".replace(",", "."))
    st.caption(negocio["explicacao"])
