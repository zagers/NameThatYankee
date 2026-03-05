# E2E Test Enhancement Plan

This document outlines a detailed, phased approach for enhancing the current End-to-End (E2E) test suite (`test_yankee_site.py`) for the Name That Yankee application. The goal is to make the tests more robust, independent of live data, and to increase coverage across edge cases, visual regressions, and accessibility/security.

## Phase 1: Test Data Independence & Mocking

Currently, the E2E tests rely on a live local server serving actual generated daily HTML files (e.g., `2025-07-11.html`). This makes tests brittle, as they depend on the presence and specific content of these dates.

**Objectives:**
1.  **Create Static Test Fixtures:** Generate a set of static HTML files specifically for testing. These files will have known, unchanging data (e.g., `test-player-1.html`) to ensure tests remain stable over time.
2.  **Configure Test Environment Server:** Update the test setup to serve from a dedicated `tests/fixtures/www/` directory rather than the project root when running the E2E suite, or use a Python mock server that intercepts and serves these static files.
3.  **Mock External APIs (Network Interception):** Since the frontend is static HTML/JS, any external calls (like to Firebase/Firestore if used for analytics storage, or image loading delays) should be intercepted and mocked at the browser level if necessary.

**Action Items:**
*   [x] Create `tests/fixtures/www/` directory.
*   [x] Create `tests/fixtures/www/index.html` with a controlled subset of gallery items.
*   [x] Create `tests/fixtures/www/quiz.html` and a sample date page (e.g., `tests/fixtures/www/2000-01-01.html`) with hardcoded "correct" answers for testing logic.
*   [x] Update `conftest.py` to start the HTTP server pointed at the `tests/fixtures/www/` directory instead of the project root.
*   [x] Update `test_yankee_site.py` to use `http://localhost:8000/2000-01-01.html` instead of `2025-07-11.html`.

## Phase 2: Analytics Edge Cases

The current analytics tests assume a perfect sunny-day scenario. We need to test how the UI handles missing or corrupted data.

**Objectives:**
1.  **Empty Data State:** Test how the analytics page renders when `localStorage` is completely empty. It should display a friendly "No data available" message instead of failing to render charts.
2.  **Corrupted Data State:** Inject malformed JSON into `localStorage` (e.g., `{'nameThatYankeeTotalScore': 'not-a-number'}`) and ensure the page handles it gracefully (e.g., by resetting the data or showing an error, rather than throwing a JS exception that breaks the page).
3.  **High Volume Data State:** Test with a large number of simulated completed puzzles to ensure the charts scale well and UI elements don't overlap.

**Action Items:**
*   [x] Add `test_analytics_empty_data` to `TestAnalyticsPage` which clears `localStorage` then loads the page.
*   [x] Add `test_analytics_corrupted_data` which injects invalid strings into the expected `localStorage` keys.
*   [x] Add `test_analytics_large_dataset` which programmaticlly populates `localStorage` with 100+ simulated game results before loading the page.

## Phase 3: Accessibility (a11y) Automation

The current accessibility test only checks for `alt` tags and a single `h1`. We can automate comprehensive accessibility scanning.

**Objectives:**
1.  **Integrate Axe-Core:** Use the `axe-selenium-python` package to inject the Axe ruleset into the browser and scan for WCAG violations on key pages.

**Action Items:**
*   [x] Add `axe-selenium-python` to `test_requirements.txt`.
*   [x] Update `TestUtilities.test_accessibility_basic` (or create a new class `TestAccessibility`) to run `axe.run()` on `index.html`, `quiz.html`, and `analytics.html`.
*   [x] Configure Axe to fail the test only on critical/serious violations, while reporting minor ones.

## Phase 4: Visual Regression Testing

Ensure that CSS changes do not accidently break the layout across different browsers or screen sizes.

**Objectives:**
1.  **Visual Comparisons:** Since the project already uses Playwright/Puppeteer-like tools (Selenium), we can implement visual regression testing using a library like `pytest-splinter` or a dedicated service like Percy. Given we want to keep it simple, we can start by migrating to Playwright (which has built-in visual comparisons) or using a dedicated Python visual testing package.
*(Note: Migrating to Playwright is generally recommended for modern E2E over Selenium due to better auto-waiting and features like visual comparisons.)*

**Action Items (Option B: Playwright Migration):**
*   [ ] **1. Dependency Setup:** Remove `selenium`, `webdriver-manager`, and `axe-selenium-python` from `test_requirements.txt`. Add `pytest-playwright` and `axe-playwright-python`.
*   [ ] **2. Fixture Migration (`conftest.py` & setup):** Refactor the `browser` fixture. Playwright provides built-in `page` fixtures, so we'll need to adapt our custom HTTP server fixture to work alongside Playwright's ecosystem.
*   [ ] **3. Syntax Migration (The Heavy Lift):** Convert all 30+ tests in `test_yankee_site.py` from Selenium's `browser.find_element(By.ID)` layout to Playwright's `page.locator()` syntax. Remove unnecessary `WebDriverWait` calls since Playwright auto-waits.
*   [ ] **4. Accessibility Port:** Update the `TestUtilities.test_accessibility_basic` logic to use the new `axe-playwright-python` injection method.
*   [ ] **5. Visual Regressions (The Goal):** Implement new tests using `expect(page).to_have_screenshot()` on the static fixtures (e.g., asserting the layout of the Header or Quiz structure) to capture baseline images and protect against CSS regressions.

## Phase 5: Security Scanner Integration (CI)

The current `TestSecurity` suite is great for application-level logic, but broader security checks can be automated.

**Objectives:**
1.  **OWASP ZAP:** Integrate a lightweight dynamic application security testing (DAST) scanner into the GitHub Actions pipeline.

**Action Items:**
*   [ ] Add a step in `.github/workflows/deploy.yml` (perhaps as a separate job or a scheduled nightly run, as DAST scans can be slow) to run the `zaproxy/action-baseline` Docker image against the local server spun up during the test phase.

---

## Suggested Next Step

The highest impact / lowest effort task right now is **Phase 1: Test Data Independence & Mocking**. Building static test fixtures will immediately eliminate the flaky tests that rely on `2025-07-11.html`. 

Would you like to start creating the `tests/fixtures/www/` directory and migrating a few tests to use it?
