# John Sterling Tribute Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a custom, automation-safe trivia page for John Sterling for 2026-05-04 with specialized layout and autocomplete logic.

**Architecture:** 
1.  **Data:** Update `stats_summary.json` and `index.html` with the Sterling entry.
2.  **Logic:** Inject "John Sterling" into the autocomplete pool in `quiz.js` for the specific date.
3.  **View:** Build a hand-coded `2026-05-04.html` with custom CSS for the tribute layout.
4.  **Safeguard:** Update `automation_config.json` to prevent overwriting.

**Tech Stack:** HTML/CSS, Vanilla JS, Python (for tests).

---

### Task 1: Automation Safeguard & Data Entry

**Files:**
- Modify: `automation_config.json`
- Modify: `stats_summary.json`
- Modify: `index.html`

- [ ] **Step 1: Update `automation_config.json` to exclude 2026-05-04**
    Add `"2026-05-04"` to an `excluded_dates` list (create if not exists) to ensure scripts don't touch it.

- [ ] **Step 2: Add John Sterling to `stats_summary.json`**
    Insert the entry at the appropriate chronological position.
    ```json
    {
        "date": "2026-05-04",
        "name": "John Sterling",
        "nickname": "The Voice of the Yankees",
        "teams": ["NYY", "ATL", "WAS", "NYK", "NYI"],
        "years": ["1970-2024"],
        "isSpecial": true
    }
    ```

- [ ] **Step 3: Manually add gallery entry to `index.html`**
    Find the gap between 2026-05-05 and 2026-05-03 and insert the `gallery-container`.
    ```html
    <div class="gallery-container" data-search-terms="may 04 2026 john sterling broadcaster voice of the yankees 1989 2024">
     <a class="gallery-item" href="2026-05-04?reveal=true">
      <img alt="John Sterling tribute trivia card" decoding="async" src="images/clue-2026-05-04.webp"/>
     </a>
     <div class="p-4">
      <p class="gallery-date">Trivia Date: May 04, 2026</p>
      <!-- Action links similar to other cards -->
     </div>
    </div>
    ```

- [ ] **Step 4: Commit**
    ```bash
    git add automation_config.json stats_summary.json index.html
    git commit -m "chore: add John Sterling data and protect date from automation"
    ```

### Task 2: TDD - Quiz Logic & Autocomplete

**Files:**
- Create: `tests/test_sterling_tribute.py`
- Modify: `js/quiz.js`

- [ ] **Step 1: Write failing test for autocomplete injection**
    Create a Python/Playwright or Vitest test that checks if "John Sterling" is in suggestions when on `quiz?date=2026-05-04`. (Since we use Vitest for frontend, we'll use that).

- [ ] **Step 2: Run test to verify it fails**
    Expected: FAIL ("John Sterling" not found in suggestions).

- [ ] **Step 3: Implement injection in `js/quiz.js`**
    ```javascript
    // inside loadQuizData
    if (date === '2026-05-04' && !allPlayers.includes('John Sterling')) {
        allPlayers.push('John Sterling');
    }
    ```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**
    ```bash
    git add js/quiz.js tests/test_sterling_tribute.py
    git commit -m "feat: inject John Sterling into autocomplete for tribute date"
    ```

### Task 3: Custom Tribute Page Implementation

**Files:**
- Create: `2026-05-04.html`
- Modify: `style.css` (if needed for shared tribute styles)

- [ ] **Step 1: Create `2026-05-04.html` with basic structure**
    Copy from `2026-05-05.html` but strip the chart and stats table.

- [ ] **Step 2: Implement custom `.tribute-layout` CSS**
    ```css
    .tribute-layout {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
    }
    .broadcast-stats {
        font-family: 'Courier New', Courier, monospace;
        background: #1a2b3c;
        color: white;
        padding: 1rem;
        border: 4px solid #f0f0f0;
    }
    ```

- [ ] **Step 3: Add Microphone iconography and timeline**
    Manually add the list of teams and years with a microphone emoji or SVG.

- [ ] **Step 4: Add `quiz-data` JSON block**
    ```html
    <div id="quiz-data" style="display:none;">
    {
        "answer": "John Sterling",
        "hints": [
            "Recipient of 16 Emmy Awards for broadcasting excellence.",
            "Called games for the Bullets, Knicks, Islanders, and Braves before arriving in the Bronx.",
            "Known for legendary personalized home run calls and 'The Yankees Win! Theeeeeee Yankees Win!'"
        ]
    }
    </div>
    ```

- [ ] **Step 5: Final verification and Commit**
    Check in browser (using `python3 serve.py`).
    ```bash
    git add 2026-05-04.html style.css
    git commit -m "feat: implement custom tribute page for John Sterling"
    ```
