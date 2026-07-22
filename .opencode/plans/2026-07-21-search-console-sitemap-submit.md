# Search Console Sitemap Submit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After each deploy, automatically resubmit the sitemap to Google Search Console so Google re-reads it and discovers new answer pages.

**Architecture:** A small Python script calls the Search Console API `sitemaps.submit` endpoint using the existing GCP service account credentials. A deploy workflow step runs the script after GitHub Pages deployment succeeds.

**Tech Stack:** Python, `google-api-python-client`, `google-auth`, GitHub Actions

## Global Constraints

- Service account credentials stored as GitHub secret `GOOGLE_INDEXING_CREDENTIALS` (reuse existing)
- Service account email must be an **Owner** in Google Search Console
- Search Console API must be enabled in the GCP project (user enables manually)
- Deploy step uses `continue-on-error: true` so failure doesn't block deployment
- Site URL: `https://namethatyankeequiz.com/`
- Sitemap URL: `https://namethatyankeequiz.com/sitemap.xml`

---

## File Structure

| File | Purpose |
|------|---------|
| `page-generator/search_console/submit_sitemap.py` | Script to submit sitemap via API |
| `tests/unit/page_generator/test_submit_sitemap.py` | Unit tests |
| `.github/workflows/deploy.yml` | Add sitemap submit step after deploy |
| `requirements.txt` | Re-add `google-api-python-client` and `google-auth` |
| `README_AUTOMATION.md` | Document the Search Console sitemap integration |

---

### Task 1: Create Sitemap Submit Script

**Files:**
- Create: `page-generator/search_console/__init__.py`
- Create: `page-generator/search_console/submit_sitemap.py`
- Test: `tests/unit/page_generator/test_submit_sitemap.py`

**Interfaces:**
- Consumes: GCP service account credentials JSON file path
- Produces: `submit_sitemap(credentials_file, site_url, sitemap_url)` function

- [ ] **Step 1: Create the package init**

Create `page-generator/search_console/__init__.py`:

```python
# ABOUTME: Initialization for the search_console package.
# ABOUTME: Google Search Console API integration for sitemap management.
```

- [ ] **Step 2: Write the failing test**

Create `tests/unit/page_generator/test_submit_sitemap.py`:

```python
# ABOUTME: Unit tests for Search Console sitemap submission script.

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

FIXTURE_DIR = Path(__file__).parent.parent.parent / "fixtures"


class TestSubmitSitemap:
    def test_submit_calls_api(self):
        mock_service = MagicMock()
        mock_service.sitemaps.return_value.submit.return_value.execute.return_value = {}

        with patch(
            "search_console.submit_sitemap.build", return_value=mock_service
        ):
            from search_console.submit_sitemap import submit_sitemap

            result = submit_sitemap(
                credentials_file="fake_creds.json",
                site_url="https://example.com/",
                sitemap_url="https://example.com/sitemap.xml",
            )

            mock_service.sitemaps.return_value.submit.assert_called_once_with(
                siteUrl="https://example.com/",
                feedpath="https://example.com/sitemap.xml",
            )
            mock_service.sitemaps.return_value.submit.return_value.execute.assert_called_once()
            assert result is True

    def test_submit_handles_api_error(self):
        mock_service = MagicMock()
        mock_service.sitemaps.return_value.submit.return_value.execute.side_effect = Exception("API error")

        with patch(
            "search_console.submit_sitemap.build", return_value=mock_service
        ):
            from search_console.submit_sitemap import submit_sitemap

            result = submit_sitemap(
                credentials_file="fake_creds.json",
                site_url="https://example.com/",
                sitemap_url="https://example.com/sitemap.xml",
            )

            assert result is False
```

- [ ] **Step 3: Run test to verify it fails**

Run: `PYTHONPATH=./page-generator python3 -m pytest tests/unit/page_generator/test_submit_sitemap.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'search_console'`

- [ ] **Step 4: Write the implementation**

Create `page-generator/search_console/submit_sitemap.py`:

```python
# ABOUTME: Submit sitemap to Google Search Console via API.
# ABOUTME: Triggers Google to re-read the sitemap and discover new pages.
"""Submit sitemap to Google Search Console.

Usage:
    from search_console.submit_sitemap import submit_sitemap
    submit_sitemap("creds.json", "https://example.com/", "https://example.com/sitemap.xml")
"""

import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/webmasters"]


def submit_sitemap(
    credentials_file: str,
    site_url: str = "https://namethatyankeequiz.com/",
    sitemap_url: str = "https://namethatyankeequiz.com/sitemap.xml",
) -> bool:
    """Submit a sitemap URL to Google Search Console.

    Args:
        credentials_file: Path to GCP service account JSON key file.
        site_url: The property URL as defined in Search Console.
        sitemap_url: The full URL of the sitemap to submit.

    Returns:
        True if submission succeeded, False otherwise.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=SCOPES
        )
        service = build("webmasters", "v3", credentials=credentials)

        logger.info(f"Submitting sitemap to Search Console: {sitemap_url}")
        service.sitemaps().submit(
            siteUrl=site_url,
            feedpath=sitemap_url,
        ).execute()

        logger.info("Sitemap submitted successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to submit sitemap: {e}")
        return False
```

- [ ] **Step 5: Run test to verify it passes**

Run: `PYTHONPATH=./page-generator python3 -m pytest tests/unit/page_generator/test_submit_sitemap.py -v`
Expected: PASS

- [ ] **Step 6: Add test to test_requirements.txt**

Verify `test_requirements.txt` includes `pytest` and `pytest-mock` (should already be there).

- [ ] **Step 7: Commit**

```bash
git add page-generator/search_console/ tests/unit/page_generator/test_submit_sitemap.py
git commit -m "feat: add Search Console sitemap submit script"
```

---

### Task 2: Add Dependencies and Deploy Step

**Files:**
- Modify: `requirements.txt` — re-add `google-api-python-client` and `google-auth`
- Modify: `.github/workflows/deploy.yml` — add sitemap submit step after deploy

**Interfaces:**
- Consumes: `submit_sitemap()` from Task 1
- Produces: Updated deploy workflow that runs sitemap submit after each push

- [ ] **Step 1: Re-add Google API dependencies to requirements.txt**

Add after `google-api-core`:

```
google-api-python-client==2.193.0
google-auth==2.49.1
```

- [ ] **Step 2: Add sitemap submit step to deploy.yml**

Add after the "Deploy to GitHub Pages" step in the deploy job:

```yaml
      - name: Submit sitemap to Search Console
        if: success()
        continue-on-error: true
        env:
          CREDS: ${{ secrets.GOOGLE_INDEXING_CREDENTIALS }}
        run: |
          printf "%s" "$CREDS" > /tmp/search-console-creds.json
          pip install google-api-python-client google-auth
          PYTHONPATH=./page-generator python -m search_console.submit_sitemap \
            --credentials /tmp/search-console-creds.json
```

- [ ] **Step 3: Add CLI interface to submit_sitemap.py**

Add to the bottom of `page-generator/search_console/submit_sitemap.py`:

```python
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Submit sitemap to Google Search Console"
    )
    parser.add_argument(
        "--credentials",
        required=True,
        help="Path to GCP service account credentials JSON",
    )
    parser.add_argument(
        "--site-url",
        default="https://namethatyankeequiz.com/",
        help="Property URL in Search Console",
    )
    parser.add_argument(
        "--sitemap-url",
        default="https://namethatyankeequiz.com/sitemap.xml",
        help="Full URL of the sitemap to submit",
    )
    args = parser.parse_args()

    success = submit_sitemap(args.credentials, args.site_url, args.sitemap_url)
    raise SystemExit(0 if success else 1)
```

- [ ] **Step 4: Verify tests still pass**

Run: `npx vitest run`
Expected: All tests pass (same as before, firestore.rules.test.js is pre-existing failure)

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .github/workflows/deploy.yml page-generator/search_console/submit_sitemap.py
git commit -m "feat: submit sitemap to Search Console after deploy"
```

---

### Task 3: Document in README_AUTOMATION.md

**Files:**
- Modify: `README_AUTOMATION.md`

**Interfaces:**
- Consumes: None
- Produces: Updated documentation

- [ ] **Step 1: Add Search Console section to README_AUTOMATION.md**

Add after the "Automation as opt-in feature" paragraph and before "## Troubleshooting":

```markdown
## Google Search Console Sitemap Integration

After each deploy, the workflow automatically resubmits the sitemap to Google
Search Console, prompting Google to re-read it and discover new pages.

### Setup Requirements

1. **Google Cloud Service Account:**
   - Use an existing service account or create one at https://console.cloud.google.com/iam-admin/serviceaccounts
   - Enable "Search Console API" in the service account's API list
   - Download the JSON key file

2. **Google Search Console:**
   - Add the service account email as an **Owner** in Search Console
   - Go to Settings > Users and permissions > Add user

3. **GitHub Secrets:**
   - Add `GOOGLE_INDEXING_CREDENTIALS` with the contents of the JSON key file

### How It Works

1. After a successful deploy, the workflow runs `search_console/submit_sitemap.py`
2. The script calls `sitemaps.submit` via the Search Console API
3. Google re-reads the sitemap and indexes any new pages
```

- [ ] **Step 2: Commit**

```bash
git add README_AUTOMATION.md
git commit -m "docs: add Search Console sitemap integration to README"
```
