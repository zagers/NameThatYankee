# Name That Yankee - Test Suite

This project uses a multi-layered testing strategy to ensure reliability across the frontend, automation pipeline, and security configurations.

## 🚀 The Master Test Runner

The primary entry point for running **all** tests locally is the master shell script:

```bash
./run_tests.sh
```

**CRITICAL**: This script orchestrates the entire test lifecycle, including environment synchronization and multi-language test execution. 
*   **Maintenance**: If you add new test files or categories (e.g., new Vitest files or Python unit tests), ensure `./run_tests.sh` is updated to include them.
*   **Environment**: Always run this within your activated virtual environment (`source .venv/bin/activate`).

---

## Test Layers

### 1. Frontend & Security Tests (JavaScript/Vitest)
- **Framework**: Vitest with JSDOM and Firebase Emulators.
- **Location**: `tests/js/`
- **Categories**:
    - **Score Breakdown**: Logic for persistent score tracking and the Interactive Pill UI (`scoreBreakdown.test.js`).
    - **Detail Pages**: Verification of score display on individual player pages (`detail.test.js`).
    - **Core Engine**: Quiz mechanics, score calculation, and text normalization.
    - **Security Rules**: Validation of Firestore security rules.
- **Run Manually**: `npm test`

### 2. E2E & Accessibility Tests (Python/Playwright)
- **Framework**: Pytest with Playwright.
- **Location**: Root directory (`test_yankee_site.py`).
- **Categories**:
    - **Site Structure**: Layout and responsive design validation.
    - **Search & Filter**: Real-time gallery filtering and date searching.
    - **Visual Regressions**: Screenshot-based layout validation.
    - **Accessibility**: Automated Axe-core audits for WCAG compliance.
- **Run Manually**: `pytest test_yankee_site.py`

### 3. Automation Pipeline Unit Tests (Python/Pytest)
- **Framework**: Pytest.
- **Location**: `tests/unit/page_generator/`
- **Purpose**: Validates the Python logic for scraping stats, processing images, and generating HTML.
- **Run Manually**: `pytest tests/unit/`

### 4. Integration Tests
- **Location**: Root directory (`test_automation.py`).
- **Purpose**: Verifies the end-to-end workflow of the page generation tools.

---

## Setup Instructions

### Prerequisites
1. **Node.js 20+** (for frontend tests)
2. **Python 3.12+** (for automation and E2E tests)
3. **Firebase CLI** (for security rule testing)

### Installation
```bash
# 1. Install Node dependencies
npm install

# 2. Setup Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r test_requirements.txt

# 3. Install Playwright browsers
playwright install --with-deps
```

---

## Troubleshooting

### Common Issues

1. **Firebase Emulator Failure**:
   Ensure no other process is using the emulator ports (default 9150 for Firestore).
   
2. **Playwright Timeout**:
   E2E tests require the local server to be responsive. `run_tests.sh` handles this automatically by spinning up a background server on port 8001.

3. **Missing Fixtures**:
   If test images or pages are missing, `run_tests.sh` will attempt to sync them from the root directory to `tests/fixtures/www/`.

---

## Contributing

When adding new features:
1. **TDD Pattern**: Write a failing test in the appropriate layer before implementing.
2. **Update Runner**: If you create a new test *file type* or a new directory of tests, update `./run_tests.sh`.
3. **Update Documentation**: Ensure this README reflects any new major categories or prerequisites.
