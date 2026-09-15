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


def test_load_all_players(tmp_path):
    js = tmp_path / "all_players.js"
    js.write_text('const ALL_PLAYERS = ["David Aardsma", "Jos\\u00e9 Abreu", "Jim Abbott"];\n', encoding="utf-8")
    assert admin_index.load_all_players(js) == ["David Aardsma", "Jos\u00e9 Abreu", "Jim Abbott"]


def test_normalize_name():
    assert admin_index.normalize_name("Jos\u00e9 Abreu") == "jose abreu"
    assert admin_index.normalize_name("  BILLY MARTIN ") == "billy martin"


def test_build_pool_detects_used_duplicates_and_available(tmp_path):
    js = tmp_path / "all_players.js"
    js.write_text(
        'const ALL_PLAYERS = ["Billy Martin", "Mike Jackson", "Luis Severino", "Dusty Baker"];\n',
        encoding="utf-8",
    )
    players = admin_index.load_all_players(js)
    puzzles = [
        {"date": "2026-09-14", "name": "Billy Martin", "nicknames": ["Billy"], "hints": [], "followup_qa": [], "career_totals": {}, "teams": [], "years": [], "war_arc": [], "images": {"clue": True, "answer": True}, "flags": []},
        {"date": "2025-01-01", "name": "Billy Martin", "nicknames": [], "hints": [], "followup_qa": [], "career_totals": {}, "teams": [], "years": [], "war_arc": [], "images": {"clue": True, "answer": True}, "flags": []},
        {"date": "2026-01-01", "name": "Luis Severino", "nicknames": ["Sevy"], "hints": [], "followup_qa": [], "career_totals": {}, "teams": [], "years": [], "war_arc": [], "images": {"clue": True, "answer": True}, "flags": []},
    ]
    pool = admin_index.build_pool(players, puzzles)
    assert pool["used"] == [
        {"date": "2026-09-14", "name": "Billy Martin"},
        {"date": "2025-01-01", "name": "Billy Martin"},
        {"date": "2026-01-01", "name": "Luis Severino"},
    ]
    assert sorted(pool["used_names"]) == ["billy martin", "luis severino"]
    assert sorted(pool["used_aliases"]) == ["billy", "billy martin", "luis severino", "sevy"]
    assert pool["duplicates"] == [["Billy Martin", ["2026-09-14", "2025-01-01"]]]
    assert pool["available_count"] == 2
    assert sorted(pool["available"]) == ["Dusty Baker", "Mike Jackson"]
