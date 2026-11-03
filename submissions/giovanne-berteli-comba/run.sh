#!/usr/bin/env bash
# Local Linux bootstrap: no system Python, pip, venv package or sudo required.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$root"
prepare_only=false
overview_only=false
case "${1:-}" in
  --prepare-only) prepare_only=true ;;
  --overview) overview_only=true ;;
  --help|-h) printf '%s\n' 'Uso: bash run.sh [--overview | --prepare-only]' '--overview: consulta agregados sem datasets, banco ou treino.' 'Sem opção: prepara e abre a triagem completa; --prepare-only: somente prepara.'; exit 0 ;;
  '') ;;
  *) printf '%s\n' 'Opção desconhecida. Use bash run.sh --help.' >&2; exit 2 ;;
esac
if (( $# > 1 )); then printf '%s\n' 'Use --overview, --prepare-only ou nenhum argumento.' >&2; exit 2; fi
fail() { printf '\nNão foi possível iniciar: %s\n' "$*" >&2; exit 1; }
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]] || fail 'O setup automático foi preparado para Linux x86_64 com glibc. Consulte docs/prototype.md para os limites.'
for dependency in flock tar sha256sum; do
  command -v "$dependency" >/dev/null || fail "Comando básico ausente: $dependency. Instale-o antes de repetir este comando."
done
mkdir -p .runtime/bootstrap
exec 9>.runtime/setup.lock
flock -n 9 || fail 'Outra preparação está em andamento. Aguarde sua conclusão e execute novamente.'
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export UV_CACHE_DIR="$root/.runtime/uv-cache"
export UV_PYTHON_INSTALL_DIR="$root/.runtime/python"
export UV_NO_PROGRESS=1 UV_NATIVE_TLS=true
python="$root/.venv/bin/python"

prepare_uv() {
  local archive="$root/.runtime/bootstrap/uv-0.9.7.tar.gz"
  local checksum=b26fcc8dfa1c39b5a5613445af3be3eefda45d9a39359bee271eafe34913583e
  local url=https://github.com/astral-sh/uv/releases/download/0.9.7/uv-x86_64-unknown-linux-gnu.tar.gz
  if [[ ! -f "$archive" ]]; then
    printf '%s\n' 'Preparando gerenciador local uv 0.9.7 (download oficial com checksum fixo)…'
    if command -v curl >/dev/null; then
      curl --fail --silent --show-error --location --retry 2 --connect-timeout 15 --max-time 180 "$url" -o "$archive.part" || fail 'Falha no download do uv. Verifique conexão, certificados/proxy e execute novamente.'
    elif command -v wget >/dev/null; then
      wget --quiet --timeout=180 "$url" -O "$archive.part" || fail 'Falha no download do uv. Verifique a conexão e execute novamente.'
    else
      fail 'É necessário curl ou wget para o primeiro download. Não é necessário instalar python3-venv.'
    fi
    printf '%s  %s\n' "$checksum" "$archive.part" | sha256sum --check --status || fail 'Checksum do download do uv não confere. O arquivo não será executado.'
    mv -- "$archive.part" "$archive"
  fi
  printf '%s  %s\n' "$checksum" "$archive" | sha256sum --check --status || fail 'Cache do uv alterado. Confira .runtime/bootstrap/uv-0.9.7.tar.gz; nada será executado.'
  tar -xzOf "$archive" uv-x86_64-unknown-linux-gnu/uv >.runtime/bootstrap/uv.tmp
  chmod 700 .runtime/bootstrap/uv.tmp
  mv -- .runtime/bootstrap/uv.tmp .runtime/bootstrap/uv
  uv="$root/.runtime/bootstrap/uv"
}

printf '%s\n' '[1/4] Conferindo o ambiente isolado…'
if [[ ! -x "$python" ]] || ! "$python" -I -c 'import sys; assert sys.version_info[:3] == (3,12,3) and sys.prefix != sys.base_prefix' >/dev/null 2>&1; then
  prepare_uv
  if [[ -e .venv || -L .venv ]]; then
    backup="$(mktemp -d "$root/.runtime/previous-venv-XXXXXX")"
    mv -- .venv "$backup/venv"
    printf 'Ambiente anterior preservado em %s\n' "$backup/venv"
  fi
  "$uv" --no-config venv --python 3.12.3 --managed-python .venv || fail 'Não foi possível fornecer Python 3.12.3. Verifique acesso ao GitHub, espaço em disco e certificados.'
fi
if ! "$python" -I -c 'import sys; sys.path.insert(0,"solution"); from triage.artifacts import ROOT,check_environment; check_environment(ROOT)' >/dev/null 2>&1; then
  [[ -n "${uv:-}" ]] || prepare_uv
  printf '%s\n' 'Sincronizando as versões fixadas das dependências locais…'
  "$uv" --no-config pip sync --python "$python" --index-url https://pypi.org/simple --only-binary :all: requirements.lock || fail 'Falha ao instalar dependências. Verifique acesso ao PyPI e espaço em disco; execute novamente para retomar.'
fi
entrypoint=solution/app.py
if "$overview_only"; then
  printf '%s\n' 'Consulta: usando apenas agregados salvos, sem baixar datasets ou treinar.'
  entrypoint=solution/overview_app.py
else
  "$python" -I solution/setup_triage.py
fi
flock -u 9
exec 9>&-
if "$prepare_only"; then exit 0; fi
port="${STREAMLIT_SERVER_PORT:-8501}"
printf '\nAbrindo a interface local em http://127.0.0.1:%s (Ctrl+C para encerrar)…\n' "$port"
exec "$python" -m streamlit run "$entrypoint" --server.port "$port" --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
