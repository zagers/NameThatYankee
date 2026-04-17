import pytest
from pathlib import Path
import sys
import os

# Add page-generator to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../page-generator')))
from html_generator import build_detail_page_html

def test_build_detail_page_includes_performance_attributes():
    player_data = {
        'name': 'Test Player',
        'nickname': 'Testy',
        'facts': ['Fact 1'],
        'career_totals': {'G': '100'},
        'yearly_war': [{'year': '2020', 'war': 1.0, 'teams': ['NYY'], 'display_team': 'NYY'}]
    }
    html = build_detail_page_html(player_data, "2020-01-01", "January 01, 2020")
    
    assert 'loading="lazy"' in html
    assert 'decoding="async"' in html
