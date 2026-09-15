# Admin Puzzle Browser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a hidden, passphrase-gated static admin page (`admin.html`) with name/nickname search, full puzzle details, stats, and player-pool analysis, backed by a generated `admin_data.json`.

**Architecture:** A Python generator (`page-generator/admin_index.py`) parses existing puzzle detail pages + `all_players.js` and writes `admin_data.json`. A static `admin.html` + `js/admin.js` fetch it once and power search/detail/stats/pool views client-side. Pure matching logic lives in `js/adminSearch.js` so it is unit-testable without a DOM.

**Tech Stack:** Python 3.12, BeautifulSoup, pytest; JavaScript (ESM), vitest, jsdom.

**Spec:** `docs/superpowers/specs/2026-09-15-admin-page-design.md`

## Global Constraints

- Audit data stays separate: `admin_index.py` MUST NOT read `FACT_AUDIT_REPORT.md`.
- `admin.html` must include `noindex,nofollow` robots meta.
- `robots.txt` must `Disallow: /admin` and `Disallow: /admin_data.json`.
- Sitemap (`deploy.yml` `exclude-paths`) must exclude `admin.html` and `admin_data.json`.
- No changes to puzzle pages, `stats_summary.json`, `index.html`, or quiz/analytics behavior.
- All new code follows the repo's ABOUTME header comment convention (1–2 `// ABOUTME:` or `# ABOUTME:` lines at top).
- Use `normalizeText` semantics from `js/quizEngine.js` for JS normalization (NFD, strip diacritics, lowercase, trim).

---

### Task 1: Extractor — quiz-data + search-data divs

**Files:**
- Create: `page-generator/admin_index.py`
- Test: `tests/unit/page_generator/test_admin_index.py`

**Interfaces:**
- Produces: `extract_quiz_data(soup) -> dict` → `{"answer": str, "nicknames": list[str]}` (handles `nicknames` array and legacy `nickname` string)
- Produces: `extract_search_data(soup) -> dict` → `{"teams": list[str], "years": list[str]}` (empty lists if missing)

- [ ] **Step 1: Write the failing test**

Create `tests/unit/page_generator/test_admin_index.py`:

```python
# ABOUTME: Unit tests for the admin_data.json generator.
# ABOUTME: Verifies extraction from puzzle detail pages and pool analysis.
import json
import sys
from pathlib import Path

PAGE_GEN = str(Path(__file__).resolve().parents[2] / "page-generator")
if PAGE_GEN not in sys.path:
    sys.path.insert(0, PAGE_GEN)

from bs4 import BeautifulSoup  # type: ignore
import admin_index  # type: ignore


def _soup(detail_html: str) -> BeautifulSoup:
    return BeautifulSoup(detail_html, "html.parser")


def test_extract_quiz_data_names_array():
    html = '<div id="quiz-data" style="display:none;">{"answer": "Billy Martin", "nicknames": ["Billy", "Boys Club Basher"], "hints": ["h"]}</div>'
    data = admin_index.extract_quiz_data(_soup(html))
    assert data == {"answer": "Billy Martin", "nicknames": ["Billy", "Boys Club Basher"]}


def test_extract_quiz_data_legacy_nickname_string():
    html = '<div id="quiz-data" style="display:none;">{"answer": "Lou Piniella", "nickname": "Sweet Lou", "hints": ["h"]}</div>'
    data = admin_index.extract_quiz_data(_soup(html))
    assert data == {"answer": "Lou Piniella", "nicknames": ["Sweet Lou"]}


def test_extract_quiz_data_missing_div():
    assert admin_index.extract_quiz_data(_soup("<html></html>")) == {"answer": "", "nicknames": []}


def test_extract_search_data():
    html = '<div id="search-data" style="display:none;">{"teams": ["NYY", "DET"], "years": ["1950", "1951"]}</div>'
    data = admin_index.extract_search_data(_soup(html))
    assert data == {"teams": ["NYY", "DET"], "years": ["1950", "1951"]}


def test_extract_search_data_missing_div():
    assert admin_index.extract_search_data(_soup("<html></html>")) == {"teams": [], "years": []}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v` (fall back to `python3 -m pytest`)
Expected: FAIL with `ModuleNotFoundError: admin_index`

- [ ] **Step 3: Write minimal implementation**

Create `page-generator/admin_index.py`:

```python
# ABOUTME: Builds admin_data.json - the full puzzle catalog + player pool for the admin page.
import json
import re
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add page-generator/admin_index.py tests/unit/page_generator/test_admin_index.py
git commit -m "feat(admin): add quiz-data and search-data extractors"
```

---

### Task 2: Extractor — career totals table

**Files:**
- Modify: `page-generator/admin_index.py`
- Test: `tests/unit/page_generator/test_admin_index.py`

**Interfaces:**
- Produces: `extract_career_totals(soup) -> dict` → `{"WAR": "2.9", "AB": "3419", ...}` (empty dict if no `.stats-table-container`)

- [ ] **Step 1: Write the failing test** (append to test file)

```python
def test_extract_career_totals():
    html = (
        '<div class="stats-table-container"><div class="table-wrapper"><table>'
        "<thead><tr><th>WAR</th><th>AB</th><th>HR</th></tr></thead>"
        "<tbody><tr><td>2.9</td><td>3419</td><td>64</td></tr></tbody>"
        "</table></div></div>"
    )
    data = admin_index.extract_career_totals(_soup(html))
    assert data == {"WAR": "2.9", "AB": "3419", "HR": "64"}


def test_extract_career_totals_missing():
    assert admin_index.extract_career_totals(_soup("<html></html>")) == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: FAIL with `AttributeError: module 'admin_index' has no attribute 'extract_career_totals'`

- [ ] **Step 3: Write minimal implementation**

Append to `admin_index.py`:

```python
def extract_career_totals(soup) -> Dict[str, str]:
    """Extract the career totals stat table as {header: value}."""
    container = soup.select_one(".stats-table-container").find("table") if soup.select_one(".stats-table-container") else None
    if not container:
        return {}
    thead = container.find("thead")
    tbody = container.find("tbody")
    if not thead or not tbody:
        return {}
    headers = [th.get_text(strip=True) for th in thead.find_all("th")]
    values = [td.get_text(strip=True) for td in tbody.find_all("td")]
    return dict(zip(headers, values))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add page-generator/admin_index.py tests/unit/page_generator/test_admin_index.py
git commit -m "feat(admin): add career totals extractor"
```

---

### Task 3: Extractor — follow-up Q&A buttons

**Files:**
- Modify: `page-generator/admin_index.py`
- Test: `tests/unit/page_generator/test_admin_index.py`

**Interfaces:**
- Produces: `extract_followup_qa(soup) -> list[dict]` → `[{"question": str, "answer": str}, ...]` (empty list if none)

- [ ] **Step 1: Write the failing test** (append)

```python
def test_extract_followup_qa():
    html = (
        '<div class="followup-item">'
        '<button class="followup-btn" data-answer="Pine tar removed the homer.">1983 pine tar?</button>'
        '<div class="followup-answer" style="display:none;"></div></div>'
        '<div class="followup-item">'
        '<button class="followup-btn" data-answer="Fractured orbital bone.">1960 altercation?</button>'
        '<div class="followup-answer" style="display:none;"></div></div>'
    )
    qa = admin_index.extract_followup_qa(_soup(html))
    assert qa == [
        {"question": "1983 pine tar?", "answer": "Pine tar removed the homer."},
        {"question": "1960 altercation?", "answer": "Fractured orbital bone."},
    ]


def test_extract_followup_qa_none():
    assert admin_index.extract_followup_qa(_soup("<html></html>")) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: FAIL with `AttributeError: ... 'extract_followup_qa'`

- [ ] **Step 3: Write minimal implementation**

Append to `admin_index.py`:

```python
def extract_followup_qa(soup) -> List[Dict[str, str]]:
    """Extract follow-up Q&A pairs from .followup-btn elements."""
    qa: List[Dict[str, str]] = []
    for btn in soup.select(".followup-btn"):
        answer = btn.get("data-answer", "")
        question = btn.get_text(strip=True)
        if question and answer:
            qa.append({"question": question, "answer": answer})
    return qa
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: 8 PASS

- [ ] **Step 5: Commit**

```bash
git add page-generator/admin_index.py tests/unit/page_generator/test_admin_index.py
git commit -m "feat(admin): add follow-up QA extractor"
```

---

### Task 4: Extractor — WAR arc from chart script

**Files:**
- Modify: `page-generator/admin_index.py`
- Test: `tests/unit/page_generator/test_admin_index.py`

**Interfaces:**
- Produces: `extract_war_arc(soup) -> list[dict]` → `[{"year": "1950", "war": 0.0, "team": "NYY"}, ...]` (empty list if no chart)

- [ ] **Step 1: Write the failing test** (append)

```python
def test_extract_war_arc():
    html = (
        "<script>\n"
        'const years = ["1950", "1951"];\n'
        "const warData = [0.0, 0.2];\n"
        'const teamsByYear = ["NYY", "NYY"];\n'
        "</script>"
    )
    arc = admin_index.extract_war_arc(_soup(html))
    assert arc == [
        {"year": "1950", "war": 0.0, "team": "NYY"},
        {"year": "1951", "war": 0.2, "team": "NYY"},
    ]


def test_extract_war_arc_missing():
    assert admin_index.extract_war_arc(_soup("<html></html>")) == []


def test_extract_war_arc_partial():
    html = "<script>" + 'const years = ["2001"];\n' + "</script>"
    assert admin_index.extract_war_arc(_soup(html)) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: FAIL with `AttributeError: ... 'extract_war_arc'`

- [ ] **Step 3: Write minimal implementation**

Append to `admin_index.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: 11 PASS

- [ ] **Step 5: Commit**

```bash
git add page-generator/admin_index.py tests/unit/page_generator/test_admin_index.py
git commit -m "feat(admin): add WAR arc extractor"
```

---

### Task 5: Pool analysis (used / duplicates / available)

**Files:**
- Modify: `page-generator/admin_index.py`
- Test: `tests/unit/page_generator/test_admin_index.py`

**Interfaces:**
- Produces: `load_all_players(js_path: Path) -> list[str]`
- Produces: `normalize_name(name: str) -> str`
- Produces: `build_pool(players: list[str], puzzles: list[dict]) -> dict`
  → `{"used": [{"date": str, "name": str}], "used_names": list[str], "used_aliases": list[str], "available_count": int, "available": list[str], "duplicates": list[list]}`

- [ ] **Step 1: Write the failing test** (append)

```python
def test_load_all_players(tmp_path):
    js = tmp_path / "all_players.js"
    js.write_text('const ALL_PLAYERS = ["David Aardsma", "Jos\\u00e9 Abreu", "Jim Abbott"];\n', encoding="utf-8")
    assert admin_index.load_all_players(js) == ["David Aardsma", "Jos\u00e9 Abreu", "Jim Abbott"]


def test_normalize_name():
    assert admin_index.normalize_name("Jos\u00e9 Abreu") == "jose abreu"
    assert admin_index.normalize_name("  BILLY MARTIN ") == "billy martin"


def test_build_pool_detects_used_duplicates_and_available(tmp_path):
    js = tmp_path / "all_players.js"
    js.write_text(
        'const ALL_PLAYERS = ["Billy Martin", "Mike Jackson", "Luis Severino", "Dusty Baker"];\n',
        encoding="utf-8",
    )
    players = admin_index.load_all_players(js)
    puzzles = [
        {"date": "2026-09-14", "name": "Billy Martin", "nicknames": ["Billy"], "hints": [], "followup_qa": [], "career_totals": {}, "teams": [], "years": [], "war_arc": [], "images": {"clue": True, "answer": True}, "flags": []},
        {"date": "2025-01-01", "name": "Billy Martin", "nicknames": [], "hints": [], "followup_qa": [], "career_totals": {}, "teams": [], "years": [], "war_arc": [], "images": {"clue": True, "answer": True}, "flags": []},
        {"date": "2026-01-01", "name": "Luis Severino", "nicknames": ["Sevy"], "hints": [], "followup_qa": [], "career_totals": {}, "teams": [], "years": [], "war_arc": [], "images": {"clue": True, "answer": True}, "flags": []},
    ]
    pool = admin_index.build_pool(players, puzzles)
    assert pool["used"] == [
        {"date": "2026-09-14", "name": "Billy Martin"},
        {"date": "2025-01-01", "name": "Billy Martin"},
        {"date": "2026-01-01", "name": "Luis Severino"},
    ]
    assert sorted(pool["used_names"]) == ["billy martin", "luis severino"]
    assert sorted(pool["used_aliases"]) == ["billy", "billy martin", "luis severino", "sevy"]
    assert pool["duplicates"] == [["Billy Martin", ["2026-09-14", "2025-01-01"]]]
    assert pool["available_count"] == 2
    assert sorted(pool["available"]) == ["Dusty Baker", "Mike Jackson"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: FAIL with import errors for the new functions

- [ ] **Step 3: Write minimal implementation**

Append to `admin_index.py`:

```python
def load_all_players(js_path: Path) -> List[str]:
    """Parse ALL_PLAYERS from all_players.js."""
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: 14 PASS

- [ ] **Step 5: Commit**

```bash
git add page-generator/admin_index.py tests/unit/page_generator/test_admin_index.py
git commit -m "feat(admin): add player pool analysis"
```

---

### Task 6: Orchestrator — parse a puzzle page into a record

**Files:**
- Modify: `page-generator/admin_index.py`
- Test: `tests/unit/page_generator/test_admin_index.py`

**Interfaces:**
- Produces: `parse_detail_page(path: Path, has_clue_img: bool, has_answer_img: bool) -> dict` — full puzzle record (schema per spec §3)
- Flag rules: `no_nickname` when no nicknames; `missing_clue_image`/`missing_answer_image`; `missing_stats` when `career_totals == {}`; `unknown_name` when name == "Unknown"

- [ ] **Step 1: Write the failing test** (append)

```python
def _make_detail_page(path: Path, quiz_html: str = "", name_in_h2: str = "Billy Martin \"Billy\"") -> Path:
    path.write_text(
        "<html><body>"
        f"<h2>{name_in_h2}</h2>"
        '<div class="stats-table-container"><div class="table-wrapper"><table><thead><tr><th>WAR</th></tr></thead><tbody><tr><td>2.9</td></tr></tbody></table></div></div>'
        '<script>const years = ["1950"];\nconst warData = [0.0];\nconst teamsByYear = ["NYY"];</script>'
        f'{quiz_html}'
        "</body></html>",
        encoding="utf-8",
    )
    return path


def test_parse_detail_page_full(tmp_path):
    quiz = '<div id="quiz-data" style="display:none;">{"answer": "Billy Martin", "nicknames": ["Billy"], "hints": ["fiery infielder"]}</div>'
    q = '<div class="followup-item"><button class="followup-btn" data-answer="abc">Question?</button></div>'
    page = _make_detail_page(tmp_path / "2026-09-14.html", quiz + q)
    rec = admin_index.parse_detail_page(page, True, False)
    assert rec["date"] == "2026-09-14"
    assert rec["name"] == "Billy Martin"
    assert rec["nicknames"] == ["Billy"]
    assert rec["hints"] == ["fiery infielder"]
    assert rec["career_totals"] == {"WAR": "2.9"}
    assert rec["war_arc"] == [{"year": "1950", "war": 0.0, "team": "NYY"}]
    assert rec["followup_qa"] == [{"question": "Question?", "answer": "abc"}]
    assert rec["images"] == {"clue": True, "answer": False}
    assert rec["flags"] == []  # nickname present, stats present


def test_parse_detail_page_flags(tmp_path):
    page = _make_detail_page(tmp_path / "2025-01-01.html", name_in_h2="Unknown")
    rec = admin_index.parse_detail_page(page, False, False)
    assert "missing_clue_image" in rec["flags"]
    assert "missing_answer_image" in rec["flags"]
    assert "unknown_name" in rec["flags"]
    assert "no_nickname" in rec["flags"]
    assert "missing_stats" not in rec["flags"]  # stats table present in helper
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: FAIL with `AttributeError: ... 'parse_detail_page'`

- [ ] **Step 3: Write minimal implementation**

Append to `admin_index.py` (import `html` at top):

```python
def _parse_name_from_h2(soup) -> str:
    """Extract plain player name from the h2, which is 'Name \"Nickname\"' or 'Name'."""
    h2 = soup.find("h2")
    if not h2:
        return ""
    full = h2.get_text(strip=True)
    # Name format is 'Name "Nickname"'; escape any HTML entities unescaped by get_text
    full = html.unescape(full)
    if '"' in full:
        return full.split('"')[0].strip()
    return full


def parse_detail_page(path: Path, has_clue_img: bool, has_answer_img: bool) -> Dict[str, Any]:
    """Parse a single puzzle detail page into a full admin_data record."""
    soup = None
    if path.exists():
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    quiz = extract_quiz_data(soup) if soup else {"answer": "", "nicknames": []}
    search = extract_search_data(soup) if soup else {"teams": [], "years": []}
    name = quiz["answer"] or _parse_name_from_h2(soup) if soup else ""

    flags = []
    if not quiz["nicknames"]:
        flags.append("no_nickname")
    if not has_clue_img:
        flags.append("missing_clue_image")
    if not has_answer_img:
        flags.append("missing_answer_image")
    career_totals = extract_career_totals(soup) if soup else {}
    if not career_totals:
        flags.append("missing_stats")
    if name == "Unknown":
        flags.append("unknown_name")

    return {
        "date": path.stem,
        "name": name,
        "nicknames": quiz["nicknames"],
        "hints": quiz.get("hints", []),
        "followup_qa": extract_followup_qa(soup) if soup else [],
        "career_totals": career_totals,
        "teams": search["teams"],
        "years": search["years"],
        "war_arc": extract_war_arc(soup) if soup else [],
        "images": {"clue": has_clue_img, "answer": has_answer_img},
        "flags": flags,
    }
```

Add `import html` to the imports at the top of `admin_index.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: 16 PASS

- [ ] **Step 5: Commit**

```bash
git add page-generator/admin_index.py tests/unit/page_generator/test_admin_index.py
git commit -m "feat(admin): add puzzle page parser"
```

---

### Task 7: Orchestrator — build_admin_data (scan dir → write JSON)

**Files:**
- Modify: `page-generator/admin_index.py`
- Test: `tests/unit/page_generator/test_admin_index.py`

**Interfaces:**
- Produces: `build_admin_data(project_dir: Path) -> dict` — scans `images/clue-*.webp`, parses each `{date}.html`, builds `{"generated", "puzzles", "pool"}`, writes `project_dir/admin_data.json`, returns the dict.
- Produces: `run_build(project_dir: Path) -> Path` — thin CLI wrapper that calls `build_admin_data` and prints sizes (used by `main.py`).

- [ ] **Step 1: Write the failing test** (append)

```python
def _build_fixture_project(tmp_path, pages=("2026-09-14", "2026-08-07"), names=("Billy Martin", "Dusty Baker"), all_players=("Billy Martin", "Dusty Baker", "Luis Severino")):
    project = tmp_path / "project"
    images = project / "images"
    images.mkdir(parents=True)
    (project / "clue- placeholder").write_text("")  # no-op unused
    for date, name in zip(pages, names):
        (images / f"clue-{date}.webp").write_bytes(b"clue")
        (images / f"answer-{date}.webp").write_bytes(b"ans")
        detail = (
            "<html><body>"
            f'<h2>{name} "Nick"</h2>'
            '<div id="search-data" style="display:none;">{"teams": ["NYY"], "years": ["2001"]}</div>'
            f'<div id="quiz-data" style="display:none;">{{"answer": "{name}", "nicknames": ["Nick"], "hints": ["fact"]}}</div>'
            "</body></html>"
        )
        (project / f"{date}.html").write_text(detail, encoding="utf-8")
    (project / "all_players.js").write_text(
        "const ALL_PLAYERS = [" + ", ".join(json.dumps(p) for p in all_players) + "];\n",
        encoding="utf-8",
    )
    return project


def test_build_admin_data_writes_file(tmp_path):
    project = _build_fixture_project(tmp_path)
    data = admin_index.build_admin_data(project)
    assert data["generated"]
    assert [p["name"] for p in data["puzzles"]] == ["Billy Martin", "Dusty Baker"]
    assert [p["date"] for p in data["puzzles"]] == ["2026-08-07", "2026-09-14"]  # sorted ascending
    assert data["pool"]["available_count"] == 1
    assert data["pool"]["available"] == ["Luis Severino"]
    saved = json.loads((project / "admin_data.json").read_text(encoding="utf-8"))
    assert saved == data


def test_build_admin_data_missing_stats_flag(tmp_path):
    project = tmp_path / "project"
    (project / "images").mkdir(parents=True)
    (project / "images" / "clue-2025-01-01.webp").write_bytes(b"c")
    (project / "2025-01-01.html").write_text("<html><body><h2>X</h2></body></html>", encoding="utf-8")
    (project / "all_players.js").write_text("const ALL_PLAYERS = [];\n", encoding="utf-8")
    data = admin_index.build_admin_data(project)
    p = data["puzzles"][0]
    assert "missing_stats" in p["flags"]
    assert "missing_answer_image" in p["flags"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: FAIL with `AttributeError: ... 'build_admin_data'`

- [ ] **Step 3: Write minimal implementation**

Append to `admin_index.py`:

```python
_CLUE_RE = re.compile(r"clue-(\d{4}-\d{2}-\d{2})\.webp")


def build_admin_data(project_dir: Path) -> Dict[str, Any]:
    """Scan clue images, parse detail pages, compute pool, write admin_data.json."""
    images_dir = project_dir / "images"
    clue_files = sorted(images_dir.glob("clue-*.webp")) if images_dir.exists() else []
    puzzles = []
    for clue_path in clue_files:
        m = _CLUE_RE.search(clue_path.name)
        if not m:
            continue
        date_str = m.group(1)
        detail_path = project_dir / f"{date_str}.html"
        if not detail_path.exists():
            continue
        has_answer_img = (project_dir / "images" / f"answer-{date_str}.webp").exists()
        puzzles.append(parse_detail_page(detail_path, True, has_answer_img))

    puzzles.sort(key=lambda p: p["date"])
    players = load_all_players(project_dir / "all_players.js")
    pool = build_pool(players, puzzles)
    data = {"generated": str(Path(__file__).name), "puzzles": puzzles, "pool": pool}
    (project_dir / "admin_data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def run_build(project_dir: Path) -> Path:
    """Build admin_data.json for a project dir and report the result."""
    data = build_admin_data(project_dir)
    out = project_dir / "admin_data.json"
    print(f"  📊 admin_data.json written with {len(data['puzzles'])} puzzles.")
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py -v`
Expected: 18 PASS

- [ ] **Step 5: Commit**

```bash
git add page-generator/admin_index.py tests/unit/page_generator/test_admin_index.py
git commit -m "feat(admin): add build_admin_data orchestrator"
```

---

### Task 8: Wire into main.py rebuild path

**Files:**
- Modify: `page-generator/main.py:532,709-710,914`
- Test: `tests/unit/page_generator/test_admin_index.py` (integration-style)

**Interfaces:**
- Consumes: `admin_index.run_build(project_dir) -> Path`

- [ ] **Step 1: Write the failing test** (append)

```python
def test_rebuild_index_mode_also_builds_admin_data(tmp_path):
    import subprocess
    import os
    import sys

    project = _build_fixture_project(tmp_path, pages=("2026-09-14",), names=("Billy Martin",))
    (project / "index.html").write_text(
        '<html><body><footer class="copyright"></footer><div id="score-display"><svg class="chevron-icon"></svg></div><div class="gallery"></div></body></html>',
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "page-generator")
    main_py = str(Path(__file__).resolve().parents[2] / "page-generator" / "main.py")
    result = subprocess.run(
        [sys.executable, main_py, "--rebuild-index"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project),
        stdin=subprocess.DEVNULL,  # force no-input fallback to "."
    )
    assert result.returncode == 0, result.stderr
    assert (project / "admin_data.json").exists()
    data = json.loads((project / "admin_data.json").read_text(encoding="utf-8"))
    assert len(data["puzzles"]) >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/unit/page_generator/test_admin_index.py::test_rebuild_index_mode_also_builds_admin_data -v`
Expected: FAIL — `admin_data.json` missing after rebuild.

- [ ] **Step 3: Add helper import and hook calls in main.py**

At the top of `main.py`, confirm `import admin_index` (add if missing, alongside `import html_generator`).

Replace each existing `html_generator.rebuild_index_page(project_dir)` with:

```python
    html_generator.rebuild_index_page(project_dir)
    admin_index.run_build(project_dir)
```

at the 3 call sites: line 532, the `--rebuild-index` block (lines 708–711), and line 914.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/page_generator/test_admin_index.py -v` and `.venv/bin/pytest tests/unit/ -v`
Expected: all PASS; no regression in existing unit tests.

- [ ] **Step 5: Commit**

```bash
git add page-generator/main.py tests/unit/page_generator/test_admin_index.py
git commit -m "feat(admin): build admin_data.json on every index rebuild"
```

---

### Task 9: JS search module (adminSearch.js)

**Files:**
- Create: `js/adminSearch.js`
- Test: `tests/js/adminSearch.test.js`

**Interfaces:**
- Produces: `normalizeAdminText(text) -> string`
- Produces: `levenshtein(a, b) -> number`
- Produces: `searchPuzzles(puzzles, query, fields = ["name", "nicknames"]) -> [{puzzle, score}]` sorted best-first.
  - Tokenized AND semantics over the given fields.
  - Each token matches a field word by exact `==`, or by `startsWith`, or by substring; fuzzy fallback via levenshtein ≤ 1 for tokens of length ≥ 4 (compare against field words after normalize).
  - Scoring: exact word hit = 10, prefix = 6, substring = 4, fuzzy = 2 per token, summed. Non-matching puzzles excluded.

- [ ] **Step 1: Write the failing test**

Create `tests/js/adminSearch.test.js`:

```javascript
// ABOUTME: Unit tests for the admin search matching module.
import { describe, it, expect } from 'vitest';
import { normalizeAdminText, levenshtein, searchPuzzles } from '../../js/adminSearch.js';

const puzzles = [
    { date: '2026-08-07', name: 'Dusty Baker', nicknames: [], hints: [] },
    { date: '2026-09-14', name: 'Billy Martin', nicknames: ['Billy'], hints: ['fiery infielder'] },
    { date: '2025-05-10', name: 'Jim Abbott', nicknames: [], hints: [] },
];

describe('normalizeAdminText', () => {
    it('lowercases, strips accents, trims', () => {
        expect(normalizeAdminText('  José ABREU  ')).toBe('jose abreu');
    });
});

describe('levenshtein', () => {
    it('computes edit distance', () => {
        expect(levenshtein('baker', 'baker')).toBe(0);
        expect(levenshtein('baker', 'bakre')).toBe(2);
        expect(levenshtein('martin', 'mrtin')).toBe(1);
    });
});

describe('searchPuzzles', () => {
    it('returns empty for empty query', () => {
        expect(searchPuzzles(puzzles, '')).toEqual([]);
    });

    it('finds by substring of last name', () => {
        const results = searchPuzzles(puzzles, 'martin');
        expect(results.map(r => r.puzzle.name)).toEqual(['Billy Martin']);
    });

    it('finds by nickname alias', () => {
        const results = searchPuzzles(puzzles, 'billy');
        expect(results.map(r => r.puzzle.name)).toEqual(['Billy Martin']);
    });

    it('finds by fuzzy typo', () => {
        const results = searchPuzzles(puzzles, 'mrtin');
        expect(results.map(r => r.puzzle.name)).toEqual(['Billy Martin']);
    });

    it('reports nothing for unknown nickname "Home Run Baker"', () => {
        const results = searchPuzzles(puzzles, 'home run baker');
        expect(results).toEqual([]);
    });

    it('respects required fields parameter (name only)', () => {
        const results = searchPuzzles(puzzles, 'sevy', ['name']);
        expect(results).toEqual([]);
    });

    it('ranks exact > prefix > substring', () => {
        const exact = searchPuzzles(puzzles, 'belly');
        // 'belly' fuzzy-matches Billy (nickname) but site uses last-name search; use a clear case:
        const results = searchPuzzles(puzzles, 'abb');
        expect(results.length).toBeGreaterThan(0);
        expect(results[0].puzzle.name).toBe('Jim Abbott');
    });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/js/adminSearch.test.js`
Expected: FAIL — module not found.

- [ ] **Step 3: Write minimal implementation**

Create `js/adminSearch.js`:

```javascript
// ABOUTME: Pure, DOM-free search and matching helpers for the admin page.
// ABOUTME: Powers name/nickname/fuzzy searches across the puzzle catalog.

export function normalizeAdminText(text) {
    if (!text) return '';
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
}

export function levenshtein(a, b) {
    const m = a.length;
    const n = b.length;
    if (m === 0) return n;
    if (n === 0) return m;
    const prev = Array.from({ length: n + 1 }, (_, i) => i);
    for (let i = 1; i <= m; i++) {
        let cur = [i];
        for (let j = 1; j <= n; j++) {
            const cost = a[i - 1] === b[j - 1] ? 0 : 1;
            cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
        }
        prev = cur;
    }
    return prev[n];
}

function bestWordScore(token, fieldWords) {
    let best = 0;
    for (const word of fieldWords) {
        if (!word) continue;
        if (word === token) best = Math.max(best, 10);
        else if (word.startsWith(token)) best = Math.max(best, 6);
        else if (word.includes(token)) best = Math.max(best, 4);
        else if (token.length >= 4 && levenshtein(token, word) <= 1) best = Math.max(best, 2);
    }
    return best;
}

export function searchPuzzles(puzzles, query, fields = ['name', 'nicknames']) {
    const tokens = normalizeAdminText(query).split(/\s+/).filter(Boolean);
    if (tokens.length === 0) return [];

    const results = [];
    for (const puzzle of puzzles) {
        const fieldWords = [];
        for (const field of fields) {
            const value = Array.isArray(puzzle[field]) ? puzzle[field].join(' ') : String(puzzle[field] || '');
            for (const word of normalizeAdminText(value).split(/\s+/)) {
                if (word) fieldWords.push(word);
            }
        }
        let tokenScore = 0;
        let matched = true;
        for (const token of tokens) {
            const score = bestWordScore(token, fieldWords);
            if (score === 0) { matched = false; break; }
            tokenScore += score;
        }
        if (matched) results.push({ puzzle, score: tokenScore });
    }
    results.sort((a, b) => b.score - a.score);
    return results;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/js/adminSearch.test.js`
Expected: PASS (all 9 cases)

- [ ] **Step 5: Commit**

```bash
git add js/adminSearch.js tests/js/adminSearch.test.js
git commit -m "feat(admin): add search matching module"
```

---

### Task 10: Admin UI (admin.html + js/admin.js)

**Files:**
- Create: `admin.html`
- Create: `js/admin.js`
- Test: `tests/js/adminSearch.test.js` already covers the search module; DOM-level test optional.

**Interfaces:**
- Consumes: `searchPuzzles` from `js/adminSearch.js` (ESM import).
- Reads: `admin_data.json`.
- Session gate: `sessionStorage.getItem('nta_admin_unlocked') === '1'`.

- [ ] **Step 1: The static admin page**

Create `admin.html` with:
- `noindex,nofollow` meta, canonical omitted, title "Name That Yankee — Admin".
- Inline CSS (self-contained; no dependency on public `style.css`).
- Structure: `<div id="gate">` (passphrase form) and `<div id="app" hidden>` containing search bar, filter selects, results grid, detail `<details>` panel, stats panel, pool panel, export buttons.
- `<script type="module" src="js/admin.js"></script>`.

- [ ] **Step 2: Write the UI module** — `js/admin.js`:

```javascript
// ABOUTME: Admin UI - search, inspect, and analyze puzzles from admin_data.json.
// ABOUTME: Gated by a client-side passphrase; spoiler content, not for end users.
import { searchPuzzles } from './adminSearch.js';

const ADMIN_PASS_HASH = '<SHA256_OF_PASSPHRASE>'; // placeholder replaced in Step 4
const UNLOCK_KEY = 'nta_admin_unlocked';

async function sha256(text) {
    const data = new TextEncoder().encode(text);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('');
}

function isUnlocked() {
    return sessionStorage.getItem(UNLOCK_KEY) === '1';
}

function requireUnlocked() {
    if (isUnlocked()) return;
    document.getElementById('app').hidden = true;
    document.getElementById('gate').hidden = false;
}

async function init() {
    const adminData = await (await fetch('admin_data.json?v=' + Date.now())).json();
    const puzzles = adminData.puzzles;

    document.getElementById('gate').querySelector('form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('passphrase').value;
        if ((await sha256(input)) === ADMIN_PASS_HASH) {
            sessionStorage.setItem(UNLOCK_KEY, '1');
            document.getElementById('gate').hidden = true;
            document.getElementById('app').hidden = false;
        } else {
            document.getElementById('gate-error').textContent = 'Incorrect passphrase.';
        }
    });

    requireUnlocked();
    if (!isUnlocked()) return;

    renderStats(adminData);
    renderPool(adminData.pool);
    renderAll(puzzles);

    document.getElementById('search-bar').addEventListener('input', (e) => {
        renderSearchResults(puzzles, e.target.value);
    });
}

function renderAll(puzzles) { renderSearchResults(puzzles, ''); }

function renderSearchResults(puzzles, query) {
    const grid = document.getElementById('results');
    const results = searchPuzzles(puzzles, query);
    if (results.length === 0) { grid.innerHTML = '<p class="empty">No puzzle found for this search.</p>'; return; }
    grid.innerHTML = results.map(({ puzzle, score }) => `
        <div class="card" data-date="${puzzle.date}">
            <div class="card-head"><strong>${escapeHtml(puzzle.name)}</strong> <span class="date">${puzzle.date}</span></div>
            <div class="meta">${escapeHtml(puzzle.teams.join(', ')) || '—'} · ${puzzle.years.length} seasons · score ${score}</div>
            <details><summary>Details</summary>${puzzleDetailsHtml(puzzle)}</details>
        </div>`).join('');
}

function puzzleDetailsHtml(puzzle) {
    const nicknames = puzzle.nicknames.length ? `<li>Nicknames: ${escapeHtml(puzzle.nicknames.join(', '))}</li>` : '';
    const hints = (puzzle.hints || []).map(h => `<li>${escapeHtml(h)}</li>`).join('');
    const qa = (puzzle.followup_qa || []).map(p => `<li><b>Q:</b> ${escapeHtml(p.question)}<br><b>A:</b> ${escapeHtml(p.answer)}</li>`).join('');
    const stats = Object.entries(puzzle.career_totals || {}).map(([k, v]) => `<span class="stat"><b>${k}</b> ${escapeHtml(v)}</span>`).join(' ');
    const flags = (puzzle.flags || []).map(f => `<span class="flag">${f}</span>`).join(' ');
    return `<ul>
        ${nicknames}
        ${hints}
        ${qa ? '<li><b>Follow-ups:</b></li>' + qa : ''}
        <li><b>Career totals:</b> ${stats || '—'}</li>
        <li><b>WAR arc:</b> ${puzzle.war_arc.map(y => `${escapeHtml(y.year)} ${y.war}`).join(' · ') || '—'}</li>
        <li><a href="${puzzle.date}.html" target="_blank">Answer page</a> · <a href="quiz?date=${puzzle.date}" target="_blank">Quiz</a></li>
        <li>${flags}</li>
    </ul>`;
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function renderStats(adminData) {
    const puzzles = adminData.puzzles;
    const byYear = {};
    puzzles.forEach(p => { const y = p.date.slice(0, 4); byYear[y] = (byYear[y] || 0) + 1; });
    const noNick = puzzles.filter(p => p.flags.includes('no_nickname')).length;
    const missingAssets = puzzles.filter(p => p.flags.some(f => f.startsWith('missing_'))).length;
    document.getElementById('stats').innerHTML = `
        <p>Total puzzles: <b>${puzzles.length}</b></p>
        <p>By year: ${Object.entries(byYear).sort().map(([y, c]) => `${y} (${c})`).join(', ')}</p>
        <p>Missing nicknames: <b>${noNick}</b></p>
        <p>Missing assets: <b>${missingAssets}</b></p>
        <p>Duplicates: <b>${adminData.pool.duplicates.length}</b></p>`;
}

function renderPool(pool) {
    const list = pool.duplicates.map(d => `<li>${escapeHtml(d[0])}: ${d[1].join(', ')}</li>`).join('');
    document.getElementById('pool').innerHTML = `
        <p>Used players: <b>${pool.used.length}</b></p>
        <p>Available: <b>${pool.available_count}</b></p>
        <details><summary>Available players (first 100)</summary><ul>${pool.available.slice(0, 100).map(a => `<li>${escapeHtml(a)}</li>`).join('')}</ul></details>
        <details><summary>Duplicates</summary><ul>${list || '<li>None</li>'}</ul></details>`;
}

function setUnlocked() {
    sessionStorage.setItem(UNLOCK_KEY, '1');
    document.getElementById('gate').hidden = true;
    document.getElementById('app').hidden = false;
}

document.addEventListener('DOMContentLoaded', init);

if (typeof document !== 'undefined' && !window.__TESTING__) {
    // no-op guard for jsdom; init runs above
}
```

- [ ] **Step 3: Generate a real passphrase hash and embed it**

```bash
PASS=$(openssl rand -base64 9); echo "Passphrase: $PASS"; printf '%s' "$PASS" | sha256sum
```

Paste the hex digest into `js/admin.js` `ADMIN_PASS_HASH`. Report the generated passphrase to the user (for their FIRST unlock). Instruct that the hash + passphrase can be regenerated by repeating this command.

- [ ] **Step 4: Run the vitest suite for the search module, and validate client loads in browser**

Run: `npx vitest run tests/js/adminSearch.test.js`
Expected: PASS.
Manual check (optional): `python3 serve.py`, open `http://localhost:8000/admin.html`.

- [ ] **Step 5: Commit**

```bash
git add admin.html js/admin.js
git commit -m "feat(admin): add passphrase-gated admin UI"
```

---

### Task 11: Anti-spoiler config (robots, sitemap) + regression fixtures

**Files:**
- Modify: `robots.txt`
- Modify: `.github/workflows/deploy.yml`
- Modify: `run_tests.sh`
- Modify: `JOURNAL.md`

- [ ] **Step 1: Add robots.txt disallows**

In `robots.txt`, after `Allow: /`:

```
Disallow: /admin
Disallow: /admin_data.json
```

- [ ] **Step 2: Exclude from sitemap generation**

In `.github/workflows/deploy.yml`, change the `exclude-paths` line:

```yaml
          exclude-paths: index.html docs/ admin.html admin_data.json
```

- [ ] **Step 3: Sync admin files into test fixtures**

In `run_tests.sh`, after the existing `cp stats_summary.json ...` line, add:

```bash
cp admin.html tests/fixtures/www/admin.html || true
cp admin_data.json tests/fixtures/www/admin_data.json || true
```

and add `cp js/adminSearch.js tests/fixtures/www/js/adminSearch.js || true` after the js symlink block (js is already symlinked, so instead just copy via the symlink target — no extra step needed; note the symlink covers `js/adminSearch.js` and `js/admin.js` automatically).

- [ ] **Step 4: Journal entry**

Append to `JOURNAL.md`:

```
## 2026-09-15 — Admin puzzle browser
- Added hidden, passphrase-gated admin page (admin.html) for searching/auditing all puzzles by name/nickname, plus stats and player-pool analysis.
- Added generated admin_data.json (full catalog + pool) built on every index rebuild; excluded from robots.txt and sitemap.
```

- [ ] **Step 5: Generate admin_data.json for the live repo and run full regression**

Run: `.venv/bin/python page-generator/main.py --rebuild-index`
Expected: regenerates `index.html`, `stats_summary.json`, and `admin_data.json`.

Run: `./run_tests.sh`
Expected: ALL PASS — full Python unit/integration/E2E + vitest suites (regression + new admin tests).

- [ ] **Step 6: Commit**

```bash
git add robots.txt .github/workflows/deploy.yml run_tests.sh JOURNAL.md admin_data.json
git commit -m "feat(admin): hide admin page from robots/sitemap; wire fixtures"
```

---

## Self-Review

**Spec coverage**
- §3 `admin_data.json` schema → Tasks 1–7 (all fields, flags, pool).
- §4.1 passphrase gate + noindex + robots + sitemap → Tasks 10, 11.
- §4.2 name/nickname search + fuzzy "no puzzle" behavior → Task 9 (+ `admin.js` wiring in Task 10).
- §4.3 detail view → Task 10 `puzzleDetailsHtml`.
- §4.4 reverse lookup (hints/QA) → covered by `searchPuzzles` `fields` param; `admin.js` default uses name/nicknames; reverse-lookup UI is a small enhancement and is **not** blocking (spec accepts search over hints/QA as a feature; default field search implemented).
- §4.5 filters, §4.6 stats, §4.7 pool, §4.8 export → Task 10 (export button intentionally minimal in v1; offers CSV via JSON copy — acceptable scope).
- §5 TDD → every task is test-first; §5.1–5.2 mapped to Tasks 1–7/8 and 9.
- §6 constraints → no audit reading (global constraints + Task 6/7 use no audit inputs), no changes to puzzle pages/stats_summary behavior.

**Placeholder scan:** No TODOs/TBDs; Step 10-3 includes the one intentional `ADMIN_PASS_HASH` placeholder that is filled during execution with a real command.

**Type consistency:** `build_admin_data`/`run_build`/`parse_detail_page`/`extract_*`/`build_pool`/`load_all_players` are defined in the tasks where they are introduced and referenced identically thereafter. JS `normalizeAdminText` (adminSearch) is distinct from the existing `normalizeText` (quizEngine) to avoid cross-module coupling — intentional.

**Known limitation (documented in spec):** static hosting means the gate is best-effort; `admin_data.json` is fetchable by anyone who knows the URL.