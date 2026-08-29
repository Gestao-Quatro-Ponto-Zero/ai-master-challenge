#!/usr/bin/env bash
# ============================================================================
# run.sh — pipeline reprodutível em UM comando (Iterações 06–07)
# Challenge 001 (Diagnóstico de Churn) · Jose Nascimento
#
# Executa os estágios 01→05, o gerador do relatório executivo (07) e, ao
# final, o verificador (solution/src/06_verify_pipeline.py). Determinístico,
# offline (zero rede), sem paths pessoais; exit code 0 = sucesso, nonzero =
# falha com mensagem.
#
# Uso:  ./run.sh          (qualquer CWD; paths resolvidos pelo próprio script)
#       make all          (mesmo pipeline — fonte única, sem lógica duplicada)
# ============================================================================
set -euo pipefail

# Resolve o diretório próprio (funciona de qualquer CWD; sem paths pessoais).
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Não gerar __pycache__ (tree limpa após regeneração; ver D1 do verificador).
export PYTHONDONTWRITEBYTECODE=1

PY="${PYTHON:-python3}"

log() { printf '[pipeline] %s\n' "$*"; }
die() { printf '[pipeline] ERRO: %s\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Preflight 1 — interpretador e dependências documentadas (requirements.txt)
# ---------------------------------------------------------------------------
command -v "$PY" >/dev/null 2>&1 \
    || die "python3 não encontrado no PATH ('$PY'). Instale Python >= 3.11 e 'pip install -r requirements.txt'."

if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
    PYVER="$("$PY" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo 'desconhecida')"
    die "Python >= 3.11 exigido (testado em 3.12.3); encontrado: $PYVER."
fi

if ! "$PY" -c 'import pandas, matplotlib' >/dev/null 2>&1; then
    die "dependências Python ausentes (pandas/matplotlib). Instale com: $PY -m pip install -r requirements.txt"
fi

# ---------------------------------------------------------------------------
# Preflight 2 — dados commitados presentes (nada é baixado; sem rede)
# ---------------------------------------------------------------------------
MISSING=0
for f in solution/data/raw/ravenstack_accounts.csv \
         solution/data/raw/ravenstack_subscriptions.csv \
         solution/data/raw/ravenstack_feature_usage.csv \
         solution/data/raw/ravenstack_support_tickets.csv \
         solution/data/raw/ravenstack_churn_events.csv; do
    if [ ! -s "$f" ]; then
        printf '[pipeline] ERRO: dado bruto ausente ou vazio: %s\n' "$f" >&2
        MISSING=1
    fi
done
if [ "$MISSING" -ne 0 ]; then
    die "dados brutos incompletos (listados acima). Eles são commitados no repo; não há download em runtime."
fi

# ---------------------------------------------------------------------------
# Estágios 01→05 + gerador 07 — execução sequencial com propagação de exit
# code. Cada estágio roda num processo python isolado; medimos tempo de
# relógio (SECONDS) e pico de memória aproximado via ru_maxrss (ver D5 das
# decisões).
# ---------------------------------------------------------------------------
run_stage() {
    local name="$1"
    local t0="$SECONDS"
    log "estágio $name: início"
    set +e
    "$PY" - "$name" <<'PYEOF'
import resource, subprocess, sys
name = sys.argv[1]
rc = subprocess.run([sys.executable, "solution/src/%s.py" % name]).returncode
if rc != 0:
    sys.exit(rc)
rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
# Linux: KB; macOS: bytes (normalização para KB)
rss_kb = rss if sys.platform.startswith("linux") else rss // 1024
print("[pipeline] %s: pico de memória aproximado: %d KB (ru_maxrss; aprox., não benchmark)" % (name, rss_kb))
PYEOF
    rc=$?
    set -e
    if [ "$rc" -ne 0 ]; then
        printf '[pipeline] ERRO: estágio %s falhou (exit %s). Estágios subsequentes NÃO foram executados. Em falhas tratadas (schema/validação) o relatório do estágio é regravado com FAILs estruturados; em falha inesperada o diagnóstico acima pode conter traceback e o relatório pode ficar desatualizado — corrija a causa e reexecute.\n' "$name" "$rc" >&2
        exit "$rc"
    fi
    log "estágio $name: OK em $((SECONDS - t0))s"
}

t0_total="$SECONDS"
run_stage 01_ingest_audit
run_stage 02_reconcile_churn
run_stage 03_root_cause
run_stage 04_lifecycle_watchlist
run_stage 05_actions_impact
run_stage 07_generate_executive_report

# ---------------------------------------------------------------------------
# Verificação final — mesmo verificador de `make verify`
# ---------------------------------------------------------------------------
log "verificação final: solution/src/06_verify_pipeline.py"
set +e
"$PY" solution/src/06_verify_pipeline.py
vrc=$?
set -e
if [ "$vrc" -ne 0 ]; then
    printf '[pipeline] ERRO: a verificação final falhou (exit %s) — veja os diagnósticos acima.\n' "$vrc" >&2
    exit "$vrc"
fi

log "pipeline concluído: 6 estágios (01–05, 07) + verificação OK em $((SECONDS - t0_total))s (offline; determinístico)."