import pytest  # type: ignore
from pathlib import Path
import stat_scrape  # type: ignore

@pytest.fixture
def sample_html_string():
    fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "bref_sample.html"
    return fixture_path.read_text()

def test_parse_stats_from_html(sample_html_string):
    career_stats = stat_scrape.parse_stats_from_html(sample_html_string)
    assert career_stats is not None
    assert career_stats["WAR"] == "71.3"
    assert career_stats["AB"] == "10000"
    assert career_stats["HR"] == "260"

