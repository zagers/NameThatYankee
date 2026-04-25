#!/bin/bash

# Stop execution immediately if any command fails
set -e

echo "================================================="
echo "🧪 STARTING NAME THAT YANKEE FULL TEST SUITE..."
echo "================================================="

# Sync fixtures with latest production files
echo "🔄 Synchronizing test fixtures..."
mkdir -p tests/fixtures/www/

# Ensure required assets are linked or copied
[ ! -L tests/fixtures/www/js ] && ln -s ../../../js tests/fixtures/www/js
[ ! -L tests/fixtures/www/images ] && ln -s ../../../images tests/fixtures/www/images
[ ! -L tests/fixtures/www/firebase-config.js ] && ln -s ../../../firebase-config.js tests/fixtures/www/firebase-config.js
[ ! -L tests/fixtures/www/all_players.js ] && ln -s ../../../all_players.js tests/fixtures/www/all_players.js

# Copy core pages and a representative historical page for E2E tests
# Use || true to prevent script exit if files are identical
cp index.html tests/fixtures/www/index.html || true
cp quiz.html tests/fixtures/www/quiz.html || true
cp instructions.html tests/fixtures/www/instructions.html || true
cp analytics.html tests/fixtures/www/analytics.html || true
cp style.css tests/fixtures/www/style.css || true
cp stats_summary.json tests/fixtures/www/stats_summary.json || true
cp 2026-04-19.html tests/fixtures/www/2026-04-19.html || true

# Use local venv pytest if available, otherwise fall back to global
if [ -f .venv/bin/pytest ]; then
  PYTEST=.venv/bin/pytest
elif [ -f venv_new/bin/pytest ]; then
  PYTEST=venv_new/bin/pytest
else
  PYTEST=pytest
fi

# Run Python Unit Tests
echo ""
echo "▶️ [1/4] Running Python Backend Unit Tests..."
echo "-------------------------------------------------"
$PYTEST tests/unit/ -v

# Run Python Automation Integration Tests
echo ""
echo "▶️ [2/4] Running Automation Integration Tests..."
echo "-------------------------------------------------"
$PYTEST test_automation.py -v

# Run Python UI/E2E Tests
echo ""
echo "▶️ [3/4] Running Python E2E & Accessibility Tests..."
echo "-------------------------------------------------"
$PYTEST test_yankee_site.py test_seo_dynamic.py -v

# Run JavaScript Tests (using npm test to include Firebase Emulator)
echo ""
echo "▶️ [4/4] Running JavaScript Frontend & Security Rules Tests..."
echo "-------------------------------------------------"
npm test

echo ""
echo "================================================="
echo "✅ SUCCESS! ALL TESTS PASSED ACROSS ALL LAYERS!"
echo "================================================="
