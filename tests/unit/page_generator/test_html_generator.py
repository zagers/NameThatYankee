import pytest  # type: ignore
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
    assert f"Answer for {date_str}" in soup.title.string
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

