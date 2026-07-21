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
        mock_creds = MagicMock()

        with patch(
            "search_console.submit_sitemap.service_account.Credentials.from_service_account_file",
            return_value=mock_creds,
        ), patch(
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
        mock_creds = MagicMock()

        with patch(
            "search_console.submit_sitemap.service_account.Credentials.from_service_account_file",
            return_value=mock_creds,
        ), patch(
            "search_console.submit_sitemap.build", return_value=mock_service
        ):
            from search_console.submit_sitemap import submit_sitemap

            result = submit_sitemap(
                credentials_file="fake_creds.json",
                site_url="https://example.com/",
                sitemap_url="https://example.com/sitemap.xml",
            )

            assert result is False
