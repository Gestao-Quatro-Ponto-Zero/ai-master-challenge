"""Lead Scorer — prioriza o pipeline aberto pra RevOps.

Roda: streamlit run src/app.py (a partir de submissions/carlos-persike/solution/)
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from ingestao import carregar_pipeline_enriquecido
from priorizacao import priorizar_pipeline_aberto
from probabilidade import calcular_tabela_sobrevivencia

OUTPUTS_DIR = Path(__file__).resolve().parents[1] / "outputs"

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
    "Ordena os negócios abertos por Valor Esperado (probabilidade histórica de fechar × "
    "valor do produto), não por valor bruto ou feeling."
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
            "sinal real mas modesto — ver Limitações."
        )

filtrado = pipeline.copy()
if filtro_regiao:
    filtrado = filtrado[filtrado["regional_office"].isin(filtro_regiao)]
if filtro_manager:
    filtrado = filtrado[filtrado["manager"].isin(filtro_manager)]
if filtro_vendedor:
    filtrado = filtrado[filtrado["sales_agent"].isin(filtro_vendedor)]

col1, col2, col3 = st.columns(3)
col1.metric("Negócios abertos", f"{len(filtrado):,}")
col2.metric("Valor esperado total", f"R$ {filtrado['valor_esperado'].sum():,.0f}")
col3.metric("Sem conta vinculada", f"{filtrado['conta_desconhecida'].mean():.0%}")

st.subheader("🎯 Top 5 pra focar hoje")
if filtrado.empty:
    st.info("Nenhum negócio nesse filtro.")
else:
    top5 = filtrado.head(5)
    for _, linha in top5.iterrows():
        conta = linha["account"] if not linha["conta_desconhecida"] else "conta não preenchida no CRM"
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{linha['product']}** — {conta} · `{linha['opportunity_id']}`")
            c1.caption(linha["explicacao"])
            c2.metric("Valor esperado", f"R$ {linha['valor_esperado']:,.0f}")

st.subheader("Fila completa")
tabela_exibicao = filtrado[
    [
        "opportunity_id",
        "sales_agent",
        "manager",
        "regional_office",
        "deal_stage",
        "product",
        "valor_esperado",
        "explicacao",
    ]
].rename(
    columns={
        "opportunity_id": "Oportunidade",
        "sales_agent": "Vendedor",
        "manager": "Manager",
        "regional_office": "Região",
        "deal_stage": "Estágio",
        "product": "Produto",
        "valor_esperado": "Valor esperado (R$)",
        "explicacao": "Por que esse score",
    }
)
st.dataframe(
    tabela_exibicao,
    use_container_width=True,
    hide_index=True,
    column_config={"Valor esperado (R$)": st.column_config.NumberColumn(format="R$ %.0f")},
)

st.subheader("🔍 Detalhe de um negócio")
if not filtrado.empty:
    escolhido_id = st.selectbox("Oportunidade", filtrado["opportunity_id"])
    negocio = filtrado[filtrado["opportunity_id"] == escolhido_id].iloc[0]

    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown("**Negócio**")
        st.write(f"Vendedor: {negocio['sales_agent']} ({negocio['manager']}, {negocio['regional_office']})")
        st.write(f"Estágio: {negocio['deal_stage']}")
        st.write(f"Produto: {negocio['product']} — R$ {negocio['valor_produto']:,.0f}")
        st.write(f"Probabilidade histórica: {negocio['probabilidade_historica']:.0%}")
        st.write(f"**Valor esperado: R$ {negocio['valor_esperado']:,.0f}**")
    with dc2:
        st.markdown("**Conta**")
        if negocio["conta_desconhecida"]:
            st.write("Conta não preenchida no CRM — sem dados de setor/porte disponíveis.")
        else:
            st.write(f"Nome: {negocio['account']}")
            st.write(f"Setor: {negocio.get('sector', '—')}")
            st.write(f"Receita anual: R$ {negocio.get('revenue', 0):,.1f}M")
            st.write(f"Funcionários: {int(negocio.get('employees', 0))}")
    st.caption(negocio["explicacao"])
