# George Steinbrenner Tribute Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a playable 4th of July tribute trivia page for legendary Yankees owner George Steinbrenner, including custom UI layout, custom autocomplete rules, sitemap/index rebuild, and testing safeguards.

**Architecture:** Process screenshot/answer images, configure autocomplete logic in JS specifically for 2026-07-04, build the custom HTML page, configure automation skip lists, rebuild index files, and run local testing.

**Tech Stack:** HTML, Vanilla CSS, JS (ES Modules), Playwright E2E testing, Python (Pillow).

## Global Constraints

- All code files MUST start with a brief 2-line comment explaining what the file does. Each line MUST start with "ABOUTME: " to make them easily greppable.
- No comments referencing temporal context like "new", "improved", "legacy".
- Follow TDD for code logic changes.

---

### Task 1: Process Puzzle and Answer Images

**Files:**
- Create: `scratch/process_images.py`
- Create: `images/clue-2026-07-04.webp`
- Create: `images/answer-2026-07-04.webp`

- [ ] **Step 1: Write scratch image processing script**
  Create a temporary Python script at `scratch/process_images.py` to download the Steinbrenner image from Wikimedia Commons and process both the screenshot and the downloaded photo into optimized WEBP format.
  
  ```python
  # ABOUTME: One-off utility to process 4th of July tribute images.
  # ABOUTME: Converts screenshot and answer photos to optimized WEBP format.
  import urllib.request
  from pathlib import Path
  from PIL import Image

  def process():
      # 1. Process screenshot clue
      screenshot_path = Path("/Users/zagers/Downloads/Screenshot 2026-07-04 at 4.40.19 PM.png")
      clue_out = Path("images/clue-2026-07-04.webp")
      with Image.open(screenshot_path) as img:
          # Convert to RGB and save as optimized webp
          img.convert("RGB").save(clue_out, "WEBP", quality=85)
          print("Saved clue-2026-07-04.webp")

      # 2. Download and process answer photo
      answer_url = "https://upload.wikimedia.org/wikipedia/commons/1/1d/George_Steinbrenner_1985.jpg"
      temp_jpg = Path("temp_steinbrenner.jpg")
      answer_out = Path("images/answer-2026-07-04.webp")
      
      print("Downloading George Steinbrenner image...")
      urllib.request.urlretrieve(answer_url, temp_jpg)
      
      with Image.open(temp_jpg) as img:
          # Convert to RGB and save as optimized webp
          img.convert("RGB").save(answer_out, "WEBP", quality=85)
          print("Saved answer-2026-07-04.webp")
          
      if temp_jpg.exists():
          temp_jpg.unlink()

  if __name__ == "__main__":
      process()
  ```

- [ ] **Step 2: Run image processing script**
  Run the script to generate the images.
  Run: `.venv/bin/python scratch/process_images.py`
  Expected: Command outputs "Saved clue-2026-07-04.webp" and "Saved answer-2026-07-04.webp".

- [ ] **Step 3: Verify output images exist**
  Verify the new images exist in the `images/` directory:
  - `images/clue-2026-07-04.webp`
  - `images/answer-2026-07-04.webp`

- [ ] **Step 4: Commit images**
  ```bash
  git add images/clue-2026-07-04.webp images/answer-2026-07-04.webp
  git commit -m "chore: add 4th of july tribute clue and answer images"
  ```

---

### Task 2: Autocomplete & Quiz Logic (TDD)

**Files:**
- Create: `tests/test_steinbrenner_tribute.py`
- Modify: `js/quiz.js`

- [ ] **Step 1: Write failing autocomplete test**
  Create `tests/test_steinbrenner_tribute.py`:
  
  ```python
  # ABOUTME: Playwright E2E tests for the George Steinbrenner tribute date.
  # ABOUTME: Verifies autocomplete Suggestions specifically on 2026-07-04.
  import pytest
  from playwright.sync_api import Page, expect
  from tests.test_config import QUIZ_URL

  def test_steinbrenner_autocomplete_on_tribute_date(page: Page):
      """Verify that George Steinbrenner appears in autocomplete for the tribute date 2026-07-04."""
      page.goto(f"{QUIZ_URL}?date=2026-07-04")
      guess_input = page.locator("#guess-input")
      expect(guess_input).to_be_visible()
      guess_input.fill("George")
      suggestions = page.locator("#suggestions-container")
      expect(suggestions).to_be_visible()
      suggestion_items = suggestions.locator(".suggestion-item")
      expect(suggestion_items).to_contain_text(["George Steinbrenner"])

  def test_the_boss_autocomplete_on_tribute_date(page: Page):
      """Verify that The Boss appears in autocomplete for the tribute date 2026-07-04."""
      page.goto(f"{QUIZ_URL}?date=2026-07-04")
      guess_input = page.locator("#guess-input")
      expect(guess_input).to_be_visible()
      guess_input.fill("The B")
      suggestions = page.locator("#suggestions-container")
      expect(suggestions).to_be_visible()
      suggestion_items = suggestions.locator(".suggestion-item")
      expect(suggestion_items).to_contain_text(["The Boss"])

  def test_steinbrenner_not_in_autocomplete_on_other_date(page: Page):
      """Verify that George Steinbrenner does NOT appear in autocomplete for other dates."""
      page.goto(f"{QUIZ_URL}?date=2026-07-03")
      guess_input = page.locator("#guess-input")
      expect(guess_input).to_be_visible()
      guess_input.fill("George")
      page.wait_for_timeout(500)
      suggestions = page.locator("#suggestions-container")
      if suggestions.is_visible():
          suggestion_items = suggestions.locator(".suggestion-item").all_inner_texts()
          assert "George Steinbrenner" not in suggestion_items
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `.venv/bin/pytest tests/test_steinbrenner_tribute.py -v`
  Expected: FAIL (because George Steinbrenner / The Boss are not in the autocomplete list for 2026-07-04).

- [ ] **Step 3: Modify autocomplete suggestions logic in `js/quiz.js`**
  Add the special check to [js/quiz.js:209-212](file:///Users/zagers/Documents/code/NameThatYankee/js/quiz.js#L209-L212):
  
  ```javascript
      // John Sterling Tribute Injection
      if (date === '2026-05-04') {
          allPlayers = ['John Sterling', ...allPlayers.filter(p => p !== 'John Sterling')];
      } else if (date === '2026-07-04') {
          allPlayers = ['George Steinbrenner', 'The Boss', ...allPlayers.filter(p => !['George Steinbrenner', 'The Boss'].includes(p))];
      }
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `.venv/bin/pytest tests/test_steinbrenner_tribute.py -v`
  Expected: PASS

- [ ] **Step 5: Commit changes**
  ```bash
  git add tests/test_steinbrenner_tribute.py js/quiz.js
  git commit -m "feat: add George Steinbrenner autocomplete logic and tests"
  ```

---

### Task 3: Build Custom Detail Page

**Files:**
- Create: `2026-07-04.html`

- [ ] **Step 1: Write the custom detail page HTML file**
  Create `2026-07-04.html`. Model it after John Sterling's `2026-05-04.html` layout, using `.tribute-layout` and custom timeline elements.
  
  ```html
  <!-- ABOUTME: Special tribute page for George Steinbrenner, "The Boss". -->
  <!-- ABOUTME: Features ownership highlights, timeline, and custom stats layout. -->
  <!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>George Steinbrenner &quot;The Boss&quot; Answer - July 04, 2026 | Name That Yankee</title>
      <link rel="stylesheet" href="style.css">
      <link rel="manifest" href="manifest.json">
      <link rel="shortcut icon" type="image/png" href="images/favicon.png">
      <link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
      <link rel="canonical" href="https://namethatyankeequiz.com/2026-07-04">
      
      <!-- Meta tags for better social sharing -->
      <meta name="description" content="Discover the career highlights and sports ownership milestone history for George 'The Boss' Steinbrenner, the featured trivia topic for the July 04, 2026 puzzle.">
      <meta property="og:title" content="Name That Yankee - July 04, 2026">
      <meta property="og:description" content="Check out this Name That Yankee puzzle! Can you identify this historic Yankees figure?">
      <meta property="og:type" content="website">
      <meta property="og:site_name" content="Name That Yankee">
      <meta property="og:image" content="https://namethatyankeequiz.com/images/social-card.webp">
      
      <meta name="twitter:card" content="summary_large_image">
      <meta name="twitter:title" content="Name That Yankee - July 04, 2026">
      <meta name="twitter:description" content="Check out this Name That Yankee puzzle! Can you identify this historic Yankees figure?">
      <meta name="twitter:image" content="https://namethatyankeequiz.com/images/social-card.webp">
      
      <meta name="apple-mobile-web-app-title" content="NameThatYankee">
  
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Name That Yankee Answer for July 04, 2026",
        "description": "Discover the career highlights and sports ownership milestone history for George 'The Boss' Steinbrenner, the featured trivia topic for the July 04, 2026 puzzle.",
        "image": "https://namethatyankeequiz.com/images/social-card.webp",
        "author": {
          "@type": "Person",
          "name": "Scott Zager"
        },
        "publisher": {
          "@type": "Organization",
          "name": "Name That Yankee",
          "logo": {
            "@type": "ImageObject",
            "url": "https://namethatyankeequiz.com/apple-touch-icon.png"
          }
        },
        "datePublished": "2026-07-04"
      }
      </script>
  </head>
  <body>
      <header>
          <div class="header-content">
              <h1>The answer for July 04, 2026 is...</h1>
          </div>
          <div class="header-controls">
              <a href="instructions" class="instructions-link">New Features!</a>
              <div id="score-display">
                  Your Score: <span id="total-score">0</span>
                  <svg aria-hidden="true" class="chevron-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                  <div id="score-breakdown-container" style="display: none;">
                      <div class="breakdown-header">Score Breakdown</div>
                      <table>
                          <thead>
                              <tr>
                                  <th>Clue</th>
                                  <th>Points</th>
                                  <th>Count</th>
                              </tr>
                          </thead>
                          <tbody id="breakdown-body"></tbody>
                      </table>
                  </div>
              </div>
          </div>
      </header>
  
      <main>
          <a href="./" class="back-link">← Back to All Questions</a>
  
          <div class="tribute-layout">
              <div class="player-photo">
                  <img src="images/answer-2026-07-04.webp" alt="Photo of George Steinbrenner" decoding="async">
              </div>
              <div class="player-info">
                  <h2>George Steinbrenner</h2>
                  <div class="facts-header">
                      <h3>Career Highlights & Facts</h3>
                      <p class="disclaimer">(The Boss)</p>
                  </div>
                  <ul>
                      <li>Born on the Fourth of July, this legendary figure bought the Yankees in 1973 for $10 million and restored the franchise to glory, winning 7 World Series titles.</li>
                      <li>Known as "The Boss," he was famous for his hands-on management style, fiery personality, and frequently hiring and firing manager Billy Martin.</li>
                      <li>Beyond baseball, he was a vice president of the United States Olympic Committee and owned interests in teams across basketball (Bulls, Pipers) and hockey (Devils).</li>
                  </ul>
  
                  <div class="broadcast-stats">
                      <div class="stat-box">
                          <span class="count">7</span>
                          <span class="label">WS Titles</span>
                      </div>
                      <div class="stat-box">
                          <span class="count">11</span>
                          <span class="label">A.L. Pennants</span>
                      </div>
                      <div class="stat-box">
                          <span class="count">.566</span>
                          <span class="label">Win Percentage</span>
                      </div>
                  </div>
  
                  <div class="timeline-container">
                      <h3>Sports Ownership & Organizational Timeline</h3>
                      <div class="timeline-item">
                          <span class="mic-icon">🏀</span>
                          <span>1960-1962: Cleveland Pipers (ABL)</span>
                      </div>
                      <div class="timeline-item">
                          <span class="mic-icon">🏀</span>
                          <span>1972-1985: Chicago Bulls (Partner)</span>
                      </div>
                      <div class="timeline-item">
                          <span class="mic-icon">⚾</span>
                          <span>1973-2010: New York Yankees (Principal Owner)</span>
                      </div>
                      <div class="timeline-item">
                          <span class="mic-icon">🏅</span>
                          <span>1985-2002: US Olympic Committee (VP)</span>
                      </div>
                      <div class="timeline-item">
                          <span class="mic-icon">🏀</span>
                          <span>1999-2004: New Jersey Nets (YankeeNets Partner)</span>
                      </div>
                      <div class="timeline-item">
                          <span class="mic-icon">🏒</span>
                          <span>2000-2004: New Jersey Devils (YankeeNets Partner)</span>
                      </div>
                  </div>
  
                  <div class="followup-section" id="followup-section">
                      <h3>Would you like to find out more about George Steinbrenner?</h3>
                      <div class="followup-buttons">
                          <div class="followup-item">
                              <button class="followup-btn" data-answer="He led a syndicate that purchased the team from CBS in 1973 for $10 million, stating he would be a hands-off owner (which quickly proved to be the opposite).">Why did Steinbrenner buy the Yankees?</button>
                              <div class="followup-answer" style="display:none;"></div>
                          </div>
                          <div class="followup-item">
                              <button class="followup-btn" data-answer="He hired and fired Billy Martin as manager five separate times between 1975 and 1988, a relationship that became a legendary pop-culture phenomenon.">How many times did he hire and fire Billy Martin?</button>
                              <div class="followup-answer" style="display:none;"></div>
                          </div>
                          <div class="followup-item">
                              <button class="followup-btn" data-answer="Created in 1999, YankeeNets was a joint business venture that merged the business operations of the Yankees, the NBA's New Jersey Nets, and later the NHL's New Jersey Devils, before dissolving in 2004.">What was YankeeNets?</button>
                              <div class="followup-answer" style="display:none;"></div>
                          </div>
                      </div>
                  </div>
              </div>
          </div>
          <div id="search-data" style="display:none;">{"teams": ["NYY", "CLE", "CHI", "Nets", "Devils"], "years": ["1973", "1977", "1978", "1996", "1998", "1999", "2000", "2009"]}</div>
          <div id="quiz-data" style="display:none;">{"answer": "George Steinbrenner", "nicknames": ["The Boss", "Steinbrenner"], "hints": ["Born on the Fourth of July, this legendary figure bought the Yankees in 1973 for $10 million and restored the franchise to glory, winning 7 World Series titles.", "Known as \"The Boss,\" he was famous for his hands-on management style, fiery personality, and frequently hiring and firing manager Billy Martin.", "Beyond baseball, he was a vice president of the United States Olympic Committee and owned interests in teams across basketball (Bulls, Pipers) and hockey (Devils)."]}</div>
      </main>
      <script type="module" src="js/detail.js"></script>
      <footer>
          <p class="disclaimer-footer">
              This site is an unofficial fan project and is not affiliated with the New York Yankees, Major League Baseball, or the YES Network. All trademarks and copyrights belong to their respective owners.
          </p>
      </footer>    
  </body>
  </html>
  ```

- [ ] **Step 2: Commit new HTML page**
  ```bash
  git add 2026-07-04.html
  git commit -m "feat: add George Steinbrenner tribute answer page HTML"
  ```

---

### Task 4: Automation Exclusions & Index Rebuild

**Files:**
- Modify: `automation_config.json`
- Modify: `stats_summary.json`
- Modify: `index.html`

- [ ] **Step 1: Update `automation_config.json`**
  Modify [automation_config.json](file:///Users/zagers/Documents/code/NameThatYankee/automation_config.json#L26) to include `2026-07-04` in the `workflow.excluded_dates` array.
  
  ```json
      "excluded_dates": ["2026-05-04", "2026-07-04"]
  ```

- [ ] **Step 2: Rebuild index page and stats summary**
  Run: `.venv/bin/python page-generator/main.py --rebuild-index`
  Expected: Outputs successfully, rebuilding `index.html` and generating the new JSON entry in `stats_summary.json` automatically based on our custom HTML metadata.

- [ ] **Step 3: Verify stats_summary.json contains George Steinbrenner**
  Check that `stats_summary.json` now includes the `2026-07-04` entry for `George Steinbrenner`.

- [ ] **Step 4: Verify index.html contains the new puzzle card**
  Check that `index.html` includes a card for `2026-07-04`.

- [ ] **Step 5: Run full local test suite**
  Run: `./run_tests.sh`
  Expected: All E2E, Unit, JS, and Playwright tests pass (100% green).

- [ ] **Step 6: Commit and clean up**
  Remove temporary `scratch/process_images.py` and commit changes.
  
  ```bash
  rm scratch/process_images.py
  git add automation_config.json stats_summary.json index.html
  git commit -m "chore: exclude date from automation and rebuild index"
  ```
