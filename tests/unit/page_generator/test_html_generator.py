import pytest  # type: ignore
import json
from bs4 import BeautifulSoup  # type: ignore
import html_generator  # type: ignore

@pytest.fixture
def sample_player_data():
    return {
        "name": "Derek Jeter",
        "nickname": "The Captain",
        "facts": ["Hit a home run for his 3000th hit", "Won 5 World Series championships"],
        "followup_qa": [
            {"question": "How many Gold Gloves?", "answer": "5"}
        ],
        "career_totals": {
            "WAR": "71.3",
            "AB": "11195",
            "HR": "260"
        },
        "yearly_war": [
            {"year": "1996", "display_team": "NYY", "teams": ["NYY"], "war": 3.3}
        ]
    }

def test_build_detail_page_html(sample_player_data):
    date_str = "1999-05-15"
    formatted_date = "May 15, 1999"
    
    html_content = html_generator.build_detail_page_html(sample_player_data, date_str, formatted_date)
    assert html_content is not None
    assert type(html_content) == str
    
    # Parse with beautiful soup to ensure semantic HTML structure behaves properly
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Check title and header match proper date
    assert f"Derek Jeter \"The Captain\" Answer - {formatted_date}" in soup.title.string
    assert f"The answer for {formatted_date} is..." in soup.find("h1").string
    
    # Check name and nickname logic maps
    assert "Derek Jeter \"The Captain\"" in soup.find("h2").string
    
    # Check follow up logic
    followup_section = soup.find(id="followup-section")
    assert followup_section is not None
    assert "How many Gold Gloves?" in followup_section.text
    
    # Check Stats table populates correctly
    stats_container = soup.find(class_="stats-table-container")
    assert stats_container is not None
    assert "71.3" in stats_container.text
    assert "260" in stats_container.text

    # Check quiz-data exists and contains correct JSON with nickname
    quiz_data_div = soup.find(id="quiz-data")
    assert quiz_data_div is not None
    import json
    quiz_data = json.loads(quiz_data_div.string)
    assert quiz_data["answer"] == "Derek Jeter"
    assert quiz_data["nicknames"] == ["The Captain"]
    assert "Hit a home run for his 3000th hit" in quiz_data["hints"]


class TestAddNicknameToPage:
    """Tests for adding nicknames to existing puzzle pages."""

    def _create_page_with_quiz_data(self, tmp_path, date_str, quiz_data):
        """Helper to create a minimal HTML page with quiz-data."""
        page = tmp_path / f"{date_str}.html"
        page.write_text(
            f'<html><body>'
            f'<div id="quiz-data" style="display:none;">'
            f'{json.dumps(quiz_data)}'
            f'</div></body></html>'
        )
        return page

    def test_adds_nickname_to_page_with_nicknames_array(self, tmp_path):
        quiz_data = {"answer": "Derek Jeter", "nicknames": ["Captain"], "hints": ["Clue 1"]}
        self._create_page_with_quiz_data(tmp_path, "2025-01-01", quiz_data)

        result = html_generator.add_nickname_to_page(tmp_path, "2025-01-01", "Mr. November")

        assert result is True
        page = tmp_path / "2025-01-01.html"
        soup = BeautifulSoup(page.read_text(), "html.parser")
        updated = json.loads(soup.find(id="quiz-data").string)
        assert updated["nicknames"] == ["Captain", "Mr. November"]

    def test_adds_nickname_to_page_with_old_format(self, tmp_path):
        quiz_data = {"answer": "Derek Jeter", "nickname": "Captain", "hints": ["Clue 1"]}
        self._create_page_with_quiz_data(tmp_path, "2025-01-01", quiz_data)

        result = html_generator.add_nickname_to_page(tmp_path, "2025-01-01", "Mr. November")

        assert result is True
        page = tmp_path / "2025-01-01.html"
        soup = BeautifulSoup(page.read_text(), "html.parser")
        updated = json.loads(soup.find(id="quiz-data").string)
        assert updated["nicknames"] == ["Captain", "Mr. November"]
        assert "nickname" not in updated

    def test_rejects_duplicate_nickname(self, tmp_path):
        quiz_data = {"answer": "Derek Jeter", "nicknames": ["Captain"], "hints": ["Clue 1"]}
        self._create_page_with_quiz_data(tmp_path, "2025-01-01", quiz_data)

        result = html_generator.add_nickname_to_page(tmp_path, "2025-01-01", "Captain")

        assert result is False

    def test_returns_false_for_missing_page(self, tmp_path):
        result = html_generator.add_nickname_to_page(tmp_path, "2099-01-01", "Captain")

        assert result is False

    def test_adds_nickname_to_page_with_no_existing_nicknames(self, tmp_path):
        quiz_data = {"answer": "Derek Jeter", "nickname": "", "hints": ["Clue 1"]}
        self._create_page_with_quiz_data(tmp_path, "2025-01-01", quiz_data)

        result = html_generator.add_nickname_to_page(tmp_path, "2025-01-01", "Captain")

        assert result is True
        page = tmp_path / "2025-01-01.html"
        soup = BeautifulSoup(page.read_text(), "html.parser")
        updated = json.loads(soup.find(id="quiz-data").string)
        assert updated["nicknames"] == ["Captain"]
