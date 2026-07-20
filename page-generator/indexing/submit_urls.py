# ABOUTME: CLI script to submit new URLs to Google Indexing API.
# ABOUTME: Reads sitemap, filters new pages, and submits to Indexing API.
"""Submit new URLs to Google Indexing API.

Usage:
    python -m page_generator.indexing.submit_urls \
        --credentials /path/to/creds.json \
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
from urllib.parse import urlparse
from xml.etree import ElementTree

from indexing.google_indexing import GoogleIndexingClient

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
        parsed_url = urlparse(url)
        if parsed_url.path.rstrip("/") == "":
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
    indexed_urls = set()
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text())
            indexed_urls = set(state.get("indexed_urls", []))
        except json.JSONDecodeError:
            logger.warning(f"Failed to decode state file: {state_path}. Starting with empty state.")

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
