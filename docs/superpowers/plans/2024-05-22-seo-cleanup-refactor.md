# SEO Cleanup Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `seo_cleanup.py` to use `BeautifulSoup` for robust HTML manipulation, fix canonical URL formatting, and improve player name extraction.

**Architecture:**
- Use `BeautifulSoup` with `html.parser` for all HTML modifications.
- Extract player name from `<title>` (various formats) or fallback to `<h2>`.
- Canonical URL always uses the file's date stem (YYYY-MM-DD).
- Normalize links using BeautifulSoup to replace `.html` extensions in internal links.

**Tech Stack:** Python 3, BeautifulSoup4, Pytest

---

### Task 1: Update Tests for New Requirements

**Files:**
- Modify: `tests/test_seo_cleanup.py`

- [ ] **Step 1: Update existing tests to reflect new requirements and add new ones for edge cases.**

- [ ] **Step 2: Run tests to verify they fail with current implementation.**

Run: `/Users/zagers/Documents/code/NameThatYankee/.worktrees/seo-finalization/.venv/bin/pytest tests/test_seo_cleanup.py -v`

### Task 2: Refactor `seo_cleanup.py`

**Files:**
- Modify: `page-generator/seo_cleanup.py`

- [ ] **Step 1: Refactor `extract_metadata` to use BeautifulSoup and handle 2026/fallback cases.**
- [ ] **Step 2: Refactor `scrub_and_inject` to use BeautifulSoup.**
- [ ] **Step 3: Refactor `normalize_links` to use BeautifulSoup.**
- [ ] **Step 4: Update `process_file` and `main` to use BeautifulSoup and `pathlib`.**

### Task 3: Execution and Verification

- [ ] **Step 1: Run tests and ensure they pass.**
- [ ] **Step 2: Run cleanup utility with `--no-dry-run`.**
- [ ] **Step 3: Commit all changes.**
