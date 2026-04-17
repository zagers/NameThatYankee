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

## Building and Running

### Development Environment Setup
To set up a new environment (e.g., a new laptop) for full development and testing:

1.  **System Dependencies:**
    *   **Java 21+:** Required for the Firebase/Firestore emulator.
    *   **Python 3.11+ & venv:** Required for the automation pipeline and backend tests.
    *   **Node.js 20+:** Required for frontend tests and development server.

2.  **Initialize Environment:**
    ```bash
    # 1. Create and activate Python virtual environment
    python3 -m venv .venv
    source .venv/bin/activate

    # 2. Install Python dependencies
    pip install -r requirements.txt -r test_requirements.txt

    # 3. Install Node.js dependencies
    npm install

    # 4. Install Playwright browsers (for UI tests)
    playwright install chromium --with-deps
    ```

### Troubleshooting New Environments
*   **Java 21 Errors:** If `npm test` fails with a Java version error, ensure you have Java 21 installed. If you have a local JDK (e.g., the Microsoft build for ARM64), run: `export JAVA_HOME=/path/to/jdk && export PATH=$JAVA_HOME/bin:$PATH` before running tests.
*   **python3-venv missing:** On some Linux systems, you may need to run `sudo apt install python3-venv` if the bootstrap script fails to create the `.venv`.
*   **Playwright Dependencies:** If UI tests fail to launch the browser, run `npx playwright install-deps` to ensure all system-level libraries are present.

### Website
The website is static and can be served by any web server or opened directly in a browser.
*   **Local Development:** You can use a simple server like `npx serve .` or Python's `python3 -m http.server`.

### Automation (Page Generator)
To use the puzzle generation tools:
1.  **Activate environment:**
    ```bash
    source .venv/bin/activate
    ```
2.  **Run automation:**
    ```bash
    # Standard workflow
    python page-generator/main.py --automate-workflow [screenshot_path]

    # Configure automation
    python page-generator/main.py --config
    ```

For more detailed information on the automation workflow, see [README_AUTOMATION.md](README_AUTOMATION.md) and [AUTOMATION_SUMMARY.md](AUTOMATION_SUMMARY.md).

## Testing

Always ensure your environment is fully set up before running tests. The primary entry point for running all tests is:

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

Name That Yankee Quiz © 2025 by Scott Zager is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
