#!/bin/bash

# Sales Dashboard Start Script
# Simple script to start the dashboard

set -e

# Navigate to script directory
cd "$(dirname "$0")"

echo "🚀 Starting Sales Pipeline Dashboard"
echo "===================================="
echo ""
echo "Starting API Server on http://localhost:3001..."
npm run server &
SERVER_PID=$!

sleep 2

echo ""
echo "Starting Dev Server on http://localhost:5173..."
npm run dev

# Kill the server process when dev server is stopped
trap "kill $SERVER_PID" EXIT
