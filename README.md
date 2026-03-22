# Name That Yankee

"Name That Yankee" is a web-based trivia game where users test their knowledge of New York Yankees players based on career statistics and highlights. The project features a public-facing website with historical puzzles and a playable quiz interface, supported by an automated pipeline for generating new trivia content.

## Project Overview

*   **Purpose:** A daily trivia game for New York Yankees fans, providing an archive of historical puzzles and a playable quiz interface.
*   **Architecture:**
    *   **Frontend:** A static website built with HTML, CSS, and Vanilla JavaScript.
    *   **Data Layer:** Player data and archives are managed through JS files (`all_players.js`) and individual HTML pages for each trivia date.
    *   **Automation (Page Generator):** A Python-based toolset that automates the creation of new puzzle pages, including scraping stats, processing images, and generating HTML.
*   **Deployment:** Hostable as a static site (e.g., GitHub Pages).

## Technology Stack

*   **Frontend:** HTML5, CSS3, JavaScript (ES Modules).
*   **Automation (Python):** Python 3.x, Selenium, Pillow (image processing), Pydantic, Beautiful Soup 4.
*   **Testing:** 
    *   **Frontend:** Vitest (with jsdom).
    *   **Automation:** Pytest.
*   **CI/CD:** GitHub Actions.

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

## Prerequisites

*   **Node.js 20+** (for frontend tests)
*   **Python 3.12+** (for automation and E2E tests)
*   **Firebase CLI** (for security rule testing)

## Getting Started

### Website
The website is static and can be served by any web server.
*   **Local Development:** You can use a simple server like `npx serve .` or Python's `python3 -m http.server`.

### Automation (Page Generator)
To use the puzzle generation tools:
1.  **Set up environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install -r test_requirements.txt
    ```
2.  **Install Playwright browsers:**
    ```bash
    playwright install --with-deps
    ```
3.  **Run automation:**
    ```bash
    # Standard workflow
    python page-generator/main.py --automate-workflow [screenshot_path]

    # Configure automation
    python page-generator/main.py --config
    ```
For more detailed information on the automation workflow, see [README_AUTOMATION.md](README_AUTOMATION.md) and [AUTOMATION_SUMMARY.md](AUTOMATION_SUMMARY.md).

## Testing

This project uses a multi-layered testing strategy. The primary entry point for running all tests is:

```bash
./run_tests.sh
```

### Test Layers
1.  **Frontend & Security Tests (Vitest):** Logic for scoring, UI, and Firestore security rules. Run with `npm test`.
2.  **E2E & Accessibility Tests (Playwright):** Site structure, search/filter, and WCAG compliance. Run with `pytest test_yankee_site.py`.
3.  **Automation Unit Tests (Pytest):** Logic for scraping, image processing, and HTML generation. Run with `pytest tests/unit/`.
4.  **Integration Tests:** End-to-end workflow of page generation tools. Run with `pytest test_automation.py`.

See [TEST_README.md](TEST_README.md) for more details.

## Development Conventions

*   **HTML Generation:** New puzzles are generated as individual HTML files named `YYYY-MM-DD.html`. These are automatically linked in `index.html` by the page generator.
*   **Images:** Puzzle clues should be in WEBP format and named `clue-YYYY-MM-DD.webp`. Player images follow a similar naming convention or are referenced in `all_players.js`.
*   **State Management:** The frontend uses `localStorage` to track scores and solved puzzles (see `index.html` and `quiz.html` scripts).

## License

This project is licensed under the ISC License.
