import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path
import time

# --- Test Configuration ---
# This points to your local index.html file.
# The `pathlib` library makes sure this works correctly on any OS.
BASE_URL = f"file://{Path(__file__).parent.resolve()}/index.html"
DETAIL_PAGE_URL = f"file://{Path(__file__).parent.resolve()}/2025-07-11.html"

# --- Test Setup (Fixture) ---
# By changing the scope to "session", this fixture will now run only
# once for the entire test run, making it much faster.
@pytest.fixture(scope="session")
def browser():
    """Initializes and tears down the Selenium WebDriver."""
    # This automatically downloads and manages the correct chromedriver for you
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.implicitly_wait(3) # Wait up to 3 seconds for elements to appear
    yield driver # This is where the test runs
    driver.quit() # This runs after all tests are finished


# --- Test Cases ---

def test_main_page_layout(browser):
    """Checks that the main page loads with the expected core elements."""
    print("Testing main page layout...")
    browser.get(BASE_URL)
    
    # Check for the main H1 title
    header_title = browser.find_element(By.TAG_NAME, 'h1').text
    assert "Name That Yankee Archives" in header_title, "Main page title is missing or incorrect."
    
    # Check if the search bar is present
    search_bar = browser.find_element(By.ID, 'search-bar')
    assert search_bar.is_displayed(), "Search bar is not visible on the main page."
    
    # Check that the gallery has items
    gallery_items = browser.find_elements(By.CLASS_NAME, 'gallery-container')
    assert len(gallery_items) > 0, "Gallery should have trivia cards on initial load."
    print("✅ Main page layout is correct.")


def test_detail_page_layout(browser):
    """Checks that a sample detail page has the correct layout."""
    print("\nTesting detail page layout...")
    browser.get(DETAIL_PAGE_URL)

    # Check for the detail page H1 title
    header_title = browser.find_element(By.TAG_NAME, 'h1').text
    assert "The Answer Is..." in header_title, "Detail page title is missing or incorrect."

    # Check for the back link
    back_link = browser.find_element(By.CLASS_NAME, 'back-link')
    assert back_link.is_displayed(), "Back link is not visible on the detail page."

    # Check for the two main columns
    player_profile = browser.find_element(By.CLASS_NAME, 'player-profile')
    original_card = browser.find_element(By.CLASS_NAME, 'original-card')
    assert player_profile.is_displayed(), "Player profile section is missing."
    assert original_card.is_displayed(), "Original clue card section is missing."
    print("✅ Detail page layout is correct.")


@pytest.mark.parametrize("search_term, expected_count", [
    ("july", 8),       # CORRECTED: Your file has 8 cards from July
    ("june", 4),       # Should find all 4 cards from June
    ("2025", 12),      # CORRECTED: Your file has 12 cards total from 2025
    ("july 9", 1),     # Should find the single card for July 9
    ("june 29", 1),    # Should find the single card for June 29
    ("july 5", 1),     # Should correctly find "July 5" without a comma
    ("foobar", 0)      # A search with no results
])
def test_search_functionality(browser, search_term, expected_count):
    """Tests the live search functionality with various queries."""
    print(f"\nTesting search for: '{search_term}'...")
    browser.get(BASE_URL)
    
    search_bar = browser.find_element(By.ID, 'search-bar')
    no_results_msg = browser.find_element(By.ID, 'no-results')
    
    # THE FIX: Clear the search bar before each new test run
    search_bar.clear()
    
    # Simulate typing into the search bar
    search_bar.send_keys(search_term)
    time.sleep(0.5) # Give the JavaScript a moment to filter

    # Get only the visible gallery items
    visible_items = [
        item for item in browser.find_elements(By.CLASS_NAME, 'gallery-container')
        if item.is_displayed()
    ]
    
    # Assert that the number of visible items is what we expect
    assert len(visible_items) == expected_count, f"Search for '{search_term}' should show {expected_count} items, but found {len(visible_items)}."
    
    # Assert that the "no results" message appears only when it should
    if expected_count == 0:
        assert no_results_msg.is_displayed(), "The 'no results' message should be visible for an empty search."
    else:
        assert not no_results_msg.is_displayed(), "The 'no results' message should be hidden when there are results."

    print(f"✅ Search for '{search_term}' passed.")

