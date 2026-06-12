@echo off
REM Sales Dashboard Start Script for Windows

cd /d "%~dp0"

echo.
echo 🚀 Starting Sales Pipeline Dashboard
echo ====================================
echo.

echo Starting API Server on http://localhost:3001...
start cmd /k "npm run server"

timeout /t 2

echo.
echo Starting Dev Server on http://localhost:5173...
echo Open http://localhost:5173 in your browser
echo.
echo Press Ctrl+C in either window to stop the servers
echo.

npm run dev
