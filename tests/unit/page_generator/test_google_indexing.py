# ABOUTME: Unit tests for Google Indexing API client.
# ABOUTME: Tests URL submission and error handling using mocked API responses.
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from indexing.google_indexing import GoogleIndexingClient

FIXTURE_DIR = Path(__file__).parent.parent.parent / "fixtures"


class TestGoogleIndexingClient:
    def test_submit_url_success(self):
        """Test successful URL submission returns metadata."""
        mock_response = json.loads(
            (FIXTURE_DIR / "mock_indexing_response.json").read_text()
        )

        with patch(
            "indexing.google_indexing.build"
        ) as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.urlNotifications().publish.return_value.execute.return_value = (
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
            "indexing.google_indexing.build"
        ) as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.urlNotifications().publish.return_value.execute.return_value = {}

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
            "indexing.google_indexing.build"
        ) as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_service.urlNotifications().publish.return_value.execute.side_effect = Exception(
                "Quota exceeded"
            )

            client = GoogleIndexingClient.__new__(GoogleIndexingClient)
            client.service = mock_service

            with pytest.raises(Exception, match="Quota exceeded"):
                client.submit_url("https://namethatyankeequiz.com/2026-07-20")
