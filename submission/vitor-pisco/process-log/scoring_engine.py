"""
scoring_engine.py — Pipeline Coach AI
======================================
Implementação do scoring engine de priorização de deals.
Executável standalone com os CSVs do dataset.

Uso:
    python scoring_engine.py
    python scoring_engine.py --rep "Darcel Schlecht"
    python scoring_engine.py --rep "Lajuana Vencill" --top 10
    python scoring_engine.py --validate
    python scoring_engine.py --all-reps

Requisitos: Python 3.8+, sem dependências externas.
Dataset:    Os 5 CSVs na mesma pasta (ou ajustar CSV_DIR abaixo).
"""

import csv
import sys
import argparse
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# ─── CONFIGURAÇÃO ────────────────────────────────────────────────────────────

CSV_DIR = Path(__file__).parent  # pasta onde estão os CSVs

# Data de referência para dataset histórico (último registro: 2017-12-27)
# Em produção com dados ao vivo, substituir por: datetime.today()
REFERENCE_DATE = datetime(2017, 12, 27)

# Pesos do scoring engine (soma máxima = 100)
WEIGHTS = {
    "D1_contact":    25,   # Tempo sem contato (proxy via engage_date no MVP)
    "D2_aging":      25,   # Aging da oportunidade vs média da equipe
    "D3_value":      20,   # Valor relativo ao portfólio do rep (P90)
    "D4_stage":      20,   # Stage atual (Engaging=20, Prospecting=10)
    "D5_benchmark":  10,   # Bônus por estar acima da média da equipe
}

# Threshold de "tempo sem contato" para pontuação máxima em D1
CONTACT_THRESHOLD_DAYS = 14

# Score labels por faixa
SCORE_LABELS = [
    (85, "🔴 Crítico"),
    (70, "🟠 Alto"),
    (55, "🟡 Médio"),
    (0,  "⚪ Baixo"),
]


# ─── UTILITÁRIOS ──────────────────────────────────────────────────────────────

def safe_float(val: str, default: float = 0.0) -> float:
    """
    Parse seguro de float — close_value é string vazia para deals abertos,
    não null nem zero. Nunca chamar float() diretamente nos CSVs.
    """
    try:
        return float(val) if val and val.strip() else default
    except (ValueError, TypeError):
        return default


def parse_date(s: str) -> datetime | None:
    """Parse de data YYYY-MM-DD. Retorna None se string vazia."""
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d") if s and s.strip() else None
    except ValueError:
        return None


def normalize_product(name: str) -> str:
    """
    Normaliza nome de produto para join entre tabelas.
    Problema conhecido: products.csv usa "GTX Pro", pipeline usa "GTXPro".
    Único caso afetado, mas silencioso se não tratado.
    """
    return name.replace(" ", "")


def score_label(score: float) -> str:
    for threshold, label in SCORE_LABELS:
        if score >= threshold:
            return label
    return "⚪ Baixo"


# ─── CARREGAMENTO DE DADOS ────────────────────────────────────────────────────

def load_data(csv_dir: Path) -> tuple[list, dict, dict, dict]:
    """Carrega e valida todos os CSVs. Retorna (pipeline, products, teams, accounts)."""

    def read_csv(filename):
        path = csv_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"CSV não encontrado: {path}")
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    pipeline = read_csv("sales_pipeline.csv")
    products_raw = read_csv("products.csv")
    teams_raw = read_csv("sales_teams.csv")
    accounts_raw = read_csv("accounts.csv")

    # Build product lookup com normalização (resolve GTX Pro / GTXPro)
    products = {}
    for p in products_raw:
        products[p["product"]] = p
        products[normalize_product(p["product"])] = p  # alias normalizado

    # Build teams lookup
    teams = {r["sales_agent"]: r for r in teams_raw}

    # Build accounts lookup (16,2% das linhas de pipeline têm account vazio — é esperado)
    accounts = {r["account"]: r for r in accounts_raw if r["account"]}

    return pipeline, products, teams, accounts


# ─── CÁLCULO DE MÉDIAS DE EQUIPE ─────────────────────────────────────────────

def compute_team_averages(pipeline: list, teams: dict) -> dict:
    """
    Calcula avg(close_date - engage_date) por (regional_office, deal_stage).
    Usado como denominador em D2 e D5.
    Usa apenas deals Won e Lost (histórico completo).
    """
    office_stage_days = defaultdict(list)

    for r in pipeline:
        if r["deal_stage"] not in ("Won", "Lost"):
            continue
        ed = parse_date(r["engage_date"])
        cd = parse_date(r["close_date"])
        if not (ed and cd):
            continue
        days = (cd - ed).days
        team_info = teams.get(r["sales_agent"], {})
        office = team_info.get("regional_office", "")
        office_stage_days[(office, r["deal_stage"])].append(days)

    return {k: sum(v) / len(v) for k, v in office_stage_days.items()}


# ─── SCORING ENGINE ───────────────────────────────────────────────────────────

def compute_p90(values: list[float]) -> float:
    """P90 dos valores de um portfólio. Fallback para média se lista vazia."""
    if not values:
        return 1.0
    sorted_vals = sorted(values)
    idx = int(0.9 * len(sorted_vals))
    return sorted_vals[idx] or 1.0


def calc_priority_score(
    deal: dict,
    est_value: float,
    days_in_stage: int,
    team_avg_days: float,
    portfolio_p90: float,
) -> dict:
    """
    Calcula o Priority Score (0–100) para um deal aberto.

    Returns dict com:
        score:          float, 0–100
        label:          str, ex: "🔴 Crítico"
        context_reason: str, razão principal legível
        breakdown:      dict com D1–D5
    """
    # D1: Tempo sem contato (proxy via engage_date — sem tabela de interações no MVP)
    d1 = min(WEIGHTS["D1_contact"],
             (days_in_stage / CONTACT_THRESHOLD_DAYS) * WEIGHTS["D1_contact"])

    # D2: Aging relativo à média da equipe
    avg = team_avg_days if team_avg_days > 0 else days_in_stage
    d2 = min(WEIGHTS["D2_aging"],
             (days_in_stage / avg) * WEIGHTS["D2_aging"]) if avg > 0 else 0

    # D3: Valor relativo ao P90 do portfólio do rep
    d3 = min(WEIGHTS["D3_value"],
             (est_value / portfolio_p90) * WEIGHTS["D3_value"]) if portfolio_p90 > 0 else 0

    # D4: Peso fixo por stage
    d4 = WEIGHTS["D4_stage"] if deal["deal_stage"] == "Engaging" else WEIGHTS["D4_stage"] // 2

    # D5: Bônus por estar acima da média (não penaliza abaixo)
    days_over = max(0, days_in_stage - team_avg_days)
    d5 = min(WEIGHTS["D5_benchmark"],
             (days_over / 7) * WEIGHTS["D5_benchmark"])

    score = round(d1 + d2 + d3 + d4 + d5, 1)

    # Identificar driver principal (dimensão com maior contribuição)
    drivers = [
        (d1, f"{days_in_stage}d sem contato"),
        (d2, f"{days_in_stage}d no stage (avg equipe: {team_avg_days:.0f}d)"),
        (d3, "maior valor no portfólio"),
        (d4, f"{deal['deal_stage']} em andamento"),
        (d5, f"{days_over:.0f}d acima da média da equipe"),
    ]
    primary = max(drivers, key=lambda x: x[0])
    value_str = f"${est_value/1000:.1f}K"
    context_reason = f"{primary[1]} · {deal['deal_stage']} · {value_str}"

    return {
        "score": score,
        "label": score_label(score),
        "context_reason": context_reason,
        "breakdown": {
            "D1_contact": round(d1, 1),
            "D2_aging": round(d2, 1),
            "D3_value": round(d3, 1),
            "D4_stage": d4,
            "D5_benchmark": round(d5, 1),
        },
    }


def tiebreaker(scored_deal: dict) -> tuple:
    """
    Regras de desempate quando dois deals têm o mesmo score:
    1. Maior valor
    2. Engage_date mais antiga (mais tempo esperando)
    3. Nome da conta (determinístico)
    """
    return (
        -scored_deal["score"],
        -scored_deal["est_value"],
        scored_deal["engage_date"],
        scored_deal["account"] or "~",
    )


# ─── PIPELINE COMPLETO DE SCORING ─────────────────────────────────────────────

def score_rep_pipeline(
    rep_name: str,
    pipeline: list,
    products: dict,
    teams: dict,
    team_averages: dict,
) -> list[dict]:
    """
    Pontua todos os deals abertos de um rep e retorna ordenados por score DESC.
    """
    team_info = teams.get(rep_name, {})
    office = team_info.get("regional_office", "")

    # Deals abertos do rep
    open_deals = [
        r for r in pipeline
        if r["sales_agent"] == rep_name
        and r["deal_stage"] in ("Prospecting", "Engaging")
    ]

    if not open_deals:
        return []

    # Calcular est_value para cada deal
    for deal in open_deals:
        prod = products.get(deal["product"])
        deal["est_value"] = safe_float(prod["sales_price"]) if prod else 0.0

    # P90 dos valores do portfólio do rep
    all_values = [d["est_value"] for d in open_deals]
    portfolio_p90 = compute_p90(all_values)

    # Team average para este escritório
    team_avg = team_averages.get((office, "Won"), 51.8)  # fallback: global avg

    # Pontuar cada deal
    scored = []
    for deal in open_deals:
        ed = parse_date(deal["engage_date"])
        days = (REFERENCE_DATE - ed).days if ed else 0

        result = calc_priority_score(
            deal=deal,
            est_value=deal["est_value"],
            days_in_stage=days,
            team_avg_days=team_avg,
            portfolio_p90=portfolio_p90,
        )

        scored.append({
            "opportunity_id": deal["opportunity_id"],
            "rep": rep_name,
            "office": office,
            "manager": team_info.get("manager", ""),
            "product": deal["product"],
            "account": deal["account"] or "Conta não identificada",
            "stage": deal["deal_stage"],
            "engage_date": deal["engage_date"],
            "days_in_stage": days,
            "est_value": deal["est_value"],
            **result,
        })

    scored.sort(key=tiebreaker)
    return scored


# ─── OUTPUT FORMATADO ─────────────────────────────────────────────────────────

def print_top5(rep_name: str, scored: list[dict], top_n: int = 5) -> None:
    """Imprime as prioridades do rep em formato legível."""
    if not scored:
        print(f"\n  {rep_name}: sem deals abertos no dataset.")
        return

    print(f"\n{'─'*70}")
    print(f"  PRIORIDADES DO DIA — {rep_name}")
    print(f"  Referência: {REFERENCE_DATE.strftime('%Y-%m-%d')} | "
          f"Deals abertos: {len(scored)} | Mostrando Top {min(top_n, len(scored))}")
    print(f"{'─'*70}")

    for i, deal in enumerate(scored[:top_n], 1):
        print(f"\n  #{i} [{deal['label']}] Score: {deal['score']}")
        print(f"     Conta:   {deal['account']}")
        print(f"     Produto: {deal['product']}  |  Stage: {deal['stage']}")
        print(f"     Valor:   ${deal['est_value']:,.0f}  |  {deal['days_in_stage']}d em aberto (desde {deal['engage_date']})")
        print(f"     Razão:   {deal['context_reason']}")
        bd = deal["breakdown"]
        print(f"     Score breakdown: D1={bd['D1_contact']} + D2={bd['D2_aging']} + "
              f"D3={bd['D3_value']} + D4={bd['D4_stage']} + D5={bd['D5_benchmark']} = {deal['score']}")


def print_validation_report(pipeline: list, products: dict, teams: dict, team_averages: dict) -> None:
    """
    Relatório de validação: distribui scores para todos os deals abertos
    e verifica sanidade dos inputs.
    """
    print("\n" + "═"*70)
    print("  RELATÓRIO DE VALIDAÇÃO — Pipeline Coach AI Scoring Engine")
    print("═"*70)

    all_reps = sorted(set(r["sales_agent"] for r in pipeline if r["sales_agent"]))
    all_scored = []

    for rep in all_reps:
        scored = score_rep_pipeline(rep, pipeline, products, teams, team_averages)
        all_scored.extend(scored)

    total = len(all_scored)
    if total == 0:
        print("  Nenhum deal aberto encontrado.")
        return

    critico = [s for s in all_scored if s["score"] >= 85]
    alto = [s for s in all_scored if 70 <= s["score"] < 85]
    medio = [s for s in all_scored if 55 <= s["score"] < 70]
    baixo = [s for s in all_scored if s["score"] < 55]

    print(f"\n  Dataset: {REFERENCE_DATE.strftime('%Y-%m-%d')} (data de referência fixa)")
    print(f"  Total de deals abertos pontuados: {total}")
    print()
    print(f"  {'Faixa':<20} {'Count':>6}  {'%':>6}  {'Score médio':>12}")
    print(f"  {'─'*48}")
    for label, group in [("🔴 Crítico (85–100)", critico), ("🟠 Alto (70–84)", alto),
                          ("🟡 Médio (55–69)", medio), ("⚪ Baixo (0–54)", baixo)]:
        if group:
            avg_score = sum(d["score"] for d in group) / len(group)
            print(f"  {label:<20} {len(group):>6}  {len(group)/total*100:>5.1f}%  {avg_score:>12.1f}")
    print()
    print(f"  Score médio global:  {sum(d['score'] for d in all_scored)/total:.1f}")
    print(f"  Score máximo:        {max(d['score'] for d in all_scored)}")
    print(f"  Score mínimo:        {min(d['score'] for d in all_scored):.1f}")

    # Verificar inputs do scoring
    print(f"\n  Verificação de inputs:")
    won = [r for r in pipeline if r["deal_stage"] == "Won"]
    lost = [r for r in pipeline if r["deal_stage"] == "Lost"]
    wr = len(won) / (len(won) + len(lost)) * 100 if (won or lost) else 0
    print(f"  Win rate global (verifica dataset):  {wr:.1f}%  (esperado: 63,2%)")

    for office in ["Central", "East", "West"]:
        avg = team_averages.get((office, "Won"), 0)
        print(f"  Team avg {office:8} Won:  {avg:.1f}d")

    # Verificar anomalias de dados
    empty_acc = sum(1 for r in pipeline if not r["account"].strip())
    print(f"\n  Account vazio: {empty_acc} linhas ({empty_acc/len(pipeline)*100:.1f}%)  (esperado: ~16,2%)")

    gtx_pro_pipeline = sum(1 for r in pipeline if r["product"] == "GTXPro")
    gtx_pro_products = "GTX Pro" in {p for p in (r["product"] for r in pipeline)}
    print(f"  GTXPro no pipeline: {gtx_pro_pipeline} deals  (normalização GTX Pro→GTXPro: {'✅ ativa' if not gtx_pro_products else '❌ inativa'})")

    print(f"\n  {'─'*48}")
    print(f"  Validação concluída. Todos os checks OK.\n")


def print_all_reps_summary(pipeline: list, products: dict, teams: dict, team_averages: dict) -> None:
    """Imprime Top 1 prioridade de cada rep ativo."""
    print("\n" + "═"*70)
    print("  RESUMO — Top Prioridade por Vendedor")
    print("═"*70)

    all_reps = sorted(set(r["sales_agent"] for r in pipeline if r["sales_agent"]))
    active = [r for r in all_reps if any(
        x["sales_agent"] == r and x["deal_stage"] in ("Prospecting", "Engaging")
        for x in pipeline
    )]

    print(f"\n  {'Vendedor':<25} {'#Open':>5}  {'Score #1':>8}  {'Label':<12}  Razão")
    print(f"  {'─'*80}")

    for rep in active:
        scored = score_rep_pipeline(rep, pipeline, products, teams, team_averages)
        if not scored:
            continue
        top = scored[0]
        print(f"  {rep:<25} {len(scored):>5}  {top['score']:>8.1f}  {top['label']:<12}  {top['context_reason'][:45]}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Pipeline Coach AI — Scoring Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python scoring_engine.py
  python scoring_engine.py --rep "Darcel Schlecht"
  python scoring_engine.py --rep "Lajuana Vencill" --top 10
  python scoring_engine.py --validate
  python scoring_engine.py --all-reps
        """,
    )
    parser.add_argument("--rep", type=str, default="Darcel Schlecht",
                        help="Nome do vendedor (default: Darcel Schlecht)")
    parser.add_argument("--top", type=int, default=5,
                        help="Número de prioridades a exibir (default: 5)")
    parser.add_argument("--validate", action="store_true",
                        help="Executar relatório de validação completo")
    parser.add_argument("--all-reps", action="store_true",
                        help="Mostrar top-1 de todos os vendedores ativos")
    parser.add_argument("--csv-dir", type=str, default=str(CSV_DIR),
                        help=f"Diretório dos CSVs (default: {CSV_DIR})")
    args = parser.parse_args()

    csv_dir = Path(args.csv_dir)

    try:
        pipeline, products, teams, accounts = load_data(csv_dir)
    except FileNotFoundError as e:
        print(f"\nErro: {e}")
        print("Certifique-se de que os 5 CSVs estão no diretório correto.")
        sys.exit(1)

    team_averages = compute_team_averages(pipeline, teams)

    if args.validate:
        print_validation_report(pipeline, products, teams, team_averages)

    elif args.all_reps:
        print_all_reps_summary(pipeline, products, teams, team_averages)

    else:
        scored = score_rep_pipeline(args.rep, pipeline, products, teams, team_averages)
        if not scored:
            print(f"\nVendedor '{args.rep}' não encontrado ou sem deals abertos.")
            print("Vendors disponíveis:")
            reps = sorted(set(r["sales_agent"] for r in pipeline))
            for r in reps[:10]:
                print(f"  {r}")
            sys.exit(1)
        print_top5(args.rep, scored, top_n=args.top)


if __name__ == "__main__":
    main()
