# ABOUTME: Unit tests for the SABR biography scraper.
# ABOUTME: Verifies that player biographies are correctly fetched from SABR.org.

import sys
from pathlib import Path
import pytest

# Add the page-generator directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "page-generator"))

from scraper import get_sabr_bio

def test_get_sabr_bio_tippy_martinez():
    """Tests fetching the SABR bio for Tippy Martinez."""
    player_name = "Tippy Martinez"
    bio = get_sabr_bio(player_name)
    
    # Assert that we got some content
    assert bio is not None
    assert len(bio) > 100
    
    # Assert some specific content known to be in his bio
    # Tippy Martinez is famous for his 3 pickoffs in one inning.
    assert "Tippy Martinez" in bio
    assert "pickoffs" in bio.lower()
