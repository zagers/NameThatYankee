# ABOUTME: E2E tests for dynamic SEO metadata injection on the quiz page.
# ABOUTME: Validates canonical tag redirection and robots noindex behavior for dated quizzes.
import pytest
from playwright.sync_api import Page, expect
import re
from pathlib import Path
from tests.test_config import BASE_URL

@pytest.mark.usefixtures("check_web_server")
class TestDynamicSEO:
    def test_quiz_canonical_no_date(self, page: Page):
        page.goto(f"{BASE_URL}/quiz.html")
        
        # Should have canonical pointing to /quiz
        canonical = page.locator('link[rel="canonical"]')
        expect(canonical).to_have_attribute("href", "https://namethatyankeequiz.com/quiz")
        
        # Should have noindex (we now static noindex all quiz pages)
        noindex = page.locator('meta[name="robots"]')
        expect(noindex).to_have_attribute("content", re.compile(r"noindex"))

    def test_quiz_canonical_with_date(self, page: Page):
        test_date = "2025-07-23"
        page.goto(f"{BASE_URL}/quiz.html?date={test_date}")
        
        # Should have canonical pointing to the reveal page
        canonical = page.locator('link[rel="canonical"]')
        # In current broken state, it might have two canonicals or the wrong one.
        # We want it to be exactly one and point to the date.
        expect(canonical).to_have_attribute("href", f"https://namethatyankeequiz.com/{test_date}")
        
        # Should have noindex
        noindex = page.locator('meta[name="robots"]')
        expect(noindex).to_have_attribute("content", re.compile(r"noindex"))
