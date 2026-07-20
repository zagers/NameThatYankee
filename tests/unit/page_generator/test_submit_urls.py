# ABOUTME: Tests for the URL submission script.
# ABOUTME: Validates sitemap parsing and URL filtering logic.
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from indexing.submit_urls import parse_sitemap, filter_new_urls

FIXTURE_DIR = Path(__file__).parent.parent.parent / "fixtures"


class TestParseSitemap:
    def test_parses_urls_from_sitemap(self):
        """Test that URLs are extracted from sitemap XML."""
        sitemap_path = FIXTURE_DIR / "mock_sitemap.xml"
        urls = parse_sitemap(sitemap_path)

        assert len(urls) == 3
        expected_urls = {
            "https://namethatyankeequiz.com/",
            "https://namethatyankeequiz.com/2026-07-19",
            "https://namethatyankeequiz.com/2026-07-20",
        }
        assert expected_urls.issubset(set(urls))

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
        assert new_urls[0] == "https://namethatyankeequiz.com/2026-07-20"

    def test_excludes_index_html(self):
        """Test that index.html pages are excluded."""
        all_urls = [
            "https://namethatyankeequiz.com/",
            "https://namethatyankeequiz.com/2026-07-20",
        ]

        new_urls = filter_new_urls(all_urls, set())

        assert len(new_urls) == 1
        assert new_urls[0] == "https://namethatyankeequiz.com/2026-07-20"

    def test_excludes_non_page_urls(self):
        """Test that non-page URLs (images, css, etc.) are excluded."""
        all_urls = [
            "https://namethatyankeequiz.com/2026-07-20",
            "https://namethatyankeequiz.com/images/clue-2026-07-20.webp",
            "https://namethatyankeequiz.com/style.css",
        ]

        new_urls = filter_new_urls(all_urls, set())

        assert len(new_urls) == 1
        assert new_urls[0] == "https://namethatyankeequiz.com/2026-07-20"
