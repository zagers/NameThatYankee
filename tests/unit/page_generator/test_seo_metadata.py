import pytest
from bs4 import BeautifulSoup
import os
from pathlib import Path
import html_generator

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

def test_canonical_tag_in_detail_page(sample_player_data):
    date_str = "1999-05-15"
    formatted_date = "May 15, 1999"
    
    html_content = html_generator.build_detail_page_html(sample_player_data, date_str, formatted_date)
    soup = BeautifulSoup(html_content, "html.parser")
    
    canonical_link = soup.find("link", rel="canonical")
    assert canonical_link is not None
    assert canonical_link["href"] == f"https://namethatyankeequiz.com/{date_str}.html"

def test_json_ld_in_detail_page(sample_player_data):
    date_str = "1999-05-15"
    formatted_date = "May 15, 1999"
    
    html_content = html_generator.build_detail_page_html(sample_player_data, date_str, formatted_date)
    soup = BeautifulSoup(html_content, "html.parser")
    
    script_tag = soup.find("script", type="application/ld+json")
    assert script_tag is not None
    
    import json
    data = json.loads(script_tag.string)
    assert data["@context"] == "https://schema.org"
    assert data["@type"] == "Article"
    assert data["headline"] == f"Name That Yankee Answer for {formatted_date}"
    assert "Derek Jeter" in data["description"]
    assert data["datePublished"] == date_str

def test_robots_txt_existence():
    # This assumes the file was created in the current working directory during the implementation
    robots_path = Path("robots.txt")
    assert robots_path.exists()
    
    content = robots_path.read_text()
    assert "User-agent: *" in content
    assert "Sitemap: https://namethatyankeequiz.com/sitemap.xml" in content
