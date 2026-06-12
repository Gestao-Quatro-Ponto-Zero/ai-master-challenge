@echo off
REM Sales Dashboard Setup Script for Windows
REM Run this script to install all dependencies and set up the project

echo.
echo 🚀 Sales Pipeline Dashboard - Setup
echo ====================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed
    echo Please install Node.js from https://nodejs.org/ ^(LTS version recommended^)
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✅ Node.js version: %NODE_VERSION%
echo.

echo 📦 Installing dependencies...
call npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo 📂 Loading data from CSV files...
call npm run setup
if %errorlevel% neq 0 (
    echo ❌ Failed to load data
    pause
    exit /b 1
)

echo.
echo ✅ Setup completed successfully!
echo.
echo 📋 Next steps:
echo   Option 1 - Run everything together:
echo     npm start
echo.
echo   Option 2 - Run separately in different terminal windows:
echo     Terminal 1: npm run server
echo     Terminal 2: npm run dev
echo.
echo Then open: http://localhost:5173 in your web browser
echo.
echo 💡 Tip: npm start will run both servers together
echo.
pause
