#!/bin/bash

# Sales Dashboard Setup Script
# Run this script to install all dependencies and set up the project

set -e  # Exit on any error

echo "🚀 Sales Pipeline Dashboard - Setup"
echo "===================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org/ (LTS version recommended)"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

echo "📦 Installing dependencies..."
npm install

echo ""
echo "📂 Loading data from CSV files..."
npm run setup

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "  Option 1 - Run everything together:"
echo "    npm start"
echo ""
echo "  Option 2 - Run separately in different terminal windows:"
echo "    Terminal 1: npm run server"
echo "    Terminal 2: npm run dev"
echo ""
echo "Then open: http://localhost:5173 in your web browser"
echo ""
echo "💡 Tip: npm start will run both servers together"
