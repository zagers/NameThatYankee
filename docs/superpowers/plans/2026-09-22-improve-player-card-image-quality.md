# Improve Player Card Image Quality

## Problem

The automation pipeline stages "junky" images for trivia pages: modern commemorative/
reprint cards, manager-era photos, duplicate images, and angled/non-rectangular card
photos. The image *search* surface isn't the problem; the rubric never considers
provenance/era/role, dedupe is URL-only, candidates stop at the first 3 Priority-1
hits, and the AI's rectangular/angle rejection lives only in the prompt (never
enforced in code).

## Scope

- P0 only. P1/P2 (query ladder, source prioritization, search-engine hardening,
  config wiring, file hygiene) are explicitly out of scope.
- Era strictness: **demote**, never hard-reject. Modern reissues / manager-era /
  non-playing-era cards demote to Priority 3, retained only as fallback.

## Tasks

### P0-A: Thread career era through the pipeline
- `analyze_player_image(image_path, player_name, api_key, career_span=None)` uses
  `career_span` to pass era context to the model and enforce provenance rules.
- Thread `career_span` from `automated_workflow._find_player_image` → `main`
  standalone mode → `player_image_search.download_and_process_player_image` →
  `_evaluate_candidates` → `ai_services.analyze_player_image`.
- Standalone `main.py` path: career_span stays `None` (optional) so behavior is
  unchanged when not provided.

### P0-B: Provenance + role rubric in `analyze_player_image`
- New model fields: `is_playing_era_card`, `printed_copyright_year`,
  `appears_as_player`, `is_modern_reissue`.
- Python-side enforcement (safe defaults: missing/unclear fields do NOT demote):
  - When `career_span` is provided and card is a modern reissue → demote to P3.
  - When `career_span` is provided and image is NOT a playing-era card → demote to P3.
  - When `career_span` is provided and player does NOT appear as a player → demote to P3.
  - When `career_span` is None → no change.

### P0-C: Content-based near-duplicate rejection
- Add `compute_dhash` + `is_near_duplicate(a, b, threshold=10)` to `image_processor.py`.
- Dedupe final staged candidates by dHash Hamming distance in
  `download_and_process_player_image` (URLs differ but images identical, e.g. two
  copies of the same modern commemorative card).

### P0-D: Rank, don't stop-at-3
- In `_evaluate_candidates`, remove the early "stop at 3 Priority-1" exit.
  Continue through the whole window, then rank best_matches by
  (priority asc, playing-era first, pixel count desc); fallbacks fill remaining slots
  to a target of 3.

### P0-D2: Enforce rectangular/angle checks in code
- `can_be_fixed_by_crop` requires `is_rectangular` True.
- `unfixable_rejection` includes `not is_rectangular`.
- Rewrite CROP BOX INSTRUCTIONS to resolve the contradiction with criterion 5
  (card-on-table / perspective photos are rejected, not cropped).

## Verification

- Run `tests/unit/page_generator/test_analyze_image.py`,
  `tests/unit/page_generator/test_player_image_search.py`,
  `tests/unit/page_generator/test_image_processor.py`,
  `tests/test_image_search_prioritization.py` — all green.
- TDD per task: write failing test, verify red, minimal code, verify green.
- Final fresh-context review of the whole branch before merge.