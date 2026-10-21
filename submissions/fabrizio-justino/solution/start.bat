@echo off
REM Sobe backend (8000) e frontend (3001) em janelas separadas e abre o navegador.
REM Primeira execucao: instala as dependencias antes.
cd /d "%~dp0"

if not exist "frontend\node_modules" (
  echo Instalando dependencias do frontend...
  pushd frontend && call npm install && popd
)
python -m pip install -q -r backend\requirements.txt

start "Lead Scorer - API" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --port 8000"
start "Lead Scorer - Web" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 8 /nobreak >nul
start http://localhost:3001
