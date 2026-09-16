# Design Spec: Admin Puzzle Browser (admin.html)

**Date:** 2026-09-15
**Topic:** Internal-only tool to search, inspect, and analyze all Name That Yankee puzzles.
**Status:** Draft

## 1. Purpose

With 275+ puzzles in the archive, puzzle management (spot-checking a player's previous use, verifying facts, planning future puzzles, auditing content quality) has become impractical to do by hand. This spec defines a **hidden admin page** that lets the site owner:

- Search all puzzles by **player name or nickname** and see whether a puzzle exists (e.g., "Home Run Baker" → no puzzle; "Baker" → the Dusty Baker trade puzzle).
- View **full spoiler details** for any puzzle (facts, career totals, follow-up Q&A, teams, years, WAR arc, images).
- Analyze the **player pool** (who has been used, duplicates, who is still available) against `all_players.js`.
- Compute **content-quality stats** (puzzles missing nicknames, images, stats; coverage by team/decade).

The page is **not for end users** — it exposes answers/spoilers. It is a static, best-effort-hidden, passphrase-gated page consistent with the static GitHub Pages deployment.

## 2. Architecture

Static-site approach, mirroring existing patterns:

- **`page-generator/admin_index.py`** — new generator module that scans puzzle data and writes **`admin_data.json`** (one file with the full catalog + pool analysis), committed and deployed like `stats_summary.json`.
- **`admin.html`** + **`js/admin.js`** — the admin UI. Fetches `admin_data.json`, renders search/filter/detail/stats/pool views.
- **`js/adminSearch.js`** — pure, testable search & matching functions (no DOM).
- Reuses existing data sources: the `#quiz-data` and `#search-data` divs and stats/follow-up markup in each `YYYY-MM-DD.html` detail page; `all_players.js` for the valid-player pool.

### 2.1 Data Flow

1. Generator scans `images/clue-*.webp` for dates (same pattern as `rebuild_index_page` in `html_generator.py`).
2. For each detail page, extract: name, nicknames, hints, career totals, teams, years, WAR arc, follow-up Q&A, image presence.
3. Load `ALL_PLAYERS` from `all_players.js`; compute used players + aliases, duplicates, and available players.
4. Write `admin_data.json`.
5. `admin.js` fetches it once and powers all views client-side.

## 3. `admin_data.json` Schema

```json
{
  "generated": "2026-09-15",
  "puzzles": [
    {
      "date": "2026-09-14",
      "name": "Billy Martin",
      "nicknames": ["Billy"],
      "hints": ["..."],
      "followup_qa": [{ "question": "...", "answer": "..." }],
      "career_totals": { "WAR": "2.9", "AB": "3419", "HR": "64" },
      "teams": ["NYY", "DET"],
      "years": ["1950", "1951"],
      "war_arc": [{ "year": "1950", "war": 0.0, "team": "NYY" }],
      "images": { "clue": true, "answer": true },
      "flags": ["no_nickname"]
    }
  ],
  "pool": {
    "used": [{ "date": "2026-09-14", "name": "Billy Martin" }],
    "used_names": ["billy martin"],
    "used_aliases": ["billy"],
    "available_count": 13654,
    "available": ["David Aardsma", "..."],
    "duplicates": [["Jim Abbott", ["2025-05-10", "2025-08-22"]]]
  }
}
```

- `flags` values: `no_nickname`, `missing_clue_image`, `missing_answer_image`, `missing_stats`, `unknown_name`. Audit data is deliberately **excluded** (kept in `FACT_AUDIT_REPORT.md` / `audit_dashboard.py` as-is).

## 4. Admin UI Functionality

### 4.1 Access Gate
- Passphrase input → `sha256(input)` compared to embedded hash in `js/admin.js` → on success sets a `sessionStorage` token; UI renders only when unlocked.
- `admin.html` ships with `noindex,nofollow` meta; `robots.txt` disallows `/admin` + `/admin_data.json`; sitemap generator excludes both files.

### 4.2 Name / Nickname Search (core)
- Live substring search over name + all nicknames.
- **Fuzzy matching** for typo tolerance (edit distance within small threshold) so "Home Run Baker" correctly reports *no puzzle* while "baker" surfaces the Dusty Baker puzzle.
- Results ranked: exact > prefix > substring > fuzzy; each card shows date, name, teams, preview of first hint.

### 4.3 Puzzle Detail View
- Full facts list, career totals table, follow-up Q&A (answers revealed), teams, years, WAR arc (table + optional chart), clue/answer image thumbnails with missing-asset badges, links to `quiz?date=` and reveal page.

### 4.4 Reverse Lookup
- Free-text search across hint text and follow-up answers.

### 4.5 Filters
- Decade, team, has-nickname / missing-nickname, missing-assets.

### 4.6 Stats Panel
- Total puzzles; per-year/per-month distribution; team coverage; nickname coverage; date gaps.

### 4.7 Pool Analysis Panel
- Used players list (with dates), duplicate alerts, searchable available players (`all_players.js` minus used) for puzzle planning.

### 4.8 Export
- Copy a puzzle row as JSON; download the catalog as CSV.

## 5. Testing & Validation (TDD)

Implemented test-first.

### 5.1 Python generator (`tests/unit/page_generator/test_admin_index.py`) — pytest
- **Fixture:** a temporary project directory with 2–3 synthetic detail pages + clue/answer image files + a small fake `all_players.js`.
- Cases:
  - Schema shape: keys/types of `admin_data.json`.
  - Name + nickname extraction from `#quiz-data` (`nicknames` array and legacy `nickname` string).
  - Hints/QA/career-totals/teams/years extraction.
  - WAR arc extraction from the chart script consts.
  - Missing image / missing stats / no-nickname / unknown-name flags.
  - Pool diff: used names, aliases, available list, duplicate detection.
  - Real `rebuild` output parses back (round-trip via `json.loads`).

### 5.2 JavaScript search (`tests/js/adminSearch.test.js`) — vitest
- Substring name match; nickname alias match; case/accent-insensitive; fuzzy typo tolerance (e.g., "martin" → Billy Martin; "Home Run Baker" → no matches); ranking order; empty-input behavior.

### 5.3 Regression
Full existing suite (`npm run test:all` / `run_tests.sh`) must stay green — no changes to `facts`, `quiz`, `index`, `analytics`, or SEO behavior. `rebuild_index_page` output (`stats_summary.json`, `index.html`) must be byte-stable w.r.t. existing tests.

## 6. Constraints & Notes

- No true auth on static hosting — passphrase + robots/sitemap exclusion is best-effort (documented limitation).
- Audit data stays separate; `admin_index.py` must not read `FACT_AUDIT_REPORT.md`.
- `admin_data.json` regenerated automatically whenever `rebuild_index_page()` runs (the 3 existing call sites in `main.py` plus the `--rebuild-index` mode).