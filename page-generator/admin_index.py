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
