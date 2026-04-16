# SEO Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a one-time cleanup script to standardize metadata and URLs in all historical trivia HTML files.

**Architecture:**
- `page-generator/seo_cleanup.py` as a CLI utility.
- Regex-based extraction of player name and date from `<title>`.
- Regex-based removal and injection of `<meta>` and `<link>` tags.
- Regex-based link normalization for internal `href` attributes.

**Tech Stack:** Python 3, `pytest`.

---

### Task 1: Create `page-generator/seo_cleanup.py` skeleton and extraction logic

**Files:**
- Create: `page-generator/seo_cleanup.py`

- [ ] **Step 1: Write `extract_metadata` function**

```python
import re

def extract_metadata(html_content):
    # Regex to find <title> tag content: [Player Name] Answer - [Date] | Name That Yankee
    match = re.search(r'<title>(.*?) Answer - (.*?) \| Name That Yankee</title>', html_content)
    if match:
        player_name = match.group(1).strip()
        date = match.group(2).strip()
        return player_name, date
    return None, None
```

- [ ] **Step 2: Commit initial skeleton**

```bash
git add page-generator/seo_cleanup.py
git commit -m "feat(seo): add extraction logic to seo_cleanup.py"
```

### Task 2: Implement scrubbing and injection logic

**Files:**
- Modify: `page-generator/seo_cleanup.py`

- [ ] **Step 1: Write `scrub_and_inject` function**

```python
def scrub_and_inject(html_content, player_name, date):
    # Remove existing description and canonical tags
    html_content = re.sub(r'\s*<meta name="description" content=".*?">', '', html_content)
    html_content = re.sub(r'\s*<link rel="canonical" href=".*?">', '', html_content)
    
    # Standardized tags
    canonical_tag = f'\n    <link rel="canonical" href="https://namethatyankeequiz.com/{date}">'
    description_tag = f'\n    <meta name="description" content="Discover the career highlights and statistics for {player_name}, the featured New York Yankee for the {date} trivia puzzle.">'
    
    # Inject after viewport tag
    viewport_pattern = r'(<meta name="viewport" content=".*?">)'
    if re.search(viewport_pattern, html_content):
        new_tags = viewport_pattern + canonical_tag + description_tag
        html_content = re.sub(viewport_pattern, r'\1' + canonical_tag + description_tag, html_content)
        
    return html_content
```

- [ ] **Step 2: Commit scrubbing logic**

```bash
git add page-generator/seo_cleanup.py
git commit -m "feat(seo): add scrubbing and injection logic to seo_cleanup.py"
```

### Task 3: Implement link normalization logic

**Files:**
- Modify: `page-generator/seo_cleanup.py`

- [ ] **Step 1: Write `normalize_links` function**

```python
def normalize_links(html_content):
    # Replace href="YYYY-MM-DD.html" with href="YYYY-MM-DD"
    # Matches href="2025-03-29.html" -> href="2025-03-29"
    pattern = r'href="(\d{4}-\d{2}-\d{2})\.html"'
    return re.sub(pattern, r'href="\1"', html_content)
```

- [ ] **Step 2: Commit link normalization**

```bash
git add page-generator/seo_cleanup.py
git commit -m "feat(seo): add link normalization logic to seo_cleanup.py"
```

### Task 4: Complete CLI utility

**Files:**
- Modify: `page-generator/seo_cleanup.py`

- [ ] **Step 1: Add CLI boilerplate**

```python
import os
import glob
import argparse

def process_file(file_path, dry_run=True):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    player_name, date = extract_metadata(content)
    if not player_name or not date:
        print(f"Skipping {file_path}: Metadata not found")
        return
    
    new_content = scrub_and_inject(content, player_name, date)
    new_content = normalize_links(new_content)
    
    if content != new_content:
        if dry_run:
            print(f"[DRY RUN] Would update {file_path}")
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {file_path}")

def main():
    parser = argparse.ArgumentParser(description="SEO Cleanup Utility")
    parser.add_argument("--no-dry-run", action="store_false", dest="dry_run", help="Apply changes")
    parser.set_defaults(dry_run=True)
    args = parser.parse_args()
    
    # Find YYYY-MM-DD.html files in the current root
    html_files = glob.glob("????-??-??.html")
    for file_path in html_files:
        process_file(file_path, args.dry_run)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit CLI utility**

```bash
git add page-generator/seo_cleanup.py
git commit -m "feat(seo): complete seo_cleanup.py CLI utility"
```

### Task 5: Implement tests

**Files:**
- Create: `tests/test_seo_cleanup.py`

- [ ] **Step 1: Write tests**

```python
import pytest
from page_generator.seo_cleanup import extract_metadata, scrub_and_inject, normalize_links

def test_extract_metadata():
    html = "<title>Babe Ruth Answer - 2025-03-29 | Name That Yankee</title>"
    name, date = extract_metadata(html)
    assert name == "Babe Ruth"
    assert date == "2025-03-29"

def test_scrub_and_inject():
    html = '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<meta name="description" content="old">\n<link rel="canonical" href="old">'
    name = "Babe Ruth"
    date = "2025-03-29"
    result = scrub_and_inject(html, name, date)
    assert 'https://namethatyankeequiz.com/2025-03-29' in result
    assert 'career highlights and statistics for Babe Ruth' in result
    assert 'content="old"' not in result

def test_normalize_links():
    html = '<a href="2025-03-30.html">Next</a>'
    result = normalize_links(html)
    assert result == '<a href="2025-03-30">Next</a>'
```

- [ ] **Step 2: Run tests**

```bash
pytest tests/test_seo_cleanup.py
```

- [ ] **Step 3: Commit tests**

```bash
git add tests/test_seo_cleanup.py
git commit -m "test(seo): add tests for seo_cleanup utility"
```

### Task 6: Execution and Verification

- [ ] **Step 1: Perform dry run**

```bash
python3 page-generator/seo_cleanup.py --dry-run
```

- [ ] **Step 2: Perform final cleanup**

```bash
python3 page-generator/seo_cleanup.py --no-dry-run
```

- [ ] **Step 3: Commit all changed files**

```bash
git add *.html
git commit -m "feat(seo): run batch cleanup on historical files"
```
