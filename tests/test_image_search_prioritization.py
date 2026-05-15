# ABOUTME: Unit tests for candidate prioritization logic in player image search.
# ABOUTME: Verifies domain-based sorting and deduplication of search results.
import pytest
from pathlib import Path
import sys
import os

# Add page-generator to path
sys.path.append(os.path.join(os.getcwd(), "page-generator"))

from automation.player_image_search import PlayerImageSearch

def test_deduplication_preserves_order():
    # Setup
    search = PlayerImageSearch(Path("images"))
    candidates = [
        {'direct_url': 'https://example.com/normal.jpg'},
        {'direct_url': 'https://ebayimg.com/card.jpg'},
        {'direct_url': 'https://another.com/img.png'},
        {'direct_url': 'https://example.com/normal.jpg'} # Duplicate
    ]
    
    # It should:
    # 1. Deduplicate by direct_url
    # 2. Preserve the original search order
    
    unique = search._deduplicate_candidates(candidates)
    
    assert len(unique) == 3
    assert unique[0]['direct_url'] == 'https://example.com/normal.jpg'
    assert unique[1]['direct_url'] == 'https://ebayimg.com/card.jpg'
    assert unique[2]['direct_url'] == 'https://another.com/img.png'
