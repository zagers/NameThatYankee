# ABOUTME: Google Indexing API client for submitting URLs to Google.
# ABOUTME: Handles authentication via service account and URL submission.
"""Google Indexing API client for requesting indexing of URLs.

Usage:
    from indexing import GoogleIndexingClient

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
