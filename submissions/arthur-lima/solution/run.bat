@echo off
setlocal
chcp 65001 > nul
cd /d "%~dp0"
echo [1/3] Verificando Python 3.12...
set "PYTHON_CMD="
python -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :python_ready
)
py -3.12 -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
if errorlevel 1 goto :python_error
set "PYTHON_CMD=py -3.12"

:python_ready
if not exist "venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 goto :failed
)
"venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)"
if errorlevel 1 (
    echo [ERRO] O venv existente usa outra versao. Renomeie-o e execute novamente com Python 3.12.
    exit /b 1
)
echo [2/3] Sincronizando dependencias, inclusive em ambientes existentes...
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed
"venv\Scripts\python.exe" -m pip check
if errorlevel 1 goto :failed

echo [TESTES] Executando suite automatizada...
"venv\Scripts\python.exe" -m pytest tests/test_engine.py -q
if errorlevel 1 goto :failed
if /i "%~1"=="--check" exit /b 0

echo [3/3] Acesse http://localhost:8501 no navegador.
"venv\Scripts\python.exe" -m streamlit run app.py
exit /b %errorlevel%

:python_error
echo [ERRO] Instale Python 3.12, acessivel por python no PATH ou pelo launcher py -3.12.
exit /b 1

:failed
echo [ERRO] Falha na preparacao ou nos testes. Inicializacao abortada.
exit /b 1
