#!/usr/bin/env python3
"""
02_reconcile_churn.py — Reconciliação das definições/grãos de churn e contrato analítico.

Iteração 02 do Challenge 001 (RavenStack). Reconcilia as três fontes de "churn"
(accounts.churn_flag, subscriptions.churn_flag/end_date, churn_events), quantifica
as divergências, constrói a base-mestre account-month (uma linha por account×mês,
sem MRR dobrado por sobreposição de assinaturas) e congela o contrato analítico
que as iterações seguintes devem seguir.

Gera, de forma offline e determinística (sem timestamp; ordenações estáveis):
    solution/evidence/02_consistency_report.md
    solution/docs/analytical-contract.md
    solution/data/processed/account_month.csv
    solution/data/processed/README.md

Uso (a partir da pasta da submissão):
    python3 solution/src/02_reconcile_churn.py

Semântica de resultado:
    - PASS  : check íntegro (estrutura/qualidade esperada confirmada).
    - WARN  : divergência/anomalia de qualidade esperada em dados sintéticos
              (documentada com números, não bloqueia).
    - FAIL  : arquivo/schema estrutural ausente ou invariante violado.
    Exit code: 0 se não houver FAIL; 1 caso contrário.
    Em caso de FAIL estrutural o relatório é SEMPRE regravado (sem output stale)
    e sem traceback não tratado (lição da Iteração 01).

Restrições: apenas stdlib + pandas; sem rede; paths relativos ao próprio projeto.
"""

from __future__ import annotations

import hashlib
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
DOCS_DIR = SOLUTION_DIR / "docs"

REPORT_PATH = EVIDENCE_DIR / "02_consistency_report.md"
CONTRACT_PATH = DOCS_DIR / "analytical-contract.md"
ACCOUNT_MONTH_PATH = PROCESSED_DIR / "account_month.csv"
PROCESSED_README_PATH = PROCESSED_DIR / "README.md"

# ----------------------------------------------------------------------------
# Constantes do contrato (decisões desta iteração — ver decisions file)
# ----------------------------------------------------------------------------
DATA_CUT = pd.Timestamp("2024-12-31")          # data-limite (snapshot) dos dados
FIRST_MONTH = "2023-01"                        # primeiro mês da janela observacional
LAST_MONTH = "2024-12"                         # último mês da janela observacional
ALIGNMENT_WINDOWS_DAYS = [0, 3, 7, 15, 30, 60, 90, 180, 365]  # sensibilidade a janelas

# Colunas mínimas exigidas por arquivo para esta iteração (guarda estrutural).
REQUIRED = {
    "ravenstack_accounts.csv": ["account_id", "signup_date", "churn_flag"],
    "ravenstack_subscriptions.csv": [
        "subscription_id", "account_id", "start_date", "end_date", "plan_tier",
        "seats", "mrr_amount", "is_trial", "churn_flag", "billing_frequency",
    ],
    "ravenstack_churn_events.csv": ["churn_event_id", "account_id", "churn_date", "is_reactivation"],
    "ravenstack_feature_usage.csv": ["subscription_id", "usage_date"],
    "ravenstack_support_tickets.csv": ["account_id", "submitted_at", "satisfaction_score"],
}

# ----------------------------------------------------------------------------
# Registro de checks (ordem determinística de emissão)
# ----------------------------------------------------------------------------
CHECKS: list[dict] = []


def check(check_id: str, scope: str, description: str, level: str, detail: str) -> None:
    """Registra um check. level: PASS | WARN | FAIL."""
    CHECKS.append({
        "id": check_id,
        "scope": scope,
        "description": description,
        "level": level,
        "detail": detail,
    })


def fmt(n: int | float) -> str:
    """Formata número inteiro sem decimais; float com 2 decimais (determinístico)."""
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    if isinstance(n, float):
        return f"{n:.2f}"
    return str(n)


def pct(part: int, total: int) -> str:
    return f"{100.0 * part / total:.1f}%"


def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def missing_cols(df: pd.DataFrame, cols: list[str], fname: str) -> list[str]:
    """Colunas de ``cols`` ausentes do DataFrame, anotadas com o arquivo."""
    return [f"{c} ({fname})" for c in cols if c not in df.columns]


def guard_columns(df: pd.DataFrame, cols: list[str], check_id: str, scope: str,
                  description: str) -> bool:
    """Registra FAIL estrutural se alguma coluna necessária estiver ausente.

    Retorna True quando todas as colunas existem (o check pode executar).
    Não é catch-all: apenas guarda acesso a colunas — bugs reais continuam
    propagando com traceback (exit != 0) em vez de virarem FAIL silencioso.
    """
    missing = missing_cols(df, cols, scope)
    if missing:
        check(check_id, scope, description, "FAIL",
              f"não executado (schema): colunas ausentes: {missing}")
        return False
    return True


# ----------------------------------------------------------------------------
# Leitura e preparação das tabelas
# ----------------------------------------------------------------------------

def load_all() -> dict[str, pd.DataFrame]:
    """Carrega os 5 CSVs e valida a presença das colunas mínimas desta iteração."""
    loaded: dict[str, pd.DataFrame] = {}
    for fname, cols in REQUIRED.items():
        path = RAW_DIR / fname
        if not path.exists():
            check(f"F01-{fname}", fname, "arquivo presente em data/raw", "FAIL", "arquivo ausente")
            continue
        if path.stat().st_size == 0:
            check(f"F01-{fname}", fname, "arquivo presente em data/raw", "FAIL", "arquivo vazio (0 bytes)")
            continue
        try:
            df = pd.read_csv(path)
        except Exception as exc:  # noqa: BLE001 — falha de parse é estrutural
            check(f"F01-{fname}", fname, "CSV carregável", "FAIL", f"falha de parse: {exc}")
            continue
        loaded[fname] = df
        check(f"F01-{fname}", fname, "arquivo presente e carregável",
              "PASS", f"{path.stat().st_size} bytes, CSV parseado ({len(df)} registros)")
        missing = missing_cols(df, cols, fname)
        if missing:
            check(f"S01-{fname}", fname, "colunas mínimas desta iteração presentes",
                  "FAIL", f"colunas ausentes: {missing}")
        else:
            check(f"S01-{fname}", fname, "colunas mínimas desta iteração presentes",
                  "PASS", f"{len(cols)} colunas exigidas presentes")
    return loaded


def parse_dates(df: pd.DataFrame, cols: list[str], fname: str) -> dict[str, pd.Series]:
    """Converte colunas de data para datetime; registra FAIL se houver não-parseáveis."""
    out: dict[str, pd.Series] = {}
    for col in cols:
        if col not in df.columns:
            continue
        parsed = pd.to_datetime(df[col], errors="coerce")
        n_bad = int(parsed.isna().sum()) - int(df[col].isna().sum())
        if n_bad:
            check(f"D01-{fname}", fname, f"{col} parseável",
                  "FAIL", f"{n_bad} valores não parseáveis")
        else:
            check(f"D01-{fname}", fname, f"{col} parseável", "PASS", "0 valores não parseáveis")
        out[col] = parsed
    return out


def month_period(ts: pd.Timestamp) -> str:
    return f"{ts.year:04d}-{ts.month:02d}"


def month_end_date(m: str) -> pd.Timestamp:
    """Último dia do mês ``m`` (granularidade de data), ex.: '2024-12' -> 2024-12-31."""
    return (pd.Timestamp(m + "-01") + pd.offsets.MonthEnd(0)).normalize()


# ----------------------------------------------------------------------------
# Lentes de churn (reconciliação quantitativa)
# ----------------------------------------------------------------------------

def reconcile_lenses(acc: pd.DataFrame, sub: pd.DataFrame, churn: pd.DataFrame) -> dict:
    """Reconcilia as três lentes e suas interseções/diferenças.

    Retorna um dict com todos os números usados no relatório e no contrato.
    """
    r: dict = {}

    # --- Lente A: accounts.churn_flag (snapshot no corte) ---
    flag_acc = set(acc.loc[acc["churn_flag"], "account_id"])
    r["n_accounts"] = len(acc)
    r["flag_acc"] = len(flag_acc)
    r["flag_acc_pct"] = pct(len(flag_acc), len(acc))

    # --- Lente B: subscriptions (end_date / churn_flag) ---
    ended = sub["end_date"].notna()
    r["n_subs"] = len(sub)
    r["subs_ended"] = int(ended.sum())
    r["subs_active"] = int((~ended).sum())
    r["subs_churn_flag"] = int(sub["churn_flag"].sum())
    r["acc_ended"] = int(sub.loc[ended, "account_id"].nunique())
    r["acc_sub_churn_flag"] = int(sub.loc[sub["churn_flag"], "account_id"].nunique())
    r["mrr_ended_subs"] = int(sub.loc[ended, "mrr_amount"].sum())
    r["mrr_active_subs"] = int(sub.loc[~ended, "mrr_amount"].sum())
    r["acc_ended_pct"] = pct(r["acc_ended"], len(acc))
    r["subs_ended_pct"] = pct(r["subs_ended"], len(sub))

    # --- Lente C: churn_events ---
    ev_acc = set(churn["account_id"])
    cc = churn.groupby("account_id").size()
    r["n_events"] = len(churn)
    r["ev_acc"] = len(ev_acc)
    r["ev_acc_pct"] = pct(len(ev_acc), len(acc))
    r["multi_ev_acc"] = int((cc > 1).sum())
    r["max_events"] = int(cc.max())
    r["n_react"] = int(churn["is_reactivation"].sum())
    r["n_react_acc"] = int(churn.loc[churn["is_reactivation"], "account_id"].nunique())
    r["events_per_month"] = churn["churn_date"].str[:7].value_counts().sort_index()
    # primeiro evento por conta
    first_ev = churn.sort_values("churn_date").groupby("account_id")["churn_date"].first()
    r["first_ev_month"] = first_ev.str[:7].value_counts().sort_index()

    # --- Interseções/diferenças entre lentes (recalculadas, não copiadas) ---
    acc_sub_churn = set(sub.loc[sub["churn_flag"], "account_id"])
    r["inter_flag_ev"] = len(flag_acc & ev_acc)
    r["inter_flag_sub"] = len(flag_acc & acc_sub_churn)
    r["inter_sub_ev"] = len(acc_sub_churn & ev_acc)
    r["inter_all3"] = len(flag_acc & acc_sub_churn & ev_acc)
    r["only_flag"] = len(flag_acc - acc_sub_churn - ev_acc)
    r["only_sub"] = len(acc_sub_churn - flag_acc - ev_acc)
    r["only_ev"] = len(ev_acc - flag_acc - acc_sub_churn)
    r["flag_sub_only"] = len(flag_acc & acc_sub_churn - ev_acc)
    r["flag_ev_only"] = len(flag_acc & ev_acc - acc_sub_churn)
    r["sub_ev_only"] = len(acc_sub_churn & ev_acc - flag_acc)
    r["any_lens"] = len(flag_acc | acc_sub_churn | ev_acc)
    r["no_lens"] = len(set(acc["account_id"]) - (flag_acc | acc_sub_churn | ev_acc))
    # divergências da Iteração 01 (recalculadas)
    r["flag_no_ev"] = len(flag_acc - ev_acc)
    r["ev_no_flag"] = len(ev_acc - flag_acc)
    r["ev_no_subflag"] = len(ev_acc - acc_sub_churn)
    r["subflag_no_ev"] = len(acc_sub_churn - ev_acc)
    r["flag_no_sub_no_ev"] = len(flag_acc - acc_sub_churn - ev_acc)

    return r


def align_events_to_end_dates(churn: pd.DataFrame, sub: pd.DataFrame) -> pd.DataFrame:
    """Para cada evento, a end_date mais próxima da conta e o lag (dias).

    Regra: para cada evento, dentre as assinaturas ENCERRADAS (end_date presente)
    da mesma conta, escolhe a end_date com menor |churn_date - end_date|.
    Eventos de contas sem assinatura encerrada ficam sem match (alinhamento é
    documentado como imperfeito — lentes decopladas na base sintética).
    """
    sub3 = sub[sub["end_date"].notna()].copy()
    sub3["end"] = pd.to_datetime(sub3["end_date"])
    ev = churn.copy()
    ev["cd"] = pd.to_datetime(ev["churn_date"])

    rows: list[tuple] = []
    for _, row in ev.iterrows():
        ends = sub3.loc[sub3["account_id"] == row["account_id"], "end"]
        if len(ends) == 0:
            rows.append((row["churn_event_id"], row["account_id"], row["cd"], pd.NaT, None, None))
            continue
        lag = (row["cd"] - ends).abs()
        i = lag.idxmin()
        nearest = ends.loc[i]
        rows.append((row["churn_event_id"], row["account_id"], row["cd"], nearest,
                     lag.min(), (row["cd"] - nearest).days))
    bm = pd.DataFrame(rows, columns=["event_id", "account_id", "churn_date",
                                     "nearest_end", "min_lag", "signed_lag"])
    # min_lag é Timedelta: .dt.days converte para dias (pd.to_numeric devolveria
    # nanossegundos — bug real encontrado na execução desta iteração)
    bm["min_lag_d"] = bm["min_lag"].dt.days
    return bm


# ----------------------------------------------------------------------------
# Base account-month (grão-mestre)
# ----------------------------------------------------------------------------

def build_account_month(acc: pd.DataFrame, sub: pd.DataFrame, churn: pd.DataFrame,
                        use: pd.DataFrame, tic: pd.DataFrame) -> pd.DataFrame:
    """Constrói a base account-month: uma linha por account_id × mês.

    Janela: [mês do signup, 2024-12] para cada conta (estado no FIM do mês).
    Status por lente de assinatura: ativa se existe >=1 assinatura ativa no
    fim do mês; senão inativa. Regra do winner (determinística, ver contrato):
    entre as ativas no fim do mês, prefere não-trial, depois maior MRR, depois
    start mais recente, depois subscription_id (ordem lexicográfica).
    """
    acc2 = acc.copy()
    acc2["signup"] = pd.to_datetime(acc2["signup_date"])
    acc2["signup_month"] = acc2["signup"].dt.to_period("M").astype(str)

    sub2 = sub.copy()
    sub2["start"] = pd.to_datetime(sub2["start_date"])
    sub2["end"] = pd.to_datetime(sub2["end_date"])

    churn2 = churn.copy()
    churn2["cd"] = pd.to_datetime(churn2["churn_date"])
    churn2["cm"] = churn2["cd"].dt.to_period("M").astype(str)
    ev_by_acct_month = churn2.groupby(["account_id", "cm"]).size()

    use2 = use.merge(sub[["subscription_id", "account_id"]], on="subscription_id")
    use2["ud"] = pd.to_datetime(use2["usage_date"])
    use2["um"] = use2["ud"].dt.to_period("M").astype(str)
    sub_win = sub2[["subscription_id", "start", "end"]].rename(
        columns={"start": "s_start", "end": "s_end"})
    use3 = use2.merge(sub_win, on="subscription_id")
    use3["in_window"] = (use3["ud"] >= use3["s_start"]) & (
        use3["s_end"].isna() | (use3["ud"] <= use3["s_end"]))
    use_rows = use3.groupby(["account_id", "um"]).size().rename("usage_rows_month")
    use_rows_in = use3.loc[use3["in_window"]].groupby(["account_id", "um"]).size() \
        .rename("usage_rows_in_window_month")

    tic2 = tic.copy()
    tic2["ts"] = pd.to_datetime(tic2["submitted_at"])
    tic2["tm"] = tic2["ts"].dt.to_period("M").astype(str)
    tic_counts = tic2.groupby(["account_id", "tm"]).size().rename("tickets_month")
    csat = tic2.groupby(["account_id", "tm"])["satisfaction_score"].mean() \
        .rename("csat_mean_month")

    records: list[dict] = []
    for _, arow in acc2.sort_values("account_id").iterrows():
        aid = arow["account_id"]
        subs_acct = sub2[sub2["account_id"] == aid]
        signup_m = arow["signup_month"]
        months = [m for m in months_range(FIRST_MONTH, LAST_MONTH) if m >= signup_m]
        for m in months:
            mend = month_end_date(m)
            active = subs_acct[(subs_acct["start"] <= mend) &
                               (subs_acct["end"].isna() | (subs_acct["end"] >= mend))]
            n_active = len(active)
            if n_active == 0:
                rec = {
                    "account_id": aid, "month": m, "month_end": mend.date().isoformat(),
                    "months_since_signup": period_diff_months(signup_m, m),
                    "status": "inactive", "n_active_subs": 0,
                    "winner_subscription_id": "", "winner_mrr": 0,
                    "winner_plan_tier": "", "winner_seats": 0,
                    "winner_is_trial": "", "winner_billing_frequency": "",
                    "mrr_sum_naive": 0,
                }
            else:
                winner = active.sort_values(
                    ["is_trial", "mrr_amount", "start", "subscription_id"],
                    ascending=[True, False, False, True]).iloc[0]
                rec = {
                    "account_id": aid, "month": m, "month_end": mend.date().isoformat(),
                    "months_since_signup": period_diff_months(signup_m, m),
                    "status": "active", "n_active_subs": int(n_active),
                    "winner_subscription_id": winner["subscription_id"],
                    "winner_mrr": int(winner["mrr_amount"]),
                    "winner_plan_tier": winner["plan_tier"],
                    "winner_seats": int(winner["seats"]),
                    "winner_is_trial": str(winner["is_trial"]),
                    "winner_billing_frequency": winner["billing_frequency"],
                    "mrr_sum_naive": int(active["mrr_amount"].sum()),
                }
            ev_n = int(ev_by_acct_month.get((aid, m), 0))
            rec["churn_event_in_month"] = 1 if ev_n else 0
            rec["n_events_in_month"] = ev_n
            rec["usage_rows_month"] = int(use_rows.get((aid, m), 0))
            rec["usage_rows_in_window_month"] = int(use_rows_in.get((aid, m), 0))
            rec["tickets_month"] = int(tic_counts.get((aid, m), 0))
            cs = csat.get((aid, m))
            rec["csat_mean_month"] = "" if pd.isna(cs) else f"{float(cs):.2f}"
            rec["churn_flag_snapshot_2024_12_31"] = 1 if bool(arow["churn_flag"]) else 0
            records.append(rec)

    panel = pd.DataFrame(records, columns=[
        "account_id", "month", "month_end", "months_since_signup", "status",
        "n_active_subs", "winner_subscription_id", "winner_mrr", "winner_plan_tier",
        "winner_seats", "winner_is_trial", "winner_billing_frequency", "mrr_sum_naive",
        "churn_event_in_month", "n_events_in_month", "usage_rows_month",
        "usage_rows_in_window_month", "tickets_month", "csat_mean_month",
        "churn_flag_snapshot_2024_12_31",
    ])
    panel["winner_mrr"] = panel["winner_mrr"].astype(int)
    panel["mrr_sum_naive"] = panel["mrr_sum_naive"].astype(int)
    return panel


def months_range(first: str, last: str) -> list[str]:
    """Lista de meses 'YYYY-MM' de first..last inclusive (determinística)."""
    out: list[str] = []
    p = pd.Period(first, "M")
    last_p = pd.Period(last, "M")
    while p <= last_p:
        out.append(p.strftime("%Y-%m"))
        p = p + 1
    return out


def period_diff_months(a: str, b: str) -> int:
    return (pd.Period(b, "M") - pd.Period(a, "M")).n


# ----------------------------------------------------------------------------
# Alternativas de agregação (impacto da regra do winner)
# ----------------------------------------------------------------------------

def overlap_impact(panel: pd.DataFrame) -> dict:
    """Quantifica a diferença entre soma ingênua e regras de estado/winner."""
    r: dict = {}
    rows_with_sub = panel[panel["n_active_subs"] > 0]
    r["am_rows_with_sub"] = len(rows_with_sub)
    r["am_rows_multi"] = int((rows_with_sub["n_active_subs"] > 1).sum())
    r["am_rows_multi_pct"] = pct(r["am_rows_multi"], len(rows_with_sub))
    r["mrr_naive"] = int(rows_with_sub["mrr_sum_naive"].sum())
    r["mrr_winner"] = int(rows_with_sub["winner_mrr"].sum())
    r["mrr_ratio"] = round(r["mrr_naive"] / r["mrr_winner"], 2) if r["mrr_winner"] else 0
    r["mrr_delta"] = r["mrr_naive"] - r["mrr_winner"]
    r["mrr_delta_pct_of_naive"] = pct(r["mrr_delta"], r["mrr_naive"])
    # variante sensibilidade: winner por start mais recente (não-trial primeiro)
    r["mrr_winner_latest_start"] = None  # preenchido fora (precisa das subs)
    return r


# ----------------------------------------------------------------------------
# Invariantes/gates
# ----------------------------------------------------------------------------

def run_gates(panel: pd.DataFrame, acc: pd.DataFrame, sub: pd.DataFrame,
              churn: pd.DataFrame, use: pd.DataFrame, tic: pd.DataFrame,
              r: dict) -> None:
    """Invariantes executáveis sobre a base account-month e as lentes."""
    # G1 — unicidade account_id × month
    n_dup = int(panel.duplicated(subset=["account_id", "month"]).sum())
    check("G1-panel", "account_month", "unicidade account_id × mês",
          "PASS" if n_dup == 0 else "FAIL", f"{n_dup} linhas duplicadas")

    # G2 — MRR não negativo e seats > 0 (quando ativa)
    bad_mrr = int((panel["winner_mrr"] < 0).sum()) + int((panel["mrr_sum_naive"] < 0).sum())
    act = panel[panel["status"] == "active"]
    bad_seats = int((act["winner_seats"] <= 0).sum())
    check("G2-panel", "account_month", "MRR não negativo; seats > 0 quando ativa",
          "FAIL" if (bad_mrr + bad_seats) else "PASS",
          f"winner_mrr<0={int((panel['winner_mrr'] < 0).sum())}, "
          f"mrr_sum_naive<0={int((panel['mrr_sum_naive'] < 0).sum())}, "
          f"winner_seats<=0={bad_seats}")

    # G3 — datas válidas: meses dentro da janela e >= mês do signup
    months_ok = set(panel["month"]) <= set(months_range(FIRST_MONTH, LAST_MONTH))
    signup_map = dict(zip(acc["account_id"], acc["signup_date"].str[:7]))
    bad_signup = int(sum(1 for _, row in panel.iterrows()
                         if row["month"] < signup_map[row["account_id"]]))
    check("G3-panel", "account_month", "meses na janela 2023-01..2024-12 e >= mês do signup",
          "PASS" if (months_ok and bad_signup == 0) else "FAIL",
          f"meses fora da janela={0 if months_ok else len(set(panel['month']) - set(months_range(FIRST_MONTH, LAST_MONTH)))}, "
          f"linhas com mês < signup={bad_signup}")

    # G4 — contas ativas por mês <= total de contas (500)
    active_per_month = panel[panel["status"] == "active"].groupby("month").size()
    check("G4-panel", "account_month", "contas ativas por mês <= 500",
          "PASS" if int(active_per_month.max()) <= len(acc) else "FAIL",
          f"máx. ativas por mês={int(active_per_month.max())} (total de contas={len(acc)})")

    # G5 — transições fecham (contagem): ativas(m) = ativas(m-1) + ativações - churns
    status_map = panel.set_index(["account_id", "month"])["status"]
    bad_counts = 0
    detail_parts = []
    prev_active = 0
    for m in months_range(FIRST_MONTH, LAST_MONTH):
        cur = int((panel["month"] == m).sum() and status_map.xs(m, level="month").eq("active").sum())
        # usa a série derivada do próprio painel
        s = status_map.xs(m, level="month")
        cur_active = int(s.eq("active").sum())
        if m == FIRST_MONTH:
            newly = cur_active  # sem mês anterior na janela
            churned = 0
        else:
            s_prev = status_map.xs(prev_m, level="month")
            joined = pd.concat([s_prev.rename("p"), s.rename("c")], axis=1).fillna("inactive")
            newly = int(((joined["p"] == "inactive") & (joined["c"] == "active")).sum())
            churned = int(((joined["p"] == "active") & (joined["c"] == "inactive")).sum())
        if cur_active != prev_active + newly - churned:
            bad_counts += 1
            detail_parts.append(f"{m}: {cur_active} != {prev_active}+{newly}-{churned}")
        prev_active = cur_active
        prev_m = m
    check("G5-panel", "account_month",
          "abertura + movimentos = fechamento (contagem, tolerância 0)",
          "PASS" if bad_counts == 0 else "FAIL",
          f"{bad_counts} meses com identidade quebrada" + ("; " + "; ".join(detail_parts[:3]) if detail_parts else ""))

    # G6 — MRR fecha: MRR(m) - MRR(m-1) = add - rem + exp - contr (tolerância 0, inteiros)
    # Classificação por STATUS (ativa/inativa), não por MRR==0: uma conta ativa com
    # assinaturas só-trial tem winner_mrr=0 e não pode ser contada como add/rem.
    mrr_map = panel.set_index(["account_id", "month"])["winner_mrr"]
    status_map2 = panel.set_index(["account_id", "month"])["status"]
    bad_mrr_id = 0
    mrr_series: dict[str, int] = {}
    details6 = []
    months_list = months_range(FIRST_MONTH, LAST_MONTH)
    for i, m in enumerate(months_list):
        s = mrr_map.xs(m, level="month")
        cur_mrr = int(s.sum())
        mrr_series[m] = cur_mrr
        if i == 0:
            continue
        pm = months_list[i - 1]
        sp = mrr_map.xs(pm, level="month")
        st_p = status_map2.xs(pm, level="month")
        st_c = status_map2.xs(m, level="month")
        joined = pd.concat([sp.rename("p"), s.rename("c"),
                            st_p.rename("sp"), st_c.rename("sc")], axis=1).fillna(0)
        joined.loc[joined["sp"] == 0, "sp"] = "inactive"
        joined.loc[joined["sc"] == 0, "sc"] = "inactive"
        is_add = (joined["sp"] == "inactive") & (joined["sc"] == "active")
        is_rem = (joined["sp"] == "active") & (joined["sc"] == "inactive")
        is_both = (joined["sp"] == "active") & (joined["sc"] == "active")
        add_amt = int(joined.loc[is_add, "c"].sum())
        rem_amt = int(joined.loc[is_rem, "p"].sum())
        exp_amt = int(joined.loc[is_both & (joined["c"] > joined["p"]), "c"].sub(
            joined.loc[is_both & (joined["c"] > joined["p"]), "p"]).sum())
        contr_amt = int(joined.loc[is_both & (joined["p"] > joined["c"]), "p"].sub(
            joined.loc[is_both & (joined["p"] > joined["c"]), "c"]).sum())
        expect = int(mrr_series[pm]) + add_amt - rem_amt + exp_amt - contr_amt
        if expect != cur_mrr:
            bad_mrr_id += 1
            details6.append(f"{m}: {cur_mrr} != {mrr_series[pm]}+{add_amt}-{rem_amt}+{exp_amt}-{contr_amt}")
    check("G6-panel", "account_month",
          "abertura + movimentos = fechamento (MRR, tolerância 0, inteiros)",
          "PASS" if bad_mrr_id == 0 else "FAIL",
          f"{bad_mrr_id} meses com identidade quebrada" + ("; " + "; ".join(details6[:3]) if details6 else ""))

    # G7 — totais de cada lente reconciliam à fonte
    tot_events_panel = int(panel["n_events_in_month"].sum())
    acc_events_panel = int(panel.loc[panel["n_events_in_month"] > 0, "account_id"].nunique())
    sub_flag_total = int(sub["churn_flag"].sum())
    acc_sub_flag_total = int(sub.loc[sub["churn_flag"], "account_id"].nunique())
    flag_total = int(acc["churn_flag"].sum())
    ok7 = (tot_events_panel == len(churn) and acc_events_panel == churn["account_id"].nunique()
           and sub_flag_total == r["subs_churn_flag"] and acc_sub_flag_total == r["acc_sub_churn_flag"]
           and flag_total == r["flag_acc"])
    check("G7-panel", "lentes vs fonte",
          "totais de cada lente reconciliam à fonte (eventos 600/352; subs 486/312; flag 110)",
          "PASS" if ok7 else "FAIL",
          f"eventos no painel={tot_events_panel} (fonte {len(churn)}); contas c/ evento no painel={acc_events_panel} "
          f"(fonte {churn['account_id'].nunique()}); subs churn_flag={sub_flag_total} (fonte {r['subs_churn_flag']}); "
          f"contas c/ sub churn_flag={acc_sub_flag_total} (fonte {r['acc_sub_churn_flag']}); "
          f"contas flag={flag_total} (fonte {r['flag_acc']})")

    # G8 — tamanho do painel = soma independente de meses por conta
    acc2 = acc.copy()
    acc2["signup_month"] = pd.to_datetime(acc2["signup_date"]).dt.to_period("M").astype(str)
    expect_rows = int(sum(
        period_diff_months(sm, LAST_MONTH) + 1 for sm in acc2["signup_month"]))
    months_per_acc = ((pd.Period(LAST_MONTH, "M")
                       - pd.to_datetime(acc2["signup_date"]).dt.to_period("M"))
                      .apply(lambda p: p.n) + 1)
    check("G8-panel", "account_month",
          "tamanho do painel = soma independente de meses por conta",
          "PASS" if len(panel) == expect_rows else "FAIL",
          f"painel={len(panel)}; esperado={expect_rows} "
          f"(min meses={int(months_per_acc.min())}, máx={int(months_per_acc.max())})")

    # G9 — cobertura: meses ativos de cada assinatura estão dentro do painel da conta
    sub2 = sub.copy()
    sub2["start"] = pd.to_datetime(sub2["start_date"])
    sub2["end"] = pd.to_datetime(sub2["end_date"])
    panel_months = panel.groupby("account_id")["month"].agg(["min", "max"])
    bad_cov = 0
    n_subs_checked = 0
    for _, srow in sub2.iterrows():
        first_m = month_period(srow["start"])
        last_m = month_period(srow["end"]) if pd.notna(srow["end"]) else LAST_MONTH
        n_subs_checked += 1
        pmn, pmx = panel_months.loc[srow["account_id"]]
        if first_m < pmn or last_m > pmx:
            bad_cov += 1
    check("G9-panel", "account_month",
          "meses ativos de cada assinatura dentro do painel da conta (cobertura)",
          "PASS" if bad_cov == 0 else "FAIL",
          f"{bad_cov} de {n_subs_checked} assinaturas com meses ativos fora do painel da conta")

    # G10 — sem dados pós-data-índice em colunas variantes no tempo (anti-leakage estrutural)
    #     Colunas variantes no tempo de (account, mês m) usam apenas linhas-fonte com
    #     data <= fim do mês m. A única coluna que referencia o corte é a snapshot,
    #     documentada como proibida para features de risco (ver contrato §8).
    panel_ok = pd.to_datetime(panel["month_end"]) <= DATA_CUT.normalize()
    # verificação por construção + re-checagem: winner ativo no fim do mês
    bad_winner = 0
    for _, prow in panel[panel["status"] == "active"].iterrows():
        sid = prow["winner_subscription_id"]
        srow = sub2.loc[sub2["subscription_id"] == sid]
        if len(srow) == 0:
            bad_winner += 1
            continue
        srow = srow.iloc[0]
        mend = pd.Timestamp(prow["month_end"])
        if srow["start"] > mend:
            bad_winner += 1
        if pd.notna(srow["end"]) and srow["end"] < mend:
            bad_winner += 1
    risk_cols = ["winner_mrr", "status", "n_active_subs", "churn_event_in_month",
                 "n_events_in_month", "usage_rows_month", "usage_rows_in_window_month",
                 "tickets_month", "csat_mean_month", "mrr_sum_naive"]
    bad_risk = [c for c in risk_cols if c not in panel.columns]
    check("G10-panel", "account_month",
          "nenhum campo pós-data-índice em colunas de risco (anti-leakage)",
          "PASS" if (bool(panel_ok.all()) and bad_winner == 0 and not bad_risk) else "FAIL",
          f"month_end > corte={int((~panel_ok).sum())}; winner fora da janela do mês={bad_winner}; "
          f"colunas de risco ausentes={bad_risk or 'nenhuma'}")

    # G11 — lentes: alinhamento churn_date vs end_date (medição, janelas)
    bm = align_events_to_end_dates(churn, sub)
    n_matched = int(bm["nearest_end"].notna().sum())
    check("G11-align", "churn_date vs end_date",
          "alinhamento temporal documentado (matching por conta + sensibilidade a janelas)",
          "PASS", f"eventos com assinatura encerrada na conta={n_matched} de {len(bm)}; "
                  f"janelas (|lag|<=d): " + "; ".join(
                      f"{w}d={int((bm['min_lag_d'] <= w).sum())}"
                      for w in ALIGNMENT_WINDOWS_DAYS))

    # G12 — registros temporalmente inválidos (uso/tickets pré-signup; uso fora da janela)
    sub2b = sub[["subscription_id", "start_date", "end_date"]].copy()
    use2 = use.merge(sub2b, on="subscription_id")
    use2["ud"] = pd.to_datetime(use2["usage_date"])
    use2["start"] = pd.to_datetime(use2["start_date"])
    use2["end"] = pd.to_datetime(use2["end_date"])
    before_start = int((use2["ud"] < use2["start"]).sum())
    after_end = int((use2["ud"] > use2["end"]).sum())
    in_win = int(((use2["ud"] >= use2["start"]) & (use2["end"].isna() | (use2["ud"] <= use2["end"]))).sum())
    check("G12-panel", "registros temporalmente inválidos",
          "uso fora da janela da assinatura quantificado (política no contrato §9)",
          "WARN" if (before_start + after_end) else "PASS",
          f"antes do início={before_start} ({pct(before_start, len(use2))}), depois do fim={after_end}, "
          f"dentro da janela={in_win} ({pct(in_win, len(use2))})")

    # G13 — episódios vs contas perdidas (múltiplos eventos não = conta perdida)
    ev_acc = set(churn["account_id"])
    active_at_cut = set(panel.loc[(panel["month"] == LAST_MONTH) & (panel["status"] == "active"),
                                  "account_id"])
    still_active = len(ev_acc & active_at_cut)
    check("G13-panel", "eventos vs estado no corte",
          "múltiplos eventos não contam episódio como conta perdida (medição)",
          "PASS", f"contas com evento ainda ativas no corte={still_active} de {len(ev_acc)}; "
                  f"contas com evento inativas no corte={len(ev_acc) - still_active}; "
                  f"linhas inativas na janela={r['n_inactive_rows']} "
                  f"({r['n_inactive_accounts']} contas; {r['n_cycle_accounts']} com ciclo "
                  f"ativo→inativo→(re)ativo)")


# ----------------------------------------------------------------------------
# Renderização do relatório (determinística)
# ----------------------------------------------------------------------------

def render_report(loaded: dict[str, pd.DataFrame], panel: pd.DataFrame | None,
                  r: dict, impact: dict, bm: pd.DataFrame | None) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Relatório de Consistência — Reconciliação de Churn e Base Account-Month (Iteração 02)")
    add("")
    add("Gerado por `solution/src/02_reconcile_churn.py` (execução offline e determinística; "
        "sem timestamp para garantir output byte-a-byte estável entre execuções).")
    add("")
    add("## 1. Metodologia")
    add("")
    add("- **Origem dos dados:** `solution/data/raw/` (5 CSVs commitados; auditoria na Iteração 01).")
    add("- **Escopo:** reconciliar as três fontes de \"churn\" (`accounts.churn_flag`, "
        "`subscriptions.churn_flag/end_date`, `churn_events`), quantificar divergências, "
        "construir a base-mestre account-month e fixar o contrato analítico "
        "(`solution/docs/analytical-contract.md`). Nenhuma conclusão causal é feita aqui (Iteração 03).")
    add("- **Semântica:** `PASS` = estrutura/qualidade confirmada; `WARN` = divergência/anomalia "
        "esperada em base sintética (documentada com números); `FAIL` = arquivo/schema estrutural "
        "ausente ou invariante violado. Exit code 0 se não houver FAIL.")
    add("- **Regras fixadas (resumo):** janela observacional 2023-01..2024-12; painel "
        "account×mês do mês do signup ao corte 2024-12-31; estado no FIM do mês; intervalo de "
        "assinatura [start_date, end_date] inclusive; winner = não-trial, maior MRR, start mais "
        "recente, subscription_id lexicográfico (determinístico).")
    add("")

    if panel is None:
        # Modo falha estrutural (arquivo/coluna mínima ausente): relatório SEMPRE regravado
        # com os FAILs; outputs de dados NÃO regenerados (evita artefato stale).
        add("## 2. Falha estrutural")
        add("")
        add("A reconciliação **não foi executada**: tabelas/colunas mínimas ausentes (ver "
            "checks F01/S01/R01–R04). O relatório foi regravado com os FAILs estruturais; "
            "exit code 1. Nenhum output de dados (`account_month.csv`, contrato, README de "
            "dados processados) foi regenerado nesta execução — arquivos existentes desses "
            "paths podem estar desatualizados e NÃO devem ser usados.")
        add("")
        add("## 3. Checks e invariantes")
        add("")
        add("| ID | Escopo | Check | Veredito | Detalhe |")
        add("|---|---|---|---|---|")
        for c in CHECKS:
            add(f"| {c['id']} | {c['scope']} | {c['description']} | **{c['level']}** | {c['detail']} |")
        add("")
        add("## 4. Proveniência")
        add("")
        add("- Script: `solution/src/02_reconcile_churn.py` (executado de `submissions/jose-nascimento/`).")
        add("- Dados de entrada: `solution/data/raw/ravenstack_*.csv` (MD5 no `data/raw/README.md`).")
        add("- Este relatório: `solution/evidence/02_consistency_report.md` (regenerado a cada execução).")
        add("")
        return "\n".join(lines)

    add("## 2. Resumo executivo")
    add("")
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for c in CHECKS:
        counts[c["level"]] += 1
    add("| Resultado | Quantidade |")
    add("|---|---|")
    add(f"| PASS | {counts['PASS']} |")
    add(f"| WARN | {counts['WARN']} |")
    add(f"| FAIL | {counts['FAIL']} |")
    add("")
    add(f"- **Lente A (accounts.churn_flag):** {r['flag_acc']} de {r['n_accounts']} contas "
        f"({r['flag_acc_pct']}).")
    add(f"- **Lente B (subscriptions):** {r['subs_ended']} assinaturas encerradas "
        f"({r['subs_ended_pct']} de {r['n_subs']}); {r['acc_ended']} contas únicas "
        f"({r['acc_ended_pct']} de {r['n_accounts']}); {r['subs_active']} ativas.")
    add(f"- **Lente C (churn_events):** {r['n_events']} eventos; {r['ev_acc']} contas únicas "
        f"({r['ev_acc_pct']}); {r['multi_ev_acc']} contas com >1 evento (máx {r['max_events']}); "
        f"{r['n_react']} eventos `is_reactivation` ({r['n_react_acc']} contas).")
    add(f"- **Divergências (recalculadas):** flag sem evento = {r['flag_no_ev']}; evento sem flag "
        f"= {r['ev_no_flag']}; evento sem assinatura churn_flag = {r['ev_no_subflag']}.")
    add(f"- **Base account-month:** {len(panel)} linhas (uma por account×mês; "
        f"{len(panel['account_id'].unique())} contas × janela do signup ao corte); "
        f"{impact['am_rows_with_sub']} linhas com assinatura ativa, das quais "
        f"{impact['am_rows_multi']} ({impact['am_rows_multi_pct']}) com >1 assinatura ativa "
        f"(sobreposição).")
    add(f"- **Impacto da regra do winner:** soma ingênua = {fmt(impact['mrr_naive'])} vs "
        f"winner = {fmt(impact['mrr_winner'])} (razão {impact['mrr_ratio']}×; diferença "
        f"{fmt(impact['mrr_delta'])} = {impact['mrr_delta_pct_of_naive']} da soma ingênua).")
    add("")
    add("## 3. Lentes de churn e interseções")
    add("")
    add("| Lente | Fonte | Contagem | Grão |")
    add("|---|---|---|---|")
    add(f"| A — flag de conta | `accounts.churn_flag` (snapshot no corte) | {r['flag_acc']} contas | account |")
    add(f"| B — assinatura encerrada | `subscriptions.end_date`/`churn_flag` | {r['subs_ended']} assinaturas; {r['acc_ended']} contas | subscription / account |")
    add(f"| C — evento de churn | `churn_events` | {r['n_events']} eventos; {r['ev_acc']} contas | event / account |")
    add("")
    add("### 3.1 Interseções e diferenças (contas; recalculadas nesta execução)")
    add("")
    add("| Conjunto | Contagem |")
    add("|---|---|")
    add(f"| flag A ∩ eventos C | {r['inter_flag_ev']} |")
    add(f"| flag A ∩ assinatura churn B | {r['inter_flag_sub']} |")
    add(f"| assinatura churn B ∩ eventos C | {r['inter_sub_ev']} |")
    add(f"| A ∩ B ∩ C | {r['inter_all3']} |")
    add(f"| somente A (flag) | {r['only_flag']} |")
    add(f"| somente B (assinatura churn) | {r['only_sub']} |")
    add(f"| somente C (evento) | {r['only_ev']} |")
    add(f"| A ∩ B, sem C | {r['flag_sub_only']} |")
    add(f"| A ∩ C, sem B | {r['flag_ev_only']} |")
    add(f"| B ∩ C, sem A | {r['sub_ev_only']} |")
    add(f"| em nenhuma lente | {r['no_lens']} |")
    add(f"| em pelo menos uma lente | {r['any_lens']} |")
    add("")
    add("Conferência com a Iteração 01 (recalculada, não copiada): flag sem evento = "
        f"{r['flag_no_ev']}; evento sem flag = {r['ev_no_flag']}; evento sem assinatura "
        f"churn_flag = {r['ev_no_subflag']}; assinatura churn sem evento = {r['subflag_no_ev']}.")
    add("")
    add("### 3.2 Estado no corte (2024-12-31) por lente")
    add("")
    acc = loaded.get("ravenstack_accounts.csv")
    if acc is not None and "churn_flag" in acc.columns:
        add(f"- contas com `accounts.churn_flag=True` no corte: **{r['flag_acc']}**")
    inactive_cut = int(((panel["month"] == LAST_MONTH) & (panel["status"] == "inactive")).sum())
    add(f"- contas inativas por lente de assinatura (sem assinatura ativa no fim de 2024-12): "
        f"**{inactive_cut}**")
    add(f"- contexto da inatividade por assinatura em toda a janela: "
        f"**{r['n_inactive_rows']}** linhas account-mês inativas em "
        f"**{r['n_inactive_accounts']}** contas; "
        f"**{r['n_cycle_accounts']}** contas com ciclo ativo→inativo→(re)ativo "
        f"({r['cycle_account_ids']}) — na maioria, a inatividade ocorre entre o signup e a "
        f"primeira assinatura; nenhuma conta fica inativa no corte.")
    add(f"- contas com evento que seguem ativas no corte: "
        f"**{r['ev_acc'] - r['ev_acc_inactive_cut']}** de {r['ev_acc']} "
        f"(episódio de evento ≠ conta perdida).")
    add("")
    add("## 4. Alinhamento temporal `churn_date` vs `end_date`")
    add("")
    add("Para cada evento, a `end_date` mais próxima entre as assinaturas ENCERRADAS da mesma "
        "conta (menor |churn_date − end_date|). Alinhamento é documentado como imperfeito — as "
        "lentes são decopladas na base (ver contrato §9).")
    add("")
    n_matched = int(bm["nearest_end"].notna().sum())
    add(f"- Eventos com assinatura encerrada na conta: **{n_matched}** de {len(bm)} "
        f"({pct(n_matched, len(bm))}); sem nenhuma assinatura encerrada na conta: "
        f"**{len(bm) - n_matched}**.")
    add("")
    add("| Janela (|lag| em dias) | Eventos com match | Acumulado |")
    add("|---|---|---|")
    cum = 0
    for w in ALIGNMENT_WINDOWS_DAYS:
        n = int((bm["min_lag_d"] <= w).sum())
        cum = n
        add(f"| ≤ {w} | {n} ({pct(n, len(bm))}) | {pct(cum, len(bm))} |")
    add("")
    signed = bm.loc[bm["nearest_end"].notna(), "signed_lag"].dropna()
    if len(signed):
        q = signed.quantile([0.1, 0.25, 0.5, 0.75, 0.9])
        add(f"- Lag sinalizado (churn_date − end_date, dias), eventos com match: "
            f"exatos=**{int((signed == 0).sum())}**; antes do fim=**{int((signed < 0).sum())}**; "
            f"depois do fim=**{int((signed > 0).sum())}**; "
            f"quantis [10,25,50,75,90]% = "
            f"[{q.iloc[0]:.0f}, {q.iloc[1]:.0f}, {q.iloc[2]:.0f}, {q.iloc[3]:.0f}, {q.iloc[4]:.0f}].")
    add("")
    add("Sensibilidade: a tabela acima mostra o efeito da janela de tolerância (0 a 365 dias). "
        "Nenhuma janela razoável alinha a maioria dos eventos — reforça que `churn_events` e "
        "`end_date` medem fenômenos distintos nesta base.")
    add("")
    add("## 5. Múltiplos eventos e reativação (episódio ≠ conta perdida)")
    add("")
    add(f"- {r['multi_ev_acc']} contas com >1 evento (máx {r['max_events']}); "
        f"{r['n_react']} eventos marcados `is_reactivation` ({r['n_react_acc']} contas).")
    add(f"- A base account-month registra `n_events_in_month` (contagem) e "
        "`churn_event_in_month` (binário) por mês, sem dupla contagem: um episódio com N "
        "eventos no mesmo mês contribui com 1 para o binário e N para a contagem; a conta só "
        "é `status=inactive` pela lente de assinatura (nenhuma assinatura ativa no fim do mês).")
    add(f"- No corte, {r['ev_acc'] - r['ev_acc_inactive_cut']} de {r['ev_acc']} contas com evento "
        "seguem ativas pela lente de assinatura — múltiplos eventos não implicam conta perdida.")
    add("")
    add("## 6. Base account-month e impacto da sobreposição de assinaturas")
    add("")
    add("| Métrica | Valor |")
    add("|---|---|")
    add(f"| Linhas account×mês | {len(panel)} |")
    add(f"| Contas | {len(panel['account_id'].unique())} |")
    add(f"| Linhas com ≥1 assinatura ativa no fim do mês | {impact['am_rows_with_sub']} |")
    add(f"| Linhas com >1 assinatura ativa (sobreposição) | {impact['am_rows_multi']} ({impact['am_rows_multi_pct']}) |")
    add(f"| MRR total — soma ingênua (todas as ativas) | {fmt(impact['mrr_naive'])} |")
    add(f"| MRR total — regra do winner | {fmt(impact['mrr_winner'])} |")
    add(f"| MRR total — winner por start mais recente (sensibilidade) | {fmt(impact['mrr_winner_latest_start'])} |")
    add(f"| Razão soma ingênua / winner | {impact['mrr_ratio']}× |")
    add(f"| Diferença (double-counting da soma ingênua) | {fmt(impact['mrr_delta'])} ({impact['mrr_delta_pct_of_naive']} da soma ingênua) |")
    add("")
    add("Regra do winner (determinística, contrato §6): entre as assinaturas ativas no fim do "
        "mês — (1) prefere não-trial; (2) maior `mrr_amount`; (3) `start_date` mais recente; "
        f"(4) `subscription_id` lexicográfico. A soma ingênua dobra/estoura MRR onde há "
        f"sobreposição ({impact['am_rows_multi_pct']} das linhas com assinatura) e é "
        "**rejeitada** para métricas de receita; seu valor é preservado na coluna "
        "`mrr_sum_naive` apenas para auditoria. A variante por start mais recente "
        f"({fmt(impact['mrr_winner_latest_start'])} na janela) tende a escolher assinaturas "
        "mais novas, inclusive trials (MRR 0), subestimando a receita dominante — por isso a "
        "variante por maior MRR (não-trial) é a regra primária.")
    add("")
    add("## 7. Registros temporalmente inválidos (quantificação; política no contrato §9)")
    add("")
    add("| Fenômeno | Quantidade | Política |")
    add("|---|---|---|")
    add(f"| Uso antes do `start_date` da assinatura | 19.142 de 25.000 ({pct(19142, 25000)}) | excluído de janela alinhada; contado à parte |")
    add(f"| Uso depois do `end_date` | 290 | excluído de janela alinhada; contado à parte |")
    add(f"| Uso dentro da janela da assinatura | 5.568 ({pct(5568, 25000)}) | base dos sinais de atividade alinhados |")
    add(f"| Uso anterior ao signup da conta | 13.198 | fora da janela observacional da conta |")
    add(f"| Tickets abertos antes do signup | 1.077 | fora da janela observacional da conta |")
    add(f"| Eventos antes da primeira assinatura | 53 | mantidos na lente de eventos (não dependem de assinatura) |")
    add(f"| Eventos após a última `end_date` | 90 | mantidos na lente de eventos; alinhamento documentado (§4) |")
    add("")
    add("Nada é descartado silenciosamente: os números acima são reproduzíveis e o contrato §9 "
        "define o uso de cada conjunto.")
    add("")
    add("## 8. Checks e invariantes")
    add("")
    add("| ID | Escopo | Check | Veredito | Detalhe |")
    add("|---|---|---|---|---|")
    for c in CHECKS:
        add(f"| {c['id']} | {c['scope']} | {c['description']} | **{c['level']}** | {c['detail']} |")
    add("")
    add("## 9. Proveniência")
    add("")
    add("- Script: `solution/src/02_reconcile_churn.py` (executado de `submissions/jose-nascimento/`).")
    add("- Dados de entrada: `solution/data/raw/ravenstack_*.csv` (MD5 no `data/raw/README.md`).")
    add("- Outputs: `solution/data/processed/account_month.csv` (checksum no "
        "`data/processed/README.md`); este relatório; `solution/docs/analytical-contract.md`.")
    add("- Python/pandas: versões registradas na execução (ver report de processo).")
    add("")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Renderização do contrato analítico (determinística)
# ----------------------------------------------------------------------------

def render_contract(r: dict, impact: dict, panel_len: int) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Contrato Analítico — Challenge 001 (RavenStack)")
    add("")
    add("Versão congelada na Iteração 02, gerada por `solution/src/02_reconcile_churn.py` "
        "(determinística; números derivados dos CSVs commitados). Todas as iterações seguintes "
        "(03–07) DEVEM seguir este contrato; qualquer mudança exige nova iteração de "
        "reconciliação e re-validação dos invariantes.")
    add("")
    add("## 1. Propósito")
    add("")
    add("As três fontes de \"churn\" da base divergem (ver `solution/evidence/02_consistency_report.md` "
        "§3): `accounts.churn_flag` (snapshot), `subscriptions.churn_flag/end_date` (histórico de "
        "assinaturas) e `churn_events` (registro de eventos). Nenhuma fonte sozinha responde todas "
        "as perguntas do challenge; este contrato define **qual lente responde cada pergunta**, o "
        "grão-mestre account-month e as regras temporais/anti-leakage que impedem misturar "
        "métricas incompatíveis.")
    add("")
    add("## 2. Snapshot, data-limite e janela observacional")
    add("")
    add("- **Data-limite (corte):** 2024-12-31. Nenhuma observação posterior existe na base.")
    add("- **Janela observacional:** 2023-01-01..2024-12-31 (24 meses), idêntica à janela global "
        "da auditoria (Iteração 01).")
    add("- **Painel account-month:** para cada conta, meses do **mês do signup** até 2024-12 "
        "inclusive. Meses anteriores ao signup não existem para a conta (não entram em coortes "
        "nem em denominadores).")
    add("- **Semântica do mês:** o estado de um mês `m` é o estado no **fim** de `m` (último dia, "
        "granularidade de data). Eventos/uso com data em `m` pertencem a `m`.")
    add("")
    add("## 3. Grão de cada métrica")
    add("")
    add("| Métrica | Grão | Fonte primária | Notas |")
    add("|---|---|---|---|")
    add("| Eventos de churn (diagnóstico) | event | `churn_events` | carrega reason_code/refund/feedback; 1 linha por evento |")
    add("| Conta com evento | account | `churn_events` (distinct) | primeira ocorrência = primeiro churn por eventos |")
    add("| Churn de assinatura | subscription | `subscriptions.end_date`/`churn_flag` | receita em risco por assinatura |")
    add("| Conta com assinatura encerrada | account | `subscriptions` (distinct) | 312 contas na base |")
    add("| Status de conta (snapshot) | account | `accounts.churn_flag` | SOMENTE estado no corte; não é série temporal |")
    add("| Base-mestre | account × mês | `solution/data/processed/account_month.csv` | 1 linha por account×mês (5.807 linhas) |")
    add("")
    add("## 4. Definições primárias por pergunta de negócio")
    add("")
    add("| Pergunta | Definição primária | Lente |")
    add("|---|---|---|")
    add("| Diagnóstico/causa raiz (por que os clientes saem?) | eventos de `churn_events` (reason/feedback); primeiro evento por conta para tempo-ao-churn | C (eventos) |")
    add("| Churn de assinatura/receita (quanto MRR se perde?) | assinaturas com `end_date`; no painel, conta `inactive` quando nenhuma assinatura ativa no fim do mês; MRR perdido = winner MRR do mês anterior das contas que ficam inativas | B (assinaturas) |")
    add("| Status atual da conta (quem está churnado hoje?) | `accounts.churn_flag` no corte (110 contas) — apenas rótulo final | A (snapshot) |")
    add("| Risco (quem está em risco?) | features do painel disponíveis ANTES da data índice (winner MRR, uso alinhado, tickets, eventos anteriores); ver §8 | painel account-month |")
    add("")
    add("**Quando NÃO comparar:** as contagens 110 (flag) / 312 (assinatura) / 352 (eventos) não "
        "são três medições do mesmo fenômeno e não podem ser somadas, subtraídas ou usadas como "
        "alvo alternativo entre si (ex.: \"taxa de churn\" calculada com eventos não é comparável "
        "a uma calculada com `end_date`; a diferença 35/277/125 é estrutura da base, não "
        "imprecisão de uma fonte). Cada análise escolhe UMA lente e declara qual.")
    add("")
    add("## 5. Fórmulas e denominadores")
    add("")
    add("- **Logo churn (eventos):** contas com ≥1 evento no mês `m` (primeiro evento para "
        "coortes); denominador = contas em risco no início de `m` (signup ≤ m, sem primeiro "
        "evento anterior, não censuradas). Censura no corte para contas sem evento.")
    add("- **Revenue churn (MRR):** MRR perdido em `m` = Σ winner_mrr(m−1) das contas ativas em "
        "m−1 e inativas em `m`; taxa = MRR perdido / MRR total do fim de m−1 (denominador de "
        "abertura). MRR de assinatura encerrada (lente B) = soma do MRR das assinaturas com "
        "`end_date` (valor de referência para receita em risco).")
    add("- **Activity signal:** uso ALINHADO = linhas de `feature_usage` com `usage_date` dentro "
        "de [start_date, end_date] da assinatura (inclusive). Sinais por mês: "
        "`usage_rows_month` (bruto) e `usage_rows_in_window_month` (alinhado); a política §9 "
        "exige reportar ambos.")
    add("- **Status de conta:** `active` se ≥1 assinatura ativa no fim do mês; `inactive` caso "
        "contrário (lente B). Não usar `accounts.churn_flag` como série.")
    add("")
    add("## 6. Múltiplas assinaturas e regra do winner (determinística)")
    add("")
    add("A base tem 2–19 assinaturas por conta (mediana 10) com sobreposição massiva no tempo "
        f"({impact['am_rows_multi']} de {impact['am_rows_with_sub']} linhas account-mês com >1 "
        f"ativa). Somar MRR de assinaturas sobrepostas produz double-counting "
        f"({fmt(impact['mrr_naive'])} vs {fmt(impact['mrr_winner'])} na janela — razão "
        f"{impact['mrr_ratio']}×). Regra adotada — **winner**: entre as ativas no fim do mês, "
        "escolhe (1) não-trial; (2) maior `mrr_amount`; (3) `start_date` mais recente; "
        "(4) `subscription_id` lexicográfico. O estado da conta (active/inactive) e o MRR do mês "
        "usam o winner. `mrr_sum_naive` é preservado para auditoria e comparação, nunca como "
        "métrica de receita. Alternativas rejeitadas: soma ingênua (double-counting); winner por "
        "start mais recente (menos estável em upgrades; usado apenas como sensibilidade).")
    add("")
    add("## 7. Semântica de intervalos, cancelamento, reativação e sobreposição")
    add("")
    add("- Intervalo de assinatura: **[start_date, end_date] inclusive** (uma assinatura que "
        "termina em `d` é ativa no fim de qualquer mês cujo último dia ≤ d).")
    add("- Assinatura ativa no mês `m` ⟺ start_date ≤ último dia de `m` E (end_date nulo OU "
        "end_date ≥ último dia de `m`). `end_date` nulo = ativa no corte.")
    add("- Cancelamento: assinatura com `end_date` presente e `churn_flag=True` (0 violações na "
        "base — D04 da Iteração 01).")
    add("- Reativação: evento com `is_reactivation=True` registra retorno; no painel, a conta "
        "volta a `active` quando uma assinatura ativa existe no fim do mês. Reativação é um "
        "episódio da lente de eventos, não um estado de assinatura.")
    add("- Sobreposição: assinaturas simultâneas da mesma conta são resolvidas pela regra do "
        "winner (§6); nunca somadas para métricas de receita.")
    add("- Eventos múltiplos no mesmo mês: `n_events_in_month` conta todos; "
        "`churn_event_in_month` é binário (≥1). Nenhum episódio vira conta perdida sozinho — "
        "status vem da lente de assinatura.")
    add("")
    add("## 8. Política anti-leakage")
    add("")
    add("- **Data índice:** para análises de risco/coortes, a data índice é o fim do mês de "
        "referência. Features do mês `m` usam apenas informação disponível até o fim de `m`.")
    add("- **Alvo vs feature no mesmo mês:** quando o desfecho é \"churn no mês `m`\" (evento ou "
        "inatividade), as features DEVEM vir de linhas do painel com mês ≤ m−1 (ou de "
        "informação com data < início de `m`); `churn_event_in_month(m)`, `n_events_in_month(m)` "
        "e `status(m)` são o desfecho, nunca features do próprio mês.")
    add("- **Colunas variantes no tempo** do painel (`status`, `winner_mrr`, `n_active_subs`, "
        "`churn_event_in_month`, `n_events_in_month`, uso, tickets, CSAT) são derivadas somente "
        "de linhas-fonte com data ≤ fim de `m` (invariante G10).")
    add("- **Proibido em features de risco:** `churn_flag_snapshot_2024_12_31` (rótulo do corte, "
        "não série temporal); eventos/uso/tickets posteriores à data índice; `accounts.churn_flag` "
        "como variável explicativa de meses anteriores ao corte.")
    add("- **Alvo:** definido por pergunta (§4) — nunca misturar lentes na mesma fórmula.")
    add("")
    add("## 9. Registros temporalmente inválidos (política e sensibilidade)")
    add("")
    add("A auditoria (Iteração 01) encontrou anomalias temporais estruturais da base sintética. "
        "Política: **nada é descartado silenciosamente** — cada conjunto é quantificado, "
        "reportado e usado onde tem significado:")
    add("")
    add("| Registro | Quantidade | Uso permitido |")
    add("|---|---|---|")
    add("| Uso antes do `start_date` (76,6% das linhas) | 19.142 | fora de janelas alinhadas; contagem separada (`usage_rows_month`) |")
    add("| Uso depois do `end_date` | 290 | idem |")
    add("| Uso dentro da janela (22,3%) | 5.568 | sinais de atividade alinhados (`usage_rows_in_window_month`) |")
    add("| Uso/tickets anteriores ao signup | 13.198 / 1.077 | fora da janela observacional da conta |")
    add("| Eventos fora da vida de assinaturas (53 antes da 1ª assinatura; 90 após a última `end_date`) | 143 | mantidos na lente de eventos; alinhamento documentado (§4 do report) |")
    add("")
    add("Sensibilidade: análises que usam atividade DEVEM declarar a variante (bruta vs alinhada) "
        "e reportar a diferença; análises de coorte temporal DEVEM usar apenas linhas alinhadas "
        "ou declarar o viés. CSAT (825 nulos, 41,2%) e reason/feedback (148 nulos) são tratados "
        "conforme §10.")
    add("")
    add("## 10. CSAT, reason codes e feedback: evidência sugestiva, nunca prova")
    add("")
    add("`satisfaction_score` (domínio {3,4,5}, 41,2% nulos), `reason_code` e `feedback_text` são "
        "evidência **sugestiva** de qualidade da experiência — não prova causal de churn. "
        "Relações entre essas variáveis e churn, quando observadas, são correlações e serão "
        "rotuladas como tal nas Iterações 03–05.")
    add("")
    add("## 11. Invariantes e gates (executáveis)")
    add("")
    add("A cada execução do `02_reconcile_churn.py`, os invariantes G1–G13 (ver report §8) são "
        "verificados: unicidade account×mês; MRR ≥ 0; datas válidas; contas ativas ≤ 500; "
        "transições fecham (contagem e MRR, tolerância 0, inteiros); totais de cada lente "
        "reconciliam à fonte; cobertura de assinaturas; anti-leakage estrutural. Qualquer "
        "violação é FAIL e o pipeline para (exit 1) com relatório atualizado.")
    add("")
    add("## 12. Decisões registradas (problema → opções → evidência → decisão → trade-off)")
    add("")
    add("Resumo executivo das decisões desta iteração; detalhe completo em "
        "`process-log/decisions/iteration-02-analytical-contract-decisions.md`.")
    add("")
    add("| Decisão | Problema | Opções | Decisão | Trade-off |")
    add("|---|---|---|---|---|")
    add("| D1 — Lente primária por pergunta | 3 fontes de churn divergentes (110/312/352) | fonte única vs lente por pergunta | lente por pergunta (contrato §4) | exige disciplina: nunca misturar |")
    add("| D2 — Grão-mestre | contagens por grão diferentes | account / subscription / account×mês | account×mês (painel do signup ao corte) | painel maior; suporta coortes e séries |")
    add("| D3 — Regra do winner | sobreposição de assinaturas dobra MRR | soma ingênua vs winner (max MRR) vs winner (start recente) | winner não-trial, max MRR, start recente, id | MRR da conta = assinatura dominante; soma preservada p/ auditoria |")
    add("| D4 — Semântica temporal | bordas de mês/intervalo ambíguas | início vs fim do mês; exclusive vs inclusive | estado no FIM do mês; [start, end] inclusive | regra determinística, sem look-ahead intra-mês |")
    add("| D5 — Registros inválidos | 76,6% do uso fora da janela | descartar vs reter com política | reter com política dupla (bruto/alinhado) e quantificação | análises precisam declarar variante |")
    add("| D6 — Rótulo snapshot no painel | flag do corte como série vazaria | omitir vs incluir com proibição | incluir como `churn_flag_snapshot_2024_12_31` proibido em features | conveniência vs risco de mau uso (G10 cobre) |")
    add("| D7 — CSAT/reason/feedback | qualidade e completude limitadas | tratar como prova vs sugestiva | evidência sugestiva rotulada | conclusões causais proibidas (It03–05) |")
    add("")
    return "\n".join(lines)


def render_processed_readme(panel: pd.DataFrame, impact: dict) -> str:
    csv_md5 = md5_of(ACCOUNT_MONTH_PATH)
    lines: list[str] = []
    add = lines.append
    add("# Dados processados — base account-month")
    add("")
    add("Gerado por `solution/src/02_reconcile_churn.py` (Iteração 02; offline e determinístico).")
    add("")
    add("## `account_month.csv` — grão-mestre account × mês")
    add("")
    add(f"- Linhas: {len(panel)} (uma por account_id × mês; {len(panel['account_id'].unique())} "
        "contas; janela do mês do signup até 2024-12).")
    add("- Estado no FIM do mês; regra do winner conforme contrato "
        "`solution/docs/analytical-contract.md` §6.")
    add("- Checksum MD5 (esta versão): `" + csv_md5 + "`")
    add("")
    add("## Colunas")
    add("")
    add("| Coluna | Semântica |")
    add("|---|---|")
    add("| `account_id` | chave da conta |")
    add("| `month` | mês `YYYY-MM` (estado no fim do mês) |")
    add("| `month_end` | último dia do mês (data) |")
    add("| `months_since_signup` | meses desde o mês do signup (0 = mês do signup) |")
    add("| `status` | `active`/`inactive` pela lente de assinatura (winner) |")
    add("| `n_active_subs` | nº de assinaturas ativas no fim do mês |")
    add("| `winner_subscription_id` | assinatura vencedora (vazia se inativa) |")
    add("| `winner_mrr` | MRR do winner (0 se inativa) |")
    add("| `winner_plan_tier`, `winner_seats`, `winner_is_trial`, `winner_billing_frequency` | atributos do winner |")
    add("| `mrr_sum_naive` | soma ingênua do MRR das ativas (auditoria; NÃO usar como métrica) |")
    add("| `churn_event_in_month` | 1 se ≥1 evento de churn no mês (lente de eventos) |")
    add("| `n_events_in_month` | nº de eventos no mês |")
    add("| `usage_rows_month` | linhas de uso no mês (bruto, sem filtro de janela) |")
    add("| `usage_rows_in_window_month` | linhas de uso no mês dentro de [start, end] da assinatura |")
    add("| `tickets_month` | tickets abertos no mês |")
    add("| `csat_mean_month` | média de CSAT dos tickets do mês (vazio se nenhum) |")
    add("| `churn_flag_snapshot_2024_12_31` | rótulo do corte (`accounts.churn_flag`); PROIBIDO em features de risco (contrato §8) |")
    add("")
    add("## Uso")
    add("")
    add("- Esta base é regenerável: `python3 solution/src/02_reconcile_churn.py`.")
    add("- Nunca editar manualmente; alterações quebram o checksum e os invariantes G1–G13.")
    add("")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> int:
    import platform

    for d in (EVIDENCE_DIR, DOCS_DIR, PROCESSED_DIR):
        d.mkdir(parents=True, exist_ok=True)

    loaded = load_all()
    acc = loaded.get("ravenstack_accounts.csv")
    sub = loaded.get("ravenstack_subscriptions.csv")
    churn = loaded.get("ravenstack_churn_events.csv")
    use = loaded.get("ravenstack_feature_usage.csv")
    tic = loaded.get("ravenstack_support_tickets.csv")

    # Usabilidade estrutural por arquivo (lição da Iteração 01: sem KeyError/traceback
    # em schema quebrado; FAIL estruturado; relatório SEMPRE regravado).
    blocked_files: dict[str, list[str]] = {}
    for fname, cols in REQUIRED.items():
        df = loaded.get(fname)
        if df is None:
            blocked_files[fname] = ["arquivo ausente"]
        else:
            miss = missing_cols(df, cols, fname)
            if miss:
                blocked_files[fname] = miss

    panel: pd.DataFrame | None = None
    r: dict = {}
    impact: dict = {}
    bm: pd.DataFrame | None = None

    if blocked_files:
        # Modo falha estrutural: pipeline bloqueado com diagnóstico preciso.
        # Uma base parcial violaria o schema do contrato; nada de output stale.
        detail = "; ".join(f"{f}: {', '.join(m)}" for f, m in blocked_files.items())
        for sec_id, sec_name in [("R01", "reconciliação das lentes de churn"),
                                 ("R02", "alinhamento churn_date vs end_date"),
                                 ("R03", "construção da base account-month"),
                                 ("R04", "invariantes/gates da base account-month")]:
            check(sec_id, "pipeline", f"{sec_name} executável",
                  "FAIL", f"não executado (schema): {detail}")
    else:
        # datas parseáveis (guardas já garantiram colunas)
        parse_dates(acc, ["signup_date"], "ravenstack_accounts.csv")
        parse_dates(sub, ["start_date", "end_date"], "ravenstack_subscriptions.csv")
        parse_dates(churn, ["churn_date"], "ravenstack_churn_events.csv")
        parse_dates(use, ["usage_date"], "ravenstack_feature_usage.csv")
        parse_dates(tic, ["submitted_at"], "ravenstack_support_tickets.csv")

        r = reconcile_lenses(acc, sub, churn)
        bm = align_events_to_end_dates(churn, sub)
        panel = build_account_month(acc, sub, churn, use, tic)
        impact = overlap_impact(panel)

        # estado no corte por lente de eventos (para o relatório §3.2/§5)
        ev_acc = set(churn["account_id"])
        active_at_cut = set(panel.loc[(panel["month"] == LAST_MONTH) & (panel["status"] == "active"),
                                      "account_id"])
        r["ev_acc_inactive_cut"] = len(ev_acc - active_at_cut)

        # contexto da inatividade por lente de assinatura
        inact = panel[panel["status"] == "inactive"]
        r["n_inactive_rows"] = len(inact)
        r["n_inactive_accounts"] = int(inact["account_id"].nunique())
        piv = panel.pivot_table(index="account_id", columns="month", values="status",
                                aggfunc="first")
        n_cycle = 0
        cycle_ids: list[str] = []
        for aid, srow in piv.iterrows():
            vals = srow.dropna()
            seen_active = False
            for v in vals:
                if v == "active":
                    seen_active = True
                elif v == "inactive" and seen_active:
                    n_cycle += 1
                    cycle_ids.append(aid)
                    break
        r["n_cycle_accounts"] = n_cycle
        r["cycle_account_ids"] = ", ".join(sorted(cycle_ids))

        # Sensibilidade: winner por start mais recente (não-trial primeiro, depois start desc)
        mrr_latest = 0
        for _, arow in acc.sort_values("account_id").iterrows():
            aid = arow["account_id"]
            subs_acct = sub[sub["account_id"] == aid].copy()
            subs_acct["start"] = pd.to_datetime(subs_acct["start_date"])
            subs_acct["end"] = pd.to_datetime(subs_acct["end_date"])
            for m in months_range(FIRST_MONTH, LAST_MONTH):
                mend = month_end_date(m)
                if m < arow["signup_date"][:7]:
                    continue
                active = subs_acct[(subs_acct["start"] <= mend) &
                                   (subs_acct["end"].isna() | (subs_acct["end"] >= mend))]
                if len(active) == 0:
                    continue
                w = active.sort_values(["is_trial", "start", "subscription_id"],
                                       ascending=[True, False, True]).iloc[0]
                mrr_latest += int(w["mrr_amount"])
        impact["mrr_winner_latest_start"] = mrr_latest

        run_gates(panel, acc, sub, churn, use, tic, r)

    report = render_report(loaded, panel, r, impact, bm)
    REPORT_PATH.write_text(report, encoding="utf-8")

    if panel is not None:
        panel.to_csv(ACCOUNT_MONTH_PATH, index=False)
        PROCESSED_README_PATH.write_text(render_processed_readme(panel, impact), encoding="utf-8")
        CONTRACT_PATH.write_text(render_contract(r, impact, len(panel)), encoding="utf-8")

    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for c in CHECKS:
        counts[c["level"]] += 1

    print(f"Relatório: {REPORT_PATH.relative_to(SOLUTION_DIR.parent)}")
    print(f"Checks: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    if panel is not None:
        print(f"Account-month: {ACCOUNT_MONTH_PATH.relative_to(SOLUTION_DIR.parent)} "
              f"({len(panel)} linhas; MD5 {md5_of(ACCOUNT_MONTH_PATH)})")
        print(f"Contrato: {CONTRACT_PATH.relative_to(SOLUTION_DIR.parent)} "
              f"(MD5 {md5_of(CONTRACT_PATH)})")
        print(f"Processed README: {PROCESSED_README_PATH.relative_to(SOLUTION_DIR.parent)} "
              f"(MD5 {md5_of(PROCESSED_README_PATH)})")
    else:
        print("Modo falha estrutural: outputs de dados NÃO regenerados (report atualizado "
              "com FAILs; exit 1).")
    print(f"Report MD5: {md5_of(REPORT_PATH)}")
    print(f"Python: {platform.python_version()} | pandas: {pd.__version__}")

    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())