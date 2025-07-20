import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path
import time

# --- Test Configuration ---
TEST_DATA_DIR = Path(__file__).parent.resolve() / "test-data"
BASE_URL = f"file://{TEST_DATA_DIR}/index.html"
DETAIL_PAGE_URL = f"file://{TEST_DATA_DIR}/2025-07-11.html" 

# --- Test Setup (Fixture) ---
@pytest.fixture(scope="session")
def browser():
    """Initializes and tears down the Selenium WebDriver once per session."""
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.implicitly_wait(3)
    yield driver
    driver.quit()

# --- Test Cases ---

def test_main_page_layout(browser):
    """Checks that the main page loads with the expected core elements."""
    print("Testing main page layout...")
    browser.get(BASE_URL)
    assert "Name That Yankee Archives" in browser.find_element(By.TAG_NAME, 'h1').text
    assert browser.find_element(By.ID, 'search-bar').is_displayed()
    # Based on your screenshot, you have 18 detail pages.
    assert len(browser.find_elements(By.CLASS_NAME, 'gallery-container')) == 19
    print("✅ Main page layout is correct.")

@pytest.mark.parametrize("search_term, expected_count", [
    ("july", 13),      # Your screenshot shows 12 files for July
    ("june", 6),       # Your screenshot shows 6 files for June
    ("july 9", 1),     # Should find the single card for July 9
    ("29", 1),         # Should find the single card for June 29
    ("9", 1),    # Should find the single card for July 9
    ("08", 1),   # Should find the single card for July 8
    ("foobar", 0)      # A search with no results
])
def test_search_functionality_by_date(browser, search_term, expected_count):
    """Tests the live search functionality with various date queries."""
    print(f"\nTesting date search for: '{search_term}'...")
    browser.get(BASE_URL)
    
    search_bar = browser.find_element(By.ID, 'search-bar')
    no_results_msg = browser.find_element(By.ID, 'no-results')
    
    search_bar.clear()
    search_bar.send_keys(search_term)
    time.sleep(0.5)

    visible_items = [
        item for item in browser.find_elements(By.CLASS_NAME, 'gallery-container')
        if item.is_displayed()
    ]
    
    assert len(visible_items) == expected_count, f"Search for '{search_term}' should show {expected_count} items, but found {len(visible_items)}."
    
    if expected_count == 0:
        assert no_results_msg.is_displayed()
    else:
        assert not no_results_msg.is_displayed()

    print(f"✅ Date search for '{search_term}' passed.")

@pytest.mark.parametrize("search_term, expected_count", [
    ("1980", 3), 
    ("2000", 5)
])
def test_search_functionality_by_year(browser, search_term, expected_count):
    """Tests that searching for a year correctly filters the cards. Should fail until implemented."""
    print(f"\nTesting year search for: '{search_term}'...")
    browser.get(BASE_URL)
    
    search_bar = browser.find_element(By.ID, 'search-bar')
    search_bar.clear()
    search_bar.send_keys(search_term)
    time.sleep(0.5)

    visible_items = [item for item in browser.find_elements(By.CLASS_NAME, 'gallery-container') if item.is_displayed()]
    
    # This assertion will fail until the feature is implemented, which is what we want for TDD.
    assert len(visible_items) == expected_count, f"Search for '{search_term}' should show {expected_count} items, but found {len(visible_items)}."
    print(f"✅ Year search for '{search_term}' passed.")


@pytest.mark.parametrize("search_term, expected_count", [
    ("Yankees", 19), 
    ("NYM", 2), 
    ("Reds", 3)
])
def test_search_functionality_by_team(browser, search_term, expected_count):
    """Tests that searching for a team name or abbreviation works. Should fail until implemented."""
    print(f"\nTesting team search for: '{search_term}'...")
    browser.get(BASE_URL)
    
    search_bar = browser.find_element(By.ID, 'search-bar')
    search_bar.clear()
    search_bar.send_keys(search_term)
    time.sleep(0.5)

    visible_items = [item for item in browser.find_elements(By.CLASS_NAME, 'gallery-container') if item.is_displayed()]
    
    # This assertion will fail until the feature is implemented.
    assert len(visible_items) == expected_count, f"Search for '{search_term}' should show {expected_count} items, but found {len(visible_items)}."
    print(f"✅ Team search for '{search_term}' passed.")

