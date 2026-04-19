# Analytics Optimization & Data Pre-generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pre-generate a `stats_summary.json` file during the puzzle automation process to eliminate the need for the browser to scrape 160+ HTML files when loading the analytics dashboard.

**Architecture:** 
1.  **Backend (Python):** Update the `rebuild_index_page` function in `html_generator.py` to extract player metadata (name, teams, years) from historical HTML files and save it to a consolidated `stats_summary.json`.
2.  **Frontend (JS):** Refactor `js/analytics.js` to fetch this single JSON file instead of crawling the entire site.

**Tech Stack:** Python 3.x, BeautifulSoup4, JavaScript (ES Modules), Vitest, Pytest.

---

### Task 1: Python - Test for `stats_summary.json` Generation

**Files:**
- Modify: `test_automation.py`

- [ ] **Step 1: Write a failing test for JSON generation**
Add a test case that checks if `rebuild_index_page` creates the expected `stats_summary.json`.

```python
def test_rebuild_index_generates_stats_summary(tmp_path):
    # Setup mock project structure
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    images_dir = project_dir / "images"
    images_dir.mkdir()
    
    # Create a dummy index.html
    (project_dir / "index.html").write_text('<div class="gallery"></div><footer id="last-updated"></footer>', encoding='utf-8')
    
    # Create a dummy clue and puzzle page
    date_str = "2026-04-18"
    (images_dir / f"clue-{date_str}.webp").write_text("fake image data")
    puzzle_html = f'''
    <html>
        <body>
            <h2>Fran Healy</h2>
            <div id="search-data">{{"teams": ["NYY", "KCR"], "years": ["1971", "1972"]}}</div>
        </body>
    </html>
    '''
    (project_dir / f"{date_str}.html").write_text(puzzle_html, encoding='utf-8')
    
    from page_generator import html_generator
    html_generator.rebuild_index_page(project_dir)
    
    stats_file = project_dir / "stats_summary.json"
    assert stats_file.exists()
    
    with open(stats_file, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]['date'] == date_str
    assert data[0]['name'] == "Fran Healy"
    assert "NYY" in data[0]['teams']
```

- [ ] **Step 2: Run the test to verify it fails**
Run: `pytest test_automation.py`
Expected: FAIL (AssertionError: stats_file.exists() is False)

- [ ] **Step 3: Commit the failing test**
```bash
git add test_automation.py
git commit -m "test: add failing test for stats_summary.json generation"
```

---

### Task 2: Python - Implement `stats_summary.json` Generation

**Files:**
- Modify: `page-generator/html_generator.py`

- [ ] **Step 1: Update `rebuild_index_page` to collect and save stats**
Modify the loop in `rebuild_index_page` to extract data and save to JSON.

```python
# In html_generator.py

def rebuild_index_page(project_dir: Path):
    # ... existing setup ...
    stats_summary = []
    
    for i, clue_file in enumerate(all_clue_files):
        # ... existing logic to get date_str ...
        
        # New logic to collect stats
        player_name = "Unknown"
        teams = []
        years = []
        
        if detail_page_path.exists():
            with open(detail_page_path, 'r', encoding='utf-8') as detail_f:
                detail_soup = BeautifulSoup(detail_f, 'html.parser')
            
            # Extract name from <h2>
            h2_el = detail_soup.find('h2')
            if h2_el:
                player_name = h2_el.get_text(strip=True)
            
            # Extract search data
            search_data_div = detail_soup.find('div', id='search-data')
            if search_data_div:
                search_data = json.loads(search_data_div.string or "{}")
                teams = search_data.get('teams', [])
                years = search_data.get('years', [])
        
        stats_summary.append({
            'date': date_str,
            'name': player_name,
            'teams': teams,
            'years': years
        })
        
        # ... existing gallery snippet generation ...

    # ... existing index.html write logic ...
    
    # Save the consolidated stats
    stats_path = project_dir / "stats_summary.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats_summary, f, indent=2)
    print(f"✅ stats_summary.json generated with {len(stats_summary)} entries.")
```

- [ ] **Step 2: Run the test to verify it passes**
Run: `pytest test_automation.py`
Expected: PASS

- [ ] **Step 3: Commit the implementation**
```bash
git add page-generator/html_generator.py
git commit -m "feat: implement stats_summary.json generation in rebuild_index_page"
```

---

### Task 3: JS - Test for `analytics.js` Refactor

**Files:**
- Modify: `tests/analytics.test.js` (or create if missing)

- [ ] **Step 1: Write a failing test for the new fetch logic**
Add a test that mocks `fetch` and checks if `initAnalytics` calls `stats_summary.json`.

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { initAnalytics } from '../js/analytics.js';

// Mock Global/External Dependencies
vi.stubGlobal('firebaseConfig', {});
vi.mock('https://www.gstatic.com/firebasejs/12.0.0/firebase-app.js', () => ({ initializeApp: vi.fn() }));
vi.mock('https://www.gstatic.com/firebasejs/12.0.0/firebase-app-check.js', () => ({ initializeAppCheck: vi.fn(), ReCaptchaV3Provider: vi.fn() }));
vi.mock('https://www.gstatic.com/firebasejs/12.0.0/firebase-firestore.js', () => ({ getFirestore: vi.fn(), collection: vi.fn(), getDocs: vi.fn(() => ({ docs: [] })) }));

describe('initAnalytics', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="loading-message"></div>
            <div id="analytics-content" class="hidden"></div>
            <canvas id="teamChart"></canvas>
            <canvas id="decadeChart"></canvas>
            <canvas id="guessesChart"></canvas>
            <canvas id="toughestPuzzlesChart"></canvas>
        `;
        vi.clearAllMocks();
    });

    it('should fetch stats_summary.json once', async () => {
        const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation((url) => {
            if (url === 'stats_summary.json') {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve([{ date: '2026-04-18', teams: ['NYY'], years: ['1971'] }])
                });
            }
            return Promise.resolve({ ok: true, text: () => Promise.resolve('') });
        });

        await initAnalytics();

        expect(fetchSpy).toHaveBeenCalledWith('stats_summary.json');
        // It should NOT fetch index.html anymore
        const calls = fetchSpy.mock.calls.map(c => c[0]);
        expect(calls).not.toContain('index.html');
    });
});
```

- [ ] **Step 2: Run the test to verify it fails**
Run: `npm test tests/analytics.test.js`
Expected: FAIL (It will still call `index.html`)

- [ ] **Step 3: Commit the failing test**
```bash
git add tests/analytics.test.js
git commit -m "test: add failing test for analytics.js refactor"
```

---

### Task 4: JS - Implement `analytics.js` Refactor

**Files:**
- Modify: `js/analytics.js`

- [ ] **Step 1: Refactor `initAnalytics` to use `stats_summary.json`**
Remove the `index.html` crawling logic and use the JSON file.

```javascript
// In js/analytics.js

export async function initAnalytics() {
    // ... existing firebase init ...

    try {
        console.log("Fetching pre-generated player stats...");
        const response = await fetch('stats_summary.json');
        if (!response.ok) throw new Error("Failed to load stats_summary.json");
        const allPlayerData = await response.json();
        console.log(`Loaded ${allPlayerData.length} players from summary.`);

        console.log("Fetching guess data...");
        // ... existing firebase guess fetch ...

        generateTeamChart(allPlayerData);
        generateDecadeChart(allPlayerData);
        // ... existing chart calls ...

        loadingMessage.style.display = 'none';
        analyticsContent.classList.remove('hidden');

    } catch (error) {
        // ... existing error handling ...
    }
}
```

- [ ] **Step 2: Run the test to verify it passes**
Run: `npm test tests/analytics.test.js`
Expected: PASS

- [ ] **Step 3: Commit the implementation**
```bash
git add js/analytics.js
git commit -m "feat: refactor analytics.js to use stats_summary.json"
```

---

### Task 5: Integration & Global Verification

- [ ] **Step 1: Run full automation to generate the real JSON**
Run: `python page-generator/main.py --all` (or just trigger index rebuild)
Wait... I need a safe way to run this. I'll just run a manual rebuild command.
Run: `python -c "from pathlib import Path; from page_generator.html_generator import rebuild_index_page; rebuild_index_page(Path('.'))"`
Expected: `stats_summary.json` created in root with ~165 entries.

- [ ] **Step 2: Run full regression suite**
Run: `./run_tests.sh`
Expected: 100% PASS (Zero failures).

- [ ] **Step 3: Final Commit**
```bash
git add stats_summary.json
git commit -m "chore: initial generation of stats_summary.json"
```
