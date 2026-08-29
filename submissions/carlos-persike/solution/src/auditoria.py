"""Auditoria dos dois datasets antes de qualquer diagnostico.

Objetivo: descobrir se os dados sao confiaveis o suficiente para basear
decisao de negocio, ou se sao sinteticos/embaralhados e isso precisa
virar parte do diagnostico (nao um obstaculo escondido).
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
DATASETS = RAIZ / "datasets"
OUTPUTS = RAIZ / "submissions" / "carlos-persike" / "solution" / "outputs"


def carregar_tickets() -> pd.DataFrame:
    return pd.read_csv(DATASETS / "customer_support_tickets.csv")


def carregar_it_tickets() -> pd.DataFrame:
    return pd.read_csv(DATASETS / "all_tickets_processed_improved_v3.csv")


def auditar_tickets(df: pd.DataFrame) -> str:
    linhas = []
    linhas.append(f"Linhas: {len(df)} | Colunas: {list(df.columns)}")
    linhas.append("\n-- Nulos por coluna --")
    linhas.append(df.isna().sum().to_string())

    linhas.append("\n-- Cardinalidade --")
    for col in ["Ticket Type", "Ticket Status", "Ticket Priority", "Ticket Channel", "Product Purchased"]:
        linhas.append(f"{col}: {df[col].nunique()} valores unicos -> {df[col].value_counts().to_dict()}")

    linhas.append("\n-- Placeholder nao interpolado em Ticket Description --")
    n_placeholder = df["Ticket Description"].str.contains(r"\{product_purchased\}", regex=True, na=False).sum()
    linhas.append(f"{n_placeholder}/{len(df)} descricoes contem o literal '{{product_purchased}}' (templated, nao texto real de cliente)")

    linhas.append("\n-- Distribuicao de Customer Satisfaction Rating por Ticket Status --")
    linhas.append(df.groupby("Ticket Status")["Customer Satisfaction Rating"].agg(["count", "mean"]).to_string())

    linhas.append("\n-- CSAT preenchido apenas quando resolvido? --")
    csat_por_status = df.groupby("Ticket Status")["Customer Satisfaction Rating"].apply(lambda s: s.notna().mean())
    linhas.append(csat_por_status.to_string())

    linhas.append("\n-- Correlacao numerica bruta (idade x satisfacao) --")
    linhas.append(str(df[["Customer Age", "Customer Satisfaction Rating"]].corr().iloc[0, 1]))

    linhas.append("\n-- Amostra de 3 descricoes (sem PII, so pra ver o padrao textual) --")
    for texto in df["Ticket Description"].dropna().sample(3, random_state=42):
        linhas.append(f"  > {texto[:160]}")

    return "\n".join(linhas)


def auditar_it_tickets(df: pd.DataFrame) -> str:
    linhas = []
    linhas.append(f"Linhas: {len(df)} | Colunas: {list(df.columns)}")
    linhas.append("\n-- Nulos por coluna --")
    linhas.append(df.isna().sum().to_string())
    linhas.append("\n-- Distribuicao de Topic_group --")
    linhas.append(df["Topic_group"].value_counts().to_string())
    linhas.append("\n-- Tamanho medio do texto por categoria (palavras) --")
    linhas.append(df.assign(n_palavras=df["Document"].str.split().str.len()).groupby("Topic_group")["n_palavras"].mean().to_string())
    linhas.append("\n-- Duplicatas exatas de texto --")
    linhas.append(str(df["Document"].duplicated().sum()))
    return "\n".join(linhas)


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    tickets = carregar_tickets()
    it_tickets = carregar_it_tickets()

    relatorio = []
    relatorio.append("=" * 80)
    relatorio.append("DATASET 1 — customer_support_tickets.csv")
    relatorio.append("=" * 80)
    relatorio.append(auditar_tickets(tickets))
    relatorio.append("\n\n" + "=" * 80)
    relatorio.append("DATASET 2 — all_tickets_processed_improved_v3.csv")
    relatorio.append("=" * 80)
    relatorio.append(auditar_it_tickets(it_tickets))

    texto_final = "\n".join(relatorio)
    (OUTPUTS / "auditoria.txt").write_text(texto_final, encoding="utf-8")
    print(texto_final)


if __name__ == "__main__":
    main()
