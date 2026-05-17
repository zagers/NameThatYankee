# ABOUTME: Design specification for the Batch Quiz Upgrade system.
# ABOUTME: Leverages Gemini 3.1 Flash Lite Batch API to upgrade 189 historical quizzes.

# Spec: Batch Quiz Upgrade System

## 1. Purpose
The current trivia archive consists of ~189 historical quizzes with varying degrees of accuracy and a simplistic "Career Highlights" format. This system will upgrade all existing quizzes to the new "Skeptical Storyteller" format (high-quality hints + Story Bites Q&A) while leveraging the **Gemini 3.1 Flash Lite Batch API** to minimize token costs (50% discount).

## 2. Success Criteria
- [ ] Generate accurate, grounded hints and Q&A for all 189 historical players.
- [ ] Minimize API costs by using the Batch API instead of interactive calls.
- [ ] Ensure data integrity via automated verification (`fact_verifier.py`) for every batch result.
- [ ] Maintain a "Resume" capability for the scraping phase to handle interruptions.
- [ ] Update all `.html` files without breaking existing layout or metadata.
- [ ] Rebuild `stats_summary.json` and `index.html` to reflect the updated content.

## 3. Architecture

### 3.1 Modules
Located in `page-generator/batch/`:

| Module | Responsibility |
| :--- | :--- |
| `prepare.py` | Scans HTML files, scrapes stats/bios, and generates `requests.jsonl`. |
| `client.py` | Manages communication with Gemini Batch API (Upload -> Poll -> Download). |
| `apply.py` | Validates responses, updates HTML files, and regenerates site manifest. |

### 3.2 Data Flow
1. **Prepare:** `HTML files` + `Scraper` -> `Dossiers` -> `requests.jsonl`
2. **Process:** `requests.jsonl` -> `Gemini Batch API` -> `responses.jsonl`
3. **Apply:** `responses.jsonl` + `Fact Verifier` -> `Updated HTML files` -> `Manifests`

### 3.3 State Management (`batch_progress.json`)
Tracks the status of each date to allow for interrupted runs:
```json
{
  "2025-04-01": {
    "player_name": "Don Mattingly",
    "status": "scraped|submitted|succeeded|failed",
    "dossier_path": "temp/dossiers/2025-04-01.json",
    "request_id": "req-123",
    "verification": "pass|fail"
  }
}
```

## 4. Implementation Details

### 4.1 Preparation Phase
- Extract player name from `h2` in existing HTML.
- Use `scraper.search_and_scrape_player` and `get_sabr_bio`.
- Construct the "Skeptical Storyteller" prompt (same as `grounded_ai.py`).
- Limit SABR bio to first 2500 words to keep input tokens reasonable.

### 4.2 Application Phase (The "Patch")
- Use `BeautifulSoup` for surgical updates:
    - Replace `.player-info ul` with new `facts`.
    - Inject/Update `#followup-section` with new `qa`.
    - Update `script#quiz-data` JSON.
- **Verification Gate:** If a result fails `fact_verifier.verify_claims`, the script **MUST NOT** update the HTML and must record the failure in `FACT_AUDIT_REPORT.md`.

## 5. Testing Strategy
- **Unit Tests:**
    - Mock Gemini Batch API for `client.py`.
    - Test `apply.py` HTML injection with various edge-case HTML structures.
    - Test `prepare.py` dossier extraction logic.
- **Integration Tests:**
    - Run a mini-batch (2-3 players) through the full pipeline.

## 6. Risks & Mitigations
- ** Hallucinations in Batch:** Mitigated by mandatory `fact_verifier` gate.
- **Rate Limits during Scraping:** Selenium driver will use the existing `shared_driver` pattern with modest delays.
- **HTML Inconsistency:** Using BeautifulSoup (html.parser) instead of Regex for updates.
