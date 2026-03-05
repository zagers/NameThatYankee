import pytest  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
from pathlib import Path
import scraper  # type: ignore

@pytest.fixture
def sample_soup():
    fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "bref_sample.html"
    return BeautifulSoup(fixture_path.read_text(), "html.parser")

def test_parse_career_totals(sample_soup):
    career_stats = scraper.parse_career_totals(sample_soup)
    assert career_stats is not None
    assert career_stats["WAR"] == "71.3"
    assert career_stats["AB"] == "10000"
    assert career_stats["HR"] == "260"

def test_parse_yearly_war(sample_soup):
    yearly_war = scraper.parse_yearly_war(sample_soup)
    assert yearly_war is not None
    assert len(yearly_war) == 2
    
    assert yearly_war[0]["year"] == "1995"
    assert yearly_war[0]["display_team"] == "NYY"
    assert yearly_war[0]["war"] == 0.1
    
    assert yearly_war[1]["year"] == "1996"
    assert yearly_war[1]["display_team"] == "NYY"
    assert yearly_war[1]["war"] == 3.3

