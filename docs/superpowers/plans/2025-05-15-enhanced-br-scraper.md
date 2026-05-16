# Enhanced Baseball-Reference Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance the Baseball-Reference scraper to extract player transactions and awards/honors.

**Architecture:** Use BeautifulSoup to find specific `div` elements by ID. For transactions, parse commented-out HTML if necessary. For awards, extract text from the `extra_stats` div.

**Tech Stack:** Python, Selenium, BeautifulSoup4, Pytest.

---

### Task 1: Write Failing Test

**Files:**
- Create: `tests/test_br_scraper_enhanced.py`

- [ ] **Step 1: Write the failing test**

```python
# ABOUTME: Tests for enhanced Baseball-Reference scraping capabilities.
# ABOUTME: Verifies extraction of transactions and awards for players.
import pytest
from page_generator.scraper import search_and_scrape_player

def test_scrape_player_enhanced_data():
    # Tippy Martinez is a good candidate with both transactions and awards
    player_name = "Tippy Martinez"
    result = search_and_scrape_player(player_name, automated=True)
    
    assert result is not None
    assert "transactions" in result
    assert isinstance(result["transactions"], list)
    assert len(result["transactions"]) > 0
    
    assert "awards" in result
    assert isinstance(result["awards"], list)
    assert len(result["awards"]) > 0
    
    # Specific check for Tippy Martinez awards (e.g., "1983 World Series")
    has_ws = any("World Series" in award for award in result["awards"])
    assert has_ws, f"Expected World Series in awards, got {result['awards']}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_br_scraper_enhanced.py`
Expected: FAIL with `KeyError: 'transactions'` or similar if `search_and_scrape_player` doesn't return these keys.

---

### Task 2: Implement Extraction Logic

**Files:**
- Modify: `page-generator/scraper.py`

- [ ] **Step 1: Implement `parse_transactions` and `parse_awards`**

Add these helper functions to `page-generator/scraper.py`:

```python
def parse_transactions(soup):
    """Parses the transactions section, handling comments if necessary."""
    transactions = []
    trans_div = soup.find('div', id='all_transactions')
    
    if not trans_div:
        # Check in comments
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if 'id="all_transactions"' in comment:
                trans_soup = BeautifulSoup(comment, 'html.parser')
                trans_div = trans_soup.find('div', id='all_transactions')
                break
                
    if trans_div:
        # Typically transitions are in a list or paragraphs
        for p in trans_div.find_all('p'):
            text = p.get_text(strip=True)
            if text:
                transactions.append(text)
                
    return transactions

def parse_awards(soup):
    """Parses the awards/honors from the extra_stats div."""
    awards = []
    awards_div = soup.find('div', id='extra_stats')
    if awards_div:
        for li in awards_div.find_all('li'):
            text = li.get_text(strip=True)
            if text:
                awards.append(text)
    return awards
```

- [ ] **Step 2: Update `search_and_scrape_player` to use new parsers**

Update the return dict in `search_and_scrape_player`:

```python
        # ... inside search_and_scrape_player ...
        career_totals = parse_career_totals(soup)
        yearly_war = parse_yearly_war(soup)
        transactions = parse_transactions(soup)
        awards = parse_awards(soup)

        if career_totals and yearly_war:
            print("  ✅ All stats scraped successfully.")
            return {
                "career_totals": career_totals, 
                "yearly_war": yearly_war,
                "transactions": transactions,
                "awards": awards
            }
```

- [ ] **Step 3: Run test to verify it passes**

Run: `pytest tests/test_br_scraper_enhanced.py`
Expected: PASS

- [ ] **Step 4: Commit changes**

```bash
git add page-generator/scraper.py tests/test_br_scraper_enhanced.py
git commit -m "feat: enhance BR scraper with transactions and awards"
```
