# ABOUTME: Unit tests for candidate prioritization logic in player image search.
# ABOUTME: Verifies domain-based sorting and deduplication of search results.
import pytest
from pathlib import Path
import sys
import os

# Add page-generator to path
sys.path.append(os.path.join(os.getcwd(), "page-generator"))

from automation.player_image_search import PlayerImageSearch

def test_prioritization_logic():
    # Setup
    search = PlayerImageSearch(Path("images"))
    candidates = [
        {'direct_url': 'https://example.com/normal.jpg'},
        {'direct_url': 'https://ebayimg.com/card.jpg'},
        {'direct_url': 'https://another.com/img.png'},
        {'direct_url': 'https://example.com/normal.jpg'} # Duplicate
    ]
    
    # We expect a new method _prioritize_candidates to handle this
    # It should:
    # 1. Deduplicate by direct_url
    # 2. Prioritize candidates from ebayimg.com
    
    # Check if method exists (it shouldn't yet, or shouldn't have the new logic)
    prioritized = search._prioritize_candidates(candidates)
    
    assert len(prioritized) == 3
    assert prioritized[0]['direct_url'] == 'https://ebayimg.com/card.jpg'
    assert prioritized[1]['direct_url'] == 'https://example.com/normal.jpg'
    assert prioritized[2]['direct_url'] == 'https://another.com/img.png'
