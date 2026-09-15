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


def load_all_players(js_path: Path) -> List[str]:
    """Parse ALL_PLAYERS from all_players.js."""
    if not js_path.exists():
        return []
    text = js_path.read_text(encoding="utf-8")
    m = re.search(r"const\s+ALL_PLAYERS\s*=\s*(\[.*?\]);", text, re.DOTALL)
    if not m:
        return []
    return json.loads(m.group(1))


def normalize_name(name: str) -> str:
    """Lowercase, strip diacritics, and trim for comparisons."""
    import unicodedata

    normalized = unicodedata.normalize("NFD", name or "")
    stripped = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return stripped.lower().strip()


def build_pool(players: List[str], puzzles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute used players, aliases, duplicates, and the available pool."""
    used = [{"date": p["date"], "name": p["name"]} for p in puzzles if p.get("name")]
    used_names = sorted({normalize_name(u["name"]) for u in used})

    aliases = set()
    for p in puzzles:
        aliases.add(normalize_name(p.get("name", "")))
        for nick in p.get("nicknames", []):
            aliases.add(normalize_name(nick))
    used_aliases = sorted(a for a in aliases if a)

    by_name: Dict[str, List[str]] = {}
    for u in used:
        by_name.setdefault(u["name"], []).append(u["date"])
    duplicates = [[name, dates] for name, dates in sorted(by_name.items()) if len(dates) > 1]

    available = [p for p in players if normalize_name(p) not in used_names]
    available.sort(key=normalize_name)
    return {
        "used": used,
        "used_names": used_names,
        "used_aliases": used_aliases,
        "available_count": len(available),
        "available": available,
        "duplicates": duplicates,
    }
