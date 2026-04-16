# SEO Cleanup Utility Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the SEO cleanup utility regex for multiline title tags, correct the test import path, and execute the cleanup on all historical pages.

**Architecture:** 
1. Update `page-generator/seo_cleanup.py` to handle multiline `<title>` tags using `re.DOTALL`.
2. Update `tests/test_seo_cleanup.py` to correctly import from the hyphenated `page-generator` directory.
3. Use a virtual environment to run `pytest`.
4. Run the cleanup script first in dry-run mode, then in live mode.

**Tech Stack:** Python 3, pytest, re

---

### Task 1: Fix Regex in `seo_cleanup.py`

**Files:**
- Modify: `page-generator/seo_cleanup.py`

- [ ] **Step 1: Update `extract_metadata` regex**

```python
def extract_metadata(html_content):
    # Regex to find <title> tag content: [Player Name] Answer - [Date] | Name That Yankee
    # Added re.DOTALL to handle multiline <title> tags
    match = re.search(r'<title>\s*(.*?)\s*Answer - \s*(.*?)\s*\| Name That Yankee\s*</title>', html_content, re.DOTALL)
    if match:
        player_name = match.group(1).strip()
        date = match.group(2).strip()
        # Handle cases where there might be newlines inside the captured groups
        player_name = " ".join(player_name.split())
        date = " ".join(date.split())
        return player_name, date
    return None, None
```

- [ ] **Step 2: Commit script fix**

```bash
git add page-generator/seo_cleanup.py
git commit -m "fix(seo): update title extraction regex to handle multiline tags"
```

### Task 2: Fix Imports in `tests/test_seo_cleanup.py`

**Files:**
- Modify: `tests/test_seo_cleanup.py`

- [ ] **Step 1: Update import in `tests/test_seo_cleanup.py`**

```python
import pytest
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Add page-generator to sys.path to allow importing from it directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'page-generator')))

from seo_cleanup import extract_metadata, scrub_and_inject, normalize_links
```

- [ ] **Step 2: Run the test to verify it passes**

Run: `/Users/zagers/Documents/code/NameThatYankee/venv_new/bin/python3 -m pytest tests/test_seo_cleanup.py`
Expected: PASS

- [ ] **Step 3: Commit test fix**

```bash
git add tests/test_seo_cleanup.py
git commit -m "test(seo): fix import path for seo_cleanup utility"
```

### Task 3: Execute SEO Cleanup

- [ ] **Step 1: Run dry-run**

Run: `/Users/zagers/Documents/code/NameThatYankee/venv_new/bin/python3 page-generator/seo_cleanup.py --dry-run`
Expected: Output showing files that would be updated.

- [ ] **Step 2: Run live cleanup**

Run: `/Users/zagers/Documents/code/NameThatYankee/venv_new/bin/python3 page-generator/seo_cleanup.py --no-dry-run`
Expected: Output showing files updated.

- [ ] **Step 3: Commit updated HTML files**

```bash
git add *.html
git commit -m "chore(seo): apply batch metadata cleanup to all historical pages"
```
