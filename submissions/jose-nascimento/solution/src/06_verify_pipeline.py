#!/usr/bin/env python3
"""
06_verify_pipeline.py — Verificador estrutural e de consistência do pipeline (Iterações 06–07).

Verifica, SEM reimplementar nenhuma análise das Iterações 01–05:

  A. Manifesto de arquivos — 5 raw CSVs, scripts 01–07, evidence 01–05,
     account_month + processado, 26 tabelas t01–t21 e EXATAMENTE 6 PNGs,
     relatório executivo (It07);
  B. Parseabilidade e não-vazio — CSVs legíveis com cabeçalho e linhas,
     Markdown presente (incl. report-executivo.md), PNGs com magic bytes e
     tamanho > 0;
  C. Consistência com contratos existentes — MD5/contagens declarados nos
     README commitados de data/raw e data/processed; invariantes estruturais
     do painel account-month DERIVADOS dos dados (nenhum número de dados
     hardcoded); reports de evidence sem gate "**FAIL**"; relações
     estruturais entre tabelas (subconjuntos documentados);
  D. Higiene — zero binários proibidos (.db/.duckdb/.sqlite/.pyc), zero
     venv/cache, zero paths pessoais/segredos em solution/, zero imports de
     rede nos scripts, requirements mínimos, run.sh executável e sem CRLF,
     ids de check únicos (gate D7);
  E. Sanidade — compile() e import de todos os scripts (01–07).
  F. Relatório executivo (It07) — presença, links relativos, exatamente 6
     imagens (1x cada), word count, claims proibidos em contexto afirmativo,
     contas ⊆ t16, ações ⊆ t18 e âncoras numéricas re-derivadas das tabelas.

Saída: uma linha por check ("[PASS]" / "[FAIL]" + id + detalhe), resumo e
exit 0 se nenhum FAIL, exit 1 caso contrário (diagnóstico estruturado, sem
traceback para falhas estruturais — qualquer exceção vira FAIL com mensagem).

Uso (qualquer CWD; paths resolvidos por __file__):
    python3 solution/src/06_verify_pipeline.py
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import sys
from pathlib import Path

# Invocação direta documentada (`python3 solution/src/06_verify_pipeline.py`)
# NÃO pode gerar `solution/src/__pycache__/` (o check E2 importa os scripts via
# importlib; sem isto, a execução direta poluiria a árvore e o próprio D1
# falharia na execução seguinte). A flag vale para todo o processo, incluindo
# o SourceFileLoader usado por E2.
sys.dont_write_bytecode = True

import pandas as pd

# ----------------------------------------------------------------------------
# Paths (relativos ao próprio projeto; sem paths pessoais)
# ----------------------------------------------------------------------------
SOLUTION_DIR = Path(__file__).resolve().parent.parent
SUBMISSION_DIR = SOLUTION_DIR.parent
RAW_DIR = SOLUTION_DIR / "data" / "raw"
PROCESSED_DIR = SOLUTION_DIR / "data" / "processed"
EVIDENCE_DIR = SOLUTION_DIR / "evidence"
DOCS_DIR = SOLUTION_DIR / "docs"
TABLES_DIR = SOLUTION_DIR / "out" / "tables"
CHARTS_DIR = SOLUTION_DIR / "out" / "charts"
SRC_DIR = SOLUTION_DIR / "src"
REPORT_PATH = SOLUTION_DIR / "report-executivo.md"

# ----------------------------------------------------------------------------
# Manifests (estrutura documentada nas Iterações 01–05; NÃO números de dados)
# ----------------------------------------------------------------------------
RAW_FILES = [
    "ravenstack_accounts.csv",
    "ravenstack_subscriptions.csv",
    "ravenstack_feature_usage.csv",
    "ravenstack_support_tickets.csv",
    "ravenstack_churn_events.csv",
]
SCRIPTS = [f"{n:02d}_{name}.py" for n, name in [
    (1, "ingest_audit"), (2, "reconcile_churn"), (3, "root_cause"),
    (4, "lifecycle_watchlist"), (5, "actions_impact"),
    (7, "generate_executive_report"), (6, "verify_pipeline")]]
EVIDENCE = [
    "01_audit_report.md",
    "02_consistency_report.md",
    "03_root_cause_report.md",
    "04_lifecycle_watchlist_report.md",
    "05_action_plan.md",
]
# It03: t01–t03/t03b/t03c/t05–t10 (13); It04: t11–t17/t14b/t15b (9); It05: t18–t21 (4).
TABLES = [
    "t01_monthly_series.csv", "t02_cohort_km.csv", "t02a_cohort_km_month.csv",
    "t02b_cohort_km_at_risk.csv", "t03_onboarding_buckets.csv",
    "t03b_onboarding_accounts.csv", "t03c_cac_equivalent.csv",
    "t05_usage_monthly.csv", "t06_support_monthly.csv", "t07_segments.csv",
    "t08_reasons.csv", "t09_causality.csv", "t10_hypothesis_verdicts.csv",
    "t11_account_lifecycle.csv", "t12_reactivation_recurrence.csv",
    "t13_state_cycles.csv", "t14_backtest_temporal.csv",
    "t14b_backtest_detail.csv", "t15_priority_segments.csv",
    "t15b_segment_overlap.csv", "t16_watchlist_top20.csv",
    "t17_rank_comparison.csv", "t18_actions_prioritized.csv",
    "t19_impact_sensitivity.csv", "t20_measurement_plan.csv",
    "t21_watchlist_split_actions.csv",
]
CHARTS = [
    "a_monthly_events_and_rate.png",
    "b_km_by_signup_quarter.png",
    "c_onboarding_exposure_by_duration.png",
    "d_usage_volume_vs_intensity.png",
    "It04_c_lifecycle_vs_current_mrr.png",
    "It04_d_backtest_lift.png",
]
# PNGs pruned no gate 3x da It04 (números preservados em tabelas t06/t07/t09/t12/t13):
# nunca podem reaparecer.
PRUNED_CHARTS = [
    "e_support_churn_vs_control.png",
    "f_segment_first_event_rates.png",
    "It04_a_recurrence_reactivation.png",
    "It04_b_cycle_lenses.png",
]
DATE_COLUMNS = {  # colunas de data por arquivo bruto (para derivar a janela global)
    "ravenstack_accounts.csv": ["signup_date"],
    "ravenstack_subscriptions.csv": ["start_date", "end_date"],
    "ravenstack_churn_events.csv": ["churn_date"],
    "ravenstack_feature_usage.csv": ["usage_date"],
    "ravenstack_support_tickets.csv": ["submitted_at", "closed_at"],
}
PANEL_STATUS_DOMAIN = {"active", "inactive"}
PANEL_NONNEG = ["winner_mrr", "mrr_sum_naive", "mrr_ended_in_month",
                "n_ended_in_month", "n_active_subs", "n_events_in_month",
                "usage_rows_month", "usage_rows_in_window_month", "tickets_month"]
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
# tokens de path pessoal (histórico das Iterações 01–05, item F2 do checklist).
# Compostos em runtime (partes) para que ESTE arquivo não case consigo mesmo
# na varredura: nenhum token completo existe literalmente no texto-fonte.
PERSONAL_PATH_TOKENS = ["".join(p) for p in [
    ("/", "tmp"), ("/", "home"), ("/", "Users/"),
    ("ub", "untu"), ("josenas", "cimento")]]
SECRET_PATTERNS = [
    re.compile(r"api[_-]?key\s*[:=]", re.IGNORECASE),
    re.compile(r"password\s*[:=]", re.IGNORECASE),
    re.compile(r"secret\s*[:=]", re.IGNORECASE),
    re.compile(r"BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"token\s*[:=]\s*['\"][A-Za-z0-9._\-]{16,}"),
]
NETWORK_IMPORTS = re.compile(
    r"^\s*(import|from)\s+(urllib|requests|httpx|aiohttp|socket|ftplib|telnetlib|"
    r"paramiko|kagglehub|wget|curl)\b",
    re.MULTILINE)
TEXT_EXTENSIONS = {".py", ".md", ".csv", ".txt", ".sh", ".yml", ".yaml",
                   ".json", ".ini", ".toml", ".cfg", ".gitignore", ""}
FORBIDDEN_SUFFIXES = (".db", ".duckdb", ".sqlite", ".sqlite3", ".pyc", ".pyo")
FORBIDDEN_DIRS = {"__pycache__", ".ipynb_checkpoints", "venv", ".venv", "env"}

# ----------------------------------------------------------------------------
# Registro de checks
# ----------------------------------------------------------------------------
CHECKS: list[dict] = []


def check(uid: str, section: str, desc: str, ok: bool, detail: str) -> None:
    CHECKS.append({"uid": uid, "section": section, "desc": desc,
                   "ok": bool(ok), "detail": str(detail)})


def safe(uid: str, section: str, desc: str, fn) -> None:
    """Executa fn() (sem args) esperando True/False; exceção vira FAIL sem traceback."""
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001 — falha estrutural vira diagnóstico
        check(uid, section, desc, False, f"exceção durante a verificação: {exc}")
        return
    check(uid, section, desc, ok, detail)


def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def text_files_under(root: Path) -> list[Path]:
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in TEXT_EXTENSIONS:
            out.append(p)
    return out


# ----------------------------------------------------------------------------
# A. Manifesto
# ----------------------------------------------------------------------------
def a_manifest() -> None:
    def _raw_set() -> tuple[bool, str]:
        actual = sorted(p.name for p in RAW_DIR.glob("*.csv"))
        expected = sorted(RAW_FILES)
        if actual != expected:
            return False, (f"data/raw/ com CSVs inesperados ou faltando: "
                           f"esperado={expected} real={actual}")
        empty = [p.name for p in RAW_DIR.iterdir() if p.is_file() and p.stat().st_size == 0]
        return (not empty), (f"5 raw CSVs presentes; vazios={empty or 'nenhum'}")
    safe("A1-raw", "manifesto", "5 raw CSVs exatos em data/raw/", _raw_set)

    def _scripts() -> tuple[bool, str]:
        missing = [s for s in SCRIPTS if not (SRC_DIR / s).is_file()]
        return (not missing), (f"scripts presentes; ausentes={missing or 'nenhum'}")
    safe("A2-src", "manifesto", "scripts 01–07 presentes em solution/src/", _scripts)

    def _evidence() -> tuple[bool, str]:
        missing = [e for e in EVIDENCE if not (EVIDENCE_DIR / e).is_file()]
        empty = [e for e in EVIDENCE
                 if (EVIDENCE_DIR / e).is_file() and (EVIDENCE_DIR / e).stat().st_size == 0]
        return (not missing and not empty), (
            f"evidence 01–05 presentes; ausentes={missing or 'nenhum'}; "
            f"vazios={empty or 'nenhum'}")
    safe("A3-evidence", "manifesto", "evidence 01–05 presentes e não vazios", _evidence)

    def _processed() -> tuple[bool, str]:
        need = [PROCESSED_DIR / "account_month.csv", PROCESSED_DIR / "README.md",
                DOCS_DIR / "analytical-contract.md"]
        missing = [p.name for p in need if not p.is_file()]
        return (not missing), (f"account_month/processado/contrato presentes; "
                               f"ausentes={missing or 'nenhum'}")
    safe("A4-processed", "manifesto", "account_month + README processado + contrato", _processed)

    def _charts() -> tuple[bool, str]:
        actual = sorted(p.name for p in CHARTS_DIR.glob("*.png"))
        if actual != sorted(CHARTS):
            return False, (f"esperados exatamente {len(CHARTS)} PNGs "
                           f"(manifesto): real={actual}")
        return True, f"exatamente {len(CHARTS)} PNGs do manifesto"
    safe("A5-charts", "manifesto", "exatamente 6 PNGs (manifesto fechado)", _charts)

    def _pruned() -> tuple[bool, str]:
        found = [c for c in PRUNED_CHARTS if (CHARTS_DIR / c).exists()]
        return (not found), (f"PNGs pruned (gate It04) ausentes: {found or 'nenhum'}")
    safe("A6-pruned", "manifesto", "4 PNGs pruned NÃO reapareceram", _pruned)

    def _tables() -> tuple[bool, str]:
        actual = sorted(p.name for p in TABLES_DIR.glob("*.csv"))
        if actual != sorted(TABLES):
            return False, (f"esperadas exatamente {len(TABLES)} tabelas "
                           f"(t01–t21): real={actual}")
        return True, f"exatamente {len(TABLES)} tabelas (manifesto t01–t21)"
    safe("A7-tables", "manifesto", "exatamente 26 tabelas em out/tables/", _tables)


# ----------------------------------------------------------------------------
# B. Parseabilidade e não-vazio
# ----------------------------------------------------------------------------
def b_parseable() -> None:
    for fname in RAW_FILES:
        path = RAW_DIR / fname
        def _one(p: Path = path, f: str = fname) -> tuple[bool, str]:
            if not p.is_file():
                return False, "arquivo ausente"
            df = pd.read_csv(p)
            if len(df) == 0:
                return False, "0 linhas de dados"
            if df.columns.tolist() == [] or any(str(c).strip() == "" for c in df.columns):
                return False, "cabeçalho vazio"
            return True, f"{len(df)} linhas x {len(df.columns)} colunas"
        safe(f"B1-{fname}", "parse", f"raw CSV parseável: {fname}", _one)

    for tname in TABLES:
        path = TABLES_DIR / tname
        def _one(p: Path = path, t: str = tname) -> tuple[bool, str]:
            if not p.is_file():
                return False, "arquivo ausente"
            df = pd.read_csv(p)
            if len(df) == 0:
                return False, "0 linhas de dados"
            return True, f"{len(df)} linhas x {len(df.columns)} colunas"
        safe(f"B2-{tname}", "parse", f"tabela CSV parseável: {tname}", _one)

    def _panel() -> tuple[bool, str]:
        path = PROCESSED_DIR / "account_month.csv"
        df = pd.read_csv(path)
        if len(df) == 0:
            return False, "0 linhas"
        return True, f"{len(df)} linhas x {len(df.columns)} colunas"
    safe("B3-panel", "parse", "account_month.csv parseável", _panel)

    for md_path in [EVIDENCE_DIR / e for e in EVIDENCE] + [
            PROCESSED_DIR / "README.md", RAW_DIR / "README.md",
            DOCS_DIR / "analytical-contract.md", REPORT_PATH]:
        # uid único por PATH relativo (evita colisão "README.md" raw/processado;
        # o gate D7-uids falha se qualquer uid se repetir)
        uid = f"B4-md-{md_path.relative_to(SOLUTION_DIR)}"
        def _one(p: Path = md_path) -> tuple[bool, str]:
            if not p.is_file() or p.stat().st_size == 0:
                return False, "ausente ou vazio"
            txt = p.read_text(encoding="utf-8")
            return ("## " in txt), f"{p.stat().st_size} bytes; seção '## ' presente"
        safe(uid, "parse", f"Markdown presente: {md_path.relative_to(SOLUTION_DIR)}", _one)

    for cname in CHARTS:
        path = CHARTS_DIR / cname
        def _one(p: Path = path, c: str = cname) -> tuple[bool, str]:
            if not p.is_file() or p.stat().st_size == 0:
                return False, "ausente ou vazio"
            magic = p.read_bytes()[:8]
            ok = magic == b"\x89PNG\r\n\x1a\n"
            return ok, f"{p.stat().st_size} bytes; magic PNG {'OK' if ok else 'INVÁLIDO'}"
        safe(f"B5-{cname}", "parse", f"PNG íntegro: {cname}", _one)


# ----------------------------------------------------------------------------
# C. Consistência com contratos existentes (derivada; sem números hardcoded)
# ----------------------------------------------------------------------------
def _parse_raw_manifest() -> dict[str, dict]:
    """Lê o manifesto commitado data/raw/README.md: arquivo -> {md5, records}."""
    txt = (RAW_DIR / "README.md").read_text(encoding="utf-8")
    out: dict[str, dict] = {}
    for line in txt.splitlines():
        m = re.match(r"\|\s*`(ravenstack_[a-z_]+\.csv)`\s*\|\s*`([0-9a-f]{32})`\s*\|"
                     r"\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|", line)
        if m:
            out[m.group(1)] = {"md5": m.group(2),
                               "records": int(m.group(4).replace(".", ""))}
    return out


def _parse_processed_manifest() -> dict:
    txt = (PROCESSED_DIR / "README.md").read_text(encoding="utf-8")
    rows = re.search(r"Linhas:\s*(\d+)", txt)
    md5m = re.search(r"Checksum MD5 \(esta versão\):\s*`([0-9a-f]{32})`", txt)
    return {"rows": int(rows.group(1)) if rows else None,
            "md5": md5m.group(1) if md5m else None}


def c_consistency() -> None:
    def _counts() -> tuple[bool, str]:
        man = _parse_raw_manifest()
        if set(man) != set(RAW_FILES):
            return False, f"manifesto raw incompleto no README: {sorted(man)}"
        bad = []
        for fname in RAW_FILES:
            n = len(pd.read_csv(RAW_DIR / fname))
            if n != man[fname]["records"]:
                bad.append(f"{fname}: real={n} manifesto={man[fname]['records']}")
        return (not bad), (f"contagens batem com data/raw/README.md; "
                           f"divergências={bad or 'nenhuma'}")
    safe("C1-raw-counts", "contrato", "contagens dos raw CSVs = manifesto commitado", _counts)

    def _md5() -> tuple[bool, str]:
        man = _parse_raw_manifest()
        bad = []
        for fname in RAW_FILES:
            real = md5_of(RAW_DIR / fname)
            if real != man[fname]["md5"]:
                bad.append(f"{fname}: real={real} manifesto={man[fname]['md5']}")
        return (not bad), (f"MD5 dos raw CSVs = manifesto commitado; "
                           f"divergências={bad or 'nenhuma'}")
    safe("C2-raw-md5", "contrato", "MD5 dos raw CSVs = data/raw/README.md", _md5)

    def _panel_manifest() -> tuple[bool, str]:
        man = _parse_processed_manifest()
        path = PROCESSED_DIR / "account_month.csv"
        n = len(pd.read_csv(path))
        real_md5 = md5_of(path)
        bad = []
        if man["rows"] is None or n != man["rows"]:
            bad.append(f"linhas: real={n} manifesto={man['rows']}")
        if man["md5"] is None or real_md5 != man["md5"]:
            bad.append(f"MD5: real={real_md5} manifesto={man['md5']}")
        return (not bad), (f"account_month bate com data/processed/README.md; "
                           f"divergências={bad or 'nenhuma'}")
    safe("C3-panel-manifest", "contrato",
         "account_month (linhas+MD5) = manifesto processado", _panel_manifest)

    def _panel_invariants() -> tuple[bool, str]:
        panel = pd.read_csv(PROCESSED_DIR / "account_month.csv")
        acc = pd.read_csv(RAW_DIR / "ravenstack_accounts.csv")
        problems: list[str] = []
        # unicidade account x mês
        if panel.duplicated(["account_id", "month"]).any():
            problems.append("duplicatas account×mês")
        # formato do mês
        if not panel["month"].astype(str).str.fullmatch(r"\d{4}-\d{2}").all():
            problems.append("mês fora do formato YYYY-MM")
        # domínios e não-negatividade
        if not set(panel["status"].astype(str)) <= PANEL_STATUS_DOMAIN:
            problems.append(f"status fora de {sorted(PANEL_STATUS_DOMAIN)}")
        for col in PANEL_NONNEG:
            if col in panel.columns and (pd.to_numeric(panel[col], errors="coerce").fillna(0) < 0).any():
                problems.append(f"{col} com valor negativo")
        # janela global derivada dos dados brutos (min/max mês de TODAS as datas)
        months: list[str] = []
        for fname, cols in DATE_COLUMNS.items():
            df = pd.read_csv(RAW_DIR / fname)
            for col in cols:
                if col in df.columns:
                    s = pd.to_datetime(df[col], errors="coerce").dropna()
                    months += [f"{d.year:04d}-{d.month:02d}" for d in s.dt.to_period("M")]
        if months:
            lo, hi = min(months), max(months)
            pmin, pmax = panel["month"].min(), panel["month"].max()
            if pmin < lo or pmax > hi:
                problems.append(f"painel fora da janela derivada [{lo}..{hi}]: "
                                f"[{pmin}..{pmax}]")
        # piso: mês de signup por conta == primeiro mês da conta no painel (contrato §2)
        signup = {r["account_id"]: str(r["signup_date"])[:7]
                  for _, r in acc[["account_id", "signup_date"]].iterrows()}
        first = panel.sort_values("month").groupby("account_id")["month"].first()
        bad_floor = [aid for aid, m in first.items()
                     if aid in signup and m != signup[aid]]
        if bad_floor:
            problems.append(f"{len(bad_floor)} contas com 1º mês != mês do signup "
                            f"(ex.: {bad_floor[:3]})")
        # cobertura: mesmas contas do raw accounts
        if set(panel["account_id"]) != set(signup):
            problems.append("conjunto de contas do painel != contas de accounts")
        return (not problems), (f"invariantes estruturais derivadas OK; "
                                f"problemas={problems or 'nenhum'}")
    safe("C4-panel-invariants", "contrato",
         "invariantes estruturais do account_month (derivadas dos dados)", _panel_invariants)

    # markers de gate nos reports: 01–02 têm tabela-resumo "| Resultado | Quantidade |"
    # com linhas "| FAIL | N |"; 03 usa "**PASS**" nas linhas de gate; 04–05 usam
    # células "| PASS |" (sem negrito). Cada report é verificado pelo seu formato.
    SUMMARY_HEADER = re.compile(r"^\|\s*Resultado\s*\|\s*Quantidade\s*\|")
    SUMMARY_FAIL = re.compile(r"^\|\s*FAIL\s*\|\s*(\d+)\s*\|")
    SUMMARY_PASS = re.compile(r"^\|\s*PASS\s*\|\s*(\d+)\s*\|")
    FAIL_MARKER = re.compile(r"\*\*FAIL\*\*|\|\s*FAIL\s*\|")
    PASS_MARKER = re.compile(r"\*\*PASS\*\*|\|\s*PASS\s*\|")

    def _evidence_gates() -> tuple[bool, str]:
        bad = []
        for e in EVIDENCE:
            txt = (EVIDENCE_DIR / e).read_text(encoding="utf-8")
            lines = txt.splitlines()
            if any(SUMMARY_HEADER.match(ln) for ln in lines):
                n_fail = [int(m.group(1)) for ln in lines
                          for m in [SUMMARY_FAIL.match(ln)] if m]
                n_pass = [int(m.group(1)) for ln in lines
                          for m in [SUMMARY_PASS.match(ln)] if m]
                if n_fail and n_fail[0] != 0:
                    bad.append(f"{e}: resumo reporta {n_fail[0]} FAIL")
                if not n_pass or n_pass[0] < 1:
                    bad.append(f"{e}: resumo sem PASS (report stale?)")
            else:
                if FAIL_MARKER.search(txt):
                    bad.append(f"{e} contém linha de gate FAIL")
                if not PASS_MARKER.search(txt):
                    bad.append(f"{e} sem nenhum gate PASS (report stale?)")
        return (not bad), (f"evidence sem gates FAIL e com gates PASS; "
                           f"problemas={bad or 'nenhum'}")
    safe("C5-evidence-gates", "contrato",
         "reports de evidence: zero gate FAIL, ao menos um gate PASS",
         _evidence_gates)

    def _cross_tables() -> tuple[bool, str]:
        problems: list[str] = []
        t11 = pd.read_csv(TABLES_DIR / "t11_account_lifecycle.csv")
        t16 = pd.read_csv(TABLES_DIR / "t16_watchlist_top20.csv")
        t21 = pd.read_csv(TABLES_DIR / "t21_watchlist_split_actions.csv")
        t14 = pd.read_csv(TABLES_DIR / "t14_backtest_temporal.csv")
        t14b = pd.read_csv(TABLES_DIR / "t14b_backtest_detail.csv")
        t18 = pd.read_csv(TABLES_DIR / "t18_actions_prioritized.csv")
        t19 = pd.read_csv(TABLES_DIR / "t19_impact_sensitivity.csv")
        t20 = pd.read_csv(TABLES_DIR / "t20_measurement_plan.csv")
        # watchlist (t16) é subconjunto da jornada (t11); split (t21) ⊆ watchlist
        if not set(t16["account_id"]) <= set(t11["account_id"]):
            problems.append("t16 com contas fora de t11")
        if not set(t21["account_id"]) <= set(t16["account_id"]):
            problems.append("t21 com contas fora de t16")
        # t11: uma linha por conta e mesmo conjunto do raw accounts (derivado)
        acc = pd.read_csv(RAW_DIR / "ravenstack_accounts.csv")
        if len(t11) != t11["account_id"].nunique():
            problems.append("t11 com account_id duplicado")
        if set(t11["account_id"]) != set(acc["account_id"]):
            problems.append("t11 com contas != raw accounts")
        # t16: watch_rank sequencial 1..N (derivado, sem hardcode de 20)
        ranks = t16["watch_rank"].tolist()
        if ranks != list(range(1, len(t16) + 1)):
            problems.append("t16 watch_rank não sequencial 1..N")
        # backtest: detalhe (t14b) usa apenas cutoffs do resumo (t14)
        if not set(t14b["cutoff"]) <= set(t14["cutoff"]):
            problems.append("t14b com cutoff fora de t14")
        # planos/impacto (t19/t20) referem apenas ações priorizadas (t18)
        for name, df in [("t19", t19), ("t20", t20)]:
            if not set(df["action_id"]) <= set(t18["action_id"]):
                problems.append(f"{name} com action_id fora de t18")
        return (not problems), (f"relações estruturais entre tabelas OK; "
                                f"problemas={problems or 'nenhum'}")
    safe("C6-cross-tables", "contrato",
         "consistência estrutural entre tabelas (subconjuntos documentados)", _cross_tables)


# ----------------------------------------------------------------------------
# D. Higiene
# ----------------------------------------------------------------------------
def d_hygiene() -> None:
    def _forbidden_binaries() -> tuple[bool, str]:
        found = []
        for p in sorted(SOLUTION_DIR.rglob("*")):
            if p.is_dir() and p.name in FORBIDDEN_DIRS:
                found.append(f"dir:{p.relative_to(SOLUTION_DIR)}")
            elif p.is_file() and p.name.lower().endswith(FORBIDDEN_SUFFIXES):
                found.append(f"file:{p.relative_to(SOLUTION_DIR)}")
        return (not found), (f"binários/cache proibidos: {found or 'nenhum'}")
    safe("D1-binaries", "higiene",
         "zero .db/.duckdb/.sqlite/.pyc e venv/cache em solution/", _forbidden_binaries)

    def _personal_paths() -> tuple[bool, str]:
        hits = []
        for p in text_files_under(SOLUTION_DIR):
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                continue
            for tok in PERSONAL_PATH_TOKENS:
                if tok.lower() in txt.lower():
                    hits.append(f"{p.relative_to(SOLUTION_DIR)} <- '{tok}'")
        return (not hits), (f"paths pessoais em solution/: {hits or 'nenhum'}")
    safe("D2-personal-paths", "higiene", "zero paths pessoais em solution/", _personal_paths)

    def _secrets() -> tuple[bool, str]:
        hits = []
        for p in text_files_under(SOLUTION_DIR):
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                continue
            for pat in SECRET_PATTERNS:
                if pat.search(txt):
                    hits.append(f"{p.relative_to(SOLUTION_DIR)} <- {pat.pattern[:24]}")
        return (not hits), (f"segredos/chaves em solution/: {hits or 'nenhum'}")
    safe("D3-secrets", "higiene", "zero segredos/chaves em solution/", _secrets)

    def _network() -> tuple[bool, str]:
        hits = []
        for p in sorted(SRC_DIR.glob("*.py")):
            txt = p.read_text(encoding="utf-8", errors="replace")
            for m in NETWORK_IMPORTS.finditer(txt):
                hits.append(f"{p.name}:{txt[:m.start()].count(chr(10)) + 1} "
                            f"'{m.group(0).strip()}'")
        return (not hits), (f"imports de rede nos scripts: {hits or 'nenhum'}")
    safe("D4-network", "higiene", "zero imports de rede em solution/src/", _network)

    def _requirements() -> tuple[bool, str]:
        path = SUBMISSION_DIR / "requirements.txt"
        if not path.is_file():
            return False, "requirements.txt ausente"
        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.strip().startswith("#")]
        ok = all(re.match(r"^(pandas|matplotlib)(==|>=|<=|~=|!=|>|<)?\S*$", ln)
                 for ln in lines)
        pkgs = sorted(ln.split("==")[0] for ln in lines)
        both = {"pandas", "matplotlib"} <= set(pkgs)
        return (ok and both), (f"dependências declaradas: {pkgs} "
                               f"(mínimas: pandas+matplotlib; "
                               f"extras={sorted(set(pkgs) - {'pandas', 'matplotlib'}) or 'nenhum'} — informativos, não bloqueiam)")
    safe("D5-requirements", "higiene", "requirements.txt mínimo (pandas+matplotlib)", _requirements)

    def _run_artifacts() -> tuple[bool, str]:
        problems = []
        run_sh = SUBMISSION_DIR / "run.sh"
        makefile = SUBMISSION_DIR / "Makefile"
        if not run_sh.is_file():
            problems.append("run.sh ausente")
        else:
            if not os.access(run_sh, os.X_OK):
                problems.append("run.sh sem bit de execução")
            data = run_sh.read_bytes()
            if data.startswith(b"#!"):
                shebang = data.splitlines()[0].decode("utf-8", "replace")
                if "bash" not in shebang:
                    problems.append(f"shebang inesperado: {shebang}")
            else:
                problems.append("run.sh sem shebang")
            if b"\r\n" in data:
                problems.append("run.sh com CRLF")
        if not makefile.is_file():
            problems.append("Makefile ausente")
        else:
            if b"\r\n" in makefile.read_bytes():
                problems.append("Makefile com CRLF")
        return (not problems), (f"run.sh executável + Makefile presente; "
                                f"problemas={problems or 'nenhum'}")
    safe("D6-run-make", "higiene", "run.sh executável (sem CRLF) + Makefile", _run_artifacts)


# ----------------------------------------------------------------------------
# E. Sanidade dos scripts
# ----------------------------------------------------------------------------
def e_sanity() -> None:
    def _compile() -> tuple[bool, str]:
        bad = []
        for s in SCRIPTS:
            path = SRC_DIR / s
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except SyntaxError as exc:
                bad.append(f"{s}: {exc}")
        return (not bad), (f"compile() de {len(SCRIPTS)} scripts; erros={bad or 'nenhum'}")
    safe("E1-compile", "sanidade", "todos os scripts compilam (sem gerar .pyc)", _compile)

    def _imports() -> tuple[bool, str]:
        bad = []
        for s in SCRIPTS:
            path = SRC_DIR / s
            mod = f"it06_{s.replace('.py', '')}"
            try:
                spec = importlib.util.spec_from_file_location(mod, path)
                if spec is None or spec.loader is None:
                    bad.append(f"{s}: spec inválido")
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception as exc:  # noqa: BLE001 — falha de import é diagnóstico
                bad.append(f"{s}: {type(exc).__name__}: {exc}")
        return (not bad), (f"import de {len(SCRIPTS)} scripts; erros={bad or 'nenhum'}")
    safe("E2-imports", "sanidade", "todos os scripts importam sem erro", _imports)


# ----------------------------------------------------------------------------
# F. Relatório executivo (Iteração 07) — estrutura, links, claims e âncoras
# ----------------------------------------------------------------------------
# Claims proibidos em contexto afirmativo (mesma semântica do gerador 07:
# menção com negação explícita é permitida — o relatório cita termos apenas
# para negá-los/proibi-los).
FORBIDDEN_CLAIMS = [
    "receita perdida", "receita salva", "receita recuperada", "revenue saved",
    "revenue lost", "forecast", "ROI", "eventos evitados", "evitados",
    "prova causal", "causa provada", "é causado", "causa do churn é",
    "churn é causado", "receita em risco",
]
_NEG_MARKERS = ["não", "sem", "nunca", "proibido", "evita", "evite",
                "evitar", "fora", "≠", "ausência", "nenhum"]


def _affirmative_use(tok: str, text: str) -> bool:
    for m in re.finditer(re.escape(tok), text):
        ctx = text[max(0, m.start() - 90):m.end() + 90]
        if not any(nm in ctx for nm in _NEG_MARKERS):
            return True
    return False


def _cell_str(df: pd.DataFrame, value_col: str, key_col: str, key: str) -> str:
    return str(df[df[key_col] == key][value_col].iloc[0])


def _report_anchors() -> list[tuple[str, str]]:
    """Números-chave re-derivados das tabelas (sem reimplementar análise)."""
    t01 = pd.read_csv(TABLES_DIR / "t01_monthly_series.csv")
    t03 = pd.read_csv(TABLES_DIR / "t03_onboarding_buckets.csv")
    t03b = pd.read_csv(TABLES_DIR / "t03b_onboarding_accounts.csv")
    t05 = pd.read_csv(TABLES_DIR / "t05_usage_monthly.csv")
    t10 = pd.read_csv(TABLES_DIR / "t10_hypothesis_verdicts.csv")
    t15 = pd.read_csv(TABLES_DIR / "t15_priority_segments.csv")
    t16 = pd.read_csv(TABLES_DIR / "t16_watchlist_top20.csv")
    t19 = pd.read_csv(TABLES_DIR / "t19_impact_sensitivity.csv")
    acc = pd.read_csv(RAW_DIR / "ravenstack_accounts.csv")
    events = pd.read_csv(RAW_DIR / "ravenstack_churn_events.csv")
    panel = pd.read_csv(PROCESSED_DIR / "account_month.csv")

    def br(v: float, nd: int = 2) -> str:
        return f"{v:.{nd}f}".replace(".", ",")

    def pint(v: int) -> str:
        return f"{v:,}".replace(",", ".")

    dec = t01[t01["month"] == "2024-12"].iloc[0]
    prev6 = t01[t01["month"].isin(
        ["2024-06", "2024-07", "2024-08", "2024-09", "2024-10", "2024-11"])]
    r1_total = int(t03["mrr_sum"].sum())
    r1_le90 = int(t03[t03["bucket"].isin(
        ["0d", "1-30d", "31-60d", "61-90d"])]["mrr_sum"].sum())
    fe90 = t03b[t03b["window_days"] == 90].iloc[0]
    cur = int(panel[panel["month"] == "2024-12"]["winner_mrr"].sum())
    top20 = int(t16["current_winner_mrr"].sum())
    s1 = t15[t15["segment"] == "S1"].iloc[0]
    imp_base = t19[t19["scenario"] == "base"].iloc[0]
    u2023 = int(t05[t05["month"].str.startswith("2023")]["rows_raw_primary"].sum())
    u2024 = int(t05[t05["month"].str.startswith("2024")]["rows_raw_primary"].sum())
    h3 = _cell_str(t10, "numbers", "hypothesis", "H3")
    h4 = _cell_str(t10, "numbers", "hypothesis", "H4")
    h9 = _cell_str(t10, "numbers", "hypothesis", "H9")
    med_int = re.search(r"mediana por conta: [\d.]+ -> [\d.]+ \(([\d.]+)%\)",
                        h3).group(1).replace(".", ",") + "%"
    h4m = re.search(r"zero-uso: churn ([\d.]+)% vs controle ([\d.]+)%",
                    h4)
    h9s = re.search(r"share ([\d.]+)%, ratio ([\d.]+)", h9)
    return [
        ("taxa dez/24", br(dec["rate_first_events_pct"]) + "%"),
        ("mediana 6m", br(prev6["rate_first_events_pct"].median()) + "%"),
        ("episódios dez", f"{int(dec['events_total'])} episódios"),
        ("primeiros dez", f"{int(dec['first_events'])} são"),
        ("R1 total", pint(r1_total)), ("R1 ≤90d", pint(r1_le90)),
        ("R1 ≤90d %", br(r1_le90 / r1_total * 100, 1) + "%"),
        ("fe90 %", br(fe90["share_of_event_accounts_pct"], 1) + "%"),
        ("uso %", "+" + br((u2024 - u2023) / u2023 * 100, 1) + "%"),
        ("intensidade mediana", med_int),
        ("zero-uso churn", h4m.group(1).replace(".", ",") + "%"),
        ("zero-uso controle", h4m.group(2).replace(".", ",") + "%"),
        ("h9 share", h9s.group(1).replace(".", ",") + "%"),
        ("S1 n", str(int(s1["N"]))),
        ("S1 mrr", pint(int(s1["current_mrr_sum"]))),
        ("top20 mrr", pint(top20)), ("top20 share", br(top20 / cur * 100, 1) + "%"),
        ("cur mrr", pint(cur)),
        ("incidência base", br(imp_base["incidence_90d"], 4)),
        ("eventos afetados base", br(imp_base["events_affected_90d"], 1)),
        ("exposição base", pint(int(imp_base["expected_exposure_affected_mrr"]))),
        ("snapshot", pint(int(acc["churn_flag"].sum()))),
        ("eventos total", pint(len(events))),
    ]


def f_report() -> None:
    def _present() -> tuple[bool, str]:
        p = REPORT_PATH
        if not p.is_file() or p.stat().st_size == 0:
            return False, "ausente ou vazio"
        return True, f"{p.stat().st_size} bytes"
    safe("F1-report", "relatório executivo",
         "report-executivo.md presente e não vazio", _present)

    def _links() -> tuple[bool, str]:
        if not REPORT_PATH.is_file():
            return False, "report ausente"
        txt = REPORT_PATH.read_text(encoding="utf-8")
        links = [l.strip() for l in
                 re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", txt)]
        broken = [l for l in links
                  if not l.startswith("http")
                  and not (SOLUTION_DIR / l).resolve().is_file()]
        return (not broken), (f"links relativos={len(links)}; "
                              f"quebrados={broken or 'nenhum'}")
    safe("F2-report-links", "relatório executivo",
         "links relativos do report existem", _links)

    def _images() -> tuple[bool, str]:
        txt = REPORT_PATH.read_text(encoding="utf-8")
        links = [l.strip() for l in
                 re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", txt)]
        imgs = [l for l in links if l.endswith(".png")]
        dups = sorted({i for i in imgs if imgs.count(i) > 1})
        return (len(imgs) == 6 and not dups), (
            f"imagens={len(imgs)}; repetidas={dups or 'nenhuma'}")
    safe("F3-report-images", "relatório executivo",
         "exatamente 6 imagens, cada uma usada 1x", _images)

    def _wordcount() -> tuple[bool, str]:
        txt = REPORT_PATH.read_text(encoding="utf-8")
        wc = len(txt.split())
        return (1400 <= wc <= 2400), f"palavras={wc} (budget 1.400–2.400)"
    safe("F4-report-wordcount", "relatório executivo",
         "word count dentro do budget", _wordcount)

    def _claims() -> tuple[bool, str]:
        txt = REPORT_PATH.read_text(encoding="utf-8")
        hits = [tok for tok in FORBIDDEN_CLAIMS
                if tok in txt and _affirmative_use(tok, txt)]
        return (not hits), (f"claims afirmativos={hits or 'nenhum'}")
    safe("F5-report-claims", "relatório executivo",
         "zero claims proibidos em contexto afirmativo", _claims)

    def _accounts() -> tuple[bool, str]:
        txt = REPORT_PATH.read_text(encoding="utf-8")
        cited = set(re.findall(r"A-[0-9a-f]{6}", txt))
        t16 = set(pd.read_csv(TABLES_DIR / "t16_watchlist_top20.csv")["account_id"])
        outside = sorted(cited - t16)
        return (not outside), (f"contas citadas={len(cited)}; "
                               f"fora da t16={outside or 'nenhum'}")
    safe("F6-report-accounts", "relatório executivo",
         "contas do report são subconjunto da t16", _accounts)

    def _actions() -> tuple[bool, str]:
        txt = REPORT_PATH.read_text(encoding="utf-8")
        cited = set(re.findall(r"ACT-\d\d", txt))
        t18 = set(pd.read_csv(TABLES_DIR / "t18_actions_prioritized.csv")["action_id"])
        outside = sorted(cited - t18)
        return (not outside), (f"ações citadas={len(cited)}; "
                               f"fora da t18={outside or 'nenhum'}")
    safe("F7-report-actions", "relatório executivo",
         "ações do report são subconjunto da t18", _actions)

    def _anchors() -> tuple[bool, str]:
        txt = REPORT_PATH.read_text(encoding="utf-8")
        missing = [label for label, val in _report_anchors() if val not in txt]
        return (not missing), (f"âncoras re-derivadas={len(_report_anchors())}; "
                               f"ausentes={missing or 'nenhum'}")
    safe("F8-report-anchors", "relatório executivo",
         "números-chave do report == tabelas (re-derivados em runtime)",
         _anchors)


# ----------------------------------------------------------------------------
# D7. Gate de integridade do próprio verificador: ids de check únicos
# ----------------------------------------------------------------------------
def check_uid_uniqueness() -> None:
    """Registra D7-uids por ÚLTIMO: ids de check duplicados quebrariam o
    diagnóstico (ex.: B4-md-README.md emitido 2× na versão anterior) — um
    duplicado vira FAIL explícito em vez de ambiguidade silenciosa."""
    seen: set[str] = set()
    dups = sorted({uid for uid in (c["uid"] for c in CHECKS)
                   if uid in seen or seen.add(uid)})
    check("D7-uids", "higiene", "ids de check únicos (sem colisão de diagnóstico)",
          not dups, f"ids duplicados={dups or 'nenhum'}")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main() -> int:
    a_manifest()
    b_parseable()
    c_consistency()
    d_hygiene()
    e_sanity()
    f_report()
    check_uid_uniqueness()  # último: valida inclusive os ids emitidos acima

    for c in CHECKS:
        flag = "PASS" if c["ok"] else "FAIL"
        print(f"[{flag}] {c['uid']} ({c['section']}): {c['desc']} — {c['detail']}")

    n_pass = sum(1 for c in CHECKS if c["ok"])
    n_fail = len(CHECKS) - n_pass
    print(f"[verify] resumo: {n_pass} PASS / {n_fail} FAIL")
    if n_fail:
        print("[verify] falhas encontradas — diagnósticos acima. "
              "Se outputs derivados estiverem ausentes/alterados, reexecute "
              "'./run.sh' (ou 'make all'); raw data e process-log nunca são "
              "regenerados pelo pipeline.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())