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
    site_url: str = "sc-domain:namethatyankeequiz.com",
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


if __name__ == "__main__":
    import argparse
    import os

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

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
        default=os.getenv("SITE_URL", "sc-domain:namethatyankeequiz.com"),
        help="Property URL in Search Console",
    )
    parser.add_argument(
        "--sitemap-url",
        default=os.getenv("SITEMAP_URL", "https://namethatyankeequiz.com/sitemap.xml"),
        help="Full URL of the sitemap to submit",
    )
    args = parser.parse_args()

    success = submit_sitemap(args.credentials, args.site_url, args.sitemap_url)
    raise SystemExit(0 if success else 1)
