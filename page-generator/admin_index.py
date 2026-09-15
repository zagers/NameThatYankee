# ABOUTME: Builds admin_data.json — the full puzzle catalog + player pool for the admin page.
import json
import re
import html
from pathlib import Path
from typing import Any, Dict, List


def extract_quiz_data(soup) -> Dict[str, Any]:
    """Extract answer + nicknames from the #quiz-data div (handles old/new formats)."""
    div = soup.find(id="quiz-data")
    if not div or not div.string:
        return {"answer": "", "nicknames": []}
    raw = json.loads(div.string)
    nicknames = raw.get("nicknames", [])
    if not nicknames:
        legacy = raw.get("nickname", "")
        nicknames = [legacy] if legacy else []
    return {"answer": raw.get("answer", ""), "nicknames": list(nicknames)}


def extract_search_data(soup) -> Dict[str, Any]:
    """Extract teams + years from the #search-data div."""
    div = soup.find(id="search-data")
    if not div or not div.string:
        return {"teams": [], "years": []}
    raw = json.loads(div.string)
    return {"teams": raw.get("teams", []), "years": raw.get("years", [])}


def extract_career_totals(soup) -> Dict[str, str]:
    """Extract the career totals stat table as {header: value}."""
    container = soup.select_one(".stats-table-container")
    table = container.find("table") if container else None
    if not table:
        return {}
    thead = table.find("thead")
    tbody = table.find("tbody")
    if not thead or not tbody:
        return {}
    headers = [th.get_text(strip=True) for th in thead.find_all("th")]
    values = [td.get_text(strip=True) for td in tbody.find_all("td")]
    return dict(zip(headers, values))
