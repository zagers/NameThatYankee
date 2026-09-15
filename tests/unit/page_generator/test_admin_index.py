# ABOUTME: Unit tests for the admin_data.json generator.
# ABOUTME: Verifies extraction from puzzle detail pages and pool analysis.
import json

from bs4 import BeautifulSoup  # type: ignore
import admin_index  # type: ignore


def _soup(detail_html: str) -> BeautifulSoup:
    return BeautifulSoup(detail_html, "html.parser")


def test_extract_quiz_data_names_array():
    html = '<div id="quiz-data" style="display:none;">{"answer": "Billy Martin", "nicknames": ["Billy", "Boys Club Basher"], "hints": ["h"]}</div>'
    data = admin_index.extract_quiz_data(_soup(html))
    assert data == {"answer": "Billy Martin", "nicknames": ["Billy", "Boys Club Basher"]}


def test_extract_quiz_data_legacy_nickname_string():
    html = '<div id="quiz-data" style="display:none;">{"answer": "Lou Piniella", "nickname": "Sweet Lou", "hints": ["h"]}</div>'
    data = admin_index.extract_quiz_data(_soup(html))
    assert data == {"answer": "Lou Piniella", "nicknames": ["Sweet Lou"]}


def test_extract_quiz_data_missing_div():
    assert admin_index.extract_quiz_data(_soup("<html></html>")) == {"answer": "", "nicknames": []}


def test_extract_search_data():
    html = '<div id="search-data" style="display:none;">{"teams": ["NYY", "DET"], "years": ["1950", "1951"]}</div>'
    data = admin_index.extract_search_data(_soup(html))
    assert data == {"teams": ["NYY", "DET"], "years": ["1950", "1951"]}


def test_extract_search_data_missing_div():
    assert admin_index.extract_search_data(_soup("<html></html>")) == {"teams": [], "years": []}
