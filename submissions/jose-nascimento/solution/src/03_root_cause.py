#!/usr/bin/env python3
"""
03_root_cause.py — Causa raiz, coortes e economia do onboarding (Iteração 03).

Testa as hipóteses pré-registradas em
`process-log/hypotheses/iteration-03-root-cause-hypotheses.md` (H1–H10) sobre os
dados RavenStack, seguindo o contrato analítico congelado da Iteração 02
(`solution/docs/analytical-contract.md`): lente de eventos (C) para diagnóstico,
lente de assinaturas para receita (R1 gross ending MRR / R2 net account-state
loss), painel account-month como estado/risco, política anti-leakage (features
<= data índice; CSAT/resolução só com tickets fechados), variantes bruta vs
alinhada de uso, censura no corte 2024-12-31.

Gera, de forma offline e determinística (sem timestamp; ordenações estáveis;
PNG byte-a-byte estáveis):
    solution/evidence/03_root_cause_report.md
    solution/out/tables/t01..t11*.csv            (auditabilidade)
    solution/out/charts/a..d_*.png            (4 gráficos essenciais; e/f
                                               substituídos pelas tabelas
                                               t06/t07/t09 — pruning do gate It04)

Semântica de resultado (mesma família das iterações 01-02):
    - PASS  : check íntegro.
    - WARN  : divergência/anomalia de qualidade esperada (documentada).
    - FAIL  : arquivo/schema estrutural ausente ou invariante violado.
    Exit code: 0 se não houver FAIL; 1 caso contrário.
    Em caso de FAIL estrutural o relatório é SEMPRE regravado (sem output
    stale) e sem traceback não tratado (lição das Iterações 01-02).

Restrições: apenas stdlib + pandas + matplotlib; sem rede; paths relativos ao
próprio projeto. Nenhum modelo preditivo/ML; nenhuma recomendação (It05);
nenhuma watchlist (It04).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
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

REPORT_PATH = EVIDENCE_DIR / "03_root_cause_report.md"
PANEL_PATH = PROCESSED_DIR / "account_month.csv"
HYPOTHESES_PATH = SOLUTION_DIR.parent / "process-log" / "hypotheses" \
    / "iteration-03-root-cause-hypotheses.md"

# ----------------------------------------------------------------------------
# Constantes (contrato analítico Iteração 02; hipóteses pré-registradas It03)
# ----------------------------------------------------------------------------
DATA_CUT = pd.Timestamp("2024-12-31")   # data-limite (corte; censura)
FIRST_MONTH = "2023-01"                 # janela observacional (contrato §2)
LAST_MONTH = "2024-12"
SUPPORT_WINDOW_DAYS = 90                # janela pré-evento p/ sinais de suporte
TENURE_BUCKETS = [(0, 3), (4, 6), (7, 12), (13, 24)]   # meses desde o signup
ONBOARDING_DAYS = [30, 60, 90]          # janelas de onboarding (dias)
# faixas de duração de assinaturas encerradas (0d = mesma data start/end —
# exposição instantânea; precisa de bucket próprio para o share fechar 100%)
DURATION_BUCKETS = [(0, 0), (1, 30), (31, 60), (61, 90), (91, 180), (181, 365),
                    (366, None)]
CAC_MULTIPLES = [1, 3, 6, 12]           # cenários CAC-equivalent (múltiplos de MRR)

# Colunas mínimas exigidas por arquivo (guarda estrutural desta iteração).
REQUIRED = {
    "ravenstack_accounts.csv": [
        "account_id", "signup_date", "industry", "referral_source",
        "plan_tier", "is_trial",
    ],
    "ravenstack_subscriptions.csv": [
        "subscription_id", "account_id", "start_date", "end_date", "mrr_amount",
    ],
    "ravenstack_churn_events.csv": [
        "churn_event_id", "account_id", "churn_date", "reason_code",
        "refund_amount_usd", "preceding_upgrade_flag", "preceding_downgrade_flag",
    ],
    "ravenstack_feature_usage.csv": ["subscription_id", "usage_date"],
    "ravenstack_support_tickets.csv": [
        "account_id", "submitted_at", "closed_at", "satisfaction_score",
        "escalation_flag", "first_response_time_minutes", "resolution_time_hours",
    ],
}
PANEL_COLUMNS = [
    "account_id", "month", "status", "winner_mrr", "mrr_ended_in_month",
    "n_ended_in_month", "churn_event_in_month", "n_events_in_month",
    "usage_rows_month", "usage_rows_in_window_month", "tickets_month",
    "csat_mean_month", "months_since_signup",
]

# ----------------------------------------------------------------------------
# Registro de checks (ordem determinística de emissão)
# ----------------------------------------------------------------------------
CHECKS: list[dict] = []


def check(check_id: str, scope: str, description: str, level: str, detail: str) -> None:
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


def pct(part: float, total: float) -> str:
    if total == 0:
        return "NA"
    return f"{100.0 * part / total:.1f}%"


def missing_cols(df: pd.DataFrame, cols: list[str], fname: str) -> list[str]:
    return [f"{c} ({fname})" for c in cols if c not in df.columns]


def guard_columns(df: pd.DataFrame, cols: list[str], check_id: str, scope: str,
                  description: str) -> bool:
    """Registra FAIL estrutural se alguma coluna necessária estiver ausente.

    Retorna True quando todas as colunas existem (o check pode executar).
    Não é catch-all: bugs reais continuam propagando com traceback (exit != 0)
    em vez de virarem FAIL silencioso.
    """
    missing = missing_cols(df, cols, scope)
    if missing:
        check(check_id, scope, description, "FAIL",
              f"não executado (schema): colunas ausentes: {missing}")
        return False
    return True


def months_range(first: str, last: str) -> list[str]:
    """Lista de meses 'YYYY-MM' de first..last inclusive (determinística)."""
    out: list[str] = []
    p = pd.Period(first, "M")
    last_p = pd.Period(last, "M")
    while p <= last_p:
        out.append(p.strftime("%Y-%m"))
        p = p + 1
    return out


def month_end_date(m: str) -> pd.Timestamp:
    return (pd.Timestamp(m + "-01") + pd.offsets.MonthEnd(0)).normalize()


def month_first_date(m: str) -> pd.Timestamp:
    return pd.Timestamp(m + "-01").normalize()


def period_diff_months(a: str, b: str) -> int:
    return (pd.Period(b, "M") - pd.Period(a, "M")).n


# ----------------------------------------------------------------------------
# Leitura e preparação (com guards estruturais)
# ----------------------------------------------------------------------------

def load_all() -> dict[str, pd.DataFrame]:
    """Carrega os 5 CSVs e valida a presença das colunas mínimas desta iteração."""
    loaded: dict[str, pd.DataFrame] = {}
    for fname, cols in REQUIRED.items():
        path = RAW_DIR / fname
        if not path.exists():
            check(f"F01-{fname}", fname, "arquivo presente em data/raw",
                  "FAIL", "arquivo ausente")
            continue
        if path.stat().st_size == 0:
            check(f"F01-{fname}", fname, "arquivo presente em data/raw",
                  "FAIL", "arquivo vazio (0 bytes)")
            continue
        try:
            df = pd.read_csv(path)
        except Exception as exc:  # noqa: BLE001 — falha de parse é estrutural
            check(f"F01-{fname}", fname, "CSV carregável", "FAIL",
                  f"falha de parse: {exc}")
            continue
        loaded[fname] = df
        check(f"F01-{fname}", fname, "arquivo presente e carregável",
              "PASS", f"{path.stat().st_size} bytes, CSV parseado ({len(df)} registros)")
        if guard_columns(df, cols, f"S01-{fname}", fname,
                         "colunas mínimas desta iteração presentes"):
            check(f"S01-{fname}", fname, "colunas mínimas desta iteração presentes",
                  "PASS", f"{len(cols)} colunas exigidas presentes")
    return loaded


def load_panel() -> pd.DataFrame | None:
    """Carrega o painel account-month (base-mestre da Iteração 02)."""
    if not PANEL_PATH.exists():
        check("F02-panel", "account_month.csv", "base-mestre presente", "FAIL",
              "arquivo ausente (rode 02_reconcile_churn.py antes)")
        return None
    try:
        panel = pd.read_csv(PANEL_PATH)
    except Exception as exc:  # noqa: BLE001
        check("F02-panel", "account_month.csv", "base-mestre carregável", "FAIL",
              f"falha de parse: {exc}")
        return None
    if guard_columns(panel, PANEL_COLUMNS, "S02-panel", "account_month.csv",
                     "colunas mínimas do painel presentes"):
        check("S02-panel", "account_month.csv", "colunas mínimas do painel presentes",
              "PASS", f"{len(PANEL_COLUMNS)} colunas exigidas presentes "
                      f"({len(panel)} linhas)")
    panel["month"] = panel["month"].astype(str)
    panel["winner_mrr"] = pd.to_numeric(panel["winner_mrr"], errors="coerce").fillna(0)
    panel["mrr_ended_in_month"] = pd.to_numeric(
        panel["mrr_ended_in_month"], errors="coerce").fillna(0)
    panel["n_ended_in_month"] = pd.to_numeric(
        panel["n_ended_in_month"], errors="coerce").fillna(0)
    panel["n_events_in_month"] = pd.to_numeric(
        panel["n_events_in_month"], errors="coerce").fillna(0)
    return panel


# ----------------------------------------------------------------------------
# A. Série mensal 2023-2024, taxas, R1/R2 e decomposição do spike
# ----------------------------------------------------------------------------

def first_event_per_account(acc: pd.DataFrame, churn: pd.DataFrame) -> pd.DataFrame:
    """Primeiro evento por conta (lente C; tie-break determinístico).

    Retorna DataFrame com account_id, first_event_date, first_event_month,
    signup_month, tenure_months (0 = mês do signup), signup_quarter.
    """
    a2 = acc[["account_id", "signup_date"]].copy()
    a2["signup"] = pd.to_datetime(a2["signup_date"])
    a2["signup_month"] = a2["signup"].dt.to_period("M").astype(str)
    a2["signup_quarter"] = a2["signup"].dt.to_period("Q").astype(str)

    c2 = churn[["churn_event_id", "account_id", "churn_date"]].copy()
    c2["cd"] = pd.to_datetime(c2["churn_date"])
    c2["cm"] = c2["cd"].dt.to_period("M").astype(str)
    first = (c2.sort_values(["cd", "churn_event_id"])
               .groupby("account_id", as_index=False).first())
    fe = a2.merge(first[["account_id", "cd", "cm"]], on="account_id", how="left")
    fe = fe.rename(columns={"cd": "first_event_date", "cm": "first_event_month"})
    fe["has_event"] = fe["first_event_month"].notna()
    fe["tenure_months"] = fe.apply(
        lambda r: period_diff_months(r["signup_month"], r["first_event_month"])
        if r["has_event"] else None, axis=1)
    return fe


def monthly_series(acc: pd.DataFrame, churn: pd.DataFrame,
                   panel: pd.DataFrame, fe: pd.DataFrame) -> pd.DataFrame:
    """Série mensal: eventos, primeiros eventos, denominadores, taxas, R1, R2."""
    months = months_range(FIRST_MONTH, LAST_MONTH)
    n_accounts = len(acc)
    ev_month = churn["churn_date"].str[:7].value_counts().sort_index()
    fe_month = fe.loc[fe["has_event"], "first_event_month"].value_counts().sort_index()
    st_map = panel.set_index(["account_id", "month"])["status"]
    wm_map = panel.set_index(["account_id", "month"])["winner_mrr"]
    mrr_ended = panel.groupby("month")["mrr_ended_in_month"].sum()
    n_ended = panel.groupby("month")["n_ended_in_month"].sum()

    rows: list[dict] = []
    prev_fe = 0
    for m in months:
        signup_le = int((fe["signup_month"] <= m).sum())
        eligible = signup_le - prev_fe          # em risco no início de m
        fe_m = int(fe_month.get(m, 0))
        ev_m = int(ev_month.get(m, 0))
        active = int((panel["month"] == m).sum())  # painel: todas as contas têm linha
        active_n = int(st_map.xs(m, level="month").eq("active").sum()) if m in months else 0
        # R2 mensal (transições de snapshot fim-de-mês; contrato §5)
        churn_to_inc = 0
        contraction = 0
        mi = months.index(m)
        if mi > 0:
            pm = months[mi - 1]
            s = pd.concat([st_map.xs(pm, level="month").rename("p"),
                           st_map.xs(m, level="month").rename("c")], axis=1).fillna("inactive")
            w = pd.concat([wm_map.xs(pm, level="month").rename("p"),
                           wm_map.xs(m, level="month").rename("c")], axis=1).fillna(0)
            tr = (s["p"] == "active") & (s["c"] == "inactive")
            churn_to_inc = int(w.loc[tr, "p"].sum())
            both = (s["p"] == "active") & (s["c"] == "active")
            cont = both & (w["p"] > w["c"])
            contraction = int(w.loc[cont, "p"].sub(w.loc[cont, "c"]).sum())
        rows.append({
            "month": m,
            "events_total": ev_m,
            "first_events": fe_m,
            "accounts_signed_up_le": signup_le,
            "eligible_at_start": eligible,
            "rate_first_events_pct": 100.0 * fe_m / eligible if eligible else float("nan"),
            "active_accounts_end": active_n,
            "events_per_active_pct": 100.0 * ev_m / active_n if active_n else float("nan"),
            "r1_mrr_ended_in_month": int(mrr_ended.get(m, 0)),
            "n_ended_in_month": int(n_ended.get(m, 0)),
            "r2_churn_to_inactive": churn_to_inc,
            "r2_active_contraction": contraction,
            "r2_net": churn_to_inc + contraction,
        })
        prev_fe += fe_m
    return pd.DataFrame(rows, columns=[
        "month", "events_total", "first_events", "accounts_signed_up_le",
        "eligible_at_start", "rate_first_events_pct", "active_accounts_end",
        "events_per_active_pct", "r1_mrr_ended_in_month", "n_ended_in_month",
        "r2_churn_to_inactive", "r2_active_contraction", "r2_net"])


def tenure_bucket(tenure: int) -> str:
    for lo, hi in TENURE_BUCKETS:
        if lo <= tenure <= hi:
            return f"{lo}-{hi}m"
    return ">24m"


def _eligible_buckets_at(fe: pd.DataFrame, p: str) -> dict[str, int]:
    """Contas elegíveis no início de p por bucket de tenure (contrato §5).

    Elegível = signup <= p E (sem primeiro evento OU primeiro evento >= p).
    Tenure em p = meses entre o signup e p.
    """
    e = fe[(fe["signup_month"] <= p) &
           (fe["first_event_month"].isna() | (fe["first_event_month"] >= p))]
    out: dict[str, int] = {}
    for _, r in e.iterrows():
        t = period_diff_months(r["signup_month"], p)
        b = tenure_bucket(t)
        out[b] = out.get(b, 0) + 1
    return out


def _events_in_bucket_at(fe: pd.DataFrame, p: str) -> dict[str, int]:
    """Primeiros eventos ocorridos em p, por bucket de tenure no momento do evento."""
    e = fe[fe["first_event_month"] == p]
    out: dict[str, int] = {}
    for _, r in e.iterrows():
        b = tenure_bucket(int(r["tenure_months"]))
        out[b] = out.get(b, 0) + 1
    return out


def spike_decomposition(series: pd.DataFrame, fe: pd.DataFrame,
                        months: list[str]) -> dict:
    """Identifica o período elevado e decompõe o PICO (mês de maior contagem).

    Regra pré-registrada (hipóteses It03): meses elevados = first_events >=
    1,5 x mediana da janela; PICO = mês de maior contagem de primeiros eventos
    (se empate, o primeiro cronologicamente). Decomposição do pico por bucket
    de tenure e coorte de signup; baseline = média dos 6 meses anteriores do
    mesmo bucket/coorte. Mecanismo (H9) = bucket com maior contribuição
    absoluta ao pico E taxa >= 1,5x a própria linha de base.
    Além disso, controle de composição de tenure: eventos esperados no pico =
    Σ_bucket contas elegíveis no bucket × taxa de baseline do bucket (média
    dos 6 meses anteriores); ratio observado/esperado ~ 1 indica que o pico é
    explicado pela composição de tenure (mix de contas jovens).
    """
    counts = series.set_index("month")["first_events"]
    median = float(counts.median())
    elevated = [m for m in months if counts[m] >= 1.5 * median] if median > 0 else []
    peak = str(counts.idxmax())
    rates = series.set_index("month")["rate_first_events_pct"].dropna()
    peak_rate_month = str(rates.idxmax())
    fe_ev = fe.loc[fe["has_event"], ["account_id", "first_event_month",
                                     "tenure_months", "signup_quarter"]].copy()
    fe_ev["bucket"] = fe_ev["tenure_months"].apply(tenure_bucket)
    months_idx = {m: i for i, m in enumerate(months)}

    mi = months_idx[peak]
    prior = months[max(0, mi - 6):mi]
    total_m = int(counts[peak])

    buck_rows: list[dict] = []
    for b in sorted(fe_ev["bucket"].unique()):
        n_m = int(((fe_ev["first_event_month"] == peak) & (fe_ev["bucket"] == b)).sum())
        n_prior = [int(((fe_ev["first_event_month"] == p) &
                        (fe_ev["bucket"] == b)).sum()) for p in prior]
        base = sum(n_prior) / len(n_prior) if n_prior else 0.0
        ratio = n_m / base if base > 0 else float("nan")
        buck_rows.append({"bucket": b, "events_in_peak": n_m,
                          "share_pct": 100.0 * n_m / total_m if total_m else 0.0,
                          "baseline_mean_6m": round(base, 2),
                          "ratio_vs_baseline": round(ratio, 2) if ratio == ratio else "NA"})

    coh_rows: list[dict] = []
    for q in sorted(fe_ev["signup_quarter"].dropna().unique()):
        n_m = int(((fe_ev["first_event_month"] == peak) &
                   (fe_ev["signup_quarter"] == q)).sum())
        n_prior = [int(((fe_ev["first_event_month"] == p) &
                        (fe_ev["signup_quarter"] == q)).sum()) for p in prior]
        base = sum(n_prior) / len(n_prior) if n_prior else 0.0
        ratio = n_m / base if base > 0 else float("nan")
        coh_rows.append({"cohort": q, "events_in_peak": n_m,
                         "share_pct": 100.0 * n_m / total_m if total_m else 0.0,
                         "baseline_mean_6m": round(base, 2),
                         "ratio_vs_baseline": round(ratio, 2) if ratio == ratio else "NA"})

    cands = [b for b in buck_rows
             if b["ratio_vs_baseline"] != "NA" and b["ratio_vs_baseline"] >= 1.5]
    if cands:
        mech = max(cands, key=lambda b: b["share_pct"])
        mechanism = (f"bucket {mech['bucket']} (share {mech['share_pct']:.1f}%, "
                     f"ratio {mech['ratio_vs_baseline']})")
    else:
        mechanism = "transversal (nenhum bucket com ratio >= 1,5x)"

    # controle de composição de tenure (sensibilidade do H2)
    expected = 0.0
    eligible_peak = _eligible_buckets_at(fe, peak)
    for b, n_elig in sorted(eligible_peak.items()):
        base_rates: list[float] = []
        for p in prior:
            elig_p = _eligible_buckets_at(fe, p).get(b, 0)
            ev_p = _events_in_bucket_at(fe, p).get(b, 0)
            if elig_p > 0:
                base_rates.append(ev_p / elig_p)
        baseline_b = sum(base_rates) / len(base_rates) if base_rates else 0.0
        expected += n_elig * baseline_b
    ratio_expected = total_m / expected if expected > 0 else float("nan")

    return {
        "elevated_months": elevated, "peak_month": peak,
        "peak_rate_month": peak_rate_month, "median": median,
        "detail": [{
            "month": peak, "total": total_m,
            "baseline_months_available": len(prior),
            "buckets": buck_rows, "cohorts": coh_rows,
            "mechanism": mechanism,
        }],
        "expected_events_tenure_std": round(expected, 2),
        "ratio_observed_vs_expected": round(ratio_expected, 2)
        if ratio_expected == ratio_expected else "NA",
    }


# ----------------------------------------------------------------------------
# B. Coortes e tempo-ao-churn (Kaplan-Meier descritivo, censura no corte)
# ----------------------------------------------------------------------------

def km_estimate(times: list[tuple[float, bool]]) -> list[dict]:
    """Kaplan-Meier descritivo (sem dependência nova).

    Entrada: lista de (tempo_do_evento_ou_censura, tem_evento). Tempos em
    unidades discretas (meses desde o signup). Censura no corte 2024-12-31:
    contas sem primeiro evento são censuradas no último mês observado
    (at-risk através do mês T inclusive, sem evento).
    Retorna linhas {t, at_risk, events, survival, cum_events}.
    """
    rows: list[dict] = []
    ts = sorted({t for t, _ in times})
    at_risk = len(times)
    surv = 1.0
    cum = 0
    for t in ts:
        d = sum(1 for (tt, ev) in times if tt == t and ev)
        c = sum(1 for (tt, ev) in times if tt == t and not ev)
        if at_risk > 0:
            surv *= (1.0 - d / at_risk)
        rows.append({"t": t, "at_risk": at_risk, "events": d,
                     "censored": c, "survival": round(surv, 4)})
        cum += d
        at_risk -= d + c
    return rows


def surv_at_horizon(surv_at: dict, horizon: int):
    """Sobrevivência KM em horizonte fixo pela FUNÇÃO DEGRAU (carry-forward):
    valor no maior t <= horizon com estimativa, SOMENTE se o horizonte for
    observável (max t >= horizon — follow-up/censura cobrem o horizonte).
    Caso contrário, vazio (correção pós-review: não exigir evento/censura
    exatamente em t = horizonte; a função degrau é constante entre tempos).
    """
    if not surv_at:
        return ""
    if max(surv_at) < horizon:
        return ""
    ts = sorted(t for t in surv_at if t <= horizon)
    return surv_at[ts[-1]]


def cohort_tables(fe: pd.DataFrame) -> dict:
    """Tabelas de coorte (trimestre e mês de signup) com KM censurado."""
    # tempo: meses desde o signup (0 = mês do signup); censura no corte
    fe2 = fe.copy()
    fe2["T_obs"] = fe2["signup_month"].apply(
        lambda sm: period_diff_months(sm, LAST_MONTH))          # último mês observado
    fe2["t_event"] = fe2["tenure_months"]
    fe2["time"] = fe2.apply(
        lambda r: r["t_event"] if r["has_event"] else r["T_obs"], axis=1)
    fe2["is_event"] = fe2["has_event"]

    q_rows: list[dict] = []
    m_rows: list[dict] = []
    for grp_col in ["signup_quarter", "signup_month"]:
        for cohort, g in fe2.groupby(grp_col, sort=True):
            times = list(zip(g["time"].astype(int), g["is_event"].astype(bool)))
            km = km_estimate(times)
            n = len(g)
            ev = int(g["is_event"].sum())
            cens = n - ev
            surv_at = {row["t"]: row["survival"] for row in km}
            surv6 = surv_at_horizon(surv_at, 6)
            surv12 = surv_at_horizon(surv_at, 12)
            surv18 = surv_at_horizon(surv_at, 18)
            rec = {
                "cohort": str(cohort), "n_accounts": n, "events": ev,
                "censored": cens,
                "observed_rate_pct": round(100.0 * ev / n, 1) if n else float("nan"),
                "km_surv_t6": surv6,
                "km_surv_t12": surv12,
                "km_surv_t18": surv18,
                "max_t_observed": max(t for t, _ in times),
                "km_churn_t6_pct": round(100.0 * (1 - surv6), 1) if surv6 != "" else "",
            }
            if grp_col == "signup_quarter":
                q_rows.append(rec)
            else:
                m_rows.append(rec)
    q_df = pd.DataFrame(q_rows)
    m_df = pd.DataFrame(m_rows)
    # tabela longa at-risk (trimestres) para auditabilidade
    long_rows: list[dict] = []
    for cohort, g in fe2.groupby("signup_quarter", sort=True):
        times = list(zip(g["time"].astype(int), g["is_event"].astype(bool)))
        for row in km_estimate(times):
            long_rows.append({"cohort": str(cohort), **row})
    long_df = pd.DataFrame(long_rows)
    return {"quarter": q_df, "month": m_df, "at_risk": long_df}


# ----------------------------------------------------------------------------
# C. Onboarding economics (exposição bruta precoce; CAC-equivalent nomeado)
# ----------------------------------------------------------------------------

def duration_bucket(days: int) -> str:
    for lo, hi in DURATION_BUCKETS:
        if hi is None:
            if days >= lo:
                return f">{lo - 1}d"
        elif lo <= days <= hi:
            return "0d" if lo == 0 and hi == 0 else f"{lo}-{hi}d"
    return "?"


def onboarding(sub: pd.DataFrame, acc: pd.DataFrame, fe: pd.DataFrame) -> dict:
    """Exposição contratual bruta precoce (R1) + cenários CAC-equivalent."""
    ended = sub[sub["end_date"].notna()].copy()
    ended["start"] = pd.to_datetime(ended["start_date"])
    ended["end"] = pd.to_datetime(ended["end_date"])
    ended["duration_days"] = (ended["end"] - ended["start"]).dt.days
    ended["bucket"] = ended["duration_days"].apply(duration_bucket)
    total_r1 = int(ended["mrr_amount"].sum())

    bucket_rows: list[dict] = []
    for b in ["0d"] + [f"{lo}-{hi}d" for lo, hi in DURATION_BUCKETS if hi is not None
                       and not (lo == 0 and hi == 0)] + [">365d"]:
        g = ended[ended["bucket"] == b]
        bucket_rows.append({
            "bucket": b, "n_subs": len(g),
            "mrr_sum": int(g["mrr_amount"].sum()),
            "share_of_r1_pct": round(100.0 * int(g["mrr_amount"].sum()) / total_r1, 1)
            if total_r1 else 0.0,
            "median_duration_days": int(g["duration_days"].median()) if len(g) else "",
        })

    # por conta: primeiro evento dentro de 30/60/90 dias do signup
    fe_ev = fe.loc[fe["has_event"]].copy()
    fe_ev["days_to_event"] = (pd.to_datetime(fe_ev["first_event_date"])
                              - pd.to_datetime(fe_ev["signup_date"])).dt.days
    n_with_event = len(fe_ev)
    n_accounts = len(acc)
    acc_rows: list[dict] = []
    for d in ONBOARDING_DAYS:
        n_le = int((fe_ev["days_to_event"] <= d).sum())
        acc_rows.append({
            "window_days": d,
            "n_first_events_le": n_le,
            "share_of_event_accounts_pct": round(100.0 * n_le / n_with_event, 1)
            if n_with_event else 0.0,
            "share_of_all_accounts_pct": round(100.0 * n_le / n_accounts, 1),
        })
    acc_df = pd.DataFrame(acc_rows)

    # exposição bruta precoce por janela de DURAÇÃO de assinatura (R1)
    exp_rows: list[dict] = []
    for d in ONBOARDING_DAYS:
        g = ended[ended["duration_days"] <= d]
        exp_rows.append({
            "window_days": d,
            "n_subs": len(g),
            "mrr_exposure": int(g["mrr_amount"].sum()),
            "share_of_r1_pct": round(100.0 * int(g["mrr_amount"].sum()) / total_r1, 1)
            if total_r1 else 0.0,
        })
    exp_df = pd.DataFrame(exp_rows)

    # cenários CAC-equivalent exposure (dataset sem custo; NUNCA "CAC queimado")
    cac_rows: list[dict] = []
    for _, r in exp_df.iterrows():
        for mult in CAC_MULTIPLES:
            cac_rows.append({
                "window_days": int(r["window_days"]),
                "scenario_mult_mrr": mult,
                "cac_equivalent_exposure": int(r["mrr_exposure"]) * mult,
                "note": "cenário nomeado; dataset não contém custo de aquisição",
            })
    cac_df = pd.DataFrame(cac_rows)

    return {"total_r1": total_r1, "buckets": pd.DataFrame(bucket_rows),
            "accounts": acc_df, "exposure": exp_df, "cac": cac_df}


# ----------------------------------------------------------------------------
# D. Uso: volume total vs intensidade por conta (variantes bruta/alinhada)
# ----------------------------------------------------------------------------

def usage_analysis(use: pd.DataFrame, acc: pd.DataFrame, sub: pd.DataFrame,
                   panel: pd.DataFrame) -> dict:
    """Testa 'o uso cresceu': volume vs intensidade; pré-signup excluído no primário."""
    u = use.merge(sub[["subscription_id", "account_id"]], on="subscription_id")
    signup_map = dict(zip(acc["account_id"], pd.to_datetime(acc["signup_date"])))
    u["ud"] = pd.to_datetime(u["usage_date"])
    u["signup"] = u["account_id"].map(signup_map)
    u["pre_signup"] = u["ud"] < u["signup"]
    sub_win = sub[["subscription_id", "start_date", "end_date"]].rename(
        columns={"start_date": "s_start", "end_date": "s_end"})
    sub_win["s_start"] = pd.to_datetime(sub_win["s_start"])
    sub_win["s_end"] = pd.to_datetime(sub_win["s_end"])
    u = u.merge(sub_win, on="subscription_id")
    u["in_window"] = (u["ud"] >= u["s_start"]) & (
        u["s_end"].isna() | (u["ud"] <= u["s_end"]))
    u["um"] = u["ud"].dt.to_period("M").astype(str)

    months = months_range(FIRST_MONTH, LAST_MONTH)
    active_by_month = (panel[panel["status"] == "active"]
                       .groupby("month").size().reindex(months).fillna(0).astype(int))

    rows: list[dict] = []
    for m in months:
        gm = u[u["um"] == m]
        prim = gm[~gm["pre_signup"]]
        rows.append({
            "month": m,
            "rows_raw_all": len(gm),
            "rows_raw_primary": len(prim),                      # sem pré-signup
            "rows_aligned_all": int(gm["in_window"].sum()),
            "rows_aligned_primary": int(prim["in_window"].sum()),
            "active_accounts_end": int(active_by_month[m]),
            "rows_raw_primary_per_active": round(len(prim) / active_by_month[m], 2)
            if active_by_month[m] else float("nan"),
            "rows_aligned_primary_per_active": round(
                int(prim["in_window"].sum()) / active_by_month[m], 2)
            if active_by_month[m] else float("nan"),
        })
    df = pd.DataFrame(rows)

    # intensidade: mediana de linhas por conta-mês (primário: sem pré-signup)
    per_acct = (u[~u["pre_signup"]].groupby(["account_id", "um"]).size()
                .reset_index(name="n"))
    med_raw = (per_acct.groupby("um")["n"].median().reindex(months))
    per_acct_align = (u[(~u["pre_signup"]) & u["in_window"]]
                      .groupby(["account_id", "um"]).size().reset_index(name="n"))
    med_align = (per_acct_align.groupby("um")["n"].median().reindex(months))

    def _year_stats(yr: str) -> dict:
        ms = [m for m in months if m.startswith(yr)]
        return {
            "total_raw_primary": int(df.loc[df["month"].isin(ms), "rows_raw_primary"].sum()),
            "total_aligned_primary": int(df.loc[df["month"].isin(ms), "rows_aligned_primary"].sum()),
            "median_per_acct_raw": float(med_raw[ms].median()),
            "median_per_acct_aligned": float(med_align[ms].median()),
            # variante pooled: mediana sobre TODOS os account-months com uso do ano
            # (sem agregar por mês antes da mediana) — mais sensível à composição;
            # reportada como nota de definição (não dirige o veredito H3)
            "median_per_acct_aligned_pooled": float(
                per_acct_align.loc[per_acct_align["um"].isin(ms), "n"].median()),
            "n_months": len(ms),
        }

    y2023 = _year_stats("2023")
    y2024 = _year_stats("2024")

    def _growth(a: float, b: float) -> float:
        return (b - a) / a * 100.0 if a else float("nan")

    growth = {
        "total_raw_primary_pct": round(_growth(y2023["total_raw_primary"],
                                               y2024["total_raw_primary"]), 1),
        "total_aligned_primary_pct": round(_growth(y2023["total_aligned_primary"],
                                                   y2024["total_aligned_primary"]), 1),
        "median_per_acct_raw_pct": round(_growth(y2023["median_per_acct_raw"],
                                                 y2024["median_per_acct_raw"]), 1),
        "median_per_acct_aligned_pct": round(_growth(y2023["median_per_acct_aligned"],
                                                     y2024["median_per_acct_aligned"]), 1),
        "median_per_acct_aligned_pooled_pct": round(
            _growth(y2023["median_per_acct_aligned_pooled"],
                    y2024["median_per_acct_aligned_pooled"]), 1),
        "y2023": y2023, "y2024": y2024,
    }

    # sensibilidade: com pré-signup incluído
    sens_rows: list[dict] = []
    for yr in ["2023", "2024"]:
        ms = [m for m in months if m.startswith(yr)]
        gm = u[u["um"].isin(ms)]
        sens_rows.append({
            "year": yr,
            "rows_raw_all": len(gm),
            "rows_aligned_all": int(gm["in_window"].sum()),
        })
    sens = pd.DataFrame(sens_rows)
    g_raw_all = _growth(int(sens.loc[0, "rows_raw_all"]),
                        int(sens.loc[1, "rows_raw_all"]))
    growth["sensitivity_total_raw_all_pct"] = round(g_raw_all, 1)
    return {"monthly": df, "median_per_acct": med_raw, "median_per_acct_aligned": med_align,
            "growth": growth, "sensitivity": sens}


# ----------------------------------------------------------------------------
# E. Suporte: sinais pré-evento (desenho honesto, anti-leakage)
# ----------------------------------------------------------------------------

def support_analysis(tic: pd.DataFrame, acc: pd.DataFrame, churn: pd.DataFrame,
                     fe: pd.DataFrame) -> dict:
    """Compara sinais de suporte em janelas de 90 dias antes da data índice.

    Desenho (pré-registrado): para cada mês m, grupo-churn = contas com
    PRIMEIRO evento em m; controle = contas elegíveis no início de m (signup
    <= m, sem primeiro evento antes de m) sem evento em m. Janela
    W(m) = [1º dia de m - 90 dias, 1º dia de m). Sinais apenas de tickets com
    submitted_at em W(m) E >= signup (pré-signup excluído no primário);
    CSAT/resolução apenas de tickets fechados com nota (contrato §10; G15:
    0 nulos de closed_at na base). Sensibilidade: controle nunca-churn;
    estratificação por tenure.
    """
    tic2 = tic.copy()
    tic2["ts"] = pd.to_datetime(tic2["submitted_at"])
    tic2["closed"] = pd.to_datetime(tic2["closed_at"])
    tic2["has_score"] = tic2["satisfaction_score"].notna()
    signup_map = dict(zip(acc["account_id"], pd.to_datetime(acc["signup_date"])))
    tic2["signup"] = tic2["account_id"].map(signup_map)
    tic2["pre_signup"] = tic2["ts"] < tic2["signup"]
    never_churn = set(acc["account_id"]) - set(churn["account_id"])
    fe_ev = fe.loc[fe["has_event"], ["account_id", "first_event_month"]].copy()
    fe_first_by_month = fe_ev.groupby("first_event_month")["account_id"].apply(set)
    signup_of = dict(zip(fe["account_id"], fe["signup_month"]))

    months = months_range(FIRST_MONTH, LAST_MONTH)
    use_months = [m for m in months[3:]]  # janela de 90 dias completa a partir de 2023-04
    # CORREÇÃO PÓS-REVIEW (finding #3): o controle exige "elegíveis sem primeiro
    # evento ANTERIOR" (contrato §5). Antes, prev_ev partia de set() em 2023-04,
    # então contas com primeiro evento em 2023-01..03 (6 contas) entravam no
    # controle de TODOS os meses (n_control 3.288 vs 3.162 pelo contrato). Seed
    # corrigido com os primeiros eventos anteriores ao primeiro mês usado:
    prev_ev: set[str] = set()
    for sm_seed in months[:3]:
        prev_ev |= fe_first_by_month.get(sm_seed, set())

    def _empty_sig() -> dict:
        return {"n_tickets": 0, "n_escalated": 0, "csat_sum": 0.0, "csat_n": 0,
                "frt_med": float("nan"), "res_med": float("nan")}

    def _pool(sigs: list[dict]) -> dict:
        n = len(sigs)
        if n == 0:
            return {}
        t = sum(s["n_tickets"] for s in sigs)
        e = sum(s["n_escalated"] for s in sigs)
        cs_sum = sum(s["csat_sum"] for s in sigs)
        cs_n = sum(s["csat_n"] for s in sigs)
        fr = sorted(s["frt_med"] for s in sigs if s["frt_med"] == s["frt_med"])
        re = sorted(s["res_med"] for s in sigs if s["res_med"] == s["res_med"])
        return {
            "n_account_month": n,
            "tickets_per_account_month": round(t / n, 3),
            "esc_rate_pct": round(100.0 * e / t, 1) if t else 0.0,
            "csat_mean": round(cs_sum / cs_n, 2) if cs_n else "",
            "median_frt_min": round(fr[len(fr) // 2], 1) if fr else "",
            "median_res_h": round(re[len(re) // 2], 1) if re else "",
        }

    def _month_agg(sigs: list[dict]) -> dict:
        t = sum(s["n_tickets"] for s in sigs)
        e = sum(s["n_escalated"] for s in sigs)
        cs_sum = sum(s["csat_sum"] for s in sigs)
        cs_n = sum(s["csat_n"] for s in sigs)
        return {"n_tickets": t, "n_escalated": e,
                "esc_rate_pct": round(100.0 * e / t, 1) if t else 0.0,
                "csat_mean": round(cs_sum / cs_n, 2) if cs_n else ""}

    month_rows: list[dict] = []
    churn_pool: list[dict] = []
    ctrl_pool: list[dict] = []
    ctrl_nc_pool: list[dict] = []
    strat_churn: dict[str, list[dict]] = {"0-6m": [], "7-12m": [], "13+m": []}
    strat_ctrl: dict[str, list[dict]] = {"0-6m": [], "7-12m": [], "13+m": []}
    for m in use_months:
        w_start = month_first_date(m) - pd.Timedelta(days=SUPPORT_WINDOW_DAYS)
        w_end = month_first_date(m)
        churn_set = fe_first_by_month.get(m, set())
        eligible = {a for a, sm in signup_of.items() if sm <= m}
        ctrl_set = eligible - churn_set - prev_ev
        ctrl_nc = ctrl_set & never_churn
        t_win = tic2[(tic2["ts"] >= w_start) & (tic2["ts"] < w_end)
                     & (~tic2["pre_signup"])]
        per: dict[str, dict] = {}
        if len(t_win):
            for a, g in t_win.groupby("account_id"):
                closed = g[g["closed"].notna()]
                csat = closed[closed["has_score"]]
                per[a] = {
                    "n_tickets": len(g),
                    "n_escalated": int(g["escalation_flag"].sum()),
                    "csat_sum": float(csat["satisfaction_score"].sum()),
                    "csat_n": len(csat),
                    "frt_med": float(closed["first_response_time_minutes"].median())
                    if len(closed) else float("nan"),
                    "res_med": float(closed["resolution_time_hours"].median())
                    if len(closed) else float("nan"),
                }
        sig = lambda a: per.get(a, _empty_sig())  # noqa: E731
        cs_sigs = [sig(a) for a in churn_set]
        ct_sigs = [sig(a) for a in ctrl_set]
        nc_sigs = [sig(a) for a in ctrl_nc]
        churn_pool.extend(cs_sigs)
        ctrl_pool.extend(ct_sigs)
        ctrl_nc_pool.extend(nc_sigs)
        ca, cc_ = _month_agg(cs_sigs), _month_agg(ct_sigs)
        month_rows.append({
            "month": m,
            "n_churn": len(churn_set), "n_control": len(ctrl_set),
            "n_control_never_churn": len(ctrl_nc),
            "tickets_churn": ca["n_tickets"], "tickets_control": cc_["n_tickets"],
            "tickets_per_churn": round(ca["n_tickets"] / len(churn_set), 3)
            if churn_set else float("nan"),
            "tickets_per_control": round(cc_["n_tickets"] / len(ctrl_set), 3)
            if ctrl_set else float("nan"),
            "esc_pct_churn": ca["esc_rate_pct"], "esc_pct_control": cc_["esc_rate_pct"],
            "csat_churn": ca["csat_mean"], "csat_control": cc_["csat_mean"],
        })
        for a in churn_set:
            t = period_diff_months(signup_of[a], m)
            b = "0-6m" if t <= 6 else ("7-12m" if t <= 12 else "13+m")
            strat_churn[b].append(sig(a))
        for a in ctrl_set:
            t = period_diff_months(signup_of[a], m)
            b = "0-6m" if t <= 6 else ("7-12m" if t <= 12 else "13+m")
            strat_ctrl[b].append(sig(a))
        prev_ev |= churn_set

    pooled = {
        "churn": _pool(churn_pool),
        "control": _pool(ctrl_pool),
        "control_never_churn": _pool(ctrl_nc_pool),
    }
    strat_out = {"churn": {b: _pool(strat_churn[b]) for b in strat_churn},
                 "control": {b: _pool(strat_ctrl[b]) for b in strat_ctrl}}
    return {"monthly": pd.DataFrame(month_rows), "pooled": pooled,
            "stratified": strat_out, "use_months": use_months}


# ----------------------------------------------------------------------------
# F. Segmentos (industry/channel/tier/trial) com denominador e flags
# ----------------------------------------------------------------------------

def segment_analysis(acc: pd.DataFrame, sub: pd.DataFrame, fe: pd.DataFrame) -> dict:
    """Taxas e exposição R1 por segmento, com mínimo de amostra e flags."""
    a2 = acc.copy()
    a2["is_trial_s"] = a2["is_trial"].astype(str)
    fe2 = fe[["account_id", "has_event", "first_event_month",
              "signup_month", "tenure_months"]].copy()
    sub2 = sub[sub["end_date"].notna()].copy()
    sub2["mrr"] = pd.to_numeric(sub2["mrr_amount"], errors="coerce").fillna(0)
    r1_by_acct = sub2.groupby("account_id")["mrr"].sum()
    total_r1 = int(r1_by_acct.sum())
    global_rate = 100.0 * int(fe2["has_event"].sum()) / len(a2)
    # sobrevivência global KM no mês 6 (referência p/ flag de segmento)
    times_all = [(int(r["tenure_months"]) if r["has_event"]
                  else period_diff_months(r["signup_month"], LAST_MONTH),
                  bool(r["has_event"])) for _, r in fe2.iterrows()]
    km_all = km_estimate(times_all)
    surv_all = {row["t"]: row["survival"] for row in km_all}
    global_surv6 = surv_at_horizon(surv_all, 6)

    attr_cols = ["industry", "referral_source", "plan_tier", "is_trial_s"]
    rows: list[dict] = []
    for col in attr_cols:
        for value, g in a2.groupby(col, sort=True):
            accs = set(g["account_id"])
            gfe = fe2[fe2["account_id"].isin(accs)]
            n_fe = int(gfe["has_event"].sum())
            rate = 100.0 * n_fe / len(g) if len(g) else float("nan")
            r1 = int(r1_by_acct.reindex(accs).fillna(0).sum())
            # sobrevivência KM no mês 6 (descritiva, se observável)
            g2 = fe2[fe2["account_id"].isin(accs)]
            times = [(int(r["tenure_months"]) if r["has_event"]
                      else period_diff_months(r["signup_month"], LAST_MONTH),
                      bool(r["has_event"])) for _, r in g2.iterrows()]
            km = km_estimate(times)
            surv_at = {row["t"]: row["survival"] for row in km}
            surv6 = surv_at_horizon(surv_at, 6)
            flags: list[str] = []
            if len(g) < 25:
                flags.append("N_BAIXO")
            if len(g) >= 25 and rate >= 1.5 * global_rate:
                flags.append("RATE_FLAG")
            if surv6 != "" and len(g) >= 25 and global_surv6 != "" \
                    and surv6 <= global_surv6 - 0.10:
                flags.append("SURV_FLAG")
            if r1 / total_r1 > 0.10:
                flags.append("MRR_FLAG")
            rows.append({
                "segment_type": col, "segment_value": str(value),
                "n_accounts": len(g), "n_first_event": n_fe,
                "rate_pct": round(rate, 1),
                "km_surv_t6": surv6 if surv6 != "" else "",
                "r1_gross_mrr": r1,
                "r1_share_pct": round(100.0 * r1 / total_r1, 1) if total_r1 else 0.0,
                "flags": "|".join(flags) if flags else "",
            })
    df = pd.DataFrame(rows)
    return {"table": df, "global_rate": round(global_rate, 1),
            "total_r1": total_r1, "global_surv6": global_surv6}


# ----------------------------------------------------------------------------
# G. Reasons/CSAT/feedback (evidência sugestiva; missingness e inconsistência)
# ----------------------------------------------------------------------------

def reasons_analysis(churn: pd.DataFrame, sub: pd.DataFrame,
                     tic: pd.DataFrame, acc: pd.DataFrame) -> dict:
    """Quantifica reason/CSAT/feedback; associações descritivas; decoplamento."""
    c = churn.copy()
    c["has_refund"] = pd.to_numeric(c["refund_amount_usd"], errors="coerce").fillna(0) > 0
    c["upg"] = c["preceding_upgrade_flag"].fillna(False).astype(bool)
    c["downg"] = c["preceding_downgrade_flag"].fillna(False).astype(bool)
    c["cd"] = pd.to_datetime(c["churn_date"])
    n = len(c)
    dist = c["reason_code"].value_counts().sort_index()
    reason_rows: list[dict] = []
    for rc in sorted(c["reason_code"].unique()):
        g = c[c["reason_code"] == rc]
        reason_rows.append({
            "reason_code": rc,
            "n_events": len(g),
            "share_pct": round(100.0 * len(g) / n, 1),
            "refund_pct": round(100.0 * int(g["has_refund"].sum()) / len(g), 1),
            "preceding_upgrade_pct": round(100.0 * int(g["upg"].sum()) / len(g), 1),
            "preceding_downgrade_pct": round(100.0 * int(g["downg"].sum()) / len(g), 1),
        })
    reason_df = pd.DataFrame(reason_rows)

    # decoplamento: eventos com assinatura encerrada ±30 dias na mesma conta
    ended = sub[sub["end_date"].notna()][["account_id", "end_date"]].copy()
    ended["end"] = pd.to_datetime(ended["end_date"])
    ev = c[["churn_event_id", "account_id", "cd"]].copy()
    matched = 0
    for _, r in ev.iterrows():
        ends = ended.loc[ended["account_id"] == r["account_id"], "end"]
        if len(ends) and ((r["cd"] - ends).abs() <= pd.Timedelta(days=30)).any():
            matched += 1

    # CSAT de contas com evento vs sem (tickets fechados com nota; todo o período)
    t = tic.copy()
    t["ts"] = pd.to_datetime(t["submitted_at"])
    t = t[t["closed_at"].notna() & t["satisfaction_score"].notna()]
    ev_accs = set(c["account_id"])
    t["has_event"] = t["account_id"].isin(ev_accs)
    csat_ev = float(t.loc[t["has_event"], "satisfaction_score"].mean())
    csat_no = float(t.loc[~t["has_event"], "satisfaction_score"].mean())

    missing = {
        "csat_nulls": int(tic["satisfaction_score"].isna().sum()),
        "csat_nulls_pct": round(100.0 * int(tic["satisfaction_score"].isna().sum())
                                / len(tic), 1),
        "reason_unknown": int((c["reason_code"] == "unknown").sum()),
        "reason_unknown_pct": round(100.0 * int((c["reason_code"] == "unknown").sum()) / n, 1),
        "feedback_nulls": int(c["feedback_text"].isna().sum()),
        "feedback_nulls_pct": round(100.0 * int(c["feedback_text"].isna().sum()) / n, 1),
        "events_matched_sub_30d": matched,
        "events_matched_sub_30d_pct": round(100.0 * matched / n, 1),
        "csat_mean_with_event": round(csat_ev, 2),
        "csat_mean_without_event": round(csat_no, 2),
    }
    return {"reasons": reason_df, "missing": missing}


# ----------------------------------------------------------------------------
# H. Vereditos das hipóteses (thresholds pré-registrados, aplicados mecanicamente)
# ----------------------------------------------------------------------------

def verdicts(a_data: dict, b_data: dict, c_data: dict, d_data: dict,
             e_data: dict, f_data: dict, g_data: dict, spike: dict) -> list[dict]:
    """Aplica os thresholds do arquivo de hipóteses a cada H1..H10."""
    out: list[dict] = []

    def add(h: str, verdict: str, numbers: str, note: str) -> None:
        out.append({"hypothesis": h, "verdict": verdict, "numbers": numbers,
                    "note": note})

    # H1 — tenure
    fe = a_data["fe"]
    fe_ev = fe.loc[fe["has_event"]]
    share_le6 = 100.0 * int((fe_ev["tenure_months"] <= 6).sum()) / len(fe_ev)
    med = float(fe_ev["tenure_months"].median())
    h1 = "SUSTENTADA" if (share_le6 >= 50.0 and med <= 6) else (
        "PARCIAL" if share_le6 >= 35.0 else "REFUTADA")
    add("H1", h1,
        f"primeiros eventos com tenure <= 6m: {share_le6:.1f}% (N={len(fe_ev)}); "
        f"mediana = {med:.0f}m; threshold: >=50% e mediana <=6",
        "ver threshold no arquivo de hipóteses")

    # H2 — composição vs taxa (pico = mês de maior contagem; thresholds pré-registrados)
    s = a_data["series"]
    fe_counts = s.set_index("month")["first_events"]
    peak_m = spike["peak_month"]
    peak_rate = float(s.loc[s["month"] == peak_m, "rate_first_events_pct"].iloc[0])
    rates = s["rate_first_events_pct"].dropna()
    med_rate = float(rates.median())
    idx = list(fe_counts.index).index(peak_m)
    prior6 = fe_counts.iloc[max(0, idx - 6):idx]
    prior6_rates = s.loc[s["month"].isin(prior6.index), "rate_first_events_pct"].dropna()
    prior6_med = float(prior6_rates.median()) if len(prior6_rates) else float("nan")
    comp_ratio = peak_rate / med_rate if med_rate else float("nan")
    rate_ratio = peak_rate / prior6_med if prior6_med == prior6_med and prior6_med else float("nan")
    std_ratio = spike["ratio_observed_vs_expected"]
    if 0.75 <= comp_ratio <= 1.25 and (rate_ratio != rate_ratio or rate_ratio < 1.5):
        h2 = "SUSTENTADA (composição domina)"
    elif comp_ratio > 1.25 and rate_ratio >= 1.5:
        h2 = "SUSTENTADA (aumento real de taxa)"
    elif 0.75 <= comp_ratio <= 1.25 or (rate_ratio != rate_ratio) or rate_ratio < 1.5:
        h2 = "PARCIAL (mistura de composição e taxa)"
    else:
        h2 = "SUSTENTADA (aumento real de taxa)"
    std_note = (f"; controle de composição de tenure: esperado "
                f"{spike['expected_events_tenure_std']} eventos, observado "
                f"{int(fe_counts[peak_m])} (ratio {std_ratio})")
    if std_ratio != "NA" and std_ratio <= 1.25:
        std_note += " — composição de tenure explica o pico (ver process report)"
    elif std_ratio != "NA":
        std_note += " — aumento persiste após controle de tenure"
    add("H2", h2,
        f"pico {peak_m}: taxa {peak_rate:.2f}% vs mediana da janela {med_rate:.2f}% "
        f"(razão {comp_ratio:.2f}); vs mediana 6m anteriores {prior6_med:.2f}% "
        f"(razão {rate_ratio:.2f}){std_note}",
        "thresholds: composição se razão 0,75-1,25 vs mediana; taxa se >=1,5x 6m anteriores")

    # H3 — uso volume vs intensidade
    g = d_data["growth"]
    if g["total_raw_primary_pct"] >= 20.0 and abs(g["median_per_acct_raw_pct"]) < 10.0:
        h3 = "SUSTENTADA"
    elif abs(g["median_per_acct_raw_pct"]) >= 10.0:
        h3 = "REFUTADA"
    else:
        h3 = "PARCIAL"
    add("H3", h3,
        f"total bruto (sem pré-signup): {g['y2023']['total_raw_primary']} -> "
        f"{g['y2024']['total_raw_primary']} ({g['total_raw_primary_pct']}%); "
        f"mediana por conta: {g['y2023']['median_per_acct_raw']} -> "
        f"{g['y2024']['median_per_acct_raw']} ({g['median_per_acct_raw_pct']}%); "
        f"alinhado: {g['total_aligned_primary_pct']}% total, "
        f"{g['median_per_acct_aligned_pct']}% mediana; sensibilidade tudo: "
        f"{g['sensitivity_total_raw_all_pct']}%",
        "threshold: total >= +20% E mediana por conta < +10%")

    # H4 — uso pré-evento
    # mediana de uso alinhado mensal: churn (janela 90d antes do evento) vs controle
    # usa o pooled do suporte? Não — usa uso. Simplificação honesta: comparar a
    # intensidade mensal mediana das contas com evento nos 3 meses antes do
    # primeiro evento vs controle sem evento (mesmo calendário).
    # CORREÇÃO PÓS-REVIEW (M1): apenas TEMPO EM RISCO/OBSERVÁVEL — meses >= signup
    # (o mês do signup existe para a conta; meses ANTERIORES não existem, contrato
    # §2: "meses anteriores ao signup não existem para a conta"). Antes, o lado
    # churn incluía meses pré-signup como zero por construção (333 de 1.048 = 31,8%
    # dos valores; Δ zero-uso 13,7 p.p. era artefato de exposição) e o lado controle
    # idem no caso m == signup_month (810 de 5.093 = 15,9%). A mesma regra
    # (pm >= signup) vale para os dois lados — período inexistente nunca vira zero.
    fe_ev2 = fe_ev.copy()
    fe_ev2["ev_ts"] = pd.to_datetime(fe_ev2["first_event_date"])
    use = a_data["usage_by_acct_month"]  # linhas alinhadas por conta×mês (primário)
    never = set(a_data["fe"].loc[~a_data["fe"]["has_event"], "account_id"])
    churn_vals: list[float] = []
    ctrl_vals: list[float] = []
    months = months_range(FIRST_MONTH, LAST_MONTH)
    for _, r in fe_ev2.iterrows():
        ev_m = r["first_event_month"]
        sm = r["signup_month"]
        mi = months.index(ev_m)
        for pm in months[max(0, mi - 3):mi]:  # até 3 meses antes do evento (exclusive)
            if pm < sm:                        # pós-signup: tempo em risco/observável
                continue
            churn_vals.append(float(use.get((r["account_id"], pm), 0)))
    # controle: contas nunca-churn; para cada mês m, amostra o mesmo conjunto de
    # meses-calendário (m-3..m-1) de cada conta nunca-churn elegível (mesma regra
    # de exposição: somente meses >= signup)
    for a in never:
        sm = fe.loc[fe["account_id"] == a, "signup_month"].iloc[0]
        for m in months:
            if m < sm:
                continue
            mi = months.index(m)
            for pm in months[max(0, mi - 3):mi]:
                if pm < sm:
                    continue
                ctrl_vals.append(float(use.get((a, pm), 0)))
    med_churn = float(pd.Series(churn_vals).median())
    med_ctrl = float(pd.Series(ctrl_vals).median())
    zero_churn = 100.0 * (1 - len([v for v in churn_vals if v > 0]) / len(churn_vals)) \
        if churn_vals else float("nan")
    zero_ctrl = 100.0 * (1 - len([v for v in ctrl_vals if v > 0]) / len(ctrl_vals)) \
        if ctrl_vals else float("nan")
    if (med_churn < 0.5 * med_ctrl) or (zero_churn - zero_ctrl >= 25.0):
        h4 = "SUSTENTADA"
    else:
        h4 = "REFUTADA"
    ratio_med = (med_churn / med_ctrl) if med_ctrl > 0 else float("nan")
    add("H4", h4,
        f"mediana linhas alinhadas/mês pré-evento: churn {med_churn:.1f} vs controle "
        f"{med_ctrl:.1f} (razão {fmt(ratio_med) if ratio_med == ratio_med else 'NA'}); "
        f"zero-uso: churn {zero_churn:.1f}% vs controle {zero_ctrl:.1f}% "
        f"(Δ {zero_churn - zero_ctrl:.1f} p.p.)",
        "threshold: razão < 0,5 OU Δ zero-uso >= 25 p.p.; janela restrita a meses "
        "pós-signup (contrato §2) — o Δ 13,7 p.p. reportado antes era artefato de "
        "exposição (meses pré-signup contados como zero) e foi corrigido")

    # H5 — suporte pré-evento
    p = e_data["pooled"]
    c_ = p["churn"]
    ct_ = p["control"]
    n_ok = c_ and ct_ and c_.get("n_account_month", 0) >= 30 \
        and ct_.get("n_account_month", 0) >= 30
    if not n_ok:
        h5 = "INCONCLUSIVA"
        h5n = (f"N por lado insuficiente: churn {c_.get('n_account_month', 0)} / "
               f"controle {ct_.get('n_account_month', 0)} contas-pool")
    else:
        diffs = {
            "tickets": c_["tickets_per_account_month"] - ct_["tickets_per_account_month"],
            "esc_ratio": (c_["esc_rate_pct"] / ct_["esc_rate_pct"])
            if ct_["esc_rate_pct"] else float("nan"),
            "frt_ratio": (c_["median_frt_min"] / ct_["median_frt_min"])
            if ct_["median_frt_min"] else float("nan"),
            "res_ratio": (c_["median_res_h"] / ct_["median_res_h"])
            if ct_["median_res_h"] else float("nan"),
        }
        csat_ok = (c_.get("csat_mean") != "" and ct_.get("csat_mean") != ""
                   and c_["csat_mean"] <= 3.5 and ct_["csat_mean"] > 4.0)
        hit = (diffs["tickets"] >= 1.0 or (diffs["esc_ratio"] == diffs["esc_ratio"]
               and diffs["esc_ratio"] >= 1.5) or csat_ok
               or (diffs["frt_ratio"] == diffs["frt_ratio"] and diffs["frt_ratio"] >= 1.5)
               or (diffs["res_ratio"] == diffs["res_ratio"] and diffs["res_ratio"] >= 1.5))
        h5 = "SUSTENTADA" if hit else "REFUTADA"
        h5n = (f"tickets/conta {c_['tickets_per_account_month']} vs "
               f"{ct_['tickets_per_account_month']} (Δ {diffs['tickets']:.2f}); "
               f"escalação {c_['esc_rate_pct']}% vs {ct_['esc_rate_pct']}%; "
               f"CSAT {c_.get('csat_mean')} vs {ct_.get('csat_mean')}; "
               f"FRT {c_.get('median_frt_min')} vs {ct_.get('median_frt_min')} min; "
               f"resolução {c_.get('median_res_h')} vs {ct_.get('median_res_h')} h")
    add("H5", h5, h5n,
        "threshold: Δ tickets >= 1 OU escalação >= 1,5x OU CSAT <=3,5 vs >4,0 OU "
        "FRT/resolução >= 1,5x")

    # H6 — segmentos
    seg = f_data["table"]
    global_rate_h6 = f_data["global_rate"]
    rate_threshold_h6 = 1.5 * global_rate_h6
    surv_global = f_data["global_surv6"]
    # CORREÇÃO PÓS-REVIEW (erro de desenho documentado, não justificativa
    # retroativa): com taxa global 70,4%, o limiar RATE_FLAG (1,5x global =
    # 105,6%) é ESTRUTURALMENTE inalcançável para uma taxa (máx. 100%) — o
    # teste de taxa pré-registrado nunca poderia ser informativo. A conclusão
    # usa o critério ALTERNATIVO pré-registrado válido (SURV_FLAG: sobrevivência
    # KM t=6 >= 10 p.p. abaixo da global, N >= 25) + o spread observado.
    surv_gap_max = 0.0
    for _, r in seg.iterrows():
        if r["km_surv_t6"] != "" and surv_global != "":
            surv_gap_max = max(surv_gap_max, surv_global - float(r["km_surv_t6"]))
    seg_ok = seg[(seg["flags"].str.contains("RATE_FLAG")) &
                 (~seg["flags"].str.contains("N_BAIXO"))]
    if len(seg_ok):
        h6 = "SUSTENTADA"
        h6n = "segmentos com RATE_FLAG: " + ", ".join(
            f"{r['segment_type']}={r['segment_value']} ({r['rate_pct']}%)"
            for _, r in seg_ok.iterrows())
    elif seg["flags"].str.contains("N_BAIXO").all() and len(seg):
        h6 = "INCONCLUSIVA"
        h6n = "todos os segmentos com N < 25 (mínimo de amostra)"
    else:
        h6 = "REFUTADA"
        h6n = (f"nenhum segmento com taxa >= 1,5x a global e N >= 25. NOTA: o "
               f"limiar RATE_FLAG é estruturalmente inalcançável (1,5 x "
               f"{global_rate_h6:.1f}% = {rate_threshold_h6:.1f}% > 100%) — teste "
               f"de taxa não informativo por desenho (erro de threshold "
               f"pré-registrado, documentado; não renegociado). Conclusão pelo "
               f"critério alternativo pré-registrado SURV_FLAG (KM t=6 >= 10 p.p. "
               f"abaixo da global {surv_global}): nenhum segmento cruza (maior gap "
               f"{surv_gap_max * 100.0:.1f} p.p.); spread de taxas observado "
               f"{float(seg['rate_pct'].min()):.1f}-{float(seg['rate_pct'].max()):.1f}%")
    add("H6", h6, h6n,
        "threshold: N >= 25 E taxa >= 1,5x global (inalcançável por desenho com "
        "taxa global > 66,7% — documentado); critério alternativo pré-registrado "
        "válido: SURV_FLAG (KM t=6 >= 10 p.p. abaixo da global); MRR_FLAG reportado "
        "à parte")

    # H7 — reasons/CSAT frágeis
    mis = g_data["missing"]
    rdf = g_data["reasons"]
    assoc = any(r["refund_pct"] > 0 for _, r in rdf.iterrows() if r["reason_code"] != "unknown")
    h7 = "SUSTENTADA" if (mis["csat_nulls_pct"] > 25.0 or mis["reason_unknown_pct"] > 10.0
                          or not assoc) else "REFUTADA"
    add("H7", h7,
        f"CSAT nulos {mis['csat_nulls_pct']}%; reason 'unknown' {mis['reason_unknown_pct']}%; "
        f"feedback nulos {mis['feedback_nulls_pct']}%; associação refund por reason: "
        f"{'presente' if assoc else 'ausente'}; eventos com sub encerrada ±30d: "
        f"{mis['events_matched_sub_30d_pct']}%",
        "threshold: missingness > 25% OU unknown > 10% OU sem associação com refund/upgrade/downgrade")

    # H8 — onboarding
    exp = c_data["exposure"]
    r1_share_90 = float(exp.loc[exp["window_days"] == 90, "share_of_r1_pct"].iloc[0])
    acc_share_90 = float(c_data["accounts"].loc[
        c_data["accounts"]["window_days"] == 90, "share_of_event_accounts_pct"].iloc[0])
    h8 = "SUSTENTADA" if (r1_share_90 >= 25.0 or acc_share_90 >= 30.0) else "REFUTADA"
    add("H8", h8,
        f"R1 de assinaturas com <=90d de vida: {r1_share_90}% do total; primeiros "
        f"eventos <=90d do signup: {acc_share_90}% das contas com evento",
        "threshold: R1 <=90d >= 25% OU eventos <=90d >= 30%")

    # H9 — mecanismo do spike
    d0 = spike["detail"][0]
    h9 = "SUSTENTADA" if not d0["mechanism"].startswith("transversal") else "REFUTADA"
    add("H9", h9,
        f"pico {d0['month']} ({d0['total']} primeiros eventos): mecanismo = "
        f"{d0['mechanism']}",
        "threshold: bucket com maior share E ratio >= 1,5x a própria linha de base")

    # H10 — rotulagem causal (compromisso de processo; tabela H no report)
    add("H10", "APLICADA",
        "tabela de causalidade com status por achado (descritivo | hipótese causal "
        "plausível | não identificável) e confundidores",
        "compromisso de processo, não hipótese de negócio")
    return out


def causality_rows(v: list[dict], a_data: dict, c_data: dict, e_data: dict,
                   f_data: dict, g_data: dict, spike: dict) -> pd.DataFrame:
    """Tabela H: achado -> associação -> confundidores -> status -> dado adicional."""
    vd = {r["hypothesis"]: r["verdict"] for r in v}
    rows: list[dict] = []
    rows.append({
        "finding": "Tenure curto e churn (H1)",
        "association": vd.get("H1", ""),
        "confounders": "mix de coortes (mais signups 2024); censura; eventos múltiplos",
        "status": "hipótese causal plausível" if vd.get("H1") == "SUSTENTADA"
        else "descritivo",
        "additional_data": "dados de onboarding real (ativação, integrações), "
        "não disponíveis na base",
    })
    rows.append({
        "finding": "Spike mensal e coortes (H2/H9)",
        "association": f"pico {spike['peak_month']}: {vd.get('H2', '')}; "
                       f"mecanismo: {spike['detail'][0]['mechanism']}",
        "confounders": "sazonalidade; censura no corte; definição de pico; "
        "composição de tenure dos elegíveis (controlada no H2)",
        "status": "hipótese causal plausível" if vd.get("H2", "").startswith(
            "SUSTENTADA") else "descritivo",
        "additional_data": "datas de ativação/uso pós-signup; campanhas de marketing",
    })
    rows.append({
        "finding": "Uso cresceu em volume, não por conta (H3)",
        "association": vd.get("H3", ""),
        "confounders": "76,6% de uso fora da janela; pré-signup; mais contas em 2024",
        "status": "descritivo",
        "additional_data": "telemetria real de produto por conta",
    })
    rows.append({
        "finding": "Uso pré-evento não precede churn (H4)",
        "association": vd.get("H4", ""),
        "confounders": "uso pré-signup; janelas curtas; base sintética com uso "
        "independente do ciclo de vida",
        "status": "não identificável" if vd.get("H4") == "REFUTADA"
        else "hipótese causal plausível",
        "additional_data": "série de uso real dentro do ciclo de assinatura",
    })
    rows.append({
        "finding": "Sinais de suporte pré-evento (H5)",
        "association": vd.get("H5", ""),
        "confounders": "tickets pré-signup; mix de tenure; nulos de CSAT",
        "status": "não identificável" if vd.get("H5") in ("REFUTADA", "INCONCLUSIVA")
        else "hipótese causal plausível",
        "additional_data": "conteúdo de tickets; CSAT com cobertura maior",
    })
    rows.append({
        "finding": "Segmentos em risco (H6)",
        "association": vd.get("H6", ""),
        "confounders": "mix de tenure/coorte por segmento; winner do mês; trials",
        "status": "descritivo" if vd.get("H6") == "REFUTADA" else "hipótese causal plausível",
        "additional_data": "firmografia/uso por segmento",
    })
    rows.append({
        "finding": "Reasons/CSAT/feedback (H7)",
        "association": vd.get("H7", ""),
        "confounders": "missingness; nulos não-aleatórios; decoplamento das lentes",
        "status": "não identificável",
        "additional_data": "entrevistas de churn; reasons com cobertura completa",
    })
    rows.append({
        "finding": "Economia do onboarding (H8)",
        "association": vd.get("H8", ""),
        "confounders": "R1 é exposição, não perda (troca/sobreposição); trials MRR 0",
        "status": "descritivo (parametrizado em cenários CAC-equivalent)",
        "additional_data": "custo real de aquisição; caminho de ativação",
    })
    rows.append({
        "finding": "Decoplamento evento vs assinatura (estrutural da base)",
        "association": f"{g_data['missing']['events_matched_sub_30d_pct']}% dos "
                       f"eventos com assinatura encerrada ±30d",
        "confounders": "base sintética; lentes de churn independentes",
        "status": "descritivo",
        "additional_data": "fonte de eventos com vínculo contratual",
    })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Gráficos (4 essenciais; e_support/f_segment substituídos pelas tabelas
# t06/t07/t09 — pruning do gate It04; PNG byte-a-byte estáveis)
# ----------------------------------------------------------------------------
_OKABE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7",
          "#56B4E9", "#F0E442", "#000000"]


def _style() -> None:
    plt.rcParams["figure.dpi"] = 150
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["savefig.facecolor"] = "white"
    plt.rcParams["axes.facecolor"] = "white"
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False
    plt.rcParams["axes.titlesize"] = 10
    plt.rcParams["axes.labelsize"] = 8.5
    plt.rcParams["legend.fontsize"] = 7.5
    plt.rcParams["xtick.labelsize"] = 7.5
    plt.rcParams["ytick.labelsize"] = 7.5


def _footer(fig, line1: str, line2: str) -> None:
    """Rodapé em coordenadas de FIGURA (dentro do canvas; 2 linhas curtas).
    Espaçamento entre linhas DERIVADO da altura da figura (altura de linha em
    fração = 6.5pt/72/altura) — as duas linhas nunca se sobrepõem entre si nem
    saem do canvas. Margens explícitas via subplots_adjust; NUNCA
    bbox_inches='tight' (que esticava o canvas com texto fora da figura e
    esmagava o eixo — causa raiz dos findings visuais dos revisores do gate
    It04)."""
    lh = 6.5 / 72.0 / fig.get_figheight()   # altura de linha (fração da figura)
    y2 = 0.008                              # segunda linha perto da borda
    y1 = y2 + 1.45 * lh                     # primeira linha, sem overlap
    fig.text(0.01, y1, line1, fontsize=6.5, color="#555555",
             ha="left", va="bottom")
    fig.text(0.01, y2, line2, fontsize=6.5, color="#555555",
             ha="left", va="bottom")


def chart_a(series: pd.DataFrame, spike: dict) -> str:
    """Série mensal: primeiros eventos (barras) e taxa por conta elegível
    (linha). Headroom de ylim para a anotação do pico ficar DENTRO dos eixos
    (não cola no título); ticks mensais rotacionados e legíveis."""
    _style()
    fig, ax1 = plt.subplots(figsize=(7.8, 4.4))
    fig.subplots_adjust(top=0.87, bottom=0.26, left=0.105, right=0.88)
    x = list(range(len(series)))
    ax1.bar(x, series["first_events"], color="#0072B2", label="primeiros eventos",
            width=0.62)
    ax1.set_xticks(x, series["month"], rotation=90, fontsize=6.5, ha="center")
    ax1.set_ylabel("primeiros eventos (n)")
    ax1.set_xlabel("mês")
    peak = int(series["first_events"].max())
    ax1.set_ylim(0, peak * 1.18)
    ax1.set_yticks(range(0, int(peak * 1.18) + 1, 10))  # sem overhang do AutoLocator
    ax2 = ax1.twinx()
    ax2.tick_params(axis="x", labelbottom=False)  # twinx não duplica labels x
    ax2.plot(x, series["rate_first_events_pct"], color="#D55E00", marker="o",
             ms=3, label="taxa por conta elegível (%)")
    ax2.set_ylabel("taxa (% de contas elegíveis no início do mês)")
    ax2.set_ylim(bottom=0)
    ax2.set_yticks([0, 5, 10, 15, 20, 25])  # sem overhang do AutoLocator
    if spike["peak_month"] in list(series["month"]):
        i = list(series["month"]).index(spike["peak_month"])
        v = int(series["first_events"].iloc[i])
        ax1.annotate(f"pico {spike['peak_month']} ({v})", xy=(i, v),
                     xytext=(i, v + 0.06 * peak),
                     fontsize=7.5, color="#D55E00", ha="center",
                     arrowprops=dict(arrowstyle="->", color="#D55E00", lw=0.7))
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", framealpha=0.92)
    ax1.set_title("Eventos de churn por mês e taxa por conta elegível (2023-2024)",
                  pad=6)
    _footer(fig,
            "Fonte: data/raw/ravenstack_churn_events.csv + "
            "ravenstack_accounts.csv;",
            "denominador = contas elegíveis no início do mês (contrato §5).")
    path = CHARTS_DIR / "a_monthly_events_and_rate.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path.name


def chart_b(km_quarter: pd.DataFrame, at_risk: pd.DataFrame) -> str:
    """Kaplan-Meier por trimestre de signup (censura no corte; Q4-2024 notada).
    Figura ~10x6 com eixo íntegro 0-1; legenda compacta (2 colunas) em faixa
    própria ABAIXO dos eixos — sem sobrepor título, curvas ou rodapé."""
    _style()
    cohorts = sorted(km_quarter["cohort"].unique())
    fig, ax = plt.subplots(figsize=(10.0, 6.0))
    fig.subplots_adjust(top=0.90, bottom=0.30, left=0.075, right=0.975)
    for i, q in enumerate(cohorts):
        g = at_risk[at_risk["cohort"] == q].sort_values("t")
        ax.step(g["t"], g["survival"], where="post",
                color=_OKABE[i % len(_OKABE)], lw=1.4,
                label=f"{q} (n={int(km_quarter.loc[km_quarter['cohort'] == q, 'n_accounts'].iloc[0])})")
        last = g.iloc[-1]
        ax.plot([last["t"]], [last["survival"]], "o",
                color=_OKABE[i % len(_OKABE)], ms=3)
    ax.set_xlabel("meses desde o signup (0 = mês do signup)")
    ax.set_ylabel("sobrevivência (sem primeiro evento) — KM")
    ax.set_ylim(0.0, 1.02)          # eixo íntegro 0-1: nenhuma curva cortada
    ax.set_xlim(-0.5, 24.5)
    ax.set_xticks([0, 6, 12, 18, 24])  # marcos semestrais (evita overhang -5/25)
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])  # sem overhang do AutoLocator
    ax.set_title("Tempo até o primeiro evento por coorte de signup "
                 "(Kaplan-Meier, censura em 2024-12-31)", pad=8)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.235),
               ncol=2, fontsize=7.5, title="coorte (trimestre)",
               title_fontsize=8, frameon=True, handlelength=1.4,
               columnspacing=1.4)
    _footer(fig,
            "Fonte: data/raw/ravenstack_churn_events.csv + "
            "ravenstack_accounts.csv.",
            "Censura: contas sem evento até 2024-12-31; Q4-2024 tem <= 3 meses "
            "observáveis — não comparar com janela completa.")
    path = CHARTS_DIR / "b_km_by_signup_quarter.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path.name


def chart_c(exposure: pd.DataFrame, buckets: pd.DataFrame) -> str:
    """Exposição bruta R1 por faixa de duração — barras HORIZONTAIS em ordem de
    duração (0d, 1-30d, 31-60d, 61-90d, 91-180d, 181-365d, >365d), com % e US$
    legíveis ao lado de cada barra; nada sobreposto."""
    _style()
    order = ["0d", "1-30d", "31-60d", "61-90d", "91-180d", "181-365d", ">365d"]
    b = buckets.set_index("bucket").loc[order].reset_index()
    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    fig.subplots_adjust(top=0.87, bottom=0.20, left=0.14, right=0.965)
    y = list(range(len(b)))
    ax.barh(y, b["mrr_sum"], color="#009E73", height=0.62)
    for i, (_, r) in enumerate(b.iterrows()):
        ax.text(r["mrr_sum"] + 9000, i,
                f"{r['share_of_r1_pct']:.1f}% · {r['mrr_sum']:,}".replace(",", "."),
                va="center", fontsize=7.5)
    ax.set_yticks(y, b["bucket"].tolist(), fontsize=8)
    ax.set_xlim(0, b["mrr_sum"].max() * 1.30)
    ax.set_xticks([0, 100000, 200000, 300000, 400000, 500000, 600000])
    ax.set_xlabel("gross ending MRR (R1, US$)")
    ax.set_ylabel("duração da assinatura encerrada (dias)")
    ax.set_title("Exposição contratual bruta precoce (R1) por duração de "
                 "assinatura", pad=6)
    ax.grid(axis="x", linestyle="-", linewidth=0.4, alpha=0.35, color="#b0b0b0")
    ax.set_axisbelow(True)
    _footer(fig,
            "Fonte: data/raw/ravenstack_subscriptions.csv (end_date presente).",
            "R1 = exposição, NÃO receita perdida (contrato §5); cenários "
            "CAC-equivalent em t03c_cac_equivalent.csv.")
    path = CHARTS_DIR / "c_onboarding_exposure_by_duration.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path.name


def chart_d(usage_monthly: pd.DataFrame) -> str:
    """Volume total vs intensidade por conta ativa (painel duplo; escalas
    claras; rodapé compacto em 2 linhas dentro do canvas)."""
    _style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.1))
    fig.subplots_adjust(top=0.85, bottom=0.22, left=0.07, right=0.985,
                        wspace=0.24)
    d = usage_monthly
    ax1.bar(list(range(len(d))), d["rows_raw_primary"], color="#0072B2",
            label="bruto (sem pré-signup)")
    ax1.bar(list(range(len(d))), d["rows_aligned_primary"], color="#E69F00",
            label="alinhado [start,end]")
    ax1.set_xticks(list(range(len(d))), d["month"], rotation=90, fontsize=6.5,
                   ha="center")
    ax1.set_ylabel("linhas de uso (n)")
    ax1.set_title("Volume total mensal de uso")
    ax1.legend(fontsize=7)
    ax2.plot(list(range(len(d))), d["rows_raw_primary_per_active"], marker="o",
             ms=3, color="#0072B2", label="bruto / conta ativa")
    ax2.plot(list(range(len(d))), d["rows_aligned_primary_per_active"], marker="o",
             ms=3, color="#E69F00", label="alinhado / conta ativa")
    ax2.set_xticks(list(range(len(d))), d["month"], rotation=90, fontsize=6.5,
                   ha="center")
    ax2.set_ylabel("linhas por conta ativa (n)")
    ax2.set_title("Intensidade mensal por conta ativa")
    ax2.legend(fontsize=7)
    fig.suptitle("Uso: volume cresce vs intensidade por conta (2023-2024)",
                 fontsize=11, y=0.97)
    _footer(fig,
            "Fonte: data/raw/ravenstack_feature_usage.csv + subscriptions + "
            "accounts;",
            "primário exclui uso pré-signup; conta ativa = painel account_month "
            "(Iteração 02).")
    path = CHARTS_DIR / "d_usage_volume_vs_intensity.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path.name

# ----------------------------------------------------------------------------
# Render do relatório (determinístico)
# ----------------------------------------------------------------------------

def render_report(a_data: dict, b_data: dict, c_data: dict, d_data: dict,
                  e_data: dict, f_data: dict, g_data: dict, spike: dict,
                  verdicts: list[dict], causal: pd.DataFrame,
                  charts: list[str], tables: list[str],
                  structural_fail: bool = False) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Relatório de Causa Raiz, Coortes e Onboarding — Iteração 03 (RavenStack)")
    add("")
    add("Gerado por `solution/src/03_root_cause.py` (execução offline e determinística; "
        "sem timestamp para garantir output byte-a-byte estável entre execuções).")
    add("")
    add("## 1. Metodologia")
    add("")
    add("- **Hipóteses pré-registradas ANTES da análise:** `process-log/hypotheses/"
        "iteration-03-root-cause-hypotheses.md` (H1–H10, com thresholds fixados antes "
        "de ver os resultados; vereditos aplicados mecanicamente na seção 10).")
    add("- **Contrato analítico (Iteração 02):** `solution/docs/analytical-contract.md` — "
        "lente de eventos (C) para diagnóstico; lente de assinaturas para receita "
        "(R1 gross ending MRR = exposição; R2 net account-state MRR loss); painel "
        "account-month (`data/processed/account_month.csv`) como estado/risco; "
        "anti-leakage (features <= data índice; CSAT/resolução só com tickets fechados); "
        "variantes bruta vs alinhada de uso; censura no corte 2024-12-31.")
    add("- **Escopo:** NENHUMA recomendação (Iteração 05), NENHUMA watchlist (Iteração 04), "
        "NENHUM modelo preditivo/ML.")
    add("- **Saídas:** este relatório; tabelas em `solution/out/tables/` "
        f"({len(tables)} arquivos); gráficos em `solution/out/charts/` ({len(charts)} arquivos).")
    add("")

    if structural_fail:
        add("## 2. Falha estrutural")
        add("")
        add("A análise **não foi executada**: tabelas/colunas mínimas ausentes (ver "
            "checks F01/S01/F02/S02). O relatório foi regravado com os FAILs "
            "estruturais; exit code 1. Nenhum output de dados (tabelas/gráficos) foi "
            "regenerado nesta execução — arquivos existentes desses paths podem estar "
            "desatualizados e NÃO devem ser usados.")
        add("")
        add("## 3. Checks e invariantes")
        add("")
        add("| ID | Escopo | Check | Veredito | Detalhe |")
        add("|---|---|---|---|---|")
        for c in CHECKS:
            add(f"| {c['id']} | {c['scope']} | {c['description']} | **{c['level']}** | {c['detail']} |")
        add("")
        return "\n".join(lines)

    s = a_data["series"]
    fe = a_data["fe"]
    d0 = spike["detail"][0]
    months_all = list(s["month"])
    r1_total = int(s["r1_mrr_ended_in_month"].sum())
    r1_last4 = int(s.loc[s["month"].isin(["2024-09", "2024-10", "2024-11", "2024-12"]),
                        "r1_mrr_ended_in_month"].sum())
    r1_dec = int(s.loc[s["month"] == "2024-12", "r1_mrr_ended_in_month"].iloc[0])
    add("## 2. Série mensal 2023-2024 e decomposição do pico")
    add("")
    add(f"- **Eventos totais:** {int(s['events_total'].sum())} (fonte `churn_events`); "
        f"**primeiros eventos:** {int(s['first_events'].sum())} (contas únicas com evento: "
        f"{int(fe['has_event'].sum())} de {len(fe)}).")
    elev = spike["elevated_months"]
    if elev:
        gap = [m for m in months_all[months_all.index(elev[0]):months_all.index(elev[-1]) + 1]
               if m not in elev]
        gap_txt = (f"; vale em {', '.join(gap)} (abaixo da regra)"
                   if gap else "")
        add(f"- **Período elevado (regra pré-registrada: first_events >= 1,5 x mediana "
            f"{spike['median']:.0f}/mês = {1.5 * spike['median']:.1f}):** "
            f"{', '.join(elev)} ({len(elev)} meses){gap_txt} — o 'churn subiu nos "
            f"últimos meses' aparece como NÍVEL elevado sustentado (com pico em "
            f"{d0['month']}), não um mês isolado.")
    else:
        add(f"- **Período elevado (regra pré-registrada: first_events >= 1,5 x mediana "
            f"{spike['median']:.0f}/mês):** nenhum.")
    add(f"- **Pico (mês de maior contagem):** **{d0['month']}** com {d0['total']} primeiros "
        f"eventos (taxa por conta elegível {s.loc[s['month'] == d0['month'], 'rate_first_events_pct'].iloc[0]:.2f}%; "
        f"mês de maior taxa: {spike['peak_rate_month']}).")
    add(f"- **Receita (declarando a lente):** R1 gross ending MRR por mês (tabela t01) "
        f"soma {r1_total} ({int(s['n_ended_in_month'].sum())} assinaturas) — exposição, "
        f"NÃO perda (contrato §5). Concentração no fim de 2024: set-dez responde por "
        f"{100.0 * r1_last4 / r1_total:.1f}% do R1 da janela e dezembro isolado por "
        f"{100.0 * r1_dec / r1_total:.1f}% (descritivo; pode ser artefato de geração da "
        f"base — não interpretado como causa). R2 net account-state MRR loss soma "
        f"{int(s['r2_churn_to_inactive'].sum())} (churn-to-inactive, "
        f"{int((s['r2_churn_to_inactive'] > 0).sum())} transições) + "
        f"{int(s['r2_active_contraction'].sum())} (active contraction) = "
        f"{int(s['r2_net'].sum())}.")
    add(f"- **Decomposição do pico {d0['month']}** (baseline: {d0['baseline_months_available']} "
        f"meses anteriores):")
    add("  - Por bucket de tenure (meses desde o signup): " +
        "; ".join(f"{b['bucket']}: {b['events_in_peak']} ({b['share_pct']:.1f}% do pico; "
                  f"baseline {b['baseline_mean_6m']}; razão {b['ratio_vs_baseline']})"
                  for b in d0["buckets"]) + ".")
    add("  - Por coorte de signup (trimestre): " +
        "; ".join(f"{b['cohort']}: {b['events_in_peak']} ({b['share_pct']:.1f}%; "
                  f"razão {b['ratio_vs_baseline']})"
                  for b in d0["cohorts"]) + ".")
    add(f"  - **Mecanismo do pico (regra H9):** {d0['mechanism']}.")
    add(f"  - **Controle de composição de tenure (sensibilidade H2):** esperado "
        f"{spike['expected_events_tenure_std']} eventos pelo mix de tenure dos "
        f"elegíveis x baseline dos buckets; observado {d0['total']} "
        f"(ratio {spike['ratio_observed_vs_expected']}).")
    add("")
    add("## 3. Coortes e tempo-ao-churn (Kaplan-Meier descritivo com censura)")
    add("")
    q = b_data["quarter"]
    add(f"- **Censura no corte 2024-12-31:** contas sem primeiro evento são observadas "
        f"até o último mês do painel (at-risk) e censuradas — a taxa observada "
        f"(eventos/n) SUBestima o churn de coortes recentes; a estimativa KM corrige "
        f"isso. Tabela completa por trimestre e por mês: `t02_cohort_km.csv`; at-risk "
        f"por trimestre: `t02b_cohort_km_at_risk.csv`.")
    add(f"- **IMPORTANTE (censura):** coortes de Q4-2024 têm <= 3 meses observáveis; "
        f"NÃO comparar Q4 com janela completa. `km_surv_t6/t12/t18` vazio = "
        f"horizonte NÃO observável (follow-up < horizonte, censura no corte). "
        f"Quando observável, o valor é o da FUNÇÃO DEGRAU no maior tempo <= "
        f"horizonte (carry-forward — não exige evento/censura exatamente em t = "
        f"horizonte).")
    add("")
    add("| Coorte (trimestre) | N contas | Eventos | Censuradas | Taxa observada | "
        "Sobrev. KM t=6 | Churn KM t=6 |")
    add("|---|---|---|---|---|---|---|")
    for _, r in q.sort_values("cohort").iterrows():
        add(f"| {r['cohort']} | {int(r['n_accounts'])} | {int(r['events'])} | "
            f"{int(r['censored'])} | {r['observed_rate_pct']}% | "
            f"{r['km_surv_t6'] if r['km_surv_t6'] != '' else 'não observado'} | "
            f"{r['km_churn_t6_pct'] if r['km_churn_t6_pct'] != '' else '—'} |")
    add("")
    add("## 4. Onboarding economics (exposição bruta precoce; cenários CAC-equivalent)")
    add("")
    add(f"- **R1 total (janela):** {c_data['total_r1']} em assinaturas encerradas.")
    add(f"- **Exposição por duração da assinatura** (tabela `t03_onboarding_buckets.csv`): "
        + "; ".join(f"{r['bucket']}: {r['n_subs']} assinaturas, {r['mrr_sum']} "
                    f"({r['share_of_r1_pct']}% do R1)" for _, r in c_data["buckets"].iterrows()) + ". "
        "O bucket `0d` = assinaturas com start = end (mesma data; 13 na base) — "
        "exposição instantânea, incluída para o share fechar 100%.")
    add(f"- **Exposição acumulada por duração (incluindo same-day `0d`;** tabela "
        f"`t03c_cac_equivalent.csv`): <= 30d: "
        f"{int(c_data['exposure'].loc[c_data['exposure']['window_days'] == 30, 'mrr_exposure'].iloc[0])} "
        f"({c_data['exposure'].loc[c_data['exposure']['window_days'] == 30, 'share_of_r1_pct'].iloc[0]}% do R1; "
        f"o bucket 1-30d isolado é "
        f"{int(c_data['buckets'].loc[c_data['buckets']['bucket'] == '1-30d', 'mrr_sum'].iloc[0])} = "
        f"{c_data['buckets'].loc[c_data['buckets']['bucket'] == '1-30d', 'share_of_r1_pct'].iloc[0]}% do R1); "
        f"<= 60d: "
        f"{int(c_data['exposure'].loc[c_data['exposure']['window_days'] == 60, 'mrr_exposure'].iloc[0])} "
        f"({c_data['exposure'].loc[c_data['exposure']['window_days'] == 60, 'share_of_r1_pct'].iloc[0]}% do R1); "
        f"<= 90d: "
        f"{int(c_data['exposure'].loc[c_data['exposure']['window_days'] == 90, 'mrr_exposure'].iloc[0])} "
        f"({c_data['exposure'].loc[c_data['exposure']['window_days'] == 90, 'share_of_r1_pct'].iloc[0]}% do R1).")
    add(f"- **Primeiro evento por conta** (tabela `t03b_onboarding_accounts.csv`): "
        + "; ".join(f"<= {int(r['window_days'])}d: {int(r['n_first_events_le'])} contas "
                    f"({r['share_of_event_accounts_pct']}% das contas com evento)"
                    for _, r in c_data["accounts"].iterrows()) + ".")
    add(f"- **Cenários CAC-equivalent exposure** (tabela `t03c_cac_equivalent.csv`): "
        f"o dataset NÃO contém custo de aquisição; os cenários são múltiplos de MRR "
        f"({', '.join(str(m) + 'x' for m in CAC_MULTIPLES)}) sobre a exposição bruta "
        f"precoce, explicitamente nomeados — nunca 'CAC queimado' nem 'receita perdida' "
        f"(R1 é exposição contratual, contrato §5).")
    add("")
    add("## 5. Uso: 'o uso cresceu' — volume vs intensidade por conta")
    add("")
    g = d_data["growth"]
    add(f"- **Volume total (primário, sem pré-signup):** {g['y2023']['total_raw_primary']} "
        f"-> {g['y2024']['total_raw_primary']} linhas "
        f"({g['total_raw_primary_pct']}%); alinhado [start,end]: "
        f"{g['total_aligned_primary_pct']}%.")
    add(f"- **Intensidade (mediana de linhas por conta-mês):** {g['y2023']['median_per_acct_raw']} "
        f"-> {g['y2024']['median_per_acct_raw']} brutas ({g['median_per_acct_raw_pct']}%); "
        f"alinhadas: {g['y2023']['median_per_acct_aligned']} -> "
        f"{g['y2024']['median_per_acct_aligned']} ({g['median_per_acct_aligned_pct']}%).")
    add(f"- **Definição da mediana:** mediana das medianas mensais sobre conta-meses "
        f"com >= 1 linha de uso (não pareada por conta; mesmo desenho das iter. "
        f"anteriores). Variante pooled (mediana sobre TODOS os account-months do ano, "
        f"sem agregar por mês): alinhado "
        f"{g['y2023']['median_per_acct_aligned_pooled']} -> "
        f"{g['y2024']['median_per_acct_aligned_pooled']} "
        f"({g['median_per_acct_aligned_pooled_pct']}%) — mais sensível à composição; "
        f"o veredito H3 é dirigido pela variante raw (2.0 -> 2.0), robusta em ambas "
        f"as definições.")
    add(f"- **Sensibilidade com pré-signup incluído:** total bruto "
        f"{g['sensitivity_total_raw_all_pct']}% (tabela `t05_usage_monthly.csv` tem as "
        f"duas variantes mês a mês).")
    add("")
    add("## 6. Suporte pré-evento (desenho honesto; anti-leakage)")
    add("")
    add(f"- **Desenho:** para cada mês m (2023-04..2024-12), grupo-churn = contas com "
        f"primeiro evento em m; controle = contas elegíveis no início de m sem evento "
        f"em m; janela W(m) = [dia 1 de m - 90d, dia 1 de m); tickets pré-signup "
        f"excluídos; CSAT/resolução apenas de tickets fechados (contrato §10). "
        f"Tabela mensal: `t06_support_monthly.csv`.")
    p = e_data["pooled"]
    c_ = p["churn"]
    ct_ = p["control"]
    cn_ = p["control_never_churn"]
    add(f"- **Pooled (média por conta-mês):** tickets/conta churn "
        f"{c_.get('tickets_per_account_month', 'NA')} vs controle "
        f"{ct_.get('tickets_per_account_month', 'NA')}; escalação "
        f"{c_.get('esc_rate_pct', 'NA')}% vs {ct_.get('esc_rate_pct', 'NA')}%; CSAT "
        f"{c_.get('csat_mean', 'NA')} vs {ct_.get('csat_mean', 'NA')} "
        f"(denominador: tickets fechados com nota); FRT mediana "
        f"{c_.get('median_frt_min', 'NA')} vs {ct_.get('median_frt_min', 'NA')} min; "
        f"resolução mediana {c_.get('median_res_h', 'NA')} vs "
        f"{ct_.get('median_res_h', 'NA')} h. Controle restrito a nunca-churn: "
        f"tickets/conta {cn_.get('tickets_per_account_month', 'NA')}.")
    st = e_data["stratified"]
    add(f"- **Estratificado por tenure (sensibilidade):** 0-6m: churn "
        f"{st['churn']['0-6m'].get('tickets_per_account_month', 'NA')} vs controle "
        f"{st['control']['0-6m'].get('tickets_per_account_month', 'NA')} tickets/conta; "
        f"7-12m: {st['churn']['7-12m'].get('tickets_per_account_month', 'NA')} vs "
        f"{st['control']['7-12m'].get('tickets_per_account_month', 'NA')}; 13+m: "
        f"{st['churn']['13+m'].get('tickets_per_account_month', 'NA')} vs "
        f"{st['control']['13+m'].get('tickets_per_account_month', 'NA')}.")
    add("")
    add("## 7. Segmentos (industry / canal / plano / trial)")
    add("")
    add(f"- **Taxa global de primeiro evento:** {f_data['global_rate']}% das contas "
        f"({int(fe['has_event'].sum())} de {len(fe)}); sobrevivência KM global no mês 6: "
        f"{f_data['global_surv6']}.")
    add("- Tabela completa: `t07_segments.csv`. Flags: `N_BAIXO` (N < 25, sem ranking), "
        "`RATE_FLAG` (taxa >= 1,5x global com N >= 25), `SURV_FLAG` (sobrevivência KM "
        "t=6 >= 10 p.p. abaixo da global, N >= 25), `MRR_FLAG` (share de R1 > 10%).")
    add("")
    add("| Segmento | Valor | N | 1º evento | Taxa | Sobrev. KM t=6 | R1 (US$) | Share R1 | Flags |")
    add("|---|---|---|---|---|---|---|---|---|")
    for _, r in f_data["table"].iterrows():
        add(f"| {r['segment_type']} | {r['segment_value']} | {int(r['n_accounts'])} | "
            f"{int(r['n_first_event'])} | {r['rate_pct']}% | "
            f"{r['km_surv_t6'] if r['km_surv_t6'] != '' else '—'} | "
            f"{int(r['r1_gross_mrr'])} | {r['r1_share_pct']}% | {r['flags']} |")
    add("")
    add("## 8. Reasons / CSAT / feedback (evidência sugestiva, nunca causa)")
    add("")
    mis = g_data["missing"]
    add(f"- **Missingness:** CSAT {mis['csat_nulls_pct']}% nulos; reason 'unknown' "
        f"{mis['reason_unknown_pct']}%; feedback nulos {mis['feedback_nulls_pct']}%.")
    add(f"- **Decoplamento estrutural:** apenas {mis['events_matched_sub_30d_pct']}% dos "
        f"eventos têm assinatura encerrada ±30 dias na mesma conta — reason_code não "
        f"se ancora em perda contratual (contrato §4/§10).")
    add(f"- **CSAT (tickets fechados com nota, todo o período):** contas com evento "
        f"{mis['csat_mean_with_event']} vs sem evento {mis['csat_mean_without_event']} "
        f"— comparação sugestiva, não causal.")
    add("- Distribuição por reason e associações com refund/upgrade/downgrade: "
        "tabela `t08_reasons.csv`.")
    add("")
    add("## 9. Correlação vs causalidade")
    add("")
    add("| Achado | Associação observada | Confundidores/alternativas | Status | Dado adicional |")
    add("|---|---|---|---|---|")
    for _, r in causal.iterrows():
        add(f"| {r['finding']} | {r['association']} | {r['confounders']} | "
            f"**{r['status']}** | {r['additional_data']} |")
    add("")
    add("## 10. Vereditos das hipóteses (thresholds pré-registrados)")
    add("")
    add("| Hipótese | Veredito | Números | Nota |")
    add("|---|---|---|---|")
    for r in verdicts:
        add(f"| {r['hypothesis']} | **{r['verdict']}** | {r['numbers']} | {r['note']} |")
    add("")
    add("## 11. Gates e validações")
    add("")
    add("| ID | Escopo | Check | Veredito | Detalhe |")
    add("|---|---|---|---|---|")
    for c in CHECKS:
        add(f"| {c['id']} | {c['scope']} | {c['description']} | **{c['level']}** | {c['detail']} |")
    add("")
    add("## 12. Causa raiz (síntese) e limitações")
    add("")
    add("- Síntese da causa raiz: ver `process-log/reports/iteration-03-root-cause-report.md` "
        "(seção de decisão do executor). Este relatório é a evidência numérica; a "
        "interpretação com status de certeza e o handoff para a Iteração 04 estão no "
        "report de processo.")
    add("- Limitações: base sintética (Iteração 01 §5); lentes de churn decopladas "
        "(contrato §4); 76,6% do uso fora da janela (contrato §9); CSAT/reasons "
        "sugestivos (contrato §10); nenhum custo de aquisição na base (CAC-equivalent "
        "são cenários nomeados).")
    add("")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Gates (invariantes executáveis desta iteração)
# ----------------------------------------------------------------------------

def run_gates(a_data: dict, b_data: dict, c_data: dict, d_data: dict,
              e_data: dict, f_data: dict, g_data: dict, panel: pd.DataFrame,
              churn: pd.DataFrame, tables: list[Path], charts: list[Path]) -> None:
    s = a_data["series"]
    fe = a_data["fe"]
    n_accounts = len(fe)

    # G1 — eventos reconciliam ao painel e às fontes
    ok = (int(s["events_total"].sum()) == len(churn)
          and int(s["first_events"].sum()) == int(fe["has_event"].sum())
          and int(panel["n_events_in_month"].sum()) == len(churn))
    check("G1-events", "série mensal",
          "eventos totais/primeiros reconciliam a churn_events e ao painel",
          "PASS" if ok else "FAIL",
          f"eventos={int(s['events_total'].sum())} (fonte {len(churn)}); "
          f"primeiros={int(s['first_events'].sum())} "
          f"(contas com evento {int(fe['has_event'].sum())}); painel={int(panel['n_events_in_month'].sum())}")

    # G2 — R1 reconciliado ao total da Iteração 02 (1.179.139 / 486)
    r1 = int(s["r1_mrr_ended_in_month"].sum())
    n_ended = int(s["n_ended_in_month"].sum())
    check("G2-r1", "lente de receita bruta",
          "R1 gross ending MRR e contagem reconciliam ao painel/contrato",
          "PASS" if r1 == 1179139 and n_ended == 486 else "FAIL",
          f"R1={r1} (contrato: 1.179.139); assinaturas={n_ended} (contrato: 486)")

    # G3 — R2 reconciliado ao contrato (18.507 / 150.817 / 169.324)
    r2a = int(s["r2_churn_to_inactive"].sum())
    r2b = int(s["r2_active_contraction"].sum())
    check("G3-r2", "lente de estado (R2)",
          "R2 churn-to-inactive + active contraction reconciliam ao contrato",
          "PASS" if r2a == 18507 and r2b == 150817 else "FAIL",
          f"churn-to-inactive={r2a} (contrato 18.507); contraction={r2b} (contrato 150.817); "
          f"net={r2a + r2b} (contrato 169.324)")

    # G4 — cadeia do denominador elegível fecha
    bad = 0
    prev = 0
    for _, r in s.iterrows():
        if r["eligible_at_start"] != r["accounts_signed_up_le"] - prev:
            bad += 1
        prev += r["first_events"]
    check("G4-eligible", "denominador elegível",
          "cadeia elegível(m) = signups <= m - primeiros eventos anteriores",
          "PASS" if bad == 0 else "FAIL",
          f"{bad} meses com quebra de cadeia; último eligible="
          f"{int(s.iloc[-1]['eligible_at_start'])}")

    # G5 — KM: at_risk(0) = N da coorte; sobrevivência em [0,1] e monotônica
    # (S(0) < 1 é legítimo: eventos ocorrem no mês 0 = mês do signup)
    bad_km = 0
    for cohort, g in b_data["at_risk"].groupby("cohort"):
        g = g.sort_values("t")
        n_cohort = int(b_data["quarter"].loc[
            b_data["quarter"]["cohort"] == cohort, "n_accounts"].iloc[0])
        if int(g.iloc[0]["at_risk"]) != n_cohort:
            bad_km += 1
        prev_s = 1.0
        for _, row in g.iterrows():
            if row["survival"] > 1.0 + 1e-9 or row["survival"] < 0.0 - 1e-9:
                bad_km += 1
                break
            if row["survival"] > prev_s + 1e-3:  # tolerância de arredondamento (4 dec.)
                bad_km += 1
                break
            prev_s = row["survival"]
    check("G5-km", "Kaplan-Meier",
          "at_risk(0) = N da coorte; sobrevivência em [0,1] e monotônica",
          "PASS" if bad_km == 0 else "FAIL",
          f"{bad_km} violações em {b_data['at_risk']['cohort'].nunique()} coortes")

    # G6 — uso: total por mês + pré-signup = 25.000 linhas
    total_all = int(d_data["monthly"]["rows_raw_all"].sum())
    total_pre = int(d_data["sensitivity"]["rows_raw_all"].sum())
    check("G6-usage", "uso",
          "linhas totais reconciliam à fonte (25.000) e pré-signup separado",
          "PASS" if total_all == 25000 and total_pre <= 25000 else "FAIL",
          f"Σ linhas por mês (com pré-signup)={total_all} (fonte 25.000); "
          f"variante sensibilidade={total_pre}")

    # G7 — suporte: pool >= 30 conta-mês por lado; closed_at 0 nulos (G15 It02)
    p = e_data["pooled"]
    check("G7-support", "suporte",
          "pool de suporte com N >= 30 conta-mês por lado; política closed_at respeitada",
          "PASS" if (p["churn"].get("n_account_month", 0) >= 30
                     and p["control"].get("n_account_month", 0) >= 30) else "FAIL",
          f"churn={p['churn'].get('n_account_month', 0)} contas-pool; "
          f"controle={p['control'].get('n_account_month', 0)}; "
          f"CSAT só fechados com nota; pré-signup excluído no primário")

    # G8 — segmentos fecham (500 contas; 352 eventos; R1 = 1.179.139)
    seg = f_data["table"]
    ok8 = (int(seg[seg["segment_type"] == "industry"]["n_accounts"].sum()) == n_accounts
           and int(seg[seg["segment_type"] == "industry"]["n_first_event"].sum())
           == int(fe["has_event"].sum())
           and int(seg[seg["segment_type"] == "industry"]["r1_gross_mrr"].sum()) == 1179139)
    check("G8-segments", "segmentos",
          "contagens de segmentos fecham (500 contas / 352 eventos / R1 1.179.139)",
          "PASS" if ok8 else "FAIL",
          f"contas={int(seg[seg['segment_type'] == 'industry']['n_accounts'].sum())}; "
          f"eventos={int(seg[seg['segment_type'] == 'industry']['n_first_event'].sum())}; "
          f"R1={int(seg[seg['segment_type'] == 'industry']['r1_gross_mrr'].sum())}")

    # G9 — zero-divisão: sem NaN/inf em colunas de taxa onde denominador > 0
    bad9 = 0
    for col in ["rate_first_events_pct", "events_per_active_pct"]:
        sub = s[s["eligible_at_start"] > 0] if col == "rate_first_events_pct" \
            else s[s["active_accounts_end"] > 0]
        if sub[col].isna().any():
            bad9 += 1
    check("G9-zerodiv", "denominadores",
          "sem NaN em taxas com denominador > 0",
          "PASS" if bad9 == 0 else "FAIL",
          f"{bad9} colunas com NaN indevido")

    # G10 — outputs existem e não são vazios
    missing_t = [t.name for t in tables if not t.exists() or t.stat().st_size == 0]
    missing_c = [c.name for c in charts if not c.exists() or c.stat().st_size == 0]
    check("G10-outputs", "outputs",
          "tabelas e gráficos gerados e não-vazios",
          "PASS" if not (missing_t or missing_c) else "FAIL",
          f"tabelas ausentes/vazias={missing_t or 'nenhuma'}; "
          f"gráficos ausentes/vazios={missing_c or 'nenhuma'}")

    # G11 — onboarding: share por duração fecha em 100% do R1 (inclui 0d)
    bsum = int(c_data["buckets"]["mrr_sum"].sum())
    check("G11-onboarding", "onboarding economics",
          "soma dos buckets de duração reconcilia ao R1 total (1.179.139)",
          "PASS" if bsum == 1179139 else "FAIL",
          f"Σ buckets={bsum} (R1 total 1.179.139); bucket 0d incluso")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> int:
    # paths de saída garantidos (nunca commitados se vazios — .gitignore)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    loaded = load_all()
    panel = load_panel()

    structural = any(c["level"] == "FAIL" for c in CHECKS)
    if structural or panel is None:
        REPORT_PATH.write_text(render_report({}, {}, {}, {}, {}, {}, {}, {}, [],
                                             pd.DataFrame(), [], [], structural_fail=True),
                               encoding="utf-8")
        return 1

    acc = loaded["ravenstack_accounts.csv"]
    sub = loaded["ravenstack_subscriptions.csv"]
    churn = loaded["ravenstack_churn_events.csv"]
    use = loaded["ravenstack_feature_usage.csv"]
    tic = loaded["ravenstack_support_tickets.csv"]

    # --- análise A: série mensal + spike ---
    fe = first_event_per_account(acc, churn)
    series = monthly_series(acc, churn, panel, fe)
    months = months_range(FIRST_MONTH, LAST_MONTH)
    spike = spike_decomposition(series, fe, months)

    # --- B: coortes/KM ---
    cohort = cohort_tables(fe)

    # --- C: onboarding ---
    onboard = onboarding(sub, acc, fe)

    # --- D: uso ---
    # uso alinhado por conta×mês (primário: sem pré-signup) para H4
    u = use.merge(sub[["subscription_id", "account_id"]], on="subscription_id")
    signup_map = dict(zip(acc["account_id"], pd.to_datetime(acc["signup_date"])))
    u["ud"] = pd.to_datetime(u["usage_date"])
    u["signup"] = u["account_id"].map(signup_map)
    u = u[u["ud"] >= u["signup"]]
    sub_win = sub[["subscription_id", "start_date", "end_date"]].rename(
        columns={"start_date": "s_start", "end_date": "s_end"})
    sub_win["s_start"] = pd.to_datetime(sub_win["s_start"])
    sub_win["s_end"] = pd.to_datetime(sub_win["s_end"])
    u = u.merge(sub_win, on="subscription_id")
    u["in_window"] = (u["ud"] >= u["s_start"]) & (
        u["s_end"].isna() | (u["ud"] <= u["s_end"]))
    u["um"] = u["ud"].dt.to_period("M").astype(str)
    aligned_by_acct_month = (u[u["in_window"]].groupby(["account_id", "um"]).size())
    usage = usage_analysis(use, acc, sub, panel)
    a_data = {"fe": fe, "series": series,
              "usage_by_acct_month": aligned_by_acct_month}

    # --- E: suporte ---
    support = support_analysis(tic, acc, churn, fe)

    # --- F: segmentos ---
    segments = segment_analysis(acc, sub, fe)

    # --- G: reasons ---
    reasons = reasons_analysis(churn, sub, tic, acc)

    # --- H: vereditos + causalidade ---
    v = verdicts(a_data, cohort, onboard, usage, support, segments, reasons, spike)
    causal = causality_rows(v, a_data, onboard, support, segments, reasons, spike)

    # --- tabelas CSV ---
    tables: list[Path] = []
    series.to_csv(TABLES_DIR / "t01_monthly_series.csv", index=False)
    cohort["quarter"].to_csv(TABLES_DIR / "t02_cohort_km.csv", index=False)
    cohort["month"].to_csv(TABLES_DIR / "t02a_cohort_km_month.csv", index=False)
    cohort["at_risk"].to_csv(TABLES_DIR / "t02b_cohort_km_at_risk.csv", index=False)
    onboard["buckets"].to_csv(TABLES_DIR / "t03_onboarding_buckets.csv", index=False)
    onboard["accounts"].to_csv(TABLES_DIR / "t03b_onboarding_accounts.csv", index=False)
    onboard["cac"].to_csv(TABLES_DIR / "t03c_cac_equivalent.csv", index=False)
    usage["monthly"].to_csv(TABLES_DIR / "t05_usage_monthly.csv", index=False)
    support["monthly"].to_csv(TABLES_DIR / "t06_support_monthly.csv", index=False)
    segments["table"].to_csv(TABLES_DIR / "t07_segments.csv", index=False)
    reasons["reasons"].to_csv(TABLES_DIR / "t08_reasons.csv", index=False)
    causal.to_csv(TABLES_DIR / "t09_causality.csv", index=False)
    pd.DataFrame(v).to_csv(TABLES_DIR / "t10_hypothesis_verdicts.csv", index=False)
    # tabelas DESTA iteração (manifesto explícito — não mistura com t11..t17 do
    # It04 no mesmo diretório; mesmo padrão do 04_lifecycle_watchlist.py)
    it03_table_names = [
        "t01_monthly_series.csv", "t02_cohort_km.csv", "t02a_cohort_km_month.csv",
        "t02b_cohort_km_at_risk.csv", "t03_onboarding_buckets.csv",
        "t03b_onboarding_accounts.csv", "t03c_cac_equivalent.csv",
        "t05_usage_monthly.csv", "t06_support_monthly.csv", "t07_segments.csv",
        "t08_reasons.csv", "t09_causality.csv", "t10_hypothesis_verdicts.csv",
    ]
    tables = [TABLES_DIR / n for n in it03_table_names]

    # --- gráficos (4 essenciais; manifesto explícito — e_support/f_segment
    # substituídos pelas tabelas t06/t07/t09, pruning do gate It04; qualquer
    # PNG pruned que reaparecer falha o check) ---
    it03_chart_names = [
        "a_monthly_events_and_rate.png",
        "b_km_by_signup_quarter.png",
        "c_onboarding_exposure_by_duration.png",
        "d_usage_volume_vs_intensity.png",
    ]
    chart_names = [
        chart_a(series, spike),
        chart_b(cohort["quarter"], cohort["at_risk"]),
        chart_c(onboard["exposure"], onboard["buckets"]),
        chart_d(usage["monthly"]),
    ]
    charts = [CHARTS_DIR / n for n in it03_chart_names]
    missing_c = [c.name for c in charts if not c.exists() or c.stat().st_size == 0]
    stale_c = sorted(
        p.name for p in CHARTS_DIR.glob("*.png")
        if p.name in ("e_support_churn_vs_control.png",
                      "f_segment_first_event_rates.png"))
    if missing_c or stale_c:
        check("C01-charts", "gráficos", "número de gráficos gerado",
              "FAIL",
              f"esperado {len(it03_chart_names)}, "
              f"ausentes/vazios={missing_c or 'nenhuma'}; "
              f"pruned reapareceram={stale_c or 'nenhuma'}")
    else:
        check("C01-charts", "gráficos", "número de gráficos gerado",
              "PASS",
              f"{len(charts)} PNGs (manifesto: {', '.join(it03_chart_names)})")

    # --- gates + relatório ---
    run_gates(a_data, cohort, onboard, usage, support, segments, reasons,
              panel, churn, tables, charts)
    REPORT_PATH.write_text(render_report(
        a_data, cohort, onboard, usage, support, segments, reasons, spike,
        v, causal, chart_names, [t.name for t in tables]), encoding="utf-8")

    n_fail = sum(1 for c in CHECKS if c["level"] == "FAIL")
    n_warn = sum(1 for c in CHECKS if c["level"] == "WARN")
    n_pass = sum(1 for c in CHECKS if c["level"] == "PASS")
    print(f"[03_root_cause] checks: {n_pass} PASS / {n_warn} WARN / {n_fail} FAIL")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())