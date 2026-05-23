# SEO Relevancy Bulk Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the search relevancy of 117 historical player pages by enriching them with unique, long-form content using the Wikipedia scraper and grounded AI pipeline.

**Architecture:** We will enhance the existing `main.py --regenerate-facts` logic to prioritize pages that are "thin" (lack biography text) and ensure that the regeneration process correctly populates the `<meta name="description">` and JSON-LD structured data.

**Tech Stack:** Python 3.x, Selenium, Google Gemini 3.1 Flash Lite, Beautiful Soup 4.

---

### Task 1: Enhance `enrich_player_bio` with Logging and Force Option

**Files:**
- Modify: `page-generator/main.py`
- Test: `tests/unit/page_generator/test_bio_enrichment.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Add page-generator to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "page-generator"))
import main

def test_enrich_player_bio_skips_if_already_long():
    with patch('scraper.get_wikipedia_summary') as mock_wiki:
        existing_bio = "A" * 600
        result = main.enrich_player_bio("Derek Jeter", existing_bio)
        assert result == existing_bio
        mock_wiki.assert_not_called()

def test_enrich_player_bio_fetches_if_short():
    with patch('scraper.get_wikipedia_summary') as mock_wiki:
        mock_wiki.return_value = "Long Wikipedia Summary Content..."
        existing_bio = "Short bio"
        result = main.enrich_player_bio("Derek Jeter", existing_bio)
        assert "Wikipedia Summary:" in result
        mock_wiki.assert_called_once_with("Derek Jeter")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/page_generator/test_bio_enrichment.py -v`
Expected: FAIL (File doesn't exist or logic needs update)

- [ ] **Step 3: Write minimal implementation**

(Already implemented, but ensure it matches the test expectations and add a `force` parameter if we want to override in the future).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/page_generator/test_bio_enrichment.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/page_generator/test_bio_enrichment.py page-generator/main.py
git commit -m "feat: add bio enrichment unit tests and verify current behavior"
```

---

### Task 2: Automated Meta Description and JSON-LD Verification

**Files:**
- Modify: `page-generator/html_generator.py`
- Test: `tests/unit/page_generator/test_seo_generation.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from pathlib import Path
import sys
from bs4 import BeautifulSoup

# Add page-generator to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "page-generator"))
import html_generator

def test_generate_detail_page_includes_meta_description():
    player_data = {
        'name': 'Don Mattingly',
        'nickname': 'The Donnie Baseball',
        'facts': ['Fact 1', 'Fact 2', 'Fact 3'],
        'career_totals': {'G': 1785},
        'yearly_war': [],
        'followup_qa': []
    }
    # Mocking files/dirs
    project_dir = Path("./temp_test_seo")
    project_dir.mkdir(exist_ok=True)
    
    html_generator.generate_detail_page(player_data, "1985-09-01", "September 01, 1985", project_dir)
    
    html_path = project_dir / "1985-09-01.html"
    with open(html_path, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        assert meta_desc is not None
        assert "Don Mattingly" in meta_desc['content']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/page_generator/test_seo_generation.py -v`
Expected: FAIL (If meta description is missing or incorrect)

- [ ] **Step 3: Implement missing SEO attributes**

Ensure `generate_detail_page` in `html_generator.py` builds a unique meta description.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/page_generator/test_seo_generation.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/page_generator/test_seo_generation.py page-generator/html_generator.py
git commit -m "fix: ensure detail pages generate unique meta descriptions for SEO"
```

---

### Task 3: Bulk Regeneration Execution (Trial Run)

**Files:**
- Execute: `page-generator/main.py`

- [ ] **Step 1: Run regeneration for a small range**

Run: `python page-generator/main.py --regenerate-facts`
Input: `2025-04-01 to 2025-04-05`

- [ ] **Step 2: Verify HTML output manually**

Check `2025-04-01.html` for:
1. Long biography text (from Wikipedia).
2. Unique meta description.
3. Grounded facts from the new pipeline.

- [ ] **Step 3: Commit the regenerated files**

```bash
git add 2025-04-*.html images/*.webp stats_summary.json index.html
git commit -m "chore: trial run of SEO content regeneration for April 2025"
```

---

### Task 4: Full Bulk Regeneration (The 117 Pages)

**Files:**
- Execute: `page-generator/main.py`

- [ ] **Step 1: Execute full range**

(This will take significant time and API quota. We will do it in batches of 20).

- [ ] **Step 2: Verify all tests pass after regeneration**

Run: `./run_tests.sh`

- [ ] **Step 3: Final Commit**

```bash
git add .
git commit -m "feat: complete bulk SEO relevancy upgrade for 100+ historical pages"
```
