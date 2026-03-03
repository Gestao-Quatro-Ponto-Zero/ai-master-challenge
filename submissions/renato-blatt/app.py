import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_PATH = os.path.expanduser("~/.cache/kagglehub/datasets/agungpambudi/crm-sales-predictive-analytics/versions/1/")

@st.cache_data
def load_data():
    pipeline = pd.read_csv(f"{DATA_PATH}sales_pipeline.csv")
    accounts = pd.read_csv(f"{DATA_PATH}accounts.csv")
    products = pd.read_csv(f"{DATA_PATH}products.csv")
    teams    = pd.read_csv(f"{DATA_PATH}sales_teams.csv")

    df = pipeline.merge(accounts, on="account", how="left")
    df = df.merge(products,  on="product",      how="left")
    df = df.merge(teams,     on="sales_agent",  how="left")

    df["engage_date"] = pd.to_datetime(df["engage_date"], errors="coerce")
    df["close_date"]  = pd.to_datetime(df["close_date"],  errors="coerce")
    max_days = (datetime.now() - df["engage_date"]).dt.days.max()
    ref_date = df["engage_date"].fillna(df["close_date"])
    dataset_max_date = ref_date.max()
    df["days_in_stage"] = (dataset_max_date - ref_date).dt.days.clip(0, 365).fillna(180)
    df["is_won"]  = (df["deal_stage"] == "Won").astype(int)
    df["is_closed"] = df["deal_stage"].isin(["Won", "Lost"])

    winrate = df[df["is_closed"]].groupby("sales_agent")["is_won"].mean().rename("seller_winrate")
    df = df.merge(winrate, on="sales_agent", how="left")
    df["seller_winrate"] = df["seller_winrate"].fillna(0.5)

    product_win = df[df["is_closed"]].groupby(["product","sector"])["is_won"].mean().rename("product_sector_winrate")
    df = df.merge(product_win, on=["product","sector"], how="left")
    df["product_sector_winrate"] = df["product_sector_winrate"].fillna(0.3)

    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce").fillna(0)
    df["close_value"] = df.apply(lambda r: r["sales_price"] if r["close_value"] == 0 and "sales_price" in r else r["close_value"], axis=1).fillna(0)
    df["value_norm"] = df["close_value"].rank(pct=True).fillna(0)
    df["freshness"]    = (1 - np.clip(df["days_in_stage"] / 60, 0, 1))

    df["score"] = (
        0.35 * df["seller_winrate"] +
        0.30 * df["product_sector_winrate"] +
        0.20 * df["freshness"] +
        0.15 * df["value_norm"]
    )
    return df
def explain_score(row):
    reasons = []
    if row["seller_winrate"] >= 0.6:
        reasons.append(f"vendedor fecha {row['seller_winrate']:.0%} dos deals similares")
    elif row["seller_winrate"] <= 0.3:
        reasons.append(f"vendedor tem histórico fraco nesse perfil ({row['seller_winrate']:.0%})")

    if row["product_sector_winrate"] >= 0.6:
        reasons.append(f"produto {row['product']} performa bem no setor {row['sector']}")
    elif row["product_sector_winrate"] <= 0.3:
        reasons.append(f"produto {row['product']} tem baixa conversão nesse setor")

    if row["freshness"] >= 0.7:
        reasons.append(f"deal fresco ({int(row['days_in_stage'])} dias)")
    elif row["freshness"] <= 0.3:
        reasons.append(f"deal esfriando ({int(row['days_in_stage'])} dias parado)")

    if row["value_norm"] >= 0.7:
        reasons.append(f"alto valor (R$ {row['close_value']:,.0f})")

    score_pct = f"{row['score']:.0%}"
    if not reasons:
        return f"Score {score_pct} — perfil médio sem sinais fortes."
    return f"Score {score_pct} — {'; '.join(reasons)}."


def gerar_briefing(vendedor, deals):
    top3 = deals.nlargest(3, "score")
    esfriando = deals[deals["freshness"] <= 0.3].nlargest(2, "score")

    top3_txt = "\n".join([f"- {r['opportunity_id']} | {r['account']} | {r['product']} | Score {r['score']:.0%} | {int(r['days_in_stage'])}d" for _, r in top3.iterrows()])
    esf_txt  = "\n".join([f"- {r['opportunity_id']} | {r['account']} | {int(r['days_in_stage'])} dias parado" for _, r in esfriando.iterrows()]) if len(esfriando) else "Nenhum deal crítico no momento."

    prompt = f"""Você é um assistente comercial experiente. 
Gere um briefing de segunda-feira para o vendedor {vendedor}.
Tom: direto, humano, motivador. Máximo 5 linhas.

Top deals para focar:
{top3_txt}

Deals esfriando (risco de perda):
{esf_txt}

Fale diretamente com {vendedor}. Não use bullet points. Use linguagem natural."""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return resp.choices[0].message.content


def chat_agente(pergunta, vendedor, deals_context):
    context = deals_context.head(20).to_string(index=False)
    prompt = f"""Você é um assistente de vendas analisando o pipeline de {vendedor}.
Dados do pipeline:
{context}

Pergunta do vendedor: {pergunta}
Responda de forma direta e prática em português."""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400
    )
    return resp.choices[0].message.content

# ─── UI ───────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Lead Scorer", page_icon="🎯", layout="wide")
df = load_data()

st.sidebar.title("🎯 Lead Scorer")
view = st.sidebar.radio("Visão:", ["Vendedor", "Manager"])

if view == "Vendedor":
    vendedor = st.sidebar.selectbox("Selecione seu nome:", sorted(df["sales_agent"].dropna().unique()))
    deals = df[(df["sales_agent"] == vendedor) & (~df["is_closed"])].copy()
    deals["explicacao"] = deals.apply(explain_score, axis=1)

    st.title(f"🎯 Pipeline de {vendedor}")
    st.caption(f"{len(deals)} deals abertos")

    with st.spinner("Gerando briefing..."):
        if len(deals) > 0:
            briefing = gerar_briefing(vendedor, deals)
            st.info(f"**Briefing da semana**\n\n{briefing}")

    st.subheader("Seus deals priorizados")
    top = deals.sort_values("score", ascending=False)[
        ["opportunity_id","account","product","sector","deal_stage","days_in_stage","close_value","score","explicacao"]
    ].reset_index(drop=True)
    top.index += 1
    st.dataframe(top.style.format({"score": "{:.0%}", "close_value": "R$ {:,.0f}", "days_in_stage": "{:.0f}d"}), use_container_width=True)

    fig = px.bar(top.head(10), x="opportunity_id", y="score", color="score",
                 color_continuous_scale="RdYlGn", title="Top 10 deals por score")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("💬 Pergunte ao agente")
    if "historico" not in st.session_state:
        st.session_state.historico = []
    pergunta = st.chat_input("Ex: Qual meu melhor deal essa semana?")
    if pergunta:
        resposta = chat_agente(pergunta, vendedor, top)
        st.session_state.historico.append(("você", pergunta))
        st.session_state.historico.append(("agente", resposta))
    for autor, msg in st.session_state.historico:
        with st.chat_message("user" if autor == "você" else "assistant"):
            st.write(msg)

elif view == "Manager":
    st.title("📊 Visão do Manager")
    regiao = st.sidebar.multiselect("Filtrar região:", sorted(df["regional_office"].dropna().unique()))
    mgr_df = df[~df["is_closed"]].copy()
    if regiao:
        mgr_df = mgr_df[mgr_df["regional_office"].isin(regiao)]

    mgr_df["explicacao"] = mgr_df.apply(explain_score, axis=1)
    receita_esperada = (mgr_df["score"] * mgr_df["close_value"]).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Deals abertos", len(mgr_df))
    col2.metric("Receita esperada (top pipeline)", f"R$ {receita_esperada:,.0f}")
    col3.metric("Vendedores ativos", mgr_df["sales_agent"].nunique())

    st.subheader("Top 20 deals do time")
    top_mgr = mgr_df.sort_values("score", ascending=False)[
        ["opportunity_id","sales_agent","account","product","deal_stage","days_in_stage","close_value","score","explicacao"]
    ].head(20).reset_index(drop=True)
    top_mgr.index += 1
    st.dataframe(top_mgr.style.format({"score": "{:.0%}", "close_value": "R$ {:,.0f}"}), use_container_width=True)

    fig2 = px.bar(mgr_df.groupby("sales_agent")["is_won"].mean().reset_index(),
                  x="sales_agent", y="is_won", title="Winrate por vendedor",
                  labels={"is_won": "Taxa de fechamento"})
    st.plotly_chart(fig2, use_container_width=True)
