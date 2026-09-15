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


def extract_followup_qa(soup) -> List[Dict[str, str]]:
    """Extract follow-up Q&A pairs from .followup-btn elements."""
    qa: List[Dict[str, str]] = []
    for btn in soup.select(".followup-btn"):
        answer = btn.get("data-answer", "")
        question = btn.get_text(strip=True)
        if question and answer:
            qa.append({"question": question, "answer": answer})
    return qa


def _find_js_array(text: str, name: str):
    """Return the parsed list for a JS `const <name> = [...]` in text, or None."""
    m = re.search(r"const\s+" + re.escape(name) + r"\s*=\s*(\[.*?\]);", text, re.DOTALL)
    return json.loads(m.group(1)) if m else None


def extract_war_arc(soup) -> List[Dict[str, Any]]:
    """Extract per-year {year, war, team} from the chart script consts."""
    text = "\n".join(s.get_text() for s in soup.find_all("script"))
    years = _find_js_array(text, "years")
    war = _find_js_array(text, "warData")
    teams = _find_js_array(text, "teamsByYear")
    if years is None or war is None or teams is None or not (len(years) == len(war) == len(teams)):
        return []
    return [
        {"year": str(y), "war": float(w), "team": str(t)}
        for y, w, t in zip(years, war, teams)
    ]
