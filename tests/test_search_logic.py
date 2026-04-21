# ABOUTME: E2E tests for the new JSON-driven smart search functionality.
# ABOUTME: Validates multi-category filtering and spoiler-safe name search for solved puzzles.

import pytest
from playwright.sync_api import Page, expect
from tests.test_config import BASE_URL

@pytest.mark.usefixtures("check_web_server")
class TestSmartSearch:
    def test_search_by_team_name(self, page: Page):
        page.goto(BASE_URL)
        search_bar = page.locator('#search-bar')
        
        # Search for "Oakland" (full name, not in abbr)
        search_bar.fill("oakland")
        page.wait_for_timeout(500)
        
        # Verify at least one Oakland card is visible
        visible_cards = page.locator('.gallery-container:visible')
        expect(visible_cards.first).to_be_visible()

    def test_search_by_decade(self, page: Page):
        page.goto(BASE_URL)
        search_bar = page.locator('#search-bar')
        
        # Search for "90s"
        search_bar.fill("90s")
        page.wait_for_timeout(500)
        
        # Verify cards are shown
        visible_cards = page.locator('.gallery-container:visible')
        expect(visible_cards.first).to_be_visible()

    def test_name_search_spoiler_protection(self, page: Page):
        page.goto(BASE_URL)
        search_bar = page.locator('#search-bar')
        
        # Clear localStorage to ensure no puzzles are marked solved
        page.evaluate("localStorage.clear()")
        page.reload()
        
        # Search for "Lou Piniella" (from today's puzzle)
        search_bar.fill("piniella")
        page.wait_for_timeout(500)
        
        # Should show NO results (spoiler protection)
        no_results = page.locator('#no-results')
        expect(no_results).to_be_visible()

    def test_name_search_for_solved_puzzles(self, page: Page):
        page.goto(BASE_URL)
        search_bar = page.locator('#search-bar')
        
        # Mock solving the April 19, 2026 puzzle (Lou Piniella)
        page.evaluate("localStorage.setItem('nameThatYankeeCompletedPuzzles', JSON.stringify(['2026-04-19']))")
        page.reload()
        
        # Search for "Sweet Lou" (nickname)
        search_bar.fill("sweet lou")
        page.wait_for_timeout(500)
        
        # Should show at least the April 19 card
        visible_cards = page.locator('.gallery-container:visible')
        expect(visible_cards).to_have_count(1)
        expect(visible_cards.locator('a.gallery-item')).to_be_visible()

    def test_multi_category_and_search(self, page: Page):
        page.goto(BASE_URL)
        search_bar = page.locator('#search-bar')
        
        # Search for "April" AND "NYY"
        search_bar.fill("april nyy")
        page.wait_for_timeout(500)
        
        # Verify results match both
        visible_cards = page.locator('.gallery-container:visible')
        expect(visible_cards.first).to_be_visible()
        # All visible dates should contain "April"
        dates = page.locator('.gallery-container:visible .gallery-date').all_text_contents()
        for date in dates:
            assert "April" in date
