# Identity PASS and Evergreen Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize the codebase by adding `ABOUTME: ` headers to all files and removing temporal language from internal comments and symbols.

**Architecture:** This is a systematic documentation and cleanup sweep. I will use scripted approaches for the headers where possible, followed by targeted manual edits for the Evergreen Pass to ensure context is preserved while removing temporal markers from comments and symbols only. Public-facing UI text is preserved. `GEMINI.md` and `JOURNAL.md` are excluded from these modifications. **All work will be performed on a dedicated feature branch as per project mandates.**

**Tech Stack:** Bash, Grep, Python (for script-based header insertion).

---

### Task 0: Preparation

- [ ] **Step 1: Create a feature branch**
Run: `git checkout -b feature/identity-and-evergreen-pass`

---

### Task 1: Identity PASS - Root Level Scripts and Configs

**Files:**
- Modify: `automate.sh`
- Modify: `package.json`
- Modify: `pytest.ini`
- Modify: `requirements.txt`
- Modify: `serve.py`
- Modify: `vitest.config.js`
- Modify: `firebase-config.js`
- Modify: `firebase.json`
- Modify: `firestore.rules`

- [ ] **Step 1: Add header to `automate.sh`**
```bash
# ABOUTME: Orchestrates the end-to-end puzzle generation and deployment workflow.
# ABOUTME: Provides a single entry point for daily automation tasks.
```

- [ ] **Step 2: Add header to `package.json`**
```json
{
  "_comment": "ABOUTME: Defines Node.js dependencies and scripts for frontend testing and linting.",
  "_comment": "ABOUTME: Configures the Vitest test runner for JSDOM-based environment."
}
```

- [ ] **Step 3: Add header to `pytest.ini`**
```ini
# ABOUTME: Configuration file for Pytest, defining test paths and environment settings.
# ABOUTME: Ensures consistent test execution across the Python automation suite.
```

- [ ] **Step 4: Add header to `requirements.txt`**
```text
# ABOUTME: Lists Python dependencies required for the page generator and automation tools.
# ABOUTME: Used for environment setup and CI/CD dependency installation.
```

- [ ] **Step 5: Add header to `serve.py`**
```python
# ABOUTME: Local development server with support for extensionless URLs.
# ABOUTME: Handles routing for static assets and HTML files without .html suffixes.
```

- [ ] **Step 6: Add header to `vitest.config.js`**
```javascript
// ABOUTME: Configuration for Vitest frontend testing framework.
// ABOUTME: Sets up JSDOM and test coverage reporting for JavaScript modules.
```

- [ ] **Step 7: Add header to `firebase.json`**
```json
{
  "_comment": "ABOUTME: Firebase hosting and configuration settings for deployment.",
  "_comment": "ABOUTME: Defines rewrite rules and hosting directory structure."
}
```

- [ ] **Step 8: Commit Identity PASS Phase 1**
```bash
git add automate.sh package.json pytest.ini requirements.txt serve.py vitest.config.js firebase.json
git commit -m "docs: add ABOUTME headers to root scripts and configs"
```

---

### Task 2: Identity PASS - JavaScript Modules

**Files:**
- Modify: `all_players.js`
- Modify: `js/analytics.js`
- Modify: `js/analyticsData.js`
- Modify: `js/detail.js`
- Modify: `js/galleryFilter.js`
- Modify: `js/quiz.js`
- Modify: `js/quizEngine.js`
- Modify: `js/scoreDisplay.js`
- Modify: `js/index.js`

- [ ] **Step 1: Add header to `all_players.js`**
```javascript
// ABOUTME: Central data repository for New York Yankees player statistics and hints.
// ABOUTME: Serves as the primary source of truth for the puzzle engine and search.
```

- [ ] **Step 2: Add header to `js/analytics.js`**
```javascript
// ABOUTME: Manages the logic for the site-wide analytics and performance dashboard.
// ABOUTME: Handles data visualization and summary statistics for trivia puzzles.
```

- [ ] **Step 3: Add header to `js/quiz.js`**
```javascript
// ABOUTME: Entry point for the interactive quiz interface logic.
// ABOUTME: Orchestrates UI updates, user input handling, and game state management.
```

- [ ] **Step 4: (Repeat for all other JS files in `js/` directory)**

- [ ] **Step 5: Commit Identity PASS Phase 2**
```bash
git add all_players.js js/*.js
git commit -m "docs: add ABOUTME headers to JavaScript modules"
```

---

### Task 3: Identity PASS - Python Automation Suite

**Files:**
- Modify: `page-generator/main.py`
- Modify: `page-generator/html_generator.py`
- Modify: `page-generator/seo_cleanup.py`
- Modify: `page-generator/scraper.py`
- (Other files in `page-generator/`)

- [ ] **Step 1: Add header to `page-generator/main.py`**
```python
# ABOUTME: CLI entry point for the Python-based puzzle automation pipeline.
# ABOUTME: Dispatches tasks for scraping, image processing, and HTML generation.
```

- [ ] **Step 2: Add header to `page-generator/html_generator.py`**
```python
# ABOUTME: Generates individual trivia puzzle HTML files from player data.
# ABOUTME: Applies SEO standards, canonical tags, and structured data templates.
```

- [ ] **Step 3: (Repeat for all other Python files in `page-generator/`)**

- [ ] **Step 4: Commit Identity PASS Phase 3**
```bash
git add page-generator/*.py
git commit -m "docs: add ABOUTME headers to automation suite"
```

---

### Task 4: Evergreen Pass - Comments and Symbols Audit

**Files:**
- Modify: `quiz.html`
- Modify: `AUTOMATION_SUMMARY.md`
- (Any other file with temporal developer-facing comments)

- [ ] **Step 1: Clean up internal comments in `quiz.html`**
Change `<!-- NEW: "I Give Up" button -->` to `<!-- Button to reveal answer and end current puzzle -->`.

- [ ] **Step 2: Clean up `AUTOMATION_SUMMARY.md` (Internal documentation)**
Replace temporal headers like "New Modules Created" or "Enhanced Files" with evergreen descriptions.
Change `### New Modules Created` to `### Core Automation Modules`.
Change `### Enhanced Files` to `### Modified System Files`.

- [ ] **Step 3: Commit Evergreen Pass Phase 1**
```bash
git add quiz.html AUTOMATION_SUMMARY.md
git commit -m "docs: remove temporal language from internal comments and documentation"
```

---

### Task 4.5: Identity PASS - Historical Puzzle Pages (Optional but thorough)
*Note: Since there are 160+ files, we will use a script to add headers to the historical .html files.*

**Files:**
- Modify: `YYYY-MM-DD.html` (batch)

- [ ] **Step 1: Run batch script to add headers to historical pages**
```bash
for f in [0-9]*.html; do
  if ! grep -q "ABOUTME:" "$f"; then
    sed -i '1i <!-- ABOUTME: Historical trivia puzzle page for a specific date. -->\n<!-- ABOUTME: Contains player stats clues and interactive reveal logic. -->' "$f"
  fi
done
```

- [ ] **Step 2: Commit Batch Update**
```bash
git add [0-9]*.html
git commit -m "docs: add ABOUTME headers to historical puzzle pages"
```

---

### Task 5: Final Verification

- [ ] **Step 1: Systematic Audit**
Run `grep` to ensure no remaining temporal markers in *comments* (e.g., `// NEW`, `/* fixed */`).

- [ ] **Step 2: Build and Test**
Run `./run_tests.sh` to ensure no breaking changes in scripts or configuration files.

- [ ] **Step 3: Final Commit**
```bash
git commit --allow-empty -m "chore: finalize identity and evergreen pass verification"
```
