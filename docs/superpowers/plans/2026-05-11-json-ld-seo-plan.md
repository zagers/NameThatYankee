# JSON-LD Schema SEO Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve SEO by transitioning to indexable, static quiz pages with rich JSON-LD `VideoGame` and `Person` schemas.

**Architecture:** We will update the Python-based `html_generator.py` to produce both an answer page and a static quiz page for every puzzle. The quiz page will contain a `VideoGame` schema, and the answer page will have an enriched `Person` schema. The frontend `quiz.js` will be updated to handle these new static URLs while maintaining backwards compatibility.

**Tech Stack:** Python (BeautifulSoup, json), JavaScript (ES Modules, Vanilla JS), Pytest, Playwright (Vitest/Pytest).

---

### Task 1: TDD - Update Automation Tests

**Files:**
- Modify: `test_automation.py`

- [ ] **Step 1: Write failing tests for dual-file generation and schema presence**

Add tests to `test_automation.py` that check if `generate_detail_page` (or a new equivalent) now creates both `YYYY-MM-DD.html` and `YYYY-MM-DD-quiz.html`, and that they contain the expected `<script type="application/ld+json">` blocks.

```python
def test_generates_quiz_and_answer_pages(tmp_path):
    from page_generator.html_generator import generate_detail_page
    player_data = {
        "name": "Derek Jeter",
        "nickname": "The Captain",
        "facts": ["Fact 1"],
        "career_totals": {"HR": "260"}
    }
    date_str = "2025-05-11"
    generate_detail_page(player_data, date_str, "May 11, 2025", tmp_path)
    
    assert (tmp_path / "2025-05-11.html").exists()
    assert (tmp_path / "2025-05-11-quiz.html").exists()

def test_quiz_page_has_game_schema(tmp_path):
    # Check for @type: VideoGame in 2025-05-11-quiz.html
    pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest test_automation.py`
Expected: FAIL (No such file or directory for `-quiz.html`)

- [ ] **Step 3: Commit**

```bash
git add test_automation.py
git commit -m "test: add failing tests for dual-file generation"
```

---

### Task 2: Implement Schema Generation in Python

**Files:**
- Modify: `page-generator/html_generator.py`

- [ ] **Step 1: Update `build_detail_page_html` with enriched Person Schema**

Update the JSON-LD template in `build_detail_page_html` to include `mainEntity: Person` with `description` and `award`.

```python
    person_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"Name That Yankee Answer for {formatted_date}",
        "mainEntity": {
            "@type": "Person",
            "name": name,
            "alternateName": nickname,
            "jobTitle": "Professional Baseball Player",
            "memberOf": {
                "@type": "SportsOrganization",
                "name": "New York Yankees"
            },
            "description": f"New York Yankees player {name} ({nickname}). Career stats include {career_totals_data}."
        }
    }
```

- [ ] **Step 2: Implement `build_quiz_page_html`**

Create a function that returns the HTML for the static quiz page, including the `VideoGame` schema and removing `noindex`.

- [ ] **Step 3: Update `generate_detail_page` to call both**

Ensure both files are written to disk.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest test_automation.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add page-generator/html_generator.py
git commit -m "feat: implement static quiz page generation and enriched person schema"
```

---

### Task 3: Update Gallery Links and Index Generation

**Files:**
- Modify: `page-generator/html_generator.py`

- [ ] **Step 1: Update `generate_gallery_snippet` to link to static quiz**

Change the `href` for the Quiz button.

```python
# Old
<a href="quiz?date={date_str}" class="action-link quiz-link" rel="nofollow">
# New
<a href="{date_str}-quiz" class="action-link quiz-link">
```

- [ ] **Step 2: Run `rebuild_index_page` locally and verify output**

Run a command to rebuild `index.html` and check the links.

- [ ] **Step 3: Commit**

```bash
git add page-generator/html_generator.py
git commit -m "feat: update gallery links to point to static quiz pages"
```

---

### Task 4: Update Frontend `quiz.js` for Static URL Support

**Files:**
- Modify: `js/quiz.js`

- [ ] **Step 1: Update `initQuiz` to infer date from filename**

If `params.get('date')` is missing, try to parse it from `window.location.pathname`.

```javascript
    let date = params.get('date');
    if (!date) {
        const pathMatch = window.location.pathname.match(/(\d{4}-\d{2}-\d{2})-quiz/);
        if (pathMatch) date = pathMatch[1];
    }
```

- [ ] **Step 2: Verify quiz still loads on a sample page**

- [ ] **Step 3: Commit**

```bash
git add js/quiz.js
git commit -m "feat: add support for inferring date from static quiz URL"
```

---

### Task 5: Migration - Generate Existing Quiz Pages

**Files:**
- Create: `migrate_quizzes.py`

- [ ] **Step 1: Write migration script**

A script that uses `html_generator.py` logic to generate `-quiz.html` files for all existing answer pages.

- [ ] **Step 2: Run migration**

Run: `python3 migrate_quizzes.py`

- [ ] **Step 3: Verify a few files exist and look correct**

- [ ] **Step 4: Commit**

```bash
git add *-quiz.html migrate_quizzes.py
git commit -m "chore: generate static quiz pages for all existing puzzles"
```

---

### Task 6: Update Regression and SEO Tests

**Files:**
- Modify: `test_yankee_site.py`
- Modify: `test_seo_dynamic.py`

- [ ] **Step 1: Update `test_yankee_site.py`**

Remove the `noindex` check for the new quiz URLs. Update the redirect expectation (answer -> quiz).

- [ ] **Step 2: Update `test_seo_dynamic.py`**

Verify the canonical tags on the new static quiz pages.

- [ ] **Step 3: Run all tests**

Run: `./run_tests.sh`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "test: update regression and SEO tests for static quiz pages"
```
