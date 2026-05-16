# Design Spec: Player Fact Audit Tool

**Date:** 2026-05-15  
**Topic:** Fact Checking AI-Generated Trivia  
**Status:** Draft

## 1. Purpose
The purpose of this tool is to identify inaccuracies in AI-generated player facts across the 180+ trivia pages in the "Name That Yankee" project. It addresses "identity swap" errors (facts belonging to the wrong player) and "hallucinated details" (incorrect stats or years).

## 2. Architecture
The tool will be implemented as a Python script (`page-generator/fact_auditor.py`) and integrated into the existing `page-generator` suite.

### 2.1 Component Overview
- **HTML Scraper:** Extracts facts and player identity from daily puzzle files.
- **Phase 1 (Identity Sweep):** A "blind" test using `gemini-3.1-flash-lite` to identify a player from facts alone.
- **Phase 2 (Grounded Audit):** A targeted verification using Gemini with Google Search enabled.
- **Reporter:** Generates a Markdown summary of findings.

## 3. Detailed Design

### 3.1 Phase 1: Identity Sweep
- **Input:** 6 facts (3 main list items + 3 Q&A pairs).
- **Prompting:** The prompt will explicitly instruct the model NOT to look at the filename or provided name (if any), but to identify the player *only* based on the facts.
- **Mismatch Logic:** If `model_prediction.name.lower() != target_player_name.lower()`, the player is flagged as "Suspect".

### 3.2 Phase 2: Grounded Audit
- **Scope:** Triggered only for "Suspect" players.
- **Google Search Integration:** Each fact is checked individually using the `google_search` tool.
- **Verdict Schema:** 
    - `fact`: The original text.
    - `is_accurate`: boolean.
    - `reasoning`: Brief explanation of the discrepancy.
    - `source`: URL to Baseball-Reference or equivalent.

### 3.3 Data Flow
1. Find all `YYYY-MM-DD.html` files.
2. For each file:
    a. Extract `player_name` and `facts_list`.
    b. Run Phase 1.
    c. If Phase 1 fails, run Phase 2 on all 6 facts.
3. Consolidate results into `FACT_AUDIT_REPORT.md`.

## 4. Testing & Validation (TDD)
- **Canary Test (Tippy Martinez):** 
    - We know Tippy Martinez (2025-05-23) contains facts that actually belong to Dick Tidrow.
    - The tool must flag Tippy Martinez as "Suspect" in Phase 1.
    - Phase 2 must identify specific incorrect facts (e.g., the 1976 trade details).
- **Unit Tests:**
    - Scraper extraction logic.
    - Result consolidation.

## 5. Cost & Usage Constraints
- **Model:** `gemini-3.1-flash-lite` for Phase 1 (Low cost).
- **Rate Limiting:** Must respect the 13s interval defined in `ai_services.py`.
- **Selective Audit:** By only running Phase 2 on mismatches, we minimize expensive search tool calls.
