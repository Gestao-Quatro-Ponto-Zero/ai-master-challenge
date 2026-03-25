#!/usr/bin/env python3
"""Pipeline de diagnóstico operacional para o Challenge 002.

Executa limpeza, análises descritivas e gera saídas (gráficos e resumo
executivo) usando o dataset data/customer_support_tickets.csv.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib

# Evita necessidade de backend gráfico instalado
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# ---------- Configurações globais ----------
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "customer_support_tickets.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
sns.set(style="whitegrid", palette="colorblind")


def normalize_col_name(name: str) -> str:
    """Gera um slug simples para comparação de nomes de coluna."""

    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name


# Mapa de aliases para cobrir grafias ligeiramente diferentes
COLUMN_ALIASES: Dict[str, Iterable[str]] = {
    "ticket_id": ["ticket_id", "id"],
    "customer_name": ["customer_name"],
    "customer_email": ["customer_email", "email"],
    "customer_age": ["customer_age", "age"],
    "customer_gender": ["customer_gender", "gender"],
    "product_purchased": ["product_purchased", "product"],
    "date_of_purchase": ["date_of_purchase", "purchase_date"],
    "ticket_type": ["ticket_type", "type"],
    "ticket_subject": ["ticket_subject", "subject"],
    "ticket_description": ["ticket_description", "description"],
    "ticket_status": ["ticket_status", "status"],
    "resolution": ["resolution", "ticket_resolution"],
    "ticket_priority": ["ticket_priority", "priority"],
    "ticket_channel": ["ticket_channel", "channel"],
    "first_response_time": ["first_response_time", "response_time"],
    "time_to_resolution": ["time_to_resolution", "resolution_time"],
    "customer_satisfaction_rating": ["customer_satisfaction_rating", "csat", "satisfaction"],
}


def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza nomes de colunas com fallback por similaridade."""

    alias_lookup = {normalize_col_name(alias): canonical for canonical, aliases in COLUMN_ALIASES.items() for alias in aliases}
    rename_map = {}
    for original in df.columns:
        normalized = normalize_col_name(original)
        if normalized in alias_lookup:
            rename_map[original] = alias_lookup[normalized]
        else:
            # fallback: mantém nome normalizado
            rename_map[original] = normalized
    return df.rename(columns=rename_map)


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"[INFO] Base carregada de {path} com {df.shape[0]} linhas e {df.shape[1]} colunas.")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = map_columns(df)
    # Espaços em branco para NaN e strip em string
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"": np.nan, "nan": np.nan})

    # Normaliza categorias de interesse
    for col in ["ticket_channel", "ticket_type", "ticket_priority", "ticket_status"]:
        if col in df.columns:
            df[col] = df[col].str.title()

    # Tipos numéricos
    if "customer_age" in df.columns:
        df["customer_age"] = pd.to_numeric(df["customer_age"], errors="coerce")

    if "customer_satisfaction_rating" in df.columns:
        df["customer_satisfaction_rating"] = pd.to_numeric(df["customer_satisfaction_rating"], errors="coerce")

    return df


def _series_to_hours(series: pd.Series) -> pd.Series:
    """Converte diversas representações de tempo em horas (float)."""

    s = series.fillna("").astype(str).str.strip()

    # 1) Valores numéricos já em horas
    numeric_mask = s.str.match(r"^-?\d+(\.\d+)?$")
    hours = pd.to_numeric(s.where(numeric_mask), errors="coerce")

    # 2) Formatos tipo HH:MM:SS
    td = pd.to_timedelta(s, errors="coerce")
    hours = hours.fillna(td.dt.total_seconds() / 3600)

    # 3) Formatos com palavras ("12 hours", "3h")
    word_mask = s.str.extract(r"(?P<num>-?\d+(?:\.\d+)?)\s*(hours|hour|hrs|h)", flags=re.IGNORECASE)
    hours = hours.fillna(pd.to_numeric(word_mask["num"], errors="coerce"))

    # 4) Timestamps completos -> horas desde o menor timestamp válido
    dt_values = pd.to_datetime(s, errors="coerce")
    if dt_values.notna().any():
        base = dt_values.min()
        hours = hours.fillna((dt_values - base).dt.total_seconds() / 3600)

    return hours


def parse_time_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col, new_col in [("first_response_time", "first_response_hours"), ("time_to_resolution", "time_to_resolution_hours")]:
        if col in df.columns:
            df[new_col] = _series_to_hours(df[col])
        else:
            df[new_col] = np.nan
            print(f"[WARN] Coluna {col} não encontrada; preenchido com NaN.")
    return df


@dataclass
class AnalysisOutputs:
    operational_summary: Dict[str, object]
    bottlenecks: Dict[Tuple[str, ...], pd.DataFrame]
    critical_groups: pd.DataFrame
    satisfaction: Dict[str, object]
    waste: Dict[str, object]
    qualitative: List[Dict[str, object]]


def run_operational_summary(df: pd.DataFrame) -> Dict[str, object]:
    summary: Dict[str, object] = {}
    summary["total_tickets"] = len(df)
    for col in ["ticket_channel", "ticket_type", "ticket_priority", "ticket_status"]:
        if col in df.columns:
            summary[f"by_{col}"] = df[col].value_counts().sort_values(ascending=False)

    summary["frt_mean"] = df["first_response_hours"].mean()
    summary["frt_median"] = df["first_response_hours"].median()
    summary["ttr_mean"] = df["time_to_resolution_hours"].mean()
    summary["ttr_median"] = df["time_to_resolution_hours"].median()
    summary["satisfaction_mean"] = df["customer_satisfaction_rating"].mean()

    print("[INFO] Visão geral:")
    print(f" - Tickets: {summary['total_tickets']}")
    print(f" - FRT média/mediana (h): {summary['frt_mean']:.2f} / {summary['frt_median']:.2f}")
    print(f" - TTR média/mediana (h): {summary['ttr_mean']:.2f} / {summary['ttr_median']:.2f}")
    print(f" - Satisfação média: {summary['satisfaction_mean']:.2f}")

    return summary


def _plot_bar(df: pd.DataFrame, x: str, y: str, title: str, path: Path):
    plt.figure(figsize=(10, 5))
    ax = sns.barplot(data=df, x=x, y=y, hue=None)
    ax.set_title(title)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def run_bottleneck_analysis(df: pd.DataFrame) -> Tuple[Dict[Tuple[str, ...], pd.DataFrame], pd.DataFrame]:
    results: Dict[Tuple[str, ...], pd.DataFrame] = {}
    critical_frames = []
    base = df[df["time_to_resolution_hours"].notna()].copy()
    groupings: List[List[str]] = [
        ["ticket_channel"],
        ["ticket_type"],
        ["ticket_priority"],
        ["ticket_channel", "ticket_type"],
        ["ticket_type", "ticket_priority"],
        ["ticket_channel", "ticket_type", "ticket_priority"],
    ]

    for cols in groupings:
        if not set(cols).issubset(base.columns):
            continue
        agg = (
            base.groupby(cols)
            .agg(
                volume=("ticket_id", "count"),
                frt_mean=("first_response_hours", "mean"),
                frt_median=("first_response_hours", "median"),
                ttr_mean=("time_to_resolution_hours", "mean"),
                ttr_median=("time_to_resolution_hours", "median"),
                satisfaction_mean=("customer_satisfaction_rating", "mean"),
            )
            .reset_index()
        )
        agg = agg.sort_values("ttr_median", ascending=False)
        results[tuple(cols)] = agg

        vol_threshold = agg["volume"].median()
        crit = agg[(agg["volume"] >= vol_threshold) & (agg["ttr_median"] >= agg["ttr_median"].quantile(0.75))]
        critical_frames.append(crit.assign(group=" + ".join(cols)))

        top_plot = agg.head(8)
        filename = OUTPUT_DIR / f"bottleneck_{'_'.join(cols)}.png"
        _plot_bar(top_plot, x=cols[-1], y="ttr_median", title=f"Mediana de TTR por {' + '.join(cols)} (h)", path=filename)

    critical_df = pd.concat(critical_frames, ignore_index=True) if critical_frames else pd.DataFrame()
    print(f"[INFO] Gargalos identificados: {len(critical_df)} grupos críticos")
    return results, critical_df


def run_satisfaction_analysis(df: pd.DataFrame) -> Dict[str, object]:
    sat: Dict[str, object] = {}
    for col in ["ticket_channel", "ticket_type", "ticket_priority", "ticket_status"]:
        if col in df.columns:
            grp = (
                df.groupby(col)
                .agg(mean_satisfaction=("customer_satisfaction_rating", "mean"), volume=("ticket_id", "count"))
                .reset_index()
                .sort_values("mean_satisfaction", ascending=False)
            )
            sat[col] = grp
            filename = OUTPUT_DIR / f"satisfaction_{col}.png"
            _plot_bar(grp, x=col, y="mean_satisfaction", title=f"Satisfação média por {col}", path=filename)

    # Correlações com tempos
    corr_frt = df[["customer_satisfaction_rating", "first_response_hours"]].dropna().corr(method="spearman").iloc[0, 1]
    corr_ttr = df[["customer_satisfaction_rating", "time_to_resolution_hours"]].dropna().corr(method="spearman").iloc[0, 1]
    sat["corr_frt"] = corr_frt
    sat["corr_ttr"] = corr_ttr

    plt.figure(figsize=(6, 5))
    sns.regplot(data=df, x="time_to_resolution_hours", y="customer_satisfaction_rating", scatter_kws={"alpha": 0.3})
    plt.title("Satisfação vs Tempo de resolução")
    plt.xlabel("Tempo de resolução (h)")
    plt.ylabel("Satisfação")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "satisfaction_vs_resolution.png")
    plt.close()

    print(f"[INFO] Correlação (Spearman) satisfação ~ FRT: {corr_frt:.3f}")
    print(f"[INFO] Correlação (Spearman) satisfação ~ TTR: {corr_ttr:.3f}")
    return sat


def run_waste_analysis(df: pd.DataFrame) -> Dict[str, object]:
    base = df[df["time_to_resolution_hours"].notna()].copy()
    if base.empty:
        return {"total_hours": 0, "recoverable_hours": 0, "by_group": pd.DataFrame(), "benchmark": np.nan}

    group_cols = ["ticket_channel", "ticket_type", "ticket_priority"]
    agg = (
        base.groupby(group_cols)
        .agg(volume=("ticket_id", "count"), ttr_median=("time_to_resolution_hours", "median"), ttr_mean=("time_to_resolution_hours", "mean"))
        .reset_index()
    )
    benchmark = agg["ttr_median"].quantile(0.25)
    agg["excess_per_ticket"] = (agg["ttr_median"] - benchmark).clip(lower=0)
    agg["recoverable_hours"] = agg["excess_per_ticket"] * agg["volume"]

    total_hours = base["time_to_resolution_hours"].sum()
    recoverable_hours = agg["recoverable_hours"].sum()

    top_waste = agg.sort_values("recoverable_hours", ascending=False)
    _plot_bar(top_waste.head(10), x="ticket_channel", y="recoverable_hours", title="Desperdício recuperável por canal (h)", path=OUTPUT_DIR / "waste_by_channel.png")

    print(f"[INFO] Horas totais consumidas (TTR): {total_hours:.1f}")
    print(f"[INFO] Horas excedentes estimadas (benchmark P25 mediana): {recoverable_hours:.1f}")

    return {
        "total_hours": total_hours,
        "recoverable_hours": recoverable_hours,
        "by_group": top_waste,
        "benchmark": benchmark,
    }


def run_qualitative_examples(df: pd.DataFrame, critical_df: pd.DataFrame) -> List[Dict[str, object]]:
    text_cols = ["ticket_subject", "ticket_description", "resolution"]
    for col in text_cols:
        if col not in df.columns:
            print(f"[WARN] Coluna de texto ausente: {col}")
            return []

    if critical_df.empty:
        return []

    examples = []
    top_groups = critical_df.sort_values(["ttr_median", "volume"], ascending=[False, False]).head(3)
    for _, row in top_groups.iterrows():
        filters = []
        for col in ["ticket_channel", "ticket_type", "ticket_priority"]:
            if col in critical_df.columns and pd.notna(row.get(col)):
                filters.append((col, row[col]))
        subset = df.copy()
        for col, val in filters:
            subset = subset[subset[col] == val]
        sample = subset[text_cols + ["time_to_resolution_hours"]].dropna().sort_values("time_to_resolution_hours", ascending=False).head(3)
        examples.append({
            "filters": filters,
            "rows": sample.to_dict(orient="records"),
        })
    return examples


def _df_to_markdown_table(df: pd.DataFrame, max_rows: int = 8) -> str:
    if df.empty:
        return "(sem dados)"
    limited = df.head(max_rows)
    return "\n" + limited.to_string(index=False) + "\n"


def export_markdown_summary(
    summary: Dict[str, object],
    critical_df: pd.DataFrame,
    satisfaction: Dict[str, object],
    waste: Dict[str, object],
    qualitative: List[Dict[str, object]],
    path: Path,
) -> None:
    key_points: List[str] = []

    if not critical_df.empty:
        top = critical_df.sort_values(["ttr_median", "volume"], ascending=[False, False]).iloc[0]
        dims = [str(top[c]) for c in ["ticket_channel", "ticket_type", "ticket_priority"] if c in critical_df.columns and pd.notna(top[c])]
        key_points.append(
            f"Gargalo mais crítico (comparativo): {' / '.join(dims)} com mediana de TTR {top['ttr_median']:.1f} h e volume {int(top['volume'])}."
        )

    if satisfaction.get("corr_ttr") is not None:
        corr = satisfaction["corr_ttr"]
        key_points.append(
            f"Não há associação monotônica relevante entre satisfação e TTR/FRT (Spearman TTR {corr:.2f}, FRT {satisfaction.get('corr_frt', np.nan):.2f}); diferenças aparecem mais entre segmentos."
        )

    for col in ["ticket_channel", "ticket_type", "ticket_priority"]:
        grp = satisfaction.get(col)
        if grp is not None and not grp.empty:
            worst = grp.sort_values("mean_satisfaction").iloc[0]
            key_points.append(f"Pior satisfação média em {col}: {worst[col]} ({worst['mean_satisfaction']:.2f}).")
            break

    if waste.get("recoverable_hours") is not None:
        key_points.append(
            f"Desperdício comparativo estimado: {waste['recoverable_hours']:.1f} h sobre {waste['total_hours']:.1f} h totais, usando benchmark interno P25 (proxy, não SLA real)."
        )

    md_lines: List[str] = []
    md_lines.append("# Diagnóstico Operacional - Challenge 002")
    md_lines.append("")
    md_lines.append("## Metodologia")
    md_lines.append(
        "1) Padronização de colunas e limpeza de nulos; "
        "2) Conversão de tempos a partir de timestamps para proxies em horas relativas ao menor registro (comparação entre grupos, não SLA absoluto); "
        "3) Análises de volume, TTR/FRT e satisfação por canal/tipo/prioridade; "
        "4) Detecção de gargalos (mediana de TTR + volume); "
        "5) Estimativa comparativa de desperdício versus benchmark interno P25; "
        "6) Amostragem qualitativa apenas para ilustração, dada a baixa confiabilidade semântica dos textos."
    )

    md_lines.append("")
    md_lines.append("## Principais achados")
    for i, point in enumerate(key_points[:5], 1):
        md_lines.append(f"- {point}")

    md_lines.append("")
    md_lines.append("## Gargalos operacionais")
    if not critical_df.empty:
        md_lines.append("Grupos com alto volume e TTR acima do P75 das respectivas distribuições:")
        md_lines.append("```")
        md_lines.append(_df_to_markdown_table(critical_df[[c for c in critical_df.columns if c not in {'group'}]], max_rows=10))
        md_lines.append("```")
    else:
        md_lines.append("Nenhum gargalo crítico identificado pelo critério adotado.")

    md_lines.append("")
    md_lines.append("## Impacto na satisfação")
    md_lines.append(
        f"Correlação (Spearman) satisfação ~ FRT: {satisfaction.get('corr_frt', np.nan):.2f}; satisfação ~ TTR: {satisfaction.get('corr_ttr', np.nan):.2f}. "
        "As correlações são próximas de zero, indicando ausência de associação monotônica relevante; diferenças de satisfação aparecem mais entre segmentos operacionais."
    )
    for col in ["ticket_channel", "ticket_type", "ticket_priority", "ticket_status"]:
        grp = satisfaction.get(col)
        if grp is not None and not grp.empty:
            md_lines.append(f"\n**Satisfação média por {col}:**")
            md_lines.append("```")
            md_lines.append(_df_to_markdown_table(grp[[col, "mean_satisfaction", "volume"]]))
            md_lines.append("```")

    md_lines.append("")
    md_lines.append("## Desperdício operacional (horas)")
    md_lines.append(
        f"Benchmark interno (comparativo): mediana P25 dos grupos ({waste.get('benchmark', np.nan):.2f} h). "
        f"Horas totais consumidas (proxy TTR): {waste.get('total_hours', 0):.1f}. "
        f"Horas excedentes recuperáveis (proxy comparativa): {waste.get('recoverable_hours', 0):.1f}."
    )
    by_group = waste.get("by_group")
    if by_group is not None and not by_group.empty:
        md_lines.append("Top grupos por desperdício recuperável:")
        md_lines.append("```")
        md_lines.append(_df_to_markdown_table(by_group[["ticket_channel", "ticket_type", "ticket_priority", "ttr_median", "volume", "recoverable_hours"]]))
        md_lines.append("```")

    md_lines.append("")
    md_lines.append("## Leitura qualitativa")
    md_lines.append(
        "Os campos textuais apresentam baixo sinal semântico (muitos placeholders/sentenças genéricas). "
        "Servem apenas como ilustração do ruído e não sustentam inferências causais."
    )
    if qualitative:
        for i, block in enumerate(qualitative, 1):
            filters = ", ".join([f"{c}={v}" for c, v in block["filters"]])
            md_lines.append(f"### Amostras do grupo {i}: {filters}")
            for row in block["rows"]:
                md_lines.append("- Assunto (ruidoso): " + str(row.get("ticket_subject")))
                md_lines.append("  - Descrição (ilustrativa): " + textwrap.shorten(str(row.get("ticket_description")), width=160, placeholder="...") )
                md_lines.append("  - Resolução (ilustrativa): " + textwrap.shorten(str(row.get("resolution")), width=160, placeholder="...") )
                md_lines.append("  - TTR (h) proxy: {:.1f}".format(row.get("time_to_resolution_hours", float("nan"))))
    else:
        md_lines.append("Sem exemplos adicionais; texto não confiável para conclusões.")

    md_lines.append("")
    md_lines.append("## Limitações")
    md_lines.append("- TTR/FRT são proxies derivadas de timestamps relativos; não representam duração operacional exata ou SLA real.")
    md_lines.append("- Ratings ausentes em grande parte da base reduzem a confiança das associações de satisfação.")
    md_lines.append("- Desperdício é estimativa comparativa baseada em benchmark interno (P25); não é mensuração financeira ou de esforço real.")

    path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[INFO] Resumo markdown salvo em {path}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df_raw = load_data()
    df = clean_data(df_raw)
    df = parse_time_columns(df)

    operational_summary = run_operational_summary(df)
    bottlenecks, critical_df = run_bottleneck_analysis(df)
    satisfaction = run_satisfaction_analysis(df)
    waste = run_waste_analysis(df)
    qualitative = run_qualitative_examples(df, critical_df)

    export_markdown_summary(
        summary=operational_summary,
        critical_df=critical_df,
        satisfaction=satisfaction,
        waste=waste,
        qualitative=qualitative,
        path=Path(__file__).resolve().parent / "diagnostic_summary.md",
    )

    print(f"[OK] Análise concluída. Arquivos gerados em {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
