# Optimize Test Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce test suite execution time by mocking overlooked Gemini API functions in Python backend integration tests.

**Architecture:** Mock `ai_services.get_facts_and_followup_from_gemini` and `ai_services.get_facts_from_gemini` in `tests/unit/page_generator/test_main_integration.py` where they were previously left unpatched. This will eliminate external API connection timeouts and rate limit sleeps during test execution.

**Tech Stack:** Python 3, Pytest, Unittest Mock

## Global Constraints

- Preserve all existing comments and docstrings.
- All new and modified tests must pass.
- Do not make external API connections in unit tests.

---

### Task 1: Patch combined facts/Q&A retrieval in test_automated_mode_workflow

**Files:**
- Modify: `tests/unit/page_generator/test_main_integration.py`

**Interfaces:**
- Consumes: None
- Produces: Mocks for `ai_services.get_facts_and_followup_from_gemini` during execution of `test_automated_mode_workflow`.

- [ ] **Step 1: Modify test_automated_mode_workflow to patch get_facts_and_followup_from_gemini**

Modify `tests/unit/page_generator/test_main_integration.py` to add `patch('ai_services.get_facts_and_followup_from_gemini', return_value={'facts': ['Fact 1', 'Fact 2'], 'qa': [{'question': 'Q1?', 'answer': 'A1.'}]})` to the mock context manager of `test_automated_mode_workflow`.

```python
    def test_automated_mode_workflow(self, temp_project_dir, sample_clue_image, sample_config, sample_player_data, sample_scraped_data):
        """Test automated mode workflow end-to-end"""
        with patch('config_manager.load_config', return_value=sample_config), \
             patch('ai_services.get_player_info_from_image', return_value=sample_player_data), \
             patch('ai_services.get_facts_and_followup_from_gemini', return_value={'facts': ['Fact 1', 'Fact 2'], 'qa': [{'question': 'Q1?', 'answer': 'A1.'}]}), \
             patch('scraper.search_and_scrape_player', return_value=sample_scraped_data), \
             ...
```

- [ ] **Step 2: Run the test to verify it passes quickly**

Run: `.venv/bin/pytest tests/unit/page_generator/test_main_integration.py::TestMainIntegrationWorkflows::test_automated_mode_workflow -v`
Expected: PASS in less than 0.1s.

- [ ] **Step 3: Commit changes**

```bash
git add tests/unit/page_generator/test_main_integration.py
git commit -m "test: mock get_facts_and_followup_from_gemini in automated mode test"
```

---

### Task 2: Patch facts retrieval in test_facts_only_mode_workflow

**Files:**
- Modify: `tests/unit/page_generator/test_main_integration.py`

**Interfaces:**
- Consumes: None
- Produces: Mocks for `ai_services.get_facts_from_gemini` during execution of `test_facts_only_mode_workflow`.

- [ ] **Step 1: Modify test_facts_only_mode_workflow to patch get_facts_from_gemini**

Modify `tests/unit/page_generator/test_main_integration.py` to add `patch('ai_services.get_facts_from_gemini', return_value=['Fact 1', 'Fact 2'])` to the mock context manager of `test_facts_only_mode_workflow`.

```python
    def test_facts_only_mode_workflow(self, temp_project_dir, sample_clue_image, sample_config, sample_player_data, sample_scraped_data):
        """Test facts-only mode workflow"""
        with patch('config_manager.load_config', return_value=sample_config), \
             patch('ai_services.get_player_info_from_image', return_value=sample_player_data), \
             patch('ai_services.get_facts_from_gemini', return_value=['Fact 1', 'Fact 2']), \
             patch('scraper.search_and_scrape_player', return_value=sample_scraped_data), \
             ...
```

- [ ] **Step 2: Run the test to verify it passes quickly**

Run: `.venv/bin/pytest tests/unit/page_generator/test_main_integration.py::TestMainIntegrationWorkflows::test_facts_only_mode_workflow -v`
Expected: PASS in less than 0.1s.

- [ ] **Step 3: Commit changes**

```bash
git add tests/unit/page_generator/test_main_integration.py
git commit -m "test: mock get_facts_from_gemini in facts-only mode test"
```

---

### Task 3: Verify overall test suite performance

**Files:**
- Modify: None

**Interfaces:**
- Consumes: None
- Produces: Verified local test suite running in under 1 minute.

- [ ] **Step 1: Run full python unit test suite**

Run: `.venv/bin/pytest tests/unit/ -v`
Expected: ALL tests pass in under 15 seconds.

- [ ] **Step 2: Run full regression test harness**

Run: `./run_tests.sh`
Expected: ALL tests pass, total time reduced from ~4 minutes to ~1 minute.
