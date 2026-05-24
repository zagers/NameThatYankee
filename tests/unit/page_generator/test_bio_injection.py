import pytest
from pathlib import Path
import sys
import os
from bs4 import BeautifulSoup

# Add page-generator to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../page-generator")))
import html_generator

def test_generate_detail_page_includes_biography(tmp_path):
    player_data = {
        'name': 'Babe Ruth',
        'nickname': 'The Bambino',
        'facts': ['Fact 1'],
        'career_totals': {},
        'yearly_war': [],
        'followup_qa': [],
        'bio': "Babe Ruth was a legendary baseball player who played for the Yankees."
    }
    
    html_generator.generate_detail_page(player_data, "1920-01-01", "January 01, 1920", tmp_path)
    
    html_path = tmp_path / "1920-01-01.html"
    with open(html_path, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')
        bio_details = soup.find('div', class_='hidden-seo')
        assert bio_details is not None
        assert "Babe Ruth was a legendary baseball player" in bio_details.get_text()
