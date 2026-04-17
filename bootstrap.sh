#!/bin/bash
# ABOUTME: Bootstraps the development environment, installing Python and Node.js dependencies.
# ABOUTME: Prepares the local environment for running the full regression test suite.

set -e

echo "================================================="
echo "🚀 BOOTSTRAPPING NAME THAT YANKEE DEV ENV..."
echo "================================================="

# 1. System Check
echo "🔍 Checking system dependencies..."
if ! command -v java &> /dev/null; then
    echo "❌ Java not found. Please install Java 21+ (e.g., sudo apt install openjdk-21-jre-headless)"
    exit 1
fi

JAVA_VER=$(java -version 2>&1 | head -n 1 | awk -F '"' '{print $2}' | awk -F '.' '{print $1}')
if [ "$JAVA_VER" -lt 21 ]; then
    echo "⚠️ Warning: Found Java version $JAVA_VER. Firebase Emulator requires Java 21+."
    echo "   If you have a local JDK, set JAVA_HOME before running tests."
fi

# 2. Python venv
echo "🐍 Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    if ! python3 -m venv .venv 2>/dev/null; then
        echo "❌ python3-venv is not installed. Please run: sudo apt install python3-venv"
        exit 1
    fi
fi
source .venv/bin/activate
pip install -r requirements.txt -r test_requirements.txt --quiet

# 3. Node modules
echo "📦 Installing Node.js dependencies..."
npm install --silent

# 4. Playwright browsers
echo "🌐 Installing Playwright browsers..."
npx playwright install chromium --with-deps

# 5. Summary
echo ""
echo "📊 Environment Diagnostics:"
java -version 2>&1 | head -n 1
python3 --version
node --version
npm --version
echo "Venv: $([[ "$VIRTUAL_ENV" != "" ]] && echo "Active" || echo "Inactive")"

echo ""
echo "================================================="
echo "✅ BOOTSTRAP COMPLETE! RUN ./run_tests.sh TO VERIFY."
echo "================================================="
