#!/usr/bin/env bash
# =====================================================================
#  🎯 G4 Educação — AI Master Challenge 003: RevOps Lead Scorer
#  Candidato: Arthur Lima
# =====================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "====================================================================="
echo " 🎯 G4 Educação — AI Master Challenge 003: RevOps Lead Scorer"
echo " Candidato: Arthur Lima"
echo "====================================================================="
echo ""

echo "[1/3] Verificando ambiente Python..."
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] python3 não encontrado. Instale Python 3.10+ para prosseguir."
    exit 1
fi

if [ ! -f "venv/bin/activate" ]; then
    echo "[2/3] Criando ambiente virtual venv e instalando dependências..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "[2/3] Ativando ambiente virtual venv..."
    source venv/bin/activate
fi

echo ""
echo "[TESTES] Executando suíte de testes automatizados com pytest..."
python -m pytest tests/test_engine.py -q
echo "[TESTES OK] Todos os testes passaram com sucesso!"

echo ""
echo "[3/3] Iniciando aplicação Streamlit (RevOps Copilot)..."
echo "Acesse no seu navegador em: http://localhost:8501"
streamlit run app.py
