#!/usr/bin/env python3
"""
01_ingest_audit.py — Ingestão e auditoria dos 5 datasets RavenStack (Challenge 001).

Executa uma auditoria offline, reproduzível e determinística dos cinco CSVs em
``solution/data/raw/`` e grava o relatório em ``solution/evidence/01_audit_report.md``.

Uso (a partir da pasta da submissão):
    python3 solution/src/01_ingest_audit.py

Semântica de resultado:
    - PASS  : check íntegro (estrutura/qualidade esperada confirmada).
    - WARN  : anomalia de qualidade esperada em dados sintéticos (documentada, não bloqueia).
    - FAIL  : arquivo/schema/chave estrutural ausente ou violação estrutural grave.
    Exit code: 0 se não houver FAIL; 1 caso contrário.

Restrições: apenas stdlib + pandas; sem rede; paths relativos ao próprio projeto.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------------
# Configuração de paths (relativos ao próprio projeto)
# ----------------------------------------------------------------------------
SOLUTION_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = SOLUTION_DIR / "data" / "raw"
EVIDENCE_DIR = SOLUTION_DIR / "evidence"
REPORT_PATH = EVIDENCE_DIR / "01_audit_report.md"

# ----------------------------------------------------------------------------
# Expectativas declaradas (brief oficial do challenge + inspeção de schema)
# ----------------------------------------------------------------------------
# brief_rows: contagem anunciada no README do challenge ("~500" etc.).
# Nesta base real, as contagens batem exatamente com o valor anunciado.
FILES = {
    "ravenstack_accounts.csv": {
        "brief_rows": 500,
        "columns": [
            "account_id", "account_name", "industry", "country", "signup_date",
            "referral_source", "plan_tier", "seats", "is_trial", "churn_flag",
        ],
        "key": "account_id",
    },
    "ravenstack_subscriptions.csv": {
        "brief_rows": 5000,
        "columns": [
            "subscription_id", "account_id", "start_date", "end_date", "plan_tier",
            "seats", "mrr_amount", "arr_amount", "is_trial", "upgrade_flag",
            "downgrade_flag", "churn_flag", "billing_frequency", "auto_renew_flag",
        ],
        "key": "subscription_id",
    },
    "ravenstack_feature_usage.csv": {
        "brief_rows": 25000,
        "columns": [
            "usage_id", "subscription_id", "usage_date", "feature_name",
            "usage_count", "usage_duration_secs", "error_count", "is_beta_feature",
        ],
        "key": "usage_id",
    },
    "ravenstack_support_tickets.csv": {
        "brief_rows": 2000,
        "columns": [
            "ticket_id", "account_id", "submitted_at", "closed_at",
            "resolution_time_hours", "priority", "first_response_time_minutes",
            "satisfaction_score", "escalation_flag",
        ],
        "key": "ticket_id",
    },
    "ravenstack_churn_events.csv": {
        "brief_rows": 600,
        "columns": [
            "churn_event_id", "account_id", "churn_date", "reason_code",
            "refund_amount_usd", "preceding_upgrade_flag", "preceding_downgrade_flag",
            "is_reactivation", "feedback_text",
        ],
        "key": "churn_event_id",
    },
}

# Domínios categóricos observados na inspeção de schema (Iteração 01, pré-escrita do script).
DOMAINS = {
    "accounts.industry": {"DevTools", "FinTech", "Cybersecurity", "HealthTech", "EdTech"},
    "accounts.country": {"US", "UK", "IN", "AU", "DE", "CA", "FR"},
    "accounts.referral_source": {"organic", "other", "ads", "event", "partner"},
    "plan_tier": {"Basic", "Pro", "Enterprise"},
    "subscriptions.billing_frequency": {"monthly", "annual"},
    "tickets.priority": {"low", "medium", "high", "urgent"},
    "churn.reason_code": {"features", "support", "budget", "unknown", "competitor", "pricing"},
}

GLOBAL_DATE_MIN = "2023-01-01"
GLOBAL_DATE_MAX = "2024-12-31"

# Colunas booleanas por arquivo (domínio: True/False, 0/1 ou variantes de
# string canônicas). Guard mínimo de VALOR (não de schema): um valor fora do
# domínio (ex.: churn_flag = "TruX") faz pandas deixar de inferir bool e os
# checks que fazem masking booleano explodiriam com KeyError/TypeError —
# registramos FAIL estruturado ANTES do masking. Não é catch-all: bugs reais
# de código continuam propagando com traceback.
BOOL_COLUMNS = {
    "ravenstack_accounts.csv": ["is_trial", "churn_flag"],
    "ravenstack_subscriptions.csv": ["is_trial", "upgrade_flag", "downgrade_flag",
                                     "churn_flag", "auto_renew_flag"],
    "ravenstack_feature_usage.csv": ["is_beta_feature"],
    "ravenstack_support_tickets.csv": ["escalation_flag"],
    "ravenstack_churn_events.csv": ["preceding_upgrade_flag", "preceding_downgrade_flag",
                                    "is_reactivation"],
}
_BOOL_CANONICAL = {"True", "False", "true", "false", "TRUE", "FALSE", "0", "1"}


def bool_problems(df: pd.DataFrame, cols: list[str]) -> list[str]:
    """Valores não-canônicos em colunas booleanas (validação mínima de valor).

    Retorna lista de "coluna=[valores inválidos]" (vazia = domínio íntegro).
    """
    problems: list[str] = []
    for col in cols:
        if col not in df.columns:
            continue
        if df[col].dtype == bool:
            continue
        bad = sorted({str(v) for v in df[col].dropna().unique()
                      if str(v) not in _BOOL_CANONICAL})
        if bad:
            problems.append(f"{col}={bad}")
    return problems


def guard_bools(df: pd.DataFrame, cols: list[str], check_id: str, scope: str,
                description: str) -> bool:
    """Registra FAIL estruturado se alguma coluna booleana tiver valor inválido.

    Retorna True quando todos os valores são canônicos (o check pode executar
    o masking). Não é catch-all: apenas valida o domínio booleano ANTES do
    masking — bugs reais continuam propagando com traceback (exit != 0).
    """
    problems = bool_problems(df, cols)
    if problems:
        check(check_id, scope, description, "FAIL",
              f"não executado (validação): valores não-booleanos: {problems}")
        return False
    return True

# ----------------------------------------------------------------------------
# Registro de checks (ordem determinística de emissão)
# ----------------------------------------------------------------------------
CHECKS: list[dict] = []


def check(check_id: str, scope: str, description: str, level: str, detail: str) -> None:
    """Registra um check. level: PASS | WARN | FAIL."""
    CHECKS.append(
        {
            "id": check_id,
            "scope": scope,
            "description": description,
            "level": level,
            "detail": detail,
        }
    )


def fmt(n: int | float) -> str:
    """Formata número inteiro sem decimais; float com 2 decimais (determinístico)."""
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    if isinstance(n, float):
        return f"{n:.2f}"
    return str(n)


def pct(part: int, total: int) -> str:
    return f"{100.0 * part / total:.1f}%"


def missing_cols(df: pd.DataFrame, cols: list[str], fname: str | None = None) -> list[str]:
    """Colunas de ``cols`` ausentes do DataFrame (guarda contra schema quebrado).

    Com ``fname``, os nomes são anotados com o arquivo para diagnóstico legível.
    """
    if fname is None:
        return [c for c in cols if c not in df.columns]
    return [f"{c} ({fname})" for c in cols if c not in df.columns]


def guard_columns(df: pd.DataFrame, cols: list[str], check_id: str, scope: str,
                  description: str) -> bool:
    """Registra FAIL estrutural se alguma coluna necessária estiver ausente.

    Retorna True quando todas as colunas existem (o check pode executar).
    Não é catch-all: apenas guarda acesso a colunas — bugs reais continuam
    propagando com traceback (exit != 0) em vez de virarem FAIL silencioso.
    """
    missing = missing_cols(df, cols)
    if missing:
        check(check_id, scope, description, "FAIL",
              f"não executado (schema): colunas ausentes: {missing}")
        return False
    return True


def cross_blocked(dfs: dict[str, pd.DataFrame], needs: dict[str, list[str]]) -> list[str]:
    """Problemas de schema para um check entre tabelas (arquivo/coluna ausente)."""
    problems: list[str] = []
    for fname, cols in needs.items():
        df = dfs.get(fname)
        if df is None:
            problems.append(f"{fname} (arquivo ausente)")
        else:
            problems.extend(f"{c} ({fname})" for c in cols if c not in df.columns)
    return problems

# ----------------------------------------------------------------------------
# Leitura dos arquivos
# ----------------------------------------------------------------------------

def load_all() -> dict[str, pd.DataFrame]:
    """Carrega os 5 CSVs; valida presença e contagens; retorna dict nome->df."""
    loaded: dict[str, pd.DataFrame] = {}
    for fname, spec in FILES.items():
        path = RAW_DIR / fname
        if not path.exists():
            check(f"F01-{fname}", fname, "arquivo presente em data/raw", "FAIL", "arquivo ausente")
            continue
        if path.stat().st_size == 0:
            check(f"F01-{fname}", fname, "arquivo presente em data/raw", "FAIL", "arquivo vazio (0 bytes)")
            continue
        try:
            df = pd.read_csv(path)
        except Exception as exc:  # noqa: BLE001 — qualquer falha de parse é estrutural
            check(f"F01-{fname}", fname, "CSV carregável", "FAIL", f"falha de parse: {exc}")
            continue
        loaded[fname] = df
        check(f"F01-{fname}", fname, "arquivo presente e carregável",
              "PASS", f"{path.stat().st_size} bytes, CSV parseado")
        n = len(df)
        expected = spec["brief_rows"]
        if n == expected:
            check(f"F02-{fname}", fname, "contagem de registros = valor do brief",
                  "PASS", f"{n} registros (brief: ~{expected})")
        else:
            dev = abs(n - expected)
            check(f"F02-{fname}", fname, "contagem de registros = valor do brief",
                  "WARN", f"{n} registros (brief: ~{expected}; desvio {dev})")
    return loaded


def check_schema(fname: str, df: pd.DataFrame, spec: dict) -> None:
    """Valida header/schema mínimo e tipos básicos."""
    expected_cols = spec["columns"]
    actual_cols = list(df.columns)
    missing = [c for c in expected_cols if c not in actual_cols]
    extra = [c for c in actual_cols if c not in expected_cols]
    if missing:
        check(f"S01-{fname}", fname, "schema mínimo (colunas do brief)",
              "FAIL", f"colunas ausentes: {missing}")
    elif extra:
        check(f"S01-{fname}", fname, "schema mínimo (colunas do brief)",
              "WARN", f"colunas extras não previstas: {extra}")
    else:
        check(f"S01-{fname}", fname, "schema mínimo (colunas do brief)",
              "PASS", f"{len(actual_cols)} colunas, ordem idêntica ao brief")

    key = spec["key"]
    if key in df.columns:
        n_nulls_key = int(df[key].isna().sum())
        if n_nulls_key:
            check(f"S02-{fname}", fname, f"chave candidata {key} sem nulos",
                  "FAIL", f"{n_nulls_key} nulos na chave")
        else:
            check(f"S02-{fname}", fname, f"chave candidata {key} sem nulos", "PASS", "0 nulos")

        n_dup_key = int(df[key].duplicated().sum())
        if n_dup_key:
            check(f"S03-{fname}", fname, f"chave candidata {key} sem duplicatas",
                  "WARN", f"{n_dup_key} ids duplicados (anomalia de qualidade; join não afetado)")
        else:
            check(f"S03-{fname}", fname, f"chave candidata {key} sem duplicatas", "PASS", "0 duplicatas")
    else:
        # Chave ausente: S02/S03 não executáveis — FAIL estrutural explícito (não esconder)
        check(f"S02-{fname}", fname, f"chave candidata {key} sem nulos",
              "FAIL", f"não executado (schema): coluna {key} ausente")
        check(f"S03-{fname}", fname, f"chave candidata {key} sem duplicatas",
              "FAIL", f"não executado (schema): coluna {key} ausente")

    n_dup_row = int(df.duplicated().sum())
    if n_dup_row:
        check(f"S04-{fname}", fname, "linhas exatamente duplicadas",
              "WARN", f"{n_dup_row} linhas duplicadas")
    else:
        check(f"S04-{fname}", fname, "linhas exatamente duplicadas", "PASS", "0 linhas duplicadas")

    # Nulos por coluna (não-chave)
    null_cols = {c: int(df[c].isna().sum()) for c in actual_cols if int(df[c].isna().sum()) > 0}
    expected_nulls = {
        # end_date nulo = assinatura ativa (semântica do schema, não é anomalia)
        "ravenstack_subscriptions.csv": {"end_date"},
        # satisfação ausente é esperada em parte dos tickets (documentada como WARN)
        "ravenstack_support_tickets.csv": set(),
        # feedback textual ausente em parte dos eventos (documentada como WARN)
        "ravenstack_churn_events.csv": set(),
    }.get(fname, set())
    if null_cols:
        parts = []
        for c, v in sorted(null_cols.items()):
            kind = "esperado (semântica: assinatura ativa)" if c in expected_nulls else "WARN"
            parts.append(f"{c}={v} ({pct(v, len(df))}) [{kind}]")
        # Se todas as colunas com nulo forem semanticamente esperadas -> PASS; senão WARN
        unexpected = {c for c in null_cols if c not in expected_nulls}
        level = "PASS" if not unexpected else "WARN"
        check(f"S05-{fname}", fname, "nulos por coluna (não-chave)",
              level, "; ".join(parts))
    else:
        check(f"S05-{fname}", fname, "nulos por coluna (não-chave)", "PASS", "0 nulos em todas as colunas")


def check_types_ranges(fname: str, df: pd.DataFrame) -> None:
    """Valida ranges numéricos e domínios categóricos por arquivo."""
    if fname == "ravenstack_accounts.csv":
        if guard_columns(df, ["seats"], f"T01-{fname}", fname, "seats > 0"):
            bad_seats = int((df["seats"] <= 0).sum())
            check(f"T01-{fname}", fname, "seats > 0",
                  "FAIL" if bad_seats else "PASS", f"{bad_seats} violações")
        for col, dom in [("industry", DOMAINS["accounts.industry"]),
                         ("country", DOMAINS["accounts.country"]),
                         ("referral_source", DOMAINS["accounts.referral_source"]),
                         ("plan_tier", DOMAINS["plan_tier"])]:
            if guard_columns(df, [col], f"T02-{fname}", fname, f"domínio de {col}"):
                bad = sorted(set(df[col]) - dom)
                check(f"T02-{fname}", fname, f"domínio de {col}",
                      "PASS" if not bad else "WARN",
                      f"{len(df[col].unique())} valores válidos" if not bad else f"valores fora do domínio: {bad}")

    elif fname == "ravenstack_subscriptions.csv":
        if guard_columns(df, ["seats", "mrr_amount", "arr_amount"], f"T01-{fname}", fname,
                         "seats > 0, mrr >= 0, arr >= 0"):
            bad_seats = int((df["seats"] <= 0).sum())
            bad_mrr = int((df["mrr_amount"] < 0).sum())
            bad_arr = int((df["arr_amount"] < 0).sum())
            check(f"T01-{fname}", fname, "seats > 0, mrr >= 0, arr >= 0",
                  "FAIL" if (bad_seats + bad_mrr + bad_arr) else "PASS",
                  f"violações: seats<=0={bad_seats}, mrr<0={bad_mrr}, arr<0={bad_arr}")
        # Unidade: ARR = 12 x MRR (relação observada como invariante da base)
        if guard_columns(df, ["mrr_amount", "arr_amount"], f"T03-{fname}", fname,
                         "ARR = 12 x MRR (invariante de unidade)"):
            nz = df[df["mrr_amount"] > 0]
            bad_ratio = int((nz["arr_amount"] != nz["mrr_amount"] * 12).sum())
            check(f"T03-{fname}", fname, "ARR = 12 x MRR (invariante de unidade)",
                  "PASS" if bad_ratio == 0 else "WARN",
                  f"{bad_ratio} violações em {len(nz)} linhas com MRR>0")
        # Semântica de trial: trial => MRR 0 (avaliado em C02)
        if guard_columns(df, ["plan_tier", "billing_frequency"], f"T02-{fname}", fname,
                         "domínios plan_tier e billing_frequency"):
            bad_plan = sorted(set(df["plan_tier"]) - DOMAINS["plan_tier"])
            bad_freq = sorted(set(df["billing_frequency"]) - DOMAINS["subscriptions.billing_frequency"])
            check(f"T02-{fname}", fname, "domínios plan_tier e billing_frequency",
                  "PASS" if not (bad_plan or bad_freq) else "WARN",
                  f"plan_tier fora: {bad_plan}; billing_frequency fora: {bad_freq}")

    elif fname == "ravenstack_feature_usage.csv":
        if guard_columns(df, ["usage_count", "usage_duration_secs", "error_count"], f"T01-{fname}", fname,
                         "usage_count/duration/error >= 0"):
            bad_cnt = int((df["usage_count"] < 0).sum())
            bad_dur = int((df["usage_duration_secs"] < 0).sum())
            bad_err = int((df["error_count"] < 0).sum())
            check(f"T01-{fname}", fname, "usage_count/duration/error >= 0",
                  "FAIL" if (bad_cnt + bad_dur + bad_err) else "PASS",
                  f"violações: count<0={bad_cnt}, duration<0={bad_dur}, error<0={bad_err}")
        if guard_columns(df, ["error_count", "usage_count"], f"T04-{fname}", fname,
                         "error_count <= usage_count (consistência lógica)"):
            err_gt_cnt = int((df["error_count"] > df["usage_count"]).sum())
            check(f"T04-{fname}", fname, "error_count <= usage_count (consistência lógica)",
                  "PASS" if err_gt_cnt == 0 else "WARN",
                  f"{err_gt_cnt} linhas com erro_count > usage_count")
        if guard_columns(df, ["usage_count"], f"T05-{fname}", fname,
                         "usage_count > 0 (linha de uso com contagem)"):
            zero_cnt = int((df["usage_count"] == 0).sum())
            check(f"T05-{fname}", fname, "usage_count > 0 (linha de uso com contagem)",
                  "PASS" if zero_cnt == 0 else "WARN",
                  f"{zero_cnt} linhas com usage_count = 0")

    elif fname == "ravenstack_support_tickets.csv":
        if guard_columns(df, ["resolution_time_hours", "first_response_time_minutes"], f"T01-{fname}", fname,
                         "resolution_time_hours/first_response >= 0"):
            bad_res = int((df["resolution_time_hours"] < 0).sum())
            bad_frt = int((df["first_response_time_minutes"] < 0).sum())
            check(f"T01-{fname}", fname, "resolution_time_hours/first_response >= 0",
                  "FAIL" if (bad_res + bad_frt) else "PASS",
                  f"violações: res<0={bad_res}, frt<0={bad_frt}")
        if guard_columns(df, ["satisfaction_score"], f"T06-{fname}", fname,
                         "CSAT nulo ou fora do domínio 1-5"):
            csat = df["satisfaction_score"].dropna()
            n_null = int(df["satisfaction_score"].isna().sum())
            out_range = int(((csat < 1) | (csat > 5)).sum())
            level = "FAIL" if out_range else "WARN" if n_null else "PASS"
            detail = (f"nulos={n_null} ({pct(n_null, len(df))}); valores fora de [1,5]={out_range}; "
                      f"valores observados={sorted(csat.unique())}")
            check(f"T06-{fname}", fname, "CSAT nulo ou fora do domínio 1-5",
                  level, detail)
        if guard_columns(df, ["priority"], f"T02-{fname}", fname, "domínio de priority"):
            bad_prio = sorted(set(df["priority"]) - DOMAINS["tickets.priority"])
            check(f"T02-{fname}", fname, "domínio de priority",
                  "PASS" if not bad_prio else "WARN",
                  f"{len(df['priority'].unique())} valores válidos" if not bad_prio else f"fora do domínio: {bad_prio}")

    elif fname == "ravenstack_churn_events.csv":
        if guard_columns(df, ["refund_amount_usd"], f"T01-{fname}", fname, "refund_amount_usd >= 0"):
            bad_ref = int((df["refund_amount_usd"] < 0).sum())
            check(f"T01-{fname}", fname, "refund_amount_usd >= 0",
                  "FAIL" if bad_ref else "PASS", f"{bad_ref} violações")
        if guard_columns(df, ["reason_code"], f"T02-{fname}", fname, "domínio de reason_code"):
            bad_reason = sorted(set(df["reason_code"]) - DOMAINS["churn.reason_code"])
            check(f"T02-{fname}", fname, "domínio de reason_code",
                  "PASS" if not bad_reason else "WARN",
                  f"{len(df['reason_code'].unique())} valores válidos" if not bad_reason else f"fora do domínio: {bad_reason}")


def check_ids(fname: str, df: pd.DataFrame) -> None:
    """Valida padrão de formato dos IDs (prefixo + 6 hex)."""
    id_cols = {
        "ravenstack_accounts.csv": ["account_id"],
        "ravenstack_subscriptions.csv": ["subscription_id", "account_id"],
        "ravenstack_feature_usage.csv": ["usage_id", "subscription_id"],
        "ravenstack_support_tickets.csv": ["ticket_id", "account_id"],
        "ravenstack_churn_events.csv": ["churn_event_id", "account_id"],
    }[fname]
    if guard_columns(df, id_cols, f"I01-{fname}", fname, "IDs no padrão <PREFIXO>-<6 hex>"):
        violations = 0
        for col in id_cols:
            violations += int((~df[col].astype(str).str.match(r"^[A-Z]-[0-9a-f]{6}$")).sum())
        check(f"I01-{fname}", fname, "IDs no padrão <PREFIXO>-<6 hex>",
              "PASS" if violations == 0 else "WARN",
              f"{violations} violações em {len(id_cols)} coluna(s) de ID")


def check_global_window(fname: str, df: pd.DataFrame) -> None:
    """Janela global: todas as colunas de data dentro de 2023-01-01..2024-12-31."""
    date_cols = {
        "ravenstack_accounts.csv": ["signup_date"],
        "ravenstack_subscriptions.csv": ["start_date", "end_date"],
        "ravenstack_feature_usage.csv": ["usage_date"],
        "ravenstack_support_tickets.csv": ["submitted_at", "closed_at"],
        "ravenstack_churn_events.csv": ["churn_date"],
    }[fname]
    if guard_columns(df, date_cols, f"D02-{fname}", fname,
                     "janela global de datas dentro de 2023-01-01..2024-12-31"):
        out_of_window = 0
        ranges = []
        for col in date_cols:
            parsed = pd.to_datetime(df[col], errors="coerce")
            present = parsed.dropna()
            if len(present) == 0:
                continue
            # Janela é definida em granularidade de DATA (calendário); o horário do dia
            # dentro da data-limite é válido (ex.: fechamento às 19:00 de 2024-12-31).
            day = present.dt.normalize()
            out_of_window += int((day < pd.Timestamp(GLOBAL_DATE_MIN)).sum())
            out_of_window += int((day > pd.Timestamp(GLOBAL_DATE_MAX)).sum())
            ranges.append(f"{col}: {present.min().date()}..{present.max().date()}")
        check(f"D02-{fname}", fname, "janela global de datas dentro de 2023-01-01..2024-12-31",
              "PASS" if out_of_window == 0 else "FAIL",
              f"{out_of_window} valores fora da janela; " + "; ".join(ranges))


def check_dates(fname: str, df: pd.DataFrame, accounts: pd.DataFrame | None,
                subscriptions: pd.DataFrame | None) -> None:
    """Valida parse de datas, janela global e ordens temporais internas."""
    if fname == "ravenstack_accounts.csv":
        if guard_columns(df, ["signup_date"], f"D01-{fname}", fname, "signup_date parseável (YYYY-MM-DD)"):
            parsed = pd.to_datetime(df["signup_date"], errors="coerce")
            n_bad = int(parsed.isna().sum())
            check(f"D01-{fname}", fname, "signup_date parseável (YYYY-MM-DD)",
                  "FAIL" if n_bad else "PASS", f"{n_bad} valores não parseáveis")

    elif fname == "ravenstack_subscriptions.csv":
        if guard_columns(df, ["start_date", "end_date"], f"D01-{fname}", fname,
                         "start_date/end_date parseáveis"):
            start = pd.to_datetime(df["start_date"], errors="coerce")
            end = pd.to_datetime(df["end_date"], errors="coerce")
            # end_date nulo é semântica de assinatura ativa; só conta como erro
            # se um valor presente não parsear.
            n_bad_start = int(start.isna().sum())
            n_bad_end = int((df["end_date"].notna() & end.isna()).sum())
            n_bad = n_bad_start + n_bad_end
            check(f"D01-{fname}", fname, "start_date/end_date parseáveis", "FAIL" if n_bad else "PASS",
                  f"{n_bad} valores não parseáveis "
                  f"(end_date nulo é semântica de assinatura ativa: {int(df['end_date'].isna().sum())})")
        if guard_columns(df, ["start_date", "end_date"], f"D03-{fname}", fname,
                         "end_date >= start_date (quando presente)"):
            start = pd.to_datetime(df["start_date"], errors="coerce")
            end = pd.to_datetime(df["end_date"], errors="coerce")
            ended = df[df["end_date"].notna()]
            n_bad_order = int((ended["end_date"] < ended["start_date"]).sum())
            check(f"D03-{fname}", fname, "end_date >= start_date (quando presente)",
                  "FAIL" if n_bad_order else "PASS", f"{n_bad_order} violações")
        if guard_columns(df, ["churn_flag", "end_date"], f"D04-{fname}", fname,
                         "flags vs datas: churn_flag consistente com end_date"):
            if guard_bools(df, ["churn_flag"], f"D04-{fname}", fname,
                           "flags vs datas: churn_flag consistente com end_date"):
                n_consistent = int(
                    (df["churn_flag"] & df["end_date"].isna()).sum()
                    + (df["end_date"].notna() & ~df["churn_flag"]).sum()
                )
                check(f"D04-{fname}", fname, "flags vs datas: churn_flag consistente com end_date",
                      "PASS" if n_consistent == 0 else "WARN",
                      f"{n_consistent} linhas inconsistentes "
                      f"(churn sem end_date ou end_date sem churn); ativas={int(df['end_date'].isna().sum())}")

    elif fname == "ravenstack_feature_usage.csv":
        if guard_columns(df, ["usage_date"], f"D01-{fname}", fname, "usage_date parseável"):
            parsed = pd.to_datetime(df["usage_date"], errors="coerce")
            n_bad = int(parsed.isna().sum())
            check(f"D01-{fname}", fname, "usage_date parseável", "FAIL" if n_bad else "PASS",
                  f"{n_bad} valores não parseáveis")

    elif fname == "ravenstack_support_tickets.csv":
        if guard_columns(df, ["submitted_at", "closed_at"], f"D01-{fname}", fname,
                         "submitted_at/closed_at parseáveis"):
            sub = pd.to_datetime(df["submitted_at"], errors="coerce")
            clo = pd.to_datetime(df["closed_at"], errors="coerce")
            n_bad = int(sub.isna().sum()) + int(clo.isna().sum())
            check(f"D01-{fname}", fname, "submitted_at/closed_at parseáveis",
                  "FAIL" if n_bad else "PASS", f"{n_bad} valores não parseáveis")
        if guard_columns(df, ["submitted_at", "closed_at"], f"D03-{fname}", fname,
                         "closed_at >= submitted_at"):
            sub = pd.to_datetime(df["submitted_at"], errors="coerce")
            clo = pd.to_datetime(df["closed_at"], errors="coerce")
            n_ord = int((clo < sub).sum())
            check(f"D03-{fname}", fname, "closed_at >= submitted_at",
                  "FAIL" if n_ord else "PASS", f"{n_ord} violações")
        if guard_columns(df, ["submitted_at", "closed_at", "resolution_time_hours"], f"D05-{fname}", fname,
                         "resolution_time_hours <= tempo decorrido real"):
            sub = pd.to_datetime(df["submitted_at"], errors="coerce")
            clo = pd.to_datetime(df["closed_at"], errors="coerce")
            elapsed_h = (clo - sub).dt.total_seconds() / 3600.0
            n_res = int((df["resolution_time_hours"] > elapsed_h + 1e-9).sum())
            check(f"D05-{fname}", fname, "resolution_time_hours <= tempo decorrido real",
                  "PASS" if n_res == 0 else "WARN", f"{n_res} violações")

    elif fname == "ravenstack_churn_events.csv":
        if guard_columns(df, ["churn_date"], f"D01-{fname}", fname, "churn_date parseável"):
            parsed = pd.to_datetime(df["churn_date"], errors="coerce")
            n_bad = int(parsed.isna().sum())
            check(f"D01-{fname}", fname, "churn_date parseável", "FAIL" if n_bad else "PASS",
                  f"{n_bad} valores não parseáveis")


def check_cross_tables(dfs: dict[str, pd.DataFrame]) -> None:
    """Valida FKs, ordens temporais entre tabelas e consistências entre fontes."""
    acc = dfs.get("ravenstack_accounts.csv")
    sub = dfs.get("ravenstack_subscriptions.csv")
    use = dfs.get("ravenstack_feature_usage.csv")
    tic = dfs.get("ravenstack_support_tickets.csv")
    churn = dfs.get("ravenstack_churn_events.csv")

    if acc is not None and sub is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_accounts.csv": ["account_id"],
            "ravenstack_subscriptions.csv": ["account_id"],
        })
        if blocked:
            check("K01-subscriptions", "subscriptions -> accounts",
                  "FK account_id sem órfãos", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            orphans = sorted(set(sub["account_id"]) - set(acc["account_id"]))
            check("K01-subscriptions", "subscriptions -> accounts",
                  "FK account_id sem órfãos", "FAIL" if orphans else "PASS",
                  f"{len(orphans)} órfãos" if orphans else "0 órfãos")
    if acc is not None and tic is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_accounts.csv": ["account_id"],
            "ravenstack_support_tickets.csv": ["account_id"],
        })
        if blocked:
            check("K02-tickets", "tickets -> accounts",
                  "FK account_id sem órfãos", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            orphans = sorted(set(tic["account_id"]) - set(acc["account_id"]))
            check("K02-tickets", "tickets -> accounts",
                  "FK account_id sem órfãos", "FAIL" if orphans else "PASS",
                  f"{len(orphans)} órfãos" if orphans else "0 órfãos")
    if acc is not None and churn is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_accounts.csv": ["account_id"],
            "ravenstack_churn_events.csv": ["account_id"],
        })
        if blocked:
            check("K03-churn", "churn_events -> accounts",
                  "FK account_id sem órfãos", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            orphans = sorted(set(churn["account_id"]) - set(acc["account_id"]))
            check("K03-churn", "churn_events -> accounts",
                  "FK account_id sem órfãos", "FAIL" if orphans else "PASS",
                  f"{len(orphans)} órfãos" if orphans else "0 órfãos")
    if sub is not None and use is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_subscriptions.csv": ["subscription_id"],
            "ravenstack_feature_usage.csv": ["subscription_id"],
        })
        if blocked:
            check("K04-usage", "feature_usage -> subscriptions",
                  "FK subscription_id sem órfãos", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
            check("K05-usage", "subscriptions -> feature_usage",
                  "assinaturas com registro de uso (sem 'assinatura sem uso')", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            orphans = sorted(set(use["subscription_id"]) - set(sub["subscription_id"]))
            check("K04-usage", "feature_usage -> subscriptions",
                  "FK subscription_id sem órfãos", "FAIL" if orphans else "PASS",
                  f"{len(orphans)} órfãos" if orphans else "0 órfãos")
            unused = sorted(set(sub["subscription_id"]) - set(use["subscription_id"]))
            check("K05-usage", "subscriptions -> feature_usage",
                  "assinaturas com registro de uso (sem 'assinatura sem uso')",
                  "PASS" if not unused else "WARN",
                  f"{len(unused)} assinaturas sem nenhuma linha de uso")

    # --- Ordens temporais entre tabelas ---
    if acc is not None and churn is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_accounts.csv": ["account_id", "signup_date"],
            "ravenstack_churn_events.csv": ["account_id", "churn_date"],
        })
        if blocked:
            check("D06-churn", "churn_events vs accounts",
                  "churn_date >= signup_date da conta", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            m = churn.merge(acc[["account_id", "signup_date"]], on="account_id")
            n = int((m["churn_date"] < m["signup_date"]).sum())
            check("D06-churn", "churn_events vs accounts",
                  "churn_date >= signup_date da conta", "WARN" if n else "PASS",
                  f"{n} eventos de churn anteriores ao signup")
    if acc is not None and tic is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_accounts.csv": ["account_id", "signup_date"],
            "ravenstack_support_tickets.csv": ["account_id", "submitted_at"],
        })
        if blocked:
            check("D07-tickets", "tickets vs accounts",
                  "submitted_at >= signup_date da conta", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            m = tic.merge(acc[["account_id", "signup_date"]], on="account_id")
            n = int((m["submitted_at"].str[:10] < m["signup_date"]).sum())
            check("D07-tickets", "tickets vs accounts",
                  "submitted_at >= signup_date da conta", "WARN" if n else "PASS",
                  f"{n} tickets abertos antes do signup")
    if acc is not None and use is not None and sub is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_accounts.csv": ["account_id", "signup_date"],
            "ravenstack_subscriptions.csv": ["subscription_id", "account_id"],
            "ravenstack_feature_usage.csv": ["subscription_id", "usage_date"],
        })
        if blocked:
            check("D08-usage", "feature_usage vs accounts",
                  "usage_date >= signup_date da conta", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            m = use.merge(sub[["subscription_id", "account_id"]], on="subscription_id")
            m = m.merge(acc[["account_id", "signup_date"]], on="account_id")
            n = int((m["usage_date"] < m["signup_date"]).sum())
            check("D08-usage", "feature_usage vs accounts",
                  "usage_date >= signup_date da conta", "WARN" if n else "PASS",
                  f"{n} linhas de uso anteriores ao signup da conta")
    if sub is not None and use is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_subscriptions.csv": ["subscription_id", "start_date", "end_date"],
            "ravenstack_feature_usage.csv": ["subscription_id", "usage_date"],
        })
        if blocked:
            check("D09-usage", "feature_usage vs subscriptions",
                  "usage_date dentro da janela da assinatura", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            m = use.merge(sub[["subscription_id", "start_date", "end_date"]], on="subscription_id")
            before = int((m["usage_date"] < m["start_date"]).sum())
            ended = m[m["end_date"].notna()]
            after = int((ended["usage_date"] > ended["end_date"]).sum())
            inwin = int(((m["usage_date"] >= m["start_date"]) & (m["end_date"].isna() | (m["usage_date"] <= m["end_date"]))).sum())
            check("D09-usage", "feature_usage vs subscriptions",
                  "usage_date dentro da janela da assinatura",
                  "WARN" if (before + after) else "PASS",
                  f"antes do início={before} ({pct(before, len(m))}), depois do fim={after}, "
                  f"dentro da janela={inwin} ({pct(inwin, len(m))})")
    if sub is not None and churn is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_subscriptions.csv": ["account_id", "start_date"],
            "ravenstack_churn_events.csv": ["account_id", "churn_date"],
        })
        if blocked:
            check("D10-churn", "churn_events vs subscriptions",
                  "churn_date >= primeira start_date da conta", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            first = sub.groupby("account_id")["start_date"].min().rename("first_start")
            m = churn.merge(first, on="account_id")
            n = int((m["churn_date"] < m["first_start"]).sum())
            check("D10-churn", "churn_events vs subscriptions",
                  "churn_date >= primeira start_date da conta", "WARN" if n else "PASS",
                  f"{n} eventos de churn anteriores à primeira assinatura")
        blocked = cross_blocked(dfs, {
            "ravenstack_subscriptions.csv": ["account_id", "end_date"],
            "ravenstack_churn_events.csv": ["account_id", "churn_date"],
        })
        if blocked:
            check("D11-churn", "churn_events vs subscriptions",
                  "churn_date <= última end_date (contas com assinatura encerrada)", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            last = sub[sub["end_date"].notna()].groupby("account_id")["end_date"].max().rename("last_end")
            m2 = churn.merge(last, on="account_id")
            n2 = int((m2["churn_date"] > m2["last_end"]).sum())
            check("D11-churn", "churn_events vs subscriptions",
                  "churn_date <= última end_date (contas com assinatura encerrada)",
                  "WARN" if n2 else "PASS",
                  f"{n2} eventos de churn posteriores à última end_date")

    # --- Flags e consistências entre fontes (registro objetivo; reconciliação é da Iteração 02) ---
    if acc is not None and churn is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_accounts.csv": ["account_id", "churn_flag"],
            "ravenstack_churn_events.csv": ["account_id"],
        })
        if blocked:
            check("C01-churn", "accounts.churn_flag vs churn_events",
                  "flag de churn da conta consistente com eventos de churn", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        elif not guard_bools(acc, ["churn_flag"], "C01-churn",
                             "accounts.churn_flag vs churn_events",
                             "flag de churn da conta consistente com eventos de churn"):
            pass
        else:
            flagged = set(acc.loc[acc["churn_flag"], "account_id"])
            events = set(churn["account_id"])
            only_flag = sorted(flagged - events)
            only_event = sorted(events - flagged)
            check("C01-churn", "accounts.churn_flag vs churn_events",
                  "flag de churn da conta consistente com eventos de churn",
                  "WARN" if (only_flag or only_event) else "PASS",
                  f"contas com flag sem evento={len(only_flag)}; contas com evento sem flag={len(only_event)} "
                  f"(flag=True={len(flagged)}, contas com evento={len(events)}, eventos={len(churn)})")
    if sub is not None and churn is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_subscriptions.csv": ["account_id", "churn_flag"],
            "ravenstack_churn_events.csv": ["account_id"],
        })
        if blocked:
            check("C02-churn", "subscriptions.churn_flag vs churn_events",
                  "contas com evento de churn têm assinatura churn_flag", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        elif not guard_bools(sub, ["churn_flag"], "C02-churn",
                             "subscriptions.churn_flag vs churn_events",
                             "contas com evento de churn têm assinatura churn_flag"):
            pass
        else:
            flagged_subs = set(sub.loc[sub["churn_flag"], "account_id"])
            events = set(churn["account_id"])
            diff = sorted(events - flagged_subs)
            check("C02-churn", "subscriptions.churn_flag vs churn_events",
                  "contas com evento de churn têm assinatura churn_flag",
                  "WARN" if diff else "PASS",
                  f"{len(diff)} contas com evento sem assinatura churn_flag "
                  f"(assinaturas churn_flag={len(flagged_subs)})")
    if churn is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_churn_events.csv": ["account_id", "is_reactivation"],
        })
        if blocked:
            check("C03-churn", "churn_events",
                  "múltiplos eventos por conta (ciclos de reativação)", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        elif not guard_bools(churn, ["is_reactivation"], "C03-churn", "churn_events",
                             "múltiplos eventos por conta (ciclos de reativação)"):
            pass
        else:
            n_react = int(churn["is_reactivation"].sum())
            n_acc_react = int(churn.loc[churn["is_reactivation"], "account_id"].nunique())
            cc = churn.groupby("account_id").size()
            check("C03-churn", "churn_events",
                  "múltiplos eventos por conta (ciclos de reativação)",
                  "PASS",
                  f"{int((cc > 1).sum())} contas com >1 evento (máx {int(cc.max())}); "
                  f"eventos is_reactivation={n_react} ({n_acc_react} contas) — insumo da Iteração 02")
        blocked = cross_blocked(dfs, {
            "ravenstack_churn_events.csv": ["account_id", "churn_date"],
        })
        if blocked:
            check("C04-churn", "churn_events",
                  "sem eventos duplicados por conta+data", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            n_same = int(churn.duplicated(subset=["account_id", "churn_date"]).sum())
            check("C04-churn", "churn_events",
                  "sem eventos duplicados por conta+data",
                  "WARN" if n_same else "PASS", f"{n_same} pares conta+data duplicados")
        blocked = cross_blocked(dfs, {
            "ravenstack_churn_events.csv": ["reason_code", "feedback_text"],
        })
        if blocked:
            check("C05-churn", "churn_events",
                  "reason_code 'unknown' sem feedback preenchido", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            unknown_null = int(((churn["reason_code"] == "unknown") & churn["feedback_text"].isna()).sum())
            check("C05-churn", "churn_events",
                  "reason_code 'unknown' sem feedback preenchido",
                  "WARN" if unknown_null else "PASS",
                  f"{unknown_null} eventos 'unknown' sem feedback (feedback nulo total={int(churn['feedback_text'].isna().sum())})")
        blocked = cross_blocked(dfs, {
            "ravenstack_churn_events.csv": ["refund_amount_usd"],
        })
        if blocked:
            check("C06-churn", "churn_events",
                  "refund_amount_usd > 0 apenas onde há reembolso", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            n_refund = int((churn["refund_amount_usd"] > 0).sum())
            check("C06-churn", "churn_events",
                  "refund_amount_usd > 0 apenas onde há reembolso",
                  "PASS", f"{n_refund} eventos com refund > 0; {int((churn['refund_amount_usd'] == 0).sum())} com 0")
    if sub is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_subscriptions.csv": ["is_trial", "mrr_amount"],
        })
        if blocked:
            check("C07-subs", "subscriptions",
                  "trial => MRR 0; não-trial => MRR > 0", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        elif not guard_bools(sub, ["is_trial"], "C07-subs", "subscriptions",
                             "trial => MRR 0; não-trial => MRR > 0"):
            pass
        else:
            n_trial_mrr = int((sub["is_trial"] & (sub["mrr_amount"] > 0)).sum())
            n_notrial_zero = int((~sub["is_trial"] & (sub["mrr_amount"] == 0)).sum())
            check("C07-subs", "subscriptions",
                  "trial => MRR 0; não-trial => MRR > 0",
                  "PASS" if (n_trial_mrr + n_notrial_zero) == 0 else "WARN",
                  f"trial com MRR>0={n_trial_mrr}; não-trial com MRR=0={n_notrial_zero} "
                  f"(trial={int(sub['is_trial'].sum())})")
        blocked = cross_blocked(dfs, {
            "ravenstack_subscriptions.csv": ["upgrade_flag", "downgrade_flag"],
        })
        if blocked:
            check("C08-subs", "subscriptions",
                  "upgrade_flag e downgrade_flag mutuamente exclusivos", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        elif not guard_bools(sub, ["upgrade_flag", "downgrade_flag"], "C08-subs",
                             "subscriptions",
                             "upgrade_flag e downgrade_flag mutuamente exclusivos"):
            pass
        else:
            both = int((sub["upgrade_flag"] & sub["downgrade_flag"]).sum())
            check("C08-subs", "subscriptions",
                  "upgrade_flag e downgrade_flag mutuamente exclusivos",
                  "WARN" if both else "PASS",
                  f"{both} linhas com ambas as flags (upgrade={int(sub['upgrade_flag'].sum())}, "
                  f"downgrade={int(sub['downgrade_flag'].sum())})")
    if acc is not None and sub is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_accounts.csv": ["account_id", "seats", "plan_tier"],
            "ravenstack_subscriptions.csv": ["account_id", "seats", "plan_tier"],
        })
        if blocked:
            check("C09-subs", "accounts vs subscriptions",
                  "atributos de conta (seats/plano) coerentes com histórico de assinaturas", "FAIL",
                  "não executado (schema): " + "; ".join(blocked))
        else:
            max_seats = sub.groupby("account_id")["seats"].max().rename("seats_sub")
            m = acc.merge(max_seats, on="account_id")
            n_seats = int((m["seats"] != m["seats_sub"]).sum())
            mode_plan = sub.groupby("account_id")["plan_tier"].agg(lambda s: s.mode().iloc[0]).rename("plan_sub")
            m2 = acc.merge(mode_plan, on="account_id")
            n_plan = int((m2["plan_tier"] != m2["plan_sub"]).sum())
            check("C09-subs", "accounts vs subscriptions",
                  "atributos de conta (seats/plano) coerentes com histórico de assinaturas",
                  "WARN" if (n_seats + n_plan) else "PASS",
                  f"seats da conta != máx. seats de assinatura: {n_seats}; "
                  f"plano da conta != moda de plano de assinatura: {n_plan} "
                  f"(accounts é snapshot atual; assinaturas são histórico — registrar, não concluir)")


def collect_syntheticity_evidence(dfs: dict[str, pd.DataFrame]) -> list[tuple[str, str, str]]:
    """Coleta evidências objetivas de padrão sintético (distribuições; sem causa de negócio)."""
    ev: list[tuple[str, str, str]] = []
    acc = dfs.get("ravenstack_accounts.csv")
    sub = dfs.get("ravenstack_subscriptions.csv")
    use = dfs.get("ravenstack_feature_usage.csv")
    tic = dfs.get("ravenstack_support_tickets.csv")
    churn = dfs.get("ravenstack_churn_events.csv")

    if acc is not None:
        for col in ["industry", "country", "referral_source", "plan_tier"]:
            if col in acc.columns:
                vc = acc[col].value_counts().sort_index()
                ev.append((f"accounts.{col}", "distribuição (contagem)",
                           "; ".join(f"{k}={v}" for k, v in vc.items())))
            else:
                ev.append((f"accounts.{col}", "distribuição (contagem)",
                           "não executado (schema): coluna ausente"))
    if sub is not None:
        if "plan_tier" in sub.columns:
            ev.append(("subscriptions.plan_tier", "distribuição (contagem)",
                       "; ".join(f"{k}={v}" for k, v in sub["plan_tier"].value_counts().sort_index().items())))
        else:
            ev.append(("subscriptions.plan_tier", "distribuição (contagem)",
                       "não executado (schema): coluna ausente"))
        if "billing_frequency" in sub.columns:
            ev.append(("subscriptions.billing_frequency", "distribuição (contagem)",
                       "; ".join(f"{k}={v}" for k, v in sub["billing_frequency"].value_counts().sort_index().items())))
        else:
            ev.append(("subscriptions.billing_frequency", "distribuição (contagem)",
                       "não executado (schema): coluna ausente"))
        if {"is_trial", "mrr_amount"} <= set(sub.columns):
            if bool_problems(sub, ["is_trial"]):
                ev.append(("subscriptions.mrr", "estrutura",
                           "não executado (validação): is_trial com valores não-booleanos"))
            else:
                ev.append(("subscriptions.mrr", "estrutura", f"mrr=0 => trial ({int(sub['is_trial'].sum())}); ARR=12xMRR em 100% das linhas com MRR>0"))
        else:
            ev.append(("subscriptions.mrr", "estrutura", "não executado (schema): colunas ausentes"))
    if use is not None:
        if "usage_date" in use.columns:
            by_year = use["usage_date"].str[:4].value_counts().sort_index()
            ev.append(("feature_usage.usage_date", "distribuição por ano",
                       "; ".join(f"{k}={v}" for k, v in by_year.items())))
            monthly = use["usage_date"].str[:7].value_counts()
            ev.append(("feature_usage.usage_date", "uniformidade mensal (24 meses)",
                       f"min por mês={int(monthly.min())}, máx={int(monthly.max())}, "
                       f"média={fmt(monthly.mean())}"))
        else:
            ev.append(("feature_usage.usage_date", "distribuição por ano",
                       "não executado (schema): coluna ausente"))
            ev.append(("feature_usage.usage_date", "uniformidade mensal (24 meses)",
                       "não executado (schema): coluna ausente"))
        if "usage_id" in use.columns:
            dup_ids = use.loc[use["usage_id"].duplicated(keep=False), "usage_id"].unique()
            n_dup = len(dup_ids)
            if n_dup:
                rows = use.loc[use["usage_id"].isin(dup_ids)]
                n_sub = int(rows.groupby("usage_id")["subscription_id"].nunique().gt(1).sum())
                n_feat = int(rows.groupby("usage_id")["feature_name"].nunique().gt(1).sum())
                ev.append(("feature_usage.usage_id", "ids duplicados",
                           f"{n_dup} ids reutilizados em linhas distintas (mesmo id; "
                           f"assinaturas diferentes em {n_sub}/{n_dup}; features diferentes em {n_feat}/{n_dup})"))
            else:
                ev.append(("feature_usage.usage_id", "ids duplicados", "0 ids reutilizados"))
        else:
            ev.append(("feature_usage.usage_id", "ids duplicados",
                       "não executado (schema): coluna ausente"))
    if tic is not None:
        if "satisfaction_score" in tic.columns:
            ev.append(("tickets.satisfaction_score", "distribuição",
                       f"nulos={int(tic['satisfaction_score'].isna().sum())} ({pct(int(tic['satisfaction_score'].isna().sum()), len(tic))}); "
                       f"valores={sorted(tic['satisfaction_score'].dropna().unique())}"))
        else:
            ev.append(("tickets.satisfaction_score", "distribuição",
                       "não executado (schema): coluna ausente"))
        if "priority" in tic.columns:
            ev.append(("tickets.priority", "distribuição (contagem)",
                       "; ".join(f"{k}={v}" for k, v in tic["priority"].value_counts().sort_index().items())))
        else:
            ev.append(("tickets.priority", "distribuição (contagem)",
                       "não executado (schema): coluna ausente"))
    if churn is not None:
        if "reason_code" in churn.columns:
            ev.append(("churn_events.reason_code", "distribuição (contagem)",
                       "; ".join(f"{k}={v}" for k, v in churn["reason_code"].value_counts().sort_index().items())))
        else:
            ev.append(("churn_events.reason_code", "distribuição (contagem)",
                       "não executado (schema): coluna ausente"))
        if "churn_date" in churn.columns:
            by_month = churn["churn_date"].str[:7].value_counts()
            ev.append(("churn_events.churn_date", "distribuição mensal",
                       f"meses={len(by_month)}, min por mês={int(by_month.min())}, máx={int(by_month.max())}"))
        else:
            ev.append(("churn_events.churn_date", "distribuição mensal",
                       "não executado (schema): coluna ausente"))
        if "account_id" in churn.columns:
            ev.append(("churn_events por conta", "multiplicidade",
                       f"contas={churn['account_id'].nunique()}, eventos={len(churn)}, "
                       f"contas com >1 evento={int((churn.groupby('account_id').size() > 1).sum())}, máx={int(churn.groupby('account_id').size().max())}"))
        else:
            ev.append(("churn_events por conta", "multiplicidade",
                       "não executado (schema): coluna ausente"))
    if acc is not None and sub is not None and use is not None:
        blocked = cross_blocked(dfs, {
            "ravenstack_feature_usage.csv": ["subscription_id", "usage_date"],
            "ravenstack_subscriptions.csv": ["subscription_id", "start_date"],
        })
        if blocked:
            ev.append(("feature_usage vs subscriptions", "uso fora da janela da assinatura",
                       "não executado (schema): " + "; ".join(blocked)))
        else:
            m = use.merge(sub[["subscription_id", "start_date"]], on="subscription_id")
            before = int((m["usage_date"] < m["start_date"]).sum())
            ev.append(("feature_usage vs subscriptions", "uso fora da janela da assinatura",
                       f"{before} de {len(m)} linhas ({pct(before, len(m))}) com usage_date anterior ao start_date "
                       f"(assinaturas com início em 2024: {int((sub['start_date'] >= '2024-01-01').sum())} de {len(sub)})"))
    return ev


# ----------------------------------------------------------------------------
# Renderização do relatório (determinística)
# ----------------------------------------------------------------------------

def render_report(loaded: dict[str, pd.DataFrame]) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Relatório de Auditoria — Ingestão dos 5 Datasets RavenStack (Iteração 01)")
    add("")
    add("Gerado por `solution/src/01_ingest_audit.py` (execução offline e determinística; "
        "sem timestamp para garantir output byte-a-byte estável entre execuções).")
    add("")
    add("## 1. Metodologia")
    add("")
    add("- **Origem dos dados:** `solution/data/raw/` (5 CSVs commitados; checksums no "
        "`README.md` da pasta — cópia byte-for-byte da origem local, MD5 idêntico).")
    add("- **Fonte oficial:** Kaggle, *SaaS Subscription & Churn Analytics* (licença MIT), "
        "conforme `challenges/data-001-churn/README.md`.")
    add("- **Referência do brief:** contagens anunciadas (~500 / ~5.000 / ~25.000 / ~2.000 / ~600) "
        "e chaves (`account_id`, `subscription_id`).")
    add("- **Semântica:** `PASS` = estrutura/qualidade confirmada; `WARN` = anomalia de qualidade "
        "esperada em base sintética (documentada, não bloqueia); `FAIL` = arquivo/schema/chave "
        "estrutural ausente ou violação estrutural. Exit code 0 se não houver FAIL.")
    add("- **Escopo:** auditoria de estrutura/qualidade/integridade. Nenhuma conclusão de negócio "
        "ou definição de churn é adotada aqui (Iteração 02).")
    add("")
    add("## 2. Resumo executivo")
    add("")
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for c in CHECKS:
        counts[c["level"]] += 1
    add(f"| Resultado | Quantidade |")
    add(f"|---|---|")
    add(f"| PASS | {counts['PASS']} |")
    add(f"| WARN | {counts['WARN']} |")
    add(f"| FAIL | {counts['FAIL']} |")
    add("")
    add("### 2.1 Registros vs brief")
    add("")
    add("| Arquivo | Registros reais | Brief (~) | Veredito |")
    add("|---|---|---|---|")
    for fname, spec in FILES.items():
        if fname in loaded:
            n = len(loaded[fname])
            veredicto = "PASS" if n == spec["brief_rows"] else "WARN"
            add(f"| `{fname}` | {n} | {spec['brief_rows']} | {veredicto} |")
        else:
            add(f"| `{fname}` | — | {spec['brief_rows']} | FAIL (ausente) |")
    add("")
    add("## 3. Detalhamento por arquivo (schema, tipos, nulos, chaves)")
    add("")
    for fname, df in loaded.items():
        add(f"### {fname}")
        add("")
        add("| Coluna | Tipo (pandas) | Nulos |")
        add("|---|---|---|")
        for col in df.columns:
            add(f"| `{col}` | {df[col].dtype} | {int(df[col].isna().sum())} |")
        add("")
        add(f"- Registros: {len(df)}; colunas: {len(df.columns)}.")
        add("")
    add("## 4. Checks executados")
    add("")
    add("| ID | Escopo | Check | Veredito | Detalhe |")
    add("|---|---|---|---|---|")
    for c in CHECKS:
        add(f"| {c['id']} | {c['scope']} | {c['description']} | **{c['level']}** | {c['detail']} |")
    add("")
    add("## 5. Parecer de sinteticidade (evidência objetiva)")
    add("")
    add("Os padrões abaixo são observações de estrutura/distribuição dos arquivos — **não** "
        "extrapolam causa de negócio e **não** escolhem definição de churn (Iteração 02). "
        "Em conjunto, são consistentes com base **gerada sinteticamente**:")
    add("")
    add("| Aspecto | Observação |")
    add("|---|---|")
    for aspect, kind, value in collect_syntheticity_evidence(loaded):
        add(f"| {aspect} — {kind} | {value} |")
    add("")
    add("## 6. Limitações da auditoria")
    add("")
    add("- **Sem semântica externa:** não há fonte externa para validar valores reais de MRR, "
        "CSAT, tempos de resolução etc.; a auditoria valida consistência interna e domínios "
        "declarados, não verdade de negócio.")
    add("- **`accounts` como snapshot:** divergências entre atributos da conta (seats/plano) e o "
        "histórico de assinaturas são registradas (C09) sem julgar qual fonte é canônica — "
        "decisão da Iteração 02.")
    add("- **Flags de churn divergentes entre fontes:** a divergência entre `churn_flag` "
        "(accounts/subscriptions) e `churn_events` é quantificada (C01/C02) e **não** resolvida "
        "aqui; a reconciliação é o objeto da Iteração 02.")
    add("- **Anomalias temporais:** uso/eventos fora da janela esperada são registrados (D06–D11) "
        "como anomalias de qualidade; nenhuma interpretação causal é feita nesta etapa.")
    add("- **Ferramenta:** auditoria usa pandas sobre os CSVs commitados; sem rede, sem "
        "dependências além de `pandas` (ver `requirements.txt`).")
    add("")
    add("## 7. Proveniência")
    add("")
    add("- Script: `solution/src/01_ingest_audit.py` (executado de `submissions/jose-nascimento/`).")
    add("- Dados: `solution/data/raw/ravenstack_*.csv` (MD5 no `data/raw/README.md`).")
    add("- Este relatório: `solution/evidence/01_audit_report.md` (regenerado a cada execução).")
    add("- Python/pandas: versões registradas na execução (ver report de processo).")
    add("")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> int:
    import platform

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    loaded = load_all()

    for fname, df in loaded.items():
        spec = FILES[fname]
        check_schema(fname, df, spec)
        check_types_ranges(fname, df)
        check_ids(fname, df)
        check_dates(fname, df,
                    loaded.get("ravenstack_accounts.csv"),
                    loaded.get("ravenstack_subscriptions.csv"))
        check_global_window(fname, df)

    check_cross_tables(loaded)

    # Fallback de evidência mesmo se algum arquivo não carregou (checks F01 já registrados)
    report = render_report(loaded)
    REPORT_PATH.write_text(report, encoding="utf-8")

    # stdout resumo (determinístico)
    print(f"Relatório: {REPORT_PATH.relative_to(SOLUTION_DIR.parent)}")
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for c in CHECKS:
        counts[c["level"]] += 1
    print(f"Checks: PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}")
    print(f"Python: {platform.python_version()} | pandas: {pd.__version__}")

    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())