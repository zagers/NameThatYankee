# Batch Quiz Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade all 189 historical trivia quizzes to the "Skeptical Storyteller" format using Gemini 3.1 Flash Lite Batch API.

**Architecture:** A three-phase pipeline (Prepare -> Batch -> Apply) with local state management for resume capability and a verification gate before updating HTML.

**Tech Stack:** Python 3.x, google-genai, BeautifulSoup, Selenium, Pytest.

---

## Task 1: Core Utilities and State Management

**Files:**
- Create: `page-generator/batch/utils.py`
- Create: `tests/unit/page_generator/batch/test_utils.py`

- [ ] **Step 1: Write the failing test for state management**
```python
def test_state_management():
    from page_generator.batch.utils import StateManager
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "progress.json"
        manager = StateManager(state_path)
        
        # Initial state should be empty
        assert manager.get_status("2025-04-01") is None
        
        # Set and save
        manager.set_status("2025-04-01", "scraped", {"player": "Don Mattingly"})
        manager.save()
        
        # Load in new instance
        new_manager = StateManager(state_path)
        assert new_manager.get_status("2025-04-01") == "scraped"
        assert new_manager.get_data("2025-04-01")["player"] == "Don Mattingly"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/unit/page_generator/batch/test_utils.py`

- [ ] **Step 3: Implement `StateManager` in `utils.py`**
```python
import json
from pathlib import Path

class StateManager:
    def __init__(self, path):
        self.path = Path(path)
        self.state = {}
        if self.path.exists():
            with open(self.path, 'r') as f:
                self.state = json.load(f)
                
    def get_status(self, date):
        entry = self.state.get(date, {})
        return entry.get("status")
        
    def get_data(self, date):
        return self.state.get(date, {}).get("data", {})
        
    def set_status(self, date, status, data=None):
        if date not in self.state:
            self.state[date] = {}
        self.state[date]["status"] = status
        if data:
            self.state[date]["data"] = data
            
    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.state, f, indent=2)
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

## Task 2: Preparation Phase (Scraper & Request Gen)

**Files:**
- Create: `page-generator/batch/prepare.py`
- Modify: `page-generator/batch/utils.py` (add prompt constant)

- [ ] **Step 1: Write failing test for `prepare.py`**
```python
def test_prepare_requests():
    from page_generator.batch.prepare import build_request
    dossier = {"name": "Test Player", "bio": "A long bio...", "career_totals": {}}
    request = build_request(dossier)
    assert "contents" in request
    assert "Test Player" in str(request)
```

- [ ] **Step 2: Implement `build_request` and the Batch Prompt**
Use the exact prompt from `grounded_ai.py`.

- [ ] **Step 3: Implement the main loop in `prepare.py`**
- Scan `*.html` in project root.
- Skip if `StateManager` says "scraped" or "submitted".
- Call `scraper.search_and_scrape_player` and `scraper.get_sabr_bio`.
- Save dossiers to `temp/dossiers/YYYY-MM-DD.json`.
- Output `requests.jsonl`.

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

## Task 3: Batch API Client

**Files:**
- Create: `page-generator/batch/client.py`

- [ ] **Step 1: Implement `client.py` using `google-genai`**
- `submit_batch(jsonl_path)`
- `get_status(job_id)`
- `download_results(job_id, output_path)`

- [ ] **Step 2: Write test with Mock Gemini API**

- [ ] **Step 3: Run tests**

- [ ] **Step 4: Commit**

---

## Task 4: Application Phase (The Patch)

**Files:**
- Create: `page-generator/batch/apply.py`

- [ ] **Step 1: Write failing test for HTML patching**
```python
def test_html_patch():
    from page_generator.batch.apply import patch_html
    old_html = "<html><body><div class='player-info'><ul><li>Old Fact</li></ul></div></body></html>"
    new_data = {
        "facts": ["New Hint 1", "New Hint 2", "New Hint 3"],
        "qa": [{"question": "Q?", "answer": "A."}]
    }
    updated = patch_html(old_html, new_data)
    assert "New Hint 1" in updated
    assert "followup-section" in updated
```

- [ ] **Step 2: Implement `patch_html` using BeautifulSoup**
- Replace `ul` inside `.player-info`.
- Inject `#followup-section` before `.stats-table-container`.
- Update `quiz-data` script.

- [ ] **Step 3: Implement `apply.py` main loop**
- Load `responses.jsonl`.
- For each response:
    - Load player dossier.
    - Run `fact_verifier.verify_claims`.
    - If pass: update HTML.
    - If fail: log to `FACT_AUDIT_REPORT.md`.

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

---

## Task 5: End-to-End Smoke Test

- [ ] **Step 1: Run `prepare.py` for 2-3 specific dates**
- [ ] **Step 2: Verify `requests.jsonl` format**
- [ ] **Step 3: Commit all remaining changes**
