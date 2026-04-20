# ABOUTME: Shared configuration constants for Name That Yankee E2E and integration tests.
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TEST_FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "www"
BASE_URL = "http://localhost:8001/"
DETAIL_PAGE_URL = f"{BASE_URL}2026-04-19"
QUIZ_URL = f"{BASE_URL}quiz.html"
ANALYTICS_URL = f"{BASE_URL}analytics.html"
