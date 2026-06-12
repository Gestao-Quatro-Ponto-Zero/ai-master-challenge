#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}  ╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}  ║   Sales Pipeline Dashboard — Quick Start  ║${NC}"
echo -e "${BLUE}  ╚══════════════════════════════════════════╝${NC}"
echo ""

if ! command -v node &> /dev/null; then
    echo -e "${RED}  ❌ Node.js is not installed${NC}"
    echo ""
    echo "  Download and install Node.js (LTS) from:"
    echo "  https://nodejs.org/"
    echo ""
    read -p "  Press Enter to open the download page, then re-run this script..."
    xdg-open "https://nodejs.org/" 2>/dev/null || open "https://nodejs.org/" 2>/dev/null
    exit 1
fi

echo -e "  ${GREEN}✅${NC} Node.js $(node --version)"

DIR="$(cd "$(dirname "$0")/sales-dashboard" && pwd)"
cd "$DIR"

if [ ! -d "node_modules" ]; then
    echo -e "  ${YELLOW}📦${NC} Installing dependencies (one-time setup)..."
    npm install --silent
    echo -e "  ${GREEN}✅${NC} Dependencies installed"
fi

if [ ! -f "data/sales.db" ]; then
    echo -e "  ${YELLOW}📂${NC} Loading data from CSV files..."
    npm run setup --silent 2>/dev/null
    echo -e "  ${GREEN}✅${NC} Data loaded"
fi

echo ""
echo -e "  ${GREEN}🚀${NC} Starting servers..."
echo ""

npm run server &
SERVER_PID=$!
sleep 2

xdg-open "http://localhost:5173" 2>/dev/null || open "http://localhost:5173" 2>/dev/null || true

trap "kill $SERVER_PID 2>/dev/null" EXIT

npm run dev
