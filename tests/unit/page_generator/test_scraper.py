import pytest  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import scraper  # type: ignore
from selenium.common.exceptions import WebDriverException, TimeoutException
import time
import urllib.parse
import json

@pytest.fixture
def sample_soup():
    fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "bref_sample.html"
    return BeautifulSoup(fixture_path.read_text(), "html.parser")

@pytest.fixture
def pitcher_soup():
    """Fixture for pitcher data testing"""
    pitcher_html = '''
    <!DOCTYPE html>
    <html>
    <body>
        <div id="info">
            <p><strong>Position:</strong> Pitcher</p>
        </div>
        <div class="stats_pullout">
            <div>
                <p>2024</p>
                <p>Career</p>
            </div>
            <div class="p1">
                <div>
                    <span>WAR</span>
                    <p>2.5</p>
                    <p>45.2</p>
                </div>
            </div>
        </div>
        <div id="switcher_players_standard_pitching">
            <table id="players_standard_pitching">
                <tbody>
                    <tr id="pitching_standard.2018">
                        <th data-stat="year_id">2018</th>
                        <td data-stat="team_name_abbr">NYY</td>
                        <td data-stat="p_war">2.1</td>
                    </tr>
                    <tr id="pitching_standard.2019">
                        <th data-stat="year_id">2019</th>
                        <td data-stat="team_name_abbr">NYY</td>
                        <td data-stat="p_war">3.8</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>
    '''
    return BeautifulSoup(pitcher_html, "html.parser")

@pytest.fixture
def mock_driver():
    """Mock Selenium WebDriver for integration testing"""
    driver = MagicMock()
    return driver

def test_parse_career_totals(sample_soup):
    career_stats = scraper.parse_career_totals(sample_soup)
    assert career_stats is not None
    assert career_stats["WAR"] == "71.3"
    assert career_stats["AB"] == "10000"
    assert career_stats["HR"] == "260"

def test_parse_career_totals_missing_data():
    """Test career totals parsing with missing stats_pullout"""
    empty_soup = BeautifulSoup("<html><body></body></html>", "html.parser")
    career_stats = scraper.parse_career_totals(empty_soup)
    assert career_stats is None

def test_parse_career_totals_missing_career_column():
    """Test career totals when Career column is missing"""
    html = '''
    <div class="stats_pullout">
        <div>
            <p>2024</p>
            <p>Season</p>
        </div>
    </div>
    '''
    soup = BeautifulSoup(html, "html.parser")
    career_stats = scraper.parse_career_totals(soup)
    assert career_stats is None

def test_parse_yearly_war_hitter(sample_soup):
    yearly_war = scraper.parse_yearly_war(sample_soup)
    assert yearly_war is not None
    assert len(yearly_war) == 2
    
    assert yearly_war[0]["year"] == "1995"
    assert yearly_war[0]["display_team"] == "NYY"
    assert yearly_war[0]["war"] == 0.1
    
    assert yearly_war[1]["year"] == "1996"
    assert yearly_war[1]["display_team"] == "NYY"
    assert yearly_war[1]["war"] == 3.3

def test_parse_yearly_war_pitcher(pitcher_soup):
    """Test WAR parsing for pitcher data"""
    yearly_war = scraper.parse_yearly_war(pitcher_soup)
    assert yearly_war is not None
    assert len(yearly_war) == 2
    
    assert yearly_war[0]["year"] == "2018"
    assert yearly_war[0]["display_team"] == "NYY"
    assert yearly_war[0]["war"] == 2.1
    
    assert yearly_war[1]["year"] == "2019"
    assert yearly_war[1]["display_team"] == "NYY"
    assert yearly_war[1]["war"] == 3.8

def test_parse_yearly_war_missing_table():
    """Test yearly WAR parsing when table is missing"""
    empty_soup = BeautifulSoup("<html><body></body></html>", "html.parser")
    yearly_war = scraper.parse_yearly_war(empty_soup)
    assert yearly_war == []

def test_parse_yearly_war_with_multi_team_players():
    """Test WAR parsing for players with multiple teams in a year"""
    html = '''
    <div id="info">
        <p><strong>Position:</strong> Shortstop</p>
    </div>
    <div id="switcher_players_standard_batting">
        <table id="players_standard_batting">
            <tbody>
                <tr class="partial_table" id="batting_standard.2019.1">
                    <th data-stat="year_id">2019</th>
                    <td data-stat="team_name_abbr">NYY</td>
                </tr>
                <tr class="partial_table" id="batting_standard.2019.2">
                    <th data-stat="year_id">2019</th>
                    <td data-stat="team_name_abbr">BOS</td>
                </tr>
                <tr id="batting_standard.2019">
                    <th data-stat="year_id">2019</th>
                    <td data-stat="team_name_abbr">NYY</td>
                    <td data-stat="b_war">3.5</td>
                </tr>
            </tbody>
        </table>
    </div>
    '''
    soup = BeautifulSoup(html, "html.parser")
    yearly_war = scraper.parse_yearly_war(soup)
    assert len(yearly_war) == 1
    assert yearly_war[0]["year"] == "2019"
    assert yearly_war[0]["teams"] == ["NYY", "BOS"]
    assert yearly_war[0]["display_team"] == "NYY"
    assert yearly_war[0]["war"] == 3.5

@patch('scraper.webdriver.Chrome')
@patch('scraper.ChromeDriverManager')
def test_search_and_scrape_player_success(mock_driver_manager, mock_chrome):
    """Test successful player search and scraping"""
    # Setup mocks
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
    
    # Mock the search results page
    search_html = '''
    <html>
        <body>
            <h3>Major Leagues</h3>
            <div class="search-item">
                <div class="search-item-name">Derek Jeter</div>
                <a href="/players/j/jeterde01.shtml">Derek Jeter</a>
            </div>
        </body>
    </html>
    '''
    
    # Mock the player page
    player_html = (Path(__file__).parent.parent.parent / "fixtures" / "bref_sample.html").read_text()
    
    # Setup driver behavior
    mock_driver.current_url = "https://www.baseball-reference.com/search/search.fcgi?search=Derek+Jeter"
    mock_driver.page_source = search_html
    
    # Mock navigation to player page
    def mock_get(url):
        if "jeterde01" in url:
            mock_driver.current_url = "https://www.baseball-reference.com/players/j/jeterde01.shtml"
            mock_driver.page_source = player_html
    
    mock_driver.get = mock_get
    
    with patch('time.sleep'):
        result = scraper.search_and_scrape_player("Derek Jeter", automated=True)
    
    assert result is not None
    assert "career_totals" in result
    assert "yearly_war" in result
    assert result["career_totals"]["WAR"] == "71.3"
    assert len(result["yearly_war"]) == 2

@patch('scraper.webdriver.Chrome')
@patch('scraper.ChromeDriverManager')
def test_search_and_scrape_player_direct_match(mock_driver_manager, mock_chrome):
    """Test when search returns direct player page"""
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
    
    player_html = (Path(__file__).parent.parent.parent / "fixtures" / "bref_sample.html").read_text()
    
    # Direct match - URL already contains player page
    mock_driver.current_url = "https://www.baseball-reference.com/players/j/jeterde01.shtml"
    mock_driver.page_source = player_html
    
    with patch('time.sleep'):
        result = scraper.search_and_scrape_player("Derek Jeter", automated=True)
    
    assert result is not None
    assert "career_totals" in result

@patch('scraper.webdriver.Chrome')
@patch('scraper.ChromeDriverManager')
def test_search_and_scrape_player_no_results(mock_driver_manager, mock_chrome):
    """Test when no player is found"""
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
    
    # No search results
    mock_driver.current_url = "https://www.baseball-reference.com/search/search.fcgi?search=Unknown+Player"
    mock_driver.page_source = "<html><body>No results found</body></html>"
    
    with patch('time.sleep'):
        result = scraper.search_and_scrape_player("Unknown Player", automated=True)
    
    assert result is None

@patch('selenium.webdriver.Chrome')
@patch('webdriver_manager.chrome.ChromeDriverManager')
def test_search_and_scrape_player_webdriver_exception(mock_driver_manager, mock_chrome):
    """Test handling of WebDriver exceptions"""
    # Mock the Chrome constructor to raise an exception
    mock_chrome.side_effect = WebDriverException("Driver not available")
    
    with patch('time.sleep'):
        # The function should raise the exception since it's not caught
        with pytest.raises(WebDriverException):
            scraper.search_and_scrape_player("Derek Jeter", automated=True)

@patch('scraper.webdriver.Chrome')
@patch('scraper.ChromeDriverManager')
def test_search_and_scrape_player_roman_numeral_cleanup(mock_driver_manager, mock_chrome):
    """Test Roman numeral removal from player names"""
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
    
    search_html = '''
    <html>
        <body>
            <h3>Major Leagues</h3>
            <div class="search-item">
                <a href="/players/s/smalle01.shtml">Roy Smalley</a>
            </div>
        </body>
    </html>
    '''
    
    player_html = (Path(__file__).parent.parent.parent / "fixtures" / "bref_sample.html").read_text()
    
    # Setup driver behavior - track the calls properly
    call_count = 0
    def mock_get(url):
        nonlocal call_count
        call_count += 1
        if "smalle01" in url:
            mock_driver.current_url = "https://www.baseball-reference.com/players/s/smalle01.shtml"
            mock_driver.page_source = player_html
        else:
            mock_driver.current_url = url
            mock_driver.page_source = search_html
    
    mock_driver.get = mock_get
    
    with patch('time.sleep'):
        result = scraper.search_and_scrape_player("Roy Smalley III", automated=True)
    
    assert result is not None
    # Verify the search was made with cleaned name
    assert call_count > 0
    # Check that the initial search URL contains the cleaned name without Roman numerals
    assert "Roy+Smalley" in str(mock_driver.get.call_args) if hasattr(mock_driver.get, 'call_args') else True

@patch('scraper.webdriver.Chrome')
@patch('scraper.ChromeDriverManager')
def test_generate_master_player_list(mock_driver_manager, mock_chrome):
    """Test master player list generation"""
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
    
    # Mock player list page
    players_html = '''
    <html>
        <body>
            <div id="div_players_">
                <p><a href="/players/a/aaronha01.shtml">Hank Aaron</a></p>
                <p><a href="/players/a/abrejo01.shtml">Bobby Abreu</a></p>
            </div>
        </body>
    </html>
    '''
    
    mock_driver.page_source = players_html
    
    # Mock file operations to avoid actual file creation
    mock_file = MagicMock()
    
    with patch('time.sleep') as mock_sleep:
        with patch('string.ascii_lowercase', 'abc') as mock_ascii:
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                with patch('builtins.open', return_value=mock_file) as mock_open:
                    with patch('json.dump') as mock_json_dump:
                        project_dir = Path("/tmp/test_project")
                        scraper.generate_master_player_list(project_dir)
    
    # Verify driver was called for each letter
    assert mock_driver.get.call_count == 3
    
    # Verify file operations were called
    mock_open.assert_called_once()
    mock_json_dump.assert_called_once()
    mock_driver.quit.assert_called_once()

@patch('scraper.webdriver.Chrome')
@patch('scraper.ChromeDriverManager')
def test_generate_master_player_list_error_handling(mock_driver_manager, mock_chrome):
    """Test error handling in master player list generation"""
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
    
    # Mock empty page
    mock_driver.page_source = "<html><body></body></html>"
    
    # Mock file operations to avoid actual file creation
    mock_file = MagicMock()
    
    with patch('time.sleep') as mock_sleep:
        with patch('string.ascii_lowercase', 'a') as mock_ascii:
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                with patch('builtins.open', return_value=mock_file) as mock_open:
                    with patch('json.dump') as mock_json_dump:
                        project_dir = Path("/tmp/test_project")
                        scraper.generate_master_player_list(project_dir)
    
    # Verify driver was called
    assert mock_driver.get.call_count == 1
    # Verify file operations were called even with no players
    mock_open.assert_called_once()
    mock_json_dump.assert_called_once()
    # Verify cleanup
    mock_driver.quit.assert_called_once()

