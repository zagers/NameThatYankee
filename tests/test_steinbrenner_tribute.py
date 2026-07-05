# ABOUTME: Playwright E2E tests for the George Steinbrenner tribute date.
# ABOUTME: Verifies autocomplete Suggestions specifically on 2026-07-04.
import pytest
from playwright.sync_api import Page, expect
from tests.test_config import QUIZ_URL

def test_steinbrenner_autocomplete_on_tribute_date(page: Page):
    """Verify that George Steinbrenner appears in autocomplete for the tribute date 2026-07-04."""
    page.goto(f"{QUIZ_URL}?date=2026-07-04")
    guess_input = page.locator("#guess-input")
    expect(guess_input).to_be_visible()
    guess_input.fill("George")
    suggestions = page.locator("#suggestions-container")
    expect(suggestions).to_be_visible()
    suggestion_items = suggestions.locator(".suggestion-item")
    expect(suggestion_items).to_contain_text(["George Steinbrenner"])

def test_the_boss_autocomplete_on_tribute_date(page: Page):
    """Verify that The Boss appears in autocomplete for the tribute date 2026-07-04."""
    page.goto(f"{QUIZ_URL}?date=2026-07-04")
    guess_input = page.locator("#guess-input")
    expect(guess_input).to_be_visible()
    guess_input.fill("The B")
    suggestions = page.locator("#suggestions-container")
    expect(suggestions).to_be_visible()
    suggestion_items = suggestions.locator(".suggestion-item")
    expect(suggestion_items).to_contain_text(["The Boss"])

def test_steinbrenner_not_in_autocomplete_on_other_date(page: Page):
    """Verify that George Steinbrenner does NOT appear in autocomplete for other dates."""
    page.goto(f"{QUIZ_URL}?date=2026-07-03")
    guess_input = page.locator("#guess-input")
    expect(guess_input).to_be_visible()
    guess_input.fill("George")
    page.wait_for_timeout(500)
    suggestions = page.locator("#suggestions-container")
    if suggestions.is_visible():
        suggestion_items = suggestions.locator(".suggestion-item").all_inner_texts()
        assert "George Steinbrenner" not in suggestion_items
