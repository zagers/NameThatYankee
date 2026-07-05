# Design Doc: 2026-07-04 George Steinbrenner Tribute Quiz

## 1. Purpose
Create a custom, non-standard trivia page for legendary Yankees owner George Steinbrenner for July 4, 2026 (his birthday). This page bypasses player-centric automation because Steinbrenner is not an MLB player and lacks traditional playing statistics (WAR, hits, etc.).

## 2. Success Criteria
*   The quiz is playable and accepts "George Steinbrenner" or "The Boss" as correct answers.
*   "George Steinbrenner" and "The Boss" appear in autocomplete suggestions ONLY on the 2026-07-04 quiz page.
*   The answer page (2026-07-04.html) uses a custom layout displaying owner stats (7 WS titles, 11 AL pennants, .566 win percentage) and sports ownership timeline iconography.
*   The page is excluded from automation updates so future automated runs won't overwrite it.
*   The gallery search correctly finds "George Steinbrenner".

## 3. Architecture & Implementation

### A. Quiz Logic (`js/quiz.js`)
*   Modify `loadQuizData` / autocomplete suggestions to check for `date === '2026-07-04'`.
*   If detected, inject "George Steinbrenner" and "The Boss" into the `allPlayers` list used for autocomplete.

### B. Custom Answer Page (`2026-07-04.html`)
*   **HTML Structure:**
    *   No `careerArcChart` canvas.
    *   Replace `player-profile` and `stats-table-container` with a custom `.tribute-layout`.
    *   Implement an "Ownership Timeline" section highlighting his roles:
        *   `1960-1962`: Cleveland Pipers (ABL)
        *   `1972-1985`: Chicago Bulls (Partner)
        *   `1973-2010`: New York Yankees (Principal Owner)
        *   `1985-2002`: US Olympic Committee (VP)
        *   `1999-2004`: New Jersey Nets (YankeeNets Partner)
        *   `2000-2004`: New Jersey Devils (YankeeNets Partner)

### C. Data Integration (`stats_summary.json`)
*   Add the George Steinbrenner entry to `stats_summary.json` via the index rebuilder:
    ```json
    {
        "date": "2026-07-04",
        "name": "George Steinbrenner",
        "nickname": "The Boss",
        "teams": ["NYY", "CLE", "CHI", "Nets", "Devils"],
        "years": ["1973", "1977", "1978", "1996", "1998", "1999", "2000", "2009"]
    }
    ```

### D. Safeguards (Regression Testing)
*   **Automation Protection:** Update `automation_config.json`'s `excluded_dates` configuration to include `2026-07-04`.
*   **Verification:** Add a test case in `tests/test_steinbrenner_tribute.py` (following TDD) that:
    1.  Verifies the page exists and has the custom HTML structure.
    2.  Verifies "George Steinbrenner" and "The Boss" are accepted as correct answers.
    3.  Verifies autocomplete works on this specific date.
