import pytest
from playwright.sync_api import Page, expect
import re
from tests.test_config import QUIZ_URL

def test_john_sterling_autocomplete_on_tribute_date(page: Page):
    """Verify that John Sterling appears in autocomplete for the tribute date 2026-05-04."""
    # Navigate to the quiz page for the specific date
    page.goto(f"{QUIZ_URL}?date=2026-05-04")
    
    # Wait for the input to be ready
    guess_input = page.locator("#guess-input")
    expect(guess_input).to_be_visible()
    
    # Type "Jo" to trigger autocomplete
    guess_input.fill("Jo")
    
    # Check for "John Sterling" in the suggestions
    suggestions = page.locator("#suggestions-container")
    expect(suggestions).to_be_visible()
    
    suggestion_items = suggestions.locator(".suggestion-item")
    expect(suggestion_items).to_contain_text(["John Sterling"])

def test_john_sterling_not_in_autocomplete_on_other_date(page: Page):
    """Verify that John Sterling does NOT appear in autocomplete for other dates."""
    # Navigate to the quiz page for a different date
    page.goto(f"{QUIZ_URL}?date=2026-04-19")
    
    # Wait for the input to be ready
    guess_input = page.locator("#guess-input")
    expect(guess_input).to_be_visible()
    
    # Type "Jo" to trigger autocomplete
    guess_input.fill("Jo")
    
    # Wait a bit for potential suggestions to load
    page.wait_for_timeout(500)
    
    # Check that "John Sterling" is NOT in the suggestions
    suggestions = page.locator("#suggestions-container")
    if suggestions.is_visible():
        suggestion_items = suggestions.locator(".suggestion-item").all_inner_texts()
        assert "John Sterling" not in suggestion_items
