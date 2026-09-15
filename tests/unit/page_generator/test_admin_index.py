# ABOUTME: Unit tests for the admin_data.json generator.
# ABOUTME: Verifies extraction from puzzle detail pages and pool analysis.
import json
from pathlib import Path

from bs4 import BeautifulSoup  # type: ignore
import admin_index  # type: ignore


def _soup(detail_html: str) -> BeautifulSoup:
    return BeautifulSoup(detail_html, "html.parser")


def test_extract_quiz_data_names_array():
    html = '<div id="quiz-data" style="display:none;">{"answer": "Billy Martin", "nicknames": ["Billy", "Boys Club Basher"], "hints": ["h"]}</div>'
    data = admin_index.extract_quiz_data(_soup(html))
    assert data == {"answer": "Billy Martin", "nicknames": ["Billy", "Boys Club Basher"], "hints": ["h"]}


def test_extract_quiz_data_legacy_nickname_string():
    html = '<div id="quiz-data" style="display:none;">{"answer": "Lou Piniella", "nickname": "Sweet Lou", "hints": ["h"]}</div>'
    data = admin_index.extract_quiz_data(_soup(html))
    assert data == {"answer": "Lou Piniella", "nicknames": ["Sweet Lou"], "hints": ["h"]}


def test_extract_quiz_data_missing_div():
    assert admin_index.extract_quiz_data(_soup("<html></html>")) == {"answer": "", "nicknames": [], "hints": []}


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


def _make_detail_page(path: Path, quiz_html: str = "", name_in_h2: str = "Billy Martin \"Billy\"") -> Path:
    path.write_text(
        "<html><body>"
        f"<h2>{name_in_h2}</h2>"
        '<div class="stats-table-container"><div class="table-wrapper"><table>'
        "<thead><tr><th>WAR</th></tr></thead>"
        "<tbody><tr><td>2.9</td></tr></tbody>"
        "</table></div></div>"
        '<script>const years = ["1950"];\nconst warData = [0.0];\nconst teamsByYear = ["NYY"];</script>'
        f"{quiz_html}"
        "</body></html>",
        encoding="utf-8",
    )
    return path


def test_parse_detail_page_full(tmp_path):
    quiz = '<div id="quiz-data" style="display:none;">{"answer": "Billy Martin", "nicknames": ["Billy"], "hints": ["fiery infielder"]}</div>'
    q = '<div class="followup-item"><button class="followup-btn" data-answer="abc">Question?</button></div>'
    page = _make_detail_page(tmp_path / "2026-09-14.html", quiz + q)
    rec = admin_index.parse_detail_page(page, True, True)
    assert rec["date"] == "2026-09-14"
    assert rec["name"] == "Billy Martin"
    assert rec["nicknames"] == ["Billy"]
    assert rec["hints"] == ["fiery infielder"]
    assert rec["career_totals"] == {"WAR": "2.9"}
    assert rec["war_arc"] == [{"year": "1950", "war": 0.0, "team": "NYY"}]
    assert rec["followup_qa"] == [{"question": "Question?", "answer": "abc"}]
    assert rec["images"] == {"clue": True, "answer": True}
    assert rec["flags"] == []


def test_parse_detail_page_flags(tmp_path):
    page = _make_detail_page(tmp_path / "2025-01-01.html", name_in_h2="Unknown")
    rec = admin_index.parse_detail_page(page, False, False)
    assert "missing_clue_image" in rec["flags"]
    assert "missing_answer_image" in rec["flags"]
    assert "unknown_name" in rec["flags"]
    assert "no_nickname" in rec["flags"]
    assert "missing_stats" not in rec["flags"]


def _build_fixture_project(tmp_path, pages=("2026-09-14", "2026-08-07"), names=("Billy Martin", "Dusty Baker"), all_players=("Billy Martin", "Dusty Baker", "Luis Severino")):
    project = tmp_path / "project"
    images = project / "images"
    images.mkdir(parents=True)
    for date, name in zip(pages, names):
        (images / f"clue-{date}.webp").write_bytes(b"clue")
        (images / f"answer-{date}.webp").write_bytes(b"ans")
        detail = (
            "<html><body>"
            f'<h2>{name} "Nick"</h2>'
            '<div id="search-data" style="display:none;">{"teams": ["NYY"], "years": ["2001"]}</div>'
            f'<div id="quiz-data" style="display:none;">{{"answer": "{name}", "nicknames": ["Nick"], "hints": ["fact"]}}</div>'
            "</body></html>"
        )
        (project / f"{date}.html").write_text(detail, encoding="utf-8")
    (project / "all_players.js").write_text(
        "const ALL_PLAYERS = [" + ", ".join(json.dumps(p) for p in all_players) + "];\n",
        encoding="utf-8",
    )
    return project


def test_build_admin_data_writes_file(tmp_path):
    project = _build_fixture_project(tmp_path)
    data = admin_index.build_admin_data(project)
    assert data["generated"]
    assert [p["date"] for p in data["puzzles"]] == ["2026-08-07", "2026-09-14"]
    assert [p["name"] for p in data["puzzles"]] == ["Dusty Baker", "Billy Martin"]
    assert data["pool"]["available_count"] == 1
    assert data["pool"]["available"] == ["Luis Severino"]
    saved = json.loads((project / "admin_data.json").read_text(encoding="utf-8"))
    assert saved == data


def test_build_admin_data_missing_stats_flag(tmp_path):
    project = tmp_path / "project"
    (project / "images").mkdir(parents=True)
    (project / "images" / "clue-2025-01-01.webp").write_bytes(b"c")
    (project / "2025-01-01.html").write_text("<html><body><h2>X</h2></body></html>", encoding="utf-8")
    (project / "all_players.js").write_text("const ALL_PLAYERS = [];\n", encoding="utf-8")
    data = admin_index.build_admin_data(project)
    p = data["puzzles"][0]
    assert "missing_stats" in p["flags"]
    assert "missing_answer_image" in p["flags"]
