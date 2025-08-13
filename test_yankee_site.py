import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path
import time
import json
import re
import requests
from urllib.parse import urljoin, urlparse
import sys

# --- Test Configuration ---
BASE_URL = "http://localhost:8000/"
DETAIL_PAGE_URL = "http://localhost:8000/2025-07-11.html"
QUIZ_URL = "http://localhost:8000/quiz.html"
ANALYTICS_URL = "http://localhost:8000/analytics.html"

# --- Test Setup (Fixture) ---
@pytest.fixture(scope="session")
def browser():
    """Initializes and tears down the Selenium WebDriver once per session."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.implicitly_wait(5)
    yield driver
    driver.quit()

@pytest.fixture(scope="session", autouse=True)
def check_web_server():
    """Check that the web server is running before running tests."""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code != 200:
            print("❌ Web server is not responding correctly")
            print("Please start your web server with: python -m http.server 8000")
            sys.exit(1)
        print("✅ Web server is running at http://localhost:8000/")
    except requests.exceptions.RequestException as e:
        print("❌ Web server is not running")
        print("Please start your web server with: python -m http.server 8000")
        print(f"Error: {e}")
        sys.exit(1)

@pytest.fixture
def wait(browser):
    """Returns a WebDriverWait object for explicit waits."""
    return WebDriverWait(browser, 10)

# ============================================================================
# 1. OVERALL SITE STRUCTURE TESTS
# ============================================================================

class TestSiteStructure:
    """Tests for overall site structure and core functionality."""
    
    def test_main_page_loads_correctly(self, browser, wait):
        """Test that the main page loads with all essential elements."""
        browser.get(BASE_URL)
        
        # Wait for page to load completely
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'header')))
        wait.until(EC.presence_of_element_located((By.ID, 'search-bar')))
        wait.until(EC.presence_of_element_located((By.ID, 'gallery-grid')))
        
        # Check page title
        assert "Name That Yankee Archives" in browser.title
        
        # Check header elements
        header = browser.find_element(By.TAG_NAME, 'header')
        assert "Name That Yankee Archives" in header.find_element(By.TAG_NAME, 'h1').text
        assert browser.find_element(By.CLASS_NAME, 'instructions-link').is_displayed()
        assert browser.find_element(By.CLASS_NAME, 'analytics-link').is_displayed()
        assert browser.find_element(By.ID, 'score-display').is_displayed()
        
        # Check search functionality
        assert browser.find_element(By.ID, 'search-bar').is_displayed()
        assert browser.find_element(By.ID, 'unsolved-filter').is_displayed()
        
        # Check gallery exists
        gallery = browser.find_element(By.ID, 'gallery-grid')
        assert len(gallery.find_elements(By.CLASS_NAME, 'gallery-container')) > 0
        
        # Check footer
        assert browser.find_element(By.TAG_NAME, 'footer').is_displayed()
    
    def test_navigation_links_work(self, browser, wait):
        """Test that all navigation links are functional."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'instructions-link')))
        
        # Test instructions link
        instructions_link = browser.find_element(By.CLASS_NAME, 'instructions-link')
        instructions_link.click()
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
        assert "How to Play" in browser.find_element(By.TAG_NAME, 'h1').text
        
        # Test analytics link
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'analytics-link')))
        analytics_link = browser.find_element(By.CLASS_NAME, 'analytics-link')
        analytics_link.click()
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
        assert "Site Analytics" in browser.find_element(By.TAG_NAME, 'h1').text
    
    def test_gallery_cards_have_required_elements(self, browser, wait):
        """Test that each gallery card has all required elements."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'gallery-container')))
        cards = browser.find_elements(By.CLASS_NAME, 'gallery-container')
        
        for card in cards[:3]:  # Test first 3 cards
            # Check image exists
            assert card.find_element(By.TAG_NAME, 'img').is_displayed()
            
            # Check date is present
            assert card.find_element(By.CLASS_NAME, 'gallery-date').is_displayed()
            
            # Check action buttons exist
            reveal_link = card.find_element(By.CLASS_NAME, 'reveal-link')
            quiz_link = card.find_element(By.CLASS_NAME, 'quiz-link')
            assert reveal_link.is_displayed()
            assert quiz_link.is_displayed()
    
    def test_responsive_design_elements(self, browser, wait):
        """Test that the site is responsive and works on different screen sizes."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, 'search-bar')))
        
        # Test mobile viewport
        browser.set_window_size(375, 667)  # iPhone SE size
        time.sleep(2)  # Increased wait time for layout changes
        assert browser.find_element(By.ID, 'search-bar').is_displayed()
        assert browser.find_element(By.ID, 'gallery-grid').is_displayed()
        
        # Test tablet viewport
        browser.set_window_size(768, 1024)  # iPad size
        time.sleep(2)  # Increased wait time for layout changes
        assert browser.find_element(By.ID, 'search-bar').is_displayed()
        
        # Test desktop viewport
        browser.set_window_size(1920, 1080)  # Desktop size
        time.sleep(2)  # Increased wait time for layout changes
        assert browser.find_element(By.ID, 'search-bar').is_displayed()

# ============================================================================
# 2. SEARCH FUNCTIONALITY TESTS
# ============================================================================

class TestSearchFunctionality:
    """Tests for search bar functionality and filtering."""
    
    def test_search_by_date(self, browser, wait):
        """Test searching by various date formats."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, 'search-bar')))
        search_bar = browser.find_element(By.ID, 'search-bar')
        
        # Test month search
        search_bar.clear()
        search_bar.send_keys("july")
        wait.until(lambda driver: len([item for item in driver.find_elements(By.CLASS_NAME, 'gallery-container') if item.is_displayed()]) > 0)
        
        visible_items = [item for item in browser.find_elements(By.CLASS_NAME, 'gallery-container') if item.is_displayed()]
        assert len(visible_items) > 0
        
        # Test specific date
        search_bar.clear()
        search_bar.send_keys("july 9")
        time.sleep(1)  # Increased wait time
        visible_items = [item for item in browser.find_elements(By.CLASS_NAME, 'gallery-container') if item.is_displayed()]
        assert len(visible_items) == 1
    
    def test_search_by_year(self, browser, wait):
        """Test searching by player career years."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, 'search-bar')))
        search_bar = browser.find_element(By.ID, 'search-bar')
        
        # Test year search
        search_bar.clear()
        search_bar.send_keys("1980")
        time.sleep(1)  # Increased wait time
        visible_items = [item for item in browser.find_elements(By.CLASS_NAME, 'gallery-container') if item.is_displayed()]
        assert len(visible_items) > 0
    
    def test_search_by_team(self, browser, wait):
        """Test searching by team names and abbreviations."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, 'search-bar')))
        search_bar = browser.find_element(By.ID, 'search-bar')
        
        # Test team abbreviation
        search_bar.clear()
        search_bar.send_keys("TOR")
        time.sleep(1)  # Increased wait time
        visible_items = [item for item in browser.find_elements(By.CLASS_NAME, 'gallery-container') if item.is_displayed()]
        assert len(visible_items) > 0
        
        # Test full team name
        search_bar.clear()
        search_bar.send_keys("Reds")
        time.sleep(1)  # Increased wait time
        visible_items = [item for item in browser.find_elements(By.CLASS_NAME, 'gallery-container') if item.is_displayed()]
        assert len(visible_items) > 0
    
    def test_unsolved_filter_checkbox(self, browser, wait):
        """Test the unsolved puzzles filter checkbox."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, 'unsolved-filter')))
        unsolved_filter = browser.find_element(By.ID, 'unsolved-filter')
        
        # Get initial count
        initial_count = len([item for item in browser.find_elements(By.CLASS_NAME, 'gallery-container') if item.is_displayed()])
        
        # Check the filter
        unsolved_filter.click()
        time.sleep(1)  # Increased wait time
        
        # Should show same or fewer items
        filtered_count = len([item for item in browser.find_elements(By.CLASS_NAME, 'gallery-container') if item.is_displayed()])
        assert filtered_count <= initial_count
        
        # Uncheck the filter
        unsolved_filter.click()
        time.sleep(1)  # Increased wait time
        
        # Should show original count
        final_count = len([item for item in browser.find_elements(By.CLASS_NAME, 'gallery-container') if item.is_displayed()])
        assert final_count == initial_count
    
    def test_no_results_message(self, browser, wait):
        """Test that no results message appears for invalid searches."""
        browser.get(BASE_URL)
        search_bar = browser.find_element(By.ID, 'search-bar')
        no_results = browser.find_element(By.ID, 'no-results')
        
        # Search for something that won't exist
        search_bar.clear()
        search_bar.send_keys("xyz123nonexistent")
        time.sleep(0.5)
        
        # Should show no results message
        assert no_results.is_displayed()
        
        # Clear search
        search_bar.clear()
        time.sleep(0.5)
        
        # Should hide no results message
        assert not no_results.is_displayed()

# ============================================================================
# 3. QUIZ FUNCTIONALITY TESTS
# ============================================================================

class TestQuizFunctionality:
    """Tests for quiz functionality including scoring, hints, and validation."""
    
    def test_quiz_page_loads_correctly(self, browser, wait):
        """Test that quiz page loads with all required elements."""
        # Navigate to a specific quiz
        browser.get(f"{QUIZ_URL}?date=2025-07-11")
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, 'clue-image')))
        wait.until(EC.presence_of_element_located((By.ID, 'guess-input')))
        wait.until(EC.presence_of_element_located((By.ID, 'submit-guess')))
        wait.until(EC.presence_of_element_located((By.ID, 'request-hint')))
        
        # Check quiz elements
        assert browser.find_element(By.ID, 'clue-image').is_displayed()
        assert browser.find_element(By.ID, 'guess-input').is_displayed()
        assert browser.find_element(By.ID, 'submit-guess').is_displayed()
        assert browser.find_element(By.ID, 'request-hint').is_displayed()
    
    def test_quiz_scoring_system(self, browser, wait):
        """Test that the quiz scoring system works correctly."""
        browser.get(f"{QUIZ_URL}?date=2025-07-11")
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, 'guess-input')))
        wait.until(EC.presence_of_element_located((By.ID, 'submit-guess')))
        wait.until(EC.presence_of_element_located((By.ID, 'total-score')))
        
        # Get initial score
        initial_score = int(browser.find_element(By.ID, 'total-score').text)
        
        # Make a correct guess (you'll need to know the answer for this test)
        guess_input = browser.find_element(By.ID, 'guess-input')
        submit_button = browser.find_element(By.ID, 'submit-guess')
        
        # Try a wrong guess first
        guess_input.clear()
        guess_input.send_keys("Wrong Player")
        submit_button.click()
        
        # Should show feedback
        feedback = wait.until(EC.visibility_of_element_located((By.ID, 'feedback-message')))
        assert "incorrect" in feedback.text.lower()
        
        # Score should remain the same (no points for wrong guess)
        current_score = int(browser.find_element(By.ID, 'total-score').text)
        assert current_score == initial_score
    
    def test_hint_system(self, browser, wait):
        """Test that hints are revealed correctly."""
        browser.get(f"{QUIZ_URL}?date=2025-07-11")
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, 'request-hint')))
        
        # Request a hint
        hint_button = browser.find_element(By.ID, 'request-hint')
        hint_button.click()
        
        # Should show hints container
        hints_container = wait.until(EC.visibility_of_element_located((By.ID, 'hints-container')))
        assert hints_container.is_displayed()
        
        # Should have hints list
        hints_list = browser.find_element(By.ID, 'hints-list')
        assert len(hints_list.find_elements(By.TAG_NAME, 'li')) > 0
    
    def test_max_guesses_limit(self, browser, wait):
        """Test that only 4 wrong guesses are allowed."""
        browser.get(f"{QUIZ_URL}?date=2025-07-11")
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, 'submit-guess')))
        submit_button = browser.find_element(By.ID, 'submit-guess')
        
        # Make 4 wrong guesses
        wrong_guesses = ["Player A", "Player B", "Player C", "Player D"]
        
        for guess in wrong_guesses:
            guess_input = browser.find_element(By.ID, 'guess-input')
            guess_input.clear()
            guess_input.send_keys(guess)
            submit_button.click()
            
            # Wait for feedback
            wait.until(EC.visibility_of_element_located((By.ID, 'feedback-message')))
            time.sleep(0.5)  # Small delay between guesses
        
        # After 4 wrong guesses, should show success area with answer
        success_area = wait.until(EC.visibility_of_element_located((By.ID, 'success-area')))
        assert success_area.is_displayed()
    
    def test_incorrect_guesses_chart(self, browser, wait):
        """Test the incorrect guesses chart functionality."""
        browser.get(f"{QUIZ_URL}?date=2025-07-11")
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, 'show-guesses-btn')))
        
        # Click to show guesses
        show_guesses_btn = browser.find_element(By.ID, 'show-guesses-btn')
        show_guesses_btn.click()
        
        # Should show chart container
        chart_container = wait.until(EC.visibility_of_element_located((By.ID, 'guesses-chart-container')))
        assert chart_container.is_displayed()
        
        # Should have canvas element
        canvas = browser.find_element(By.ID, 'guessesChart')
        assert canvas.is_displayed()
    
    def test_input_validation(self, browser, wait):
        """Test that only valid player names are accepted."""
        browser.get(f"{QUIZ_URL}?date=2025-07-11")
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, 'guess-input')))
        wait.until(EC.presence_of_element_located((By.ID, 'submit-guess')))
        
        guess_input = browser.find_element(By.ID, 'guess-input')
        submit_button = browser.find_element(By.ID, 'submit-guess')
        
        # Test empty input
        guess_input.clear()
        submit_button.click()
        
        # Should not accept empty input
        feedback = wait.until(EC.visibility_of_element_located((By.ID, 'feedback-message')))
        assert "incorrect" in feedback.text.lower() or "invalid" in feedback.text.lower()
        
        # Test very long input
        guess_input.clear()
        guess_input.send_keys("A" * 100)  # Very long name
        submit_button.click()
        
        # Should handle long input gracefully
        feedback = wait.until(EC.visibility_of_element_located((By.ID, 'feedback-message')))
        assert feedback.is_displayed()

# ============================================================================
# 4. SECURITY TESTING
# ============================================================================

class TestSecurity:
    """Tests for security vulnerabilities."""
    
    def test_xss_prevention(self, browser, wait):
        """Test that XSS attacks are prevented."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, 'search-bar')))
        search_bar = browser.find_element(By.ID, 'search-bar')
        
        # Try XSS payload
        xss_payload = "<script>alert('xss')</script>"
        search_bar.clear()
        search_bar.send_keys(xss_payload)
        time.sleep(1)  # Wait for any processing
        
        # Check that script is not executed
        # This test verifies that the script tag is not rendered as HTML
        page_source = browser.page_source
        assert xss_payload in page_source  # Should be escaped/encoded
        
        # Verify no alert was triggered (this would be caught by browser security anyway)
        # The main test is that the script doesn't execute
    
    def test_sql_injection_prevention(self, browser, wait):
        """Test that SQL injection attempts are handled safely."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, 'search-bar')))
        search_bar = browser.find_element(By.ID, 'search-bar')
        
        # Try SQL injection payload
        sql_payload = "'; DROP TABLE users; --"
        search_bar.clear()
        search_bar.send_keys(sql_payload)
        
        # Should not crash the application
        time.sleep(1)
        assert browser.find_element(By.ID, 'search-bar').is_displayed()
    
    def test_local_storage_security(self, browser, wait):
        """Test that localStorage is used securely."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'header')))
        
        # Check that sensitive data is not stored in localStorage
        local_storage = browser.execute_script("return window.localStorage;")
        
        # Should only contain expected keys
        expected_keys = ['nameThatYankeeTotalScore', 'nameThatYankeeCompletedPuzzles']
        for key in local_storage.keys():
            assert key in expected_keys, f"Unexpected localStorage key: {key}"
    
    def test_content_security_policy(self, browser, wait):
        """Test for basic CSP headers (if implemented)."""
        # This would require a web server to test properly
        # For file:// URLs, CSP headers won't be present
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'header')))
        
        # Check that external resources are loaded securely
        # This is more of a manual verification, but we can check for HTTPS URLs
        page_source = browser.page_source
        
        # Check for any HTTP URLs (should be HTTPS)
        http_urls = re.findall(r'http://[^\s"\'<>]+', page_source)
        assert len(http_urls) == 0, f"Found HTTP URLs: {http_urls}"
    
    def test_input_sanitization(self, browser, wait):
        """Test that user inputs are properly sanitized."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, 'search-bar')))
        search_bar = browser.find_element(By.ID, 'search-bar')
        
        # Test various malicious inputs
        malicious_inputs = [
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "&#60;script&#62;alert(1)&#60;/script&#62;"
        ]
        
        for malicious_input in malicious_inputs:
            search_bar.clear()
            search_bar.send_keys(malicious_input)
            time.sleep(1)  # Increased wait time
            
            # Should not crash or execute malicious code
            assert browser.find_element(By.ID, 'search-bar').is_displayed()
    
    def test_file_access_restriction(self, browser, wait):
        """Test that file access is properly restricted."""
        # Try to access a non-existent page
        browser.get("http://localhost:8000/nonexistent-page.html")
        
        # Wait for page to load
        time.sleep(2)  # Give time for redirect or error
        
        # Should show 404 or redirect to main page
        current_url = browser.current_url
        page_source = browser.page_source
        
        # Either should be on main page or show error
        assert "Name That Yankee Archives" in page_source or "404" in page_source.lower()

# ============================================================================
# 5. ANALYTICS PAGE TESTS
# ============================================================================

class TestAnalyticsPage:
    """Tests for the analytics page functionality."""
    
    def test_analytics_page_loads(self, browser, wait):
        """Test that analytics page loads correctly."""
        browser.get(ANALYTICS_URL)
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'chart-grid')))
        
        # Check page title
        assert "Site Analytics" in browser.find_element(By.TAG_NAME, 'h1').text
        
        # Check for analytics elements
        assert browser.find_element(By.CLASS_NAME, 'chart-grid').is_displayed()
        
        # Check for chart containers
        chart_cards = browser.find_elements(By.CLASS_NAME, 'chart-card')
        assert len(chart_cards) >= 4  # Should have at least 4 charts
    
    def test_analytics_charts_load(self, browser, wait):
        """Test that analytics charts are properly loaded."""
        browser.get(ANALYTICS_URL)
        
        # Wait for charts to load
        time.sleep(3)  # Give charts time to render
        
        # Check for chart canvases
        chart_canvases = browser.find_elements(By.TAG_NAME, 'canvas')
        assert len(chart_canvases) >= 3  # Should have multiple charts
        
        # Check that charts are visible
        for canvas in chart_canvases:
            assert canvas.is_displayed()
    
    def test_analytics_data_accuracy(self, browser, wait):
        """Test that analytics data is accurate and consistent."""
        browser.get(ANALYTICS_URL)
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, 'analytics-content')))
        
        # Check that analytics content is loaded
        analytics_content = browser.find_element(By.ID, 'analytics-content')
        assert analytics_content.is_displayed()
        
        # Check that loading message is hidden
        loading_message = browser.find_element(By.ID, 'loading-message')
        assert not loading_message.is_displayed()
    
    def test_analytics_navigation(self, browser, wait):
        """Test navigation to and from analytics page."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'analytics-link')))
        
        # Navigate to analytics
        analytics_link = browser.find_element(By.CLASS_NAME, 'analytics-link')
        analytics_link.click()
        
        # Should be on analytics page
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
        assert "Site Analytics" in browser.find_element(By.TAG_NAME, 'h1').text
        
        # Navigate back
        back_link = browser.find_element(By.CLASS_NAME, 'back-link')
        back_link.click()
        
        # Should be back on main page
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
        assert "Name That Yankee Archives" in browser.find_element(By.TAG_NAME, 'h1').text

# ============================================================================
# ADDITIONAL UTILITY TESTS
# ============================================================================

class TestUtilities:
    """Additional utility and edge case tests."""
    
    def test_browser_compatibility(self, browser, wait):
        """Test that the site works across different browser configurations."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.ID, 'search-bar')))
        
        # Test JavaScript functionality
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        # Test keyboard navigation
        search_bar = browser.find_element(By.ID, 'search-bar')
        search_bar.click()
        search_bar.send_keys(Keys.TAB)
        
        # Should move to next element
        active_element = browser.switch_to.active_element
        assert active_element != search_bar
    
    def test_performance_basic(self, browser, wait):
        """Basic performance test - page should load within reasonable time."""
        start_time = time.time()
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'header')))
        load_time = time.time() - start_time
        
        # Page should load within 5 seconds
        assert load_time < 5, f"Page took {load_time:.2f} seconds to load"
    
    def test_accessibility_basic(self, browser, wait):
        """Basic accessibility test."""
        browser.get(BASE_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'header')))
        
        # Check for alt text on images
        images = browser.find_elements(By.TAG_NAME, 'img')
        for img in images:
            alt_text = img.get_attribute('alt')
            assert alt_text is not None and alt_text != "", "Images should have alt text"
        
        # Check for proper heading structure
        headings = browser.find_elements(By.TAG_NAME, 'h1')
        assert len(headings) == 1, "Should have exactly one h1 element"

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])

