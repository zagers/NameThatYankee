# Improve Player Image Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the player image search success rate by allowing the AI to evaluate landscape images for potential portrait card cropping, refining AI verification criteria, and centralizing candidate prioritization.

**Architecture:** 
1. Remove the hard "landscape" check from `player_image_search.py` to allow the AI to evaluate all large images.
2. Update the AI to determine if a landscape image contains a portrait-oriented baseball card that can be cropped.
3. Refine the Gemini AI prompt to be more permissive of vintage card designs and signatures.
4. Centralize the candidate prioritization logic into a shared helper and apply it to both Google and Bing results.

**Tech Stack:** Python, Selenium, Google Gemini API, Pillow.

---

### Task 1: Centralize Candidate Prioritization

**Files:**
- Modify: `page-generator/automation/player_image_search.py`
- Test: `tests/test_image_search_prioritization.py` (New)

- [ ] **Step 1: Write the failing test for prioritization**
Create a test that verifies priority domains are sorted correctly.

```python
import pytest
from pathlib import Path
from automation.player_image_search import PlayerImageSearch

def test_prioritization_logic():
    search = PlayerImageSearch(Path("images"))
    candidates = [
        {'direct_url': 'https://example.com/normal.jpg'},
        {'direct_url': 'https://ebayimg.com/card.jpg'},
        {'direct_url': 'https://another.com/img.png'}
    ]
    # We expect a new method _prioritize_candidates to handle this
    prioritized = search._prioritize_candidates(candidates)
    assert prioritized[0]['direct_url'] == 'https://ebayimg.com/card.jpg'
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_image_search_prioritization.py`

- [ ] **Step 3: Implement centralized prioritization**
Refactor `player_image_search.py` to extract domain prioritization into `_prioritize_candidates` and use it in both Google and Bing flows.

```python
    def _prioritize_candidates(self, candidates: List[dict]) -> List[dict]:
        seen = set()
        unique_candidates = []
        priority_domains = ['showzone.io', 'showzone.gg', 'cards.theshow.com', 'topps.com', 'ebayimg.com', 'ebay.com', 'tcdb.com']
        
        # First pass: Priority domains
        for c in candidates:
            url = c['direct_url']
            if url not in seen and any(domain in url.lower() for domain in priority_domains):
                seen.add(url)
                unique_candidates.append(c)
        
        # Second pass: General results
        for c in candidates:
            url = c['direct_url']
            if url not in seen:
                seen.add(url)
                unique_candidates.append(c)
        return unique_candidates
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_image_search_prioritization.py`

- [ ] **Step 5: Commit**
`git add page-generator/automation/player_image_search.py tests/test_image_search_prioritization.py && git commit -m "refactor: centralize candidate prioritization"`

---

### Task 2: Allow AI to Evaluate Landscape Images for Cropping

**Files:**
- Modify: `page-generator/automation/player_image_search.py`
- Test: `tests/test_image_search_orientation.py` (New)

- [ ] **Step 1: Write the failing test**
Verify that landscape images are passed to the AI instead of being skipped.

```python
from pathlib import Path
from automation.player_image_search import PlayerImageSearch
from unittest.mock import MagicMock

def test_landscape_image_not_skipped():
    search = PlayerImageSearch(Path("images"))
    # Mock image_processor to return a large landscape image
    search.image_processor.get_image_info = MagicMock(return_value={'width': 1000, 'height': 800})
    
    # In the current code, this would return False or skip in a loop
    # We want to ensure it proceeds to AI analysis
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Modify orientation check logic**
Remove the hard `if width > height: continue` in `player_image_search.py`. This allows the AI to see the image and decide if a valid portrait card exists within the landscape frame.

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**
`git add page-generator/automation/player_image_search.py && git commit -m "feat: allow AI to evaluate landscape images for portrait cropping"`

---

### Task 3: Refine AI Verification Prompt

**Files:**
- Modify: `page-generator/ai_services.py`
- Test: `tests/test_ai_image_prompt.py` (New - Mocked API)

- [ ] **Step 1: Update AI Prompt in ai_services.py**
Update the `analyze_player_image` prompt to:
1. Clarify "Printed Autographs" are part of design for vintage cards.
2. Explicitly handle landscape images: "If the image is landscape, check if it contains a portrait-oriented baseball card. If so, provide the crop_box and mark as Priority 1 or 2. If it is landscape and NO portrait card can be cropped, it MUST be Priority 0."
3. Relax "Unofficial Uniform" for vintage eras.

- [ ] **Step 2: Verify prompt structure**
(Manual verification of the prompt text or a unit test to check string contains new criteria).

- [ ] **Step 3: Commit**
`git add page-generator/ai_services.py && git commit -m "feat: refine Gemini image analysis prompt for better vintage card support and landscape cropping"`
