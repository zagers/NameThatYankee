import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path
import time

# --- Test Configuration ---
BASE_URL = f"file://{Path(__file__).parent.resolve()}/index.html"
# We still need a specific page to test the detail layout
DETAIL_PAGE_URL = f"file://{Path(__file__).parent.resolve()}/2025-07-11.html" 

# --- Test Setup (Fixture) ---
@pytest.fixture(scope="session")
def browser():
    """Initializes and tears down the Selenium WebDriver once per session."""
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.implicitly_wait(3)
    yield driver
    driver.quit()

# --- Helper Function for Dynamic Counting ---
def get_expected_count(browser, search_term):
    """
    Scans the page to dynamically determine how many items should match a search.
    """
    search_tokens = search_term.lower().strip().split(' ')
    all_items = browser.find_elements(By.CLASS_NAME, 'gallery-container')
    expected_count = 0
    
    for item in all_items:
        date_element = item.find_element(By.CLASS_NAME, 'gallery-date')
        date_text = date_element.text.lower().replace('trivia date:', '').replace(',', '').strip()
        date_tokens = date_text.split(' ')
        
        # Check if every search token is present in the card's date tokens
        if all(token in date_tokens for token in search_tokens):
            expected_count += 1
            
    return expected_count

# --- Test Cases ---

def test_main_page_layout(browser):
    """Checks that the main page loads with the expected core elements."""
    print("Testing main page layout...")
    browser.get(BASE_URL)
    assert "Name That Yankee Archives" in browser.find_element(By.TAG_NAME, 'h1').text
    assert browser.find_element(By.ID, 'search-bar').is_displayed()
    assert len(browser.find_elements(By.CLASS_NAME, 'gallery-container')) > 0
    print("✅ Main page layout is correct.")

def test_detail_page_layout(browser):
    """Checks that a sample detail page has the correct layout."""
    # First, ensure the detail page we want to test actually exists
    detail_path = Path(DETAIL_PAGE_URL.replace(f"file://", ""))
    if not detail_path.exists():
        pytest.skip(f"Skipping detail page test because {detail_path.name} does not exist.")

    print("\nTesting detail page layout...")
    browser.get(DETAIL_PAGE_URL)
    assert "The answer for" in browser.find_element(By.TAG_NAME, 'h1').text
    assert browser.find_element(By.CLASS_NAME, 'back-link').is_displayed()
    assert browser.find_element(By.CLASS_NAME, 'player-profile').is_displayed()
    assert browser.find_element(By.CLASS_NAME, 'original-card').is_displayed()
    print("✅ Detail page layout is correct.")

# The test now dynamically calculates the expected count for each search term
@pytest.mark.parametrize("search_term", [
    "july",
    "june",
    "2025",
    "july 9",
    "june 29",
    "july 5",
    "foobar" # This should always result in 0
])
def test_search_functionality(browser, search_term):
    """Tests the live search functionality with various queries."""
    print(f"\nTesting search for: '{search_term}'...")
    browser.get(BASE_URL)
    
    # Dynamically determine the correct number of results before searching
    expected_count = get_expected_count(browser, search_term)
    print(f"  (Dynamically determined that expected count is {expected_count})")
    
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
        assert no_results_msg.is_displayed(), "The 'no results' message should be visible."
    else:
        assert not no_results_msg.is_displayed(), "The 'no results' message should be hidden."

    print(f"✅ Search for '{search_term}' passed.")

