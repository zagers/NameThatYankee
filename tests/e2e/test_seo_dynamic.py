import pytest
from playwright.sync_api import Page, expect
import re
from pathlib import Path

# Reuse the setup from test_yankee_site.py if possible, or just use the same port
# Since we are in the same repo, we can probably just run it.

BASE_URL = "http://localhost:8001"

@pytest.mark.usefixtures("check_web_server")
class TestDynamicSEO:
    def test_quiz_canonical_no_date(self, page: Page):
        page.goto(f"{BASE_URL}/quiz.html")
        
        # Should have canonical pointing to /quiz
        canonical = page.locator('link[rel="canonical"]')
        expect(canonical).to_have_attribute("href", "https://namethatyankeequiz.com/quiz")
        
        # Should NOT have noindex
        noindex = page.locator('meta[name="robots"][content="noindex"]')
        expect(noindex).to_have_count(0)

    def test_quiz_canonical_with_date(self, page: Page):
        test_date = "2025-07-23"
        page.goto(f"{BASE_URL}/quiz.html?date={test_date}")
        
        # Should have canonical pointing to the reveal page
        canonical = page.locator('link[rel="canonical"]')
        # In current broken state, it might have two canonicals or the wrong one.
        # We want it to be exactly one and point to the date.
        expect(canonical).to_have_attribute("href", f"https://namethatyankeequiz.com/{test_date}")
        
        # Should have noindex
        noindex = page.locator('meta[name="robots"][content="noindex"]')
        expect(noindex).to_be_attached()
