#!/bin/bash

# Stop execution immediately if any command fails
set -e

echo "================================================="
echo "🧪 STARTING NAME THAT YANKEE FULL TEST SUITE..."
echo "================================================="

# Sync fixtures with latest production files
echo "🔄 Synchronizing test fixtures..."
# Use || true to prevent script exit if files are identical
cp quiz.html tests/fixtures/www/quiz.html || true
cp style.css tests/fixtures/www/style.css || true
# (js/ is already symlinked in the fixture directory)

# Run Python Unit Tests
echo ""
echo "▶️ [1/4] Running Python Backend Unit Tests..."
echo "-------------------------------------------------"
pytest tests/unit/ -v

# Run Python Automation Integration Tests
echo ""
echo "▶️ [2/4] Running Automation Integration Tests..."
echo "-------------------------------------------------"
pytest test_automation.py -v

# Run Python UI/E2E Tests
echo ""
echo "▶️ [3/4] Running Python E2E & Accessibility Tests..."
echo "-------------------------------------------------"
pytest test_yankee_site.py -v

# Run JavaScript Tests (using npm test to include Firebase Emulator)
echo ""
echo "▶️ [4/4] Running JavaScript Frontend & Security Rules Tests..."
echo "-------------------------------------------------"
npm test

echo ""
echo "================================================="
echo "✅ SUCCESS! ALL TESTS PASSED ACROSS ALL LAYERS!"
echo "================================================="
