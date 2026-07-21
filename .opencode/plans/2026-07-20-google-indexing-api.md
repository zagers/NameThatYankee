# Google Indexing API Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically submit newly deployed pages to Google Indexing API for faster indexing (minutes vs days).

**Architecture:** Add a Python script that calls Google Indexing API using service account credentials, integrated as a post-deploy step in the GitHub Actions workflow. The script compares the current sitemap with previously indexed URLs and submits only new pages.

**Tech Stack:** Python, Google API client library (`google-api-python-client`, `google-auth`), GitHub Actions

## Global Constraints

- Python 3.12 (matches CI)
- GCP service account credentials stored as GitHub secret (`GOOGLE_INDEXING_CREDENTIALS`)
- Max 200 Indexing API requests per day per project
- Must not block deployment on API failure (non-blocking step)
- Follow existing code patterns in `page-generator/automation/`

---

## File Structure

```
page-generator/
  indexing/                      # NEW directory
    __init__.py
    google_indexing.py          # Core Indexing API client
    submit_urls.py             # CLI entry point for submitting URLs

.github/workflows/
  deploy.yml                   # MODIFY: Add indexing step after deploy

tests/unit/page_generator/
  test_google_indexing.py      # NEW: Unit tests for indexing client

tests/fixtures/
  mock_indexing_response.json  # NEW: Test fixture
```

---

## Task 1: Create Indexing API Client

**Files:**
- Create: `page-generator/indexing/__init__.py`
- Create: `page-generator/indexing/google_indexing.py`
- Create: `tests/unit/page_generator/test_google_indexing.py`
- Create: `tests/fixtures/mock_indexing_response.json`

**Interfaces:**
- Produces: `GoogleIndexingClient` class with `submit_url(url: str) -> dict` method

- [ ] **Step 1: Create the test fixture**

Create `tests/fixtures/mock_indexing_response.json`:

```json
{
  "urlNotificationMetadata": {
    "url": "https://namethatyankeequiz.com/2026-07-20",
    "latestUpdate": {
      "type": "URL_UPDATED",
      "notifyTime": "2026-07-20T12:00:00Z"
    }
  }
}
```

- [ ] **Step 2: Write the failing test**

Create `tests/unit/page_generator/test_google_indexing.py`:

```python
# ABOUTME: Unit tests for Google Indexing API client.
# ABOUTME: Tests URL submission and error handling using mocked API responses.
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from page_generator.indexing.google_indexing import GoogleIndexingClient

FIXTURE_DIR = Path(__file__).parent.parent.parent / "fixtures"


class TestGoogleIndexingClient:
    def test_submit_url_success(self):
        """Test successful URL submission returns metadata."""
        mock_response = json.loads(
            (FIXTURE_DIR / "mock_indexing_response.json").read_text()
        )

        with patch(
            "page_generator.indexing.google_indexing.build"
        ) as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.urlNotifications().publish().execute.return_value = (
                mock_response
            )

            client = GoogleIndexingClient.__new__(GoogleIndexingClient)
            client.service = mock_service

            result = client.submit_url("https://namethatyankeequiz.com/2026-07-20")

            assert result == mock_response
            mock_service.urlNotifications().publish.assert_called_once()

    def test_submit_url_returns_url(self):
        """Test that the submitted URL is included in the request."""
        with patch(
            "page_generator.indexing.google_indexing.build"
        ) as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.urlNotifications().publish().execute.return_value = {}

            client = GoogleIndexingClient.__new__(GoogleIndexingClient)
            client.service = mock_service

            url = "https://namethatyankeequiz.com/2026-07-20"
            client.submit_url(url)

            call_args = mock_service.urlNotifications().publish.call_args
            body = call_args[1]["body"] if "body" in call_args[1] else call_args[0][0]
            assert body["url"] == url
            assert body["type"] == "URL_UPDATED"

    def test_submit_url_handles_api_error(self):
        """Test that API errors are caught and re-raised with context."""
        with patch(
            "page_generator.indexing.google_indexing.build"
        ) as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.urlNotifications().publish().execute.side_effect = Exception(
                "Quota exceeded"
            )

            client = GoogleIndexingClient.__new__(GoogleIndexingClient)
            client.service = mock_service

            with pytest.raises(Exception, match="Quota exceeded"):
                client.submit_url("https://namethatyankeequiz.com/2026-07-20")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/unit/page_generator/test_google_indexing.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'page_generator.indexing'`

- [ ] **Step 4: Create the indexing client**

Create `page-generator/indexing/__init__.py`:

```python
"""Google Indexing API integration for faster page indexing."""
```

Create `page-generator/indexing/google_indexing.py`:

```python
# ABOUTME: Google Indexing API client for submitting URLs to Google.
# ABOUTME: Handles authentication via service account and URL submission.
"""Google Indexing API client for requesting indexing of URLs.

Usage:
    from page_generator.indexing import GoogleIndexingClient

    client = GoogleIndexingClient.from_credentials_file("path/to/creds.json")
    result = client.submit_url("https://namethatyankeequiz.com/2026-07-20")

Requires:
    - google-api-python-client
    - google-auth
    - Service account with Indexing API enabled
    - Service account email must be owner in Google Search Console
"""

import logging
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/indexing"]
INDEXING_API_NAME = "indexing"
INDEXING_API_VERSION = "v3"


class GoogleIndexingClient:
    """Client for Google Indexing API."""

    def __init__(self, credentials_file: str | Path):
        """Initialize client with path to service account credentials JSON.

        Args:
            credentials_file: Path to the GCP service account JSON key file.
        """
        self.credentials_file = Path(credentials_file)
        self.service = self._build_service()

    def _build_service(self):
        """Build and return the Indexing API service object."""
        credentials = service_account.Credentials.from_service_account_file(
            str(self.credentials_file), scopes=SCOPES
        )
        return build(INDEXING_API_NAME, INDEXING_API_VERSION, credentials=credentials)

    def submit_url(self, url: str) -> dict:
        """Submit a URL to Google for indexing.

        Args:
            url: The full URL to submit (e.g., "https://namethatyankeequiz.com/2026-07-20")

        Returns:
            dict: The API response containing URL notification metadata.

        Raises:
            Exception: If the API call fails.
        """
        body = {"url": url, "type": "URL_UPDATED"}
        logger.info(f"Submitting URL to Indexing API: {url}")

        response = self.service.urlNotifications().publish(body=body).execute()
        logger.info(f"Indexing API response: {response}")
        return response

    @classmethod
    def from_credentials_file(cls, credentials_file: str | Path) -> "GoogleIndexingClient":
        """Create client from credentials file path.

        Args:
            credentials_file: Path to the GCP service account JSON key file.

        Returns:
            GoogleIndexingClient: Initialized client instance.
        """
        return cls(credentials_file)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/unit/page_generator/test_google_indexing.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add page-generator/indexing/ tests/unit/page_generator/test_google_indexing.py tests/fixtures/mock_indexing_response.json
git commit -m "feat: add Google Indexing API client"
```

---

## Task 2: Create URL Submission Script

**Files:**
- Create: `page-generator/indexing/submit_urls.py`
- Create: `tests/unit/page_generator/test_submit_urls.py`
- Create: `tests/fixtures/mock_sitemap.xml`

**Interfaces:**
- Consumes: `GoogleIndexingClient` from Task 1
- Produces: CLI script `python -m page_generator.indexing.submit_urls`

- [ ] **Step 1: Create sitemap fixture**

Create `tests/fixtures/mock_sitemap.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://namethatyankeequiz.com/</loc>
    <lastmod>2026-07-20</lastmod>
  </url>
  <url>
    <loc>https://namethatyankeequiz.com/2026-07-19</loc>
    <lastmod>2026-07-19</lastmod>
  </url>
  <url>
    <loc>https://namethatyankeequiz.com/2026-07-20</loc>
    <lastmod>2026-07-20</lastmod>
  </url>
</urlset>
```

- [ ] **Step 2: Write the failing test**

Create `tests/unit/page_generator/test_submit_urls.py`:

```python
# ABOUTME: Tests for the URL submission script.
# ABOUTME: Validates sitemap parsing and URL filtering logic.
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from page_generator.indexing.submit_urls import parse_sitemap, filter_new_urls

FIXTURE_DIR = Path(__file__).parent.parent.parent / "fixtures"


class TestParseSitemap:
    def test_parses_urls_from_sitemap(self):
        """Test that URLs are extracted from sitemap XML."""
        sitemap_path = FIXTURE_DIR / "mock_sitemap.xml"
        urls = parse_sitemap(sitemap_path)

        assert len(urls) == 3
        assert "https://namethatyankeequiz.com/" in urls
        assert "https://namethatyankeequiz.com/2026-07-19" in urls
        assert "https://namethatyankeequiz.com/2026-07-20" in urls

    def test_handles_missing_sitemap(self):
        """Test that missing sitemap raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_sitemap(Path("/nonexistent/sitemap.xml"))


class TestFilterNewUrls:
    def test_filters_already_indexed_urls(self):
        """Test that previously indexed URLs are excluded."""
        all_urls = [
            "https://namethatyankeequiz.com/",
            "https://namethatyankeequiz.com/2026-07-19",
            "https://namethatyankeequiz.com/2026-07-20",
        ]
        indexed = {"https://namethatyankeequiz.com/", "https://namethatyankeequiz.com/2026-07-19"}

        new_urls = filter_new_urls(all_urls, indexed)

        assert len(new_urls) == 1
        assert "https://namethatyankeequiz.com/2026-07-20" in new_urls

    def test_excludes_index_html(self):
        """Test that index.html pages are excluded."""
        all_urls = [
            "https://namethatyankeequiz.com/",
            "https://namethatyankeequiz.com/2026-07-20",
        ]

        new_urls = filter_new_urls(all_urls, set())

        assert len(new_urls) == 1
        assert "https://namethatyankeequiz.com/2026-07-20" in new_urls

    def test_excludes_non_page_urls(self):
        """Test that non-page URLs (images, css, etc.) are excluded."""
        all_urls = [
            "https://namethatyankeequiz.com/2026-07-20",
            "https://namethatyankeequiz.com/images/clue-2026-07-20.webp",
            "https://namethatyankeequiz.com/style.css",
        ]

        new_urls = filter_new_urls(all_urls, set())

        assert len(new_urls) == 1
        assert "https://namethatyankeequiz.com/2026-07-20" in new_urls
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/unit/page_generator/test_submit_urls.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'page_generator.indexing.submit_urls'`

- [ ] **Step 4: Implement the submission script**

Create `page-generator/indexing/submit_urls.py`:

```python
# ABOUTME: CLI script to submit new URLs to Google Indexing API.
# ABOUTME: Reads sitemap, filters new pages, and submits to Indexing API.
"""Submit new URLs to Google Indexing API.

Usage:
    python -m page_generator.indexing.submit_urls \\
        --credentials /path/to/creds.json \\
        --sitemap /path/to/sitemap.xml

This script:
1. Parses the sitemap to find all URLs
2. Filters out non-page URLs and already-indexed URLs
3. Submits new URLs to Google Indexing API
"""

import argparse
import json
import logging
from pathlib import Path
from xml.etree import ElementTree

from page_generator.indexing.google_indexing import GoogleIndexingClient

logger = logging.getLogger(__name__)

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
EXCLUDE_PATTERNS = ["/images/", "/docs/", ".css", ".js", ".webp", ".png", ".jpg"]


def parse_sitemap(sitemap_path: Path) -> list[str]:
    """Parse sitemap XML and return list of URLs.

    Args:
        sitemap_path: Path to the sitemap.xml file.

    Returns:
        List of URLs found in the sitemap.

    Raises:
        FileNotFoundError: If sitemap file doesn't exist.
    """
    if not sitemap_path.exists():
        raise FileNotFoundError(f"Sitemap not found: {sitemap_path}")

    tree = ElementTree.parse(sitemap_path)
    root = tree.getroot()

    urls = []
    for url_elem in root.findall(f"{{{SITEMAP_NS}}}url"):
        loc = url_elem.find(f"{{{SITEMAP_NS}}}loc")
        if loc is not None and loc.text:
            urls.append(loc.text)

    return urls


def filter_new_urls(urls: list[str], indexed_urls: set[str]) -> list[str]:
    """Filter URLs to only include new, indexable pages.

    Args:
        urls: List of all URLs from sitemap.
        indexed_urls: Set of URLs already submitted for indexing.

    Returns:
        List of new URLs that should be submitted.
    """
    new_urls = []
    for url in urls:
        # Skip if already indexed
        if url in indexed_urls:
            continue

        # Skip root URL
        if url.rstrip("/") == "https://namethatyankeequiz.com":
            continue

        # Skip non-page URLs
        if any(pattern in url for pattern in EXCLUDE_PATTERNS):
            continue

        new_urls.append(url)

    return new_urls


def main():
    """Main entry point for the submission script."""
    parser = argparse.ArgumentParser(description="Submit URLs to Google Indexing API")
    parser.add_argument(
        "--credentials",
        required=True,
        help="Path to GCP service account credentials JSON",
    )
    parser.add_argument(
        "--sitemap",
        required=True,
        help="Path to sitemap.xml",
    )
    parser.add_argument(
        "--state-file",
        default=".indexing_state.json",
        help="Path to state file tracking submitted URLs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview URLs without submitting",
    )
    args = parser.parse_args()

    # Load state
    state_path = Path(args.state_file)
    if state_path.exists():
        state = json.loads(state_path.read_text())
        indexed_urls = set(state.get("indexed_urls", []))
    else:
        indexed_urls = set()

    # Parse sitemap
    sitemap_path = Path(args.sitemap)
    all_urls = parse_sitemap(sitemap_path)
    logger.info(f"Found {len(all_urls)} URLs in sitemap")

    # Filter new URLs
    new_urls = filter_new_urls(all_urls, indexed_urls)
    logger.info(f"Found {len(new_urls)} new URLs to submit")

    if not new_urls:
        print("No new URLs to submit.")
        return

    if args.dry_run:
        print("Dry run - URLs that would be submitted:")
        for url in new_urls:
            print(f"  - {url}")
        return

    # Submit URLs
    client = GoogleIndexingClient(args.credentials)
    submitted = []

    for url in new_urls:
        try:
            client.submit_url(url)
            submitted.append(url)
            logger.info(f"Successfully submitted: {url}")
        except Exception as e:
            logger.error(f"Failed to submit {url}: {e}")

    # Update state
    indexed_urls.update(submitted)
    state_path.write_text(json.dumps({"indexed_urls": sorted(indexed_urls)}, indent=2))
    print(f"Submitted {len(submitted)} URLs for indexing.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/unit/page_generator/test_submit_urls.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add page-generator/indexing/submit_urls.py tests/unit/page_generator/test_submit_urls.py tests/fixtures/mock_sitemap.xml
git commit -m "feat: add URL submission script with sitemap parsing"
```

---

## Task 3: Add Google API Dependencies

**Files:**
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: None
- Produces: Required Python packages for Indexing API

- [ ] **Step 1: Add dependencies to requirements.txt**

Add to `requirements.txt`:

```
google-api-python-client>=2.100.0
google-auth>=2.23.0
```

- [ ] **Step 2: Install and verify**

Run: `pip install -r requirements.txt`
Expected: Successfully installs `google-api-python-client` and `google-auth`

- [ ] **Step 3: Run all unit tests**

Run: `python -m pytest tests/unit/ -v`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: add Google API client dependencies for Indexing API"
```

---

## Task 4: Integrate into Deploy Workflow

**Files:**
- Modify: `.github/workflows/deploy.yml`

**Interfaces:**
- Consumes: `page_generator.indexing.submit_urls` module
- Produces: Updated deploy workflow with indexing step

- [ ] **Step 1: Add indexing step to deploy job**

Add after the "Deploy to GitHub Pages" step in `deploy.yml`:

```yaml
  # The Deploy job
  deploy:
    if: github.event_name == 'push' && github.ref == 'refs/heads/master'
    needs: [build, security-scan]
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4

      - name: Submit new URLs to Google Indexing API
        if: success()
        continue-on-error: true
        run: |
          pip install google-api-python-client google-auth
          python -m page_generator.indexing.submit_urls \
            --credentials /tmp/google-indexing-creds.json \
            --sitemap ./_site/sitemap.xml \
            --state-file .indexing_state.json

      - name: Write indexing state
        if: success()
        uses: actions/upload-artifact@v4
        with:
          name: indexing-state
          path: .indexing_state.json
          retention-days: 90
```

- [ ] **Step 2: Add secrets instructions as comments**

Add a comment block at the top of `deploy.yml` explaining required secrets:

```yaml
# Required secrets:
#   GOOGLE_INDEXING_CREDENTIALS: GCP service account JSON key file
#     - Service account must have Indexing API enabled
#     - Service account email must be owner in Google Search Console
#     - Get from: https://console.cloud.google.com/iam-admin/serviceaccounts
```

- [ ] **Step 3: Verify workflow syntax**

Run: `act -l` or check with `actionlint` if available
Expected: No syntax errors

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: add Google Indexing API step to deploy workflow"
```

---

## Task 5: Add Manual Indexing Command to CLI

**Files:**
- Modify: `page-generator/main.py`

**Interfaces:**
- Consumes: `submit_urls.main` from Task 2
- Produces: New CLI flag `--submit-indexing`

- [ ] **Step 1: Add CLI argument to main.py**

Add to the argument parser in `main.py`:

```python
parser.add_argument(
    "--submit-indexing",
    action="store_true",
    help="Submit new URLs to Google Indexing API",
)
```

- [ ] **Step 2: Add handler for the new flag**

Add handler after argument parsing:

```python
if args.submit_indexing:
    from page_generator.indexing.submit_urls import main as submit_main
    submit_main()
    sys.exit(0)
```

- [ ] **Step 3: Test CLI help**

Run: `python page-generator/main.py --help`
Expected: Shows `--submit-indexing` option

- [ ] **Step 4: Commit**

```bash
git add page-generator/main.py
git commit -m "feat: add --submit-indexing CLI flag"
```

---

## Task 6: Update Documentation

**Files:**
- Modify: `README_AUTOMATION.md`

**Interfaces:**
- Consumes: All previous tasks
- Produces: Updated documentation

- [ ] **Step 1: Add Indexing API section to README_AUTOMATION.md**

Add to `README_AUTOMATION.md`:

```markdown
## Google Indexing API Integration

New pages are automatically submitted to Google for indexing after deployment.

### Setup Requirements

1. **Google Cloud Service Account:**
   - Create at https://console.cloud.google.com/iam-admin/serviceaccounts
   - Enable "Indexing API" in the service account's API list
   - Download the JSON key file

2. **Google Search Console:**
   - Add the service account email as an **Owner** in Search Console
   - Go to Settings > Users and permissions > Add user

3. **GitHub Secrets:**
   - Add `GOOGLE_INDEXING_CREDENTIALS` with the contents of the JSON key file

### How It Works

1. After a successful deploy, the workflow parses the sitemap
2. New URLs (not previously submitted) are sent to Google Indexing API
3. Submission state is stored as a GitHub artifact for deduplication

### Manual Submission

To manually submit URLs:

```bash
python page-generator/main.py --submit-indexing \
    --credentials /path/to/creds.json \
    --sitemap ./_site/sitemap.xml
```

### Quotas

- Google Indexing API limit: 200 requests per day per project
- State file prevents duplicate submissions
```

- [ ] **Step 2: Commit**

```bash
git add README_AUTOMATION.md
git commit -m "docs: add Indexing API setup instructions"
```

---

## Verification Checklist

After implementation, verify:

1. [ ] All unit tests pass: `python -m pytest tests/unit/page_generator/test_google_indexing.py tests/unit/page_generator/test_submit_urls.py -v`
2. [ ] CLI help shows new flag: `python page-generator/main.py --help`
3. [ ] Workflow syntax is valid
4. [ ] Dry-run mode works: `python -m page_generator.indexing.submit_urls --credentials creds.json --sitemap sitemap.xml --dry-run`
