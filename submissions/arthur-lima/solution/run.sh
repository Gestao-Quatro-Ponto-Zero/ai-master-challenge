#!/usr/bin/env bash
set -euo pipefail
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"
echo "[1/3] Verificando Python 3.12..."
if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN=python3.12
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
else
    echo "[ERRO] Instale Python 3.12."
    exit 1
fi
if ! "$PYTHON_BIN" -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)'; then
    echo "[ERRO] Este conjunto de dependencias requer Python 3.12."
    exit 1
fi
if [ ! -f "venv/bin/python" ]; then
    "$PYTHON_BIN" -m venv venv
fi
if ! venv/bin/python -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)'; then
    echo "[ERRO] Renomeie o venv de outra versao e execute novamente com Python 3.12."
    exit 1
fi
echo "[2/3] Sincronizando dependencias, inclusive em ambientes existentes..."
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m pip check
venv/bin/python -m pytest tests/test_engine.py -q
if [ "${1:-}" = "--check" ]; then
    exit 0
fi
echo "[3/3] Acesse http://localhost:8501 no navegador."
exec venv/bin/python -m streamlit run app.py
