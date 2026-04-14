import pytest
from bs4 import BeautifulSoup
import os
import json
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
    assert canonical_link["href"] == f"https://namethatyankeequiz.com/{date_str}"

def test_meta_description_in_detail_page(sample_player_data):
    date_str = "1999-05-15"
    formatted_date = "May 15, 1999"
    
    html_content = html_generator.build_detail_page_html(sample_player_data, date_str, formatted_date)
    soup = BeautifulSoup(html_content, "html.parser")
    
    meta_desc = soup.find("meta", attrs={"name": "description"})
    assert meta_desc is not None
    assert meta_desc["content"] == "The player revealed for this New York Yankees trivia puzzle is Derek Jeter."

def test_json_ld_in_detail_page(sample_player_data):
    date_str = "1999-05-15"
    formatted_date = "May 15, 1999"
    
    html_content = html_generator.build_detail_page_html(sample_player_data, date_str, formatted_date)
    soup = BeautifulSoup(html_content, "html.parser")
    
    script_tag = soup.find("script", type="application/ld+json")
    assert script_tag is not None
    
    data = json.loads(script_tag.string)
    assert data["@context"] == "https://schema.org"
    assert data["@type"] == "Article"
    assert data["headline"] == f"Name That Yankee Answer for {formatted_date}"
    assert "Derek Jeter" in data["description"]
    assert data["datePublished"] == date_str

def test_json_ld_with_quoted_name(sample_player_data):
    # Test that a name with quotes is properly escaped in JSON-LD
    sample_player_data["name"] = 'Babe "The Bambino" Ruth'
    date_str = "1923-04-18"
    formatted_date = "April 18, 1923"
    
    html_content = html_generator.build_detail_page_html(sample_player_data, date_str, formatted_date)
    soup = BeautifulSoup(html_content, "html.parser")
    
    script_tag = soup.find("script", type="application/ld+json")
    assert script_tag is not None
    
    # This should be valid JSON
    data = json.loads(script_tag.string)
    assert data["description"] == 'The player revealed for this New York Yankees trivia puzzle is Babe "The Bambino" Ruth.'

def test_robots_txt_existence():
    # Resolving path relative to the test file for robustness across environments
    robots_path = Path(__file__).resolve().parent.parent.parent.parent / "robots.txt"
    assert robots_path.exists()
    
    content = robots_path.read_text()
    assert "User-agent: *" in content
    assert "Sitemap: https://namethatyankeequiz.com/sitemap.xml" in content
