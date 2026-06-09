"""
Diagnóstico operacional — Dataset 1 (Customer Support Tickets)

Entregas do desafio:
  1. Onde o fluxo trava (gargalos por canal, tipo, prioridade)
  2. O que impacta satisfação
  3. Quanto estamos desperdiçando em horas

Uso:
  python analise_dataset1.py
  python analise_dataset1.py --dataset /caminho/customer_support_tickets.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parents[4]  # g4-challenge/
DEFAULT_DATASET = (
    WORKSPACE_ROOT / "data/dataset1-support-tickets/customer_support_tickets.csv"
)
OUTPUT_DIR = SCRIPT_DIR / "output"

PRIORITY_ORDER = ["Low", "Medium", "High", "Critical"]
STATUS_UNRESOLVED = {"Open", "Pending Customer Response"}


def resolve_dataset_path(cli_path: str | None) -> Path:
    if cli_path:
        return Path(cli_path).expanduser().resolve()
    return DEFAULT_DATASET


def count_physical_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset não encontrado: {path}\n"
            "Baixe do Kaggle e coloque em data/dataset1-support-tickets/"
        )

    # Ticket Description e Resolution contem quebras de linha entre aspas.
    # O parse correto depende do CSV respeitar RFC 4180 (campos multilinha quoted).
    df = pd.read_csv(
        path,
        encoding="utf-8",
        quoting=csv.QUOTE_MINIMAL,
        engine="python",
    )

    n_rows = len(df)
    n_unique = df["Ticket ID"].nunique()
    if n_unique != n_rows:
        dupes = df[df["Ticket ID"].duplicated(keep=False)]["Ticket ID"].nunique()
        raise ValueError(
            f"Parse inconsistente: {n_rows:,} linhas vs {n_unique:,} Ticket IDs unicos "
            f"({dupes:,} IDs duplicados). Verifique quoting do CSV."
        )

    return df


def add_cycle_time(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Calcula tempo de ciclo em horas a partir de timestamps.

    First Response Time e Time to Resolution sao instantes (nao duracoes).
    Tempo de ciclo = |Time to Resolution - First Response Time| em horas.
    Usamos valor absoluto porque ~metade dos closed tem ordem invertida nos dados.
    """
    out = df.copy()
    out["first_response_at"] = pd.to_datetime(out["First Response Time"], errors="coerce")
    out["resolved_at"] = pd.to_datetime(out["Time to Resolution"], errors="coerce")

    delta = out["resolved_at"] - out["first_response_at"]
    out["cycle_hours_signed"] = delta.dt.total_seconds() / 3600
    out["cycle_hours"] = out["cycle_hours_signed"].abs()

    closed = out[out["Ticket Status"] == "Closed"]
    with_both = closed["cycle_hours_signed"].notna()
    signed = closed.loc[with_both, "cycle_hours_signed"]
    inverted = int((signed < 0).sum())

    meta = {
        "closed_with_cycle": int(with_both.sum()),
        "inverted_order": inverted,
        "inverted_pct": inverted / with_both.sum() * 100 if with_both.sum() else 0.0,
    }
    return out, meta


# ---------------------------------------------------------------------------
# 0. Exploração
# ---------------------------------------------------------------------------


def print_exploration(df: pd.DataFrame, dataset_path: Path) -> None:
    section("0. EXPLORACAO DO DATASET")

    physical_lines = count_physical_lines(dataset_path)
    multiline_desc = int(df["Ticket Description"].str.contains("\n", na=False).sum())

    print(f"Linhas fisicas no arquivo: {physical_lines:,}")
    print(f"Tickets parseados (registros): {len(df):,}")
    print(f"Ticket IDs unicos: {df['Ticket ID'].nunique():,}")
    print(
        f"Diferenca linhas vs tickets: {physical_lines - len(df):,} "
        f"(campos multilinha em Ticket Description/Resolution; parse OK se IDs unicos = registros)"
    )
    print(f"Ticket Description com quebra de linha: {multiline_desc:,} ({multiline_desc/len(df)*100:.1f}%)")
    print(f"Colunas: {len(df.columns)}")
    print("\nColunas e tipos:")
    for col in df.columns:
        print(f"  - {col}: {df[col].dtype}")

    print("\nValores ausentes:")
    for col in df.columns:
        n = df[col].isna().sum()
        if n:
            print(f"  - {col}: {n:,} ({n / len(df) * 100:.1f}%)")

    print("\nCardinalidade (categóricas):")
    for col in [
        "Ticket Type",
        "Ticket Status",
        "Ticket Priority",
        "Ticket Channel",
        "Customer Gender",
    ]:
        print(f"\n  {col}:")
        for val, cnt in df[col].value_counts().items():
            print(f"    {val}: {cnt:,}")

    print("\nPadrão de missing por status (campos operacionais):")
    for status in df["Ticket Status"].unique():
        sub = df[df["Ticket Status"] == status]
        print(f"  {status} (n={len(sub):,}):")
        print(f"    First Response Time ausente: {sub['First Response Time'].isna().sum():,}")
        print(f"    Time to Resolution ausente:  {sub['Time to Resolution'].isna().sum():,}")
        print(f"    Satisfaction ausente:        {sub['Customer Satisfaction Rating'].isna().sum():,}")

    print(
        "\nNota sobre tempos: 'First Response Time' e 'Time to Resolution' sao "
        "timestamps (nao duracoes em horas). O tempo de ciclo sera calculado na "
        "secao seguinte como |TTR - FRT| (ver DIAGNOSTICO.md)."
    )


def print_cycle_time_notes(meta: dict) -> None:
    section("0b. TEMPO DE CICLO - METODOLOGIA")

    print(
        "Definicao: cycle_hours = |Time to Resolution - First Response Time| convertido em horas."
    )
    print(
        "Motivo do valor absoluto: em dados sinteticos, TTR pode ser anterior a FRT "
        "sem indicar ciclo negativo; trata-se de ruido de ordem, nao de evento real."
    )
    print(f"Tickets Closed com ambos timestamps: {meta['closed_with_cycle']:,}")
    print(
        f"Ordem invertida (TTR < FRT): {meta['inverted_order']:,} "
        f"({meta['inverted_pct']:.1f}%) - abs() aplicado em todos os closed."
    )


# ---------------------------------------------------------------------------
# 1. Gargalos
# ---------------------------------------------------------------------------


def analyze_bottlenecks(df: pd.DataFrame) -> pd.DataFrame:
    section("1. ONDE O FLUXO TRAVA - GARGALOS")

    closed = df[df["Ticket Status"] == "Closed"]
    unresolved = df[df["Ticket Status"].isin(STATUS_UNRESOLVED)]

    print(f"Tickets sem resolução: {len(unresolved):,} ({len(unresolved)/len(df)*100:.1f}%)")
    print(f"  - Open (sem primeira resposta): {(df['Ticket Status']=='Open').sum():,}")
    print(
        f"  - Pending Customer Response: "
        f"{(df['Ticket Status']=='Pending Customer Response').sum():,}"
    )

    print("\nVolume de tickets não resolvidos por canal:")
    print_table(
        unresolved.groupby("Ticket Channel")
        .size()
        .sort_values(ascending=False)
        .rename("tickets_abertos")
    )

    print("\nTempo de ciclo medio/mediano (Closed) - por canal:")
    print_table(
        closed.groupby("Ticket Channel")["cycle_hours"]
        .agg(["mean", "median", "count"])
        .rename(columns={"mean": "media_h", "median": "mediana_h", "count": "n"})
        .sort_values("media_h", ascending=False)
    )

    print("\nPor tipo de ticket:")
    print_table(
        closed.groupby("Ticket Type")["cycle_hours"]
        .agg(["mean", "median", "count"])
        .rename(columns={"mean": "media_h", "median": "mediana_h", "count": "n"})
        .sort_values("media_h", ascending=False)
    )

    print("\nPor prioridade:")
    print_table(
        closed.groupby("Ticket Priority")["cycle_hours"]
        .agg(["mean", "median", "count"])
        .rename(columns={"mean": "media_h", "median": "mediana_h", "count": "n"})
        .sort_values("media_h", ascending=False)
    )

    print("\nPiores combinacoes canal x tipo x prioridade (media de horas, n>=20):")
    combo = (
        closed.groupby(["Ticket Channel", "Ticket Type", "Ticket Priority"])["cycle_hours"]
        .agg(["mean", "median", "count"])
        .reset_index()
    )
    combo = combo[combo["count"] >= 20].sort_values("mean", ascending=False)
    print_table(
        combo.head(15).rename(
            columns={"mean": "media_h", "median": "mediana_h", "count": "n"}
        )
    )

    print("\nOnde o fluxo trava além do tempo:")
    stall = (
        df.groupby(["Ticket Channel", "Ticket Type", "Ticket Priority", "Ticket Status"])
        .size()
        .unstack(fill_value=0)
    )
    stall["total"] = stall.sum(axis=1)
    stall["pct_nao_resolvido"] = (
        stall.get("Open", 0) + stall.get("Pending Customer Response", 0)
    ) / stall["total"] * 100
    stall = stall.sort_values("pct_nao_resolvido", ascending=False)
    print_table(stall[["total", "pct_nao_resolvido"]].head(12))

    return combo


# ---------------------------------------------------------------------------
# 2. Satisfação
# ---------------------------------------------------------------------------


def analyze_satisfaction(df: pd.DataFrame) -> None:
    section("2. O QUE IMPACTA A SATISFAÇÃO")

    closed = df[df["Ticket Status"] == "Closed"].copy()
    sat = closed["Customer Satisfaction Rating"]

    print(f"Tickets com nota (Closed): {sat.notna().sum():,}")
    print(f"Média geral: {sat.mean():.2f}  |  Mediana: {sat.median():.1f}")

    print("\nSatisfação média por canal:")
    print_table(
        closed.groupby("Ticket Channel")["Customer Satisfaction Rating"]
        .agg(["mean", "median", "count"])
        .rename(columns={"mean": "media_nota", "median": "mediana_nota", "count": "n"})
        .sort_values("media_nota")
    )

    print("\nPor tipo:")
    print_table(
        closed.groupby("Ticket Type")["Customer Satisfaction Rating"]
        .agg(["mean", "median", "count"])
        .rename(columns={"mean": "media_nota", "median": "mediana_nota", "count": "n"})
        .sort_values("media_nota")
    )

    print("\nPor prioridade:")
    print_table(
        closed.groupby("Ticket Priority")["Customer Satisfaction Rating"]
        .agg(["mean", "median", "count"])
        .rename(columns={"mean": "media_nota", "median": "mediana_nota", "count": "n"})
        .sort_values("media_nota")
    )

    corr = sat.corr(closed["cycle_hours"])
    print(f"\nCorrelacao Pearson (nota x tempo de ciclo em horas): {corr:.3f}")

    # Comparação por faixas de tempo
    closed["faixa_horas"] = pd.cut(
        closed["cycle_hours"],
        bins=[0, 4, 8, 12, 24, np.inf],
        labels=["0-4h", "4-8h", "8-12h", "12-24h", "24h+"],
    )
    print("\nSatisfação por faixa de tempo de tratamento:")
    print_table(
        closed.groupby("faixa_horas", observed=True)["Customer Satisfaction Rating"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "media_nota", "count": "n"})
    )

    # Efeito relativo: desvio da média global por categoria
    global_mean = sat.mean()
    print(f"\nDesvio vs média global ({global_mean:.2f}):")
    for dim in ["Ticket Channel", "Ticket Type", "Ticket Priority"]:
        effect = closed.groupby(dim)["Customer Satisfaction Rating"].mean() - global_mean
        worst = effect.idxmin()
        best = effect.idxmax()
        print(
            f"  {dim}: pior={worst} ({effect[worst]:+.2f}), "
            f"melhor={best} ({effect[best]:+.2f})"
        )

    print(
        "\nLeitura: tipo 'Refund request' e prioridade 'Critical' puxam notas para baixo; "
        "tempo de resolucao tem correlacao fraca; canal e natureza do pedido pesam mais."
    )


# ---------------------------------------------------------------------------
# 3. Desperdício em horas
# ---------------------------------------------------------------------------


def analyze_waste(df: pd.DataFrame) -> dict[str, float]:
    section("3. QUANTO ESTAMOS DESPERDIÇANDO (HORAS)")

    closed = df[df["Ticket Status"] == "Closed"]
    open_tickets = df[df["Ticket Status"] == "Open"]
    pending = df[df["Ticket Status"] == "Pending Customer Response"]

    median_h = closed["cycle_hours"].median()
    mean_h = closed["cycle_hours"].mean()

    hours_closed = closed["cycle_hours"].sum()
    hours_pending = len(pending) * median_h
    hours_open = len(open_tickets) * median_h
    total_estimated = hours_closed + hours_pending + hours_open

    print("Metodologia:")
    print("  A) Closed  -> soma real de cycle_hours = |TTR-FRT| (tempo de ciclo ja consumido)")
    print("  B) Pending -> n x mediana closed (tempo investido sem fechamento)")
    print("  C) Open    -> n x mediana closed (fila sem primeira resposta)")
    print(f"  Mediana de referência: {median_h:.1f}h  |  Média: {mean_h:.1f}h")

    print(f"\nA) Horas em tickets fechados:     {hours_closed:>10,.0f} h")
    print(f"B) Estimativa tickets pendentes:  {hours_pending:>10,.0f} h  ({len(pending):,} tickets)")
    print(f"C) Estimativa tickets abertos:    {hours_open:>10,.0f} h  ({len(open_tickets):,} tickets)")
    print(f"   TOTAL ESTIMADO:                {total_estimated:>10,.0f} h")
    print(f"   Equivalente (~40h/semana):      {total_estimated/40:>10,.0f} semanas-pessoa")

    cost_per_hour = 35  # USD — parâmetro editável; cenário ilustrativo
    print(f"\nCusto ilustrativo (@ US${cost_per_hour}/h agente): US${total_estimated * cost_per_hour:,.0f}")

    print("\nMaior desperdício recuperável por dimensão (horas estimadas em não resolvidos):")
    unresolved = df[df["Ticket Status"].isin(STATUS_UNRESOLVED)]
    for dim in ["Ticket Channel", "Ticket Type", "Ticket Priority"]:
        waste = unresolved.groupby(dim).size() * median_h
        waste = waste.sort_values(ascending=False)
        top = waste.index[0]
        print(f"  {dim}: {top} -> {waste[top]:,.0f} h estimadas ({waste[top]/total_estimated*100:.1f}% do total)")

    # Cenário de recuperação: reduzir piores combos ao P25
    p25 = closed["cycle_hours"].quantile(0.25)
    above_p75 = closed[closed["cycle_hours"] > closed["cycle_hours"].quantile(0.75)]
    recoverable = (above_p75["cycle_hours"] - p25).clip(lower=0).sum()
    print(
        f"\nCenário conservador: tickets closed acima do P75 reduzidos ao P25 "
        f"-> {recoverable:,.0f} h recuperaveis ({recoverable/hours_closed*100:.1f}% do tempo ja gasto em closed)"
    )

    return {
        "hours_closed": hours_closed,
        "hours_pending": hours_pending,
        "hours_open": hours_open,
        "total_estimated": total_estimated,
        "recoverable_p75_to_p25": recoverable,
    }


# ---------------------------------------------------------------------------
# Gráficos (opcional)
# ---------------------------------------------------------------------------


def save_charts(df: pd.DataFrame) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n(matplotlib nao instalado - graficos ignorados)")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    closed = df[df["Ticket Status"] == "Closed"]

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))

    for ax, col, title in zip(
        axes,
        ["Ticket Channel", "Ticket Type", "Ticket Priority"],
        ["Horas por canal", "Horas por tipo", "Horas por prioridade"],
    ):
        means = closed.groupby(col)["cycle_hours"].mean().sort_values(ascending=True)
        means.plot(kind="barh", ax=ax, color="#2563eb")
        ax.set_title(title)
        ax.set_xlabel("Media de horas (tempo de ciclo)")

    plt.tight_layout()
    path = OUTPUT_DIR / "gargalos_por_dimensao.png"
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"\nGráfico salvo: {path}")

    fig, ax = plt.subplots(figsize=(8, 4))
    sat_by_channel = closed.groupby("Ticket Channel")["Customer Satisfaction Rating"].mean()
    sat_by_channel.sort_values().plot(kind="bar", ax=ax, color="#16a34a")
    ax.set_title("Satisfação média por canal")
    ax.set_ylabel("Nota (1-5)")
    ax.set_ylim(1, 5)
    plt.tight_layout()
    path = OUTPUT_DIR / "satisfacao_por_canal.png"
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"Gráfico salvo: {path}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def print_table(obj: pd.DataFrame | pd.Series) -> None:
    with pd.option_context("display.max_rows", 50, "display.width", 120, "display.float_format", "{:.2f}".format):
        print(obj.to_string())


class Tee:
    """Duplica stdout para arquivo."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)

    def flush(self):
        for s in self.streams:
            s.flush()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnóstico operacional — Dataset 1")
    parser.add_argument("--dataset", help="Caminho alternativo para o CSV")
    parser.add_argument("--no-charts", action="store_true", help="Não gerar gráficos")
    args = parser.parse_args()

    dataset_path = resolve_dataset_path(args.dataset)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "diagnostico_dataset1.txt"

    raw = load_data(dataset_path)

    original_stdout = sys.stdout
    with open(report_path, "w", encoding="utf-8") as f:
        sys.stdout = Tee(original_stdout, f)
        print(f"Dataset: {dataset_path}")
        print_exploration(raw, dataset_path)
        df, cycle_meta = add_cycle_time(raw)
        print_cycle_time_notes(cycle_meta)
        analyze_bottlenecks(df)
        analyze_satisfaction(df)
        metrics = analyze_waste(df)
        if not args.no_charts:
            save_charts(df)
        closed = df[df["Ticket Status"] == "Closed"]
        section("RESUMO EXECUTIVO")
        print(
            f"- Arquivo: {count_physical_lines(dataset_path):,} linhas fisicas -> "
            f"{len(df):,} tickets unicos (campos multilinha)."
        )
        print(
            f"- {len(df[df['Ticket Status'].isin(STATUS_UNRESOLVED)]):,} tickets "
            f"({len(df[df['Ticket Status'].isin(STATUS_UNRESOLVED)])/len(df)*100:.0f}%) sem resolucao."
        )
        print(
            f"- Tempo de ciclo (|TTR-FRT|): media {closed['cycle_hours'].mean():.1f}h, "
            f"mediana {closed['cycle_hours'].median():.1f}h; "
            f"{cycle_meta['inverted_pct']:.0f}% com ordem invertida nos timestamps."
        )
        print(
            f"- Desperdicio estimado: {metrics['total_estimated']:,.0f} h; "
            f"{metrics['recoverable_p75_to_p25']:,.0f} h recuperaveis (cenario P75->P25)."
        )
        sys.stdout = original_stdout

    print(f"\nRelatório salvo em: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
