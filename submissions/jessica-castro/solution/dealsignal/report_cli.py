"""
DealSignal — CLI Report Generator

Gera um relatório priorizado (CSV ou PDF) diretamente pelo terminal,
sem precisar abrir o Streamlit.

Uso:
    python report_cli.py                          # top 20, CSV
    python report_cli.py --top 50 --format pdf    # top 50, PDF
    python report_cli.py --agent "João Silva"     # filtra por vendedor
    python report_cli.py --office "SP" --manager "Ana" --top 10 --format pdf
    python report_cli.py --rating AAA AA          # filtra por rating(s)
    python report_cli.py --output relatorio.csv   # nome customizado
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from config.constants import RATING_ORDER
from utils.report import generate_csv, generate_pdf, make_csv_filename, make_pdf_filename


# ── Data loading (sem Streamlit) ──────────────────────────────────────────────

def _load_results() -> pd.DataFrame:
    path = ROOT / "data" / "results.csv"
    if not path.exists():
        print("❌  data/results.csv não encontrado. Execute: python run_pipeline.py")
        sys.exit(1)
    df = pd.read_csv(path)
    df["win_probability"]  = pd.to_numeric(df["win_probability"],  errors="coerce")
    df["expected_revenue"] = pd.to_numeric(df["expected_revenue"], errors="coerce")
    df["effective_value"]  = pd.to_numeric(df["effective_value"],  errors="coerce")
    return df


def _load_metadata() -> dict:
    path = ROOT / "model" / "artifacts" / "metadata.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


# ── Filter + sort ─────────────────────────────────────────────────────────────

def _apply_filters(
    df: pd.DataFrame,
    office: Optional[str],
    manager: Optional[str],
    agent: Optional[str],
    ratings: Optional[List[str]],
    top: int,
) -> pd.DataFrame:
    if office:
        df = df[df["office"].str.lower() == office.lower()]
    if manager:
        df = df[df["manager"].str.lower() == manager.lower()]
    if agent:
        df = df[df["sales_agent"].str.lower() == agent.lower()]
    if ratings:
        df = df[df["deal_rating"].isin(ratings)]

    df = df.sort_values("expected_revenue", ascending=False).reset_index(drop=True)
    return df.head(top)


# ── KPIs ─────────────────────────────────────────────────────────────────────

def _build_kpis(df: pd.DataFrame) -> dict:
    total_pipeline  = df["effective_value"].sum()
    total_revenue   = df["expected_revenue"].sum()
    avg_prob        = df["win_probability"].mean()
    priority_count  = int(df["deal_rating"].isin(["AAA", "AA"]).sum())

    def _fmt_m(v: float) -> str:
        return f"R$ {v / 1_000_000:.1f}M".replace(".", ",")

    return {
        "Pipeline Total":    _fmt_m(total_pipeline),
        "Receita Esperada":  _fmt_m(total_revenue),
        "Prob. Média":       f"{avg_prob * 100:.1f}%",
        "Deals":             str(len(df)),
        "Prioritários (AAA+AA)": str(priority_count),
    }


# ── Active filters dict ───────────────────────────────────────────────────────

def _active_filters(office, manager, agent, ratings, top) -> dict:  # type: ignore[override]
    f = {}
    if office:
        f["Escritório"] = office
    if manager:
        f["Manager"] = manager
    if agent:
        f["Vendedor"] = agent
    if ratings:
        f["Rating"] = ", ".join(ratings)
    f["Top"] = str(top)
    return f


# ── Print summary to stdout ───────────────────────────────────────────────────

def _print_summary(df: pd.DataFrame, kpis: dict, filters: dict) -> None:
    print("\n" + "─" * 60)
    print("  DealSignal — Relatório Priorizado")
    print("─" * 60)

    if filters:
        print("  Filtros:", "  |  ".join(f"{k}: {v}" for k, v in filters.items()))
        print()

    print("  KPIs")
    for k, v in kpis.items():
        print(f"    {k:<25} {v}")
    print()

    print(f"  Top {len(df)} Deals")
    print(f"  {'#':<4} {'Rating':<8} {'Conta':<30} {'Produto':<22} {'Rec. Esperada':>14}  {'Prob':>6}")
    print("  " + "-" * 90)
    for i, row in df.iterrows():
        rev = row.get("expected_revenue", 0)
        rev_str = f"R$ {rev:>10,.0f}" if pd.notna(rev) else "—"
        prob = row.get("win_probability", 0)
        prob_str = f"{prob * 100:.0f}%" if pd.notna(prob) else "—"
        conta   = str(row.get("account", "—"))[:30]
        produto = str(row.get("product", "—"))[:22]
        rating  = str(row.get("deal_rating", "—"))
        print(f"  {i+1:<4} {rating:<8} {conta:<30} {produto:<22} {rev_str}  {prob_str:>6}")

    print("─" * 60 + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="DealSignal — Gerador de relatório priorizado via CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--office",  type=str, default=None, help="Filtrar por escritório")
    parser.add_argument("--manager", type=str, default=None, help="Filtrar por manager")
    parser.add_argument("--agent",   type=str, default=None, help="Filtrar por vendedor")
    parser.add_argument("--rating",  type=str, nargs="+", metavar="RATING",
                        choices=RATING_ORDER, default=None,
                        help=f"Filtrar por rating(s): {', '.join(RATING_ORDER)}")
    parser.add_argument("--top",     type=int, default=20, help="Número de deals (padrão: 20)")
    parser.add_argument("--format",  type=str, choices=["csv", "pdf"], default="csv",
                        help="Formato do relatório: csv ou pdf (padrão: csv)")
    parser.add_argument("--output",  type=str, default=None,
                        help="Nome do arquivo de saída (padrão: gerado automaticamente)")
    parser.add_argument("--no-print", action="store_true",
                        help="Não exibir resumo no terminal")
    args = parser.parse_args()

    df       = _load_results()
    metadata = _load_metadata()

    filters  = _active_filters(args.office, args.manager, args.agent, args.rating, args.top)
    filtered = _apply_filters(df, args.office, args.manager, args.agent, args.rating, args.top)

    if filtered.empty:
        print("⚠️   Nenhum deal encontrado com os filtros informados.")
        sys.exit(0)

    kpis = _build_kpis(filtered)

    if not args.no_print:
        _print_summary(filtered, kpis, filters)

    # Generate file
    if args.format == "csv":
        data     = generate_csv(filtered)
        filename = args.output or make_csv_filename(filters)
        Path(filename).write_bytes(data)
        print(f"✅  CSV salvo: {filename}  ({len(filtered)} deals)")

    else:
        data     = generate_pdf(filtered, kpis, filters, metadata)
        filename = args.output or make_pdf_filename(filters)
        Path(filename).write_bytes(data)
        print(f"✅  PDF salvo: {filename}  ({len(filtered)} deals)")


if __name__ == "__main__":
    main()
