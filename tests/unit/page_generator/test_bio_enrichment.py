import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import os

# Add page-generator to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../page-generator")))
import main

def test_enrich_player_bio_skips_if_already_long():
    with patch('scraper.get_wikipedia_summary') as mock_wiki:
        existing_bio = "A" * 600
        result = main.enrich_player_bio("Derek Jeter", existing_bio)
        assert result == existing_bio
        mock_wiki.assert_not_called()

def test_enrich_player_bio_fetches_if_short():
    with patch('scraper.get_wikipedia_summary') as mock_wiki:
        mock_wiki.return_value = "Long Wikipedia Summary Content..."
        existing_bio = "Short bio"
        result = main.enrich_player_bio("Derek Jeter", existing_bio)
        assert "Long Wikipedia Summary Content..." in result
        mock_wiki.assert_called_once_with("Derek Jeter")

def test_enrich_player_bio_force_override():
    with patch('scraper.get_wikipedia_summary') as mock_wiki:
        mock_wiki.return_value = "Forced content"
        existing_bio = "A" * 1000
        result = main.enrich_player_bio("Derek Jeter", existing_bio, force=True)
        assert "Forced content" in result
        mock_wiki.assert_called_once_with("Derek Jeter")
