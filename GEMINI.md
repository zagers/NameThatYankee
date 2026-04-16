# Name That Yankee - Project Context

"Name That Yankee" is a web-based trivia game where users test their knowledge of New York Yankees players based on career statistics and highlights. The project includes a public-facing website and an automated pipeline for generating new trivia puzzles.

## Project Overview

*   **Purpose:** A daily trivia game for New York Yankees fans, providing an archive of historical puzzles and a playable quiz interface.
*   **Architecture:**
    *   **Frontend:** A static website built with HTML, CSS, and Vanilla JavaScript.
    *   **Data Layer:** Player data and archives are managed through JS files (`all_players.js`) and individual HTML pages for each trivia date.
    *   **Automation (Page Generator):** A Python-based toolset that automates the creation of new puzzle pages, including scraping stats, processing images, and generating HTML.
*   **Deployment:** Hostable as a static site (e.g., GitHub Pages). `sitemap.xml` is automatically generated during the GitHub Actions deployment process.

## Technology Stack

*   **Frontend:** HTML5, CSS3, JavaScript (ES Modules).
*   **Automation (Python):** Python 3.x, Selenium (web scraping/search), Pillow (image processing), Pydantic (config validation), Beautiful Soup 4 (HTML parsing).
*   **Testing:** 
    *   **Frontend:** Vitest (with jsdom).
    *   **Automation:** Pytest.
*   **CI/CD:** GitHub Actions (configured in `.github/workflows/`).

## Key Files & Directories

*   `index.html`: The main archives page and entry point for the site.
*   `quiz.html`: The interactive quiz interface.
*   `all_players.js`: Central data file containing player information and historical records.
*   `style.css`: Primary stylesheet for the entire application.
*   `page-generator/`: Root directory for the Python automation suite.
    *   `main.py`: Entry point for the automation CLI.
    *   `automation/`: Modules for image processing, player search, and git integration.
    *   `html_generator.py`: Logic for generating new trivia page HTML.
*   `images/`: Contains puzzle clues (webp) and player images.
*   `automation_config.json`: Persistent settings for the automation pipeline.

## Building and Running

### Website
The website is static and can be served by any web server or opened directly in a browser.
*   **Local Development:** You can use a simple server like `npx serve .` or Python's `python3 -m http.server`.

### Automation (Page Generator)
To use the puzzle generation tools:
1.  **Set up environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
2.  **Run automation:**
    ```bash
    # Standard workflow
    python page-generator/main.py --automate-workflow [screenshot_path]

    # Configure automation
    python page-generator/main.py --config
    ```

### Testing
*   **Run all tests:** `./run_tests.sh`
*   **Frontend only:** `npm test`
*   **Automation only:** `pytest`

## Development Conventions

*   **Primary Branch:** The primary development branch is named `master`. Always ensure you are on `master` before creating new feature branches or performing synchronization.
*   **HTML Generation:** New puzzles are generated as individual HTML files named `YYYY-MM-DD.html`. These are automatically linked in `index.html` by the page generator.
*   **Images:** Puzzle clues should be in WEBP format and named `clue-YYYY-MM-DD.webp`. Player images follow a similar naming convention or are referenced in `all_players.js`.
*   **Testing:** All new automation features must be accompanied by tests in `test_automation.py` or the `tests/` directory. Frontend logic should be tested using Vitest.
*   **Security & Dependency Updates:** All security and dependency updates (including Dependabot fixes) MUST be performed on dedicated branches to allow for Pull Request review. Do not commit these changes directly to `master`. If a Dependabot branch already exists for the update, use that branch. Always verify changes with the full test suite (`./run_tests.sh`) before pushing to the branch.
*   **PR Workflow:** ALL changes made by Gemini CLI (including documentation and code) MUST be performed on dedicated branches. The agent MUST NOT merge its own changes into `master`; the user will perform all Pull Request reviews and merges.
*   **State Management:** The frontend uses `localStorage` to track scores and solved puzzles (see `index.html` and `quiz.html` scripts).

## TODO

### Performance Optimization
*   **Lazy Loading:** Implement lazy loading for the archive gallery in `index.html` to improve initial load times as the puzzle collection grows.

### SEO Improvements (Google Indexing) - COMPLETED 2026-04-15
*   **Clean URLs:** Updated all `rel="canonical"` tags across 160+ historical `.html` files to point to clean URLs.
*   **Internal Links:** Normalized all site-wide navigation (gallery, header, analytics) to use extensionless URLs.
*   **Unique Meta Descriptions:** Standardized all historical pages with unique, player-specific meta descriptions.
*   **Automation Update:** Modified `page-generator/html_generator.py` to automate these standards for all future puzzles.

## Journal

### 2026-04-15: SEO Finalization & Link Normalization
*   **Batch Metadata Cleanup:** Implemented `page-generator/seo_cleanup.py` (BeautifulSoup-based) and standardized 164 historical trivia pages. Every page now has a unique meta description and a clean canonical URL.
*   **Automation Synchronization:** Updated the permanent `html_generator.py` pipeline to ensure new puzzles automatically follow SEO best practices.
*   **Site-wide Link Normalization:** Audited and updated `index.html`, `quiz.html`, `instructions.html`, `analytics.html`, and all JavaScript-driven links to remove `.html` extensions from internal navigation.
*   **Infrastructure:** Updated `.gitignore` to exclude session-specific metadata and committed design documentation to the `docs/` directory for architectural transparency.
*   **Verification:** Confirmed 100% pass rate across the full 288-test suite (Unit, Automation, E2E, and JS).
