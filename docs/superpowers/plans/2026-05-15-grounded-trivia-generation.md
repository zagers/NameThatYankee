# Grounded Trivia Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a high-accuracy trivia generation pipeline that uses scraped data from Baseball-Reference and SABR.org to eliminate hallucinations and identity swaps.

**Architecture:** A four-stage pipeline: (1) Deep Data Harvesting from BR/SABR, (2) Grounded AI Generation using a "Dossier" prompt, (3) AI Claim Extraction, and (4) Python-based Cross-Verification against the raw scraped data.

**Tech Stack:** Python 3, Selenium (headless), BeautifulSoup4, Google GenAI (Gemini 3.1 Flash Lite).

---

### Task 1: SABR Biography Scraper

**Files:**
- Modify: `page-generator/scraper.py`
- Test: `tests/test_sabr_scraper.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from page-generator.scraper import get_sabr_bio

def test_get_sabr_bio_success():
    # Tippy Martinez has a known bio
    bio = get_sabr_bio("Tippy Martinez")
    assert "pickoff" in bio.lower()
    assert "Baltimore Orioles" in bio
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sabr_scraper.py -v`
Expected: FAIL (ImportError or AttributeError)

- [ ] **Step 3: Implement `get_sabr_bio` in `scraper.py`**

```python
def get_sabr_bio(player_name):
    import requests
    from bs4 import BeautifulSoup
    import urllib.parse
    
    # Simple search or direct link guess
    search_query = urllib.parse.quote_plus(player_name)
    search_url = f"https://sabr.org/?s={search_query}&post_type=bioproj"
    
    response = requests.get(search_url, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find first result
    link = soup.select_one('.search-result-title a')
    if not link: return ""
    
    bio_url = link['href']
    bio_response = requests.get(bio_url, timeout=10)
    bio_soup = BeautifulSoup(bio_response.text, 'html.parser')
    
    content = bio_soup.select_one('.entry-content')
    return content.get_text(separator=' ', strip=True) if content else ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_sabr_scraper.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add page-generator/scraper.py
git commit -m "feat: add SABR biography scraper"
```

---

### Task 2: Enhanced Baseball-Reference Scraper (Transactions & Awards)

**Files:**
- Modify: `page-generator/scraper.py`
- Test: `tests/test_br_scraper_enhanced.py`

- [ ] **Step 1: Write the failing test**

```python
def test_scrape_player_enhanced():
    from page-generator.scraper import search_and_scrape_player
    data = search_and_scrape_player("Tippy Martinez", automated=True)
    assert "transactions" in data
    assert "awards" in data
    assert any("Baltimore Orioles" in t for t in data["transactions"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_br_scraper_enhanced.py -v`
Expected: FAIL (KeyError: 'transactions')

- [ ] **Step 3: Update `search_and_scrape_player` and helpers**

```python
def parse_transactions(soup):
    trans_div = soup.find('div', id='all_transactions')
    if not trans_div: return []
    return [li.get_text(strip=True) for li in trans_div.find_all('li')]

def parse_awards(soup):
    awards_div = soup.find('div', id='extra_stats')
    if not awards_div: return []
    return [a.get_text(strip=True) for a in awards_div.find_all('a')]

# Update search_and_scrape_player to include these
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_br_scraper_enhanced.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add page-generator/scraper.py
git commit -m "feat: enhance BR scraper with transactions and awards"
```

---

### Task 3: Grounded AI Generation Service

**Files:**
- Create: `page-generator/grounded_ai.py`
- Test: `tests/test_grounded_ai.py`

- [ ] **Step 1: Write the failing test**

```python
def test_generate_grounded_facts():
    from page-generator.grounded_ai import generate_grounded_trivia
    dossier = {
        "name": "Tippy Martinez",
        "stats": "...",
        "bio": "...",
        "transactions": ["Traded to BAL in 1976"]
    }
    result = generate_grounded_trivia(dossier)
    assert "facts" in result
    assert "claims" in result
    assert len(result["facts"]) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_grounded_ai.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement `generate_grounded_trivia`**

Prompt AI as a Copy Editor, requiring a JSON with `facts`, `qa`, and `claims`. Claims should be a list of dicts: `{"subject": "...", "predicate": "...", "object": "..."}`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_grounded_ai.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add page-generator/grounded_ai.py
git commit -m "feat: implement grounded AI trivia generation service"
```

---

### Task 4: Python Verification Engine (The Hard Gate)

**Files:**
- Create: `page-generator/fact_verifier.py`
- Test: `tests/test_fact_verifier.py`

- [ ] **Step 1: Write the failing test**

```python
def test_verify_claim_mismatch():
    from page-generator.fact_verifier import verify_claims
    raw_data = {"years": ["1974", "1975"]}
    claims = [{"type": "year", "value": "1980"}]
    assert verify_claims(claims, raw_data) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fact_verifier.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `verify_claims`**

Loop through claims (years, teams, stats) and check for existence in `raw_data`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_fact_verifier.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add page-generator/fact_verifier.py
git commit -m "feat: implement Python fact verification engine"
```

---

### Task 5: Pipeline Integration

**Files:**
- Modify: `page-generator/main.py`

- [ ] **Step 1: Update the main automation loop**

Replace the old `get_facts_and_followup_from_gemini` call with the new grounded pipeline: Dossier -> AI Gen -> Verify -> Retry if failed.

- [ ] **Step 2: Manual End-to-End Test**

Run: `python page-generator/main.py --automate-workflow path/to/clue.webp`
Verify that facts are generated and verified.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: integrate grounded pipeline into main automation"
```
