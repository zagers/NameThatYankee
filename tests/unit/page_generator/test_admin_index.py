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


def test_extract_career_totals():
    html = (
        '<div class="stats-table-container"><div class="table-wrapper"><table>'
        "<thead><tr><th>WAR</th><th>AB</th><th>HR</th></tr></thead>"
        "<tbody><tr><td>2.9</td><td>3419</td><td>64</td></tr></tbody>"
        "</table></div></div>"
    )
    data = admin_index.extract_career_totals(_soup(html))
    assert data == {"WAR": "2.9", "AB": "3419", "HR": "64"}


def test_extract_career_totals_missing():
    assert admin_index.extract_career_totals(_soup("<html></html>")) == {}


def test_extract_followup_qa():
    html = (
        '<div class="followup-item">'
        '<button class="followup-btn" data-answer="Pine tar removed the homer.">1983 pine tar?</button>'
        '<div class="followup-answer" style="display:none;"></div></div>'
        '<div class="followup-item">'
        '<button class="followup-btn" data-answer="Fractured orbital bone.">1960 altercation?</button>'
        '<div class="followup-answer" style="display:none;"></div></div>'
    )
    qa = admin_index.extract_followup_qa(_soup(html))
    assert qa == [
        {"question": "1983 pine tar?", "answer": "Pine tar removed the homer."},
        {"question": "1960 altercation?", "answer": "Fractured orbital bone."},
    ]


def test_extract_followup_qa_none():
    assert admin_index.extract_followup_qa(_soup("<html></html>")) == []


def test_extract_war_arc():
    html = (
        "<script>\n"
        'const years = ["1950", "1951"];\n'
        "const warData = [0.0, 0.2];\n"
        'const teamsByYear = ["NYY", "NYY"];\n'
        "</script>"
    )
    arc = admin_index.extract_war_arc(_soup(html))
    assert arc == [
        {"year": "1950", "war": 0.0, "team": "NYY"},
        {"year": "1951", "war": 0.2, "team": "NYY"},
    ]


def test_extract_war_arc_missing():
    assert admin_index.extract_war_arc(_soup("<html></html>")) == []


def test_extract_war_arc_partial():
    html = "<script>" + 'const years = ["2001"];\n' + "</script>"
    assert admin_index.extract_war_arc(_soup(html)) == []
