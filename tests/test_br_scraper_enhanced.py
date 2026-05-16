# ABOUTME: Tests for enhanced Baseball-Reference scraping capabilities.
# ABOUTME: Verifies extraction of transactions and awards for players.
import pytest
import sys
from pathlib import Path

# Add the page-generator directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "page-generator"))

from scraper import search_and_scrape_player

def test_scrape_player_enhanced_data():
    # Tippy Martinez is a good candidate with both transactions and awards
    player_name = "Tippy Martinez"
    result = search_and_scrape_player(player_name, automated=True)
    
    assert result is not None
    assert "transactions" in result
    assert isinstance(result["transactions"], list)
    assert len(result["transactions"]) > 0
    
    assert "awards" in result
    assert isinstance(result["awards"], list)
    assert len(result["awards"]) > 0
    
    # Specific check for Tippy Martinez awards (e.g., "1983 World Series")
    has_ws = any("World Series" in award for award in result["awards"])
    assert has_ws, f"Expected World Series in awards, got {result['awards']}"
