# Design Spec: Analytics Optimization & Data Pre-generation
# Date: 2026-04-19

## Status
Proposed (Approved by Scott)

## Context
The current analytics dashboard (`analytics.html`) is inefficient. To gather player statistics (teams, years) for its charts, it fetches `index.html`, parses all puzzle links, and then performs a separate network request and DOM parse for every single historical puzzle page (~165+). This results in high latency, excessive bandwidth usage, and a poor user experience.

## Objectives
1.  **Performance:** Reduce network requests for static player data from ~166 to 1.
2.  **Responsiveness:** Achieve near-instant loading of the analytics dashboard.
3.  **Future-proofing:** Enable faster site-wide search by including player names in the pre-generated data.

## Proposed Changes

### 1. Data Layer: `stats_summary.json`
A new JSON file will be generated in the project root. It will serve as the single source of truth for historical puzzle metadata.

**Schema:**
```json
[
  {
    "date": "YYYY-MM-DD",
    "name": "Player Name",
    "teams": ["ABC", "XYZ"],
    "years": ["YYYY", "YYYY"]
  }
]
```

### 2. Automation: `page-generator/html_generator.py`
The `rebuild_index_page` function will be updated to generate `stats_summary.json` whenever the index is rebuilt.
- **Logic:** During the existing iteration over `all_clue_files`, the script will parse each puzzle's `.html` file.
- **Extraction:** It will extract the `name` (from `<h2>` or metadata) and the `search-data` JSON object (already present in the HTML).
- **Output:** It will write the consolidated list to `stats_summary.json`.

### 3. Frontend: `js/analytics.js`
The `initAnalytics` function will be refactored.
- **Old Logic:** Fetch `index.html` -> Loop through links -> Fetch each page -> Parse `search-data`.
- **New Logic:** Fetch `stats_summary.json` once.
- **Compatibility:** The data structure passed to the chart generation functions (`processTeamData`, `processDecadeData`) will remain identical to avoid breaking changes in the processing logic.

### 4. Verification & TDD Strategy
We will follow Test-Driven Development for both the Python and JavaScript changes.

**Python (Automation):**
1.  **Failing Test:** Create a test in `test_automation.py` that verifies `rebuild_index_page` creates a valid `stats_summary.json` with expected data.
2.  **Implementation:** Update `html_generator.py` to make the test pass.
3.  **Verification:** Run `pytest`.

**JavaScript (Frontend):**
1.  **Failing Test:** Create a Vitest unit test for `initAnalytics` (or a mock-based integration test) that expects a single fetch to `stats_summary.json`.
2.  **Implementation:** Refactor `js/analytics.js` to use the new JSON source.
3.  **Verification:** Run `npm test`.

## Success Criteria
- `stats_summary.json` is automatically updated whenever a new puzzle is added.
- `analytics.html` loads successfully with zero 404s or console errors.
- Network panel shows only 1 request for player data instead of 160+.
- All 288+ regression tests pass.
