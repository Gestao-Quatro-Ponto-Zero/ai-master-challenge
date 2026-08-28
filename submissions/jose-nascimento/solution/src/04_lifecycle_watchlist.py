#!/usr/bin/env python3
"""
04_lifecycle_watchlist.py — Ciclos de reativação, jornada da conta e watchlist
operacional (Iteração 04).

Reconstrói a jornada de cada conta (eventos, reativações marcadas, ciclos reais
de estado no painel account-month, valor acumulado) e valida por backtest
point-in-time SEM ML se algum sinal observável até a data índice prediz o
próximo evento. As regras do backtest e a regra de composição da watchlist
foram fixadas ANTES dos resultados (ver
`process-log/decisions/iteration-04-watchlist-decisions.md`, D4/D6); nenhum
threshold foi ajustado após ver os números.

Contrato analítico (Iteração 02) respeitado:
- eventos ≠ subscriptions ≠ snapshot (lentes separadas; contrato §4);
- winner = estado/exposição, nunca churn contratual isolado (§6);
- `gross ending MRR` = exposição, não receita perdida (§5);
- anti-leakage: features <= data índice; targets/outcomes nunca em features;
  `accounts.churn_flag` (snapshot) proibido em features (§8);
- censura no corte 2024-12-31; follow-up explícito em análises de reativação.

Nomenclatura: a watchlist é nomeada conforme o resultado do backtest
(regra D8): se nenhum sinal tiver lift consistente, é `operational
priority/exposure` (ordenação por exposição + evidência), NUNCA "churn risk
score". Sem ML, sem recomendações (It05), sem ROI.

Gera, de forma offline e determinística (sem timestamp; ordenações estáveis):
    solution/evidence/04_lifecycle_watchlist_report.md
    solution/out/tables/t11..t17*.csv          (auditabilidade)
    solution/out/charts/It04_c/d_*.png         (2 gráficos essenciais; It04_a/b
                                                substituídos pelas tabelas
                                                t12/t13 — pruning do gate It04)

Semântica de resultado (mesma família das iterações 01-03):
    - PASS : check íntegro.
    - WARN : divergência/anomalia de qualidade esperada (documentada).
    - FAIL : arquivo/schema estrutural ausente ou invariante violado.
    Exit code: 0 se não houver FAIL; 1 caso contrário. Em caso de FAIL
    estrutural o relatório é SEMPRE regravado (sem output stale) e sem
    traceback não tratado.

Restrições: apenas stdlib + pandas + matplotlib; sem rede; paths relativos ao
próprio projeto.
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

REPORT_PATH = EVIDENCE_DIR / "04_lifecycle_watchlist_report.md"
PANEL_PATH = PROCESSED_DIR / "account_month.csv"

# ----------------------------------------------------------------------------
# Constantes (contrato It02; regras PRÉ-especificadas — decisions D4/D6)
# ----------------------------------------------------------------------------
DATA_CUT = pd.Timestamp("2024-12-31")     # data-limite (corte; censura)
WATCH_CUT = DATA_CUT                      # cutoff da watchlist
ONBOARDING_DAYS = 90                      # tenure <= 90d = onboarding (It03 H1/H8)
RECENT_DAYS = 90                          # janela "evento recente" / R1 recente
BACKTEST_CUTOFFS = ["2024-03-31", "2024-06-30", "2024-09-30"]
BACKTEST_HORIZON_DAYS = 90                # horizonte primário (observável p/ todos)
SENSITIVITY_HORIZON = 180                 # sensibilidade (cutoffs 03-31 e 06-30)
REACT_THRESHOLD = 2                       # R_A: recorrência = >= 2 eventos
LIFT_VALIDATION = 1.15                    # D4: lift > 1,15 nos 3 cutoffs p/ validar
MIN_RULE_N = 25                           # D4: N mínimo p/ considerar a regra
WATCH_TIER_A = 8                          # D6: caps da watchlist (8/8/4)
WATCH_TIER_B = 8
WATCH_TIER_C = 4

# Regras do backtest (identificador, rótulo, descrição) — fixadas em D4.
RULES = [
    ("A", "recorrencia>=2",      "n_events_pre >= 2"),
    ("B", "reativacao>=1",       "n_react_pre >= 1"),
    ("C", "evento<=90d",         "last_event_days <= 90"),
    ("D", "onboarding<=90d",     "tenure_days <= 90"),
    ("E", "winner>=P75",         "winner_mrr_at >= P75 do cutoff"),
    ("F", "A e C",               "recorrencia>=2 E evento<=90d"),
    ("G", "B e C",               "reativacao>=1 E evento<=90d"),
    ("H", "D e C",               "onboarding<=90d E evento<=90d"),
    ("I", "E e (A|B|C)",         "winner>=P75 E (recorrencia|reativacao|evento<=90d)"),
]

# Colunas mínimas exigidas por arquivo (guarda estrutural desta iteração).
REQUIRED = {
    "ravenstack_accounts.csv": [
        "account_id", "signup_date", "churn_flag",
    ],
    "ravenstack_subscriptions.csv": [
        "subscription_id", "account_id", "start_date", "end_date", "mrr_amount",
        "churn_flag",
    ],
    "ravenstack_churn_events.csv": [
        "churn_event_id", "account_id", "churn_date", "is_reactivation",
    ],
}
PANEL_COLUMNS = [
    "account_id", "month", "status", "winner_mrr",
    "churn_flag_snapshot_2024_12_31",
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
    return [c for c in cols if c not in df.columns]


def guard_columns(df: pd.DataFrame, cols: list[str], check_id: str, scope: str,
                  fname: str) -> None:
    miss = missing_cols(df, cols, fname)
    if miss:
        check(check_id, scope, "colunas mínimas presentes",
              "FAIL", f"{fname}: faltam {miss}")
    else:
        check(check_id, scope, "colunas mínimas presentes",
              "PASS", f"{fname}: {len(cols)} colunas exigidas presentes")


# ----------------------------------------------------------------------------
# Carga com guardas estruturais
# ----------------------------------------------------------------------------
def load_all() -> dict[str, pd.DataFrame]:
    loaded: dict[str, pd.DataFrame] = {}
    for fname, cols in REQUIRED.items():
        path = RAW_DIR / fname
        if not path.exists():
            check(f"F01-{fname}", fname, "arquivo presente e carregável",
                  "FAIL", "arquivo ausente")
            continue
        try:
            df = pd.read_csv(path)
        except Exception as exc:  # noqa: BLE001 — guarda estrutural, sem traceback
            check(f"F01-{fname}", fname, "arquivo presente e carregável",
                  "FAIL", f"erro de parse: {type(exc).__name__}")
            continue
        check(f"F01-{fname}", fname, "arquivo presente e carregável",
              "PASS", f"{path.stat().st_size} bytes, CSV parseado ({len(df)} registros)")
        guard_columns(df, cols, f"S01-{fname}", fname, fname)
        loaded[fname] = df
    return loaded


def load_panel() -> pd.DataFrame | None:
    if not PANEL_PATH.exists():
        check("F01-account_month.csv", "account_month.csv",
              "arquivo presente e carregável", "FAIL", "arquivo ausente")
        return None
    try:
        df = pd.read_csv(PANEL_PATH)
    except Exception as exc:  # noqa: BLE001
        check("F01-account_month.csv", "account_month.csv",
              "arquivo presente e carregável", "FAIL",
              f"erro de parse: {type(exc).__name__}")
        return None
    check("F01-account_month.csv", "account_month.csv",
          "arquivo presente e carregável", "PASS",
          f"CSV parseado ({len(df)} linhas)")
    guard_columns(df, PANEL_COLUMNS, "S02-panel", "account_month.csv",
                  "account_month.csv")
    return df


# ----------------------------------------------------------------------------
# Estatísticas de recorrência e reativação (lente de eventos)
# ----------------------------------------------------------------------------
def recurrence_stats(churn: pd.DataFrame) -> dict:
    """Distribuição de eventos por conta; concentração; gaps entre eventos."""
    cnt = churn.groupby("account_id").size()
    dist = cnt.value_counts().sort_index()
    out = {
        "total_events": int(len(churn)),
        "accounts_with_event": int(cnt.size),
        "dist": {int(k): int(v) for k, v in dist.items()},
        "accounts_2plus": int((cnt >= 2).sum()),
        "accounts_3plus": int((cnt >= 3).sum()),
        "max_events": int(cnt.max()),
        "events_from_multi": int(cnt[cnt >= 2].sum()),
        "accounts_1": int((cnt == 1).sum()),
    }
    # gaps entre eventos consecutivos (por conta; ordenado por data)
    ev = churn.sort_values(["account_id", "churn_date"]).copy()
    ev["churn_date"] = pd.to_datetime(ev["churn_date"])
    ev["gap_days"] = ev.groupby("account_id")["churn_date"].diff().dt.days
    gaps = ev.loc[ev["gap_days"].notna(), "gap_days"]
    out["n_gaps"] = int(len(gaps))
    out["gap_median"] = float(gaps.median())
    out["gap_mean"] = float(gaps.mean())
    out["gaps_le90"] = int((gaps <= RECENT_DAYS).sum())
    return out


def reactivation_episodes(churn: pd.DataFrame) -> dict:
    """Episódios de reativação (flag is_reactivation): sequência temporal,
    gaps e Kaplan-Meier do tempo até o próximo evento com censura no corte.
    NENHUM episódio sem próximo evento observado é chamado de 'sucesso':
    a censura é declarada (follow-up explícito)."""
    ev = churn.copy()
    ev["churn_date"] = pd.to_datetime(ev["churn_date"])
    flags = ev[ev["is_reactivation"] == True]  # noqa: E712
    rows: list[dict] = []
    for _, rr in flags.iterrows():
        aid = rr["account_id"]
        d = rr["churn_date"]
        prior = ev[(ev["account_id"] == aid) & (ev["churn_date"] < d)]["churn_date"]
        nxt = ev[(ev["account_id"] == aid) & (ev["churn_date"] > d)]["churn_date"]
        rows.append({
            "account_id": aid,
            "react_date": d,
            "gap_from_prev": (d - prior.max()).days if len(prior) else None,
            "has_prev": bool(len(prior)),
            "gap_to_next": (nxt.min() - d).days if len(nxt) else None,
            "has_next": bool(len(nxt)),
            "fu_days": (DATA_CUT - d).days,
        })
    eps = pd.DataFrame(rows)
    out: dict = {
        "n_flags": int(len(eps)),
        "n_accounts": int(eps["account_id"].nunique()),
        "first_event_flags": int((eps["has_prev"] == False).sum()),  # noqa: E712
        "n_with_prev": int(eps["has_prev"].sum()),
        "n_with_next": int(eps["has_next"].sum()),
        "n_censored": int((eps["has_next"] == False).sum()),  # noqa: E712
        "gap_from_prev_median": float(eps.loc[eps["has_prev"], "gap_from_prev"].median()),
        "gap_to_next_median": float(eps.loc[eps["has_next"], "gap_to_next"].median()),
        "gap_to_next_mean": float(eps.loc[eps["has_next"], "gap_to_next"].mean()),
        "episodes": eps,
        "monthly": flags.groupby(flags["churn_date"].dt.to_period("M").astype(str)).size(),
    }
    # flags recentes (out-dez/2024 = > corte-90d) e censuradas recentes — base das
    # frases de censura do relatório (derivadas em runtime, nunca hardcoded)
    recent_mask = eps["react_date"] > DATA_CUT - pd.Timedelta(days=RECENT_DAYS)
    out["recent_flags"] = int(recent_mask.sum())
    out["recent_censored"] = int(
        (recent_mask & (eps["has_next"] == False)).sum())  # noqa: E712
    # follow-up explícito: taxa com denominador de episódios com follow-up >= w
    fu: list[dict] = []
    for w in (30, 90, 180):
        sub = eps[eps["fu_days"] >= w]
        within = sub[(sub["has_next"]) & (sub["gap_to_next"] <= w)]
        fu.append({
            "window_days": w,
            "episodes_with_followup": int(len(sub)),
            "next_event_within": int(len(within)),
            "rate": float(len(within) / len(sub)) if len(sub) else float("nan"),
        })
    out["followup"] = fu
    # Kaplan-Meier do tempo até o próximo evento (censura no corte)
    ts = sorted(
        (int(r["gap_to_next"]) if r["has_next"] else int(r["fu_days"]), r["has_next"])
        for r in rows
    )
    n = len(ts)
    idx = 0
    surv = 1.0
    km: list[dict] = []
    median = None
    while idx < n:
        t = ts[idx][0]
        d = sum(1 for (tt, e) in ts[idx:] if tt == t and e)
        c = sum(1 for (tt, e) in ts[idx:] if tt == t and not e)
        n_risk = n - idx
        if d > 0:
            surv *= (1.0 - d / n_risk)
            km.append({"t": t, "survival": surv})
            if median is None and surv <= 0.5:
                median = t
        idx += d + c
    out["km"] = km
    out["km_median"] = median
    out["km_surv_90d"] = next(
        (item["survival"] for item in km if item["t"] >= RECENT_DAYS),
        km[-1]["survival"] if km else float("nan"))
    out["km_surv_180d"] = next(
        (item["survival"] for item in km if item["t"] >= SENSITIVITY_HORIZON),
        km[-1]["survival"] if km else float("nan"))
    return out


# ----------------------------------------------------------------------------
# Ciclos reais de estado (painel account-month; lente B)
# ----------------------------------------------------------------------------
def state_cycles(panel: pd.DataFrame, sub: pd.DataFrame) -> dict:
    """Transições active->inactive e inactive->active do painel, distinguindo
    gap inicial de ativação (signup -> primeira assinatura ativa) de retorno
    real. Conta ciclos completos active->inactive->active por conta."""
    pm = panel.sort_values(["account_id", "month"]).copy()
    prev = pm.groupby("account_id")["status"].shift(1)
    dec = (prev == "active") & (pm["status"] == "inactive")
    inc = (prev == "inactive") & (pm["status"] == "active")
    pm["_dec"] = dec
    pm["_inc"] = inc
    # inc é "gap de ativação" se a conta nunca teve mês ativo antes; senão retorno
    pm["_ever_active_before"] = pm.groupby("account_id")["status"].transform(
        lambda s: (s == "active").cumsum().shift(1).fillna(0))
    # R2 (churn-to-inactive) usa o winner do mês ANTERIOR à saída — o mês inativo
    # tem winner 0 no painel (INFO-2 dos revisores; coluna winner_mrr_prev)
    prev_winner = pm.groupby("account_id")["winner_mrr"].shift(1)
    dec_rows = pm[dec].copy()
    dec_rows["winner_mrr_prev"] = prev_winner[dec].astype(int)
    inc_rows = pm[inc].copy()
    inc_rows["_is_activation_gap"] = inc_rows["_ever_active_before"] == 0
    n_gap = int(inc_rows["_is_activation_gap"].sum())
    n_return = int((~inc_rows["_is_activation_gap"]).sum())
    # ciclo completo = conta com >= 1 saída (dec) E >= 1 retorno real (inc pós-ativação)
    return_accounts = set(inc_rows.loc[~inc_rows["_is_activation_gap"],
                                       "account_id"])
    cycle_accounts = sorted(set(dec_rows["account_id"]) & return_accounts)
    out = {
        "n_dec": int(len(dec_rows)),
        "n_inc": int(len(inc_rows)),
        "n_activation_gaps": n_gap,
        "n_returns": n_return,
        "cycle_accounts": cycle_accounts,
        "n_full_cycles": len(cycle_accounts),
        "dec_r2_sum": int(dec_rows["winner_mrr_prev"].sum()),
        "dec_rows": dec_rows[["account_id", "month", "winner_mrr",
                              "winner_mrr_prev"]].copy(),
        "inc_returns": inc_rows.loc[~inc_rows["_is_activation_gap"],
                                    ["account_id", "month"]].copy(),
    }
    # contratual: assinaturas encerradas seguidas de nova assinatura
    s2 = sub.sort_values(["account_id", "start_date"]).copy()
    s2["_next_start"] = s2.groupby("account_id")["start_date"].shift(-1)
    rel = s2[(s2["churn_flag"] == True) & s2["_next_start"].notna()]  # noqa: E712
    out["re_sign_subs"] = int(len(rel))
    out["re_sign_accounts"] = int(rel["account_id"].nunique())
    out["ended_sub_accounts"] = int(sub[sub["end_date"].notna()]["account_id"].nunique())
    return out


# ----------------------------------------------------------------------------
# Jornada por conta (t11) — features observáveis até o cutoff
# ----------------------------------------------------------------------------
def lifecycle_features(acc: pd.DataFrame, sub: pd.DataFrame, churn: pd.DataFrame,
                       panel: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por conta com jornada completa e campos observáveis até
    DATA_CUT. `lifecycle_value_proxy` = soma do winner_mrr mensal do painel
    (1 valor por account×mês — sem double-counting; PROXY, não receita GAAP).
    `accounts.churn_flag` entra APENAS como contexto/qualidade (rótulo
    snapshot), nunca como feature de predição (contrato §8)."""
    ev = churn.copy()
    ev["churn_date"] = pd.to_datetime(ev["churn_date"])
    sub2 = sub.copy()
    sub2["start_date"] = pd.to_datetime(sub2["start_date"])
    sub2["end_date"] = pd.to_datetime(sub2["end_date"])
    pm = panel.copy()

    rows: list[dict] = []
    n_ev = ev.groupby("account_id").size()
    n_react = ev[ev["is_reactivation"] == True].groupby("account_id").size()  # noqa: E712
    last = ev.sort_values("churn_date").groupby("account_id")["churn_date"].last()
    ended = sub2[sub2["end_date"].notna()]
    n_ended = ended.groupby("account_id").size()
    r1_total = ended.groupby("account_id")["mrr_amount"].sum()
    r1_recent = ended[ended["end_date"] > DATA_CUT - pd.Timedelta(days=RECENT_DAYS)] \
        .groupby("account_id")["mrr_amount"].sum()
    n_subs = sub2.groupby("account_id").size()
    dec_row = pm[pm["month"] == "2024-12"].set_index("account_id")
    proxy = pm.groupby("account_id")["winner_mrr"].sum()
    months_active = pm[pm["status"] == "active"].groupby("account_id").size()

    for _, a in acc.iterrows():
        aid = a["account_id"]
        tenure = (DATA_CUT - pd.Timestamp(a["signup_date"])).days
        le = last.get(aid)
        wm = dec_row.loc[aid, "winner_mrr"] if aid in dec_row.index else None
        rows.append({
            "account_id": aid,
            "signup_date": str(a["signup_date"]),
            "tenure_days": int(tenure),
            "n_subs_total": int(n_subs.get(aid, 0)),
            "n_subs_ended": int(n_ended.get(aid, 0)),
            "r1_mrr_total": int(r1_total.get(aid, 0)),
            "r1_mrr_recent_90d": int(r1_recent.get(aid, 0)),
            "n_events": int(n_ev.get(aid, 0)),
            "n_reactivations": int(n_react.get(aid, 0)),
            "last_event_date": str(le.date()) if pd.notna(le) else "",
            "last_event_days_ago": int((DATA_CUT - le).days) if pd.notna(le) else -1,
            "current_status": str(dec_row.loc[aid, "status"]) if aid in dec_row.index else "",
            "current_winner_mrr": int(wm) if pd.notna(wm) else 0,
            "lifecycle_value_proxy": int(proxy.get(aid, 0)),
            "months_active": int(months_active.get(aid, 0)),
            "churn_flag_snapshot_2024_12_31": int(a["churn_flag"]),
        })
    df = pd.DataFrame(rows)
    df["is_onboarding"] = df["tenure_days"] <= ONBOARDING_DAYS
    df["is_recent_event"] = (df["last_event_days_ago"] >= 0) & \
        (df["last_event_days_ago"] <= RECENT_DAYS)
    df["is_recurrence"] = df["n_events"] >= REACT_THRESHOLD
    df["is_reactivated"] = df["n_reactivations"] >= 1
    df["is_high_value"] = df["current_winner_mrr"] >= \
        df["current_winner_mrr"].quantile(0.75)
    return df


# ----------------------------------------------------------------------------
# Backtest point-in-time (sem ML; regras pré-especificadas em D4)
# ----------------------------------------------------------------------------
def wilson_ci(k: int, n: int) -> tuple[float, float]:
    """Intervalo de Wilson 95% para proporção k/n."""
    if n == 0:
        return (float("nan"), float("nan"))
    z = 1.96
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / den
    return (c - h, c + h)


def backtest_run(acc: pd.DataFrame, sub: pd.DataFrame, churn: pd.DataFrame,
                 panel: pd.DataFrame) -> dict:
    """Backtest temporal: para cada cutoff, features com dados <= cutoff e
    outcome = primeiro/próximo evento em (cutoff, cutoff+horizonte]. Múltiplos
    eventos no horizonte NÃO duplicam logos (outcome binário por conta)."""
    ev = churn.copy()
    ev["churn_date"] = pd.to_datetime(ev["churn_date"])
    sub2 = sub.copy()
    sub2["start_date"] = pd.to_datetime(sub2["start_date"])
    sub2["end_date"] = pd.to_datetime(sub2["end_date"])
    acc2 = acc.copy()
    acc2["signup_date"] = pd.to_datetime(acc2["signup_date"])

    cutoffs = [(c, BACKTEST_HORIZON_DAYS) for c in BACKTEST_CUTOFFS]
    cutoffs += [(c, SENSITIVITY_HORIZON)
                for c in BACKTEST_CUTOFFS[:2]]  # sensibilidade 180d
    all_rows: list[dict] = []
    per_cutoff: list[dict] = []

    for cstr, horizon in cutoffs:
        c = pd.Timestamp(cstr)
        c_end = c + pd.Timedelta(days=horizon)
        elig = acc2[acc2["signup_date"] <= c]
        outcome_ser = ev[(ev["churn_date"] > c) & (ev["churn_date"] <= c_end)] \
            .groupby("account_id").size()
        n_outcome = int((elig["account_id"].isin(outcome_ser.index)).sum())

        # ---- features: SOMENTE dados <= cutoff ----
        e_pre = ev[ev["churn_date"] <= c]
        n_ev_pre = e_pre.groupby("account_id").size()
        n_react_pre = e_pre[e_pre["is_reactivation"] == True] \
            .groupby("account_id").size()  # noqa: E712
        last_pre = e_pre.sort_values("churn_date").groupby("account_id")["churn_date"].last()
        r1_pre = sub2[(sub2["end_date"] > c - pd.Timedelta(days=RECENT_DAYS))
                      & (sub2["end_date"] <= c)] \
            .groupby("account_id")["mrr_amount"].sum()
        wm_at = panel[panel["month"] == cstr[:7]].set_index("account_id")["winner_mrr"]
        proxy_pre = panel[panel["month"] <= cstr[:7]] \
            .groupby("account_id")["winner_mrr"].sum()

        for _, a in elig.iterrows():
            aid = a["account_id"]
            tenure = (c - a["signup_date"]).days
            le = last_pre.get(aid)
            rows = {
                "account_id": aid,
                "cutoff": cstr,
                "horizon_days": horizon,
                "tenure_days": int(tenure),
                "n_events_pre": int(n_ev_pre.get(aid, 0)),
                "n_react_pre": int(n_react_pre.get(aid, 0)),
                "last_event_days": int((c - le).days) if pd.notna(le) else -1,
                "recent_ended_mrr_90d": int(r1_pre.get(aid, 0)),
                "winner_mrr_at": int(wm_at.get(aid, 0)) if aid in wm_at.index else 0,
                "lifecycle_proxy_pre": int(proxy_pre.get(aid, 0)),
                "outcome": int(aid in outcome_ser.index),
            }
            all_rows.append(rows)

        df = pd.DataFrame(all_rows)
        df = df[(df["cutoff"] == cstr) & (df["horizon_days"] == horizon)]
        baseline = df["outcome"].mean()
        p75 = df["winner_mrr_at"].quantile(0.75)
        rule_masks = {
            "A": df["n_events_pre"] >= REACT_THRESHOLD,
            "B": df["n_react_pre"] >= 1,
            "C": (df["last_event_days"] >= 0) & (df["last_event_days"] <= RECENT_DAYS),
            "D": df["tenure_days"] <= ONBOARDING_DAYS,
            "E": df["winner_mrr_at"] >= p75,
            "F": (df["n_events_pre"] >= REACT_THRESHOLD)
                 & (df["last_event_days"] >= 0) & (df["last_event_days"] <= RECENT_DAYS),
            "G": (df["n_react_pre"] >= 1)
                 & (df["last_event_days"] >= 0) & (df["last_event_days"] <= RECENT_DAYS),
            "H": (df["tenure_days"] <= ONBOARDING_DAYS)
                 & (df["last_event_days"] >= 0) & (df["last_event_days"] <= RECENT_DAYS),
            "I": (df["winner_mrr_at"] >= p75) & (
                (df["n_events_pre"] >= REACT_THRESHOLD)
                | (df["n_react_pre"] >= 1)
                | ((df["last_event_days"] >= 0) & (df["last_event_days"] <= RECENT_DAYS))),
        }
        for rid, _, desc in RULES:
            m = rule_masks[rid]
            n_rule = int(m.sum())
            k_rule = int(df.loc[m, "outcome"].sum())
            prec = k_rule / n_rule if n_rule else float("nan")
            rec = k_rule / n_outcome if n_outcome else float("nan")
            lo, hi = wilson_ci(k_rule, n_rule)
            per_cutoff.append({
                "cutoff": cstr, "horizon_days": horizon, "rule": rid,
                "rule_label": dict((r[0], r[1]) for r in RULES)[rid],
                "rule_desc": desc,
                "n_eligible": int(len(df)), "baseline_rate": round(baseline, 4),
                "n_outcome": n_outcome, "n_rule": n_rule, "rule_outcomes": k_rule,
                "precision": round(prec, 4) if prec == prec else "NA",
                "recall": round(rec, 4) if rec == rec else "NA",
                "lift": round(prec / baseline, 3) if (prec == prec and baseline > 0) else "NA",
                "ci_lo": round(lo, 4) if lo == lo else "NA",
                "ci_hi": round(hi, 4) if hi == hi else "NA",
            })
        # verificação anti-leakage: data máxima usada nas features <= cutoff
        max_feat_event = e_pre["churn_date"].max()
        max_feat_r1 = sub2[sub2["end_date"] <= c]["end_date"].max()
        check(f"G6b-leak-{cstr}-{horizon}", "anti-leakage",
              f"features do cutoff {cstr} (horizonte {horizon}d) usam apenas "
              "dados <= cutoff",
              "PASS" if (pd.isna(max_feat_event) or max_feat_event <= c)
              and (pd.isna(max_feat_r1) or max_feat_r1 <= c) else "FAIL",
              f"máx churn_date em features={max_feat_event}; máx end_date={max_feat_r1}; "
              f"cutoff={cstr}")

    return {"detail": pd.DataFrame(all_rows), "per_cutoff": pd.DataFrame(per_cutoff)}


def backtest_summary(bt: pd.DataFrame) -> dict:
    """Síntese pré-registrada (D4): regra validada se lift > 1,15 nos 3
    cutoffs de 90d com N >= 25. Retorna também o veredito por regra."""
    rows: list[dict] = []
    for rid, label, _ in RULES:
        sub = bt[(bt["rule"] == rid) & (bt["horizon_days"] == BACKTEST_HORIZON_DAYS)]
        lifts = [r for r in sub["lift"] if isinstance(r, float)]
        ns = sub["n_rule"].tolist()
        ok = (len(lifts) == 3 and all(l > LIFT_VALIDATION for l in lifts)
              and all(n >= MIN_RULE_N for n in ns))
        rows.append({
            "rule": rid, "rule_label": label,
            "lifts_90d": "; ".join(f"{l:.2f}" for l in lifts),
            "n_rule_by_cutoff": "; ".join(str(n) for n in ns),
            "validated": "SIM" if ok else "NAO",
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Segmentos de atenção (estados/jornadas; overlap declarado)
# ----------------------------------------------------------------------------
def priority_segments(lf: pd.DataFrame, bt_summary: pd.DataFrame) -> dict:
    def lifts(rid: str) -> str:
        """Lifts 90d da regra no formato '0,44/0,41/0,89' — mesma fonte do
        resumo (bt_summary), evitando números narrativos hardcoded."""
        row = bt_summary[bt_summary["rule"] == rid]
        if row.empty:
            return "NA"
        return row.iloc[0]["lifts_90d"].replace("; ", "/").replace(".", ",")

    multi = lf["n_events"] >= REACT_THRESHOLD
    n_multi = int(multi.sum())
    share_multi = pct(int(lf.loc[multi, "n_events"].sum()), int(lf["n_events"].sum()))
    n_s5 = int(lf["is_high_value"].sum())
    segs: list[dict] = []
    defs = [
        ("S1", "Onboarding (tenure<=90d)", "is_onboarding",
         f"sinal VALIDADO no backtest (regra D: lift {lifts('D')} nos cutoffs 90d)",
         "estado de jornada; mecanismo It03 H1/H8 (churn precoce de coortes novas)"),
        ("S2", "Repeat-event (>=2 eventos)", "is_recurrence",
         f"regra A: lift {lifts('A')} — SEM lift consistente; associação histórica",
         f"concentração de eventos ({share_multi} dos eventos vêm de {n_multi} "
         "contas); recorrência descreve histórico, não prediz próximo evento"),
        ("S3", "Reativacao recente (flag out-dez/2024)", "s3_recent_react",
         None,  # preenchido pelo caller (usa KM de reactivation_episodes)
         "episódio de evento marcado is_reactivation; NÃO é ciclo de estado; "
         "subconjunto de S4 (declarado)"),
        ("S4", "Evento recente (ultimo evento<=90d)", "is_recent_event",
         f"regra C: lift {lifts('C')} — SEM lift; janela acionável de CS",
         "último episódio de churn em out-dez/2024; acionabilidade operacional, "
         "não predição"),
        ("S5", "Alto valor (winner>=P75)", "is_high_value",
         f"regra E: lift {lifts('E')} — SEM lift; segmento de exposição, não risco",
         f"exposição atual (winner MRR >= P75); proteção de receita; {n_s5} contas "
         "(empates no quantil; 125 esperadas)"),
    ]
    react_recent = None  # S3 preenchido pelo caller (datas reais de reativação)
    for sid, name, col, backtest_note, rationale in defs:
        if col == "s3_recent_react":
            continue  # preenchido pelo caller
        m = lf[col]
        g = lf[m]
        segs.append({
            "segment": sid, "name": name,
            "N": int(len(g)),
            "current_mrr_sum": int(g["current_winner_mrr"].sum()),
            "lifecycle_proxy_sum": int(g["lifecycle_value_proxy"].sum()),
            "ever_event_rate": round(float((g["n_events"] >= 1).mean()), 4),
            "recent_event_rate": round(float(g["is_recent_event"].mean()), 4),
            "backtest_evidence": backtest_note,
            "uncertainty": "intervalos largos (N pequeno); censura no corte",
            "rationale": rationale,
        })
    # overlaps (matriz declarada — nunca oculta; S3 usa a MESMA definição da
    # tabela de segmentos: flag de reativação em out-dez/2024)
    overlaps: list[dict] = []
    for (n1, m1), (n2, m2) in [
        (("S1", lf["is_onboarding"]), ("S2", lf["is_recurrence"])),
        (("S1", lf["is_onboarding"]), ("S4", lf["is_recent_event"])),
        (("S2", lf["is_recurrence"]), ("S4", lf["is_recent_event"])),
        (("S3", lf["s3_recent_react"]), ("S4", lf["is_recent_event"])),
        (("S2", lf["is_recurrence"]), ("S3", lf["s3_recent_react"])),
    ]:
        overlaps.append({
            "segment_a": n1, "segment_b": n2,
            "overlap_n": int((m1 & m2).sum()),
        })
    return {"segments": pd.DataFrame(segs), "overlaps": pd.DataFrame(overlaps)}


# ----------------------------------------------------------------------------
# Exposição por lente separada (R1 gross ending MRR e winner atual)
# ----------------------------------------------------------------------------
def exposure_lenses(sub: pd.DataFrame, churn: pd.DataFrame, lf: pd.DataFrame) -> dict:
    """R1 (gross ending MRR, exposição contratual) e winner atual (exposição de
    estado) das contas multi-evento e reativadas — LENTES SEPARADAS (contrato
    §5): nenhum número é 'receita perdida' nem 'dinheiro recuperado'."""
    s2 = sub.copy()
    s2["end_date"] = pd.to_datetime(s2["end_date"])
    ended = s2[s2["end_date"].notna()]
    r1 = ended.groupby("account_id")["mrr_amount"].sum()
    ev = churn.copy()
    ev["churn_date"] = pd.to_datetime(ev["churn_date"])
    cnt = ev.groupby("account_id").size()
    multi = set(cnt[cnt >= REACT_THRESHOLD].index)
    react = set(ev[ev["is_reactivation"] == True]["account_id"])  # noqa: E712
    lf_idx = lf.set_index("account_id")
    out = {
        "multi": {
            "n": len(multi),
            "r1_total": int(r1.reindex(multi).sum()),
            "r1_share": float(r1.reindex(multi).sum() / r1.sum()) if r1.sum() else 0.0,
            "current_mrr": int(lf_idx.loc[list(multi), "current_winner_mrr"].sum()),
        },
        "react": {
            "n": len(react),
            "r1_total": int(r1.reindex(react).sum()),
            "r1_share": float(r1.reindex(react).sum() / r1.sum()) if r1.sum() else 0.0,
            "current_mrr": int(lf_idx.loc[list(react), "current_winner_mrr"].sum()),
        },
        "r1_total_all": int(r1.sum()),
    }
    return out


# ----------------------------------------------------------------------------
# Watchlist (tiers + caps declarados; D6)
# ----------------------------------------------------------------------------
def build_watchlist(lf: pd.DataFrame, cycle_accounts: list[str]) -> pd.DataFrame:
    df = lf.copy()
    # tier de prioridade (D6): A = onboarding (sinal validado); B = evento
    # recente (fora de A); C = histórico (recorrência/reativação, sem evento
    # recente, winner >= P50) — ordem de evidência + acionabilidade.
    p50 = df["current_winner_mrr"].quantile(0.5)
    tier: dict[str, str] = {}
    for _, r in df.iterrows():
        if r["is_onboarding"]:
            tier[r["account_id"]] = "A"
        elif r["is_recent_event"]:
            tier[r["account_id"]] = "B"
        elif (r["is_recurrence"] or r["is_reactivated"]) \
                and (not r["is_recent_event"]) and r["current_winner_mrr"] >= p50:
            tier[r["account_id"]] = "C"
        else:
            tier[r["account_id"]] = "X"
    df["watch_tier"] = df["account_id"].map(tier)
    top: list[pd.DataFrame] = []
    for t, cap in (("A", WATCH_TIER_A), ("B", WATCH_TIER_B), ("C", WATCH_TIER_C)):
        g = df[df["watch_tier"] == t].sort_values(
            ["current_winner_mrr", "account_id"], ascending=[False, True]).head(cap)
        top.append(g)
    wl = pd.concat(top).copy()
    wl["watch_rank"] = range(1, len(wl) + 1)
    wl["state_cycles"] = wl["account_id"].isin(cycle_accounts).astype(int)
    cols = ["watch_rank", "account_id", "watch_tier", "current_winner_mrr",
            "lifecycle_value_proxy", "tenure_days", "n_events", "n_reactivations",
            "n_subs_ended", "r1_mrr_recent_90d", "last_event_date",
            "last_event_days_ago", "current_status", "state_cycles",
            "is_onboarding", "is_recent_event", "is_recurrence", "is_reactivated",
            "is_high_value", "churn_flag_snapshot_2024_12_31"]
    return wl[cols]


# ----------------------------------------------------------------------------
# Rank comparison: top-20 current MRR vs top-20 lifecycle proxy (D5)
# ----------------------------------------------------------------------------
def rank_comparison(lf: pd.DataFrame) -> dict:
    topc = lf.nlargest(20, "current_winner_mrr")
    topl = lf.nlargest(20, "lifecycle_value_proxy")
    both = set(topc["account_id"]) & set(topl["account_id"])
    rows: list[dict] = []
    for i, (_, r) in enumerate(topc.iterrows(), start=1):
        rows.append({"dimension": "current_mrr", "rank": i,
                     "account_id": r["account_id"],
                     "current_winner_mrr": int(r["current_winner_mrr"]),
                     "lifecycle_value_proxy": int(r["lifecycle_value_proxy"]),
                     "tenure_days": int(r["tenure_days"])})
    for i, (_, r) in enumerate(topl.iterrows(), start=1):
        rows.append({"dimension": "lifecycle_proxy", "rank": i,
                     "account_id": r["account_id"],
                     "current_winner_mrr": int(r["current_winner_mrr"]),
                     "lifecycle_value_proxy": int(r["lifecycle_value_proxy"]),
                     "tenure_days": int(r["tenure_days"])})
    df = pd.DataFrame(rows)
    # rank shifts entre contas compartilhadas
    shifts: list[dict] = []
    rc = {a: i + 1 for i, a in enumerate(topc["account_id"])}
    rl = {a: i + 1 for i, a in enumerate(topl["account_id"])}
    for a in sorted(both):
        s = rc[a] - rl[a]
        if abs(s) >= 3:
            shifts.append({"account_id": a, "current_rank": rc[a],
                           "lifecycle_rank": rl[a], "shift": s})
    spearman = lf[["current_winner_mrr", "lifecycle_value_proxy"]] \
        .corr(method="spearman").iloc[0, 1]
    return {
        "table": df,
        "overlap": len(both),
        "jaccard": len(both) / (len(topc) + len(topl) - len(both)),
        "spearman": float(spearman),
        "shifts": pd.DataFrame(shifts),
        "top_current": list(topc["account_id"]),
        "top_lifecycle": list(topl["account_id"]),
    }


# ----------------------------------------------------------------------------
# Gráficos (2 essenciais; prefixo It04 — It04_a/b substituídos pelas tabelas
# t12/t13, pruning do gate It04; não repetem It03)
# ----------------------------------------------------------------------------
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
    """Rodapé em coordenadas de FIGURA (dentro do canvas; 2 linhas). Margens
    explícitas via subplots_adjust; NUNCA bbox_inches='tight' (que esticava o
    canvas com texto fora da figura e esmagava o eixo — causa raiz dos
    findings visuais dos revisores)."""
    fig.text(0.01, 0.02, line1, fontsize=6.5, color="#555555",
             ha="left", va="bottom")
    fig.text(0.01, 0.005, line2, fontsize=6.5, color="#555555",
             ha="left", va="bottom")


def chart_c(lf: pd.DataFrame, rc: dict) -> str:
    """Exposição atual (winner MRR) vs valor de jornada (lifecycle proxy),
    com top-20 de cada dimensão destacados. Legenda em faixa própria ACIMA
    dos eixos (não cobre pontos); rótulos com offset em pontos (sem colisão
    com o título)."""
    _style()
    topc = set(rc["top_current"])
    topl = set(rc["top_lifecycle"])
    both = topc & topl
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    fig.subplots_adjust(top=0.80, bottom=0.13, left=0.105, right=0.97)
    for _, r in lf.iterrows():
        if r["account_id"] in both:
            c, ms, z = "#CC79A7", 30, 26
        elif r["account_id"] in topc:
            c, ms, z = "#D55E00", 20, 18
        elif r["account_id"] in topl:
            c, ms, z = "#009E73", 20, 18
        else:
            c, ms, z = "#0072B2", 10, 10
        ax.scatter(r["current_winner_mrr"], r["lifecycle_value_proxy"],
                   color=c, s=ms, zorder=z, alpha=0.8)
    for aid in ("A-68f37c", "A-a8d89d", "A-c70870"):
        r = lf[lf["account_id"] == aid].iloc[0]
        ax.annotate(aid, (r["current_winner_mrr"], r["lifecycle_value_proxy"]),
                    xytext=(7, 7), textcoords="offset points", fontsize=7,
                    color="#333333")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks([10**2, 10**3, 10**4])  # sem overhang 10^5 do AutoLocator
    ax.set_yticks([10**3, 10**4, 10**5])  # sem overhang 10^2/10^6
    ax.set_xlabel("current winner MRR (US$/mês; exposição atual)")
    ax.set_ylabel("lifecycle_value_proxy (US$; Σ winner MRR mensal)")
    ax.set_title("Exposição atual vs valor de jornada (proxy log-log)", pad=6)
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#0072B2",
               markersize=6, label="demais contas (500)"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#D55E00",
               markersize=6, label="top-20 current MRR"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#009E73",
               markersize=6, label="top-20 lifecycle proxy"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#CC79A7",
               markersize=7, label="nas duas listas"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.885),
               ncol=4, fontsize=7.5, frameon=True)
    _footer(fig,
            "Fonte: data/processed/account_month.csv (winner MRR mensal; soma sem "
            "dupla contagem). Proxy operacional, não receita GAAP.",
            "Gerado por src/04_lifecycle_watchlist.py.")
    path = CHARTS_DIR / "It04_c_lifecycle_vs_current_mrr.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path.name


def chart_d(bt: pd.DataFrame) -> str:
    """Lift por regra × cutoff (90d) — dot plot HORIZONTAL com CI de Wilson:
    regras no eixo y, lift no x; 3 cutoffs por cor/offset; linhas verticais em
    1,0 e no limiar 1,15; legenda fora dos dados; R_D destacado por faixa leve
    + marcadores maiores (sem poluição de anotações internas)."""
    _style()
    sub = bt[(bt["horizon_days"] == BACKTEST_HORIZON_DAYS)].copy()
    rules = [r[0] for r in RULES]
    cutoffs = sorted(sub["cutoff"].unique())
    colors = ["#0072B2", "#E69F00", "#009E73"]
    offsets = [-0.22, 0.0, 0.22]
    from matplotlib.lines import Line2D
    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    fig.subplots_adjust(top=0.85, bottom=0.155, left=0.27, right=0.965)
    # faixa de destaque de R_D (índice 3 de A..I) — leve, sem textos no interior
    ax.axhspan(len(rules) - 1 - 3 - 0.5, len(rules) - 1 - 3 + 0.5,
               color="#f2f2f2", zorder=0)
    for i, c in enumerate(cutoffs):
        g = sub[sub["cutoff"] == c].set_index("rule").reindex(rules)
        for j, r in enumerate(rules):
            lift = g.loc[r, "lift"]
            if not isinstance(lift, float):
                continue
            lo = g.loc[r, "ci_lo"]
            hi = g.loc[r, "ci_hi"]
            base = g["baseline_rate"].iloc[0]
            y = len(rules) - 1 - j + offsets[i]
            err = [[lift - max(0.0, float(lo) / base)],
                   [float(hi) / base - lift]]
            big = r == "D"
            ax.errorbar(lift, y, xerr=err, fmt="o", color=colors[i],
                        ms=(9 if big else 6.5),
                        mec="#333333" if big else "none", mew=0.8 if big else 0,
                        ecolor=colors[i], elinewidth=1.0, capsize=0,
                        alpha=0.95, zorder=3)
    ax.axvline(1.0, color="#555555", lw=1.0, linestyle="--", zorder=1)
    ax.text(1.0, len(rules) - 0.38, "baseline (lift = 1)", fontsize=7,
            color="#555555", ha="center")
    ax.axvline(LIFT_VALIDATION, color="#D55E00", lw=0.9, linestyle=":", zorder=1)
    ax.text(LIFT_VALIDATION + 0.02, len(rules) - 0.38,
            f"limiar {LIFT_VALIDATION}", fontsize=7, color="#D55E00", ha="left")
    ax.set_yticks(list(range(len(rules))))
    ax.set_yticklabels([f"R_{r[0]} {r[1]}" for r in RULES], fontsize=7.5)
    ax.set_xlabel("lift (precision / baseline) — horizonte 90d; "
                  "barras = CI de Wilson 95% da precision")
    ax.set_title("Backtest point-in-time: lift por regra × cutoff (sem ML; "
                 "regras pré-especificadas)", pad=8)
    ax.set_xlim(0, 2.9)
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=colors[i],
               markersize=7, label=f"cutoff {c}") for i, c in enumerate(cutoffs)
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.955),
               ncol=3, fontsize=7.5, frameon=True)
    _footer(fig,
            "Fonte: data/raw/*.csv + data/processed/account_month.csv; features <= "
            "cutoff; outcome = 1º/próximo evento em (cutoff, cutoff+90d].",
            "CI = intervalo de Wilson 95% da precision escalado pela baseline; "
            "R_D destacado (única regra validada — D4). Gerado por "
            "src/04_lifecycle_watchlist.py.")
    path = CHARTS_DIR / "It04_d_backtest_lift.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path.name


# ----------------------------------------------------------------------------
# Render do relatório
# ----------------------------------------------------------------------------
def render_report(rec: dict, react: dict, cyc: dict, lf: pd.DataFrame,
                  bt: dict, bt_sum: pd.DataFrame, seg: dict, wl: pd.DataFrame,
                  rc: dict, expo: dict, chart_names: list[str],
                  table_names: list[str], structural_fail: bool = False) -> str:
    if structural_fail:
        return (
            "# Relatório de Ciclos, Jornada e Watchlist — Iteração 04 (RavenStack)\n\n"
            "## Falha estrutural\n\n"
            "O pipeline não pôde executar: arquivos/schema exigidos ausentes ou "
            "inválidos (ver checks acima). Nenhuma análise foi gerada; tabelas e "
            "gráficos não foram regravados (outputs anteriores preservados no "
            "histórico, sem resultado stale). Corrija a fonte e re-execute.\n\n"
            "## Checks emitidos\n\n| ID | Escopo | Check | Veredito | Detalhe |\n"
            "|---|---|---|---|---|\n" +
            "\n".join(
                f"| {c['id']} | {c['scope']} | {c['description']} | {c['level']} | "
                f"{c['detail']} |" for c in CHECKS) + "\n"
        )

    # ---- números narrativos derivados em runtime (nada hardcoded; âncoras
    # verificadas nos gates G13) ----
    bt_df = bt["per_cutoff"]
    bt180 = bt_df[bt_df["horizon_days"] == SENSITIVITY_HORIZON]

    def lifts_txt(rid: str, horizon: int) -> str:
        sub = bt_df[(bt_df["rule"] == rid) & (bt_df["horizon_days"] == horizon)] \
            .sort_values("cutoff")
        return "/".join(f"{l:.2f}".replace(".", ",") for l in sub["lift"]
                        if isinstance(l, float))

    rd90 = bt_df[(bt_df["rule"] == "D")
                 & (bt_df["horizon_days"] == BACKTEST_HORIZON_DAYS)]
    prec_min, prec_max = float(rd90["precision"].min()), float(rd90["precision"].max())
    base_min, base_max = float(rd90["baseline_rate"].min()), \
        float(rd90["baseline_rate"].max())
    exc_parts: list[str] = []
    exc_cutoffs: list[str] = []
    for rid, _, _ in RULES:
        sub = bt180[(bt180["rule"] == rid) & (bt180["lift"] > 1.05)
                    & (bt180["n_rule"] < MIN_RULE_N)].sort_values("cutoff")
        for _, row in sub.iterrows():
            exc_parts.append(f"R_{rid} {row['lift']:.2f} (N={int(row['n_rule'])})"
                             .replace(".", ","))
            exc_cutoffs.append(str(row["cutoff"]))
    exc_txt = "; ".join(exc_parts) if exc_parts else "nenhuma"
    exc_cuts_txt = ", ".join(sorted(set(exc_cutoffs))) if exc_cutoffs else "—"
    cens_txt = (
        f"a maioria é recente ({react['recent_censored']} de "
        f"{react['n_censored']} = {pct(react['recent_censored'], react['n_censored'])})"
        if react["recent_censored"] > react["n_censored"] / 2 else
        f"{react['recent_censored']} de {react['n_censored']} "
        f"({pct(react['recent_censored'], react['n_censored'])}) são recentes")
    a8 = lf[lf["account_id"] == "A-a8d89d"]
    c7 = lf[lf["account_id"] == "A-c70870"]
    a8_row = a8.iloc[0] if len(a8) else None
    c7_row = c7.iloc[0] if len(c7) else None
    a8_note = None
    if a8_row is not None:
        in_life = a8_row["account_id"] in rc["top_lifecycle"]
        in_curr = a8_row["account_id"] in rc["top_current"]
        a8_note = ("top-20 da jornada, fora do top-20 atual"
                   if (in_life and not in_curr)
                   else "exemplo de conta antiga com jornada longa")
    n_snapshot = int(lf["churn_flag_snapshot_2024_12_31"].sum())
    r2_ci = int(cyc.get("dec_r2_sum", 0))

    s = [
        "# Relatório de Ciclos de Reativação, Jornada da Conta e Watchlist — "
        "Iteração 04 (RavenStack)",
        "",
        "Gerado por `solution/src/04_lifecycle_watchlist.py` (execução offline e "
        "determinística; sem timestamp para garantir output byte-a-byte estável "
        "entre execuções).",
        "",
        "## 1. Metodologia",
        "",
        "- **Contrato analítico (It02):** `solution/docs/analytical-contract.md` — "
        "eventos ≠ subscriptions ≠ snapshot (lentes C/B/A); winner = estado/exposição "
        "(§6); gross ending MRR = exposição, não receita perdida (§5); anti-leakage: "
        "features <= data índice, targets nunca em features (§8); censura no corte "
        "2024-12-31.",
        "- **Regras pré-especificadas ANTES dos resultados:** `process-log/decisions/"
        "iteration-04-watchlist-decisions.md` (D4: regras do backtest com thresholds "
        "fixos; D6: composição da watchlist; D8: nomenclatura proporcional ao lift). "
        "Nenhum threshold foi ajustado após ver os números. **Nota de transparência "
        "(registro honesto):** o arquivo de decisões foi commitado no MESMO commit do "
        "código e dos outputs (`adbbad7`) — a cronologia git não prova a separação "
        "temporal; a pré-especificação é atestada pelo conteúdo interno (números de "
        "exploração que divergem dos finais, ex.: KM 0,72/0,64 vs 0,653/0,476) e por "
        "auto-relato do executor (a prática It03 de commitar decisões antes do código "
        "é retomada nas It05+).",
        "- **Escopo:** NENHUMA recomendação/ROI (It05), NENHUM modelo preditivo/ML, "
        "nenhum score somando pesos sem validação.",
        "- **Saídas:** este relatório; tabelas em `solution/out/tables/` "
        f"({len(table_names)} arquivos); gráficos em `solution/out/charts/` "
        f"({len(chart_names)} arquivos).",
        "",
        "## 2. Recorrência de eventos (lente C — histórico, NÃO predição)",
        "",
        f"- Eventos totais: **{rec['total_events']}**; contas com >= 1 evento: "
        f"**{rec['accounts_with_event']}** de 500.",
        f"- Distribuição por conta (0/1/2/3/4/5 eventos): "
        f"{rec['dist'].get(0, 0)} / {rec['dist'].get(1, 0)} / {rec['dist'].get(2, 0)} / "
        f"{rec['dist'].get(3, 0)} / {rec['dist'].get(4, 0)} / {rec['dist'].get(5, 0)} "
        f"contas. Máximo: **{rec['max_events']}** eventos.",
        f"- **Recorrência:** {rec['accounts_2plus']} contas com >= 2 eventos; "
        f"{rec['accounts_3plus']} com >= 3. Concentração: **{rec['events_from_multi']} "
        f"de {rec['total_events']} eventos ({pct(rec['events_from_multi'], rec['total_events'])})** "
        f"vêm das contas com >= 2 eventos — {rec['accounts_2plus']} contas concentram "
        f"{pct(rec['events_from_multi'], rec['total_events'])} dos episódios.",
        f"- Gaps entre eventos consecutivos da mesma conta: n={rec['n_gaps']}, "
        f"mediana **{fmt(rec['gap_median'])} dias**, média {fmt(rec['gap_mean'])}; "
        f"{rec['gaps_le90']} gaps ({pct(rec['gaps_le90'], rec['n_gaps'])}) <= 90d. "
        "Este é o espaçamento observado ENTRE eventos — não é uma predição do próximo "
        "evento (ver backtest, seção 6: a regra de recorrência NÃO tem lift).",
        f"- **Exposição dessas contas (lentes separadas, contrato §5):** R1 gross "
        f"ending MRR das {expo['multi']['n']} contas multi-evento = "
        f"**{fmt(expo['multi']['r1_total'])}** "
        f"({pct(expo['multi']['r1_total'], expo['r1_total_all'])} do R1 da janela "
        f"{fmt(expo['r1_total_all'])}) — exposição contratual, NÃO receita perdida; "
        f"winner atual (estado) dessas contas = **{fmt(expo['multi']['current_mrr'])}**/mês. "
        "As duas lentes medem coisas diferentes e não se somam.",
        "",
        "## 3. Reativação marcada (`is_reactivation`) — sequência temporal com censura",
        "",
        f"- Flags: **{react['n_flags']}** em **{react['n_accounts']}** contas "
        f"(confirmado: {react['n_flags']} flags / {react['n_accounts']} contas).",
        f"- **{react['first_event_flags']}** flags são o PRIMEIRO evento da conta "
        "(sem evento anterior na janela 2023-2024): a flag marca 'retorno' no dataset "
        "sem evento anterior observável — nuance estrutural, não silenciada.",
        f"- Episódios com evento anterior: {react['n_with_prev']} (gap mediano "
        f"{fmt(react['gap_from_prev_median'])} dias).",
        f"- Próximo evento após a reativação: observado em {react['n_with_next']} "
        f"episódios (gap mediano {fmt(react['gap_to_next_median'])} dias; média "
        f"{fmt(react['gap_to_next_mean'])}); **{react['n_censored']} episódios sem "
        "próximo evento observado** — NÃO são 'sucesso de reativação': "
        f"{react['recent_flags']} de {react['n_flags']} flags "
        f"({pct(react['recent_flags'], react['n_flags'])}) ocorrem em out-dez/2024 "
        "(parcela substancial, NÃO maioria) e a janela termina no corte (censura). "
        f"Entre as censuradas ({react['n_censored']} episódios), {cens_txt} em "
        "out-dez/2024 — a censura concentra-se nos episódios mais recentes.",
        "- **Follow-up explícito (denominador declarado):**",
        "",
        "| Janela | Episódios com follow-up >= janela | Próximo evento dentro da janela | Taxa |",
        "|---|---|---|---|",
    ]
    for f in react["followup"]:
        s.append(
            f"| <= {f['window_days']}d | {f['episodes_with_followup']} | "
            f"{f['next_event_within']} | {pct(f['next_event_within'], f['episodes_with_followup'])} |")
    s += [
        "",
        f"- **Kaplan-Meier (tempo até o próximo evento após reativação; censura no "
        f"corte):** sobrevivência em 90d = **{react['km_surv_90d']:.3f}** "
        f"(ou seja, ≈ {100 * (1 - react['km_surv_90d']):.0f}% dos episódios têm "
        f"próximo evento <= 90d); em 180d = {react['km_surv_180d']:.3f}; mediana = "
        f"**{react['km_median']} dias** (alcançada na janela). A taxa observada "
        f"({react['n_with_next']}/{react['n_flags']} = "
        f"{pct(react['n_with_next'], react['n_flags'])}) SUBestima o retorno por "
        "censura — e nenhuma taxa aqui é 'receita recuperada': reativação é "
        "episódio de evento, sem ligação demonstrável com receita (contrato §5).",
        f"- **Exposição das contas reativadas (lentes separadas):** R1 das "
        f"{expo['react']['n']} contas com flag = **{fmt(expo['react']['r1_total'])}** "
        f"({pct(expo['react']['r1_total'], expo['r1_total_all'])} do R1) — exposição "
        f"contratual, NÃO receita recuperada pela reativação; winner atual = "
        f"**{fmt(expo['react']['current_mrr'])}**/mês (estado).",
        "",
        "## 4. Ciclos reais de estado (painel account-month; lente B)",
        "",
        f"- Transições `active→inactive` no painel: **{cyc['n_dec']}** (contrato R2: "
        f"churn-to-inactive = {fmt(r2_ci)} em exatamente essas {cyc['n_dec']} "
        "transições).",
        f"- Transições `inactive→active`: **{cyc['n_inc']}**, das quais "
        f"**{cyc['n_activation_gaps']}** são o gap inicial signup→primeira assinatura "
        f"ativa (ex.: A-019782 signup 2023-04, primeira assinatura ativa 2023-06) e "
        f"**{cyc['n_returns']}** são retornos reais após inatividade.",
        f"- **Ciclos completos active→inactive→active: {cyc['n_full_cycles']} contas** "
        f"({', '.join(cyc['cycle_accounts'])}). Detalhe: A-180abf (inativa nov/2023, "
        f"ativa desde jan/2024; 5 eventos, nenhum flag de reativação) e A-0baac2 "
        f"(inativa set/2024 — sub encerrada 2024-09-13 —, ativa desde out/2024; "
        f"4 eventos, nenhum flag de reativação).",
        "- **Comparação honesta das lentes:** 175 contas com >= 2 eventos (recorrência) "
        "≠ 55 contas com flag de reativação (evento) ≠ 2 contas com ciclo real de "
        "estado (assinatura). Nenhuma dessas contagens é intercambiável: 175 "
        "multi-evento NÃO são 175 contas que morreram/reviveram — o estado de "
        "assinatura mudou de ativo→inativo apenas 2 vezes em toda a janela.",
        f"- Contratualmente: {cyc['ended_sub_accounts']} contas têm assinatura "
        f"encerrada; {cyc['re_sign_accounts']} contas têm assinatura encerrada "
        f"SEGUIDA de nova assinatura ({cyc['re_sign_subs']} assinaturas) — "
        "re-assinatura contratual, outra lente ainda (não confundir com reativação "
        "de evento nem com ciclo de estado do painel).",
        "",
        "## 5. Jornada/valor: `lifecycle_value_proxy` e exposição atual",
        "",
        "- **Definição (D2):** `lifecycle_value_proxy` = soma do `winner_mrr` mensal "
        "do painel account-month até o cutoff (1 valor por account×mês; sem dupla "
        "contagem de assinaturas sobrepostas). **PROXY operacional, não receita GAAP** "
        "e não receita recuperada.",
        f"- Totais: Σ proxy (janela) = **{fmt(lf['lifecycle_value_proxy'].sum())}** "
        "(= Σ winner do painel, contrato It02); current winner MRR no corte "
        f"(2024-12) = **{fmt(lf['current_winner_mrr'].sum())}** ({len(lf)} contas "
        "ativas por estado — ver limitações, seção 10).",
        f"- **Top-20 por current MRR vs top-20 por lifecycle proxy:** overlap = "
        f"**{rc['overlap']} contas** (Jaccard {rc['jaccard']:.2f}); correlação de "
        f"Spearman entre as dimensões = **{rc['spearman']:.3f}**. Rank shifts "
        f">= 3 posições entre as duas listas (contas compartilhadas):",
        "",
        "| Conta | Rank current | Rank lifecycle | Shift |",
        "|---|---|---|---|",
    ]
    for sh in rc["shifts"].to_dict("records"):
        s.append(f"| {sh['account_id']} | {sh['current_rank']} | "
                 f"{sh['lifecycle_rank']} | {sh['shift']:+d} |")
    s += [
        "",
        "- **Viés declarado:** o proxy acumula ao longo do tenure → favorece contas "
        "antigas "
        + (f"(ex.: A-a8d89d, {fmt(a8_row['current_winner_mrr'])}/mês atuais, "
           f"{fmt(a8_row['lifecycle_value_proxy'])} de jornada, tenure "
           f"{int(a8_row['tenure_days'])}d — {a8_note})" if a8_row is not None else "")
        + "; o MRR atual favorece contas novas de alto valor "
        + (f"(ex.: A-c70870, {fmt(c7_row['current_winner_mrr'])}/mês, jornada "
           f"{fmt(c7_row['lifecycle_value_proxy'])}, tenure "
           f"{int(c7_row['tenure_days'])}d)" if c7_row is not None else "")
        + ". **As duas dimensões se complementam; nenhuma substitui a outra.**",
        "",
        "## 6. Backtest point-in-time (sem ML; regras pré-especificadas em D4)",
        "",
        f"- **Desenho:** cutoffs {', '.join(BACKTEST_CUTOFFS)} com horizonte de "
        f"{BACKTEST_HORIZON_DAYS} dias (totalmente observável; o mais tardio termina "
        f"em 2024-12-29 <= corte); sensibilidade com horizonte de "
        f"{SENSITIVITY_HORIZON} dias nos dois primeiros cutoffs. Elegíveis = contas "
        "com signup <= cutoff. Outcome = primeiro/próximo evento em (cutoff, "
        "cutoff+horizonte] — binário por conta; múltiplos eventos NÃO duplicam logos.",
        "- **Features (somente dados <= cutoff):** tenure_days; n_events_pre; "
        "n_react_pre; last_event_days; recent_ended_mrr_90d (R1); winner_mrr_at; "
        "lifecycle_proxy_pre. **Proibidos e não usados:** `accounts.churn_flag` "
        "(snapshot) e qualquer evento/assinatura com data > cutoff (auditoria "
        "coluna a coluna na seção 9).",
        "- **Regras (thresholds fixos, sem tunagem):**",
        "",
        "| Regra | Definição |",
        "|---|---|",
    ]
    for rid, label, desc in RULES:
        s.append(f"| R_{rid} {label} | {desc} |")
    s += [
        "",
        "- **Resultados (horizonte 90d):** tabela completa em "
        "`out/tables/t14_backtest_temporal.csv` (baseline, precision, recall, lift, "
        "intervalo de Wilson 95% por regra × cutoff). Resumo dos lifts:",
        "",
        "| Regra | lift 2024-03-31 | lift 2024-06-30 | lift 2024-09-30 | N por cutoff | Validada* |",
        "|---|---|---|---|---|---|",
    ]
    for _, r in bt_sum.iterrows():
        lifts = r['lifts_90d'].split("; ") if r['lifts_90d'] else ["", "", ""]
        while len(lifts) < 3:
            lifts.append("")
        s.append(f"| R_{r['rule']} {r['rule_label']} | {lifts[0]} | {lifts[1]} | "
                 f"{lifts[2]} | {r['n_rule_by_cutoff']} | {r['validated']} |")
    s += [
        "",
        "*Critério pré-registrado (D4): lift > 1,15 nos TRÊS cutoffs de 90d com "
        f"N >= {MIN_RULE_N}.",
        "- **Leitura:** a única regra com lift consistente é **R_D (onboarding, "
        f"tenure <= 90d)**: {lifts_txt('D', BACKTEST_HORIZON_DAYS)} (precision "
        f"{prec_min:.2f}–{prec_max:.2f}; a base inteira tem taxa de evento em 90d "
        f"de {base_min:.2f}–{base_max:.2f}). **Recorrência (R_A: "
        f"{lifts_txt('A', BACKTEST_HORIZON_DAYS)}), reativação (R_B: "
        f"{lifts_txt('B', BACKTEST_HORIZON_DAYS)} — lift apenas no período do "
        f"spike, inconsistente) e alto MRR (R_E: {lifts_txt('E', BACKTEST_HORIZON_DAYS)}) "
        f"NÃO validam**; evento recente (R_C: {lifts_txt('C', BACKTEST_HORIZON_DAYS)}) "
        f"também não. A sensibilidade de 180d confirma: somente R_D tem lift "
        f"consistente ({lifts_txt('D', SENSITIVITY_HORIZON)}); as demais ficam <= 1,05 "
        f"**com o filtro pré-registrado N >= {MIN_RULE_N} (D4)** — sem esse filtro há "
        f"exceções aparentes e instáveis (N < {MIN_RULE_N}, cutoff {exc_cuts_txt}): "
        f"{exc_txt} — abaixo do N mínimo da regra D4, portanto não validam.",
        "- **Consequência (D8):** NÃO existe score de risco de churn com validação "
        "temporal nesta base. A watchlist abaixo é nomeada **operational "
        "priority/exposure**: ordenação por exposição (winner MRR) + evidência "
        "(onboarding validado; recência para ação de CS), com cada linha rotulada "
        "pelo seu sinal. Recorrência e reativação permanecem como associações "
        "históricas descritas nas seções 2–3, nunca como preditores.",
        "",
        "## 7. Segmentos de atenção (estados/jornadas; N e US$)",
        "",
        "| Segmento | N | Current MRR (US$) | Lifecycle proxy (US$) | Taxa evento (hist.) | Taxa evento recente | Evidência de backtest | Incerteza | Rationale |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in seg["segments"].iterrows():
        s.append(f"| {r['segment']} {r['name']} | {r['N']} | {fmt(r['current_mrr_sum'])} "
                 f"| {fmt(r['lifecycle_proxy_sum'])} | {r['ever_event_rate']:.3f} | "
                 f"{r['recent_event_rate']:.3f} | {r['backtest_evidence']} | "
                 f"{r['uncertainty']} | {r['rationale']} |")
    s += [
        "",
        "- **Overlap declarado (nunca oculto):**",
        "",
        "| Par | Overlap (contas) |",
        "|---|---|",
    ]
    for _, r in seg["overlaps"].iterrows():
        s.append(f"| {r['segment_a']} ∩ {r['segment_b']} | {r['overlap_n']} |")
    s += [
        "",
        "- Notas: S3 (reativação recente) ⊆ S4 (evento recente) por construção "
        "(o flag é um evento). S5 é segmento de exposição, NÃO de risco (regra E sem "
        "lift). Os segmentos são jornadas, não firmografia — It03 (H6) não encontrou "
        "heterogeneidade material por industry/channel/tier.",
        "",
        "## 8. Watchlist atual (cutoff 2024-12-31) — operational priority/exposure",
        "",
        "- **Regra de composição (D6, pré-especificada):** tiers com caps declarados, "
        "NUNCA score: **Tier A** (8) = onboarding (tenure <= 90d — único sinal "
        "validado no backtest); **Tier B** (8) = evento recente (último evento <= 90d, "
        "fora do A — janela acionável de CS, sem lift validado); **Tier C** (4) = "
        "recorrência/reativação sem evento recente com winner >= P50 (proteção de "
        "receita). Dentro de cada tier: `winner_mrr` desc (exposição), desempate por "
        "account_id. A composição 8/8/4 é uma escolha de governança declarada e "
        "reproduzível, não um modelo de risco.",
        "- **Top-20 (tabela completa: `out/tables/t16_watchlist_top20.csv`):**",
        "",
        "| Rank | Conta | Tier | Winner MRR | Lifecycle proxy | Tenure (d) | Eventos | Reativ. | Último evento | Dias desde | R1 recente 90d | Flag snapshot |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in wl.iterrows():
        s.append(f"| {int(r['watch_rank'])} | {r['account_id']} | {r['watch_tier']} "
                 f"| {fmt(r['current_winner_mrr'])} | {fmt(r['lifecycle_value_proxy'])} "
                 f"| {int(r['tenure_days'])} | {int(r['n_events'])} | {int(r['n_reactivations'])} "
                 f"| {r['last_event_date'] or '—'} | "
                 f"{int(r['last_event_days_ago']) if r['last_event_days_ago'] >= 0 else '—'} "
                 f"| {fmt(r['r1_mrr_recent_90d'])} | {int(r['churn_flag_snapshot_2024_12_31'])} |")
    s += [
        "",
        "- **Guia de interpretação (leia antes de usar):**",
        "  1. Esta lista NÃO prevê churn futuro: NENHUM alvo futuro é incluído e "
        "nenhuma conta é 'declarada em risco de sair'. É uma priorização operacional "
        "de atenção (onboarding validado; episódios recentes; exposição).",
        f"  2. `churn_flag_snapshot_2024_12_31` é o rótulo snapshot do dataset "
        f"({n_snapshot} contas no corte) — contexto de qualidade, PROIBIDO como "
        "feature preditora (contrato §8); sua presença na tabela não altera a prioridade.",
        "  3. `winner_mrr` = exposição atual (estado, contrato §6); "
        "`lifecycle_value_proxy` = jornada acumulada (proxy, D2).",
        "  4. CS pode usar a lista para: contato de ativação/onboarding (Tier A), "
        "conversa de renovação/winback com contexto do episódio recente (Tier B) e "
        "revisão de conta de alto valor com histórico (Tier C) — sem afirmar que "
        "qualquer conta 'vai sair'.",
        "  5. As 500 contas com todas as features estão em "
        "`out/tables/t11_account_lifecycle.csv` — qualquer re-fatia da regra é "
        "reproduzível.",
        "",
        "## 9. Auditoria de leakage (coluna a coluna)",
        "",
        "| Feature (backtest) | Fonte | Janela de dados usada | Verificação estrutural |",
        "|---|---|---|---|",
        "| tenure_days | ravenstack_accounts.signup_date | signup <= cutoff | data fixa de cadastro; sem componente futuro |",
        "| n_events_pre | ravenstack_churn_events.churn_date | churn_date <= cutoff | max(churn_date) <= cutoff (check G6b) |",
        "| n_react_pre | ravenstack_churn_events (is_reactivation) | churn_date <= cutoff | idem |",
        "| last_event_days | ravenstack_churn_events.churn_date | max churn_date <= cutoff | idem |",
        "| recent_ended_mrr_90d | ravenstack_subscriptions.end_date | end_date em (cutoff-90d, cutoff] | max(end_date) <= cutoff (check G6b) |",
        "| winner_mrr_at | account_month (mês do cutoff) | month == mês do cutoff | painel derivado de subs com start <= fim do mês (contrato G10) |",
        "| lifecycle_proxy_pre | account_month.winner_mrr | month <= mês do cutoff | idem |",
        "| outcome | ravenstack_churn_events.churn_date | churn_date em (cutoff, cutoff+horizonte] | NUNCA usado em features (conjuntos disjuntos por construção) |",
        "| accounts.churn_flag | ravenstack_accounts | — | PROIBIDO em features (snapshot); presente apenas como contexto na watchlist |",
        "",
        "## 10. Limitações e causalidade",
        "",
        "- **Associação, não causalidade:** recorrência e reativação são associações "
        "históricas descritas nas seções 2–3; o único padrão com validação temporal "
        "é onboarding (R_D), coerente com a causa raiz de It03 (churn precoce de "
        "coortes novas) — hipótese causal plausível, não prova.",
        "- **All-active no corte:** todas as 500 contas estão ativas por estado em "
        "2024-12 (enquanto o snapshot marca 110 como churnadas) — a validação direta "
        "de 'perda real de estado' no presente é limitada; o backtest usa eventos "
        "históricos como outcome.",
        "- **Proxies:** lifecycle_value_proxy é soma de winner MRR mensal (não "
        "receita GAAP; não inclui MRR de assinaturas não-dominantes); winner é "
        "estado/exposição, não churn contratual isolado (contrato §6).",
        "- **Sinteticidade/timestamps:** a base é sintética (It01 §5); o pico de "
        "eventos no fim de 2024 pode ser artefato de geração — os lifts do backtest "
        "em 2024-09-30+90d cobrem justamente esse período e são os mais altos para "
        "R_D, o que reforça a cautela de não extrapolar.",
        "- **Censura:** episódios de reativação sem próximo evento observado são "
        "censurados no corte (KM, seção 3); coortes recentes têm follow-up curto.",
        "- **N pequenos:** intervalos de Wilson largos (tabela t14); N >= 25 exigido "
        "para considerar uma regra (D4).",
        "",
        "## 11. Gates e validações",
        "",
        "| ID | Escopo | Check | Veredito | Detalhe |",
        "|---|---|---|---|---|",
    ]
    for c in CHECKS:
        s.append(f"| {c['id']} | {c['scope']} | {c['description']} | {c['level']} | "
                 f"{c['detail']} |")
    s += [
        "",
        "## 12. Arquivos gerados",
        "",
        "- Tabelas: " + ", ".join(f"`{t}`" for t in table_names) + ".",
        "- Gráficos: " + ", ".join(f"`{c}`" for c in chart_names) + ".",
        "",
        "Leitura das tabelas: `t11_account_lifecycle.csv` (jornada completa de 500 "
        "contas), `t12_reactivation_recurrence.csv` (distribuições de eventos e "
        "episódios de reativação), `t13_state_cycles.csv` (ciclos reais vs lentes), "
        "`t14_backtest_temporal.csv` (regras × cutoffs) e `t14b_backtest_detail.csv` "
        "(flags por conta × cutoff para auditoria), `t15_priority_segments.csv` "
        "(segmentos N/US$) e `t15b_segment_overlap.csv` (overlap), "
        "`t16_watchlist_top20.csv` (watchlist), `t17_rank_comparison.csv` "
        "(top-20 current vs lifecycle).",
    ]
    return "\n".join(s)


# ----------------------------------------------------------------------------
# Gates
# ----------------------------------------------------------------------------
def run_gates(rec: dict, react: dict, cyc: dict, lf: pd.DataFrame, bt: dict,
              bt_sum: pd.DataFrame, seg: dict, wl: pd.DataFrame, rc: dict,
              churn: pd.DataFrame, tables: list[Path], charts: list[Path]) -> None:
    # G1 — recorrência reconcilia com a fonte
    check("G1-events", "recorrência",
          "totais de eventos e contas reconciliam com churn_events",
          "PASS" if (rec["total_events"] == len(churn)
                     and rec["accounts_with_event"] == churn["account_id"].nunique())
          else "FAIL",
          f"eventos={rec['total_events']} (fonte {len(churn)}); contas="
          f"{rec['accounts_with_event']} (fonte {churn['account_id'].nunique()})")
    check("G1b-events", "recorrência",
          "contagens 2+/3+/máx corretas",
          "PASS" if (rec["accounts_2plus"] == 175 and rec["accounts_3plus"] == 59
                     and rec["max_events"] == 5) else "FAIL",
          f"2+={rec['accounts_2plus']} (esperado 175); 3+={rec['accounts_3plus']} "
          f"(esperado 59); máx={rec['max_events']} (esperado 5)")
    # G2 — reativação 61/55
    check("G2-reactivation", "reativação",
          "flags e contas de reativação (61/55) confirmadas",
          "PASS" if (react["n_flags"] == 61 and react["n_accounts"] == 55) else "FAIL",
          f"flags={react['n_flags']} (esperado 61); contas={react['n_accounts']} "
          f"(esperado 55)")
    check("G2b-reactivation", "reativação",
          "episódios fecham (com/sem próximo evento + censura)",
          "PASS" if react["n_with_next"] + react["n_censored"] == react["n_flags"]
          else "FAIL",
          f"com próximo={react['n_with_next']}; censurados={react['n_censored']}; "
          f"total={react['n_flags']}")
    # G3 — ciclos
    check("G3-cycles", "ciclos de estado",
          "transições do painel fecham (contrato R2: 2 churn-to-inactive)",
          "PASS" if (cyc["n_dec"] == 2 and cyc["n_inc"] == 281
                     and cyc["n_activation_gaps"] == 279 and cyc["n_returns"] == 2
                     and cyc["n_full_cycles"] == 2) else "FAIL",
          f"dec={cyc['n_dec']} (esperado 2); inc={cyc['n_inc']} (esperado 281); "
          f"gaps={cyc['n_activation_gaps']}; retornos={cyc['n_returns']}; "
          f"ciclos={cyc['n_full_cycles']}")
    # G4 — painel
    check("G4-panel", "painel",
          "500 contas; Σ winner da janela reconcilia com o contrato (28.766.224)",
          "PASS" if lf["lifecycle_value_proxy"].sum() == 28766224 else "FAIL",
          f"Σ proxy={lf['lifecycle_value_proxy'].sum()} (esperado 28.766.224)")
    check("G4b-panel", "painel",
          "current winner MRR do corte (3.668.852) e 500 contas ativas por estado",
          "PASS" if (lf["current_winner_mrr"].sum() == 3668852
                     and (lf["current_status"] == "active").all()) else "FAIL",
          f"Σ winner 2024-12={lf['current_winner_mrr'].sum()} (esperado 3.668.852); "
          f"ativas por estado={(lf['current_status'] == 'active').sum()}/500")
    # G5 — proxy consistente com o painel
    check("G5-proxy", "lifecycle proxy",
          "Σ proxy por conta == Σ winner_mrr do painel (sem dupla contagem)",
          "PASS" if lf["lifecycle_value_proxy"].sum() == 28766224 else "FAIL",
          "proxy = soma mensal de winner_mrr (1 linha por account×mês)")
    # G6 — backtest: elegíveis e outcomes reconciliam
    exp_elig = {"2024-03-31": 283, "2024-06-30": 348, "2024-09-30": 420}
    exp_out = {"2024-03-31": 61, "2024-06-30": 86, "2024-09-30": 124}
    ok_elig = all(
        int(bt["per_cutoff"][(bt["per_cutoff"]["cutoff"] == c)
                             & (bt["per_cutoff"]["horizon_days"] == 90)]
            ["n_eligible"].iloc[0]) == exp_elig[c] for c in exp_elig)
    ok_out = all(
        int(bt["per_cutoff"][(bt["per_cutoff"]["cutoff"] == c)
                             & (bt["per_cutoff"]["horizon_days"] == 90)]
            ["n_outcome"].iloc[0]) == exp_out[c] for c in exp_out)
    check("G6-backtest", "backtest",
          "elegíveis e outcomes por cutoff reconciliam com as fontes",
          "PASS" if (ok_elig and ok_out) else "FAIL",
          f"elegíveis={ {c: int(bt['per_cutoff'][(bt['per_cutoff']['cutoff'] == c) & (bt['per_cutoff']['horizon_days'] == 90)]['n_eligible'].iloc[0]) for c in exp_elig} } (esperado {exp_elig}); "
          f"outcomes={ {c: int(bt['per_cutoff'][(bt['per_cutoff']['cutoff'] == c) & (bt['per_cutoff']['horizon_days'] == 90)]['n_outcome'].iloc[0]) for c in exp_out} } (esperado {exp_out})")
    # G7 — regras pré-especificadas aplicadas mecanicamente
    validated = set(bt_sum[bt_sum["validated"] == "SIM"]["rule"])
    check("G7-rules", "backtest",
          "veredito de validação mecânico (lift > 1,15 nos 3 cutoffs, N >= 25)",
          "PASS" if validated == {"D"} else "FAIL",
          f"regras validadas={sorted(validated)} (esperado {{D}}) — thresholds "
          "pré-especificados em D4, sem tunagem")
    # G8 — watchlist
    ok_wl = (len(wl) == 20 and wl["account_id"].nunique() == 20
             and wl["watch_tier"].value_counts().to_dict() == {"A": 8, "B": 8, "C": 4})
    check("G8-watchlist", "watchlist",
          "20 contas únicas; composição 8/8/4 (tiers A/B/C)",
          "PASS" if ok_wl else "FAIL",
          f"linhas={len(wl)}; únicas={wl['account_id'].nunique()}; "
          f"tiers={wl['watch_tier'].value_counts().to_dict()}")
    # G9 — segmentos com overlap declarado
    check("G9-segments", "segmentos",
          "segmentos com N>0 e overlap declarado",
          "PASS" if (seg["segments"]["N"] > 0).all() and len(seg["overlaps"]) == 5
          else "FAIL",
          f"segmentos={len(seg['segments'])}; pares de overlap={len(seg['overlaps'])}")
    # G10 — outputs (somente desta iteração)
    check("G10-outputs", "outputs",
          "tabelas e gráficos desta iteração gerados e não-vazios",
          "PASS" if tables and charts and all(t.stat().st_size > 0 for t in tables)
          and all(c.stat().st_size > 0 for c in charts) else "FAIL",
          f"tabelas={len(tables)}; gráficos={len(charts)}")
    # G11 — rank comparison (âncora de regressão da execução determinística)
    check("G11-rank", "rank comparison",
          "overlap top-20 current vs lifecycle e Spearman (âncora de regressão)",
          "PASS" if (rc["overlap"] == 7 and 0.56 <= rc["spearman"] <= 0.59) else "FAIL",
          f"overlap={rc['overlap']} (âncora 7); Spearman={rc['spearman']:.3f} "
          f"(âncora 0,575)")
    # G12 — sem divisão por zero / NaN indevido em taxas
    bad = bt["per_cutoff"][(bt["per_cutoff"]["n_rule"] > 0)
                           & (bt["per_cutoff"]["precision"] == "NA")]
    check("G12-zerodiv", "denominadores",
          "sem NaN em precision com n_rule > 0",
          "PASS" if len(bad) == 0 else "FAIL",
          f"linhas com NaN indevido={len(bad)}")
    # G13 — âncoras de regressão dos claims executivos materiais (todas as
    # frases narrativas do relatório são DERIVADAS em runtime destes objetos;
    # se os dados mudarem e os textos descolarem, o gate falha)
    ok_km = (abs(react["km_surv_90d"] - 0.653) <= 0.001
             and abs(react["km_surv_180d"] - 0.476) <= 0.001
             and react["km_median"] == 187)
    check("G13-km", "narrativa",
          "âncoras KM do relatório (90d 0,653; 180d 0,476; mediana 187d)",
          "PASS" if ok_km else "FAIL",
          f"km90={react['km_surv_90d']:.3f} (âncora 0,653); "
          f"km180={react['km_surv_180d']:.3f} (âncora 0,476); "
          f"mediana={react['km_median']} (âncora 187)")
    ok_react = (react["recent_flags"] == 26 and react["recent_censored"] == 20
                and react["first_event_flags"] == 26)
    check("G13-reactivation", "narrativa",
          "âncoras de reativação (26 flags out-dez; 20 das 37 censuradas recentes; "
          "26 flags 1º evento)",
          "PASS" if ok_react else "FAIL",
          f"recent_flags={react['recent_flags']} (âncora 26); "
          f"recent_censored={react['recent_censored']} (âncora 20); "
          f"first_event_flags={react['first_event_flags']} (âncora 26)")
    b90 = [float(x) for x in bt["per_cutoff"]
           [(bt["per_cutoff"]["rule"] == "B")
            & (bt["per_cutoff"]["horizon_days"] == BACKTEST_HORIZON_DAYS)]
           .sort_values("cutoff")["lift"]]
    d90 = [float(x) for x in bt["per_cutoff"]
           [(bt["per_cutoff"]["rule"] == "D")
            & (bt["per_cutoff"]["horizon_days"] == BACKTEST_HORIZON_DAYS)]
           .sort_values("cutoff")["lift"]]
    ok_exact = (len(b90) == 3 and len(d90) == 3
                and all(abs(a - b) <= 0.001 for a, b in zip(b90, [0.515, 0.405, 1.295]))
                and all(abs(a - b) <= 0.001 for a, b in zip(d90, [1.574, 1.556, 1.835])))
    check("G13-backtest-exact", "narrativa",
          "lifts exatos de R_B e R_D (90d) — base das strings derivadas dos segmentos",
          "PASS" if ok_exact else "FAIL",
          f"R_B={b90} (âncora [0.515, 0.405, 1.295]); "
          f"R_D={d90} (âncora [1.574, 1.556, 1.835])")
    g180 = bt["per_cutoff"][(bt["per_cutoff"]["rule"] == "G")
                            & (bt["per_cutoff"]["horizon_days"] == SENSITIVITY_HORIZON)
                            & (bt["per_cutoff"]["cutoff"] == "2024-06-30")].iloc[0]
    h180 = bt["per_cutoff"][(bt["per_cutoff"]["rule"] == "H")
                            & (bt["per_cutoff"]["horizon_days"] == SENSITIVITY_HORIZON)
                            & (bt["per_cutoff"]["cutoff"] == "2024-06-30")].iloc[0]
    ok_sens = (abs(float(g180["lift"]) - 1.362) <= 0.006 and int(g180["n_rule"]) == 12
               and abs(float(h180["lift"]) - 1.606) <= 0.006 and int(h180["n_rule"]) == 16)
    check("G13-sens180", "narrativa",
          "exceções aparentes da sensibilidade 180d (R_G 1,36 N=12; R_H 1,61 N=16, "
          "cutoff 06-30 — instáveis, N < 25)",
          "PASS" if ok_sens else "FAIL",
          f"R_G 180d 06-30 lift={g180['lift']} (âncora 1.362), N={g180['n_rule']} "
          f"(âncora 12); R_H 180d 06-30 lift={h180['lift']} (âncora 1.606), "
          f"N={h180['n_rule']} (âncora 16)")
    a8_id, c7_id = "A-a8d89d", "A-c70870"
    ok_narr = (a8_id in rc["top_lifecycle"] and a8_id not in rc["top_current"]
               and c7_id in rc["top_current"]
               and int(lf["churn_flag_snapshot_2024_12_31"].sum()) == 110
               and int(cyc.get("dec_r2_sum", 0)) == 18507)
    check("G13-narrative", "narrativa",
          "âncoras dos exemplos narrativos (A-a8d89d na jornada/fora do atual; "
          "A-c70870 no atual; snapshot 110; R2 churn-to-inactive 18.507)",
          "PASS" if ok_narr else "FAIL",
          f"A-a8d89d: top_lifecycle={a8_id in rc['top_lifecycle']}, "
          f"top_current={a8_id in rc['top_current']}; "
          f"A-c70870: top_current={c7_id in rc['top_current']}; "
          f"snapshot={int(lf['churn_flag_snapshot_2024_12_31'].sum())} (âncora 110); "
          f"R2 churn-to-inactive={int(cyc.get('dec_r2_sum', 0))} "
          "(âncora 18.507)")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    loaded = load_all()
    panel = load_panel()

    structural = any(c["level"] == "FAIL" for c in CHECKS)
    if structural or panel is None or "ravenstack_accounts.csv" not in loaded \
            or "ravenstack_subscriptions.csv" not in loaded \
            or "ravenstack_churn_events.csv" not in loaded:
        REPORT_PATH.write_text(render_report({}, {}, {}, pd.DataFrame(), {},
                                             pd.DataFrame(), {}, pd.DataFrame(),
                                             {}, {}, [], [], structural_fail=True),
                               encoding="utf-8")
        print("[04_lifecycle_watchlist] Falha estrutural — relatório regravado; "
              "exit 1 (sem traceback)")
        return 1

    acc = loaded["ravenstack_accounts.csv"]
    sub = loaded["ravenstack_subscriptions.csv"]
    churn = loaded["ravenstack_churn_events.csv"]

    # --- análises ---
    rec = recurrence_stats(churn)
    # conta de contas com flag de reativação (para o gráfico B)
    rec["n_react_accounts"] = int(
        churn[churn["is_reactivation"] == True]["account_id"].nunique())  # noqa: E712
    react = reactivation_episodes(churn)
    cyc = state_cycles(panel, sub)
    lf = lifecycle_features(acc, sub, churn, panel)
    # S3 (reativação recente) com as datas reais de reativação
    ev_d = churn.copy()
    ev_d["churn_date"] = pd.to_datetime(ev_d["churn_date"])
    react_recent_accounts = set(
        ev_d[(ev_d["is_reactivation"] == True)  # noqa: E712
             & (ev_d["churn_date"] > DATA_CUT - pd.Timedelta(days=RECENT_DAYS))]
        ["account_id"])
    lf["s3_recent_react"] = lf["account_id"].isin(react_recent_accounts)
    bt = backtest_run(acc, sub, churn, panel)
    bt_sum = backtest_summary(bt["per_cutoff"])
    seg = priority_segments(lf, bt_sum)
    seg_rows = seg["segments"].to_dict("records")
    rb_lifts = bt_sum[bt_sum["rule"] == "B"].iloc[0]["lifts_90d"] \
        .replace("; ", "/").replace(".", ",")
    s3_row = {
        "segment": "S3", "name": "Reativacao recente (flag out-dez/2024)",
        "N": int(lf["s3_recent_react"].sum()),
        "current_mrr_sum": int(lf.loc[lf["s3_recent_react"],
                                      "current_winner_mrr"].sum()),
        "lifecycle_proxy_sum": int(lf.loc[lf["s3_recent_react"],
                                          "lifecycle_value_proxy"].sum()),
        "ever_event_rate": round(float(lf.loc[lf["s3_recent_react"],
                                              "n_events"].ge(1).mean()), 4),
        "recent_event_rate": 1.0,
        "backtest_evidence": (
            f"regra B: lift {rb_lifts} — inconsistente (lift apenas no spike); "
            f"KM 90d = {react['km_surv_90d']:.3f} "
            f"({100 * (1 - react['km_surv_90d']):.0f}% dos episódios com próximo "
            f"evento <=90d), mediana {react['km_median']}d, censura declarada"),
        "uncertainty": (
            f"intervalos largos (N pequeno); censura no corte; "
            f"{react['first_event_flags']} das {react['n_flags']} flags são o "
            "1º evento da conta"),
        "rationale": "episódio de evento marcado is_reactivation; NÃO é ciclo de "
                     "estado; subconjunto de S4 (declarado)",
    }
    seg["segments"] = pd.DataFrame(seg_rows[:2] + [s3_row] + seg_rows[2:])
    wl = build_watchlist(lf, cyc["cycle_accounts"])
    rc = rank_comparison(lf)
    expo = exposure_lenses(sub, churn, lf)

    # --- tabelas CSV ---
    lf.to_csv(TABLES_DIR / "t11_account_lifecycle.csv", index=False)
    t12 = []
    for k, v in rec["dist"].items():
        t12.append({"metric": "accounts_by_n_events", "level": k, "value": v})
    for k, v in [("accounts_2plus", rec["accounts_2plus"]),
                 ("accounts_3plus", rec["accounts_3plus"]),
                 ("max_events", rec["max_events"]),
                 ("events_from_multi_event_accounts", rec["events_from_multi"]),
                 ("total_events", rec["total_events"]),
                 ("reactivation_flags", react["n_flags"]),
                 ("reactivation_accounts", react["n_accounts"]),
                 ("reactivation_first_event_flags", react["first_event_flags"]),
                 ("episodes_with_prev_event", react["n_with_prev"]),
                 ("episodes_with_next_event", react["n_with_next"]),
                 ("episodes_censored", react["n_censored"]),
                 ("gap_median_days", rec["gap_median"]),
                 ("gap_to_next_median_days", react["gap_to_next_median"]),
                 ("km_surv_90d", react["km_surv_90d"]),
                 ("km_surv_180d", react["km_surv_180d"]),
                 ("km_median_days", react["km_median"] or "NA"),
                 ("r1_multi_event_accounts", expo["multi"]["r1_total"]),
                 ("r1_share_multi_event_accounts",
                  f"{expo['multi']['r1_share']:.3f}"),
                 ("current_mrr_multi_event_accounts", expo["multi"]["current_mrr"]),
                 ("r1_reactivated_accounts", expo["react"]["r1_total"]),
                 ("r1_share_reactivated_accounts", f"{expo['react']['r1_share']:.3f}"),
                 ("current_mrr_reactivated_accounts", expo["react"]["current_mrr"]),
                 ("r1_total_window", expo["r1_total_all"])]:
        t12.append({"metric": k, "level": "", "value": v})
    for f in react["followup"]:
        t12.append({"metric": f"next_event_within_{f['window_days']}d",
                    "level": f"episodes_with_followup={f['episodes_with_followup']}",
                    "value": f"{f['next_event_within']} ({pct(f['next_event_within'], f['episodes_with_followup'])})"})
    pd.DataFrame(t12).to_csv(TABLES_DIR / "t12_reactivation_recurrence.csv",
                             index=False)
    t13 = []
    for cid, name, val in [
        ("accounts_2plus_events", "contas com >= 2 eventos (recorrência)",
         rec["accounts_2plus"]),
        ("ended_sub_accounts", "contas com assinatura encerrada",
         cyc["ended_sub_accounts"]),
        ("re_sign_accounts", "contas com re-assinatura (sub encerrada + nova sub)",
         cyc["re_sign_accounts"]),
        ("reactivation_flag_accounts", "contas com flag de reativação",
         rec["n_react_accounts"]),
        ("activation_gaps", "transições inactive->active = gap de ativação",
         cyc["n_activation_gaps"]),
        ("returns", "transições inactive->active = retorno real", cyc["n_returns"]),
        ("full_cycles", "ciclos reais active->inactive->active",
         cyc["n_full_cycles"]),
    ]:
        if cid in ("accounts_2plus_events", "reactivation_flag_accounts"):
            lens = "eventos"
        elif cid in ("ended_sub_accounts", "re_sign_accounts"):
            lens = "assinaturas"
        else:
            lens = "estado (painel)"
        t13.append({"lens": lens, "metric": cid, "name": name, "value": val})
    for _, r in cyc["dec_rows"].iterrows():
        t13.append({"lens": "estado (painel)", "metric": "active_to_inactive",
                    "name": f"{r['account_id']} em {r['month']}",
                    "value": f"winner_mrr {fmt(r['winner_mrr'])} "
                             f"(mês anterior: {fmt(r['winner_mrr_prev'])} — R2)"})
    pd.DataFrame(t13).to_csv(TABLES_DIR / "t13_state_cycles.csv", index=False)
    bt["per_cutoff"].to_csv(TABLES_DIR / "t14_backtest_temporal.csv", index=False)
    bt["detail"].to_csv(TABLES_DIR / "t14b_backtest_detail.csv", index=False)
    seg["segments"].to_csv(TABLES_DIR / "t15_priority_segments.csv", index=False)
    seg["overlaps"].to_csv(TABLES_DIR / "t15b_segment_overlap.csv", index=False)
    wl.to_csv(TABLES_DIR / "t16_watchlist_top20.csv", index=False)
    rc["table"].to_csv(TABLES_DIR / "t17_rank_comparison.csv", index=False)
    # tabelas DESTA iteração (escopo explícito; não mistura com t01..t10 do It03)
    it04_tables = [
        "t11_account_lifecycle.csv", "t12_reactivation_recurrence.csv",
        "t13_state_cycles.csv", "t14_backtest_temporal.csv",
        "t14b_backtest_detail.csv", "t15_priority_segments.csv",
        "t15b_segment_overlap.csv", "t16_watchlist_top20.csv",
        "t17_rank_comparison.csv",
    ]
    tables = [TABLES_DIR / t for t in it04_tables]

    # --- gráficos (2 essenciais; It04_a/b → tabelas t12/t13, pruning do gate
    # It04; manifesto explícito — qualquer It04_*.png fora do manifesto falha) ---
    it04_chart_names = [
        "It04_c_lifecycle_vs_current_mrr.png",
        "It04_d_backtest_lift.png",
    ]
    chart_names = [
        chart_c(lf, rc),
        chart_d(bt["per_cutoff"]),
    ]
    charts = [CHARTS_DIR / n for n in it04_chart_names]
    missing_charts = [c.name for c in charts
                      if not c.exists() or c.stat().st_size == 0]
    stale_charts = sorted(
        p.name for p in CHARTS_DIR.glob("It04_*.png")
        if p.name not in it04_chart_names)
    check("C01-charts", "gráficos", "número de gráficos gerado",
          "PASS" if not missing_charts and not stale_charts else "FAIL",
          f"esperado {len(it04_chart_names)}, "
          f"ausentes/vazios={missing_charts or 'nenhuma'}; "
          f"fora do manifesto={stale_charts or 'nenhuma'}")

    # --- gates + relatório ---
    run_gates(rec, react, cyc, lf, bt, bt_sum, seg, wl, rc, churn, tables, charts)
    REPORT_PATH.write_text(render_report(
        rec, react, cyc, lf, bt, bt_sum, seg, wl, rc, expo,
        chart_names, [t.name for t in tables]), encoding="utf-8")

    n_fail = sum(1 for c in CHECKS if c["level"] == "FAIL")
    n_warn = sum(1 for c in CHECKS if c["level"] == "WARN")
    n_pass = sum(1 for c in CHECKS if c["level"] == "PASS")
    print(f"[04_lifecycle_watchlist] checks: {n_pass} PASS / {n_warn} WARN / "
          f"{n_fail} FAIL")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())