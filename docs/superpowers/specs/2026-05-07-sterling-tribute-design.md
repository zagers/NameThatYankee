# Design Doc: 2026-05-04 John Sterling Tribute Quiz

## 1. Purpose
Create a custom, non-standard trivia page for legendary Yankees announcer John Sterling for May 4, 2026. This page bypasses the standard player-centric automation because Sterling does not have traditional baseball stats (WAR, hits, etc.).

## 2. Success Criteria
*   The quiz is playable and accepts "John Sterling" as the correct answer.
*   "John Sterling" appears in the autocomplete list ONLY on the 2026-05-04 quiz page.
*   The answer page (2026-05-04.html) uses a custom layout mirroring the "Broadcaster" stats (Emmys, World Series) and microphone iconography.
*   The page is "safe" from automation regressions; it won't be overwritten or broken by future bulk updates.
*   The gallery search correctly finds "John Sterling".

## 3. Architecture & Implementation

### A. Quiz Logic (`js/quiz.js`)
*   Modify `loadQuizData` to detect `date === '2026-05-04'`.
*   If detected, push "John Sterling" into the `allPlayers` array used for autocomplete.
*   Ensure the `QuizEngine` is initialized with "John Sterling" and relevant broadcast-themed hints.

### B. Custom Answer Page (`2026-05-04.html`)
*   **HTML Structure:** 
    *   No `careerArcChart` canvas.
    *   Replace `player-profile` and `stats-table-container` with a custom `.tribute-layout`.
    *   Implement a "Broadcast Resume" section with microphone icons for his various teams (Bullets, Knicks, Islanders, Braves, Yankees).
*   **Styling:**
    *   Add scoped CSS within the file or specific classes in `style.css` to handle the grid layout for Emmys/World Series counts.

### C. Data Integration (`stats_summary.json`)
*   Manually add the John Sterling entry.
*   Include search terms like "Broadcaster", "Announcer", "Voice of the Yankees".

### D. Safeguards (Regression Testing)
*   **Automation Protection:** Update `automation_config.json` (or similar) to ensure the generator skips this date.
*   **Verification:** Add a test case in `tests/test_sterling_tribute.py` (following TDD) that:
    1.  Verifies the page exists and has the custom HTML structure.
    2.  Verifies "John Sterling" is the correct answer.
    3.  Verifies autocomplete works on this specific date.

## 4. Visual Layout (Answer Page)
```text
[ Photo of John Sterling ]
[ TITLE: John Sterling - The Voice of the Yankees ]
[ STATS BLOCK: 16 EMMYS | 5 WORLD SERIES ]
[ TIMELINE: 
  (Mic) 1970-71 Bullets
  (Mic) 1973-74 Knicks
  ...
  (Mic) 1989-2024 Yankees
]
```

## 5. Implementation Phases
1.  **Branching:** Create `feature/sterling-tribute`.
2.  **TDD (Test First):** Write tests for the Sterling page behavior.
3.  **Data:** Update `stats_summary.json`.
4.  **Logic:** Update `js/quiz.js` for autocomplete injection.
5.  **View:** Hand-code `2026-05-04.html`.
6.  **Verification:** Run `./run_tests.sh`.
