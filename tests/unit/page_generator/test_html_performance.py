import pytest
from pathlib import Path
import sys
import os

# Add page-generator to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../page-generator')))
from html_generator import build_detail_page_html, generate_gallery_snippet

def test_generate_gallery_snippet_lcp_logic():
    # Item 0 (First) - Should be EAGER
    html_0 = generate_gallery_snippet(0, "2026-04-17", "April 17, 2026", "terms")
    assert 'loading="lazy"' not in html_0
    
    # Item 5 (Sixth) - Should be EAGER (last one above the fold)
    html_5 = generate_gallery_snippet(5, "2026-04-12", "April 12, 2026", "terms")
    assert 'loading="lazy"' not in html_5
    
    # Item 6 (Seventh) - Should be LAZY
    html_6 = generate_gallery_snippet(6, "2026-04-11", "April 11, 2026", "terms")
    assert 'loading="lazy"' in html_6

def test_build_detail_page_includes_performance_attributes():
    player_data = {
        'name': 'Test Player',
        'nickname': 'Testy',
        'facts': ['Fact 1'],
        'career_totals': {'G': '100'},
        'yearly_war': [{'year': '2020', 'war': 1.0, 'teams': ['NYY'], 'display_team': 'NYY'}]
    }
    html = build_detail_page_html(player_data, "2020-01-01", "January 01, 2020")
    
    # Detail pages should eager load (no loading="lazy")
    assert 'loading="lazy"' not in html
    assert 'decoding="async"' in html
