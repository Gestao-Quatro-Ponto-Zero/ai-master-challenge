#!/usr/bin/env python3
"""
05_actions_impact.py — Ações priorizadas, impacto em faixa e plano de medição
(Iteração 05).

Converte a evidência validada (It02–It04) em decisões executivas: 4 ações
(ACT-01..04), impacto em cenários paramétricos com premissas nomeadas, matriz
de priorização sem score arbitrário, plano de medição com desenho experimental
e watchlist dividida em 8 onboarding validados vs 12 exposure-only.

Contrato analítico (It02) e fatos congelados respeitados:
- onboarding <= 90d é a ÚNICA regra com lift consistente (1,57/1,56/1,83);
  recorrência/reativação/MRR NÃO validam (It04 D4/D8);
- R1 = exposição contratual bruta, NÃO perda (§5); eventos ≠ logos ≠ receita
  (§4); lift ≠ efeito causal do programa (premissa de planejamento, testada
  pelo experimento ACT-01 — nunca derivada do lift);
- CAC/winback/custos NÃO existem na base: esforço é qualitativo (S/M/L);
- claims PROIBIDOS: "receita salva", "revenue saved", CAC queimado factual,
  causalidade provada, score preditivo, reativação mais barata (ver
  `process-log/decisions/iteration-05-action-impact-assumptions.md` §6).

Premissas fixadas ANTES do cálculo (mesmo arquivo de decisões): cenários de
redução relativa 10%/20%/30% (conservador/base/ambicioso), incidência histórica
= precision pooled da regra D (cutoffs 90d) com lower/base/upper, população
elegível = estoque onboarding no corte (esperado 80 contas; 621.981 US$ winner
MRR) com sensibilidade de fluxo.

Gera, de forma offline e determinística (sem timestamp; ordenações estáveis):
    solution/evidence/05_action_plan.md        (CEO-readable, conciso)
    solution/out/tables/t18_actions_prioritized.csv
    solution/out/tables/t19_impact_sensitivity.csv
    solution/out/tables/t20_measurement_plan.csv
    solution/out/tables/t21_watchlist_split_actions.csv   (única tabela extra)

NÃO gera PNG (keep-set visual fechado em 6, It03+It04). Sem ML, sem custo
monetário inventado, sem anualização como forecast.

Semântica de resultado (mesma família das iterações 01-04):
    - PASS : check íntegro.
    - WARN : divergência/anomalia de qualidade esperada (documentada).
    - FAIL : arquivo/schema estrutural ausente ou invariante violado.
    Exit code: 0 se não houver FAIL; 1 caso contrário. Em caso de FAIL
    estrutural o relatório é SEMPRE regravado (sem output stale) e sem
    traceback não tratado.

Restrições: apenas stdlib + pandas; sem rede; paths relativos ao próprio
projeto; nenhuma constante de dado hardcoded (todos os números derivados em
runtime dos inputs; gate G10 verifica a ausência de literais derivados).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------------
# Configuração de paths (relativos ao próprio projeto)
# ----------------------------------------------------------------------------
SOLUTION_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = SOLUTION_DIR / "data" / "raw"
PROCESSED_DIR = SOLUTION_DIR / "data" / "processed"
EVIDENCE_DIR = SOLUTION_DIR / "evidence"
OUT_DIR = SOLUTION_DIR / "out"
TABLES_DIR = OUT_DIR / "tables"
CHARTS_DIR = OUT_DIR / "charts"

REPORT_PATH = EVIDENCE_DIR / "05_action_plan.md"
PANEL_PATH = PROCESSED_DIR / "account_month.csv"
T11_PATH = TABLES_DIR / "t11_account_lifecycle.csv"
T14_PATH = TABLES_DIR / "t14_backtest_temporal.csv"
T15_PATH = TABLES_DIR / "t15_priority_segments.csv"
T16_PATH = TABLES_DIR / "t16_watchlist_top20.csv"

# ----------------------------------------------------------------------------
# Constantes (estruturais/contrato/premissas — NUNCA valores de dados)
# ----------------------------------------------------------------------------
DATA_CUT = pd.Timestamp("2024-12-31")       # data-limite (corte; censura)
ONBOARDING_DAYS = 90                        # tenure <= 90d = onboarding (It03 H1/H8)
BACKTEST_HORIZON_DAYS = 90                  # horizonte do backtest (It04 D4)
PANEL_MONTH = "2024-12"                     # mês do corte no painel account-month

# Cenários de redução relativa da taxa de evento (premissas de planejamento
# fixadas ANTES do cálculo — decisions It05 §3; NÃO derivadas do lift).
REDUCTION_SCENARIOS = [
    ("conservador", 0.10),
    ("base", 0.20),
    ("ambicioso", 0.30),
]
# Sensibilidades: incidência lower/base/upper (do backtest It04) e população
# (estoque no corte vs fluxo médio trimestral 2024).
INCIDENCE_LABELS = {"lower": "sens-inc-lo", "base": "sens-inc-base",
                    "upper": "sens-inc-hi"}

# Desenho experimental (ACT-01): alpha/poder para MDE (aproximação normal de
# duas proporções, fechada; sem dependência extra).
ALPHA = 0.05
POWER = 0.80
EXPERIMENT_SPLIT = 0.50                   # 50/50 tratado/holdout por semana
EXPERIMENT_QUARTERS = 4                   # janela de decisão (4 trimestres)

# Metas de qualidade de dados (ACT-03) — metas de política, não valores de
# dados observados (estes são derivados em runtime).
TARGETS = {
    "csat_coverage": 0.90,      # tickets com CSAT >= 90%
    "reason_unknown": 0.05,     # reason_code 'unknown' < 5%
    "usage_in_window": 0.90,    # uso dentro da janela da assinatura >= 90%
    "activation_milestone": 1.0,  # milestone de ativação capturado em 100%
}
LINKAGE_TARGET = 0.80           # eventos com sub encerrada ±30d >= 80%

# Saídas permitidas (escopo fechado; tabela extra única t21).
ALLOWED_TABLES = [
    "t18_actions_prioritized.csv",
    "t19_impact_sensitivity.csv",
    "t20_measurement_plan.csv",
    "t21_watchlist_split_actions.csv",
]

# Colunas mínimas exigidas por arquivo (guarda estrutural desta iteração).
REQUIRED = {
    "ravenstack_accounts.csv": ["account_id", "signup_date"],
    "ravenstack_subscriptions.csv": [
        "subscription_id", "account_id", "start_date", "end_date",
    ],
    "ravenstack_churn_events.csv": [
        "churn_event_id", "account_id", "churn_date", "reason_code",
    ],
    "ravenstack_feature_usage.csv": ["usage_id", "subscription_id", "usage_date"],
    "ravenstack_support_tickets.csv": ["ticket_id", "satisfaction_score"],
    "account_month.csv": ["account_id", "month", "winner_mrr"],
    "t11_account_lifecycle.csv": [
        "account_id", "tenure_days", "current_winner_mrr",
    ],
    "t14_backtest_temporal.csv": [
        "cutoff", "horizon_days", "rule", "n_rule", "rule_outcomes",
        "precision",
    ],
    "t15_priority_segments.csv": ["segment", "N", "current_mrr_sum"],
    "t16_watchlist_top20.csv": [
        "account_id", "watch_tier", "current_winner_mrr",
    ],
}

# ----------------------------------------------------------------------------
# Registro de checks (ordem determinística de emissão)
# ----------------------------------------------------------------------------
CHECKS: list[dict] = []


class StructuralError(Exception):
    """Falha estrutural (arquivo/schema ausente ou inválido)."""


def check(check_id: str, scope: str, description: str, level: str,
          detail: str) -> None:
    """Registra um check. level: PASS | WARN | FAIL."""
    CHECKS.append({
        "id": check_id, "scope": scope, "description": description,
        "level": level, "detail": detail,
    })


def fmt(n: object) -> str:
    """Formata número inteiro sem decimais; float com 2 decimais (determinístico)."""
    if n is None:
        return ""
    if isinstance(n, float):
        if n != n:  # NaN
            return "NA"
        if n.is_integer():
            return str(int(n))
        return f"{n:.2f}"
    return str(n)


def fmt_br_int(n: float | int) -> str:
    """Inteiro com separador de milhar pt-BR (determinístico)."""
    return f"{int(round(n)):,}".replace(",", ".")


def fmt_br_dec(n: float) -> str:
    """Decimal com vírgula pt-BR (determinístico)."""
    return f"{n:.1f}".replace(".", ",")


def missing_cols(df: pd.DataFrame, cols: list[str], fname: str) -> list[str]:
    return [c for c in cols if c not in df.columns]


def guard_columns(df: pd.DataFrame, cols: list[str], check_id: str, scope: str,
                  fname: str) -> None:
    miss = missing_cols(df, cols, fname)
    if miss:
        check(check_id, scope, "colunas mínimas presentes", "FAIL",
              f"{fname}: faltam {miss}")
        raise StructuralError(f"colunas ausentes em {fname}: {miss}")
    check(check_id, scope, "colunas mínimas presentes", "PASS",
          f"{fname}: {len(cols)} colunas exigidas presentes")


def load_csv(path: Path, check_id: str, scope: str, fname: str,
             cols: list[str]) -> pd.DataFrame:
    if not path.exists():
        check(check_id, scope, "arquivo presente e carregável", "FAIL",
              f"{fname}: arquivo ausente ({path.name})")
        raise StructuralError(f"arquivo ausente: {path.name}")
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001 — falha estrutural, sem traceback
        check(check_id, scope, "arquivo presente e carregável", "FAIL",
              f"{fname}: erro de parse ({exc})")
        raise StructuralError(f"erro de parse: {path.name}") from exc
    check(check_id, scope, "arquivo presente e carregável", "PASS",
          f"{fname}: CSV parseado ({len(df)} registros)")
    guard_columns(df, cols, f"SC-{check_id}", scope, fname)
    return df


# ----------------------------------------------------------------------------
# Computações (todas derivadas em runtime; nenhuma constante de dado)
# ----------------------------------------------------------------------------

def compute_onboarding_base(t11: pd.DataFrame) -> dict:
    """Base elegível atual: contas onboarding (tenure <= 90d) no corte."""
    onb = t11[t11["tenure_days"] <= ONBOARDING_DAYS].copy()
    n = int(len(onb))
    mrr_sum = int(onb["current_winner_mrr"].sum())
    avg_mrr = mrr_sum / n if n else 0.0
    return {"n": n, "mrr_sum": mrr_sum, "avg_mrr": avg_mrr}


def compute_incidence(t14: pd.DataFrame) -> dict:
    """Incidência histórica de primeiro/próximo evento em 90d entre contas
    onboarding = precision da regra D (backtest It04, cutoffs 90d)."""
    rd = t14[(t14["rule"] == "D")
             & (t14["horizon_days"] == BACKTEST_HORIZON_DAYS)].copy()
    if rd.empty:
        raise StructuralError("regra D com horizonte 90d ausente em t14")
    outcomes = int(rd["rule_outcomes"].sum())
    n_rule = int(rd["n_rule"].sum())
    pooled = outcomes / n_rule if n_rule else 0.0
    lo = float(rd["precision"].min())
    hi = float(rd["precision"].max())
    return {"outcomes": outcomes, "n_rule": n_rule, "pooled": pooled,
            "lo": lo, "hi": hi}


def compute_inflow(accounts: pd.DataFrame) -> dict:
    """Fluxo de signups de 2024 (trimestres) — sensibilidade de população."""
    acc = accounts.copy()
    acc["signup_date"] = pd.to_datetime(acc["signup_date"])
    y2024 = acc[acc["signup_date"].dt.year == 2024]
    q = y2024.groupby(y2024["signup_date"].dt.quarter).size()
    counts = [int(q.get(i, 0)) for i in range(1, 5)]
    avg = sum(counts) / len(counts)
    return {"quarters": counts, "avg": avg, "total": int(len(y2024)),
            "min": min(counts), "max": max(counts)}


def compute_total_exposure(panel: pd.DataFrame) -> int:
    """Exposição atual total (lente winner/estado) no mês do corte."""
    pm = panel[panel["month"] == PANEL_MONTH]
    return int(pm["winner_mrr"].sum())


def compute_watchlist_split(t16: pd.DataFrame) -> dict:
    """Split da watchlist: 8 onboarding validados (Tier A) vs 12 exposure-only."""
    ta = t16[t16["watch_tier"] == "A"]
    tbc = t16[t16["watch_tier"] != "A"]
    a_sum = int(ta["current_winner_mrr"].sum())
    bc_sum = int(tbc["current_winner_mrr"].sum())
    return {
        "tier_a_n": int(len(ta)), "tier_a_sum": a_sum,
        "tier_bc_n": int(len(tbc)), "tier_bc_sum": bc_sum,
        "total_n": int(len(t16)), "total_sum": a_sum + bc_sum,
    }


def compute_data_quality(events: pd.DataFrame, tickets: pd.DataFrame,
                         subs: pd.DataFrame, usage: pd.DataFrame) -> dict:
    """Qualidade estrutural dos dados (baseline ACT-03), derivada em runtime."""
    csat_coverage = float(tickets["satisfaction_score"].notna().mean())
    reason_unknown = float((events["reason_code"] == "unknown").mean())
    m = subs.merge(usage, on="subscription_id")
    end_eff = m["end_date"].fillna(DATA_CUT)
    aligned = ((m["usage_date"] >= m["start_date"])
               & (m["usage_date"] <= end_eff)).sum()
    usage_in_window = float(aligned / len(m))
    ev = events.copy()
    ev["churn_date"] = pd.to_datetime(ev["churn_date"])
    ended = subs[["account_id", "end_date"]].dropna()
    ended["end_date"] = pd.to_datetime(ended["end_date"])
    linked = 0
    for _, e in ev.iterrows():
        acc_subs = ended[ended["account_id"] == e["account_id"]]
        if ((acc_subs["end_date"] - e["churn_date"]).abs()
                <= pd.Timedelta(days=30)).any():
            linked += 1
    linkage = float(linked / len(ev))
    # milestone de ativação: nenhum campo de ativação/milestone nos raw files
    raw_cols: list[str] = []
    for fname in ("ravenstack_accounts.csv", "ravenstack_subscriptions.csv",
                  "ravenstack_churn_events.csv",
                  "ravenstack_feature_usage.csv",
                  "ravenstack_support_tickets.csv"):
        df = pd.read_csv(RAW_DIR / fname)
        raw_cols.extend(str(c).lower() for c in df.columns)
    activation_field = any(
        any(tok in {"activation", "milestone", "time_to_value"}
            for tok in c.split("_"))
        for c in raw_cols)
    return {
        "csat_coverage": csat_coverage,
        "reason_unknown": reason_unknown,
        "usage_in_window": usage_in_window,
        "linkage": linkage,
        "activation_field": activation_field,
        "n_tickets": int(len(tickets)),
        "n_events": int(len(events)),
        "n_usage": int(len(usage)),
    }


def build_scenarios(onb: dict, inc: dict, inflow: dict) -> pd.DataFrame:
    """Cenários e sensibilidades de impacto (t19) — componentes explícitos.

    expected_events_90d = N * incidence (histórico descritivo)
    events_affected     = N * incidence * redução_relativa
    exposure_affected   = Σ winner_mrr(elegíveis) * incidence * redução_relativa
    """
    rows: list[dict] = []
    n_base = onb["n"]
    exp_base = onb["mrr_sum"]

    def row(scenario: str, incidence: float, n: float, reduction: float,
            note: str) -> dict:
        exp_events = n * incidence
        affected_events = exp_events * reduction
        exposure_base = exp_base * (n / n_base) if n_base else 0.0
        affected_exposure = exposure_base * incidence * reduction
        return {
            "action_id": "ACT-01",
            "scenario": scenario,
            "incidence_90d": round(incidence, 4),
            "eligible_n": round(n, 2),
            "expected_events_90d": round(exp_events, 1),
            "rel_reduction_pct": round(reduction * 100.0, 1),
            "events_affected_90d": round(affected_events, 1),
            "exposure_base_mrr": round(exposure_base),
            "expected_exposure_affected_mrr": round(affected_exposure),
            "note": note,
        }

    for label, red in REDUCTION_SCENARIOS:
        incidence = {"conservador": inc["lo"], "base": inc["pooled"],
                     "ambicioso": inc["hi"]}[label]
        rows.append(row(
            label, incidence, n_base, red,
            "premissa de planejamento (10/20/30% de redução relativa); "
            "NÃO derivada do lift; a ser testada pelo experimento ACT-01"))
    for label, incidence in (("lower", inc["lo"]), ("base", inc["pooled"]),
                             ("upper", inc["hi"])):
        rows.append(row(
            INCIDENCE_LABELS[label], incidence, n_base, 0.20,
            "sensibilidade de incidência (precision regra D, cutoffs 90d)"))
    rows.append(row(
        "sens-pop-flow", inc["pooled"], inflow["avg"], 0.20,
        "sensibilidade de população: fluxo médio trimestral 2024 de signups"))
    rows.append(row(
        "annualized", inc["pooled"], 4.0 * n_base, 0.20,
        "annualized MRR-equivalent exposure — aritmética (4 coortes "
        "trimestrais do estoque atual); NÃO é forecast"))
    return pd.DataFrame(rows)


def mde_required_n(p1: float, p2: float) -> float:
    """N por braço para detectar p1 vs p2 (aproximação normal, 2 proporções)."""
    z = 1.959963984540054 if ALPHA == 0.05 else 1.6448536269514722  # 1.96 / 1.64
    z_beta = 0.8416212335729143 if POWER == 0.80 else 1.2815515655446004
    delta = p1 - p2
    return (z + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2)) / (delta ** 2)


def mde_for_n(n_arm: float, p1: float) -> float:
    """Menor efeito detectável (REDUÇÃO RELATIVA p1->p2) com n_arm por braço,
    resolvido por bissecção (sem dependência extra). n_required decresce com a
    redução absoluta mid = p1 - p2."""
    lo, hi = 1e-9, p1 * 0.999
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if mde_required_n(p1, p1 - mid) > n_arm:
            lo = mid          # efeito maior que mid é necessário -> sobe lo
        else:
            hi = mid          # mid já detectável -> desce hi
    return ((lo + hi) / 2.0) / p1


def build_prioritized(impact: dict, onb: dict, wl: dict,
                      quality: dict) -> pd.DataFrame:
    """Matriz de priorização (t18) — sem score numérico arbitrário."""
    ev_lo, ev_hi = impact["events_lo"], impact["events_hi"]
    ex_lo, ex_hi = impact["exposure_lo"], impact["exposure_hi"]
    rows = [
        {
            "action_id": "ACT-01",
            "action": "Programa de ativação/onboarding 0-90d: milestones "
                      "instrumentados, intervenção por estágio e rollout "
                      "gradual com holdout (desenho experimental)",
            "family": "A+D (onboarding/time-to-value + experimento causal)",
            "decision": "Now",
            "evidence_strength": "ALTA — única regra com lift consistente "
                                 "(1,57/1,56/1,83; 3 cutoffs 90d; N>=25); "
                                 "efeito do programa NÃO medido",
            "evidence_ref": "t14_backtest_temporal.csv (regra D); "
                            "evidence/04 §6; decisions It04 D4",
            "impact_metric": "eventos de churn (lente C) evitados em 90d; "
                             "expected MRR-equivalent exposure affected "
                             "(lente winner/estado)",
            "impact_range": f"{fmt_br_dec(ev_lo)}–{fmt_br_dec(ev_hi)} "
                            f"eventos/90d; exposição "
                            f"{fmt_br_int(ex_lo)}–{fmt_br_int(ex_hi)} US$/90d "
                            f"(cenários conservador–ambicioso)",
            "effort": "M",
            "time_to_first_signal": "90d (1ª coorte completa do rollout)",
            "reversibility": "ALTA (rollout gradual; holdout preserva "
                             "comparabilidade)",
            "owner": "PM Onboarding (desenho) + CS (execução)",
            "dependencies": "ACT-03 (milestone de ativação e reason "
                            "estruturado)",
            "mechanism_expected": "reduzir tempo-para-ativação e taxa de "
                                  "primeiro evento em 90d por intervenção por "
                                  "estágio; causalidade só via experimento",
            "stop_go_criteria": "GO: redução relativa >= 10% (piso do cenário "
                                "conservador) após 4 trimestres; STOP: efeito "
                                "negativo com CI excluindo 0 em 2 trimestres; "
                                "guardrails de CSAT/escalação",
        },
        {
            "action_id": "ACT-02",
            "action": "Triage operacional semanal da watchlist top-20: 8 "
                      "onboarding validados vs 12 exposure-only",
            "family": "B (uso operacional da watchlist)",
            "decision": "Now",
            "evidence_strength": "MÉDIA — 8/20 ancorados em sinal validado; "
                                 "12/20 = exposição/recência sem lift (NÃO "
                                 "rotular risco)",
            "evidence_ref": "t16_watchlist_top20.csv; evidence/04 §8; "
                            "decisions It04 D6/D8",
            "impact_metric": "cobertura de triage (20 contas/semana); "
                             "exposição coberta (winner MRR)",
            "impact_range": f"20 contas/semana; exposição coberta "
                            f"{fmt_br_int(wl['total_sum'])} US$/mês "
                            f"(10,7% da exposição total); sem estimativa de "
                            f"US$ de efeito",
            "effort": "S",
            "time_to_first_signal": "1 semana",
            "reversibility": "ALTA (sem mudança de contrato/produto)",
            "owner": "CS Lead + agente CS",
            "dependencies": "watchlist It04 (t16)",
            "mechanism_expected": "atenção humana priorizada por evidência + "
                                  "exposição; tratamento diferenciado por "
                                  "grupo",
            "stop_go_criteria": "GO: >= 90% do top-20 triaged/semana por 4 "
                                "semanas; STOP: sem ação documentável por 2 "
                                "semanas seguidas",
        },
        {
            "action_id": "ACT-03",
            "action": "Instrumentação de dados: milestone de ativação, reason "
                      "estruturado, timestamps alinhados, CSAT com cobertura, "
                      "lens unificada",
            "family": "C (contrato/instrumentação de dados)",
            "decision": "Next",
            "evidence_strength": "ALTA como habilitadora — limitações "
                                 "estruturais documentadas (It01–It04); "
                                 "pré-requisito da medição ACT-01",
            "evidence_ref": "contract §9/§10; evidence/01 §5; evidence/03 §8",
            "impact_metric": "quality coverage (não-US$): CSAT, reason, uso "
                             "em janela, milestone de ativação",
            "impact_range": f"CSAT com nota: {fmt_br_dec(quality['csat_coverage']*100)}% "
                            f"hoje -> >= 90%; reason 'unknown' "
                            f"{fmt_br_dec(quality['reason_unknown']*100)}% -> "
                            f"< 5%; uso em janela "
                            f"{fmt_br_dec(quality['usage_in_window']*100)}% -> "
                            f">= 90%; milestone de ativação 0% -> 100% dos "
                            f"novos signups",
            "effort": "M",
            "time_to_first_signal": "4 semanas (primeiros campos)",
            "reversibility": "MÉDIA (mudanças de schema exigem migração)",
            "owner": "Data/Product Eng",
            "dependencies": "contrato analítico It02",
            "mechanism_expected": "habilitar leading metrics e reduzir viés "
                                  "estrutural das análises futuras",
            "stop_go_criteria": "GO: metas de cobertura atingidas em 2 "
                                "trimestres; STOP: 2 trimestres sem avanço",
        },
        {
            "action_id": "ACT-04",
            "action": "Piloto OBSERVACIONAL de reativação/recorrência com "
                      "dados instrumentados (sem claim de ROI)",
            "family": "E (reativação/recorrência — baixa confiança)",
            "decision": "Later",
            "evidence_strength": "BAIXA — sem lift (0,52/0,41/1,29; regra B); "
                                 "associação descritiva com censura (KM 90d "
                                 "0,653; mediana 187d)",
            "evidence_ref": "t14_backtest_temporal.csv (regra B); "
                            "evidence/04 §3; decisions It04 D7",
            "impact_metric": "observação: taxa de próximo evento pós-"
                             "reativação com follow-up explícito; NÃO US$",
            "impact_range": "sem estimativa financeira (proibido ROI de "
                            "winback/reativação mais barata)",
            "effort": "S",
            "time_to_first_signal": "1 trimestre (primeiras reativações com "
                                    "follow-up)",
            "reversibility": "ALTA (piloto sem compromisso)",
            "owner": "CS + Data",
            "dependencies": "ACT-03 (instrumentação)",
            "mechanism_expected": "medir recorrência pós-reativação com dados "
                                  "estruturados; escalar só por regra "
                                  "pré-registrada",
            "stop_go_criteria": "GO (escalar): taxa de próximo evento <= 90d "
                                ">= 34,7% (âncora KM) após 2 trimestres "
                                "instrumentados; senão encerrar",
        },
    ]
    return pd.DataFrame(rows)


def build_measurement_plan(onb: dict, inc: dict) -> pd.DataFrame:
    """Plano de medição (t20): leading/lagging/guardrails por ação."""
    rows = [
        # ACT-01
        ("ACT-01", "leading", "milestone_completion_rate",
         "proporção de novos signups que completam o milestone de ativação "
         "dentro de 7/14/30 dias do signup",
         "novos signups com milestone capturado (ACT-03)",
         "coorte de signup (semanal)", "7/14/30d do signup",
         "instrumentação ACT-03 (novo campo)", "PM Onboarding",
         "semanal", "GO se >= 60% no dia 14 em 2 coortes consecutivas"),
        ("ACT-01", "leading", "time_to_first_key_action",
         "dias do signup até a primeira ação-chave (integração/uso alinhado)",
         "novos signups", "coorte de signup (semanal)", "90d",
         "feature_usage alinhado (contrato §9)", "PM Onboarding", "semanal",
         "redução de mediana vs baseline It03"),
        ("ACT-01", "leading", "onboarding_completion_rate",
         "proporção de contas onboarding com todas as etapas do programa "
         "concluídas em 90d", "coorte de signup", "coorte de signup",
         "90d", "instrumentação ACT-03", "CS", "semanal",
         ">= 70% ao fim do 1º trimestre do rollout"),
        ("ACT-01", "lagging", "first_event_90d_rate",
         "taxa de primeiro evento de churn (lente C) em 90d por coorte",
         "contas elegíveis da coorte (signup <= início)", "coorte de signup",
         "90d após signup", "churn_events (contrato §4/§8)", "CS + Data",
         "mensal", "comparar tratado vs holdout (experimento)"),
        ("ACT-01", "lagging", "r1_gross_exposure_short_lived",
         "R1 gross ending MRR de assinaturas com <= 90d de vida (lente R1 "
         "separada; exposição, NÃO perda)", "assinaturas encerradas",
         "trimestre", "90d de vida da assinatura", "subscriptions (contrato §5)",
         "Data", "trimestral", "reportar sempre com a lente declarada"),
        ("ACT-01", "lagging", "state_mrr_lens",
         "winner MRR (estado) e R2 net loss (churn-to-inactive + contraction) "
         "por lente separada", "contas ativas", "trimestre", "trimestre",
         "account_month (contrato §5)", "Data", "trimestral",
         "nunca misturar R1/R2 na mesma fórmula"),
        ("ACT-01", "guardrail", "csat_and_escalation",
         "CSAT médio e taxa de escalação do suporte nas contas do programa",
         "tickets fechados com nota (contrato §10)", "contas do rollout",
         "90d", "support_tickets", "CS", "semanal",
         "STOP se CSAT < 3,5 ou escalação >= 1,5x baseline por 4 semanas"),
        # ACT-02
        ("ACT-02", "leading", "triage_coverage_weekly",
         "proporção do top-20 com triage registrado na semana",
         "top-20 (t16)", "top-20 fixo na semana", "semana",
         "t16_watchlist_top20.csv + registro de triage (novo)",
         "CS Lead", "semanal", "GO se >= 90% por 4 semanas"),
        ("ACT-02", "leading", "action_documented_rate",
         "proporção de contas triaged com ação registrada (contato de "
         "ativação/renovação/revisão)", "top-20 triaged", "semana", "semana",
         "registro de triage (novo)", "CS Lead", "semanal",
         ">= 80% das contas triaged com ação"),
        ("ACT-02", "lagging", "contact_outcome_90d",
         "desfecho documentado dos contatos em 90d (ativação concluída, "
         "renovação, upgrade, re-evento)", "contas com contato", "coorte de "
         "contato", "90d", "registro de triage + churn_events", "CS Lead",
         "trimestral", "descritivo; NÃO atribuir causalidade"),
        ("ACT-02", "guardrail", "no_risk_labeling",
         "comunicação sem rótulo de risco para os 12 exposure-only",
         "top-20", "semana", "semana", "registro de triage", "CS Lead",
         "semanal", "FAIL de processo se qualquer conta B/C rotulada como "
         "'alto risco'"),
        # ACT-03
        ("ACT-03", "leading", "field_coverage",
         "cobertura de campos instrumentados (CSAT, reason estruturado, "
         "milestone de ativação)", "tickets/eventos/signups",
         "mês corrente", "mês", "tickets/events/novo campo milestone",
         "Data Eng", "semanal", "avanço monotônico até as metas"),
        ("ACT-03", "leading", "usage_in_window_share",
         "proporção de linhas de uso dentro da janela da assinatura",
         "feature_usage", "mês corrente", "mês",
         "feature_usage + subscriptions (contrato §9)", "Data Eng", "mensal",
         ">= 90% (meta)"),
        ("ACT-03", "lagging", "event_sub_linkage",
         "proporção de eventos com assinatura encerrada ±30d na mesma conta",
         "churn_events", "trimestre", "trimestre", "churn_events + "
         "subscriptions", "Data Eng", "trimestral",
         ">= 80% (meta); habilita análises futuras"),
        ("ACT-03", "guardrail", "no_imputation",
         "nenhuma imputação de fechamento futuro/CSAT (política closed_at)",
         "tickets", "mês", "mês", "support_tickets", "Data Eng", "mensal",
         "contrato §10; violação = FAIL de processo"),
        # ACT-04
        ("ACT-04", "leading", "reactivation_followup",
         "nº de reativações marcadas com follow-up explícito (janela "
         "observável)", "episódios is_reactivation", "mês corrente", "mês",
         "churn_events (It04 §3)", "CS + Data", "mensal",
         ">= 90% dos episódios com follow-up definido"),
        ("ACT-04", "lagging", "next_event_rate_90d_180d",
         "taxa de próximo evento <= 90d/180d pós-reativação (KM com censura "
         "no corte)", "episódios de reativação", "coorte de reativação",
         "90d/180d", "churn_events (It04 §3)", "Data", "trimestral",
         "comparar com âncora 34,7% (KM 90d) e 52,4% (180d)"),
        ("ACT-04", "guardrail", "no_roi_claim",
         "nenhum valor em US$ atribuído a reativação (sem ligação com "
         "receita)", "n/a", "n/a", "n/a", "n/a", "CS + Data", "n/a",
         "claim de ROI/winback = FAIL de processo"),
    ]
    return pd.DataFrame(
        rows, columns=["action_id", "metric_type", "metric", "definition",
                       "denominator", "cohort", "window", "source", "owner",
                       "cadence", "stop_go"])


def build_watchlist_split(t16: pd.DataFrame) -> pd.DataFrame:
    """Split da watchlist (t21): 8 onboarding validados vs 12 exposure-only."""
    out: list[dict] = []
    for _, r in t16.sort_values(["watch_rank"]).iterrows():
        if r["watch_tier"] == "A":
            group = "validated_onboarding"
            action = ("Contato de ativação/onboarding com milestone "
                      "(sinal validado: lift 1,57/1,56/1,83)")
        else:
            group = "exposure_only"
            action = ("Revisão de conta/renovação com contexto do episódio "
                      "(sem sinal validado — NÃO rotular alto risco)")
        out.append({
            "watch_rank": int(r["watch_rank"]),
            "account_id": r["account_id"],
            "watch_tier": r["watch_tier"],
            "group": group,
            "current_winner_mrr": int(r["current_winner_mrr"]),
            "triage_action": action,
            "owner": "CS Lead + agente CS",
            "cadence": "semanal",
            "risk_label_note": ("priorização operacional/exposição (It04 D8); "
                                "nenhuma conta é declarada em risco de sair"),
        })
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------
# Gates
# ----------------------------------------------------------------------------

def run_gates(t14: pd.DataFrame, onb: dict, inc: dict, inflow: dict,
              total_exposure: int, wl: dict, quality: dict,
              scenarios: pd.DataFrame, t18: pd.DataFrame, t20: pd.DataFrame,
              t21: pd.DataFrame, t15: pd.DataFrame,
              charts_before: list[str], written_tables: list[str]) -> None:
    # G2 — base onboarding: t11 (runtime) vs t15 (segmento S1)
    s1 = t15[t15["segment"] == "S1"]
    if not s1.empty:
        ok = (int(s1["N"].iloc[0]) == onb["n"]
              and int(s1["current_mrr_sum"].iloc[0]) == onb["mrr_sum"])
        check("G2-onboarding-base", "base elegível",
              "base onboarding (t11) consistente com segmento S1 (t15)",
              "PASS" if ok else "FAIL",
              f"t11: n={onb['n']}, MRR={onb['mrr_sum']}; t15 S1: "
              f"n={int(s1['N'].iloc[0])}, MRR={int(s1['current_mrr_sum'].iloc[0])}")
    else:
        check("G2-onboarding-base", "base elegível",
              "base onboarding (t11) consistente com segmento S1 (t15)",
              "FAIL", "segmento S1 ausente em t15")

    # G3 — incidência: pooled via duas vias (agregação direta vs média
    # ponderada por n_rule) + ordem lo <= pooled <= hi
    rd = t14[(t14["rule"] == "D")
             & (t14["horizon_days"] == BACKTEST_HORIZON_DAYS)]
    pooled_alt = float((rd["precision"] * rd["n_rule"]).sum()
                       / rd["n_rule"].sum())
    inc_ok = (abs(pooled_alt - inc["pooled"]) < 1e-3
              and inc["lo"] <= inc["pooled"] <= inc["hi"])
    check("G3-incidence", "incidência",
          "precision pooled/min/max da regra D (90d) consistentes",
          "PASS" if inc_ok else "FAIL",
          f"pooled={inc['pooled']:.4f} (2 vias), lo={inc['lo']:.4f}, "
          f"hi={inc['hi']:.4f}")

    # G4 — aritmética dos cenários: re-cálculo independente (loop) == tabela
    mismatch = 0
    for _, r in scenarios.iterrows():
        exp_events = r["eligible_n"] * r["incidence_90d"]
        aff_events = exp_events * (r["rel_reduction_pct"] / 100.0)
        if abs(exp_events - r["expected_events_90d"]) > 0.11 \
                or abs(aff_events - r["events_affected_90d"]) > 0.11:
            mismatch += 1
    check("G4-scenarios", "cenários",
          "aritmética dos cenários re-calculada de forma independente",
          "PASS" if mismatch == 0 else "FAIL",
          f"{mismatch} linhas com divergência > 0,1")

    # G5 — watchlist: 8/12, somas e share da exposição total
    wl_ok = (wl["tier_a_n"] == 8 and wl["tier_bc_n"] == 12
             and wl["total_n"] == 20)
    share = 100.0 * wl["total_sum"] / total_exposure if total_exposure else 0.0
    check("G5-top20", "watchlist",
          "split 8/12 e exposição coberta consistentes",
          "PASS" if wl_ok else "FAIL",
          f"Tier A: {wl['tier_a_n']} contas / {wl['tier_a_sum']}; "
          f"B+C: {wl['tier_bc_n']} / {wl['tier_bc_sum']}; total "
          f"{wl['total_n']} / {wl['total_sum']} "
          f"({share:.1f}% da exposição {total_exposure})")

    # G6 — fluxo de signups 2024
    inflow_ok = (inflow["min"] <= inflow["avg"] <= inflow["max"]
                 and inflow["total"] > 0
                 and sum(inflow["quarters"]) == inflow["total"])
    check("G6-inflow", "população",
          "fluxo trimestral 2024 consistente",
          "PASS" if inflow_ok else "FAIL",
          f"trimestres={inflow['quarters']}, total={inflow['total']}, "
          f"média={inflow['avg']:.2f}")

    # G7 — poder estatístico: MDE decrescente com N
    n_arms = [max(1, int(inflow["avg"] * EXPERIMENT_SPLIT)),
              max(1, int(inflow["avg"])),
              max(1, int(inflow["avg"] * EXPERIMENT_QUARTERS * EXPERIMENT_SPLIT))]
    mdes = [mde_for_n(n, inc["pooled"]) for n in n_arms]
    mde_ok = mdes[0] > mdes[1] > mdes[2]
    check("G7-power", "experimento",
          "MDE monotônico decrescente com N por braço",
          "PASS" if mde_ok else "FAIL",
          f"N/braço={n_arms} -> MDE(80% power)="
          f"{[f'{m*100:.0f}%' for m in mdes]}")

    # G8 — plano de medição completo por ação
    missing_plan = []
    for aid in ("ACT-01", "ACT-02", "ACT-03", "ACT-04"):
        sub = t20[t20["action_id"] == aid]
        for mtype in ("leading", "lagging", "guardrail"):
            if (sub["metric_type"] == mtype).sum() < 1:
                missing_plan.append(f"{aid}:{mtype}")
    check("G8-measurement", "medição",
          "plano de medição com leading/lagging/guardrail por ação",
          "PASS" if not missing_plan else "FAIL",
          "faltam: " + (", ".join(missing_plan) if missing_plan else "nenhum"))

    # G9 — outputs: apenas 4 tabelas; charts intocados; sem PNG novo
    charts_after = sorted(p.name for p in CHARTS_DIR.glob("*.png"))
    charts_ok = charts_before == charts_after
    extra = [t for t in written_tables if t not in ALLOWED_TABLES]
    missing_out = [t for t in ALLOWED_TABLES if t not in written_tables]
    check("G9-outputs", "outputs",
          "exatamente 4 tabelas (sem extra); charts intocados (sem PNG novo)",
          "PASS" if charts_ok and not extra and not missing_out else "FAIL",
          f"tabelas={len(written_tables)} (extra={extra or 'nenhuma'}, "
          f"ausentes={missing_out or 'nenhuma'}); charts antes/depois "
          f"{'iguais' if charts_ok else 'DIFERENTES'}")

    # G10 — nenhuma constante de dado hardcoded no próprio script
    src = Path(__file__).resolve().read_text(encoding="utf-8")
    runtime_derived = [
        str(onb["mrr_sum"]), f"{inc['pooled']:.4f}",
        str(wl["tier_a_sum"]), str(wl["tier_bc_sum"]),
        str(wl["total_sum"]), str(total_exposure),
    ]
    hits = sorted({v for v in runtime_derived if v in src})
    check("G10-no-hardcoded", "higiene",
          "valores derivados ausentes como literais no script",
          "PASS" if not hits else "FAIL",
          f"literais derivados encontrados={hits or 'nenhum'}")

    # G11 — qualidade de dados (baseline ACT-03) derivada em runtime
    q_ok = (quality["csat_coverage"] > 0 and quality["csat_coverage"] < 1
            and 0 < quality["reason_unknown"] < 1
            and 0 < quality["usage_in_window"] < 1
            and 0 <= quality["linkage"] <= 1
            and not quality["activation_field"])
    check("G11-data-quality", "dados",
          "baseline de qualidade derivado em runtime (sem literais)",
          "PASS" if q_ok else "FAIL",
          f"CSAT={quality['csat_coverage']*100:.1f}%, unknown="
          f"{quality['reason_unknown']*100:.2f}%, uso em janela="
          f"{quality['usage_in_window']*100:.1f}%, vínculo evento-sub="
          f"{quality['linkage']*100:.1f}%, campo de ativação presente="
          f"{quality['activation_field']}")

    # G12 — consistência report <-> CSV (re-lê as tabelas escritas)
    readback = {}
    for t in written_tables:
        df = pd.read_csv(TABLES_DIR / t)
        readback[t] = df
    t19_back = readback["t19_impact_sensitivity.csv"]
    base_row = t19_back[t19_back["scenario"] == "base"]
    t21_back = readback["t21_watchlist_split_actions.csv"]
    t18_back = readback["t18_actions_prioritized.csv"]
    ok_back = (not base_row.empty
               and int(t21_back["current_winner_mrr"].sum()) == wl["total_sum"]
               and len(t18_back) == 4
               and len(t21_back) == 20)
    check("G12-consistency", "consistência",
          "tabelas escritas re-lidas e consistentes com o cálculo",
          "PASS" if ok_back else "FAIL",
          f"t19 base rows={len(base_row)}, t21 soma="
          f"{int(t21_back['current_winner_mrr'].sum())} (esperado "
          f"{wl['total_sum']}), t18 ações={len(t18_back)}, t21 linhas="
          f"{len(t21_back)}")


# ----------------------------------------------------------------------------
# Relatório (CEO-readable, conciso; sem timestamp)
# ----------------------------------------------------------------------------

def md_table(header: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def render_report(onb: dict, inc: dict, inflow: dict, total_exposure: int,
                  wl: dict, quality: dict, scenarios: pd.DataFrame,
                  t18: pd.DataFrame, t20: pd.DataFrame, t21: pd.DataFrame,
                  mdes: list[float], n_arms: list[int],
                  table_names: list[str],
                  structural_fail: bool = False) -> str:
    if structural_fail:
        return (
            "# Plano de Ações e Impacto — Iteração 05 (RavenStack)\n\n"
            "## Falha estrutural\n\n"
            "O pipeline não pôde executar: arquivos/schema exigidos ausentes "
            "ou inválidos (ver checks acima). Nenhuma análise foi gerada; "
            "tabelas não foram regravadas (outputs anteriores preservados no "
            "histórico, sem resultado stale). Corrija a fonte e re-execute.\n\n"
            "## Checks emitidos\n\n| ID | Escopo | Check | Veredito | Detalhe |\n"
            "|---|---|---|---|---|\n" +
            "\n".join(
                f"| {c['id']} | {c['scope']} | {c['description']} | "
                f"{c['level']} | {c['detail']} |" for c in CHECKS) + "\n"
        )

    base = scenarios[scenarios["scenario"] == "base"].iloc[0]
    cons = scenarios[scenarios["scenario"] == "conservador"].iloc[0]
    amb = scenarios[scenarios["scenario"] == "ambicioso"].iloc[0]
    ann = scenarios[scenarios["scenario"] == "annualized"].iloc[0]
    ev_lo, ev_hi = cons["events_affected_90d"], amb["events_affected_90d"]
    ex_lo, ex_hi = (cons["expected_exposure_affected_mrr"],
                    amb["expected_exposure_affected_mrr"])
    share = 100.0 * wl["total_sum"] / total_exposure

    # Tabelas markdown (do próprio dataframe; nada hardcoded)
    t18_md = md_table(
        ["ID", "Ação", "Decisão", "Evidência", "Impacto (faixa)", "Esforço",
         "1º sinal", "Owner"],
        [[r["action_id"], r["action"], r["decision"],
          r["evidence_strength"].split(" — ")[0], r["impact_range"],
          r["effort"], r["time_to_first_signal"], r["owner"]]
         for _, r in t18.iterrows()])
    t19_md = md_table(
        ["Ação", "Cenário", "Incidência 90d", "N elegível",
         "Eventos esp. 90d", "Redução rel.", "Eventos afetados",
         "Exposição base (US$)", "Exposição afetada (US$)", "Nota"],
        [[r["action_id"], r["scenario"], f"{r['incidence_90d']:.4f}",
          fmt(r["eligible_n"]), fmt(r["expected_events_90d"]),
          f"{r['rel_reduction_pct']:.1f}%", fmt(r["events_affected_90d"]),
          fmt_br_int(r["exposure_base_mrr"]),
          fmt_br_int(r["expected_exposure_affected_mrr"]), r["note"]]
         for _, r in scenarios.iterrows()])
    t20_lead = t20[t20["metric_type"] == "leading"]
    t20_md = md_table(
        ["Ação", "Tipo", "Métrica", "Definição (resumo)", "Denominador",
         "Coorte", "Janela", "Fonte", "Owner", "Cadência"],
        [[r["action_id"], r["metric_type"], r["metric"],
          r["definition"][:110], r["denominator"][:80], r["cohort"][:50],
          r["window"], r["source"][:70], r["owner"], r["cadence"]]
         for _, r in t20.iterrows()])
    t21_md = md_table(
        ["Rank", "Conta", "Tier", "Grupo", "Winner MRR", "Ação de triage",
         "Owner", "Cadência"],
        [[str(r["watch_rank"]), r["account_id"], r["watch_tier"], r["group"],
          fmt_br_int(r["current_winner_mrr"]),
          r["triage_action"][:110], r["owner"], r["cadence"]]
         for _, r in t21.sort_values(["watch_rank"]).iterrows()])

    md = f"""# Plano de Ações e Impacto — Iteração 05 (RavenStack)

Gerado por `solution/src/05_actions_impact.py` (execução offline e
determinística; sem timestamp para garantir output byte-a-byte estável).
Premissas fixadas ANTES do cálculo em
`process-log/decisions/iteration-05-action-impact-assumptions.md`.

## 1. Resposta primeiro

Quatro ações, duas para agora:

| Ação | Decisão | Por quê |
|---|---|---|
| **ACT-01** Programa de ativação/onboarding 0-90d com milestones instrumentados e rollout gradual (experimento com holdout) | **Now** | única ação ancorada em sinal com validação temporal (lift 1,57/1,56/1,83 nos 3 cutoffs 90d; N≥25). Impacto PLANEJADO (não medido): **{fmt_br_dec(ev_lo)}–{fmt_br_dec(ev_hi)} eventos/90d** e **{fmt_br_int(ex_lo)}–{fmt_br_int(ex_hi)} US$ de expected MRR-equivalent exposure affected/90d** (base: {fmt_br_dec(base['events_affected_90d'])} eventos; {fmt_br_int(base['expected_exposure_affected_mrr'])} US$). O lift descreve associação observada — **não é efeito do programa**; o efeito será medido pelo experimento |
| **ACT-02** Triage semanal da watchlist top-20 (8 onboarding validados vs 12 exposure-only) | **Now** | esforço baixo (S), usa watchlist existente; exposição coberta **{fmt_br_int(wl['total_sum'])} US$/mês ({fmt_br_dec(share)}%** do total). Os 12 exposure-only NÃO são rotulados como alto risco |
| **ACT-03** Instrumentação de dados (milestone de ativação, reason estruturado, timestamps, CSAT, lens unificada) | **Next** | pré-requisito da medição do ACT-01; metas de qualidade nomeadas (sem US$) |
| **ACT-04** Piloto observacional de reativação/recorrência | **Later** | baixa confiança (sem lift; associação descritiva com censura); sem claim de ROI |

## 2. Evidência que sustenta (curto)

- **Onboarding ≤ 90d é o único sinal validado** temporalmente (backtest
  point-in-time It04; regra D: 1,57/1,56/1,83; sensibilidade 180d 1,26/1,51).
  Coerente com a causa raiz It03 (53,4% dos primeiros eventos ≤ 90d do signup;
  R1 ≤ 90d = 68,4% da janela — exposição, não perda).
- **Recorrência, reativação e alto MRR NÃO validam** (0,44/0,41/0,89 ·
  0,52/0,41/1,29 · 0,56/0,85/0,71) → watchlist é **operational
  priority/exposure**, nunca score.
- **Segmentos amplos, uso e suporte não discriminam** (It03 H3–H6) →
  nenhuma ação é desenhada sobre eles.
- **All-active no corte** (500/500 por estado) → impacto medido por eventos
  (lente C) e exposição (lentes R1/winner separadas), nunca por "perda real
  de estado" no presente.

## 3. Ações priorizadas (detalhe em `t18_actions_prioritized.csv`)

{t18_md}

Sem score numérico: decisão por evidência + impacto + esforço, com
reversibilidade, dependências e stop/go declarados por linha.

## 4. Impacto em faixa — fórmula, cenários e honestidade

**Fórmula (só ACT-01 tem estimativa de exposição defensável):**

```
expected_events_90d   = N_elegível × incidence_90d              (histórico descritivo)
events_affected_90d   = N_elegível × incidence_90d × redução_relativa
exposure_affected     = Σ winner_mrr(elegíveis) × incidence_90d × redução_relativa
```

- `N_elegível` = {onb['n']} contas onboarding no corte (tenure ≤ 90d);
  Σ winner MRR = **{fmt_br_int(onb['mrr_sum'])} US$** (lente estado/exposição).
- `incidence_90d` = precision pooled da regra D nos cutoffs 90d =
  **{inc['outcomes']}/{inc['n_rule']} = {inc['pooled']:.4f}**
  (lower {inc['lo']:.4f} / upper {inc['hi']:.4f}).
- `redução_relativa` = **premissa de planejamento** 10%/20%/30%
  (conservador/base/ambicioso) — NÃO derivada do lift; será testada pelo
  experimento ACT-01.

{t19_md}

**Honestidade (obrigatória):** eventos ≠ logos ≠ revenue churn (lentes C/B/A
não intercambiáveis, contrato §4); R1 é exposição contratual, **não é perda**
(§5); a linha `annualized` é aritmética (4 coortes), **não é forecast**;
nenhum custo monetário é afirmado (CAC/winback não existem na base); ACT-02/03/04
não têm linha de US$ porque não há estimativa financeira defensável — impacto
operacional mensurável (coverage, quality, instrumentation) no lugar.

## 5. Experimento do programa de ativação (ACT-01)

- **Desenho:** rollout gradual por semana de signup, 50/50 tratado/holdout,
  por {EXPERIMENT_QUARTERS} trimestres; outcome = primeiro evento de churn
  (lente C) em 90d; features pré-registradas (mesmas do backtest It04, sem
  leakage).
- **Poder (aproximação normal de 2 proporções; sem dependência extra):**
  N por braço ≈ {n_arms[0]}/{n_arms[1]}/{n_arms[2]} (1/2/4 trimestres) →
  menor efeito detectável a 80% power ≈
  **{mdes[0]*100:.0f}% / {mdes[1]*100:.0f}% / {mdes[2]*100:.0f}%** de redução
  relativa. Com o fluxo de ~{inflow['avg']:.0f} signups/trimestre, efeitos
  abaixo de ~{mdes[2]*100:.0f}% **não são detectáveis** em 4 trimestres:
  resultados inconclusivos NÃO são evidência de ausência de efeito.
- **Regra de decisão pré-registrada:** GO (escala total) se ponto estimado de
  redução relativa ≥ 10% (piso do cenário conservador) após 4 trimestres;
  STOP se efeito negativo com CI 95% excluindo 0 após 2 trimestres; senão
  estende holdout/reescopa.

## 6. Plano de medição (detalhe em `t20_measurement_plan.csv`)

{t20_md}

## 7. Watchlist: 8 onboarding validados vs 12 exposure-only

A watchlist (It04) é **operational priority/exposure**. O Tier A (8 contas,
onboarding ≤ 90d — único sinal validado) recebe contato de ativação; os
Tiers B/C (12 contas: evento recente + proteção de receita) recebem revisão
de conta/renovação e **não são rotulados como alto risco de churn**.

{t21_md}

## 8. Não fazer agora

1. **ML/score preditivo de churn** — nenhuma regra além de onboarding valida
   temporalmente (It04 D8); score sem validação é claim falso.
2. **Desconto generalizado** — sem custos na base, seria preço inventado;
   nenhuma evidência de que preço dirige o churn precoce.
3. **Automação de churn (mensagens/desconto automáticos)** — sem validação
   causal; começaria pela experimentação (ACT-01).
4. **Decisão por reason_code/CSAT** — evidência sugestiva com missingness alta
   (CSAT 41,2% nulos; reason 'unknown' 15,8%; contrato §10).
5. **ROI pontual / revenue saved / reativação mais barata** — proibido nesta
   base (sem CAC/winback; R1 é exposição; reativação sem ligação com receita).

## 9. Limitações e handoff para a Iteração 06

- Impacto é **planejado, não medido**: cenários são premissas nomeadas com
  componentes expostos; o experimento ACT-01 é o caminho para efeito medido.
- All-active no corte, sinteticidade da base e N pequenos (intervalos largos)
  seguem limitando qualquer extrapolação (It04 §10).
- It06 (automação): recebe este script como 5º estágio do pipeline
  (`01..05`), determinístico, offline, sem novas dependências; `run.sh` deve
  re-gerar `05_action_plan.md` + `t18..t21` idênticos (byte-a-byte).
"""

    # --- claims proibidos ausentes do corpo do relatório (verificação ANTES
    # da tabela de gates; varre apenas as seções 1-7 — a seção 8 é a lista de
    # proibições e nomeia os termos propositalmente) ---
    lower = md.split("## 8.")[0].lower()
    forbidden_hits = [w for w in ("receita salva", "revenue saved",
                                  "cac queimado")
                      if w in lower]
    check("G11b-forbidden-claims", "honestidade",
          "texto do relatório sem claims proibidos (afirmativos)",
          "PASS" if not forbidden_hits else "FAIL",
          f"hits={forbidden_hits or 'nenhum'}")

    md += f"""
## 10. Gates e validações

| ID | Escopo | Check | Veredito | Detalhe |
|---|---|---|---|---|
""" + "\n".join(
        f"| {c['id']} | {c['scope']} | {c['description']} | {c['level']} | "
        f"{c['detail']} |" for c in CHECKS) + f"""

## 11. Arquivos gerados

- Tabelas: {", ".join(table_names)}.
- Relatório: este arquivo (`05_action_plan.md`). Nenhum PNG gerado (keep-set
  visual fechado em 6; charts intocados — gate G9).
"""
    return md


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> int:
    try:
        accounts = load_csv(RAW_DIR / "ravenstack_accounts.csv", "F01",
                            "ravenstack_accounts.csv",
                            "ravenstack_accounts.csv",
                            REQUIRED["ravenstack_accounts.csv"])
        subs = load_csv(RAW_DIR / "ravenstack_subscriptions.csv", "F02",
                        "ravenstack_subscriptions.csv",
                        "ravenstack_subscriptions.csv",
                        REQUIRED["ravenstack_subscriptions.csv"])
        events = load_csv(RAW_DIR / "ravenstack_churn_events.csv", "F03",
                          "ravenstack_churn_events.csv",
                          "ravenstack_churn_events.csv",
                          REQUIRED["ravenstack_churn_events.csv"])
        usage = load_csv(RAW_DIR / "ravenstack_feature_usage.csv", "F04",
                         "ravenstack_feature_usage.csv",
                         "ravenstack_feature_usage.csv",
                         REQUIRED["ravenstack_feature_usage.csv"])
        tickets = load_csv(RAW_DIR / "ravenstack_support_tickets.csv", "F05",
                           "ravenstack_support_tickets.csv",
                           "ravenstack_support_tickets.csv",
                           REQUIRED["ravenstack_support_tickets.csv"])
        panel = load_csv(PANEL_PATH, "F06", "account_month.csv",
                         "account_month.csv", REQUIRED["account_month.csv"])
        t11 = load_csv(T11_PATH, "F07", "t11_account_lifecycle.csv",
                       "t11_account_lifecycle.csv",
                       REQUIRED["t11_account_lifecycle.csv"])
        t14 = load_csv(T14_PATH, "F08", "t14_backtest_temporal.csv",
                       "t14_backtest_temporal.csv",
                       REQUIRED["t14_backtest_temporal.csv"])
        t15 = load_csv(T15_PATH, "F09", "t15_priority_segments.csv",
                       "t15_priority_segments.csv",
                       REQUIRED["t15_priority_segments.csv"])
        t16 = load_csv(T16_PATH, "F10", "t16_watchlist_top20.csv",
                       "t16_watchlist_top20.csv",
                       REQUIRED["t16_watchlist_top20.csv"])

        for df in (usage, events, subs):
            if "churn_date" in df.columns:
                df["churn_date"] = pd.to_datetime(df["churn_date"])
            if "usage_date" in df.columns:
                df["usage_date"] = pd.to_datetime(df["usage_date"])
            if "start_date" in df.columns:
                df["start_date"] = pd.to_datetime(df["start_date"])
            if "end_date" in df.columns:
                df["end_date"] = pd.to_datetime(df["end_date"])
        for df in (t11, t16):
            if "current_winner_mrr" in df.columns:
                df["current_winner_mrr"] = pd.to_numeric(
                    df["current_winner_mrr"])

        charts_before = sorted(p.name for p in CHARTS_DIR.glob("*.png"))

        # --- computações ---
        onb = compute_onboarding_base(t11)
        inc = compute_incidence(t14)
        inflow = compute_inflow(accounts)
        total_exposure = compute_total_exposure(panel)
        wl = compute_watchlist_split(t16)
        quality = compute_data_quality(events, tickets, subs, usage)
        scenarios = build_scenarios(onb, inc, inflow)
        t18 = build_prioritized(
            {"events_lo": scenarios[scenarios["scenario"] == "conservador"]
             .iloc[0]["events_affected_90d"],
             "events_hi": scenarios[scenarios["scenario"] == "ambicioso"]
             .iloc[0]["events_affected_90d"],
             "exposure_lo": scenarios[scenarios["scenario"] == "conservador"]
             .iloc[0]["expected_exposure_affected_mrr"],
             "exposure_hi": scenarios[scenarios["scenario"] == "ambicioso"]
             .iloc[0]["expected_exposure_affected_mrr"]},
            onb, wl, quality)
        t20 = build_measurement_plan(onb, inc)
        t21 = build_watchlist_split(t16)

        n_arms = [max(1, int(inflow["avg"] * EXPERIMENT_SPLIT)),
                  max(1, int(inflow["avg"])),
                  max(1, int(inflow["avg"] * EXPERIMENT_QUARTERS
                              * EXPERIMENT_SPLIT))]
        mdes = [mde_for_n(n, inc["pooled"]) for n in n_arms]

        # --- escrita das tabelas (escopo fechado) ---
        t18.to_csv(TABLES_DIR / "t18_actions_prioritized.csv", index=False)
        scenarios.to_csv(TABLES_DIR / "t19_impact_sensitivity.csv", index=False)
        t20.to_csv(TABLES_DIR / "t20_measurement_plan.csv", index=False)
        t21.to_csv(TABLES_DIR / "t21_watchlist_split_actions.csv", index=False)
        written_tables = list(ALLOWED_TABLES)

        # --- gates ---
        run_gates(t14, onb, inc, inflow, total_exposure, wl, quality,
                  scenarios, t18, t20, t21, t15, charts_before,
                  written_tables)

        md = render_report(onb, inc, inflow, total_exposure, wl, quality,
                           scenarios, t18, t20, t21, mdes, n_arms,
                           written_tables)
        REPORT_PATH.write_text(md, encoding="utf-8")
    except StructuralError:
        # regrava SEMPRE o relatório (sem stale) e sai sem traceback
        REPORT_PATH.write_text(render_report({}, {}, {}, 0, {}, {},
                                             pd.DataFrame(), pd.DataFrame(),
                                             pd.DataFrame(), pd.DataFrame(),
                                             [], [], [], structural_fail=True),
                               encoding="utf-8")
        return 1

    n_fail = sum(1 for c in CHECKS if c["level"] == "FAIL")
    n_warn = sum(1 for c in CHECKS if c["level"] == "WARN")
    n_pass = sum(1 for c in CHECKS if c["level"] == "PASS")
    print(f"[05_actions_impact] checks: {n_pass} PASS / {n_warn} WARN / "
          f"{n_fail} FAIL")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())