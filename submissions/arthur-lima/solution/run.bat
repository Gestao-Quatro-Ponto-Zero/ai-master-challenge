@echo off
chcp 65001 > nul
echo =====================================================================
echo  🎯 G4 Educação — AI Master Challenge 003: RevOps Lead Scorer
echo  Candidato: Arthur Lima
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Verificando ambiente Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Python não foi encontrado no PATH. Instale o Python 3.10+ e tente novamente.
    pause
    exit /b 1
)

if not exist "venv\Scripts\activate.bat" (
    echo [2/3] Criando ambiente virtual venv e instalando dependências...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao criar o ambiente virtual venv.
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao instalar dependências de requirements.txt.
        pause
        exit /b 1
    )
) else (
    echo [2/3] Ativando ambiente virtual venv...
    call venv\Scripts\activate.bat
)

echo.
echo [TESTES] Executando suíte de testes automatizados com pytest...
python -m pytest tests/test_engine.py -q
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha na execução da suíte de testes. Abortando inicialização.
    pause
    exit /b 1
) else (
    echo [TESTES OK] Todos os testes passaram com sucesso!
)

echo.
echo [3/3] Iniciando aplicação Streamlit (RevOps Copilot)...
echo Acesse no seu navegador em: http://localhost:8501
streamlit run app.py
pause
