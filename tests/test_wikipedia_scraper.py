# ABOUTME: Unit tests for the Wikipedia summary scraper.
# ABOUTME: Verifies that player biographies are correctly fetched from Wikipedia API.

import sys
from pathlib import Path
import pytest

# Add the page-generator directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "page-generator"))

from scraper import get_wikipedia_summary

def test_get_wikipedia_summary_sal_fasano():
    """Tests fetching the Wikipedia summary for Sal Fasano."""
    player_name = "Sal Fasano"
    summary = get_wikipedia_summary(player_name)
    
    # Assert that we got some content
    assert summary is not None
    assert len(summary) > 100
    
    # Assert some specific content known to be in his summary
    assert "Sal" in summary
    assert "Fasano" in summary
    assert "catcher" in summary.lower()

def test_get_wikipedia_summary_nonexistent():
    """Tests fetching the Wikipedia summary for a nonexistent player."""
    player_name = "Nonexistent FakePlayerNameXYZ"
    summary = get_wikipedia_summary(player_name)
    
    # Assert that it returns None gracefully
    assert summary is None
