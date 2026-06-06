# Identity-Blind Narrative Clues Design

## Overview
The goal of this design is to eliminate generic "filler" facts in the New York Yankees trivia clues (Career Highlights & Facts). Currently, the "spoiler ban" is so strict that the AI defaults to safe, generic statements like "utility player" or "signed as a free agent." This design introduces a "Narrative-First" approach that encourages distinctive, flavor-rich facts while maintaining the challenge of the quiz.

## Goals
- Replace generic clues with distinctive, high-impact narrative hooks.
- Maintain a strict "spoiler ban" (no names, teams, or years).
- Use player relationships and signature traits to provide context without giving away the answer.
- Implement a "Hall of Boredom" filter to automatically reject low-quality clues.

## Architecture

### 1. "Hall of Boredom" Filter
A list of forbidden phrases and concepts that are considered too generic for a high-quality trivia hint.
- "Signed as an amateur free agent"
- "Utility player"
- "Played for multiple organizations"
- "Filling gaps at multiple infield positions"
- "Frequently on the move"
- "Versatile infielder/pitcher"

### 2. Prompt Engineering (`page-generator/grounded_ai.py`)
Update the `generate_grounded_trivia` prompt with the following directives:
- **Narrative Hooks**: Prioritize specific anecdotes (weird injuries, signature quirks like "losing his helmet," or famous postseason moments described without names).
- **Relational Context**: Describe connections to legendary figures using titles (e.g., "The Captain," "A Hall of Fame base-stealer") instead of names.
- **Achievement-Based Clues**: Mention All-Star selections, Gold Gloves, or World Series rings as "major awards" or "championship hardware" without specifying the year.

### 3. Quality Guard Enhancement
Enhance the existing `Quality Guard` in `grounded_ai.py` to:
- Check for "Hall of Boredom" phrases using fuzzy matching or keyword lists.
- Verify that at least one hint is "High Impact" (contains a relational context or signature trait).

## Design Sections

### Section 1: The "Hall of Boredom" List
We will define a `FORBIDDEN_GENERIC_PHRASES` list in `grounded_ai.py`. Any clue containing these phrases (or semantic equivalents) will trigger an automatic retry.

### Section 2: Relational & Flavor Directives
The prompt will be updated to include specific examples of "Good" vs "Bad" clues:
- **Bad**: "Was a utility player for the club that signed him."
- **Good**: "Served as the primary backup to the legendary Captain during the final years of the icon's career."
- **Bad**: "Was traded mid-season multiple times."
- **Good**: "Was a key piece in a mid-season blockbuster trade for a Hall of Fame base-stealer."

### Section 3: Verification Logic
The `contains_hall_of_shame` function will be expanded to include the new generic phrases.

## Testing Strategy
1. **Unit Test**: Test the new `is_generic_hint` function with known bad strings.
2. **Integration Test**: Run the generator for Eduardo Núñez (2026-06-05) and verify that the output is more distinctive than the current clues.
3. **Regression Test**: Ensure the "spoiler ban" (no teams/years) is still strictly enforced.
