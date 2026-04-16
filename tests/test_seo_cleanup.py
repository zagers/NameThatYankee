import pytest
import sys
import os
from bs4 import BeautifulSoup

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Add page-generator to sys.path to allow importing from it directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'page-generator')))

from seo_cleanup import extract_metadata, scrub_and_inject, normalize_links

def test_extract_metadata_standard():
    html = "<title>Babe Ruth Answer - 2025-03-29 | Name That Yankee</title>"
    soup = BeautifulSoup(html, 'html.parser')
    name, date = extract_metadata(soup)
    assert name == "Babe Ruth"
    assert date == "2025-03-29"

def test_extract_metadata_2026_format():
    html = "<title>Answer for 2026-03-05 | Name That Yankee</title><h2>Derek Jeter</h2>"
    soup = BeautifulSoup(html, 'html.parser')
    name, date = extract_metadata(soup)
    assert name == "Derek Jeter"
    assert date == "2026-03-05"

def test_extract_metadata_multiline_and_extra_space():
    html = """
    <title>
        Lou Gehrig 
        Answer - 
        2025-04-01 | 
        Name That Yankee
    </title>
    """
    soup = BeautifulSoup(html, 'html.parser')
    name, date = extract_metadata(soup)
    assert name == "Lou Gehrig"
    assert date == "2025-04-01"

def test_scrub_and_inject_robust():
    html = """
    <html>
    <head>
        <meta content="width=device-width, initial-scale=1.0" name="viewport">
        <link href="old" rel="canonical">
        <meta content="old" name="description">
    </head>
    <body></body>
    </html>
    """
    name = "Babe Ruth"
    date_stem = "2025-03-29"
    soup = BeautifulSoup(html, 'html.parser')
    result_soup = scrub_and_inject(soup, name, date_stem)
    result_html = str(result_soup)
    
    assert 'href="https://namethatyankeequiz.com/2025-03-29"' in result_html
    assert 'career highlights and statistics for Babe Ruth' in result_html
    assert 'content="old"' not in result_html
    assert 'href="old"' not in result_html

def test_normalize_links_bs4():
    html = '<div><a href="2025-03-30.html">Next</a><a href="index.html">Home</a></div>'
    soup = BeautifulSoup(html, 'html.parser')
    result_soup = normalize_links(soup)
    result_html = str(result_soup)
    assert 'href="2025-03-30"' in result_html
    assert 'href="index"' in result_html
