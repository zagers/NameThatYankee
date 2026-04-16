import pytest
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Add page-generator to sys.path to allow importing from it directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'page-generator')))

from seo_cleanup import extract_metadata, scrub_and_inject, normalize_links

def test_extract_metadata():
    html = "<title>Babe Ruth Answer - 2025-03-29 | Name That Yankee</title>"
    name, date = extract_metadata(html)
    assert name == "Babe Ruth"
    assert date == "2025-03-29"

def test_scrub_and_inject():
    html = '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<meta name="description" content="old">\n<link rel="canonical" href="old">'
    name = "Babe Ruth"
    date = "2025-03-29"
    result = scrub_and_inject(html, name, date)
    assert 'https://namethatyankeequiz.com/2025-03-29' in result
    assert 'career highlights and statistics for Babe Ruth' in result
    assert 'content="old"' not in result
    assert 'href="old"' not in result

def test_normalize_links():
    html = '<a href="2025-03-30.html">Next</a>'
    result = normalize_links(html)
    assert result == '<a href="2025-03-30">Next</a>'
