"""
EDA — Challenge 003 Lead Scorer.

Script de Exploratory Data Analysis sobre o sales_pipeline.csv.
Construído contra a SPEC do Prompt 02 (AGENT-B + SKILL-04).

Regras do harness aplicadas:
- Não assumir nomes de coluna — print df.columns + dtypes primeiro
- Paths relativos via pathlib (sem hardcode de máquina)
- Sem PII printado (sales_agent anonimizado em relatório)
- Formato de data MM/DD/YYYY explicitado — não confiar em ISO
- Output paralelo em eda_report.txt para auditoria

Uso:
    (venv) python eda.py
"""
from __future__ import annotations

from pathlib import Path
from io import StringIO

import pandas as pd

# --- Paths relativos ao arquivo atual ---------------------------------------
BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
REPORT_PATH = BASE / "eda_report.txt"

PIPELINE_CSV = DATA_DIR / "sales_pipeline.csv"
ACCOUNTS_CSV = DATA_DIR / "accounts.csv"
PRODUCTS_CSV = DATA_DIR / "products.csv"
SALES_TEAMS_CSV = DATA_DIR / "sales_teams.csv"

DATE_FORMAT = "%m/%d/%Y"  # validado na mão — primeira linha: 02/15/2025


def _emit(buf: StringIO, msg: str = "") -> None:
    """Escreve no buffer e ecoa no stdout."""
    print(msg)
    buf.write(msg + "\n")


def _hr(buf: StringIO, char: str = "=", n: int = 70) -> None:
    _emit(buf, char * n)


def section(buf: StringIO, title: str) -> None:
    _emit(buf)
    _hr(buf)
    _emit(buf, title.upper())
    _hr(buf)


# --- 0. load pipeline validating schema -------------------------------------
def load_pipeline() -> pd.DataFrame:
    """Carrega sales_pipeline.csv validando schema real."""
    df = pd.read_csv(PIPELINE_CSV)
    # Hook dtype-check: nunca confiar em dtypes inferidos p/ datas
    df["engage_date"] = pd.to_datetime(df["engage_date"], format=DATE_FORMAT, errors="coerce")
    df["close_date"] = pd.to_datetime(df["close_date"], format=DATE_FORMAT, errors="coerce")
    return df


# --- 1. Schema + dtypes -----------------------------------------------------
def report_schema(buf: StringIO, df: pd.DataFrame) -> None:
    section(buf, "1. Schema e dtypes")
    _emit(buf, f"Shape: {df.shape[0]} linhas × {df.shape[1]} colunas")
    _emit(buf)
    _emit(buf, "Colunas:")
    for col in df.columns:
        _emit(buf, f"  - {col}: {df[col].dtype}")
    _emit(buf)
    _emit(buf, "head(3):")
    _emit(buf, df.head(3).to_string(index=False))


# --- 2. Nulos por coluna ----------------------------------------------------
def report_nulls(buf: StringIO, df: pd.DataFrame) -> None:
    section(buf, "2. Nulos por coluna")
    nulls = df.isna().sum()
    pct = (nulls / len(df) * 100).round(2)
    table = pd.DataFrame({"n_nulos": nulls, "pct": pct}).sort_values("n_nulos", ascending=False)
    _emit(buf, table.to_string())
    _emit(buf)
    # Hook pct-null-alert: alerta em colunas com >20% nulos
    high_null = table[table["pct"] > 20]
    if not high_null.empty:
        _emit(buf, "ALERTA: colunas com >20% nulos:")
        for col, row in high_null.iterrows():
            _emit(buf, f"  - {col}: {row['pct']}% nulos")
    else:
        _emit(buf, "Nenhuma coluna com >20% nulos.")


# --- 3. Distribuição de deal_stage ------------------------------------------
def report_stage_distribution(buf: StringIO, df: pd.DataFrame) -> None:
    section(buf, "3. Distribuição de deal_stage")
    counts = df["deal_stage"].value_counts()
    pct = (counts / len(df) * 100).round(2)
    table = pd.DataFrame({"contagem": counts, "pct": pct})
    _emit(buf, table.to_string())


# --- 4. Win rate por sales_agent (PII-anonimizado) --------------------------
def report_agent_winrate(buf: StringIO, df: pd.DataFrame) -> None:
    section(buf, "4. Win rate por sales_agent (Won / Won+Lost)")
    closed = df[df["deal_stage"].isin(["Won", "Lost"])]
    if closed.empty:
        _emit(buf, "Sem deals fechados para calcular win rate.")
        return

    grouped = closed.groupby("sales_agent")["deal_stage"].agg(
        won=lambda s: (s == "Won").sum(),
        lost=lambda s: (s == "Lost").sum(),
    )
    grouped["total_fechados"] = grouped["won"] + grouped["lost"]
    grouped["win_rate"] = (grouped["won"] / grouped["total_fechados"] * 100).round(2)
    grouped = grouped.sort_values("win_rate", ascending=False)

    # PII: não printar nome real do agente — anonimizar para o relatório
    grouped_print = grouped.copy()
    agent_map = {name: f"agent_{i+1:02d}" for i, name in enumerate(grouped_print.index)}
    grouped_print.index = [agent_map[a] for a in grouped_print.index]

    _emit(buf, grouped_print.to_string())
    _emit(buf)
    _emit(buf, f"Agentes no dataset (anonimizados no relatório): {df['sales_agent'].nunique()}")
    _emit(buf, f"Faixa de win rate: {grouped['win_rate'].min():.2f}% a {grouped['win_rate'].max():.2f}%")
    _emit(buf, f"Win rate médio global: {(closed['deal_stage'] == 'Won').mean() * 100:.2f}%")


# --- 5. Distribuição de close_value por stage -------------------------------
def report_value_by_stage(buf: StringIO, df: pd.DataFrame) -> None:
    section(buf, "5. Distribuição de close_value por deal_stage")
    summary = df.groupby("deal_stage")["close_value"].agg(
        ["count", "mean", "median", "min", "max", "sum"]
    ).round(2)
    _emit(buf, summary.to_string())
    _emit(buf)
    # Armadilha A4: close_value==0 em Won?
    won_zero = df[(df["deal_stage"] == "Won") & (df["close_value"] == 0)]
    _emit(buf, f"Deals Won com close_value=0 (potencial bug): {len(won_zero)}")


# --- 6. Tempo médio engage→close por stage ----------------------------------
def report_velocity_by_stage(buf: StringIO, df: pd.DataFrame) -> None:
    section(buf, "6. Tempo médio entre engage_date e close_date por stage")
    df_closed = df.dropna(subset=["close_date", "engage_date"]).copy()
    df_closed["dias_pipeline"] = (df_closed["close_date"] - df_closed["engage_date"]).dt.days

    if df_closed.empty:
        _emit(buf, "Sem deals com engage_date e close_date preenchidos.")
        return

    summary = df_closed.groupby("deal_stage")["dias_pipeline"].agg(
        ["count", "mean", "median", "min", "max"]
    ).round(2)
    _emit(buf, summary.to_string())
    _emit(buf)
    _emit(buf, "Distribuição geral (dias no pipeline, deals fechados):")
    _emit(buf, df_closed["dias_pipeline"].describe().round(2).to_string())


# --- 7. Nulos em engage_date estratificados por stage (A2) ------------------
def report_engage_nulls_by_stage(buf: StringIO, df: pd.DataFrame) -> None:
    section(buf, "7. Nulos em engage_date por deal_stage (armadilha A2)")
    nulls = df.groupby("deal_stage")["engage_date"].apply(lambda s: s.isna().sum())
    total = df.groupby("deal_stage")["engage_date"].size()
    pct = (nulls / total * 100).round(2)
    table = pd.DataFrame({"n_nulos_engage": nulls, "total": total, "pct": pct})
    _emit(buf, table.to_string())


# --- 8. Crosstab manager × regional_office (A10) ----------------------------
def report_manager_office(buf: StringIO) -> None:
    section(buf, "8. Crosstab manager × regional_office (armadilha A10)")
    if not SALES_TEAMS_CSV.exists():
        _emit(buf, "sales_teams.csv não encontrado — pulando crosstab.")
        return
    teams = pd.read_csv(SALES_TEAMS_CSV)
    crosstab = pd.crosstab(teams["manager"], teams["regional_office"])
    _emit(buf, crosstab.to_string())
    _emit(buf)
    diagonal = (crosstab.values > 0).sum(axis=1)
    n_managers = len(crosstab)
    fully_diagonal = (diagonal == 1).sum()
    _emit(buf, f"Managers cobrindo exatamente 1 escritório: {fully_diagonal}/{n_managers}")
    if fully_diagonal == n_managers:
        _emit(buf, "ALERTA: manager e regional_office são colineares — usar só um deles.")


# --- 9. Tabelas auxiliares (accounts / products) ----------------------------
def report_aux_tables(buf: StringIO) -> None:
    section(buf, "9. Tabelas auxiliares (accounts / products)")
    if ACCOUNTS_CSV.exists():
        acc = pd.read_csv(ACCOUNTS_CSV)
        _emit(buf, f"accounts.csv: {len(acc)} contas")
        _emit(buf, f"Colunas: {list(acc.columns)}")
        _emit(buf, f"  industries: {acc['industry'].nunique()} valores únicos")
        _emit(buf, f"  countries: {acc['country'].nunique()}")
        _emit(buf, f"  revenue: min={acc['revenue'].min()}, max={acc['revenue'].max()}, median={acc['revenue'].median()}")
        _emit(buf, f"  employees: min={acc['employees'].min()}, max={acc['employees'].max()}")
        _emit(buf, f"  has_trial: {acc['has_trial'].value_counts().to_dict()}")
    _emit(buf)
    if PRODUCTS_CSV.exists():
        prod = pd.read_csv(PRODUCTS_CSV)
        _emit(buf, f"products.csv: {len(prod)} produtos")
        _emit(buf, f"Colunas: {list(prod.columns)}")
        _emit(buf, prod.to_string(index=False))


# --- main -------------------------------------------------------------------
def main() -> None:
    buf = StringIO()

    _emit(buf, "=" * 70)
    _emit(buf, "EDA REPORT — Challenge 003 Lead Scorer")
    _emit(buf, f"Fonte: {PIPELINE_CSV.name}")
    _emit(buf, "=" * 70)

    df = load_pipeline()

    report_schema(buf, df)
    report_nulls(buf, df)
    report_stage_distribution(buf, df)
    report_agent_winrate(buf, df)
    report_value_by_stage(buf, df)
    report_velocity_by_stage(buf, df)
    report_engage_nulls_by_stage(buf, df)
    report_manager_office(buf)
    report_aux_tables(buf)

    _emit(buf)
    _hr(buf)
    _emit(buf, "FIM DO RELATÓRIO")
    _hr(buf)

    REPORT_PATH.write_text(buf.getvalue(), encoding="utf-8")
    print(f"\nRelatório salvo em: {REPORT_PATH}")


if __name__ == "__main__":
    main()
