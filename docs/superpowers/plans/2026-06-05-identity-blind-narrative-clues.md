# Identity-Blind Narrative Clues Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve trivia clue generation by enforcing a "Narrative-First" approach and filtering out generic filler phrases.

**Architecture:** Update `page-generator/grounded_ai.py` to include a "Hall of Boredom" list, refine the Gemini prompt for distinctive storytelling, and enhance the quality guard to reject boring clues.

**Tech Stack:** Python, Google Gemini API

---

### Task 1: Update Quality Guard Logic

**Files:**
- Modify: `page-generator/grounded_ai.py`

- [ ] **Step 1: Define `FORBIDDEN_GENERIC_PHRASES` list**
Add a list of boring phrases to filter out at the top of the file or within the validation section.
```python
FORBIDDEN_GENERIC_PHRASES = [
    "signed as an amateur free agent",
    "utility player",
    "played for multiple organizations",
    "filling gaps at multiple infield positions",
    "frequently on the move",
    "versatile infielder",
    "versatile pitcher",
    "professional journey"
]
```

- [ ] **Step 2: Update `contains_hall_of_shame` to check for generic phrases**
Modify the existing function to loop through the new list and return any matches.

- [ ] **Step 3: Update `is_invalid_hint` to use the new list**
Ensure hints are rejected if they contain any "Hall of Boredom" phrases.

- [ ] **Step 4: Commit**
```bash
git add page-generator/grounded_ai.py
git commit -m "feat: add Hall of Boredom filter to grounded_ai.py"
```

### Task 2: Refine Gemini Prompt for Narrative Hooks

**Files:**
- Modify: `page-generator/grounded_ai.py`

- [ ] **Step 1: Update the `TASK 1: QUIZ HINTS` prompt section**
Add explicit instructions for "Narrative Hooks" and "Relational Context". Include the "Bad" vs "Good" examples from the design spec.

- [ ] **Step 2: Update the `GLOBAL RULES` section**
Add the "Distinctiveness Directive" and the instruction to avoid the "Hall of Boredom".

- [ ] **Step 3: Commit**
```bash
git add page-generator/grounded_ai.py
git commit -m "feat: refine Gemini prompt for distinctive narrative hooks"
```

### Task 3: Validation and Testing

**Files:**
- Create: `tests/test_clue_quality.py`

- [ ] **Step 1: Write unit tests for the filter**
Test `is_invalid_hint` with both generic and distinctive strings.

- [ ] **Step 2: Run unit tests**
Run: `pytest tests/test_clue_quality.py`

- [ ] **Step 3: Perform Integration Test with Eduardo Núñez**
Run the generator for 2026-06-05 and verify the new hints are more distinctive.
Run: `python page-generator/main.py 2026-06-05`

- [ ] **Step 4: Commit**
```bash
git add tests/test_clue_quality.py
git commit -m "test: add quality filter unit tests"
```
