#!/bin/bash
# ABOUTME: Bootstraps the development environment, installing Python and Node.js dependencies.
# ABOUTME: Prepares the local environment for running the full regression test suite.

set -e

echo "================================================="
echo "🚀 BOOTSTRAPPING NAME THAT YANKEE DEV ENV..."
echo "================================================="

# 1. Python venv
echo "🐍 Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt -r test_requirements.txt --quiet

# 2. Node modules
echo "📦 Installing Node.js dependencies..."
npm install --silent

# 3. Playwright browsers
echo "🌐 Installing Playwright browsers..."
npx playwright install chromium --with-deps

echo ""
echo "================================================="
echo "✅ BOOTSTRAP COMPLETE! RUN ./run_tests.sh TO VERIFY."
echo "================================================="
