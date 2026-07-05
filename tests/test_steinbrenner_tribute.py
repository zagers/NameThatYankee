# ABOUTME: Playwright E2E tests for the George Steinbrenner tribute date.
# ABOUTME: Verifies autocomplete suggestions and the detail page tribute layout.
import pytest
from playwright.sync_api import Page, expect
import re
from tests.test_config import BASE_URL, QUIZ_URL

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
    page.goto(f"{QUIZ_URL}?date=2026-04-19")
    guess_input = page.locator("#guess-input")
    expect(guess_input).to_be_visible()
    guess_input.fill("George")
    page.wait_for_timeout(500)
    suggestions = page.locator("#suggestions-container")
    if suggestions.is_visible():
        suggestion_items = suggestions.locator(".suggestion-item").all_inner_texts()
        assert "George Steinbrenner" not in suggestion_items

def test_submit_nickname_guess_correct(page: Page):
    """Verify that entering 'The Boss' in the guess input submits correctly and transitions to completed state."""
    page.goto(BASE_URL)
    page.evaluate("window.localStorage.clear();")
    page.goto(f"{QUIZ_URL}?date=2026-07-04")
    
    guess_input = page.locator("#guess-input")
    expect(guess_input).to_be_visible()
    guess_input.fill("The Boss")
    guess_input.press("Enter")
    
    success_area = page.locator("#success-area")
    expect(success_area).to_be_visible()

def test_steinbrenner_detail_page_loads_and_has_tribute_layout(page: Page):
    """Verify that George Steinbrenner detail page loads and has tribute layout features."""
    page.goto(f"{BASE_URL}2026-07-04?reveal=true")
    page.wait_for_load_state("networkidle")
    
    # Check title and header
    expect(page).to_have_title(re.compile("George Steinbrenner"))
    expect(page.locator("h2")).to_contain_text("George Steinbrenner")
    
    # Check layout container
    tribute_layout = page.locator(".tribute-layout")
    expect(tribute_layout).to_be_visible()
    
    # Check photo
    photo = tribute_layout.locator(".player-photo img")
    expect(photo).to_be_visible()
    expect(photo).to_have_attribute("src", "images/answer-2026-07-04.webp")
    
    # Check stats
    stats = page.locator(".broadcast-stats")
    expect(stats).to_be_visible()
    expect(stats.locator(".stat-box").nth(0).locator(".count")).to_contain_text("7")
    expect(stats.locator(".stat-box").nth(0).locator(".label")).to_contain_text("WS Titles")
    expect(stats.locator(".stat-box").nth(1).locator(".count")).to_contain_text("11")
    expect(stats.locator(".stat-box").nth(1).locator(".label")).to_contain_text("A.L. Pennants")
    expect(stats.locator(".stat-box").nth(2).locator(".count")).to_contain_text(".566")
    expect(stats.locator(".stat-box").nth(2).locator(".label")).to_contain_text("Win Percentage")
    
    # Check timeline
    timeline = page.locator(".timeline-container")
    expect(timeline).to_be_visible()
    expect(timeline.locator("h3")).to_contain_text("Sports Ownership & Organizational Timeline")
    expect(timeline.locator(".timeline-item")).to_have_count(6)
    
    # Check followup section
    followup = page.locator("#followup-section")
    expect(followup).to_be_visible()
    
    buttons = followup.locator(".followup-btn")
    expect(buttons).to_have_count(3)
    
    # Click a button and verify answer is revealed
    first_btn = buttons.nth(0)
    first_answer = followup.locator(".followup-answer").nth(0)
    expect(first_answer).not_to_be_visible()
    first_btn.click()
    expect(first_answer).to_be_visible()
    expect(first_answer).to_contain_text("He led a syndicate that purchased the team")
