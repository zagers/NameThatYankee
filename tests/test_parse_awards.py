# ABOUTME: Unit tests for award parsing in scraper.py.
# ABOUTME: Verifies awards are extracted from the live Baseball-Reference bling structure.

import sys
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent / "page-generator"))

from scraper import parse_awards


def test_parse_awards_extracts_from_bling_ul():
    html = """<ul id="bling">
        <li class="all_star"><a href="/allstar/">1x All-Star</a></li>
        <li class=""><a href="/postseason/">1983 World Series</a></li>
    </ul>"""
    soup = BeautifulSoup(html, "html.parser")
    awards = parse_awards(soup)
    assert awards == ["1x All-Star", "1983 World Series"]


def test_parse_awards_empty_when_no_awards():
    soup = BeautifulSoup("<html><body><p>No awards here</p></body></html>", "html.parser")
    assert parse_awards(soup) == []
